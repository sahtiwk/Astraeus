from pydantic import BaseModel
from typing import List

class ParsedLogEvent(BaseModel):
    timestamp: str
    level: str
    service: str
    message: str
    raw_line: str

class AnomalyChunk(BaseModel):
    chunk_id: str
    start_ts: str
    end_ts: str
    severity: str
    keywords: List[str]
    chunk_text: str

class RCAResponse(BaseModel):
    summary: str
    probable_root_cause: str
    confidence: float
    severity: str
    affected_component: str
    evidence_lines: List[str]
    recommended_actions: List[str]
