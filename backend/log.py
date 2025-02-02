import pyewf
import pytsk3
import os
import re
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
from datetime import datetime, UTC  # Import UTC for timestamp handling
import sys

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UPLOADS_DIR = os.path.join(ROOT_DIR, 'uploads')

class EWFImgInfo(pytsk3.Img_Info):
    def __init__(self, ewf_handle):
        self._ewf_handle = ewf_handle
        super().__init__()

    def read(self, offset, size):
        self._ewf_handle.seek(offset)
        return self._ewf_handle.read(size)

    def get_size(self):
        return self._ewf_handle.get_media_size()

def format_timestamp(timestamp):
    """Convert timestamp to human-readable format."""
    if timestamp is None:
        return "N/A"
    # Use timezone-aware datetime
    return datetime.fromtimestamp(timestamp, UTC).strftime('%Y-%m-%d %H:%M:%S')

def extract_timestamps(content):
    timestamp_pattern = r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}"
    return re.findall(timestamp_pattern, content)

def detect_anomalies(content, timestamps):
    anomalies = []
    if not timestamps:
        anomalies.append("No timestamps found in the log file.")

    unexpected_keywords = ["ERROR", "CRITICAL", "FAILURE", "WARNING", "ALERT", "EXCEPTION"]
    for keyword in unexpected_keywords:
        if keyword in content:
            anomalies.append(f"Keyword '{keyword}' detected in log content.")

    for ts in timestamps:
        try:
            ts_dt = datetime.strptime(ts, '%Y-%m-%d %H:%M:%S')
            if ts_dt.year < 2000 or ts_dt.year > datetime.now().year:
                anomalies.append(f"Unusual timestamp detected: {ts}")
        except ValueError:
            anomalies.append(f"Invalid timestamp format: {ts}")

    return len(anomalies) > 0

def analyze_log(file_entry, file_path, logs_data):
    offset = 0
    size = 1024 * 1024
    log_content = ""

    try:
        while offset < file_entry.info.meta.size:
            try:
                data = file_entry.read_random(offset, size)
                if not data:
                    break
                log_content += data.decode(errors="ignore")
                offset += len(data)
            except Exception as read_error:
                print(f"Error reading file content for {file_path}: {read_error}")
                break

        timestamps = extract_timestamps(log_content)
        is_anomaly = detect_anomalies(log_content, timestamps)
        
        log_entry = {
            "path": file_path,
            "size": file_entry.info.meta.size,
            "created_time": format_timestamp(file_entry.info.meta.crtime),
            "modified_time": format_timestamp(file_entry.info.meta.mtime),
            "accessed_time": format_timestamp(file_entry.info.meta.atime),
            "type": os.path.splitext(file_path)[1] or "No Extension",
            "anomaly_reason": "Anomaly detected" if is_anomaly else "No anomalies detected"
        }
        logs_data.append(log_entry)

    except Exception as e:
        print(f"An error occurred while analyzing {file_path}: {e}")

    return logs_data

def extract_logs(file_entry, parent_path="/", logs_data=[]):
    if not file_entry.info.meta or not file_entry.info.meta.size:
        return logs_data

    file_path = os.path.join(parent_path, file_entry.info.name.name.decode())

    if file_entry.info.meta.type == pytsk3.TSK_FS_META_TYPE_DIR:
        for sub_entry in file_entry.as_directory():
            if sub_entry.info.name.name not in [b".", b".."]:
                logs_data = extract_logs(sub_entry, file_path, logs_data)
    else:
        log_file_name = file_entry.info.name.name.decode()
        if log_file_name.endswith((".log", ".evtx", ".txt")):
            logs_data = analyze_log(file_entry, file_path, logs_data)

    return logs_data

