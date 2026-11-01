"""Assemble only verified Linux-x64 manager and BOTH exact local engines.

No external downloads, credentials, existing profile import, installation,
or unverified alternate engine. Output must be new on an explicit volume.
"""
from pathlib import Path
import argparse
import hashlib
import importlib.util
import json
import os
import shutil
import stat
import subprocess
import sys
import tarfile
import zipfile

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
spec = importlib.util.spec_from_file_location('native_linux', HERE / 'native_policy.py')
native = importlib.util.module_from_spec(spec)
spec.loader.exec_module(native)


def digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def package_reproducer(root):
    target = root / 'source/native-linux-reproducer.zip'
    with zipfile.ZipFile(target, 'x', zipfile.ZIP_DEFLATED) as archive:
        names = ['native_policy.py', 'test_native_policy.py',
                 'wayfern-native-policy.json', 'cbrowser-native-policy.json',
                 'launcher.py', 'build_kit.py', 'START_HERE.md', 'AGENTS.md']
        for name in names:
            archive.write(HERE / name, 'distribution/linux155/' + name)
        dataset = REPO / 'distribution/native-data/155-fingerprint-tables.json'
        if digest(dataset) != 'e1190dfb79ebd6ecd1f13e120e861219873e4b2c04e292485b7f44f15fd3d90c':
            raise ValueError('public-native-dataset-checksum')
        archive.write(dataset, 'distribution/native-data/155-fingerprint-tables.json')
    return digest(target)


