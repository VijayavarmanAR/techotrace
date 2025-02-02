import pyewf
import pytsk3
import os
from datetime import datetime
import Registry.Registry as reg
import json
import csv
from typing import Dict, List, Any, Counter
from collections import defaultdict
import io

class EWFImgInfo(pytsk3.Img_Info):
    def __init__(self, ewf_handle):
        self._ewf_handle = ewf_handle
        super().__init__()

    def read(self, offset, size):
        self._ewf_handle.seek(offset)
        return self._ewf_handle.read(size)

    def get_size(self):
        return self._ewf_handle.get_media_size()

def calculate_key_depth(key_path: str) -> int:
    """Calculate the depth of a registry key in the hierarchy."""
    # Split path and filter out empty strings
    path_parts = [part for part in key_path.split('\\') if part]
    return len(path_parts)

def analyze_operation_type(key_timestamp: datetime, value_data: Any) -> str:
    """Determine the likely operation type based on key attributes."""
    try:
        current_time = datetime.now()
        if key_timestamp is None:
            return "UNKNOWN"
        
        time_diff = current_time - key_timestamp
        
        if time_diff.days < 1:  # Recent changes
            return "MODIFY"
        elif isinstance(value_data, (bytes, bytearray)):
            return "BINARY_UPDATE"
        else:
            return "ACCESS"
    except Exception:
        return "UNKNOWN"

def safe_decode(value: bytes) -> str:
    """Safely decode byte strings."""
    try:
        return value.decode('utf-8', errors='replace')
    except (AttributeError, UnicodeDecodeError):
        return str(value)

def determine_value_type(value) -> str:
    """Determine the detailed type of a registry value."""
    if isinstance(value, bytes):
        return "BINARY"
    elif isinstance(value, int):
        return "INTEGER"
    elif isinstance(value, list):
        return "MULTI_STRING"
    elif isinstance(value, str):
        return "STRING"
    else:
        return f"OTHER_{type(value).__name__}"

def parse_registry_file(file_path: str) -> tuple[List[Dict[str, Any]], Dict[str, Counter]]:
    """Parse a registry file and return structured data with statistics."""
    registry_data = []
    statistics = {
        'key_depths': Counter(),
        'value_types': Counter(),
        'operations': Counter(),
        'key_frequencies': Counter()
    }
    
    try:
        registry = reg.Registry(file_path)
        
        def traverse_registry(key, current_depth=0) -> None:
            try:
                # Process values in the current key
                values = []
                key_path = key.path()
                
                # Update statistics
                statistics['key_depths'][current_depth] += 1
                statistics['key_frequencies'][key_path] += 1
                
                for value in key.values():
                    try:
                        value_data = value.value()
                        value_type = determine_value_type(value_data)
                        operation = analyze_operation_type(key.timestamp(), value_data)
                        
                        statistics['value_types'][value_type] += 1
                        statistics['operations'][operation] += 1
                        
                        values.append({
                            'name': value.name(),
                            'value': str(value_data),
                            'type': value_type,
                            'operation': operation
                        })
                    except Exception as e:
                        values.append({
                            'name': value.name(),
                            'value': f"Error reading value: {str(e)}",
                            'type': 'ERROR',
                            'operation': 'ERROR'
                        })

                # Create entry for this key
                entry = {
                    'registry_file': os.path.basename(file_path),
                    'key_path': key_path,
                    'key_depth': current_depth,
                    'last_write_time': key.timestamp().strftime('%Y-%m-%d %H:%M:%S') if key.timestamp() else "N/A",
                    'values': values,
                    'number_of_values': len(values),
                    'number_of_subkeys': len(list(key.subkeys())),
                    'operation_summary': {op: statistics['operations'][op] for op in ['MODIFY', 'BINARY_UPDATE', 'ACCESS', 'UNKNOWN']}
                }
                registry_data.append(entry)

                # Recursively process all subkeys
                for subkey in key.subkeys():
                    traverse_registry(subkey, current_depth + 1)

            except Exception as e:
                print(f"Error processing key {key.path() if hasattr(key, 'path') else 'unknown'}: {e}")

        # Start traversal from root
        traverse_registry(registry.root())
        
    except Exception as e:
        print(f"Error parsing registry file {file_path}: {e}")
    
    return registry_data, statistics

