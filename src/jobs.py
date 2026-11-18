"""Persistent local jobs. Workers write their own results and can be cancelled."""
import json
from contextlib import contextmanager
import os
import sqlite3
import subprocess
import sys
import threading
import time
import uuid
from pathlib import Path
import psutil
from src.privacy import redact


class JobStore:
    def __init__(self,path):
        self.path=str(Path(path).resolve())
        Path(self.path).parent.mkdir(parents=True,exist_ok=True)
        with self.connect() as con:
            con.execute('CREATE TABLE IF NOT EXISTS jobs (id TEXT PRIMARY KEY, cache_key TEXT NOT NULL, status TEXT NOT NULL, request TEXT NOT NULL, result TEXT, error TEXT, pid INTEGER, pid_created REAL, created REAL NOT NULL)')
            con.execute('CREATE TABLE IF NOT EXISTS reports (cache_key TEXT PRIMARY KEY, report TEXT NOT NULL)')

    @contextmanager
    def connect(self):
        con=sqlite3.connect(self.path,timeout=10)
        con.row_factory=sqlite3.Row
        try:
            with con:
                yield con
        finally:
            con.close()

    def get(self,job_id):
        with self.connect() as con:row=con.execute('SELECT * FROM jobs WHERE id=?',(job_id,)).fetchone()
        return dict(row) if row else None

    def latest(self,key):
        with self.connect() as con:row=con.execute('SELECT * FROM jobs WHERE cache_key=? ORDER BY created DESC LIMIT 1',(key,)).fetchone()
        return dict(row) if row else None

    def submit(self,key,request):
        # Deep-redact string values without changing JSON structure.
        def clean(value):
            if isinstance(value,str):return redact(value)
            if isinstance(value,list):return [clean(v) for v in value]
            if isinstance(value,dict):return {k:clean(v) for k,v in value.items()}
            return value
        with self.connect() as con:
            con.execute('BEGIN IMMEDIATE')
            existing=con.execute("SELECT id FROM jobs WHERE cache_key=? AND status IN ('queued','starting','running','completed') ORDER BY created DESC LIMIT 1",(key,)).fetchone()
            if existing:return existing['id']
            jid=uuid.uuid4().hex
            cleaned=clean(request)
            if 'endpoint' in request:
                from src.llm_analysis import validate_endpoint
                cleaned['endpoint']=validate_endpoint(request['endpoint'])
            con.execute('INSERT INTO jobs(id,cache_key,status,request,created) VALUES (?,?,?,?,?)',
                (jid,key,'queued',json.dumps(cleaned),time.time()))
        return jid

    def complete(self,jid,report):
        with self.connect() as con:
            con.execute('BEGIN IMMEDIATE')
            row=con.execute('SELECT * FROM jobs WHERE id=?',(jid,)).fetchone()
            if not row or row['status']!='running':return False
            con.execute("UPDATE jobs SET status='completed',result=? WHERE id=?",(report.model_dump_json(),jid))
            con.execute('INSERT OR REPLACE INTO reports VALUES (?,?)',(row['cache_key'],report.model_dump_json()))
        return True

    def fail(self,jid,error='Local diagnosis failed; check model server and retry.'):
        with self.connect() as con:
            con.execute("UPDATE jobs SET status='failed',error=? WHERE id=? AND status IN ('starting','running')",(error,jid))


def worker_alive(row):
    if not row.get('pid') or not row.get('pid_created'):return False
    try:
        p=psutil.Process(row['pid'])
        return abs(p.create_time()-row['pid_created'])<0.01 and p.is_running() and row['id'] in p.cmdline()
    except (psutil.Error,OSError):return False


class JobManager:
    def __init__(self,path):
        self.store=JobStore(path)
        self.lock=threading.Lock()

    def poll(self):
        with self.lock,self.store.connect() as con:
            rows=[dict(r) for r in con.execute("SELECT * FROM jobs WHERE status IN ('starting','running')")]
            for row in rows:
                # Allow the parent to register a newly launched process.
                if row['status']=='starting' and time.time()-row['created']<15:continue
                if not worker_alive(row):
                    con.execute("UPDATE jobs SET status='interrupted',error='Worker stopped before completion. Retry this incident.' WHERE id=? AND status IN ('starting','running')",(row['id'],))
            con.commit()
            if con.execute("SELECT 1 FROM jobs WHERE status IN ('starting','running')").fetchone():return
            con.execute('BEGIN IMMEDIATE')
            if con.execute("SELECT 1 FROM jobs WHERE status IN ('starting','running')").fetchone():return
            row=con.execute("SELECT * FROM jobs WHERE status='queued' ORDER BY created LIMIT 1").fetchone()
            if not row:return
            con.execute("UPDATE jobs SET status='starting',created=? WHERE id=?",(time.time(),row['id']))
            con.commit()
            try:
                process=subprocess.Popen([sys.executable,'-m','src.job_worker','--db',self.store.path,'--job',row['id']],
                    cwd=str(Path(__file__).resolve().parents[1]),stdin=subprocess.DEVNULL,stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,creationflags=subprocess.CREATE_NO_WINDOW if os.name=='nt' else 0)
                created=psutil.Process(process.pid).create_time()
                con.execute('UPDATE jobs SET pid=?,pid_created=? WHERE id=?',(process.pid,created,row['id']))
            except (OSError,psutil.Error):
                con.execute("UPDATE jobs SET status='failed',error='Could not start local worker' WHERE id=?",(row['id'],))

    def cancel(self,jid):
        with self.lock,self.store.connect() as con:
            row=con.execute('SELECT * FROM jobs WHERE id=?',(jid,)).fetchone()
            if not row:return
            row=dict(row)
            con.execute("UPDATE jobs SET status='cancelled' WHERE id=? AND status IN ('queued','starting','running')",(jid,))
            con.commit()
            if row['status'] in ('starting','running') and worker_alive(row):
                try:psutil.Process(row['pid']).terminate()
                except psutil.Error:pass
