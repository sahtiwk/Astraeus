"""Measure local generation latency, never human investigation speedup."""
import os
import sys
import time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.parser import parse_log_text
from src.anomaly import detect_anomalies
from src.llm_analysis import generate_rca


def run_rca_time_benchmark(log_file: str):
    if os.getenv("ASTRAEUS_RUN_RCA_BENCHMARK") != "1":
        return {"status": "skipped"}
    from itertools import islice
    with open(log_file, encoding="utf-8") as stream:
        events = parse_log_text("".join(islice(stream, 20000)))
    anomalies = detect_anomalies(events)
    if not anomalies:
        return {"status": "no_anomalies"}
    start = time.perf_counter()
    try:
        generate_rca(anomalies[0])
        return {"status": "success", "ai_rca_time_s": time.perf_counter() - start}
    except Exception:
        return {"status": "failed"}
