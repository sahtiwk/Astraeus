import os
import sys
import time
import json

# Add project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.parser import parse_log_text
from src.anomaly import detect_anomalies
from src.llm_analysis import generate_rca

# Assume a manual root cause analysis by an engineer takes 15 minutes on average
MANUAL_BASELINE_SECONDS = 15 * 60

def run_rca_time_benchmark(log_file: str):
    print("--- Running RCA Investigation Time Benchmark ---")
    
    if not os.getenv("GEMINI_API_KEY"):
        print("Warning: GEMINI_API_KEY not set. Cannot run RCA time benchmark.")
        return {"rca_generation_time": 0, "reduction_percentage": 0, "status": "skipped"}
        
    if not os.path.exists(log_file):
        print(f"Error: {log_file} not found. Run generate_mock_data.py first.")
        return None
        
    print("Extracting a sample anomaly for RCA...")
    with open(log_file, 'r', encoding='utf-8') as f:
        # Just read the first 1000 lines to find an anomaly quickly
        raw_text = "\n".join([next(f) for _ in range(20000)])
        
    events = parse_log_text(raw_text)
    anomalies = detect_anomalies(events)
    
    if not anomalies:
        print("Warning: No anomalies found in the sample text. Cannot run RCA.")
        return {"rca_generation_time": 0, "reduction_percentage": 0, "status": "no_anomalies"}
        
    sample_anomaly = anomalies[0]
    
    print(f"Generating RCA for anomaly: '{sample_anomaly.keywords}'...")
    start_time = time.time()
    
    try:
        rca_result = generate_rca(sample_anomaly)
        rca_time = time.time() - start_time
        
        print(f"RCA Generation completed in {rca_time:.2f} seconds.")
        print(f"AI RCA Summary: {rca_result.summary}")
        
        reduction = ((MANUAL_BASELINE_SECONDS - rca_time) / MANUAL_BASELINE_SECONDS) * 100
        
        print(f"\n--- Manual Baseline: {MANUAL_BASELINE_SECONDS}s (15 mins) ---")
        print(f"--- AI RCA Time: {rca_time:.2f}s ---")
        print(f"--- Investigation Time Reduced By: {reduction:.2f}% ---")
        
        return {
            "manual_baseline_s": MANUAL_BASELINE_SECONDS,
            "ai_rca_time_s": rca_time,
            "reduction_percentage": reduction,
            "status": "success"
        }
        
    except Exception as e:
        print(f"Failed to generate RCA: {e}")
        return {"rca_generation_time": 0, "reduction_percentage": 0, "status": "failed"}

if __name__ == "__main__":
    test_dir = os.path.dirname(os.path.abspath(__file__))
    log_file = os.path.join(test_dir, "test_100k.log")
    run_rca_time_benchmark(log_file)
