from unittest.mock import Mock
from streamlit.testing.v1 import AppTest
from src.pipeline import ingest


def test_ui_no_model_no_network_and_reruns(tmp_path,monkeypatch):
    import app
    import socket
    monkeypatch.setattr(socket, 'create_connection', Mock(side_effect=AssertionError('Network forbidden')))
    vectors=Mock()
    reports=Mock()
    reports.get.return_value=None
    monkeypatch.setattr(app,'stores',lambda path:(vectors,reports))
    jobs=Mock();jobs.store.latest.return_value=None
    monkeypatch.setattr(app,'job_manager',lambda path:jobs)
    at=AppTest.from_string('import app; app.main()').run()
    assert not at.exception
    assert not any('Gemini' in x.value for x in at.text_input)
    state=ingest(b'2026-05-29 10:00:00 ERROR api-service timeout')
    state.update(indexed=False,history={})
    at.session_state['analysis']=state
    at.run()
    assert not at.exception
    at.run()
    vectors.index_anomaly_chunks.assert_not_called()
    vectors.query_similar_anomalies.assert_not_called()
    vectors.index_anomaly_chunks.return_value=Mock(indexed=1,failed=[])
    next(b for b in at.button if b.label=='Save incidents to local history').click().run()
    assert not at.exception
    at.run()
    assert vectors.index_anomaly_chunks.call_count==1
    vectors.query_similar_anomalies.return_value=[]
    next(b for b in at.button if b.label=='Find historical incidents').click().run()
    assert not at.exception
    assert vectors.query_similar_anomalies.call_args.kwargs['exclude_source_id']==state['source_id']



def test_cancel_running_job_from_ui(monkeypatch):
    import app
    reports=Mock();reports.get.return_value=None
    jobs=Mock();jobs.store.latest.return_value={'id':'job1','status':'running','error':None}
    monkeypatch.setattr(app,'stores',lambda path:(Mock(),reports))
    monkeypatch.setattr(app,'job_manager',lambda path:jobs)
    at=AppTest.from_string('import app; app.main()').run()
    state=ingest(b'2026-05-29 10:00:00 ERROR api-service timeout')
    state.update(indexed=True,history={})
    at.session_state['analysis']=state
    at.run()
    next(b for b in at.button if b.label=='Cancel diagnosis').click().run()
    assert not at.exception
    jobs.cancel.assert_called_once_with('job1')
