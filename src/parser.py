import re
from typing import List
from src.schemas import ParsedLogEvent

LOG_LEVELS = r"(INFO|WARN|WARNING|ERROR|FATAL|DEBUG|TRACE|CRITICAL)"
LOG_PATTERN = re.compile(
    rf"^(?:\[?(?P<level1>{LOG_LEVELS})\]?\s*)?"
    r"(?P<timestamp>\d{4}-\d{2}-\d{2}[ T]\d{2}:\d{2}:\d{2}(?:\.\d+)?)\s*"
    rf"(?:\[?(?P<level2>{LOG_LEVELS})\]?\s+)?"
    r"(?:(?P<service>[a-zA-Z0-9_-]+)\s+)?"
    r"(?P<message>.*)$",
    re.IGNORECASE
)

def parse_log_text(raw_text: str) -> List[ParsedLogEvent]:
    events: List[ParsedLogEvent] = []
    
    for line in raw_text.splitlines():
        if not line.strip():
            continue
            
        match = LOG_PATTERN.match(line)
        if match:
            level = match.group("level1") or match.group("level2")
            if level:
                level = level.upper()
                if level == "WARNING":
                    level = "WARN"
            else:
                level = "UNKNOWN"
                
            timestamp = match.group("timestamp")
            service = match.group("service") or ""
            message = match.group("message") or ""
            
            events.append(ParsedLogEvent(
                timestamp=timestamp,
                level=level,
                service=service,
                message=message,
                raw_line=line
            ))
        else:
            if events:
                events[-1].message += "\n" + line
                events[-1].raw_line += "\n" + line
            else:
                events.append(ParsedLogEvent(
                    timestamp="UNKNOWN",
                    level="UNKNOWN",
                    service="",
                    message=line,
                    raw_line=line
                ))
                
    return events
