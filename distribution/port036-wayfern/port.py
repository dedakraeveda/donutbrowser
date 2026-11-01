"""Reproducible source-only overlay: plan/export/apply/verify, JSON output.

Never installs Donut, reads profiles, copies runtime state or mutates Git.
Patches are human-readable; apply reconstructs only against exact pinned input
hashes. For a DIFFERENT upstream version, use the logged three-way method and
review conflicts: never force these patches onto changed source.
"""
from __future__ import annotations
import argparse
import difflib
import hashlib
import json
from pathlib import Path
import shutil
import sys
import zipfile

HERE = Path(__file__).resolve().parent
SUFFIXES = {'.rs','.tsx','.ts','.json','.toml','.md','.lock','.css','.yaml','.yml','.mjs','.cjs','.js','.py','.txt'}
EXCLUDED = {'node_modules','.next','dist','target','.git','.local','.cache','.driver','artifacts','binaries','__pycache__'}

def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def valid(relative: str) -> Path:
    p = Path(relative)
    if p.is_absolute() or '..' in p.parts or any(n in EXCLUDED for n in p.parts) or p.name == '.env':
        raise ValueError('Invalid source-only overlay path')
    return p

def files(root: Path) -> dict[str, Path]:
    result = {}
    def walk(path: Path):
        for p in path.iterdir():
            if p.is_symlink() or p.is_junction():
                continue
            if p.is_dir():
                if p.name not in EXCLUDED:
                    walk(p)
            elif p.suffix in SUFFIXES and p.name != '.env':
                result[p.relative_to(root).as_posix()] = p
    walk(root)
    return result

def delta(upstream: Path, candidate: Path):
    old, new = files(upstream), files(candidate)
    records = []
    for name in sorted(old.keys() | new.keys()):
        a = old[name].read_bytes() if name in old else None
        b = new[name].read_bytes() if name in new else None
        if a == b:
            continue
        # Changed text only; no opaque binaries/auth state belong in an overlay.
        if a is not None:
            a.decode('utf8')
        if b is not None:
            b.decode('utf8')
        records.append((name,a,b))
    return records

def export(upstream: Path, candidate: Path):
    records = []
    for name,a,b in delta(upstream,candidate):
        rel = valid(name)
        patch = HERE/'patches'/Path(name+'.patch')
        patch.parent.mkdir(parents=True,exist_ok=True)
        patch.write_text(''.join(difflib.unified_diff(
            a.decode('utf8').splitlines(True) if a is not None else [],
            b.decode('utf8').splitlines(True) if b is not None else [],
            fromfile='a/'+name,tofile='b/'+name)),encoding='utf8',newline='')
        # Exact payload is separately hashed for simple, fail-closed application;
        # the patch is the review surface and is retained for future 3-way ports.
        payload = HERE/'overlay'/rel
        if b is not None:
            payload.parent.mkdir(parents=True,exist_ok=True)
            payload.write_bytes(b)
        records.append({'path':name,'before':digest(a) if a is not None else None,
                        'after':digest(b) if b is not None else None})
    baseline={name:digest(p.read_bytes()) for name,p in files(upstream).items()}
    manifest={'upstream':'0.36.0','candidate':'0.36.0+authorized.9','state':'IN_PROGRESS_NOT_RELEASED',
              'sourceOnly':True,'baseline':baseline,'files':records}
    (HERE/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf8')
    return {'operation':'export','files':len(records),'manifest':str(HERE/'manifest.json')}

def verify(root: Path, before: bool):
    m=json.loads((HERE/'manifest.json').read_text(encoding='utf8'));bad=[]
    key='before' if before else 'after'
    if before:
        for name,expected in m.get('baseline',{}).items():
            p=root/valid(name)
            if not p.is_file() or digest(p.read_bytes())!=expected:bad.append(name)
    for row in m['files']:
        p=root/valid(row['path']);actual=digest(p.read_bytes()) if p.is_file() else None
        if actual!=row[key]:bad.append(row['path'])
    return {'operation':'preflight' if before else 'verify','ok':not bad,'mismatched':bad,'files':len(m['files'])}

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('operation',choices=['capabilities','status','plan','export','preflight','apply','verify'])
    p.add_argument('--upstream',type=Path)
    p.add_argument('--candidate',type=Path)
    p.add_argument('--destination',type=Path)
    a=p.parse_args()
    if a.operation=='capabilities':
        result={'operation':'capabilities','operations':['status','plan','export','preflight','apply','verify'],
                'sourceOnly':True,'changesInstalledApp':False,'requiresNewDestination':True}
    elif a.operation=='status':
        manifest=HERE/'manifest.json'
        m=json.loads(manifest.read_text(encoding='utf8')) if manifest.exists() else {}
        result={'operation':'status','manifestPresent':manifest.exists(),'state':m.get('state'),'upstream':m.get('upstream'),'files':len(m.get('files',[]))}
    elif a.operation in ['plan','export']:
        if not a.upstream or not a.candidate:p.error('--upstream and --candidate required')
        result=export(a.upstream,a.candidate) if a.operation=='export' else {'operation':'plan','paths':[n for n,_,_ in delta(a.upstream,a.candidate)]}
    elif a.operation=='apply':
        if not a.upstream or not a.destination:p.error('--upstream and --destination required')
        result=verify(a.upstream,True)
        if not result['ok']:print(json.dumps(result));return 2
        destination=a.destination.resolve()
        if a.destination.exists() or destination.drive.upper()!='D:':raise ValueError('New D: destination required')
        if destination.is_relative_to(a.upstream.resolve()):raise ValueError('Destination must not be inside the upstream source tree')
        shutil.copytree(a.upstream,a.destination)
        m=json.loads((HERE/'manifest.json').read_text(encoding='utf8'))
        for row in m['files']:
            rel=valid(row['path']);target=a.destination/rel
            if row['after'] is None:
                if target.exists():target.unlink()
            else:
                data=(HERE/'overlay'/rel).read_bytes()
                if digest(data)!=row['after']:raise ValueError('Overlay checksum mismatch')
                target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(data)
        result=verify(a.destination,False);result['operation']='apply'
    else:
        root=a.upstream if a.operation=='preflight' else a.candidate
        if not root:p.error('Source root required')
        result=verify(root,a.operation=='preflight')
    print(json.dumps(result,ensure_ascii=False,indent=2));return 0 if result.get('ok',True) else 2

if __name__=='__main__':
    try:raise SystemExit(main())
    except (ValueError,OSError) as error:
        print(json.dumps({'ok':False,'error':str(error)}));raise SystemExit(2)
