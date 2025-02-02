import pyewf
import pytsk3
import os
from datetime import datetime
import json
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
from pathlib import Path
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
    if timestamp is None:
        return "N/A"
    return datetime.utcfromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')

def detect_anomalies(file_data):
    try:
        file_path = file_data['path'].lower()
        file_size = file_data['size']
        created_time = datetime.strptime(file_data['created_time'], '%Y-%m-%d %H:%M:%S')
        modified_time = datetime.strptime(file_data['modified_time'], '%Y-%m-%d %H:%M:%S')
        accessed_time = datetime.strptime(file_data['accessed_time'], '%Y-%m-%d %H:%M:%S')
        current_time = datetime.now()

        if '/.' in file_path or file_path.split('/')[-1].startswith('.'):
            return "Hidden file/directory"
        if '.exe' in file_path and '/windows/system32' not in file_path:
            return "Executable in non-standard location"
        if created_time > current_time:
            return "Future creation timestamp"
        if modified_time < created_time:
            return "Modified before creation"
        if 'system32' in file_path and '/temp/' in file_path:
            return "System file in temporary location"
        if 'chrome' in file_path and file_size > 500_000_000:
            return "Unusually large browser data"
        if 'firewall' in file_path and file_size < 1024:
            return "Suspiciously small firewall log"
        if any(port in file_path for port in ['4444', '31337', '1337', '666', '6666', '8080']):
            return "Reference to suspicious port"
        if 'hosts' in file_path and modified_time > accessed_time:
            return "Modified hosts file"
        if any(x in file_path for x in ['netcat', 'wireshark', 'tcpdump']) and '/desktop/' in file_path:
            return "Network tool in user space"
        
        return None
    except Exception as e:
        print(f"Error in anomaly detection: {str(e)}")
        return None

def is_network_related(file_path):
    network_keywords = [
        "/AppData/Local/Google/Chrome/User Data",
        "/AppData/Local/Mozilla/Firefox/Profiles",
        "/AppData/Local/Microsoft/Windows/INetCache",
        "/Windows/System32/winevt/Logs/Microsoft-Windows-NetworkProfile",
        "/Windows/System32/drivers/etc/hosts",
        "/Windows/System32/LogFiles/W3SVC",
        "/Windows/System32/netstat",
        "/Windows/System32/drivers/tcpip",
        "/Windows/System32/LogFiles/Firewall",
        "/inetpub/logs",
        "/AppData/Local/Microsoft/Outlook",
    ]
    
    network_extensions = [
        '.pcap', '.pcapng', '.evt', '.evtx', '.log',
        '.sqlite', '.db', '.dat', '.etl', '.pf',
        '.hosts', '.dnscache', '.history', '.eml'
    ]

    return any(keyword.lower() in file_path.lower() for keyword in network_keywords) or \
           any(file_path.lower().endswith(ext) for ext in network_extensions)

def extract_network_files(file_entry, parent_path="/", results=None):
    if results is None:
        results = []

    try:
        if not file_entry.info.meta or not file_entry.info.meta.size:
            return results

        file_name = file_entry.info.name.name.decode()
        file_path = os.path.join(parent_path, file_name)

        if file_entry.info.meta.type == pytsk3.TSK_FS_META_TYPE_DIR:
            try:
                for sub_entry in file_entry.as_directory():
                    if sub_entry.info.name.name not in [b".", b".."]:
                        results = extract_network_files(sub_entry, file_path, results)
            except Exception as dir_error:
                print(f"Error accessing directory {file_path}: {dir_error}")
        else:
            if is_network_related(file_path):
                file_data = {
                    "path": file_path,
                    "size": file_entry.info.meta.size,
                    "created_time": format_timestamp(file_entry.info.meta.crtime),
                    "modified_time": format_timestamp(file_entry.info.meta.mtime),
                    "accessed_time": format_timestamp(file_entry.info.meta.atime),
                    "type": "File"
                }

                anomaly = detect_anomalies(file_data)
                if anomaly:
                    file_data["anomaly_reason"] = anomaly
                
                results.append(file_data)

    except Exception as e:
        print(f"Error processing {parent_path}: {e}")

    return results

