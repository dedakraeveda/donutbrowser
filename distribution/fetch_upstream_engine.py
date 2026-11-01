#!/usr/bin/env python3
"""Explicit pinned upstream engine acquisition. Does not claim private core source."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import tarfile
import tempfile
import urllib.request

MANIFEST = Path(__file__).with_name('upstream-engines.json')


def sha256(path):
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


def extract(archive, destination):
    # Python >=3.12's data filter also rejects escaping symlinks/devices.
    if not hasattr(tarfile, 'data_filter'):
        raise RuntimeError('Python with tarfile.data_filter is required for extraction')
    if destination.exists():
        raise FileExistsError('Do not overwrite an existing engine directory')
    with tarfile.open(archive) as source:
        source.extractall(destination, filter='data')


def fetch(platform, destination, archive=None):
    data = json.loads(MANIFEST.read_text(encoding='utf-8'))
    selected = data['platforms'][platform]
    destination = destination.resolve()
    if destination.exists():
        raise FileExistsError('Destination already exists')
    destination.parent.mkdir(parents=True, exist_ok=True)
    if shutil.disk_usage(destination.parent).free < 2 * 2**30:
        raise RuntimeError('Need 2 GiB free on destination volume')
    with tempfile.TemporaryDirectory(prefix='engine-fetch-', dir=destination.parent) as temp:
        downloaded = Path(temp) / 'upstream.tar.gz'
        if archive:
            downloaded = archive.resolve()
        else:
            request = urllib.request.Request(selected['url'], headers={'User-Agent': 'Donut-Agent-Kit-source-audit'})
            with urllib.request.urlopen(request, timeout=120) as source, downloaded.open('xb') as target:
                shutil.copyfileobj(source, target, 1024 * 1024)
        if sha256(downloaded) != selected['sha256']:
            raise ValueError('Pinned upstream archive checksum mismatch')
        extract(downloaded, destination)
    executable = destination / selected['executable']
    if not executable.is_file():
        raise RuntimeError('Expected native executable missing from upstream archive')
    provenance = {'vendor': 'CloakHQ/CloakBrowser', 'binaryModified': False,
                  'privateCoreRebuilt': False, 'platform': platform,
                  'technicalVersion': selected['version'], 'archiveSha256': selected['sha256'],
                  'sourceUrl': selected['url'], 'wrapperSourceCommit': data['source']['commit'],
                  'ourLayer': 'Donut manager/launch/profile/network/MCP integration, not private C++ engine'}
    (destination / 'ENGINE-PROVENANCE.json').write_text(json.dumps(provenance, indent=2), encoding='utf-8')
    notices = destination / 'upstream-notices'
    shutil.copytree(Path(__file__).with_name('upstream-notices'), notices)
    print(json.dumps({'ok': True, 'engineRoot': str(destination), 'platform': platform,
                      'technicalVersion': selected['version'], 'coreRebuiltFromSource': False}))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--platform', required=True, choices=['linux-x64', 'darwin-arm64', 'darwin-x64'])
    parser.add_argument('--destination', type=Path, required=True)
    parser.add_argument('--archive', type=Path, help='Existing official archive; checksum is still mandatory')
    args = parser.parse_args()
    fetch(args.platform, args.destination, args.archive)
