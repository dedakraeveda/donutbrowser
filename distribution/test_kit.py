"""Launcher boundary/unit tests; real browser evidence is separate smoke_kit.mjs."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

EXE = Path(sys.argv[1]).resolve()
TEMP = Path(os.environ.get('DONUT_KIT_TEST_TEMP', 'D:/projects/temp/donut-agent-kit-20261028/launcher-tests'))
TEMP.mkdir(parents=True, exist_ok=True)


class LauncherTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(dir=TEMP)
        self.root = Path(self.temp.name) / 'Folder with spaces'
        self.root.mkdir()
        shutil.copy2(EXE, self.root / EXE.name)
    def tearDown(self):
        self.temp.cleanup()
    def call(self, command, *args):
        p = subprocess.run([str(self.root / EXE.name), command, *args, '--json'], capture_output=True, text=True, creationflags=0x08000000, timeout=15)
        return p.returncode, json.loads(p.stdout)
    def fixture(self):
        files = {}
        for name in ['app/donutbrowser-kit.exe', 'cbrowser/chrome.exe']:
            p = self.root / name
            p.parent.mkdir(exist_ok=True)
            p.write_bytes(b'unit-test-only-not-a-runtime')
            files[name] = hashlib.sha256(p.read_bytes()).hexdigest()
        (self.root / 'MANIFEST.json').write_text(json.dumps({'files':files}))
    def test_capability_envelope(self):
        code, d = self.call('capabilities')
        self.assertEqual(code,0);self.assertTrue(d['ok']);self.assertEqual(d['contractVersion'],1)
        self.assertIn('verify',d['result']['commands'])
    def test_missing_payload_rejected(self):
        code,d=self.call('preflight');self.assertEqual(code,2);self.assertEqual(d['error']['code'],'payload-missing')
    def test_status_does_not_create_state(self):
        code,d=self.call('status');self.assertEqual(code,0);self.assertFalse(d['result']['statePresent']);self.assertFalse((self.root/'state').exists())
    def test_plan_no_writes(self):
        self.fixture();code,d=self.call('plan');self.assertEqual(code,0);self.assertFalse(d['result']['changesInstalledDonut']);self.assertFalse((self.root/'state').exists())
    def test_manifest_roundtrip(self):
        self.fixture();code,d=self.call('verify');self.assertEqual(code,0);self.assertEqual(d['result']['payloadFilesVerified'],2);self.assertFalse(d['result']['liveMcpChecked'])
    def test_manifest_tampering(self):
        self.fixture();(self.root/'cbrowser/chrome.exe').write_bytes(b'changed');code,d=self.call('verify');self.assertEqual(code,2);self.assertEqual(d['error']['code'],'payload-hash-mismatch')
    def test_manifest_traversal(self):
        self.fixture();(self.root/'MANIFEST.json').write_text(json.dumps({'files':{'../outside.txt':'bad'}}));code,d=self.call('verify');self.assertEqual(code,2);self.assertEqual(d['error']['code'],'manifest-path-invalid')
    def test_unknown_arguments(self):
        code,d=self.call('status','--not-supported');self.assertEqual(code,2);self.assertEqual(d['error']['code'],'invalid-arguments')

if __name__=='__main__':
    unittest.main(argv=[sys.argv[0]],verbosity=2)
