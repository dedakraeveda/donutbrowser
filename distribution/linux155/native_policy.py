"""Exact Linux-x64 authorized native engine reproduction, no installation/auth access.

Uses only pinned public original resources and reviewed native transforms.
A file verification result is not a manager/runtime or production-release claim.
"""
from pathlib import Path
import argparse
import hashlib
import json
import os
import shutil
import struct
import sys
import tempfile

HERE = Path(__file__).resolve().parent
MANIFESTS = {
    'wayfern': '17ec97266e6c090f416b01389b6b188c4e355fbb19bfe7e99aaad819a9f67a3b',
    'cbrowser': 'a387b370eaffa3a14bb728cc1d74efcf23931f4952611238c71bbc165b264a7e',
}


def digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def policy(engine):
    data = (HERE / (engine + '-native-policy.json')).read_bytes()
    if hashlib.sha256(data).hexdigest() != MANIFESTS[engine]:
        raise ValueError('reviewed-policy-manifest-checksum')
    result = json.loads(data)
    if result['platform'] != 'linux-x64' or result['symlinks']:
        raise ValueError('unsupported-policy-resource-shape')
    return result


def inventory(root):
    if not root.is_dir() or root.is_symlink():
        raise ValueError('regular-directory-required')
    result = {}
    for path in root.rglob('*'):
        if path.is_symlink():
            raise ValueError('linked-resource-refused')
        if path.is_file():
            name = path.relative_to(root).as_posix()
            if path.name.lower() in {'cookies', 'login data', 'license.key', 'local state'} or path.name.startswith('.env'):
                raise ValueError('private-state-refused')
            result[name] = digest(path)
    return result


def marker(spec, engine):
    if engine == 'wayfern':
        return {'schemaVersion': 1, 'policyId': 'authorized-local-v1', 'platform': 'linux-x64',
                'technicalVersion': '155.0.8059.79', 'exeSha256': spec['outputSha256'],
                'dllSha256': '', 'sourceRebuilt': False, 'licenseMode': 'offline-local',
                'vendorCredentialsIncluded': False}
    return {'schemaVersion': 1, 'platform': 'linux-x64', 'release': '1.33',
            'technicalVersion': '155.0.8059.39.2', 'exeSha256': spec['outputSha256'],
            'sourceRebuilt': False, 'licenseMode': 'offline-local', 'vendorCredentialsIncluded': False}


def marker_name(engine):
    return 'WAYFERN-FORK.json' if engine == 'wayfern' else 'CBROWSER-FORK.json'


def verify(root, engine):
    spec = policy(engine)
    name = marker_name(engine)
    if json.loads((root / name).read_text()) != marker(spec, engine):
        raise ValueError('invalid-engine-marker')
    expected = dict(spec['files'])
    expected['chrome'] = spec['outputSha256']
    actual = inventory(root)
    actual.pop(name, None)
    if actual != expected:
        raise ValueError('native-resource-inventory-mismatch')
    return {'ok': True, 'platform': 'linux-x64', 'engine': engine, 'filesVerified': len(expected) + 1,
            'executableSha256': spec['outputSha256'], 'releaseEligible': False,
            'managerIntegrationVerified': False, 'installedApplicationChanged': False}


def patch_executable(executable, spec, engine):
    if digest(executable) != spec['sourceSha256']:
        raise ValueError('unsupported-original-executable')
    with executable.open('r+b') as stream:
        header = stream.read(64)
        if header[:6] != bytes.fromhex('7f454c460201') or struct.unpack_from('<H', header, 18)[0] != 62:
            raise ValueError('linux-x64-ELF-required')
        offset = struct.unpack_from('<Q', header, 32)[0]
        entry, count = struct.unpack_from('<HH', header, 54)
        if entry != 56 or not 0 < count < 100:
            raise ValueError('invalid-ELF-program-headers')
        stream.seek(offset)
        segments = [struct.unpack('<IIQQQQQQ', stream.read(entry)) for _ in range(count)]
        touched = []
        for row in spec['patches'] if engine == 'wayfern' else spec['regions']:
            address = int(row['va'], 16)
            if row.get('datasetFile'):
                # Only the one pinned checked-in public dataset is accepted.
                if row['datasetFile'] != '../native-data/155-fingerprint-tables.json':
                    raise ValueError('unknown-dataset')
                data = (HERE.parent / 'native-data/155-fingerprint-tables.json').read_bytes()
                if hashlib.sha256(data).hexdigest() != row['datasetSha256'] or len(data) > row['size']:
                    raise ValueError('dataset-checksum-or-capacity')
                after = data + bytes(row['size'] - len(data))
            else:
                after = bytes.fromhex(row['after'])
            matches = [s[2] + address - s[3] for s in segments
                       if s[0] == 1 and s[3] <= address and address + len(after) <= s[3] + s[5]]
            if len(matches) != 1:
                raise ValueError('ambiguous-or-unmapped-native-region')
            at = matches[0]
            if any(at < end and start < at + len(after) for start, end in touched):
                raise ValueError('overlapping-native-regions')
            stream.seek(at)
            before = stream.read(len(after))
            if 'before' in row:
                if before != bytes.fromhex(row['before']):
                    raise ValueError('native-preimage')
            elif hashlib.sha256(before).hexdigest() != row['beforeSha256']:
                raise ValueError('native-preimage-digest')
            stream.seek(at)
            stream.write(after)
            touched.append((at, at + len(after)))
    if digest(executable) != spec['outputSha256']:
        raise ValueError('native-postimage')