def create_dashboard(logs_data, output_file="log_analysis_dashboard.html"):
    # Convert to DataFrame
    df = pd.DataFrame(logs_data)
    
    # Data preprocessing
    df['size_mb'] = df['size'] / (1024 * 1024)
    df['predicted_anomaly'] = df['anomaly_reason'].apply(lambda x: 1 if x == "Anomaly detected" else 0)
    
    # Convert timestamps
    for col in ['created_time', 'modified_time', 'accessed_time']:
        df[col] = pd.to_datetime(df[col])
    
    # Create dashboard with subplots - Fixed subplot creation
    fig = make_subplots(
        rows=6, 
        cols=1,
        subplot_titles=(
            'Anomaly Detection Timeline',
            'File Type Distribution',
            'File Size Distribution',
            'Time of Day Analysis',
            'Access Pattern Analysis',
            'Path Depth Analysis'
        ),
        vertical_spacing=0.05,
        row_heights=[0.2, 0.15, 0.15, 0.15, 0.15, 0.15]  # Fixed parameter name
    )

    # 1. Anomaly Timeline
    daily_stats = df.groupby(df['created_time'].dt.date).agg({
        'predicted_anomaly': ['count', 'sum']
    }).reset_index()
    daily_stats.columns = ['date', 'total', 'anomalies']
    daily_stats['normal'] = daily_stats['total'] - daily_stats['anomalies']

    fig.add_trace(
        go.Scatter(
            x=daily_stats['date'],
            y=daily_stats['anomalies'],
            name='Anomalies',
            line=dict(color='red', width=2),
            mode='lines+markers'
        ),
        row=1, col=1
    )
    fig.add_trace(
        go.Scatter(
            x=daily_stats['date'],
            y=daily_stats['normal'],
            name='Normal Files',
            line=dict(color='green', width=2),
            mode='lines+markers'
        ),
        row=1, col=1
    )

    # 2. File Type Distribution
    type_dist = df.groupby(['type', 'anomaly_reason']).size().unstack(fill_value=0)
    
    fig.add_trace(
        go.Bar(
            x=type_dist.index,
            y=type_dist['No anomalies detected'],
            name='Normal Files',
            marker_color='green'
        ),
        row=2, col=1
    )
    fig.add_trace(
        go.Bar(
            x=type_dist.index,
            y=type_dist['Anomaly detected'],
            name='Anomalous Files',
            marker_color='red'
        ),
        row=2, col=1
    )

    # 3. File Size Distribution
    def size_category(size):
        if size < 0.1:
            return 'Tiny (<0.1MB)'
        elif size < 1:
            return 'Small (0.1-1MB)'
        elif size < 10:
            return 'Medium (1-10MB)'
        elif size < 100:
            return 'Large (10-100MB)'
        else:
            return 'Very Large (>100MB)'

    df['size_category'] = df['size_mb'].apply(size_category)
    size_dist = pd.crosstab(df['size_category'], df['anomaly_reason'])
    
    fig.add_trace(
        go.Bar(
            x=list(size_dist.index),
            y=size_dist['No anomalies detected'],
            name='Normal Files',
            marker_color='green'
        ),
        row=3, col=1
    )
    fig.add_trace(
        go.Bar(
            x=list(size_dist.index),
            y=size_dist['Anomaly detected'],
            name='Anomalous Files',
            marker_color='red'
        ),
        row=3, col=1
    )

    # 4. Time of Day Analysis
    df['hour_created'] = df['created_time'].dt.hour
    hourly_dist = pd.crosstab(df['hour_created'], df['anomaly_reason'])
    
    fig.add_trace(
        go.Scatter(
            x=hourly_dist.index,
            y=hourly_dist['No anomalies detected'],
            name='Normal Activity',
            line=dict(color='green', width=2),
            mode='lines+markers'
        ),
        row=4, col=1
    )
    fig.add_trace(
        go.Scatter(
            x=hourly_dist.index,
            y=hourly_dist['Anomaly detected'],
            name='Anomalous Activity',
            line=dict(color='red', width=2),
            mode='lines+markers'
        ),
        row=4, col=1
    )

    # 5. Access Pattern Analysis
    df['time_between_mod_access'] = (df['accessed_time'] - df['modified_time']).dt.total_seconds()
    df['time_between_create_mod'] = (df['modified_time'] - df['created_time']).dt.total_seconds()
    
    fig.add_trace(
        go.Scatter(
            x=df[df['predicted_anomaly']==0]['time_between_create_mod'],
            y=df[df['predicted_anomaly']==0]['time_between_mod_access'],
            mode='markers',
            name='Normal Files',
            marker=dict(color='green', size=8, opacity=0.6)
        ),
        row=5, col=1
    )
    fig.add_trace(
        go.Scatter(
            x=df[df['predicted_anomaly']==1]['time_between_create_mod'],
            y=df[df['predicted_anomaly']==1]['time_between_mod_access'],
            mode='markers',
            name='Anomalous Files',
            marker=dict(color='red', size=8, opacity=0.6)
        ),
        row=5, col=1
    )

    # 6. Path Depth Analysis
    df['path_depth'] = df['path'].str.count('/')
    
    fig.add_trace(
        go.Scatter(
            x=df[df['predicted_anomaly']==0]['path_depth'],
            y=df[df['predicted_anomaly']==0]['size_mb'],
            mode='markers',
            name='Normal Files',
            marker=dict(color='green', size=8, opacity=0.6)
        ),
        row=6, col=1
    )
    fig.add_trace(
        go.Scatter(
            x=df[df['predicted_anomaly']==1]['path_depth'],
            y=df[df['predicted_anomaly']==1]['size_mb'],
            mode='markers',
            name='Anomalous Files',
            marker=dict(color='red', size=8, opacity=0.6)
        ),
        row=6, col=1
    )

    # Update layout
    fig.update_layout(
        height=1500,
        title=dict(
            text='Forensic Log Analysis Dashboard',
            x=0.5,
            font=dict(size=24)
        ),
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ),
        paper_bgcolor='white',
        plot_bgcolor='rgba(0,0,0,0)'
    )

    # Update axes labels
    fig.update_xaxes(title_text="Date", row=1, col=1)
    fig.update_xaxes(title_text="File Type", row=2, col=1)
    fig.update_xaxes(title_text="Size Category", row=3, col=1)
    fig.update_xaxes(title_text="Hour of Day", row=4, col=1)
    fig.update_xaxes(title_text="Time Between Creation and Modification (s)", row=5, col=1)
    fig.update_xaxes(title_text="Path Depth", row=6, col=1)

    fig.update_yaxes(title_text="Number of Files", row=1, col=1)
    fig.update_yaxes(title_text="Number of Files", row=2, col=1)
    fig.update_yaxes(title_text="Number of Files", row=3, col=1)
    fig.update_yaxes(title_text="Number of Files", row=4, col=1)
    fig.update_yaxes(title_text="Time Between Modification and Access (s)", row=5, col=1)
    fig.update_yaxes(title_text="File Size (MB)", row=6, col=1)

    # Add summary statistics
    total_files = len(df)
    total_anomalies = df['predicted_anomaly'].sum()
    anomaly_rate = (total_anomalies / total_files) * 100

    stats_text = (
        f"Summary Statistics<br>"
        f"Total Files Analyzed: {total_files}<br>"
        f"Total Anomalies: {int(total_anomalies)}<br>"
        f"Anomaly Rate: {anomaly_rate:.2f}%"
    )

    fig.add_annotation(
        xref="paper",
        yref="paper",
        x=0,
        y=1.15,
        text=stats_text,
        showarrow=False,
        font=dict(size=14),
        align="left"
    )

    # Save dashboard
    fig.write_html(output_file)
    print(f"Dashboard has been saved to {output_file}")

