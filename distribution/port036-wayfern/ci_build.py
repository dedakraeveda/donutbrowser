"""Native runner check/build. No secrets, production access or installation."""
from pathlib import Path
import hashlib
import json
import os
import shutil
import subprocess
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[2]
WORK = Path(os.environ['RUNNER_TEMP'])/'port036-native'
SOURCE = WORK/'source'
OUTPUT = WORK/'artifacts'
TARGET = WORK/'target'


def run(args, cwd=SOURCE):
    print('RUN', ' '.join(str(a) for a in args), flush=True)
    subprocess.run([str(a) for a in args], cwd=cwd, env=ENV, check=True,
                   **({'creationflags': 0x08000000} if os.name == 'nt' else {}))


# os.environ on Windows normalizes names to uppercase; preserve that contract
# after copying to a plain dict (the MSVC action emits mixed-case names).
ENV = {(k.upper() if os.name == 'nt' else k): v for k, v in os.environ.items() if not any(s in k.upper() for s in ['TOKEN', 'SECRET', 'PASSWORD', 'API_KEY', 'LICENSE_KEY', 'TAURI_SIGNING_'])}
ENV.update(CARGO_HOME=str(WORK/'cargo-home'), CARGO_TARGET_DIR=str(TARGET),
           CARGO_BUILD_JOBS='2', CARGO_INCREMENTAL='0', CARGO_PROFILE_DEV_DEBUG='0',
           CARGO_PROFILE_RELEASE_LTO='false', CARGO_PROFILE_RELEASE_CODEGEN_UNITS='16',
           RUST_MIN_STACK='16777216', RUST_TEST_THREADS='1',
           BUILD_TAG='0.36.0+authorized.9', NEXT_PUBLIC_DONUT_LOCAL_FEATURES='1',
           NEXT_TELEMETRY_DISABLED='1', PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD='1',
           npm_config_cache=str(WORK/'npm-cache'), npm_config_manage_package_manager_versions='false')
for key in ['TEMP', 'TMP', 'TMPDIR']:
    ENV[key] = str(WORK/'tmp')
(WORK/'tmp').mkdir(parents=True, exist_ok=True)
ENV['DONUTBROWSER_DATA_ROOT'] = str(WORK/'unit-state/DonutBrowserDev')
ENV['WEBVIEW2_USER_DATA_FOLDER'] = str(WORK/'unit-webview')
if os.name == 'nt':
    compiler = Path(ENV['VCTOOLSINSTALLDIR'])/'bin/Hostx64/x64/link.exe'
    if not compiler.is_file():
        raise RuntimeError('Selected MSVC linker missing')
    ENV['PATH'] = str(compiler.parent)+os.pathsep+ENV['PATH']
    ENV['CARGO_TARGET_X86_64_PC_WINDOWS_MSVC_LINKER'] = str(compiler)
print(json.dumps({'platform': sys.platform, 'freeGiB': round(shutil.disk_usage(WORK).free/2**30, 2)}), flush=True)
if shutil.disk_usage(WORK).free < 25*2**30:
    raise RuntimeError('Native runner needs25GiB free')
# pnpm's cmd shim cannot be spawned shell-free on Windows. Call its actual Node
# entry point, resolved from the action's configured installation tree.
PNPM = shutil.which('pnpm')
if not PNPM:
    raise RuntimeError('pnpm absent')
if os.name == 'nt' and Path(PNPM).suffix.lower() != '.exe':
    shim = Path(PNPM)
    roots = [shim.parent/'node_modules/pnpm/bin', shim.parent.parent/'pnpm/bin', shim.parent.parent/'node_modules/pnpm/bin']
    matches = [p for root in roots for p in root.glob('pnpm.*js')]
    if not matches:
        raise RuntimeError('Cannot find real pnpm entry point; no shell fallback')
    PNPM_CMD = ['node', str(matches[0])]
else:
    PNPM_CMD = [PNPM]
run(PNPM_CMD+['install', '--frozen-lockfile', '--ignore-scripts', '--store-dir', str(WORK/'pnpm-store')])
run(PNPM_CMD+['exec', 'tsc', '--noEmit'])
run(PNPM_CMD+['build'])
run(['node', 'src-tauri/download-xray.mjs'])
manifest = SOURCE/'src-tauri/Cargo.toml'
run(['cargo', 'fmt', '--manifest-path', manifest, '--all', '--', '--check'])
run(['cargo', 'check', '--locked', '--manifest-path', manifest, '--all-targets', '--all-features'])
run(['cargo', 'test', '--locked', '--manifest-path', manifest, '--lib', 'wayfern_local_policy', '--', '--test-threads=1'])
run(['cargo', 'test', '--locked', '--manifest-path', manifest, '--lib', 'manual_browser_updates_do_not_prune_downloaded_payloads', '--', '--test-threads=1'])
run(['cargo', 'build', '--locked', '--release', '--manifest-path', manifest, '--bin', 'donut-proxy'])
suffix = '.exe' if os.name == 'nt' else ''
# Existing source helper recognizes CARGO_TARGET_DIR and copies exact host sidecar.
run(['node', 'src-tauri/copy-proxy-binary.mjs', '--release'])
run(['cargo', 'build', '--locked', '--release', '--manifest-path', manifest, '--bin', 'donutbrowser'])
if os.name == 'nt':
    run(['cargo', 'build', '--locked', '--manifest-path', 'e2e/app/Cargo.toml'])
OUTPUT.mkdir()
files = [TARGET/'release'/('donutbrowser'+suffix), TARGET/'release'/('donut-proxy'+suffix)]
if os.name == 'nt':
    files.append(TARGET/'debug/donutbrowser-e2e.exe')
files += list((SOURCE/'src-tauri/binaries').glob('xray-*'))
files += [SOURCE/'LICENSE', ROOT/'distribution/port036-wayfern/manifest.json', ROOT/'AUTHORIZED_FORK.md']
report = {'platform': sys.platform, 'architecture': os.environ.get('BUILD_ARCH'),
          'kind': 'native-manager-binaries-not-full-engine-kit', 'guiRuntimeVerified': False,
          'engineBundled': False, 'installed': False, 'releaseProfile': {'optLevel': 3, 'lto': False, 'codegenUnits': 16}, 'files': {}}
archive = OUTPUT/('Donut036-native-'+os.environ['BUILD_ARCH']+'.zip')
with zipfile.ZipFile(archive, 'x', zipfile.ZIP_DEFLATED) as z:
    for f in files:
        if not f.is_file():
            raise RuntimeError('Required output absent: '+str(f))
        name = f.name
        z.write(f, name)
        with f.open('rb') as stream:
            report['files'][name] = hashlib.file_digest(stream, 'sha256').hexdigest()
with archive.open('rb') as stream:
    report['archiveSha256'] = hashlib.file_digest(stream, 'sha256').hexdigest()
(OUTPUT/'BUILD.json').write_text(json.dumps(report, indent=2)+'\n')
print(json.dumps(report, indent=2))