def save_to_json(data: List[Dict[str, Any]], statistics: Dict[str, Counter], output_file: str):
    """Save registry data and statistics to JSON file."""
    try:
        output_data = {
            'registry_entries': data,
            'statistics': {
                'key_depths': dict(statistics['key_depths']),
                'value_types': dict(statistics['value_types']),
                'operations': dict(statistics['operations']),
                'most_frequent_keys': dict(statistics['key_frequencies'].most_common(10))
            }
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=4, ensure_ascii=False)
        print(f"Successfully saved JSON data to {output_file}")
    except Exception as e:
        print(f"Error saving JSON file: {e}")

def save_to_csv(data: List[Dict[str, Any]], statistics: Dict[str, Counter], output_file: str):
    """Save registry data and statistics to CSV files."""
    try:
        # Save main registry data
        main_csv = output_file
        stats_csv = output_file.replace('.csv', '_statistics.csv')
        
        # Flatten and save main data
        flattened_data = []
        for entry in data:
            base_entry = {
                'registry_file': entry['registry_file'],
                'key_path': entry['key_path'],
                'key_depth': entry['key_depth'],
                'last_write_time': entry['last_write_time'],
                'number_of_values': entry['number_of_values'],
                'number_of_subkeys': entry['number_of_subkeys']
            }
            
            if entry['values']:
                for value in entry['values']:
                    row = base_entry.copy()
                    row.update({
                        'value_name': value['name'],
                        'value_data': value['value'],
                        'value_type': value['type'],
                        'operation': value['operation']
                    })
                    flattened_data.append(row)
            else:
                row = base_entry.copy()
                row.update({
                    'value_name': '',
                    'value_data': '',
                    'value_type': '',
                    'operation': ''
                })
                flattened_data.append(row)

        # Save main data
        with open(main_csv, 'w', newline='', encoding='utf-8-sig') as f:
            fieldnames = ['registry_file', 'key_path', 'key_depth', 'last_write_time',
                         'number_of_values', 'number_of_subkeys', 
                         'value_name', 'value_data', 'value_type', 'operation']
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(flattened_data)

        # Save statistics
        stats_data = []
        # Key depths
        for depth, count in statistics['key_depths'].items():
            stats_data.append({'category': 'key_depth', 'value': depth, 'count': count})
        # Value types
        for vtype, count in statistics['value_types'].items():
            stats_data.append({'category': 'value_type', 'value': vtype, 'count': count})
        # Operations
        for op, count in statistics['operations'].items():
            stats_data.append({'category': 'operation', 'value': op, 'count': count})
        # Most frequent keys
        for key, count in statistics['key_frequencies'].most_common(10):
            stats_data.append({'category': 'frequent_keys', 'value': key, 'count': count})

        with open(stats_csv, 'w', newline='', encoding='utf-8-sig') as f:
            fieldnames = ['category', 'value', 'count']
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(stats_data)

        print(f"Successfully saved CSV data to {main_csv} and {stats_csv}")
    except Exception as e:
        print(f"Error saving CSV files: {e}")

