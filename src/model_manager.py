"""Explicit, checksum-verified local model setup. Never downloads on app startup."""
import hashlib
import json
import os
import platform
import shutil
import zipfile
from pathlib import Path
import requests
import psutil

ROOT = Path(__file__).resolve().parents[1]


def manifest():
    return json.loads((ROOT / 'models-manifest.json').read_text(encoding='utf-8'))


def checksum(path):
    digest=hashlib.sha256()
    with open(path,'rb') as stream:
        for block in iter(lambda:stream.read(4*1024*1024),b''):
            digest.update(block)
    return digest.hexdigest()


def hardware():
    memory=psutil.virtual_memory()
    return dict(os=platform.system(),architecture=platform.machine(),python=platform.python_version(),
                cpu_count=os.cpu_count(),ram_gib=round(memory.total/2**30,2),
                available_gib=round(memory.available/2**30,2))


def verify(path, spec):
    path=Path(path)
    return path.is_file() and path.stat().st_size==spec['size'] and checksum(path)==spec['sha256']


def download(url, destination, spec):
    destination=Path(destination)
    destination.parent.mkdir(parents=True,exist_ok=True)
    if verify(destination,spec):
        return destination
    if shutil.disk_usage(destination.parent).free < spec['size']*1.2:
        raise RuntimeError('Insufficient disk space for this model')
    partial=destination.with_suffix(destination.suffix+'.partial')
    # Resume only if the server honors the byte range. Final digest checks all bytes.
    offset=partial.stat().st_size if partial.exists() else 0
    if offset >= spec['size']:
        if verify(partial,spec):
            os.replace(partial,destination)
            return destination
        partial.unlink()
        offset=0
    headers={'Range':f'bytes={offset}-'} if offset else {}
    with requests.get(url,headers=headers,stream=True,timeout=(15,90)) as response:
        response.raise_for_status()
        append=offset>0 and response.status_code==206
        if not append:offset=0
        received=offset
        next_progress=received+64*1024*1024
        print(f'Downloading {destination.name}: {received}/{spec["size"]} bytes',flush=True)
        with partial.open('ab' if append else 'wb') as output:
            for block in response.iter_content(1024*1024):
                if block:
                    output.write(block);received+=len(block)
                    if received>=next_progress:
                        print(f'{destination.name}: {received}/{spec["size"]} bytes',flush=True)
                        next_progress=received+64*1024*1024
    if not verify(partial,spec):
        raise RuntimeError(f'Checksum/size mismatch; incomplete file retained at {partial}')
    os.replace(partial,destination)
    return destination


def install_model(name='qwen3-1.7b-q4',directory=None,source=None):
    spec=manifest()['models'][name]
    target=Path(directory or ROOT/'models')/spec['file']
    target.parent.mkdir(parents=True,exist_ok=True)
    if source:
        if not verify(source,spec):raise ValueError('Imported model does not match the pinned checksum')
        if Path(source).resolve()!=target.resolve():shutil.copy2(source,target)
    else:
        url=f"https://huggingface.co/{spec['repo']}/resolve/{spec['revision']}/{spec['file']}"
        download(url,target,spec)
    (target.parent/(target.name+'.metadata.json')).write_text(json.dumps(spec,indent=2))
    return target


def install_runtime(directory=None):
    key='windows-x64' if platform.system()=='Windows' and platform.machine().lower() in ('amd64','x86_64') else ''
    if not key:raise RuntimeError('Automatic runtime setup is currently Windows x64 only; install llama.cpp manually on this platform')
    spec=manifest()['runtimes'][key]
    target=Path(directory or ROOT/'runtime')/spec['version']
    archive=download(spec['url'],target/'runtime.zip',spec)
    with zipfile.ZipFile(archive) as z:
        for member in z.infolist():
            if not (target/member.filename).resolve().is_relative_to(target.resolve()):
                raise ValueError('Unsafe runtime archive path')
        z.extractall(target)
    return next(target.rglob('llama-server.exe'))


def main():
    import argparse
    parser=argparse.ArgumentParser()
    parser.add_argument('action',choices=['hardware','download','import','verify','runtime'])
    parser.add_argument('--name',default='qwen3-1.7b-q4')
    parser.add_argument('--directory')
    parser.add_argument('--file')
    args=parser.parse_args()
    if args.action=='hardware':print(json.dumps(hardware(),indent=2))
    elif args.action=='runtime':print(install_runtime(args.directory))
    elif args.action=='verify':
        if not args.file or not verify(args.file,manifest()['models'][args.name]):raise SystemExit('Model verification failed')
        print('Model checksum verified')
    else:
        if args.action=='import' and not args.file:parser.error('import requires --file')
        print(install_model(args.name,args.directory,args.file if args.action=='import' else None))

if __name__=='__main__':main()
