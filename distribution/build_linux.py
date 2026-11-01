#!/usr/bin/env python3
"""Package verified native Linux outputs. Full kit requires the real Linux CBrowser."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import tarfile


def digest(path):
    result = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            result.update(chunk)
    return result.hexdigest()


def require_elf(path):
    with path.open('rb') as stream:
        if stream.read(4) != b'\x7fELF':
            raise ValueError('Expected native Linux ELF: ' + path.name)


def package(args):
    source = args.source.resolve()
    outputs = args.native_outputs.resolve()
    release = args.output.resolve()
    if release.exists():
        raise FileExistsError('Refuse to overwrite release')
    if not args.app_only and not args.engine_root:
        raise ValueError('Full kit requires --engine-root; do not substitute another vendor/browser')
    if args.app_only and args.engine_root:
        raise ValueError('Choose full engine kit OR explicitly named app-only package')
    for name in ['donutbrowser', 'donut-proxy']:
        require_elf(outputs / name)
    expected = 'donut-proxy 0.29.6-authorized.7-kit1'
    if subprocess.check_output([str(outputs / 'donut-proxy'), '--version'], text=True).strip() != expected:
        raise ValueError('Sidecar build tag mismatch')
    xray = source / 'src-tauri/binaries/xray-x86_64-unknown-linux-gnu'
    require_elf(xray)
    release.mkdir(parents=True)
    root = release / 'Donut-Agent-Kit'
    (root / 'app').mkdir(parents=True)
    for name in ['donutbrowser', 'donut-proxy']:
        dest = root / 'app' / ('donutbrowser-kit' if name == 'donutbrowser' else name)
        shutil.copy2(outputs / name, dest)
        subprocess.run(['strip', '--strip-debug', str(dest)], check=True)
        dest.chmod(0o755)
    shutil.copy2(xray, root / 'app/xray')
    (root / 'app/xray').chmod(0o755)
    (root / 'app/.portable').touch()
    docs = root / 'docs'
    docs.mkdir()
    for name in ['AGENT-GUIDE.md', 'CLIENTS.md', 'STACK.md']:
        shutil.copy2(source / 'distribution' / name, docs / name)
    shutil.copy2(source / 'distribution/LINUX.md', root / 'START_HERE.md')
    shutil.copy2(source / 'distribution/AGENTS.md', root / 'AGENTS.md')
    shutil.copy2(source / 'distribution/kit_linux.py', root / 'kit_linux.py')
    shutil.copy2(source / '146_Cl.txt', root / '146_Cl.txt')
    (root / 'Donut-Agent-Kit').write_text('#!/bin/sh\nset -eu\nHERE=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)\nexec python3 "$HERE/kit_linux.py" "$@"\n', encoding='utf-8')
    (root / 'Donut-Agent-Kit').chmod(0o755)
    licenses = root / 'licenses'
    licenses.mkdir()
    for src, dest in [(source / 'LICENSE', 'Donut-AGPL-3.0.txt'),
                      (source / 'distribution/Chromium-LICENSE.txt', 'Chromium-LICENSE.txt'),
                      (source / 'src-tauri/binaries/xray-LICENSE.txt', 'Xray-core-LICENSE.txt'),
                      (source / 'AUTHORIZED_FORK.md', 'AUTHORIZED_FORK.md')]:
        shutil.copy2(src, licenses / dest)
    upstream = None
    if args.engine_root:
        engine = args.engine_root.resolve()
        if (engine / 'ENGINE-PROVENANCE.json').is_file():
            upstream = json.loads((engine / 'ENGINE-PROVENANCE.json').read_text(encoding='utf-8'))
            shutil.copy2(engine / 'ENGINE-PROVENANCE.json', root / 'ENGINE-PROVENANCE.json')
            shutil.copy2(source / 'distribution/UPSTREAM-146-AUDIT.md', docs / 'UPSTREAM-146-AUDIT.md')
            shutil.copy2(source / 'distribution/LINUX-CANDIDATE.md', root / 'START_HERE.md')
        require_elf(engine / 'chrome')
        if any(p.name in {'Cookies', 'History', 'Login Data', 'Local State', 'Default'} for p in engine.rglob('*')):
            raise ValueError('Reject browser user data in engine distribution')
        shutil.copytree(engine, root / 'cbrowser')
        if args.geoip:
            assets = root / 'assets'
            assets.mkdir()
            shutil.copy2(args.geoip, assets / 'GeoLite2-City.mmdb')
            (licenses / 'GeoLite2-NOTICE.txt').write_text('This product includes GeoLite2 data created by MaxMind, available from https://www.maxmind.com . Terms: https://www.maxmind.com/en/geolite2/eula\n', encoding='utf-8')
    (licenses / 'BUILD-PLATFORM.txt').write_text(subprocess.check_output(['ldd', '--version'], text=True).splitlines()[0] + '\n' +
        'Built on Ubuntu 26.04 x86_64. This package does not bundle GTK/WebKit or claim older-glibc compatibility.\n', encoding='utf-8')
    ignored = {'.git', '.local', '.cache', 'target', 'node_modules', '.next', 'dist', 'gen', '__pycache__', 'state', 'test-results'}
    with tarfile.open(root / 'Donut-Agent-Kit-source.tar.gz', 'w:gz') as archive:
        for directory, dirs, names in os.walk(source):
            dirs[:] = [d for d in dirs if d not in ignored]
            for name in names:
                path = Path(directory) / name
                if path.is_symlink() or name.startswith('.env') and name not in {'.envrc', '.env.example'}:
                    continue
                if path.relative_to(source).parts[:2] == ('src-tauri', 'binaries') and path.suffix not in {'.txt', '.json'}:
                    continue
                if path.suffix in {'.exe', '.dll', '.pdb', '.pyc', '.log', '.tsbuildinfo'} or name == 'TASK-STATE.md':
                    continue
                archive.add(path, arcname=path.relative_to(source), recursive=False)
    details = {'platform': 'linux-x86_64-ubuntu26.04', 'cbrowserRelease': '1.33',
               'engineBundled': not args.app_only,
               'status': 'app-only; Linux CBrowser required' if args.app_only else ('upstream-engine compatibility candidate; core not rebuilt' if upstream else 'complete-engine-kit'),
               'engineProvenance': upstream,
               'files': {str(p.relative_to(root)): digest(p) for p in sorted(root.rglob('*')) if p.is_file()}}
    (root / 'MANIFEST.json').write_text(json.dumps(details, indent=2), encoding='utf-8')
    suffix = '-app-only' if args.app_only else ('-upstream146-candidate' if upstream else '')
    artifact = release / ('Donut-Agent-Kit-CBrowser-1.33-linux-x64-ubuntu26.04' + suffix + '.tar.gz')
    with tarfile.open(artifact, 'w:gz') as archive:
        archive.add(root, arcname='Donut-Agent-Kit')
    (release / 'SHA256.json').write_text(json.dumps({artifact.name: digest(artifact)}, indent=2), encoding='utf-8')
    print(json.dumps({'artifact': str(artifact), 'bytes': artifact.stat().st_size,
                      'sha256': digest(artifact), 'engineBundled': not args.app_only}))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--native-outputs', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--engine-root', type=Path)
    parser.add_argument('--geoip', type=Path)
    parser.add_argument('--app-only', action='store_true')
    package(parser.parse_args())