def process_registry_files(fs):
    """Process Windows Registry files from the image."""
    registry_paths = [
        "/Windows/System32/config/SYSTEM",
        "/Windows/System32/config/SOFTWARE",
        "/Windows/System32/config/SAM",
        "/Windows/System32/config/SECURITY",
        "/Users/*/NTUSER.DAT"
    ]
    
    all_registry_data = []
    combined_statistics = {
        'key_depths': Counter(),
        'value_types': Counter(),
        'operations': Counter(),
        'key_frequencies': Counter()
    }
    
    print("\nExtracting and analyzing registry files...")
    
    for reg_path in registry_paths:
        if "*" in reg_path:
            try:
                base_path = reg_path[:reg_path.index("*")]
                file_pattern = reg_path[reg_path.rindex("/")+1:]
                
                directory = fs.open_dir(base_path)
                for entry in directory:
                    if entry.info.name.name not in [b".", b".."]:
                        try:
                            name = entry.info.name.name.decode('utf-8', errors='replace')
                            user_path = f"{base_path}{name}/{file_pattern}"
                            output_path = f"extracted_{name}_{file_pattern}"
                            
                            if extract_registry_file(fs, user_path, output_path):
                                print(f"Processing {output_path}...")
                                registry_data, statistics = parse_registry_file(output_path)
                                all_registry_data.extend(registry_data)
                                
                                # Combine statistics
                                for key in combined_statistics:
                                    combined_statistics[key].update(statistics[key])
                                    
                        except Exception as e:
                            print(f"Error processing user registry {name}: {e}")
            except Exception as e:
                print(f"Error processing wildcard path {reg_path}: {e}")
        else:
            try:
                output_path = f"extracted_{os.path.basename(reg_path)}"
                if extract_registry_file(fs, reg_path, output_path):
                    print(f"Processing {output_path}...")
                    registry_data, statistics = parse_registry_file(output_path)
                    all_registry_data.extend(registry_data)
                    
                    # Combine statistics
                    for key in combined_statistics:
                        combined_statistics[key].update(statistics[key])
                        
            except Exception as e:
                print(f"Error processing registry file {reg_path}: {e}")
    
    # Save collected data
    if all_registry_data:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        json_file = f'registry_analysis_{timestamp}.json'
        csv_file = f'registry_analysis_{timestamp}.csv'
        
        save_to_json(all_registry_data, combined_statistics, json_file)
        save_to_csv(all_registry_data, combined_statistics, csv_file)
        
        print(f"\nAnalysis complete. Files saved:")
        print(f"- {json_file}")
        print(f"- {csv_file}")
        print(f"- {csv_file.replace('.csv', '_statistics.csv')}")
        
        # Print summary statistics
        print("\nSummary Statistics:")
        print(f"Total keys processed: {sum(combined_statistics['key_depths'].values())}")
        print(f"Maximum key depth: {max(combined_statistics['key_depths'].keys())}")
        print("\nMost common operations:")
        for op, count in combined_statistics['operations'].most_common(3):
            print(f"  {op}: {count}")
        print("\nMost common value types:")
        for vtype, count in combined_statistics['value_types'].most_common(3):
            print(f"  {vtype}: {count}")
    else:
        print("\nNo registry data was collected.")

def extract_registry_file(fs, reg_path: str, output_path: str) -> bool:
    """Extract a registry file from the image to local storage."""
    try:
        f = fs.open(reg_path)
        data = f.read_random(0, f.info.meta.size)
        with open(output_path, 'wb') as outfile:
            outfile.write(data)
        return True
    except Exception as e:
        print(f"Error extracting {reg_path}: {e}")
        return False

def main():
    split_files_directory = "/media/pranaash31/USB DISK/now/"
    
    split_files = sorted(
        [os.path.join(split_files_directory, f) for f in os.listdir(split_files_directory) 
         if f.endswith(tuple([f".E{i:02}" for i in range(1, 17)]))],
        key=lambda x: x
    )

    if not split_files:
        print("No E01 files found in the directory.")
        return

    print(f"E01 files detected: {split_files}")

    try:
        ewf_handle = pyewf.handle()
        ewf_handle.open(split_files)
        img_info = EWFImgInfo(ewf_handle)
        fs = pytsk3.FS_Info(img_info)
        process_registry_files(fs)
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        if 'ewf_handle' in locals():
            ewf_handle.close()

if __name__ == "__main__":
    main()