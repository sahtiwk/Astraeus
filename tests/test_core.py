import json
import pytest
from pydantic import ValidationError
from src.parser import parse_log_text
from src.anomaly import detect_anomalies
from src.pipeline import ingest, decode_bytes
from src.schemas import RCAResponse
from src.privacy import redact


def test_timezone_and_service_less_message():
    event=parse_log_text('2026-05-29T10:00:00+02:00 ERROR Connection timeout')[0]
    assert event.timestamp=='2026-05-29 08:00:00'
    assert event.level=='ERROR'
    assert event.service==''
    assert event.message=='Connection timeout'


def test_json_lines_remain_separate():
    line=json.dumps(dict(timestamp='2026-05-29T10:00:00Z',level='ERROR',service='api',message='failure'))
    events=parse_log_text(line+'\n'+line)
    assert len(events)==2
    assert events[0].service=='api'
    assert events[0].record_id!=events[1].record_id


def test_invalid_records_are_visible_not_tracebacks():
    events=parse_log_text('2026-02-30 10:00:00 ERROR broken\nrandom text\n{invalid json}')
    assert len(events)==3
    assert all(e.parse_warning for e in events)


def test_multiline_and_hdfs():
    events=parse_log_text('081109 203615 148 ERROR dfs.DataNode: failed\n    at example\nValueError: bad\n081109 203616 148 INFO dfs.DataNode: ok')
    assert len(events)==2
    assert 'ValueError: bad' in events[0].message
    assert events[0].timestamp=='2008-11-09 20:36:15'


def test_service_names_and_critical_detection():
    events=parse_log_text('2026-05-29T10:00:00Z CRITICAL api-service Service unavailable')
    chunks=detect_anomalies(events)
    assert events[0].service=='api-service'
    assert len(chunks)==1 and chunks[0].severity=='HIGH'


def test_benign_info_keywords_do_not_trigger():
    events=parse_log_text('2026-05-29 10:00:00 INFO No exception; timeout and failed counters are zero')
    assert not detect_anomalies(events)


def test_groups_services_and_time_without_overlap():
    raw='\n'.join(['2026-05-29 10:00:00 ERROR api-service timeout',
                   '2026-05-29 10:00:01 ERROR api-service failed',
                   '2026-05-29 10:00:02 ERROR db-service failed',
                   '2026-05-29 10:02:00 ERROR api-service failed'])
    chunks=detect_anomalies(parse_log_text(raw))
    assert len(chunks)==3
    ids=[rid for c in chunks for rid in c.record_ids]
    assert len(ids)==len(set(ids))==4
    assert chunks==detect_anomalies(parse_log_text(raw))


@pytest.mark.parametrize('kwargs',[{'window_size':0},{'step_size':-1},{'score_threshold':0}])
def test_invalid_parameters(kwargs):
    with pytest.raises(ValueError):
        detect_anomalies([],**kwargs)


def test_redaction_at_ingest_boundary():
    state=ingest(b'2026-05-29 10:00:00 ERROR api-service timeout api_key=abc123 email=alice@example.com ip=10.0.0.1')
    text=state['anomalies'][0].chunk_text
    assert 'abc123' not in text and 'alice@example.com' not in text and '10.0.0.1' not in text
    assert '[REDACTED]' in text
    assert 'abc123' not in str(state['preview'])


def test_empty_and_utf16_inputs():
    with pytest.raises(ValueError): ingest(b'')
    assert decode_bytes('hello'.encode('utf-16'))=='hello'


def test_schema_rejects_invalid_output():
    data=dict(summary='x',probable_root_cause='x',confidence=0.5,severity='HIGH',affected_component='api',evidence_lines=['x'],recommended_actions=[])
    for change in [dict(confidence=9),dict(confidence=float('nan')),dict(severity='BANANA')]:
        with pytest.raises(ValidationError): RCAResponse(**(data|change))


def test_long_running_errors_do_not_merge_indefinitely():
    raw='\n'.join(f'2026-05-29 10:{minute:02}:00 ERROR api-service failed' for minute in range(5))
    assert len(detect_anomalies(parse_log_text(raw)))==3


def test_folder_import_keeps_files_separate_and_skips_duplicates(tmp_path):
    from src.pipeline import ingest_folder
    raw=b'2026-05-29 10:00:00 ERROR api-service failure'
    (tmp_path/'a.log').write_bytes(raw);(tmp_path/'b.log').write_bytes(raw)
    (tmp_path/'c.log').write_bytes(b'2026-05-29 10:00:01 ERROR db-service failure')
    result=ingest_folder(tmp_path)
    assert result['counts']['events']==2
    assert len(result['source_ids'])==2 and len(result['anomalies'])==2


def test_folder_requires_explicit_path():
    import pytest
    from src.pipeline import ingest_folder
    with pytest.raises(ValueError):ingest_folder('')
