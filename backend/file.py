import pyewf
import pytsk3
import os
import json
from datetime import datetime
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import sys

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UPLOADS_DIR = os.path.join(ROOT_DIR, 'uploads')

class EWFImgInfo(pytsk3.Img_Info):
    """Custom Img_Info class for pytsk3 to read from pyewf."""
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
    return datetime.utcfromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')

def extract_files(file_entry, parent_path="/", results=None):
    """Extract file information recursively."""
    if results is None:
        results = []

    try:
        if not file_entry.info.meta or not file_entry.info.name:
            return results

        file_name = file_entry.info.name.name.decode('utf-8', errors='replace')
        file_path = os.path.join(parent_path, file_name)

        # Create file entry
        file_data = {
            "path": file_path,
            "size": file_entry.info.meta.size,
            "created_time": format_timestamp(file_entry.info.meta.crtime),
            "modified_time": format_timestamp(file_entry.info.meta.mtime),
            "accessed_time": format_timestamp(file_entry.info.meta.atime),
            "type": "Directory" if file_entry.info.meta.type == pytsk3.TSK_FS_META_TYPE_DIR else "File"
        }
        
        results.append(file_data)

        if file_entry.info.meta.type == pytsk3.TSK_FS_META_TYPE_DIR:
            try:
                for sub_entry in file_entry.as_directory():
                    if sub_entry.info.name.name not in [b".", b".."]:
                        extract_files(sub_entry, file_path, results)
            except Exception as dir_error:
                print(f"Error accessing directory {file_path}: {dir_error}")

    except Exception as e:
        print(f"Error processing {parent_path}: {e}")

    return results

