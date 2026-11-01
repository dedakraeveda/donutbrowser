"""Reconstruct reviewed source on any native runner; no installation/Git changes."""
from pathlib import Path
import argparse
import hashlib
import importlib.util
import json
import shutil
import stat
import zipfile

HERE = Path(__file__).resolve().parent
ARCHIVE_SHA256 = '62f277cd2f376be920c5bf00b5afac7e952b5ebcffd250ccab487f5ead2e1122'


def prepare(archive: Path, destination: Path):
    if destination.exists() or not destination.parent.is_dir():
        raise ValueError('New destination with existing parent required')
    with archive.open('rb') as f:
        if hashlib.file_digest(f, 'sha256').hexdigest() != ARCHIVE_SHA256:
            raise ValueError('Upstream archive checksum mismatch')
    spec = importlib.util.spec_from_file_location('reviewed_overlay', HERE/'port.py')
    overlay = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(overlay)
    manifest = json.loads((HERE/'manifest.json').read_text())
    # Authenticate every replacement before extracting/writing anything.
    for row in manifest['files']:
        rel = overlay.valid(row['path'])
        if row['after'] is not None:
            data = (HERE/'overlay'/rel).read_bytes()
            if hashlib.sha256(data).hexdigest() != row['after']:
                raise ValueError('Overlay checksum mismatch')
    total = 0
    with zipfile.ZipFile(archive) as z:
        roots = set()
        for entry in z.infolist():
            rel = Path(entry.filename)
            if rel.is_absolute() or '..' in rel.parts or '\\' in entry.filename:
                raise ValueError('Unsafe archive member')
            # Python's ZipFile materializes this upstream documentation link as
            # literal text; never create/follow a filesystem symlink. Preserve
            # the exact baseline used by the previously verified source replay.
            if stat.S_ISLNK(entry.external_attr >> 16) and not (
                entry.filename == 'donutbrowser-0.36.0/CLAUDE.md'
                and z.read(entry) == b'AGENTS.md'
            ):
                raise ValueError('Unapproved archive symlink')
            roots.add(rel.parts[0])
            total += entry.file_size
        if roots != {'donutbrowser-0.36.0'} or total > 128*1024**2:
            raise ValueError('Unexpected upstream archive shape/size')
        if shutil.disk_usage(destination.parent).free < total*3+1024**3:
            raise ValueError('Insufficient destination space')
        staging = destination.with_name(destination.name+'-upstream')
        if staging.exists():
            raise ValueError('Staging already exists')
        staging.mkdir()
        z.extractall(staging)
    upstream = staging/'donutbrowser-0.36.0'
    result = overlay.verify(upstream, True)
    if not result['ok']:
        raise ValueError('Pristine source preflight mismatch')
    shutil.copytree(upstream, destination)
    for row in manifest['files']:
        rel = overlay.valid(row['path'])
        target = destination/rel
        if row['after'] is None:
            if target.exists():
                target.unlink()
        else:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes((HERE/'overlay'/rel).read_bytes())
    result = overlay.verify(destination, False)
    if not result['ok']:
        raise ValueError('Reconstructed source verification failed')
    return dict(result, operation='prepare-native-ci-source', sourceArchiveSha256=ARCHIVE_SHA256)


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--archive', type=Path, required=True)
    p.add_argument('--destination', type=Path, required=True)
    args = p.parse_args()
    print(json.dumps(prepare(args.archive, args.destination), indent=2))
