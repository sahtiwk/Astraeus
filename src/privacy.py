"""Best-effort redaction, not a guarantee of complete PII detection."""
import re

PATTERNS = [
    (re.compile(r'(?i)\b(bearer\s+)[A-Za-z0-9._~+/-]+=*'), r'\1[REDACTED]'),
    (re.compile(r'(?i)(\b(?:api[_-]?key|token|password|secret)\b["\x27]?\s*[:=]\s*["\x27]?)[^\s,"\x27;]+'), r'\1[REDACTED]'),
    (re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b'), '[EMAIL]'),
    (re.compile(r'\b(?:\d{1,3}\.){3}\d{1,3}\b'), '[IP]'),
]


def redact(text: str) -> str:
    for pattern, replacement in PATTERNS:
        text = pattern.sub(replacement, text)
    return text
