"""Reproduce the authorized local Wayfern Windows155 candidate, never install it.

Exact baseline and complete output hashes are mandatory. No vendor keys, forged
responses, activation service or Chromium source rebuild are provided here.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import struct
import tempfile

HERE = Path(__file__).resolve().parent
POLICY = json.loads((HERE / 'wayfern-native-policy.json').read_text(encoding='utf8'))
BASELINE_SHA256 = POLICY['sourceSha256']
OUTPUT_SHA256 = POLICY['candidateSha256']
EXE_SHA256 = POLICY['originalExeSha256']
MARKER = 'WAYFERN-FORK.json'
ORIGINAL_INVENTORY_SHA256 = 'f50a6ceec8b4d066abcbd99cd33e701a084b67d9a5c954356eeee9935f9bbb71'
_original_inventory = (HERE / 'wayfern-original-files.json').read_bytes()
if hashlib.sha256(_original_inventory).hexdigest() != ORIGINAL_INVENTORY_SHA256:
    raise ValueError('original-inventory-checksum-mismatch')
ORIGINAL_FILES = json.loads(_original_inventory)['files']


def digest(path: Path) -> str:
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def offset(data: bytes, rva: int, length: int) -> int:
    if len(data) < 64 or data[:2] != b'MZ':
        raise ValueError('invalid-pe')
    pe = struct.unpack_from('<I', data, 60)[0]
    if pe + 24 > len(data) or data[pe:pe+4] != b'PE\0\0':
        raise ValueError('invalid-pe')
    machine, count = struct.unpack_from('<HH', data, pe+4)
    optional = struct.unpack_from('<H', data, pe+20)[0]
    if machine != 0x8664 or not 0 < count < 100:
        raise ValueError('unsupported-pe')
    found = []
    for index in range(count):
        at = pe+24+optional+40*index
        if at+40 > len(data):
            raise ValueError('invalid-section-table')
        _, va, size, raw = struct.unpack_from('<IIII', data, at+8)
        if va <= rva and rva+length <= va+size:
            target = raw+rva-va
            if target+length > len(data):
                raise ValueError('patch-outside-file')
            found.append(target)
    if len(found) != 1:
        raise ValueError('ambiguous-or-unmapped-rva')
    return found[0]


def patched(data: bytes) -> bytes:
    if hashlib.sha256(data).hexdigest() != BASELINE_SHA256:
        raise ValueError('unrecognized-original-dll')
    output = bytearray(data)
    touched: set[int] = set()
    for row in POLICY['patches']:
        before, after = bytes.fromhex(row['before']), bytes.fromhex(row['after'])
        if len(before) != len(after) or not before:
            raise ValueError('invalid-patch-width')
        at = offset(data, int(row['rva'], 16), len(before))
        region = set(range(at, at+len(before)))
        if touched & region or data[at:at+len(before)] != before:
            raise ValueError('overlap-or-preimage-mismatch')
        touched |= region
        output[at:at+len(after)] = after
    result = bytes(output)
    if hashlib.sha256(result).hexdigest() != OUTPUT_SHA256:
        raise ValueError('native-postimage-mismatch')
    return result


def source_inventory(root: Path) -> dict[str, str]:
    if not root.is_dir() or root.is_symlink() or root.is_junction():
        raise ValueError('regular-source-required')
    inventory = {}
    for p in root.rglob('*'):
        if p.is_symlink() or p.is_junction():
            raise ValueError('source-links-rejected')
        if p.name.lower() in {'cookies', 'history', 'login data', 'local state', 'profiles', 'state', 'default'} or p.name.lower().startswith('.env'):
            raise ValueError('private-browser-state-rejected')
        if p.is_file():
            inventory[p.relative_to(root).as_posix()] = digest(p)
    if inventory.get('chrome.dll') != BASELINE_SHA256 or inventory.get('chrome.exe') != EXE_SHA256:
        raise ValueError('unrecognized-original-engine')
    if MARKER in inventory or 'WAYFERN-MANIFEST.json' in inventory:
        raise ValueError('source-already-modified')
    if inventory != ORIGINAL_FILES:
        raise ValueError('original-resource-inventory-mismatch')
    return inventory


def verify(root: Path) -> dict:
    if not root.is_dir() or root.is_symlink() or root.is_junction():
        raise ValueError('regular-result-required')
    marker = json.loads((root / MARKER).read_text(encoding='utf8'))
    manifest = json.loads((root / 'WAYFERN-MANIFEST.json').read_text(encoding='utf8'))
    if marker != marker_body():
        raise ValueError('unrecognized-marker')
    actual = {p.relative_to(root).as_posix(): digest(p) for p in root.rglob('*') if p.is_file() and p.name != 'WAYFERN-MANIFEST.json'}
    if any(p.is_symlink() or p.is_junction() for p in root.rglob('*')) or actual != manifest['files']:
        raise ValueError('payload-manifest-mismatch')
    if actual.get('chrome.dll') != OUTPUT_SHA256 or actual.get('chrome.exe') != EXE_SHA256:
        raise ValueError('native-runtime-mismatch')
    resources = dict(actual)
    resources.pop(MARKER)
    expected = dict(ORIGINAL_FILES)
    expected['chrome.dll'] = OUTPUT_SHA256
    if resources != expected:
        raise ValueError('result-resource-inventory-mismatch')
    return {'ok': True, 'files': len(actual), 'dllSha256': OUTPUT_SHA256, 'releaseEligible': False, 'managerIntegrationVerified': False}


def marker_body() -> dict:
    return {'schemaVersion': 1, 'policyId': 'authorized-local-v1', 'platform': 'windows-x64',
            'technicalVersion': '155.0.8059.79', 'exeSha256': EXE_SHA256,
            'dllSha256': OUTPUT_SHA256, 'sourceRebuilt': False,
            'licenseMode': 'offline-local', 'vendorCredentialsIncluded': False}


def apply(source: Path, destination: Path) -> dict:
    if os.name != 'nt':
        raise ValueError('windows-apply-only')
    if destination.exists() or destination.is_symlink() or destination.is_junction() or not destination.parent.is_dir() or destination.resolve().drive.upper() == 'C:':
        raise ValueError('new-non-system-destination-required')
    if destination.resolve().is_relative_to(source.resolve()) or source.resolve().is_relative_to(destination.resolve()):
        raise ValueError('overlapping-source-destination')
    inventory = source_inventory(source)
    needed = sum((source/n).stat().st_size for n in inventory) + 1024**3
    if shutil.disk_usage(destination.parent).free < max(20*1024**3+needed, needed*2):
        raise ValueError('destination-disk-budget')
    replacement = patched((source/'chrome.dll').read_bytes())
    stage = Path(tempfile.mkdtemp(prefix='wayfern-policy-', dir=destination.parent))
    try:
        for name, expected in inventory.items():
            target = stage/name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source/name, target)
            if digest(target) != expected:
                raise ValueError('source-changed-during-copy')
        (stage/'chrome.dll').write_bytes(replacement)
        (stage/MARKER).write_text(json.dumps(marker_body(), indent=2)+'\n', encoding='utf8')
        files = {p.relative_to(stage).as_posix(): digest(p) for p in stage.rglob('*') if p.is_file()}
        (stage/'WAYFERN-MANIFEST.json').write_text(json.dumps({'files': files}, indent=2)+'\n', encoding='utf8')
        result = verify(stage)
        if destination.exists() or destination.is_symlink() or destination.is_junction():
            raise ValueError('destination-created-concurrently')
        stage.rename(destination)
        return dict(result, destination=str(destination), installedApplicationChanged=False)
    finally:
        # Only the fresh staging directory created by this invocation, never
        # destination/source or a substituted reparse point. A completed rename
        # leaves nothing to clean; all failed copies remain unpublished.
        if stage.exists() and not stage.is_symlink() and not stage.is_junction():
            shutil.rmtree(stage)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('operation', choices=['capabilities', 'status', 'preflight', 'plan', 'apply', 'verify'])
    parser.add_argument('--source', type=Path)
    parser.add_argument('--destination', type=Path)
    a = parser.parse_args()
    if a.operation == 'capabilities':
        result = {'operations': ['status', 'preflight', 'plan', 'apply', 'verify'], 'platform': 'windows-x64', 'installedAppChanges': False, 'vendorCredentialAccess': False}
    elif a.operation == 'status':
        result = dict(marker_body(), releaseEligible=False, nativeProtocolTestsPassed=True, managerIntegrationVerified=False)
    elif a.operation in ['preflight', 'plan']:
        if not a.source:
            parser.error('--source required')
        inventory = source_inventory(a.source)
        patched((a.source/'chrome.dll').read_bytes())
        result = {'ok': True, 'sourceFiles': len(inventory), 'patches': POLICY['patches'], 'sourceUnchanged': True}
    elif a.operation == 'apply':
        if not a.source or not a.destination:
            parser.error('--source and --destination required')
        result = apply(a.source, a.destination)
    else:
        if not a.destination:
            parser.error('--destination required')
        result = verify(a.destination)
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    try:
        main()
    except (ValueError, OSError, KeyError) as error:
        print(json.dumps({'ok': False, 'error': str(error)}))
        raise SystemExit(2)
