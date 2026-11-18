"""Run safe controlled faults; ground truth comes from the operation, not an LLM."""
import json
from contextlib import closing
import socket
import sqlite3
import tempfile
import threading
from datetime import datetime,timedelta
from pathlib import Path

FAMILIES=['missing_config','invalid_config','database_locked','unique_violation','missing_file','connection_refused','pool_exhausted','healthy','unresolved']
TERMS={
 'missing_config':['missing','configuration','environment','keyerror'],
 'invalid_config':['json','configuration','syntax','parsing'],
 'database_locked':['lock','concurrent','transaction'],
 'unique_violation':['unique','duplicate','constraint'],
 'missing_file':['missing','not found','does not exist','no such file'],
 'connection_refused':['refused','not listening','unavailable','no service'],
 'pool_exhausted':['pool','exhaust','permit','capacity'],
 'healthy':['healthy'],
 'unresolved':['insufficient','cannot determine','not enough','unclear','unknown'],
}


def exercise(family,index,root):
    if family=='missing_config':
        try:{}[f'SERVICE_ENDPOINT_{index}']
        except KeyError as e:return f'KeyError: missing required configuration {e}', 'Missing required configuration key', 'executed'
    if family=='invalid_config':
        try:json.loads('{"retries": '+str(index)+',}')
        except json.JSONDecodeError as e:return f'JSONDecodeError: {e.msg} at line {e.lineno}', 'Malformed JSON configuration', 'executed'
    if family=='database_locked':
        path=root/'db.sqlite'
        with closing(sqlite3.connect(path)) as con, con:con.execute('CREATE TABLE items (id INTEGER)')
        first=sqlite3.connect(path);second=sqlite3.connect(path,timeout=0.01)
        try:
            first.execute('BEGIN EXCLUSIVE');first.execute('INSERT INTO items VALUES (?)',(index,))
            try:second.execute('INSERT INTO items VALUES (?)',(index+1,))
            except sqlite3.OperationalError as e:return f'OperationalError: {e}; concurrent writer transaction active', 'Concurrent SQLite write transaction holds database lock', 'executed'
        finally:first.rollback();first.close();second.close()
    if family=='unique_violation':
        with closing(sqlite3.connect(':memory:')) as con, con:
            con.execute('CREATE TABLE items (id INTEGER UNIQUE)');con.execute('INSERT INTO items VALUES (?)',(index,))
            try:con.execute('INSERT INTO items VALUES (?)',(index,))
            except sqlite3.IntegrityError as e:return f'IntegrityError: {e}; insert rejected', 'Duplicate value violates a UNIQUE database constraint', 'executed'
    if family=='missing_file':
        try:(root/f'config-{index}.json').read_text()
        except FileNotFoundError:return f'FileNotFoundError: config-{index}.json does not exist', 'Required configuration file is absent', 'executed'
    if family=='connection_refused':
        with socket.socket() as bound:
            bound.bind(('127.0.0.1',0))
            # Bound but intentionally not listening; no service outside this machine is contacted.
            try:
                with socket.create_connection(bound.getsockname(),timeout=1):pass
            except OSError:return 'ConnectionRefusedError: connection refused by local dependency; listener is not running', 'Dependency has no listening server', 'executed'
    if family=='pool_exhausted':
        pool=threading.BoundedSemaphore(1);pool.acquire()
        try:
            assert not pool.acquire(timeout=0.01)
            return 'TimeoutError: connection pool exhausted; active=1 capacity=1 available=0', 'All permits in the bounded connection pool are held', 'executed'
        finally:pool.release()
    if family=='healthy':
        path=root/'ok.txt';path.write_text('ok');assert path.read_text()=='ok'
        return 'Request completed successfully; health check passed', 'No injected fault', 'executed'
    return 'TimeoutError: request exceeded deadline; no upstream metrics or configuration available', 'Unresolved: the supplied evidence does not establish the cause', 'ambiguous fixture, not a confirmed fault'


def generate(output,runs=12):
    cases=[]
    for family in FAMILIES:
        for index in range(runs):
            with tempfile.TemporaryDirectory(prefix='astraeus-fixture-') as tmp:
                message,cause,method=exercise(family,index,Path(tmp))
            run_id=f'{family}-{index:03}'
            stamp=datetime(2026,1,1)+timedelta(days=index)
            service=f'example-{index%3}'
            logs='\n'.join(json.dumps(dict(timestamp=(stamp+timedelta(seconds=n)).isoformat()+'Z',level=level,service=service,message=msg)) for n,(level,msg) in enumerate([
                ('INFO',f'Request run-{index:03} started'),
                ('INFO' if family=='healthy' else 'ERROR',message)]))
            split='train' if index<runs//2 else 'validation' if index<3*runs//4 else 'test'
            cases.append(dict(id=run_id,run_id=run_id,split=split,family=family,logs=logs,
                expected_cause=cause,expected_terms=TERMS[family],should_detect=family!='healthy',
                should_abstain=family=='unresolved',provenance={'method':method,'generator':'evaluation/generate_cases.py','license':'CC0-1.0'}))
    output=Path(output);output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text('\n'.join(json.dumps(c) for c in cases)+'\n',encoding='utf-8')
    return cases

if __name__=='__main__':
    print('Generated',len(generate(Path(__file__).parent/'cases.jsonl')),'controlled cases')
