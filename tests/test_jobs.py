import json
from unittest.mock import Mock
from src.jobs import JobStore,JobManager
from src.schemas import RCAResponse
from src.reports import ReportStore


def report():
    return RCAResponse(summary='test',probable_root_cause='unknown',confidence=0,severity='LOW',affected_component='api',evidence_lines=['evidence'],recommended_actions=[])


def test_jobs_deduplicate_redact_and_complete_atomically(tmp_path):
    path=tmp_path/'jobs.db';store=JobStore(path)
    jid=store.submit('key',{'text':'password=private'})
    assert store.submit('key',{})==jid
    assert 'private' not in store.get(jid)['request']
    assert not store.complete(jid,report())
    with store.connect() as con:con.execute("UPDATE jobs SET status='running' WHERE id=?",(jid,))
    assert store.complete(jid,report())
    assert JobStore(path).get(jid)['status']=='completed'
    assert ReportStore(path).get('key')==report()


def test_cancel_prevents_late_result_and_allows_retry(tmp_path):
    manager=JobManager(tmp_path/'jobs.db');jid=manager.store.submit('key',{})
    manager.cancel(jid)
    assert manager.store.get(jid)['status']=='cancelled'
    assert not manager.store.complete(jid,report())
    assert manager.store.submit('key',{})!=jid


def test_recover_dead_worker_without_reexecution(tmp_path):
    manager=JobManager(tmp_path/'jobs.db');jid=manager.store.submit('key',{})
    with manager.store.connect() as con:con.execute("UPDATE jobs SET status='running',pid=0 WHERE id=?",(jid,))
    manager.poll()
    assert manager.store.get(jid)['status']=='interrupted'
    assert ReportStore(manager.store.path).get('key') is None


def test_worker_persists_result_without_ui(tmp_path,monkeypatch):
    from src.job_worker import execute
    path=tmp_path/'jobs.db';store=JobStore(path)
    payload={'anomaly':dict(chunk_id='c',start_ts='x',end_ts='y',severity='LOW',keywords=[],chunk_text='evidence'),'history':[],'endpoint':'http://127.0.0.1:8080/v1','model':'local'}
    jid=store.submit('key',payload)
    monkeypatch.setattr('src.job_worker.generate_rca',lambda *a,**k:report())
    execute(path,jid)
    assert JobStore(path).get(jid)['status']=='completed'
    assert ReportStore(path).get('key')==report()


def test_transport_endpoint_is_validated_not_redacted(tmp_path):
    store=JobStore(tmp_path/'jobs.db')
    jid=store.submit('key',{'endpoint':'http://127.0.0.1:8080/v1','text':'client 10.0.0.1'})
    saved=json.loads(store.get(jid)['request'])
    assert saved['endpoint']=='http://127.0.0.1:8080/v1'
    assert '10.0.0.1' not in saved['text']
    import pytest
    with pytest.raises(ValueError):store.submit('remote',{'endpoint':'https://example.com'})
