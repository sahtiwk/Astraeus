import json
from unittest.mock import Mock
import pytest
from src.anomaly import detect_anomalies
from src.parser import parse_log_text
from src.llm_analysis import generate_rca, validate_endpoint, build_context
from src.reports import ReportStore, report_key
from src.schemas import RCAResponse

@pytest.fixture
def chunk():
    return detect_anomalies(parse_log_text('2026-05-29 10:00:00 ERROR api-service timeout api_key=secret-value'))[0]

@pytest.mark.parametrize('url',['https://example.com/v1','http://localhost.evil/v1','http://127.0.0.1@evil/v1','http://127.0.0.1/v1?url=evil','http://localhost:8080/v1','http://192.168.1.2/v1'])
def test_refuses_non_loopback_or_ambiguous_urls(url):
    with pytest.raises(ValueError): validate_endpoint(url)


def test_local_generation_validates_and_redacts(monkeypatch,chunk):
    context,evidence=build_context(chunk)
    report=dict(summary='timeout',probable_root_cause='Insufficient evidence; investigate pool usage',confidence=0.3,severity='MEDIUM',affected_component='api',evidence_lines=evidence,recommended_actions=['Check pool metrics'])
    session=Mock()
    session.__enter__=Mock(return_value=session)
    session.__exit__=Mock(return_value=False)
    response=session.post.return_value
    response.status_code=200
    response.json.return_value={'choices':[{'message':{'content':json.dumps(report)}}]}
    monkeypatch.setattr('src.llm_analysis.requests.Session',lambda:session)
    result=generate_rca(chunk)
    assert result.confidence==0.3
    assert session.trust_env is False
    sent=session.post.call_args.kwargs
    assert 'secret-value' not in json.dumps(sent['json'])
    assert sent['allow_redirects'] is False
    report['evidence_lines']=['fabricated']
    response.json.return_value={'choices':[{'message':{'content':json.dumps(report)}}]}
    with pytest.raises(RuntimeError,match='unsupported evidence'): generate_rca(chunk)
    response.status_code=302
    with pytest.raises(RuntimeError,match='redirects'): generate_rca(chunk)


def test_report_cache_survives_restart(tmp_path,chunk):
    path=tmp_path/'reports.db'
    store=ReportStore(path)
    report=RCAResponse(summary='x',probable_root_cause='unknown',confidence=0,severity='LOW',affected_component='unknown',evidence_lines=['x'],recommended_actions=[])
    key=report_key(chunk,[],'local','v1')
    store.put(key,report)
    assert ReportStore(path).get(key)==report
    assert report_key(chunk,[],'local','v2')!=key
    assert store.get('missing') is None
