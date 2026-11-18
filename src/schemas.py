from typing import Literal
from pydantic import BaseModel, Field

class ParsedLogEvent(BaseModel):
    timestamp: str
    level: str
    service: str
    message: str
    raw_line: str
    record_id: str = ""
    line_number: int = 0
    parse_warning: str = ""

class AnomalyChunk(BaseModel):
    chunk_id: str
    start_ts: str
    end_ts: str
    severity: Literal["LOW", "MEDIUM", "HIGH"]
    keywords: list[str]
    chunk_text: str
    source_id: str = ""
    record_ids: list[str] = Field(default_factory=list)

class RCAResponse(BaseModel):
    summary: str
    probable_root_cause: str
    confidence: float = Field(ge=0, le=1)
    severity: Literal["LOW", "MEDIUM", "HIGH"]
    affected_component: str
    evidence_lines: list[str]
    recommended_actions: list[str]
