import os
import random
from datetime import datetime, timedelta

LOG_LEVELS = ["INFO", "DEBUG", "WARN"]
SERVICES = ["auth-service", "payment-api", "user-db", "frontend-app", "background-worker"]

NORMAL_MESSAGES = [
    "User login successful",
    "Processing payment request",
    "Database connection established",
    "Serving static assets",
    "Worker heartbeat received",
    "Cache hit for user profile",
    "Starting background job",
    "Job completed successfully"
]

ANOMALY_SCENARIOS = [
    {
        "type": "database_timeout",
        "messages": [
            "[ERROR] user-db Connection timeout while waiting for pool",
            "[ERROR] user-db Failed to execute query: timeout",
            "[ERROR] user-db exception in database thread",
            "[ERROR] auth-service traceback: user profile not found due to db error",
            "[ERROR] auth-service User login failed due to db connection refused"
        ]
    },
    {
        "type": "memory_leak",
        "messages": [
            "[WARN] payment-api Memory usage above 80%",
            "[WARN] payment-api Memory usage above 90%",
            "[ERROR] payment-api oom killer invoked",
            "[ERROR] payment-api nullpointerexception during heap allocation",
            "[FATAL] payment-api Service crashed due to exception"
        ]
    }
]

def generate_log_line(timestamp, level=None, service=None, message=None, rng=None):
    rng = rng or random
    if level is None:
        level = rng.choices(LOG_LEVELS, weights=[0.7, 0.2, 0.1])[0]
    if service is None:
        service = rng.choice(SERVICES)
    if message is None:
        message = rng.choice(NORMAL_MESSAGES)
    
    return f"{timestamp.strftime('%Y-%m-%d %H:%M:%S')} [{level}] {service} {message}"

def generate_mock_logs(output_file: str, num_lines: int = 100000, anomaly_frequency: int = 5000, seed: int = 42):
    """Generates synthetic logs and saves them to a file."""
    if num_lines < 0 or anomaly_frequency <= 0:
        raise ValueError("Invalid generator parameters")
    rng = random.Random(seed)
    os.makedirs(os.path.dirname(output_file) or ".", exist_ok=True)
    
    current_time = datetime(2026, 1, 1, 0, 0, 0)
    
    ground_truth_anomalies = []
    
    actual_line = 0
    with open(output_file, 'w', encoding='utf-8') as f:
        for i in range(1, num_lines + 1):
            if i % anomaly_frequency == 0:
                scenario = rng.choice(ANOMALY_SCENARIOS)
                start_ts = current_time.strftime('%Y-%m-%d %H:%M:%S')
                
                start_line = actual_line + 1
                # Inject a cluster of errors (an anomaly window)
                for msg in scenario["messages"]:
                    current_time += timedelta(milliseconds=rng.randint(10, 500))
                    # Extract level and service from predefined msg
                    parts = msg.split(" ", 2)
                    level = parts[0].strip("[]")
                    service = parts[1]
                    text = parts[2]
                    
                    line = generate_log_line(current_time, level, service, text, rng=rng)
                    f.write(line + "\n")
                    actual_line += 1
                    if actual_line == start_line:
                        start_ts = current_time.strftime("%Y-%m-%d %H:%M:%S")
                    
                end_ts = current_time.strftime('%Y-%m-%d %H:%M:%S')
                ground_truth_anomalies.append({
                    "start_line": start_line,
                    "end_line": actual_line,
                    "type": scenario["type"],
                    "start_ts": start_ts,
                    "end_ts": end_ts
                })
            else:
                line = generate_log_line(current_time, rng=rng)
                f.write(line + "\n")
                actual_line += 1
                
            current_time += timedelta(milliseconds=rng.randint(100, 1000))
            
    return ground_truth_anomalies

if __name__ == "__main__":
    import json
    print("Generating 100K synthetic logs...")
    test_dir = os.path.dirname(os.path.abspath(__file__))
    log_file = os.path.join(test_dir, "test_100k.log")
    truth_file = os.path.join(test_dir, "ground_truth.json")
    
    anomalies = generate_mock_logs(log_file, num_lines=100000)
    
    with open(truth_file, 'w') as f:
        json.dump(anomalies, f, indent=2)
        
    print(f"Generated {log_file} with {len(anomalies)} injected anomalies.")
    print(f"Ground truth saved to {truth_file}.")
