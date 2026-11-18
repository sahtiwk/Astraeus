"""Build a source distribution ZIP with an explicit, secret-free allowlist."""
import hashlib
import json
import zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
TOP=['app.py','README.md','IMPLEMENTATION_PLAN.md','VALIDATION.md','pyproject.toml','uv.lock','requirements.txt','requirements-dev.txt','models-manifest.json','install.ps1','Install Astraeus.cmd','Start Astraeus.cmd','WINDOWS_QUICKSTART.md','run.ps1','install.sh','Dockerfile','docker-compose.yml','.dockerignore','.gitignore','pytest.ini']


def build(output=None):
    files=[ROOT/p for p in TOP if (ROOT/p).is_file()]
    for folder,patterns in [('src',['*.py']),('scripts',['*.py']),('tests',['test_*.py','__init__.py','benchmark_*.py','run_all_benchmarks.py']),('docs',['*.md']),('.streamlit',['*.toml']),('.github',['*.yml']),('evaluation',['*.py','*.md','cases.jsonl','results-*-v*.json']),('data/samples',['*.log'])]:
        for pattern in patterns:files.extend((ROOT/folder).rglob(pattern))
    # Test generator is a test dependency; only owned safe sample logs are bundled.
    files.append(ROOT/'tests/generate_mock_data.py')
    files=sorted(p for p in set(files) if p.name != 'demo.yml')
    output=Path(output or ROOT/'dist/astraeus-0.3.0-rc1-windows-x64.zip');output.parent.mkdir(parents=True,exist_ok=True)
    hashes={p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
    with zipfile.ZipFile(output,'w',zipfile.ZIP_DEFLATED) as z:
        def put(name,data):
            info=zipfile.ZipInfo(name,date_time=(2026,1,1,0,0,0))
            info.compress_type=zipfile.ZIP_DEFLATED
            info.external_attr=0o644 << 16
            z.writestr(info,data)
        for p in files:put('astraeus/'+p.relative_to(ROOT).as_posix(),p.read_bytes())
        put('astraeus/RELEASE_MANIFEST.json',json.dumps(hashes,indent=2).encode())
    output.with_suffix('.sha256').write_text(hashlib.sha256(output.read_bytes()).hexdigest()+'  '+output.name+'\n')
    return output

if __name__=='__main__':print(build())
