from unittest.mock import Mock
from src.schemas import AnomalyChunk
from src.vector_store import VectorStore


def make_chunk(i):
    return AnomalyChunk(chunk_id=str(i),start_ts='2026-01-01 00:00:00',end_ts='2026-01-01 00:00:01',severity='HIGH',keywords=[],chunk_text='timeout token=secret',source_id='upload')


def store_with_fake_collection():
    store=VectorStore.__new__(VectorStore)
    store.collection=Mock()
    store.collection.get.return_value={'ids':[]}
    return store


def test_index_batches_redacts_and_reports_failures(monkeypatch):
    store=store_with_fake_collection()
    batches=[]
    def embed(texts):
        batches.append(texts)
        assert all('secret' not in text for text in texts)
        return [[1.0,0.0] for _ in texts]
    monkeypatch.setattr('src.vector_store.get_embeddings',embed)
    result=store.index_anomaly_chunks([make_chunk(i) for i in range(5)],batch_size=2)
    assert [len(b) for b in batches]==[2,2,1]
    assert result.indexed==5 and not result.failed
    store.collection.upsert.side_effect=RuntimeError('disk full')
    result=store.index_anomaly_chunks([make_chunk(10)])
    assert result.failed==['10'] and result.indexed==0


def test_existing_ids_skip_embedding(monkeypatch):
    store=store_with_fake_collection()
    store.collection.get.return_value={'ids':['1']}
    embed=Mock(side_effect=AssertionError('should not embed'))
    monkeypatch.setattr('src.vector_store.get_embeddings',embed)
    assert store.index_anomaly_chunks([make_chunk(1)]).indexed==0
    embed.assert_not_called()


def test_exclusion_and_empty_store(monkeypatch):
    store=store_with_fake_collection()
    embed=Mock(return_value=[1,0])
    monkeypatch.setattr('src.vector_store.get_embedding',embed)
    store.collection.count.return_value=0
    assert store.query_similar_anomalies('timeout')==[]
    embed.assert_not_called()
    store.collection.count.return_value=4
    store.collection.query.return_value={'ids':[['self','a','b','c']], 'documents':[['a']*4], 'metadatas':[[{'severity':'HIGH'}]*4]}
    result=store.query_similar_anomalies('timeout',exclude_ids=['self'],exclude_source_id='upload')
    assert [c.chunk_id for c in result]==['a','b','c']
    assert store.collection.query.call_args.kwargs['where']=={'source_id':{'$ne':'upload'}}
