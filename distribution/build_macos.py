#!/usr/bin/env python3
"""Prepare native macOS .app/.zip/.dmg on a Mac/Xcode runner; no private core rebuild."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import plistlib
import shutil
import subprocess
import sys
import tarfile

REPO = Path(__file__).resolve().parents[1]


def run(command, cwd, env):
    subprocess.run([str(x) for x in command], cwd=cwd, env=env, check=True)


def digest(path):
    value = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            value.update(chunk)
    return value.hexdigest()


def prepare_source(destination):
    if destination.exists():
        raise FileExistsError('Refuse to overwrite source snapshot')
    if (REPO / '.git').exists():
        names = subprocess.check_output(['git', 'ls-files', '--cached', '--others', '--exclude-standard', '-z'], cwd=REPO).decode().split('\0')
    else:
        inventory = REPO / '.kit-source-inventory.json'
        if not inventory.is_file():
            raise RuntimeError('Use a Git checkout or the verified prepared source archive')
        files = json.loads(inventory.read_text(encoding='utf-8'))['files']
        names = list(files)
        for name, expected in files.items():
            relative = Path(name)
            original = REPO / relative
            path = original.resolve()
            if relative.is_absolute() or '..' in relative.parts or original.is_symlink() or not path.is_relative_to(REPO.resolve()) or not path.is_file() or digest(path) != expected:
                raise ValueError('Prepared source inventory mismatch')
    ignored = {'.git', 'node_modules', '.local', 'target', '.next', '__pycache__', 'state'}
    for name in names:
        if not name:
            continue
        relative = Path(name)
        source = REPO / relative
        if any(p in ignored for p in relative.parts) or source.is_symlink() or not source.is_file():
            continue
        if relative.name == 'TASK-STATE.md' or relative.name.startswith('.env'):
            continue
        if source.suffix in {'.exe', '.dll', '.pdb', '.pyc', '.log', '.zip'}:
            continue
        target = destination / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
    config = destination / 'src-tauri/tauri.conf.json'
    data = json.loads(config.read_text(encoding='utf-8'))
    data['identifier'] = 'com.donutbrowser.agentkit'
    data['productName'] = 'Donut Agent Kit'
    data['bundle']['macOS']['minimumSystemVersion'] = '12.0'
    config.write_text(json.dumps(data, indent=2), encoding='utf-8')
    inventory = {p.relative_to(destination).as_posix(): digest(p) for p in destination.rglob('*') if p.is_file() and not p.is_symlink()}
    (destination / '.kit-source-inventory.json').write_text(json.dumps({'files': inventory}, indent=2), encoding='utf-8')


def build(args):
    if sys.platform != 'darwin':
        raise RuntimeError('Real Mac with Xcode SDK required; this is not a Windows/Linux cross-build')
    work = args.work.resolve()
    output = args.output.resolve()
    if work.exists() or output.exists():
        raise FileExistsError('Work/output must be new directories')
    work.mkdir(parents=True)
    if shutil.disk_usage(work).free < 12 * 2**30:
        raise RuntimeError('Need at least12GiB free on Mac build volume')
    source = work / 'source'
    prepare_source(source)
    temp = work / 'tmp'; temp.mkdir()
    env = {k: v for k, v in os.environ.items() if not any(s in k.upper() for s in ['TOKEN', 'PASSWORD', 'SECRET', 'API_KEY', 'LICENSE_KEY', 'APPLE_', 'DONUT_', 'BROWSER_', 'TAURI_SIGNING_'])}
    env.update(TMPDIR=str(temp), TMP=str(temp), TEMP=str(temp), CARGO_TARGET_DIR=str(work / 'target'),
               CARGO_BUILD_JOBS='2', CARGO_INCREMENTAL='0', BUILD_TAG='0.29.6-authorized.7-kit1',
               NEXT_PUBLIC_DONUT_LOCAL_FEATURES='1', NEXT_TELEMETRY_DISABLED='1', PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD='1',
               npm_config_cache=str(work / 'npm-cache'), PNPM_HOME=str(work / 'pnpm-home'))
    run(['xcrun', '--find', 'clang'], source, env)
    run(['rustup', 'target', 'add', args.target], source, env)
    run(['pnpm', 'install', '--frozen-lockfile', '--ignore-scripts', '--store-dir', str(work / 'pnpm-store')], source, env)
    # Direct CLI avoids the source .env loader and runs the exact checked-in frontend.
    run(['node', 'node_modules/next/dist/bin/next', 'build', '--webpack'], source, env)
    run(['node', 'src-tauri/download-xray.mjs', '--target', args.target], source, env)
    manifest = source / 'src-tauri/Cargo.toml'
    run(['cargo', 'build', '--release', '--locked', '--target', args.target, '--manifest-path', manifest, '--bin', 'donut-proxy'], source, env)
    binaries = work / 'target' / args.target / 'release'
    shutil.copy2(binaries / 'donut-proxy', source / 'src-tauri/binaries' / ('donut-proxy-' + args.target))
    run(['cargo', 'build', '--release', '--locked', '--target', args.target, '--manifest-path', manifest, '--bin', 'donutbrowser'], source, env)
    arch = 'arm64' if args.target.startswith('aarch64') else 'x86_64'
    platform = 'darwin-arm64' if arch == 'arm64' else 'darwin-x64'
    engine = None
    provenance = None
    if args.engine_mode == 'upstream-legacy':
        engine = work / 'engine'
        run([sys.executable, source / 'distribution/fetch_upstream_engine.py', '--platform', platform, '--destination', engine], source, env)
        provenance = json.loads((engine / 'ENGINE-PROVENANCE.json').read_text())
    output.mkdir(parents=True)
    app = work / 'Donut Agent Kit.app'
    macos = app / 'Contents/MacOS'; macos.mkdir(parents=True)
    resources = app / 'Contents/Resources'; resources.mkdir()
    for original, name in [(binaries / 'donutbrowser', 'donutbrowser-kit'), (binaries / 'donut-proxy', 'donut-proxy'),
                           (source / 'src-tauri/binaries' / ('xray-' + args.target), 'xray')]:
        shutil.copy2(original, macos / name)
        (macos / name).chmod(0o755)
    for name in ['donutbrowser-kit', 'donut-proxy', 'xray']:
        run(['file', macos / name], source, env)
        run(['codesign', '--force', '--sign', '-', macos / name], source, env)
    info = {'CFBundleName': 'Donut Agent Kit', 'CFBundleDisplayName': 'Donut Agent Kit',
            'CFBundleIdentifier': 'com.donutbrowser.agentkit', 'CFBundleExecutable': 'DonutAgentKit',
            'CFBundlePackageType': 'APPL', 'CFBundleShortVersionString': '1.33', 'CFBundleVersion': '1330',
            'LSMinimumSystemVersion': '12.0', 'NSHighResolutionCapable': True,
            'NSCameraUsageDescription': 'Camera access is optional and requires your permission.',
            'NSMicrophoneUsageDescription': 'Microphone access is optional and requires your permission.'}
    (app / 'Contents/Info.plist').write_bytes(plistlib.dumps(info))
    if engine:
        shutil.copytree(engine, resources / 'cbrowser', symlinks=True)
    for name in ['146_Cl.txt', 'LICENSE']:
        shutil.copy2(source / name, resources / name)
    shutil.copy2(source / 'distribution/MACOS.md', resources / 'START_HERE.md')
    docs = resources / 'docs'; docs.mkdir()
    for name in ['AGENT-GUIDE.md', 'CLIENTS.md', 'STACK.md', 'UPSTREAM-146-AUDIT.md']:
        shutil.copy2(source / 'distribution' / name, docs / name)
    metadata = {'cbrowserRelease': '1.33', 'engineBundled': engine is not None, 'upstream': provenance,
                'engineTechnicalVersion': provenance['technicalVersion'] if provenance else None,
                'engineExecutable': 'cbrowser/Chromium.app/Contents/MacOS/Chromium' if engine else None,
                'macosNativeRunVerified': False, 'signing': 'ad-hoc only; not Developer-ID/notarized'}
    (resources / 'KIT.json').write_text(json.dumps(metadata, indent=2), encoding='utf-8')
    run(['xcrun', 'swiftc', '-O', '-target', arch + '-apple-macosx12.0', source / 'distribution/MacLauncher.swift', '-o', macos / 'DonutAgentKit'], source, env)
    # Exclude signing products and the outer signing-mutated launcher to avoid self-reference.
    files = {p.relative_to(app).as_posix(): digest(p) for p in app.rglob('*')
             if p.is_file() and not p.is_symlink() and '_CodeSignature' not in p.parts and p != macos / 'DonutAgentKit'}
    (resources / 'MANIFEST.json').write_text(json.dumps({'files': files, 'excludedSigningProducts': True}, indent=2), encoding='utf-8')
    run(['codesign', '--force', '--sign', '-', '--identifier', 'com.donutbrowser.agentkit', app], source, env)
    run(['codesign', '--verify', '--deep', '--strict', app], source, env)
    run([macos / 'DonutAgentKit', 'verify', '--json'], source, env)
    suffix = '-upstream145-candidate' if engine else '-app-only'
    stem = 'Donut-Agent-Kit-CBrowser-1.33-macos-' + arch + suffix
    run(['ditto', '-c', '-k', '--keepParent', app, output / (stem + '.zip')], source, env)
    run(['hdiutil', 'create', '-format', 'UDZO', '-volname', 'Donut Agent Kit', '-srcfolder', app, output / (stem + '.dmg')], source, env)
    ignored = {'node_modules', '.git', '.local', 'target', 'dist', '.next', 'gen', '__pycache__'}
    with tarfile.open(output / (stem + '-source.tar.gz'), 'w:gz') as archive:
        for directory, dirs, names in os.walk(source):
            dirs[:] = [d for d in dirs if d not in ignored]
            for name in names:
                p = Path(directory) / name
                if p.is_symlink() or p.relative_to(source).parts[:2] == ('src-tauri', 'binaries') and p.suffix not in {'.txt', '.json'}:
                    continue
                if name.startswith('.env') or p.suffix in {'.exe', '.dll', '.pdb', '.pyc', '.log', '.tsbuildinfo'}:
                    continue
                archive.add(p, arcname=p.relative_to(source), recursive=False)
    (output / 'SHA256.json').write_text(json.dumps({p.name: digest(p) for p in output.iterdir() if p.is_file()}, indent=2), encoding='utf-8')
    print(json.dumps({'ok': True, 'output': str(output), 'architecture': arch, 'engineMode': args.engine_mode,
                      'nativeGuiSmoke': 'not-run; requires separate real Mac check', 'notarized': False}))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--target', choices=['aarch64-apple-darwin', 'x86_64-apple-darwin'], required=True)
    parser.add_argument('--work', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--engine-mode', choices=['app-only', 'upstream-legacy'], default='app-only')
    build(parser.parse_args())
