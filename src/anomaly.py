"""Deterministic severity-based detection with bounded incident groups."""
import hashlib
from datetime import datetime
from typing import Iterable
from src.schemas import AnomalyChunk, ParsedLogEvent

CRITICAL_KEYWORDS = ['timeout', 'failed', 'traceback', 'connection refused', 'nullpointerexception', 'oom', 'exception']


def detect_anomalies(events: Iterable[ParsedLogEvent], window_size: int = 50,
                     step_size: int = 25, score_threshold: int = 15,
                     source_id: str = '', max_gap_seconds: int = 60) -> list[AnomalyChunk]:
    # step_size is retained for benchmark compatibility; overlapping windows are gone.
    if min(window_size, step_size, score_threshold, max_gap_seconds) <= 0:
        raise ValueError('Detection parameters must be positive')
    groups = {}
    chunks = []

    def finish(group):
        if not group:
            return
        keywords = sorted({k for e in group for k in CRITICAL_KEYWORDS if k in e.message.lower()})
        critical = any(e.level in ('FATAL', 'CRITICAL') for e in group)
        errors = sum(e.level == 'ERROR' for e in group)
        # INFO keywords do not trigger incidents. WARN requires a meaningful keyword.
        score = sum(15 if e.level == 'ERROR' else 3 for e in group) + 5 * len(keywords)
        if not critical and score < score_threshold:
            return
        severity = 'HIGH' if critical or errors >= 3 else 'MEDIUM' if errors else 'LOW'
        text = '\n'.join(f'[{e.level}] {e.service} {e.message}'.strip() for e in group)
        identity = source_id + '\n' + '\n'.join(f'{e.record_id}:{e.timestamp}:{e.raw_line}' for e in group)
        chunks.append(AnomalyChunk(chunk_id=hashlib.sha256(identity.encode()).hexdigest(),
            start_ts=group[0].timestamp, end_ts=group[-1].timestamp, severity=severity,
            keywords=keywords, chunk_text=text, source_id=source_id,
            record_ids=[e.record_id for e in group if e.record_id]))

    for event in events:
        if event.level not in ('ERROR', 'FATAL', 'CRITICAL', 'WARN'):
            continue
        if event.level == 'WARN' and not any(k in event.message.lower() for k in CRITICAL_KEYWORDS):
            continue
        group = groups.setdefault(event.service, [])
        if group:
            try:
                current = datetime.fromisoformat(event.timestamp)
                gap = (current - datetime.fromisoformat(group[-1].timestamp)).total_seconds()
                span = (current - datetime.fromisoformat(group[0].timestamp)).total_seconds()
            except ValueError:
                gap = span = max_gap_seconds + 1
            if len(group) >= window_size or gap < 0 or gap > max_gap_seconds or span > max_gap_seconds:
                finish(group)
                group = groups[event.service] = []
        group.append(event)
    for group in groups.values():
        finish(group)
    order = {'HIGH': 0, 'MEDIUM': 1, 'LOW': 2}
    return sorted(chunks, key=lambda c: (order[c.severity], c.start_ts, c.chunk_id))
