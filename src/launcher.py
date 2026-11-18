"""Launch the local UI and optionally the verified bundled model server."""
import argparse
import os
import socket
import subprocess
import sys
import time
from pathlib import Path
from src.model_manager import ROOT,manifest,verify,hardware


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--with-model',action='store_true')
    parser.add_argument('--auto-model',action='store_true')
    parser.add_argument('--model-port',type=int,default=8080);parser.add_argument('--ui-port',type=int,default=8501)
    args=parser.parse_args();children=[];log=None
    for port in (args.ui_port, args.model_port):
        if not 1 <= port <= 65535:
            parser.error('Ports must be between 1 and 65535')
    if args.auto_model:
        spec = manifest()['models']['qwen3-1.7b-q4']
        available = hardware()['available_gib']
        args.with_model = (
            verify(ROOT / 'models' / spec['file'], spec)
            and bool(list((ROOT / 'runtime').rglob('llama-server.exe')))
            and available >= spec['recommended_available_gib']
        )
        if not args.with_model:
            print('Starting core analysis. Optional diagnosis needs a verified model, runtime and 3 GB available RAM.', flush=True)
    for port in ([args.ui_port, args.model_port] if args.with_model else [args.ui_port]):
        try:
            with socket.socket() as probe:
                probe.bind(('127.0.0.1', port))
        except OSError:
            raise SystemExit(f'Local port {port} is already in use. Close the existing app or select another port.')
    flags=subprocess.CREATE_NO_WINDOW if os.name=='nt' else 0
    try:
        if args.with_model:
            config=manifest();spec=config['models']['qwen3-1.7b-q4'];model=ROOT/'models'/spec['file']
            if not verify(model,spec):raise SystemExit('Model missing or checksum mismatch. Run python -m src.model_manager download first.')
            if hardware()['available_gib']<spec['recommended_available_gib']:raise SystemExit('Less than 3 GB available RAM. Close other applications or launch without --with-model.')
            runtimes=list((ROOT/'runtime').rglob('llama-server.exe' if os.name=='nt' else 'llama-server'))
            if not runtimes:raise SystemExit('Local runtime missing. Run python -m src.model_manager runtime, or start your own server.')
            logs=ROOT/'data';logs.mkdir(exist_ok=True)
            log=(logs/'model-server.log').open('a',encoding='utf-8')
            children.append(subprocess.Popen([str(runtimes[0]),'-m',str(model),'--host','127.0.0.1','--port',str(args.model_port),
                '--alias','astraeus-qwen3-1.7b','-c','4096','-t',str(min(4,os.cpu_count() or 1)),'--parallel','1','--reasoning','off'],
                cwd=ROOT,stdin=subprocess.DEVNULL,stdout=log,stderr=log,creationflags=flags))
            import requests
            with requests.Session() as session:
                session.trust_env=False
                for _ in range(60):
                    if children[0].poll() is not None:raise SystemExit('Model server failed; inspect data/model-server.log')
                    try:
                        if session.get(f'http://127.0.0.1:{args.model_port}/health',timeout=1).status_code==200:break
                    except requests.RequestException:pass
                    time.sleep(1)
                else:raise SystemExit('Model server did not become ready within 60 seconds')
        env=os.environ.copy()
        embedding = ROOT / 'models' / 'embedding'
        if embedding.is_dir():
            env.setdefault('ASTRAEUS_EMBEDDING_MODEL', str(embedding))
        env['ASTRAEUS_LOCAL_ENDPOINT']=f'http://127.0.0.1:{args.model_port}/v1'
        ui=subprocess.Popen([sys.executable,'-m','streamlit','run',str(ROOT/'app.py'),'--server.address=127.0.0.1',f'--server.port={args.ui_port}', '--server.headless=false'],cwd=ROOT,env=env)
        children.append(ui)
        print(f'Astraeus: http://127.0.0.1:{args.ui_port} (Ctrl+C stops this launcher)',flush=True)
        ui.wait()
    except KeyboardInterrupt:pass
    finally:
        for process in reversed(children):
            if process.poll() is None:
                process.terminate()
                try:process.wait(timeout=10)
                except subprocess.TimeoutExpired:process.kill();process.wait()
        if log:log.close()

if __name__=='__main__':main()
