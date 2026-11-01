#!/usr/bin/env python3
"""Portable Linux-x64 Donut fork launcher. No personal-state import or vendor keys."""
from pathlib import Path
import argparse
import hashlib
import json
import os
import platform
import shutil
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parent
APP = ROOT / 'app/donutbrowser'
STATE = ROOT / 'state'


def digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def integrity():
    manifest = json.loads((ROOT / 'MANIFEST.json').read_text())
    for name, expected in manifest['files'].items():
        file = ROOT / name
        if not file.resolve().is_relative_to(ROOT) or file.is_symlink() or not file.is_file():
            raise ValueError('payload-path-invalid')
        if digest(file) != expected:
            raise ValueError('payload-hash-mismatch: ' + name)
    return len(manifest['files'])


def running():
    result = []
    for p in Path('/proc').iterdir():
        if p.name.isdigit():
            try:
                if (p / 'exe').resolve() == APP.resolve():
                    result.append(int(p.name))
            except (OSError, RuntimeError):
                pass
    return result


def environment():
    # Fresh local state only. Existing caller credentials/cloud tokens are not
    # propagated to either the manager or the bundled offline engines.
    env = {k: v for k, v in os.environ.items()
           if not k.startswith(('PI_', 'DONUT', 'BROWSER_', 'WAYFERN_', 'CLOAKBROWSER_', 'TAURI_', 'WEBKIT_INSPECTOR'))
           and not any(t in k.upper() for t in ['TOKEN', 'SECRET', 'PASSWORD', 'API_KEY', 'LICENSE_KEY'])}
    home = STATE / 'home'
    env.update(HOME=str(home), XDG_CONFIG_HOME=str(home / '.config'),
               XDG_CACHE_HOME=str(home / '.cache'), XDG_DATA_HOME=str(home / '.local/share'),
               DONUTBROWSER_DATA_ROOT=str(STATE), BROWSER_BINARY_PATH=str(ROOT / 'cbrowser/chrome'),
               BROWSER_VERSION='155.0.8059.39.2', TMPDIR=str(STATE / 'tmp'),
               TMP=str(STATE / 'tmp'), TEMP=str(STATE / 'tmp'))
    for p in [home, home / '.config', home / '.cache', home / '.local/share', STATE / 'tmp']:
        p.mkdir(parents=True, exist_ok=True, mode=0o700)
    return env


def preflight(graphical=False):
    if sys.platform != 'linux' or platform.machine() not in ['x86_64', 'amd64']:
        raise ValueError('linux-x64-required')
    if not APP.is_file() or not os.access(APP, os.X_OK):
        raise ValueError('manager-not-executable')
    if os.geteuid() == 0:
        raise ValueError('run-as-normal-user-not-root; sandbox-is-not-disabled-by-launcher')
    if shutil.disk_usage(ROOT).free < 1024**3:
        raise ValueError('destination-needs-one-GiB-free')
    if graphical and not (os.environ.get('DISPLAY') or os.environ.get('WAYLAND_DISPLAY')):
        raise ValueError('graphical-session-required')
    if len(str(STATE / 'tmp').encode()) > 55:
        raise ValueError('extract-to-shorter-path-for-Chromium-Unix-sockets')
    return {'ok': True, 'managerPresent': True, 'enginesBundled': ['cbrowser', 'wayfern'],
            'sandboxDisabled': False, 'state': str(STATE)}


def initial_state():
    settings = STATE / 'data/settings/app_settings.json'
    settings.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    if not settings.exists():
        with settings.open('x') as stream:
            json.dump({'onboarding_completed': True, 'disable_auto_updates': True,
                       'cloak_binary_path': str(ROOT / 'cbrowser/chrome')}, stream)
        settings.chmod(0o600)
    registry = STATE / 'data/data/downloaded_browsers.json'
    install = STATE / 'data/binaries/wayfern/155.0.8059.79'
    if not registry.exists():
        install.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        if not install.exists():
            install.symlink_to(ROOT / 'wayfern', target_is_directory=True)
        registry.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        with registry.open('x') as stream:
            json.dump({'browsers': {'wayfern': {'155.0.8059.79': {
                'browser': 'wayfern', 'version': '155.0.8059.79', 'file_path': str(install)}}}}, stream)
        registry.chmod(0o600)
    geo = STATE / 'cache/GeoLite2-City.mmdb'
    if not geo.exists():
        geo.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        with geo.open('xb') as target, (ROOT / 'assets/GeoLite2-City.mmdb').open('rb') as source:
            shutil.copyfileobj(source, target)


def launch():
    preflight(graphical=True)
    count = integrity()
    active = running()
    if active:
        return {'alreadyRunning': True, 'pids': active}
    initial_state()
    env = environment()
    with (STATE / 'launcher.log').open('ab') as log:
        proc = subprocess.Popen([str(APP)], cwd=APP.parent, env=env, stdin=subprocess.DEVNULL,
                                stdout=log, stderr=log, close_fds=True, start_new_session=True)
    time.sleep(3)
    if proc.poll() is not None:
        raise ValueError('manager-exited-see-state/launcher.log')
    return {'pid': proc.pid, 'processAlive': True, 'payloadFilesVerified': count,
            'liveBrowserCheckedByThisCommand': False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('operation', nargs='?', default='launch',
                        choices=['capabilities', 'status', 'preflight', 'plan', 'verify', 'launch', 'accept-wayfern-terms'])
    parser.add_argument('--json', action='store_true')
    parser.add_argument('--authorized', action='store_true', help='Explicit informed Wayfern terms acceptance')
    args = parser.parse_args()
    if args.operation == 'capabilities':
        result = {'operations': ['status', 'preflight', 'plan', 'verify', 'launch', 'accept-wayfern-terms'],
                  'engineBundled': True, 'platform': 'linux-x64', 'credentialMigration': False,
                  'uiRequired': ['account login', 'OTP', 'API/MCP token configuration']}
    elif args.operation == 'status':
        result = {'managerPresent': APP.is_file(), 'pids': running(), 'statePresent': STATE.exists(),
                  'liveRuntimeVerifiedByThisCommand': False}
    elif args.operation in ['plan', 'preflight']:
        result = preflight()
    elif args.operation == 'verify':
        result = {'payloadFilesVerified': integrity(), 'runtimeVerifiedByThisCommand': False}
    elif args.operation == 'accept-wayfern-terms':
        if not args.authorized:
            parser.error('Read licenses/Wayfern terms first, then supply --authorized explicitly')
        preflight()
        integrity()
        env = environment()
        completed = subprocess.run([str(ROOT / 'wayfern/chrome'), '--accept-terms-and-conditions'],
                                   cwd=ROOT / 'wayfern', env=env, capture_output=True, timeout=30)
        accepted = Path(env['XDG_CONFIG_HOME']) / 'Wayfern/license-accepted'
        if completed.returncode or not accepted.is_file():
            raise ValueError('official-isolated-terms-acceptance-failed')
        result = {'acceptedByOfficialEngine': True, 'personalMarkerReadOrCopied': False}
    else:
        result = launch()
    print(json.dumps({'ok': True, 'operation': args.operation, 'contractVersion': 1, 'result': result}))


if __name__ == '__main__':
    try:
        main()
    except (OSError, ValueError, KeyError, subprocess.TimeoutExpired) as error:
        print(json.dumps({'ok': False, 'error': str(error)}))
        raise SystemExit(2)
