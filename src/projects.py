"""Local project boundaries and explicit history clearing."""
import re
from pathlib import Path


def project_directory(root,name):
    if not re.fullmatch(r'[a-zA-Z0-9_-]{1,64}',name):
        raise ValueError('Project names use 1–64 letters, numbers, hyphens or underscores')
    base=Path(root).resolve()
    result=(base/'projects'/name).resolve()
    if not result.is_relative_to(base):raise ValueError('Project path escapes the data directory')
    return result


def clear_history(vectors,jobs):
    # Refuse deletion while a worker can still write into this project.
    with jobs.store.connect() as con:
        con.execute('BEGIN IMMEDIATE')
        if con.execute("SELECT 1 FROM jobs WHERE status IN ('queued','starting','running')").fetchone():
            raise ValueError('Cancel or finish active jobs before clearing project history')
        while True:
            ids=vectors.collection.get(limit=1000,include=[])['ids']
            if not ids:break
            vectors.collection.delete(ids=ids)
        con.execute('DELETE FROM reports')
        con.execute('DELETE FROM jobs')