def build(args):
    if sys.platform != 'linux':
        raise ValueError('assemble-on-Linux-to-preserve-file-modes')
    if args.destination.exists() or not args.destination.parent.is_dir():
        raise ValueError('new-destination-required')
    if args.source.exists() is False or not (args.source / 'src-tauri/src/wayfern_local_policy.rs').is_file():
        raise ValueError('reconstructed-matching-source-required')
    manifest = json.loads((REPO / 'distribution/port036-wayfern/manifest.json').read_text())
    for row in manifest['files']:
        path = args.source / row['path']
        actual = digest(path) if path.is_file() else None
        if actual != row['after']:
            raise ValueError('matching-source-overlay-mismatch: ' + row['path'])
    for engine, root in [('cbrowser', args.cbrowser), ('wayfern', args.wayfern)]:
        if not native.verify(root, engine)['ok']:
            raise ValueError('unverified-native-engine')
    ci = json.loads((args.manager / 'BUILD.json').read_text())
    if ci['platform'] != 'linux' or ci['architecture'] != 'linux-x64':
        raise ValueError('native-manager-architecture')
    archives = list(args.manager.glob('*.zip'))
    if len(archives) != 1 or digest(archives[0]) != ci['archiveSha256']:
        raise ValueError('native-manager-archive-checksum')
    for path in [args.cbrowser, args.wayfern, args.manager]:
        if args.destination.resolve().is_relative_to(path.resolve()):
            raise ValueError('overlapping-build-destination')
    needed = sum(p.stat().st_size for root in [args.cbrowser, args.wayfern] for p in root.rglob('*') if p.is_file())
    if shutil.disk_usage(args.destination.parent).free < needed * 2 + 2 * 1024**3:
        raise ValueError('output-volume-peak-budget')
    root = args.destination
    root.mkdir()
    (root / 'app').mkdir()
    (root / 'assets').mkdir()
    (root / 'licenses').mkdir()
    (root / 'source').mkdir()
    with zipfile.ZipFile(archives[0]) as archive:
        if set(archive.namelist()) != set(ci['files']):
            raise ValueError('unexpected-manager-archive-member')
        names = {'donutbrowser': 'donutbrowser', 'donut-proxy': 'donut-proxy',
                 'xray-x86_64-unknown-linux-gnu': 'xray'}
        for name, target in names.items():
            with archive.open(name) as stream:
                data = stream.read()
            if hashlib.sha256(data).hexdigest() != ci['files'][name]:
                raise ValueError('manager-binary-hash')
            if data[:6] != bytes.fromhex('7f454c460201') or data[18:20] != bytes.fromhex('3e00'):
                raise ValueError('ELF64-x86_64-manager-required')
            path = root / 'app' / target
            path.write_bytes(data)
            path.chmod(0o755)
        for name in ['LICENSE', 'AUTHORIZED_FORK.md', 'xray-LICENSE.txt', 'xray-x86_64-unknown-linux-gnu.source.json']:
            data = archive.read(name)
            if hashlib.sha256(data).hexdigest() != ci['files'][name]:
                raise ValueError('manager-license-hash')
            (root / 'licenses' / name).write_bytes(data)
    shutil.copytree(args.cbrowser, root / 'cbrowser')
    shutil.copytree(args.wayfern, root / 'wayfern')
    shutil.copy2(args.geoip, root / 'assets/GeoLite2-City.mmdb')
    (root / 'licenses/GeoLite2-NOTICE.txt').write_text('This product includes GeoLite2 data created by MaxMind, available from https://www.maxmind.com . Terms: https://www.maxmind.com/en/geolite2/eula\n')
    for name in ['launcher.py', 'START_HERE.md', 'AGENTS.md']:
        shutil.copy2(HERE / name, root / name)
    (root / 'Donut-Agent-Kit').write_text('#!/bin/sh\nset -eu\nHERE=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)\nexec python3 "$HERE/launcher.py" "$@"\n')
    (root / 'Donut-Agent-Kit').chmod(0o755)
    (root / '146_Cl.txt').write_text('CBrowser fork release: 1.33\nLinux x64 technical engine: 155.0.8059.39.2\nWayfern technical engine: 155.0.8059.79\nNative binary modifications, not Chromium C++ source rebuilds.\n')
    # Source is reconstructed from a checksum-pinned public archive and exact
    # reviewed overlay; no local repo/node_modules/.env/working state is packed.
    source_zip = root / 'source/donut036-matching-source.zip'
    excluded = {'.git', '.local', 'node_modules', 'target', '.next', '__pycache__', 'artifacts'}
    with zipfile.ZipFile(source_zip, 'x', zipfile.ZIP_DEFLATED) as archive:
        for path in args.source.rglob('*'):
            rel = path.relative_to(args.source)
            if any(x in excluded for x in rel.parts):
                continue
            if path.is_symlink() or (path.name.startswith('.env') and path.name not in ['.env.example', '.envrc']) or path.suffix in ['.dat', '.key']:
                raise ValueError('private-or-linked-source-material-refused')
            if path.is_file():
                archive.write(path, rel.as_posix())
    native_source_sha = package_reproducer(root)
    (root / 'BUILD.json').write_text(json.dumps({'nativeReproducerSha256': native_source_sha, 'kind': 'both-native-engine-linux-x64-kit-candidate',
        'managerBuild': ci, 'managerSourceCommit': args.commit, 'cbrowser': native.verify(root / 'cbrowser', 'cbrowser'),
        'wayfern': native.verify(root / 'wayfern', 'wayfern'), 'installed': False,
        'guiRuntimeVerifiedByBuilder': False, 'completeUpstreamE2E': False,
        'sourceSha256': digest(source_zip)}, indent=2) + '\n')
    files = {p.relative_to(root).as_posix(): digest(p) for p in root.rglob('*') if p.is_file()}
    (root / 'MANIFEST.json').write_text(json.dumps({'schemaVersion': 1, 'engineBundled': True, 'files': files}, indent=2) + '\n')
    # State must not exist at packaging time. Test only a clean extracted copy.
    if (root / 'state').exists():
        raise ValueError('runtime-state-in-payload')
    result = {'ok': True, 'root': str(root), 'filesVerified': len(files), 'engineBundled': ['cbrowser', 'wayfern'],
              'managerSourceCommit': args.commit, 'releaseEligible': False, 'runtimeVerifiedByBuilder': False}
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ['manager', 'cbrowser', 'wayfern', 'source', 'geoip', 'destination']:
        parser.add_argument('--' + name, type=Path, required=True)
    parser.add_argument('--commit', required=True)
    try:
        build(parser.parse_args())
    except (OSError, ValueError, KeyError) as error:
        print(json.dumps({'ok': False, 'error': str(error)}))
        raise SystemExit(2)
