"""Bounded ingestion shared by the UI and tests."""
import hashlib
import io
from src.parser import iter_log_events
from src.anomaly import detect_anomalies
from src.privacy import redact

MAX_BYTES = 50 * 1024 * 1024
MAX_EVENTS = 500000


def decode_bytes(data: bytes) -> str:
    if not data or len(data) > MAX_BYTES:
        raise ValueError('Choose a nonempty file no larger than 50 MB')
    if data.startswith((b'\xff\xfe', b'\xfe\xff')):
        return data.decode('utf-16')
    try:
        return data.decode('utf-8-sig')
    except UnicodeDecodeError:
        return data.decode('latin-1')


def ingest(data: bytes):
    source_id=hashlib.sha256(data).hexdigest()
    text=decode_bytes(data)
    preview=[]
    warnings=[]
    counts={'events':0, 'warnings':0}
    def events():
        for event in iter_log_events(io.StringIO(text),source_id):
            counts['events'] += 1
            if counts['events'] > MAX_EVENTS:
                raise ValueError('File exceeds 500,000 events; split it before importing')
            if len(event.message) > 65536:
                raise ValueError('A log record exceeds 64 KB; split or trim oversized records')
            if event.parse_warning:
                counts['warnings'] += 1
                if len(warnings)<20:
                    warnings.append(f'Line {event.line_number}: {event.parse_warning}')
            event.message=redact(event.message)
            event.raw_line=redact(event.raw_line)
            if len(preview)<50:
                preview.append(event.model_dump())
            yield event
    chunks=detect_anomalies(events(),source_id=source_id)
    return dict(source_id=source_id, preview=preview, warnings=warnings,
                counts=counts, anomalies=chunks)


def ingest_folder(folder):
    from pathlib import Path
    if not str(folder).strip():raise ValueError('Enter a local folder path')
    root=Path(folder).expanduser().resolve()
    if not root.is_dir():raise ValueError('Choose an existing local folder')
    paths=[];size=0
    for path in root.rglob('*'):
        if path.suffix.lower() not in ('.log','.txt','.jsonl') or not path.is_file():continue
        if not path.resolve().is_relative_to(root):raise ValueError('A file points outside the selected folder')
        paths.append(path);size+=path.stat().st_size
        if len(paths)>50 or size>MAX_BYTES:raise ValueError('Folder import supports up to 50 files and 50 MB total')
    if not paths:raise ValueError('No supported log files found')
    result={'source_ids':[],'preview':[],'warnings':[],'counts':{'events':0,'warnings':0},'anomalies':[]}
    for path in sorted(paths):
        if path.stat().st_size==0:continue
        data=ingest(path.read_bytes())
        if data['source_id'] in result['source_ids']:continue
        result['source_ids'].append(data['source_id'])
        result['counts']['events']+=data['counts']['events'];result['counts']['warnings']+=data['counts']['warnings']
        if result['counts']['events']>MAX_EVENTS:raise ValueError('Folder exceeds 500,000 events')
        result['preview'].extend(data['preview'][:max(0,50-len(result['preview']))])
        result['warnings'].extend([f'{path.name}: {w}' for w in data['warnings']][:max(0,20-len(result['warnings']))])
        result['anomalies'].extend(data['anomalies'])
    result['source_id']=hashlib.sha256(''.join(result['source_ids']).encode()).hexdigest()
    return result
