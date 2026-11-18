"""Conservative streaming parser. Ambiguous plain messages are preserved."""
import hashlib
import io
import json
import re
from datetime import datetime, timezone
from typing import Iterable, Iterator
from src.schemas import ParsedLogEvent

LEVELS = r"INFO|WARNING|WARN|ERROR|FATAL|DEBUG|TRACE|CRITICAL"
ISO = re.compile(
    rf"^(?:\[?(?P<before>{LEVELS})\]?\s+)?"
    r"(?P<ts>\d{4}-\d{2}-\d{2}[ T]\d{2}:\d{2}:\d{2}(?:[.,]\d+)?(?:Z|[+-]\d{2}:?\d{2})?)\s+"
    rf"(?:\[?(?P<after>{LEVELS})\]?\s+)?(?P<body>.*)$", re.I)
HDFS = re.compile(rf"^(?P<ts>\d{{6}} \d{{6}})\s+\d+\s+(?P<level>{LEVELS})\s+(?P<service>\S+):\s*(?P<body>.*)$", re.I)
CONTINUATION = re.compile(r'^\s+|^Traceback \(|^Caused by:|^During handling|^[\w.]+(?:Error|Exception):|^\.{3} \d+ more')


def normalize_timestamp(value: str) -> str:
    dt = datetime.fromisoformat(value.replace('Z', '+00:00').replace(',', '.'))
    if dt.tzinfo:
        dt = dt.astimezone(timezone.utc).replace(tzinfo=None)
    return dt.isoformat(sep=' ')


def _parse(line: str, number: int, source_id: str) -> ParsedLogEvent:
    timestamp, level, service, message, warning = 'UNKNOWN', 'UNKNOWN', '', line, ''
    try:
        if line.lstrip().startswith('{'):
            obj = json.loads(line)
            if not isinstance(obj, dict):
                raise ValueError('JSON record must be an object')
            timestamp = normalize_timestamp(str(obj.get('timestamp', obj.get('time', ''))))
            level = str(obj.get('level', obj.get('severity', 'UNKNOWN'))).upper()
            service = str(obj.get('service', obj.get('service_name', '')))
            message = str(obj.get('message', obj.get('msg', '')))
        elif match := HDFS.match(line):
            timestamp = datetime.strptime(match['ts'], '%y%m%d %H%M%S').isoformat(sep=' ')
            level, service, message = match['level'].upper(), match['service'], match['body']
        elif match := ISO.match(line):
            timestamp = normalize_timestamp(match['ts'])
            level = (match['after'] or match['before'] or 'UNKNOWN').upper()
            message = match['body']
            # Only explicit service syntax is consumed; a bare first word is ambiguous.
            service_match = re.match(r'^(?:\[(?P<bracket>[^\]]+)\]|(?P<colon>[\w.$-]+):|(?P<named>[\w.$]+[-_][\w.$-]+))\s+(?P<msg>.*)$', message)
            if service_match:
                service = service_match['bracket'] or service_match['colon'] or service_match['named']
                message = service_match['msg']
        else:
            warning = 'Unsupported record format'
        if level == 'WARNING':
            level = 'WARN'
        if level not in LEVELS.split('|'):
            level = 'UNKNOWN'
            warning = warning or 'Missing or unsupported severity'
    except (ValueError, TypeError, OverflowError):
        timestamp, level, service, message = 'UNKNOWN', 'UNKNOWN', '', line
        warning = 'Invalid JSON or timestamp'
    rid = hashlib.sha256(f'{source_id}:{number}:{line}'.encode()).hexdigest()[:20]
    return ParsedLogEvent(timestamp=timestamp, level=level, service=service,
        message=message, raw_line=line, record_id=rid, line_number=number, parse_warning=warning)


def iter_log_events(lines: Iterable[str], source_id: str = '') -> Iterator[ParsedLogEvent]:
    pending = None
    for number, raw in enumerate(lines, 1):
        line = raw.rstrip('\r\n')
        if not line.strip():
            continue
        event = _parse(line, number, source_id)
        if pending is not None and event.parse_warning == 'Unsupported record format' and CONTINUATION.match(line):
            pending.message += '\n' + line
            pending.raw_line += '\n' + line
        else:
            if pending is not None:
                yield pending
            pending = event
    if pending is not None:
        yield pending


def parse_log_text(raw_text: str, source_id: str = '') -> list[ParsedLogEvent]:
    return list(iter_log_events(io.StringIO(raw_text), source_id))
