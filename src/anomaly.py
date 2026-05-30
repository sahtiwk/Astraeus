import uuid
from typing import List, Tuple
from src.schemas import ParsedLogEvent, AnomalyChunk

CRITICAL_KEYWORDS = [
    "timeout", "failed", "traceback", "connection refused", 
    "nullpointerexception", "oom", "exception"
]

def detect_anomalies(
    events: List[ParsedLogEvent], 
    window_size: int = 50, 
    step_size: int = 25,
    score_threshold: int = 15
) -> List[AnomalyChunk]:
    
    anomalies_with_score: List[Tuple[int, AnomalyChunk]] = []
    
    if len(events) < window_size:
        window_size = max(len(events), 1)
        step_size = window_size
        
    for i in range(0, len(events), step_size):
        window_events = events[i : i + window_size]
        if not window_events:
            break
            
        score = 0
        error_count = 0
        found_keywords = set()
        
        start_ts = window_events[0].timestamp
        end_ts = window_events[-1].timestamp
        
        for event in window_events:
            if event.level in ["ERROR", "FATAL", "CRITICAL"]:
                score += 10
                error_count += 1
            elif event.level == "WARN":
                score += 3
                
            lower_msg = event.message.lower()
            for kw in CRITICAL_KEYWORDS:
                if kw in lower_msg:
                    score += 5
                    found_keywords.add(kw)
                    
        if error_count >= 3:
            score += 20
            found_keywords.add("repeated failures")
            
        if score >= score_threshold:
            if score >= 50:
                severity = "HIGH"
            elif score >= 25:
                severity = "MEDIUM"
            else:
                severity = "LOW"
                
            # Filter out normal logs and strip timestamps to create a highly focused semantic signature
            relevant_logs = [e for e in window_events if e.level in ["WARN", "ERROR", "FATAL", "CRITICAL"]]
            if not relevant_logs:
                relevant_logs = window_events
                
            chunk_text = "\n".join([f"[{e.level}] {e.service} {e.message}" for e in relevant_logs])
            
            import hashlib
            # Make sure chunk_id is unique even if the text signature is identical
            chunk_hash = hashlib.md5(f"{start_ts}_{chunk_text}".encode('utf-8')).hexdigest()
            
            chunk = AnomalyChunk(
                chunk_id=chunk_hash,
                start_ts=start_ts,
                end_ts=end_ts,
                severity=severity,
                keywords=list(found_keywords),
                chunk_text=chunk_text
            )
            anomalies_with_score.append((score, chunk))
            
    anomalies_with_score.sort(key=lambda x: x[0], reverse=True)
    
    return [chunk for score, chunk in anomalies_with_score]