# ... [Previous code remains the same until the main function]

def main(ewf_directory):
    split_files = sorted(
        [os.path.join(ewf_directory, f) for f in os.listdir(ewf_directory) 
         if f.endswith(tuple([f".E{i:02}" for i in range(1, 17)]))],
        key=lambda x: x
    )

    if not split_files:
        print("No EWF files found in the directory.")
        return

    print(f"EWF files detected: {split_files}")

    try:
        ewf_handle = pyewf.handle()
        ewf_handle.open(split_files)
        img_info = EWFImgInfo(ewf_handle)
        fs = pytsk3.FS_Info(img_info)

        print("Analyzing logs from EWF image...")
        root_dir = fs.open_dir("/")
        logs_data = []
        
        for entry in root_dir:
            if entry.info.name.name not in [b".", b".."]:
                logs_data = extract_logs(entry, logs_data=logs_data)

        # Create and save dashboard
        create_dashboard(logs_data, "log_analysis_dashboard.html")
        print("Analysis and visualization complete!")

    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        if 'ewf_handle' in locals():
            ewf_handle.close()

if __name__ == "__main__":

    # Get the third argument passed from the command line
    if len(sys.argv) < 2:
        print("Please provide the full path for the case directory.")
        sys.exit(1)

    case_name = sys.argv[1]
    EWF_DIRECTORY = os.path.join(UPLOADS_DIR, f"case_{case_name}")
    main(EWF_DIRECTORY)