#!/usr/bin/env python3
"""Linux launcher for Donut Agent Kit; no credential migration or browser substitution."""
import argparse
import datetime
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parent
APP = ROOT / 'app/donutbrowser-kit'
STATE = ROOT / 'state'
CONFIG = STATE / 'launcher.local.json'


def envelope(op, result):
    return {'ok': True, 'operation': op, 'contractVersion': 1, 'result': result,
            'evidence': {'verifiedAt': datetime.datetime.now(datetime.timezone.utc).isoformat(),
                         'scope': str(ROOT), 'status': 'local-check'}}


def manifest():
    return json.loads((ROOT / 'MANIFEST.json').read_text(encoding='utf-8'))


def integrity():
    data = manifest()
    for relative, expected in data['files'].items():
        path = (ROOT / relative).resolve()
        if not path.is_relative_to(ROOT) or not path.is_file():
            raise ValueError('manifest-path-invalid')
        digest = hashlib.sha256()
        with path.open('rb') as stream:
            for chunk in iter(lambda: stream.read(1024 * 1024), b''):
                digest.update(chunk)
        if digest.hexdigest() != expected:
            raise ValueError('payload-hash-mismatch')
    return len(data['files'])


def engine():
    bundled = ROOT / 'cbrowser/chrome'
    if bundled.is_file():
        return bundled
    if CONFIG.is_file():
        data = json.loads(CONFIG.read_text(encoding='utf-8'))
        path = Path(data.get('enginePath', '')).expanduser()
        if path.is_absolute() and path.is_file():
            return path
    return None


def running():
    found = []
    for directory in Path('/proc').iterdir():
        if not directory.name.isdigit():
            continue
        try:
            if (directory / 'exe').resolve() == APP:
                found.append(int(directory.name))
        except (PermissionError, FileNotFoundError, OSError):
            pass
    return sorted(found)


def preflight(require_engine=True):
    if sys.platform != 'linux' or not APP.is_file() or not os.access(APP, os.X_OK):
        raise ValueError('native-app-missing')
    if shutil.disk_usage(ROOT).free < 2 * 2**30:
        raise ValueError('destination-disk-low')
    if not os.environ.get('DISPLAY') and not os.environ.get('WAYLAND_DISPLAY'):
        raise ValueError('graphical-session-required')
    selected = engine()
    if require_engine and selected is None:
        raise ValueError('linux-cbrowser-required')
    if selected:
        with selected.open('rb') as stream:
            magic = stream.read(4)
        if not os.access(selected, os.X_OK) or magic != b'\x7fELF':
            raise ValueError('native-linux-engine-invalid')
    return selected


def launch():
    selected = preflight()
    count = integrity()
    pids = running()
    if pids:
        return {'alreadyRunning': True, 'runningPids': pids, 'liveMcpChecked': False}
    settings = STATE / 'data/settings/app_settings.json'
    settings.parent.mkdir(parents=True, exist_ok=True)
    if not settings.exists():
        try:
            with settings.open('x', encoding='utf-8') as stream:
                json.dump({'onboarding_completed': True, 'disable_auto_updates': True,
                           'cloak_binary_path': str(selected)}, stream)
            settings.chmod(0o600)
        except FileExistsError:
            pass
    cache = STATE / 'cache'
    cache.mkdir(exist_ok=True)
    geo = cache / 'GeoLite2-City.mmdb'
    if not geo.exists() and (ROOT / 'assets/GeoLite2-City.mmdb').is_file():
        with geo.open('xb') as dest, (ROOT / 'assets/GeoLite2-City.mmdb').open('rb') as source:
            shutil.copyfileobj(source, dest)
    temp = STATE / 'tmp'
    temp.mkdir(exist_ok=True)
    child_env = {k: v for k, v in os.environ.items()
                 if not k.startswith(('DONUT', 'BROWSER_', 'WEBKIT_INSPECTOR'))}
    child_env.update(DONUTBROWSER_DATA_ROOT=str(STATE), BROWSER_BINARY_PATH=str(selected),
                     BROWSER_VERSION=(ROOT / '146_Cl.txt').read_text(encoding='utf-8').splitlines()[0],
                     TMPDIR=str(temp), TMP=str(temp), TEMP=str(temp))
    # GUI launch is explicit. No shell, no inherited agent protocol/log pipes.
    with (STATE / 'launcher.log').open('ab') as log:
        child = subprocess.Popen([str(APP)], cwd=APP.parent, env=child_env,
                                 stdin=subprocess.DEVNULL, stdout=log, stderr=log,
                                 close_fds=True, start_new_session=True)
    time.sleep(3)
    if child.poll() is not None:
        raise ValueError('manager-exited-check-system-dependencies')
    return {'pid': child.pid, 'processAlive': True, 'cbrowserRelease': '1.33',
            'payloadFilesVerified': count, 'liveMcpChecked': False}


def main():
    parser = argparse.ArgumentParser(description='Donut Agent Kit Linux launcher; read START_HERE.md')
    parser.add_argument('operation', nargs='?', default='launch',
                        choices=['capabilities', 'status', 'preflight', 'plan', 'verify', 'launch'])
    parser.add_argument('--json', action='store_true')
    args = parser.parse_args()
    try:
        if args.operation == 'capabilities':
            result = {'commands': ['capabilities', 'status', 'preflight', 'plan', 'verify', 'launch'],
                      'cbrowserRelease': '1.33', 'engineBundled': manifest().get('engineBundled', False),
                      'uiRequired': ['User MCP/REST token entry', 'Account login and OTP'],
                      'unsupported': ['Windows engine execution', 'Automatic alternate browser download',
                                      'Credential/profile migration']}
        elif args.operation == 'status':
            result = {'appPresent': APP.is_file(), 'enginePresent': engine() is not None,
                      'engineBundled': manifest().get('engineBundled', False),
                      'cbrowserRelease': '1.33', 'statePresent': STATE.exists(),
                      'runningPids': running(), 'liveMcpChecked': False}
        elif args.operation == 'verify':
            result = {'payloadFilesVerified': integrity(), 'enginePresent': engine() is not None,
                      'runningPids': running(), 'liveMcpChecked': False}
        elif args.operation in {'plan', 'preflight'}:
            selected = preflight()
            result = {'ready': True, 'willLaunch': str(APP), 'browser': str(selected),
                      'writes': [str(STATE)], 'changesInstalledDonut': False,
                      'copiesPersonalProfiles': False}
        else:
            result = launch()
        print(json.dumps(envelope(args.operation, result), ensure_ascii=False))
        return 0
    except Exception as error:
        code = str(error) if isinstance(error, ValueError) else 'internal-error'
        print(json.dumps({'ok': False, 'operation': args.operation, 'contractVersion': 1,
                          'error': {'code': code, 'stage': 'preflight-or-verify', 'retryable': False,
                                    'nextAction': 'Read START_HERE.md and supply your developer-provided Linux CBrowser, not Windows or another engine'}}))
        return 2 if isinstance(error, ValueError) else 1


if __name__ == '__main__':
    sys.exit(main())
