"""Small persistent cache for validated reports; one connection per operation."""
import hashlib
from contextlib import closing
import json
import sqlite3
from pathlib import Path
from src.llm_analysis import PROMPT_VERSION
from src.schemas import RCAResponse


def report_key(anomaly, history, endpoint, model):
    data = dict(incident=anomaly.model_dump(), history=[c.model_dump() for c in history],
                endpoint=endpoint, model=model, prompt=PROMPT_VERSION)
    return hashlib.sha256(json.dumps(data,sort_keys=True).encode()).hexdigest()


class ReportStore:
    def __init__(self, path):
        self.path = str(path)
        Path(path).parent.mkdir(parents=True,exist_ok=True)
        with closing(sqlite3.connect(self.path)) as con, con:
            con.execute('CREATE TABLE IF NOT EXISTS reports (cache_key TEXT PRIMARY KEY, report TEXT NOT NULL)')

    def get(self, key):
        with closing(sqlite3.connect(self.path)) as con, con:
            row=con.execute('SELECT report FROM reports WHERE cache_key=?',(key,)).fetchone()
        return RCAResponse.model_validate_json(row[0]) if row else None

    def put(self, key, report):
        validated = RCAResponse.model_validate(report.model_dump())
        with closing(sqlite3.connect(self.path)) as con, con:
            con.execute('INSERT OR REPLACE INTO reports VALUES (?,?)',(key,validated.model_dump_json()))
