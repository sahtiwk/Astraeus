"""Explicit real-process smoke check against an already running local model."""
import argparse,json,tempfile,time
from pathlib import Path
from src.jobs import JobManager
from src.pipeline import ingest
from src.reports import ReportStore

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--endpoint',default='http://127.0.0.1:18080/v1');args=parser.parse_args()
    with tempfile.TemporaryDirectory() as directory:
        db=Path(directory)/'jobs.db';manager=JobManager(db)
        chunk=ingest(b'2026-01-01T00:00:00Z ERROR [database] sqlite3.OperationalError: database is locked')['anomalies'][0]
        payload={'anomaly':chunk.model_dump(),'history':[],'endpoint':args.endpoint,'model':'astraeus-qwen3-1.7b'}
        jid=manager.store.submit('complete',payload);manager.poll()
        # A new manager emulates the UI restarting while the independent worker runs.
        manager=JobManager(db);deadline=time.monotonic()+180
        while manager.store.get(jid)['status'] in ('queued','starting','running') and time.monotonic()<deadline:
            time.sleep(.25);manager.poll()
        assert manager.store.get(jid)['status']=='completed',manager.store.get(jid)['error']
        assert ReportStore(db).get('complete')
        cancelled=manager.store.submit('cancel',payload);manager.poll();manager.cancel(cancelled)
        time.sleep(1)
        assert manager.store.get(cancelled)['status']=='cancelled'
        assert ReportStore(db).get('cancel') is None
        print(json.dumps({'real_worker_completion':True,'restart_result_retained':True,'cancelled_without_saved_report':True}))
if __name__=='__main__':main()
