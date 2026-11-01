"""Download pinned public original into a disposable native macOS ARM64 job."""
from pathlib import Path
import hashlib
import json
import os
import platform
import plistlib
import shutil
import struct
import subprocess
import urllib.request

ROOT = Path(os.environ['RUNNER_TEMP']) / 'donut-arm-native-probe'
URL = 'https://download.wayfern.com/wayfern_155.0.8059.79-1.1_macos.dmg'
SHA = '4a4e1f58e489eda94cdd9bb1ed7a44fc88127ea831082870ea4f96541413c248'
FRAMEWORK_SHA = '9179fcaa2bd927237622272f68ac9a4a3fbed5bb21da7afab543ae0b76e55816'


def digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


assert platform.system() == 'Darwin' and platform.machine() == 'arm64'
assert not ROOT.exists()
assert shutil.disk_usage(ROOT.parent).free >= 9 * 2**30, 'Native VM peak disk budget'
ROOT.mkdir()
report = {'scope': 'unmodified official ARM64 baseline, not an own fork release',
          'platform': platform.platform(), 'sourceUrl': URL, 'sha256': SHA,
          'signatureScope': 'macOS codesign verification, not a notarization claim',
          'freeBytesBefore': shutil.disk_usage(ROOT).free}
archive = ROOT / 'official-wayfern.dmg'
with urllib.request.urlopen(URL, timeout=90) as response, archive.open('xb') as target:
    shutil.copyfileobj(response, target, length=2**20)
assert digest(archive) == SHA, 'Original DMG differs from locally observed exact original'
mount = ROOT / 'mount'
mount.mkdir()
subprocess.run(['hdiutil', 'attach', '-readonly', '-nobrowse', '-mountpoint', str(mount), str(archive)], check=True, capture_output=True)
try:
    source = mount / 'Wayfern.app'
    assert source.is_dir() and not source.is_symlink()
    for path in source.rglob('*'):
        if path.is_symlink():
            assert path.resolve().is_relative_to(source.resolve()), 'External app symlink refused'
    shutil.copytree(source, ROOT / 'Wayfern.app', symlinks=True)
finally:
    subprocess.run(['hdiutil', 'detach', str(mount)], check=True, capture_output=True)
app = ROOT / 'Wayfern.app'
framework = app / 'Contents/Frameworks/Wayfern Framework.framework/Versions/155.0.8059.79/Wayfern Framework'
assert digest(framework) == FRAMEWORK_SHA
with framework.open('rb') as stream:
    magic, cpu = struct.unpack('<II', stream.read(8))
assert magic == 0xfeedfacf and cpu == 0x100000c
verified = subprocess.run(['codesign', '--verify', '--deep', '--strict', '--verbose=2', str(app)], capture_output=True, text=True)
report['stockCodeSignatureValid'] = verified.returncode == 0
report['stockCodeSignatureDiagnostic'] = (verified.stdout + verified.stderr)[-1800:]
report['frameworkSha256'] = FRAMEWORK_SHA
report['freeBytesAfterUnpack'] = shutil.disk_usage(ROOT).free
(ROOT / 'INPUT.json').write_text(json.dumps(report, indent=2))
assert verified.returncode == 0, 'Original app signature check failed; no signing bypass'
(ROOT / 'package.json').write_text(json.dumps({'private': True, 'dependencies': {'playwright': '1.63.0-alpha-2026-08-31'}}))
print(json.dumps(report, indent=2))
