"""Independent process entry point. Completed results survive UI/browser exit."""
import argparse
import json
import os
import psutil
from src.jobs import JobStore
from src.llm_analysis import generate_rca
from src.schemas import AnomalyChunk


def execute(db,jid):
    store=JobStore(db)
    with store.connect() as con:
        con.execute('BEGIN IMMEDIATE')
        row=con.execute('SELECT * FROM jobs WHERE id=?',(jid,)).fetchone()
        if not row or row['status'] not in ('queued','starting'):return
        con.execute("UPDATE jobs SET status='running',pid=?,pid_created=? WHERE id=?",(os.getpid(),psutil.Process().create_time(),jid))
        payload=json.loads(row['request'])
    try:
        report=generate_rca(AnomalyChunk.model_validate(payload['anomaly']),
            [AnomalyChunk.model_validate(v) for v in payload.get('history',[])],
            endpoint=payload['endpoint'],model=payload['model'])
        store.complete(jid,report)
    except Exception:
        store.fail(jid)

if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--db',required=True)
    parser.add_argument('--job',required=True)
    args=parser.parse_args()
    execute(args.db,args.job)