def apply(source, destination, engine):
    if sys.platform != 'linux':
        raise ValueError('native-linux-apply-only')
    if destination.exists() or destination.is_symlink() or not destination.parent.is_dir():
        raise ValueError('new-destination-with-existing-parent-required')
    if destination.resolve().is_relative_to(source.resolve()) or source.resolve().is_relative_to(destination.resolve()):
        raise ValueError('source-destination-overlap')
    spec = policy(engine)
    if inventory(source) != spec['files']:
        raise ValueError('original-full-resource-inventory-mismatch')
    needed = sum((source / name).stat().st_size for name in spec['files'])
    if shutil.disk_usage(destination.parent).free < needed + 2 * 1024**3:
        raise ValueError('destination-disk-budget')
    stage = Path(tempfile.mkdtemp(prefix='native-linux-stage-', dir=destination.parent))
    try:
        shutil.copytree(source, stage, dirs_exist_ok=True)
        if inventory(stage) != spec['files']:
            raise ValueError('source-changed-during-copy')
        patch_executable(stage / 'chrome', spec, engine)
        (stage / marker_name(engine)).write_text(json.dumps(marker(spec, engine), indent=2) + '\n')
        result = verify(stage, engine)
        if destination.exists() or destination.is_symlink():
            raise ValueError('destination-created-concurrently')
        # On Linux rename can replace an empty directory. Refuse that race
        # through renameat2(RENAME_NOREPLACE), not an overwrite-prone rename.
        import ctypes
        libc = ctypes.CDLL(None, use_errno=True)
        fn = libc.renameat2
        fn.argtypes = [ctypes.c_int, ctypes.c_char_p, ctypes.c_int, ctypes.c_char_p, ctypes.c_uint]
        fn.restype = ctypes.c_int
        if fn(-100, os.fsencode(stage), -100, os.fsencode(destination), 1):
            raise OSError(ctypes.get_errno(), 'atomic no-replace publish failed')
        return dict(result, destination=str(destination))
    finally:
        if stage.exists() and not stage.is_symlink():
            shutil.rmtree(stage)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('operation', choices=['capabilities', 'status', 'preflight', 'plan', 'apply', 'verify'])
    parser.add_argument('--engine', choices=list(MANIFESTS), required=True)
    parser.add_argument('--source', type=Path)
    parser.add_argument('--destination', type=Path)
    args = parser.parse_args()
    spec = policy(args.engine)
    if args.operation in ['capabilities', 'status']:
        result = {'operations': ['status', 'preflight', 'plan', 'apply', 'verify'], 'engine': args.engine,
                  'platform': 'linux-x64', 'vendorCredentialsRequired': False, 'changesInstalledApp': False,
                  'outputSha256': spec['outputSha256'], 'releaseEligible': False}
    elif args.operation in ['plan', 'preflight']:
        if not args.source:
            parser.error('--source required')
        if inventory(args.source) != spec['files']:
            raise ValueError('original-resource-inventory-mismatch')
        result = {'ok': True, 'files': len(spec['files']), 'sourcePreserved': True}
    elif args.operation == 'apply':
        if not args.source or not args.destination:
            parser.error('--source and --destination required')
        result = apply(args.source, args.destination, args.engine)
    else:
        if not args.destination:
            parser.error('--destination required')
        result = verify(args.destination, args.engine)
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    try:
        main()
    except (OSError, ValueError, KeyError, struct.error) as error:
        print(json.dumps({'ok': False, 'error': str(error)}))
        raise SystemExit(2)