def create_advanced_dashboard(network_files):
    """Create an advanced interactive dashboard with detailed forensic analysis."""
    
    # Convert to DataFrame for easier manipulation
    df = pd.DataFrame(network_files)
    df['created_time'] = pd.to_datetime(df['created_time'])
    df['modified_time'] = pd.to_datetime(df['modified_time'])
    df['accessed_time'] = pd.to_datetime(df['accessed_time'])
    df['file_extension'] = df['path'].apply(lambda x: Path(x).suffix.lower())
    df['directory'] = df['path'].apply(lambda x: str(Path(x).parent))
    df['is_anomalous'] = df['anomaly_reason'].notna()

    # Create the main figure with subplots
    fig = make_subplots(
        rows=3, cols=2,
        subplot_titles=(
            'File Analysis Overview',
            'Anomaly Distribution',
            'Temporal Analysis',
            'File Type Distribution',
            'Directory Impact Analysis',
            'Anomaly Types'
        ),
        specs=[
            [{"type": "indicator"}, {"type": "pie"}],
            [{"type": "scatter", "colspan": 2}, None],
            [{"type": "bar"}, {"type": "bar"}]
        ],
        vertical_spacing=0.12,
        horizontal_spacing=0.1
    )

    # 1. File Analysis Overview (Indicator)
    total_files = len(df)
    anomaly_count = df['is_anomalous'].sum()
    fig.add_trace(
        go.Indicator(
            mode="number+delta",
            value=total_files,
            title={"text": "Total Files Analyzed"},
            delta={'reference': total_files-anomaly_count},
            domain={'row': 0, 'column': 0}
        ),
        row=1, col=1
    )

    # 2. Anomaly Distribution (Pie Chart)
    labels = ['Normal Files', 'Anomalous Files']
    values = [total_files - anomaly_count, anomaly_count]
    fig.add_trace(
        go.Pie(
            labels=labels,
            values=values,
            hole=0.4,
            marker_colors=['#2ecc71', '#e74c3c']
        ),
        row=1, col=2
    )

    # 3. Temporal Analysis (Scatter Plot)
    fig.add_trace(
        go.Scatter(
            x=df['created_time'],
            y=df['size'],
            mode='markers',
            marker=dict(
                size=8,
                color=df['is_anomalous'].astype(int),
                colorscale=[[0, '#2ecc71'], [1, '#e74c3c']],
                showscale=True,
                colorbar=dict(title='Anomaly Status')
            ),
            text=df['path'].apply(lambda x: os.path.basename(x)),
            hovertemplate="<b>%{text}</b><br>" +
                         "Size: %{y}<br>" +
                         "Time: %{x}<br>" +
                         "<extra></extra>"
        ),
        row=2, col=1
    )

    # 4. File Type Distribution
    type_counts = df.groupby(['file_extension', 'is_anomalous']).size().unstack(fill_value=0)
    colors = ['#2ecc71', '#e74c3c']
    
    for i, (col, color) in enumerate(zip(type_counts.columns, colors)):
        fig.add_trace(
            go.Bar(
                name=f'{"Anomalous" if col else "Normal"}',
                x=type_counts.index,
                y=type_counts[col],
                marker_color=color
            ),
            row=3, col=1
        )

    # 5. Anomaly Types Breakdown
    if 'anomaly_reason' in df.columns:
        anomaly_counts = df['anomaly_reason'].value_counts()
        fig.add_trace(
            go.Bar(
                x=anomaly_counts.values,
                y=anomaly_counts.index,
                orientation='h',
                marker_color='#e74c3c'
            ),
            row=3, col=2
        )

    # Update layout with modern styling
    fig.update_layout(
        title={
            'text': "Network Forensic Analysis Dashboard",
            'y':0.95,
            'x':0.5,
            'xanchor': 'center',
            'yanchor': 'top',
            'font': {'size': 24, 'color': '#2c3e50'}
        },
        showlegend=True,
        height=1200,
        template="plotly_white",
        paper_bgcolor='white',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(
            family="Arial, sans-serif",
            size=12,
            color="#2c3e50"
        )
    )

    # Update axes
    fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor='rgba(189, 195, 199, 0.5)')
    fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='rgba(189, 195, 199, 0.5)')

    # Add statistical annotations
    anomaly_rate = (anomaly_count/total_files) * 100
    annotations = [
        dict(
            text=f"Anomaly Rate: {anomaly_rate:.1f}%",
            xref="paper", yref="paper",
            x=0.02, y=1.05,
            showarrow=False,
            font=dict(size=14, color="#2c3e50")
        )
    ]
    
    fig.update_layout(annotations=annotations)

    # Save the dashboard
    fig.write_html(
        "network_analysis_dashboard.html",
        include_plotlyjs=True,
        full_html=True,
        include_mathjax=False
    )

def main(split_files_directory):
    try:
        # Find and sort E01 files
        split_files = sorted(
            [os.path.join(split_files_directory, f) for f in os.listdir(split_files_directory) 
             if f.endswith(tuple([f".E{i:02}" for i in range(1, 17)]))],
            key=lambda x: x
        )

        if not split_files:
            print("No E01 files found in the directory.")
            return

        print(f"E01 files detected: {split_files}")

        # Process files
        ewf_handle = pyewf.handle()
        ewf_handle.open(split_files)
        
        img_info = EWFImgInfo(ewf_handle)
        fs = pytsk3.FS_Info(img_info)
        
        print("\nAnalyzing E01 image for network-related files...")
        network_files = []
        root_dir = fs.open_dir("/")
        for entry in root_dir:
            if entry.info.name.name not in [b".", b".."]:
                network_files = extract_network_files(entry, "/", network_files)

        # Save results to JSON
        with open("network.json", "w", encoding='utf-8') as f:
            json.dump(network_files, f, indent=4)

        # Create visualization dashboard
        print("\nGenerating advanced visualization dashboard...")
        create_advanced_dashboard(network_files)
        
        # Print summary statistics
        anomaly_count = sum(1 for file in network_files if "anomaly_reason" in file)
        print("\nAnalysis Summary:")
        print(f"Total files analyzed: {len(network_files)}")
        print(f"Files with anomalies: {anomaly_count}")
        print(f"Anomaly rate: {(anomaly_count/len(network_files)*100):.2f}%")
        
        # Print anomaly breakdown
        print("\nAnomaly Type Breakdown:")
        anomaly_types = {}
        for file in network_files:
            if "anomaly_reason" in file:
                reason = file["anomaly_reason"]
                anomaly_types[reason] = anomaly_types.get(reason, 0) + 1
        
        for reason, count in sorted(anomaly_types.items(), key=lambda x: x[1], reverse=True):
            print(f"  - {reason}: {count}")

        print("\nResults saved to:")
        print("- network.json (detailed data)")
        print("- network_analysis_dashboard.html (interactive visualization)")

    except Exception as e:
        print(f"An error occurred: {e}")
        import traceback
        print(traceback.format_exc())
    finally:
        if 'ewf_handle' in locals():
            ewf_handle.close()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Please provide the full path for the case directory.")
        sys.exit(1)

    case_name = sys.argv[1]
    EWF_DIRECTORY = os.path.join(UPLOADS_DIR, f"case_{case_name}")
    main(EWF_DIRECTORY)