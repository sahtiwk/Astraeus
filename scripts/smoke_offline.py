"""Preinstalled integration probe: refuse non-loopback Python socket connections."""
import socket,tempfile,json,argparse
from pathlib import Path

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--endpoint',default='http://127.0.0.1:18080/v1');args=parser.parse_args()
    original=socket.socket.connect
    def local_only(self,address):
        if isinstance(address,tuple) and address[0] not in ('127.0.0.1','::1'):
            raise AssertionError('Non-loopback connection attempted')
        return original(self,address)
    socket.socket.connect=local_only
    from src.pipeline import ingest
    from src.vector_store import VectorStore
    from src.llm_analysis import generate_rca
    from src.reports import ReportStore
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as directory:
        chunks=ingest(b'2026-01-01T00:00:00Z ERROR [db] sqlite3.OperationalError: database is locked')['anomalies']
        vectors=VectorStore(str(Path(directory)/'vectors'))
        assert vectors.index_anomaly_chunks(chunks).indexed==1
        assert vectors.query_similar_anomalies('database locked')
        assert not vectors.query_similar_anomalies('database locked',exclude_source_id=chunks[0].source_id)
        report=generate_rca(chunks[0],endpoint=args.endpoint,model='astraeus-qwen3-1.7b')
        store=ReportStore(Path(directory)/'reports.db');store.put('probe',report)
        assert ReportStore(Path(directory)/'reports.db').get('probe')==report
        print(json.dumps({'external_python_sockets_blocked':True,'real_embeddings_vectors_rca_reload':True}))
if __name__=='__main__':main()