def create_dashboard(data, output_file="files_analysis_dashboard.html"):
    """Create forensic analysis dashboard."""
    try:
        # Convert data to DataFrame
        df = pd.DataFrame(data)
        
        # Convert timestamps to datetime
        for col in ['created_time', 'modified_time', 'accessed_time']:
            df[col] = pd.to_datetime(df[col], errors='coerce')

        # Create the dashboard with subplots
        fig = make_subplots(
            rows=6, 
            cols=1,
            subplot_titles=(
                'File Activity Timeline',
                'File Type Distribution',
                'File Size Distribution',
                'Directory Depth Analysis',
                'Access Pattern Analysis',
                'Temporal Activity Pattern'
            ),
            vertical_spacing=0.05,
            row_heights=[0.2, 0.15, 0.15, 0.15, 0.15, 0.15]
        )

        # 1. File Activity Timeline
        timeline_data = df.groupby(df['created_time'].dt.date).size().reset_index()
        timeline_data.columns = ['date', 'count']
        
        fig.add_trace(
            go.Scatter(
                x=timeline_data['date'],
                y=timeline_data['count'],
                name='File Creation',
                line=dict(color='#2E8B57', width=2),
                mode='lines+markers'
            ),
            row=1, col=1
        )

        # 2. File Type Distribution
        type_counts = df['type'].value_counts()
        
        fig.add_trace(
            go.Bar(
                x=type_counts.index,
                y=type_counts.values,
                name='File Types',
                marker_color=['#4682B4', '#20B2AA']
            ),
            row=2, col=1
        )

        # 3. File Size Distribution
        df['size_mb'] = df['size'] / (1024 * 1024)
        df['size_category'] = pd.cut(
            df['size_mb'],
            bins=[0, 0.1, 1, 10, 100, float('inf')],
            labels=['<0.1MB', '0.1-1MB', '1-10MB', '10-100MB', '>100MB']
        )
        size_dist = df['size_category'].value_counts()

        fig.add_trace(
            go.Bar(
                x=size_dist.index,
                y=size_dist.values,
                name='Size Distribution',
                marker_color='#6B8E23'
            ),
            row=3, col=1
        )

        # 4. Directory Depth Analysis
        df['depth'] = df['path'].str.count('/')
        depth_dist = df.groupby(['depth', 'type']).size().unstack(fill_value=0)

        if 'Directory' in depth_dist.columns:
            fig.add_trace(
                go.Bar(
                    x=depth_dist.index,
                    y=depth_dist['Directory'],
                    name='Directories',
                    marker_color='#4169E1'
                ),
                row=4, col=1
            )

        if 'File' in depth_dist.columns:
            fig.add_trace(
                go.Bar(
                    x=depth_dist.index,
                    y=depth_dist['File'],
                    name='Files',
                    marker_color='#32CD32'
                ),
                row=4, col=1
            )

        # 5. Access Pattern Analysis
        df['hour_accessed'] = df['accessed_time'].dt.hour
        hourly_access = df['hour_accessed'].value_counts().sort_index()

        fig.add_trace(
            go.Scatter(
                x=hourly_access.index,
                y=hourly_access.values,
                name='Hourly Access',
                line=dict(color='#9370DB', width=2),
                mode='lines+markers'
            ),
            row=5, col=1
        )

        # 6. Monthly Activity Pattern
        monthly_activity = df.groupby(df['created_time'].dt.to_period('M')).size()

        fig.add_trace(
            go.Bar(
                x=[str(x) for x in monthly_activity.index],
                y=monthly_activity.values,
                name='Monthly Activity',
                marker_color='#DAA520'
            ),
            row=6, col=1
        )

        # Update layout
        fig.update_layout(
            height=1500,
            showlegend=True,
            title=dict(
                text='Forensic Analysis Dashboard',
                x=0.5,
                font=dict(size=24)
            ),
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            ),
            paper_bgcolor='white',
            plot_bgcolor='rgba(0,0,0,0.05)'
        )

        # Update axes labels
        fig.update_xaxes(title_text="Date", row=1, col=1)
        fig.update_xaxes(title_text="File Type", row=2, col=1)
        fig.update_xaxes(title_text="Size Category", row=3, col=1)
        fig.update_xaxes(title_text="Directory Depth", row=4, col=1)
        fig.update_xaxes(title_text="Hour of Day", row=5, col=1)
        fig.update_xaxes(title_text="Month", row=6, col=1)

        fig.update_yaxes(title_text="Number of Files", row=1, col=1)
        fig.update_yaxes(title_text="Count", row=2, col=1)
        fig.update_yaxes(title_text="Number of Files", row=3, col=1)
        fig.update_yaxes(title_text="Count", row=4, col=1)
        fig.update_yaxes(title_text="Access Count", row=5, col=1)
        fig.update_yaxes(title_text="Activity Count", row=6, col=1)

        # Add summary statistics
        total_files = len(df)
        total_dirs = len(df[df['type'] == 'Directory'])
        total_size = df['size_mb'].sum()

        stats_text = (
            f"Summary Statistics<br>"
            f"Total Files: {total_files:,}<br>"
            f"Total Directories: {total_dirs:,}<br>"
            f"Total Size: {total_size:.2f} MB<br>"
            f"Average File Size: {(total_size/total_files if total_files > 0 else 0):.2f} MB"
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
        return True

    except Exception as e:
        print(f"Error creating dashboard: {e}")
        return False

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

        print(f"Found {len(split_files)} E01 files.")
        print("Starting analysis...")

        # Open EWF image
        ewf_handle = pyewf.handle()
        ewf_handle.open(split_files)

        # Process filesystem
        img_info = EWFImgInfo(ewf_handle)
        fs = pytsk3.FS_Info(img_info)
        
        # Extract all files
        print("Extracting file information...")
        all_files = []
        root_dir = fs.open_dir("/")
        
        for entry in root_dir:
            if entry.info.name.name not in [b".", b".."]:
                files = extract_files(entry, "/")
                if files:
                    all_files.extend(files)

        print(f"Found {len(all_files)} files/directories.")

        # Save results to JSON
        json_file = "extracted_files.json"
        with open(json_file, "w", encoding='utf-8') as f:
            json.dump(all_files, f, indent=4)
        print(f"File information saved to {json_file}")

        # Create visualization
        print("Creating visualization dashboard...")
        if create_dashboard(all_files, "files_analysis_dashboard.html"):
            print("Analysis complete! Open files_analysis_dashboard.html in a web browser to view results.")
        else:
            print("Analysis complete, but visualization failed. Check the JSON file for results.")

    except Exception as e:
        print(f"An error occurred during analysis: {e}")
        import traceback
        print(traceback.format_exc())
    finally:
        if 'ewf_handle' in locals():
            try:
                ewf_handle.close()
            except Exception as close_error:
                print(f"Error closing EWF handle: {close_error}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Please provide the full path for the case directory.")
        sys.exit(1)

    case_name = sys.argv[1]
    EWF_DIRECTORY = os.path.join(UPLOADS_DIR, f"case_{case_name}")
    main(EWF_DIRECTORY)