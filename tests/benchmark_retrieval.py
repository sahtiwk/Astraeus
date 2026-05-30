import os
import sys
import json
import uuid
import tempfile
import time
from datetime import datetime

# Add project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.parser import parse_log_text
from src.anomaly import detect_anomalies
from src.vector_store import VectorStore

def run_retrieval_benchmark(log_file: str, truth_file: str):
    print("--- Running Retrieval Accuracy Benchmark ---")
    
    if not os.path.exists(log_file) or not os.path.exists(truth_file):
        print("Error: Missing mock data files. Run generate_mock_data.py first.")
        return None
        
    with open(log_file, 'r', encoding='utf-8') as f:
        raw_text = f.read()
        
    with open(truth_file, 'r', encoding='utf-8') as f:
        ground_truth = json.load(f)
        
    print("Parsing logs and detecting anomalies...")
    events = parse_log_text(raw_text)
    anomalies = detect_anomalies(events)
    print(f"Detected {len(anomalies)} anomalies to index.")
    
    # Create a temporary VectorStore
    temp_dir = tempfile.mkdtemp()
    test_db_path = os.path.join(temp_dir, "chromadb_test")
    vs = VectorStore(db_path=test_db_path)
    
    # Match detected anomalies to ground truth to get their "types"
    def parse_time(ts_str):
        return datetime.strptime(ts_str, '%Y-%m-%d %H:%M:%S')

    anomaly_types = {}
    for anomaly in anomalies:
        a_start = parse_time(anomaly.start_ts)
        a_end = parse_time(anomaly.end_ts)
        
        assigned_type = "unknown"
        for gt in ground_truth:
            gt_start = parse_time(gt["start_ts"])
            gt_end = parse_time(gt["end_ts"])
            
            if a_start <= gt_end and a_end >= gt_start:
                assigned_type = gt["type"]
                break
                
        anomaly_types[anomaly.chunk_id] = assigned_type

    print(f"Mapped anomalies to {len(set(anomaly_types.values()))} ground truth types.")

    print("Indexing anomalies into local Vector Store...")
    start_time = time.time()
    vs.index_anomaly_chunks(anomalies)
    index_time = time.time() - start_time
    print(f"Indexing completed in {index_time:.2f} seconds.")
    


    # Calculate Top-3 Accuracy
    print("Evaluating Top-3 Accuracy...")
    correct_top3 = 0
    total_queries = 0
    
    for anomaly in anomalies:
        query_type = anomaly_types.get(anomaly.chunk_id, "unknown")
        if query_type == "unknown":
            continue
            
        # We only evaluate if there is at least one other anomaly of the same type
        same_type_count = sum(1 for v in anomaly_types.values() if v == query_type)
        if same_type_count <= 1:
            continue
            
        total_queries += 1
        
        try:
            # Query Top-4 since the query itself might be returned as Top 1
            results = vs.query_similar_anomalies(anomaly.chunk_text, limit=4)
            
            # Remove the query anomaly itself
            filtered_results = [r for r in results if r.chunk_id != anomaly.chunk_id]
            top_3 = filtered_results[:3]
            
            # Check if any of the top-3 results share the same type
            hit = False
            for res in top_3:
                res_type = anomaly_types.get(res.chunk_id)
                if res_type == query_type:
                    hit = True
                    break
                    
            if hit:
                correct_top3 += 1
        except Exception as e:
            print(f"Query failed: {e}")
            
    accuracy = (correct_top3 / total_queries) * 100 if total_queries > 0 else 0
    print(f"\n--- Top-3 Retrieval Accuracy: {accuracy:.2f}% ({correct_top3}/{total_queries}) ---")
    
    return {
        "index_time": index_time,
        "total_queries": total_queries,
        "correct_top3": correct_top3,
        "top_3_accuracy": accuracy
    }

if __name__ == "__main__":
    test_dir = os.path.dirname(os.path.abspath(__file__))
    log_file = os.path.join(test_dir, "test_100k.log")
    truth_file = os.path.join(test_dir, "ground_truth.json")
    run_retrieval_benchmark(log_file, truth_file)
