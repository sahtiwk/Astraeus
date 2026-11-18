import os
import sys
import time

# Add project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.parser import parse_log_text
from src.anomaly import detect_anomalies

def run_throughput_benchmark(log_file: str):
    print(f"--- Running Throughput Benchmark on {log_file} ---")
    
    if not os.path.exists(log_file):
        print(f"Error: {log_file} does not exist. Run generate_mock_data.py first.")
        return None
        
    with open(log_file, 'r', encoding='utf-8') as f:
        raw_text = f.read()
        
    file_size_mb = os.path.getsize(log_file) / (1024 * 1024)
    print(f"File Size: {file_size_mb:.2f} MB")
    
    # 1. Benchmark Parsing
    print("Starting Parsing...")
    start_time = time.time()
    events = parse_log_text(raw_text)
    parse_time = time.time() - start_time
    
    num_events = len(events)
    parse_throughput = num_events / parse_time if parse_time > 0 else 0
    print(f"Parsed {num_events} events in {parse_time:.2f} seconds.")
    print(f"Parsing Throughput: {parse_throughput:.2f} events/second")
    
    # 2. Benchmark Anomaly Detection
    print("\nStarting Anomaly Detection...")
    start_time = time.time()
    anomalies = detect_anomalies(events)
    detect_time = time.time() - start_time
    
    print(f"Detected {len(anomalies)} anomalies in {detect_time:.2f} seconds.")
    
    total_time = parse_time + detect_time
    total_throughput = num_events / total_time if total_time > 0 else 0
    print(f"\n--- Total Processing Time: {total_time:.2f} seconds ---")
    print(f"--- Total Throughput: {total_throughput:.2f} events/second ---")
    
    return {
        "num_events": num_events,
        "file_size_mb": file_size_mb,
        "parse_time": parse_time,
        "parse_throughput": parse_throughput,
        "detect_time": detect_time,
        "total_time": total_time,
        "total_throughput": total_throughput,
        "num_anomalies_detected": len(anomalies)
    }

if __name__ == "__main__":
    test_dir = os.path.dirname(os.path.abspath(__file__))
    log_file = os.path.join(test_dir, "test_100k.log")
    run_throughput_benchmark(log_file)
