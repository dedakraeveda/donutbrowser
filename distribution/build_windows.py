#!/usr/bin/env python3
"""Native Windows manager build for hosted runners; no engine/key silently substituted."""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import zipfile

REPO = Path(__file__).resolve().parents[1]


def digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def build(args):
    if sys.platform != 'win32':
        raise RuntimeError('Native Windows/MSVC host required')
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    work, output = args.work.resolve(), args.output.resolve()
    if work.exists() or output.exists():
        raise FileExistsError('Work and output must be new directories')
    work.mkdir(parents=True)
    system = Path(os.environ['SystemDrive'] + '/')
    free = {str(p): round(shutil.disk_usage(p).free / 2**30, 2) for p in (system, work)}
    print(json.dumps({'freeGiB': free, 'scope': 'hosted Windows build runner'}), flush=True)
    if shutil.disk_usage(system).free < 20 * 2**30 or shutil.disk_usage(work).free < 15 * 2**30:
        raise RuntimeError('Need20GiB system and15GiB destination free; no automatic system cleanup')
    spec = importlib.util.spec_from_file_location('mac_source_staging', REPO / 'distribution/build_macos.py')
    staging = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(staging)
    source = work / 'source'
    staging.prepare_source(source)
    temp = work / 'tmp'; temp.mkdir()
    env = {k: v for k, v in os.environ.items() if not any(s in k.upper() for s in
           ['TOKEN', 'PASSWORD', 'SECRET', 'API_KEY', 'LICENSE_KEY', 'GITHUB_', 'DONUT_', 'BROWSER_', 'NEXT_PUBLIC_'])}
    env.update(TMPDIR=str(temp), TMP=str(temp), TEMP=str(temp), CARGO_HOME=str(work / 'cargo-home'),
               CARGO_TARGET_DIR=str(work / 'target'), CARGO_BUILD_JOBS='2', CARGO_INCREMENTAL='0',
               BUILD_TAG='0.29.6-authorized.7-kit1', NEXT_PUBLIC_DONUT_LOCAL_FEATURES='1',
               NEXT_TELEMETRY_DISABLED='1', PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD='1',
               npm_config_cache=str(work / 'npm-cache'), PNPM_HOME=str(work / 'pnpm-home'))

    stage = 0

    def run(command):
        nonlocal stage
        stage += 1
        log = work / ('stage-' + str(stage) + '.log')
        print('RUN', stage, str(command[0]), flush=True)
        with log.open('w', encoding='utf-8') as stream:
            result = subprocess.run([str(p) for p in command], cwd=source, env=env,
                                    stdout=stream, stderr=subprocess.STDOUT,
                                    creationflags=subprocess.CREATE_NO_WINDOW)
        lines = log.read_text(encoding='utf-8', errors='replace').splitlines()
        print('\n'.join(lines[-80:] if result.returncode else lines[-8:]), flush=True)
        if result.returncode:
            raise RuntimeError('Native build stage failed: ' + str(stage) + '; see stage log')
        if shutil.disk_usage(system).free < 20 * 2**30:
            raise RuntimeError('System disk budget reached; stop before next stage')

    run(['rustc', '--version'])
    run(['cargo', '--version'])
    run(['pnpm.cmd', 'install', '--frozen-lockfile', '--ignore-scripts', '--store-dir', work / 'pnpm-store'])
    run(['node', 'node_modules/next/dist/bin/next', 'build', '--webpack'])
    run(['node', 'src-tauri/download-xray.mjs', '--target', 'x86_64-pc-windows-msvc'])
    manifest = source / 'src-tauri/Cargo.toml'
    run(['cargo', 'rustc', '--release', '--locked', '--manifest-path', manifest, '--bin', 'donut-proxy', '--', '-C', 'lto=off'])
    native = work / 'target/release'
    binaries = source / 'src-tauri/binaries'
    shutil.copy2(native / 'donut-proxy.exe', binaries / 'donut-proxy-x86_64-pc-windows-msvc.exe')
    run(['cargo', 'build', '--release', '--locked', '--manifest-path', manifest, '--bin', 'donutbrowser'])
    output.mkdir(parents=True)
    root = work / 'Donut-Agent-Kit-windows-app-only'; root.mkdir()
    app = root / 'app'; app.mkdir()
    for origin, name in [(native / 'donutbrowser.exe', 'donutbrowser-kit.exe'),
                         (native / 'donut-proxy.exe', 'donut-proxy.exe'),
                         (binaries / 'xray-x86_64-pc-windows-msvc.exe', 'xray.exe')]:
        with origin.open('rb') as stream:
            if stream.read(2) != b'MZ':
                raise RuntimeError('Native PE binary required')
        shutil.copy2(origin, app / name)
    (app / '.portable').write_bytes(b'')
    (root / 'Open manager.cmd').write_text(
        '@echo off\r\nsetlocal\r\nset "DONUTBROWSER_DATA_ROOT=%~dp0state"\r\n'
        'set "TEMP=%~dp0state\\tmp"\r\nset "TMP=%TEMP%"\r\n'
        'if not exist "%TEMP%" mkdir "%TEMP%"\r\n'
        'start "" "%~dp0app\\donutbrowser-kit.exe"\r\n', encoding='ascii')
    shutil.copy2(source / '146_Cl.txt', root / '146_Cl.txt')
    shutil.copy2(source / 'LICENSE', root / 'LICENSE-Donut-AGPL-3.0.txt')
    shutil.copy2(binaries / 'xray-LICENSE.txt', root / 'LICENSE-Xray.txt')
    shutil.copy2(source / 'distribution/WINDOWS-NATIVE.md', root / 'START_HERE.md')
    shutil.copy2(source / 'distribution/AGENT-GUIDE.md', root / 'AGENT-GUIDE.md')
    shutil.copy2(source / 'distribution/CLIENTS.md', root / 'CLIENTS.md')
    (root / 'KIT.json').write_text(json.dumps({'productRelease': '1.33', 'engineBundled': False,
        'status': 'native-manager-app-only; not a refreshed CBrowser engine',
        'newEngineBlocker': 'Official current155/156 distribution and local license required',
        'nativeBrowserSmoke': False, 'secretsIncluded': False}, indent=2), encoding='utf-8')
    with zipfile.ZipFile(root / 'Donut-source.zip', 'w', zipfile.ZIP_DEFLATED) as archive:
        ignored = {'node_modules', '.git', '.next', 'target', 'dist', 'gen', '__pycache__', '.driver', '.local'}
        for folder, dirs, names in os.walk(source):
            dirs[:] = [d for d in dirs if d not in ignored]
            for name in names:
                path = Path(folder) / name
                if path.is_symlink() or name.startswith('.env') or path.suffix in {'.exe', '.dll', '.pdb', '.log', '.pyc', '.tsbuildinfo'}:
                    continue
                archive.write(path, path.relative_to(source))
    files = {p.relative_to(root).as_posix(): digest(p) for p in root.rglob('*') if p.is_file()}
    (root / 'MANIFEST.json').write_text(json.dumps({'files': files}, indent=2), encoding='utf-8')
    for name, expected in files.items():
        if digest(root / name) != expected:
            raise RuntimeError('Payload integrity mismatch')
    artifact = output / 'Donut-Agent-Kit-1.33-windows-x64-app-only.zip'
    with zipfile.ZipFile(artifact, 'w', zipfile.ZIP_DEFLATED) as archive:
        for p in root.rglob('*'):
            if p.is_file():
                archive.write(p, Path(root.name) / p.relative_to(root))
    (output / 'SHA256.json').write_text(json.dumps({artifact.name: digest(artifact)}, indent=2), encoding='utf-8')
    print(json.dumps({'ok': True, 'archive': str(artifact), 'engineBundled': False,
                      'nativeWindowsCompiled': True, 'nativeBrowserSmoke': False}))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--work', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    build(parser.parse_args())
