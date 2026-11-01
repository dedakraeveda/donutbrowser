import importlib.util
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location('linux_kit', Path(__file__).with_name('kit_linux.py'))
kit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(kit)


class LinuxKitTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.app = self.root / 'app/donutbrowser-kit'
        self.app.parent.mkdir()
        self.app.write_bytes(b'\x7fELF-test-fixture')
        self.app.chmod(0o755)
        self.patches = [patch.object(kit, k, v) for k, v in {
            'ROOT': self.root, 'APP': self.app, 'STATE': self.root / 'state',
            'CONFIG': self.root / 'state/launcher.local.json'}.items()]
        for p in self.patches:
            p.start()
    def tearDown(self):
        for p in reversed(self.patches):
            p.stop()
        self.temp.cleanup()
    def test_app_only_has_no_fake_engine(self):
        self.assertIsNone(kit.engine())
    def test_missing_engine_rejects_before_state_write(self):
        with patch.dict(os.environ, {'DISPLAY': ':123'}):
            with self.assertRaisesRegex(ValueError, 'linux-cbrowser-required'):
                kit.preflight()
        self.assertFalse((self.root / 'state').exists())
    def test_windows_engine_rejected(self):
        browser = self.root / 'cbrowser/chrome'
        browser.parent.mkdir()
        browser.write_bytes(b'MZ-Windows-not-Linux')
        browser.chmod(0o755)
        with patch.dict(os.environ, {'DISPLAY': ':123'}):
            with self.assertRaisesRegex(ValueError, 'native-linux-engine-invalid'):
                kit.preflight()
    def test_manifest_rejects_traversal(self):
        (self.root / 'MANIFEST.json').write_text(json.dumps({'files': {'../outside': 'bad'}}))
        with self.assertRaisesRegex(ValueError, 'manifest-path-invalid'):
            kit.integrity()
    def test_manifest_rejects_tampering(self):
        (self.root / 'MANIFEST.json').write_text(json.dumps({'files': {'app/donutbrowser-kit': 'bad'}}))
        with self.assertRaisesRegex(ValueError, 'payload-hash-mismatch'):
            kit.integrity()
    def test_relative_external_engine_ignored(self):
        kit.CONFIG.parent.mkdir()
        kit.CONFIG.write_text('{"enginePath":"relative/chrome"}')
        self.assertIsNone(kit.engine())


if __name__ == '__main__':
    unittest.main(verbosity=2)
