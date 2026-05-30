import os
import sys
from dotenv import load_dotenv

load_dotenv()

from generate_mock_data import generate_mock_logs
from benchmark_throughput import run_throughput_benchmark
from benchmark_retrieval import run_retrieval_benchmark
from benchmark_rca_time import run_rca_time_benchmark

def main():
    print("="*50)
    print("   LOGSAGE (ASTRAEUS) PERFORMANCE BENCHMARK SUITE")
    print("="*50)
    
    test_dir = os.path.dirname(os.path.abspath(__file__))
    log_file = os.path.join(test_dir, "test_100k.log")
    truth_file = os.path.join(test_dir, "ground_truth.json")
    
    # 1. Data Generation
    print("\n[1/4] Generating Mock Data (100K logs)...")
    if not os.path.exists(log_file) or not os.path.exists(truth_file):
        import json
        anomalies = generate_mock_logs(log_file, num_lines=100000)
        with open(truth_file, 'w') as f:
            json.dump(anomalies, f, indent=2)
    else:
        print(f"Using existing mock data: {log_file}")
        
    # 2. Throughput Benchmark
    print("\n[2/4] Running Throughput Benchmark...")
    throughput_results = run_throughput_benchmark(log_file)
    
    # 3. Retrieval Benchmark
    print("\n[3/4] Running Top-3 Retrieval Accuracy Benchmark...")
    retrieval_results = run_retrieval_benchmark(log_file, truth_file)
    
    # 4. RCA Time Benchmark
    print("\n[4/4] Running RCA Time Simulator Benchmark...")
    rca_results = run_rca_time_benchmark(log_file)
    
    print("\n" + "="*50)
    print("                 BENCHMARK REPORT")
    print("="*50)
    
    if throughput_results:
        print("\n## 1. Processing Throughput (100K+ Logs)")
        print(f"- Total Events Processed: {throughput_results['num_events']}")
        print(f"- File Size: {throughput_results['file_size_mb']:.2f} MB")
        print(f"- Parse Time: {throughput_results['parse_time']:.2f}s")
        print(f"- Anomaly Detection Time: {throughput_results['detect_time']:.2f}s")
        print(f"- Overall Processing Time: {throughput_results['total_time']:.2f}s")
        print(f"- Overall Throughput: {throughput_results['total_throughput']:.2f} events/sec")
    
    if retrieval_results:
        print("\n## 2. Top-3 Retrieval Accuracy")
        if retrieval_results.get("status") == "skipped":
            print("- Status: Skipped (Missing API Key)")
        else:
            print(f"- Total Test Queries: {retrieval_results['total_queries']}")
            print(f"- Successful Top-3 Hits: {retrieval_results['correct_top3']}")
            print(f"- Accuracy: {retrieval_results['top_3_accuracy']:.2f}%")
            
    if rca_results:
        print("\n## 3. RCA Investigation Time")
        if rca_results.get("status") == "skipped":
            print("- Status: Skipped (Missing API Key)")
        elif rca_results.get("status") == "no_anomalies":
            print("- Status: Skipped (No anomalies found)")
        elif rca_results.get("status") == "failed":
            print("- Status: Failed to generate RCA")
        else:
            print(f"- Manual Baseline Assumption: {rca_results['manual_baseline_s']}s")
            print(f"- AI Generation Time: {rca_results['ai_rca_time_s']:.2f}s")
            print(f"- Investigation Time Reduced By: {rca_results['reduction_percentage']:.2f}%")
            
    print("\n" + "="*50)

if __name__ == "__main__":
    main()
