import argparse
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import sys
import tarfile
import tempfile
import unittest
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
TEMP = HERE.parent / '.local/upstream-unit-tmp'
TEMP.mkdir(parents=True, exist_ok=True)


def module(name):
    spec = importlib.util.spec_from_file_location(name, HERE / (name + '.py'))
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


fetcher = module('fetch_upstream_engine')
mac = module('build_macos')
windows = module('build_windows')


class UpstreamTests(unittest.TestCase):
    def test_platform_pins_do_not_pretend_mac145_is146(self):
        data = json.loads((HERE / 'upstream-engines.json').read_text())
        self.assertEqual(data['platforms']['linux-x64']['version'], '146.0.7680.177.5')
        self.assertEqual(data['platforms']['darwin-arm64']['version'], '145.0.7632.109.2')
        self.assertEqual(data['platforms']['darwin-x64']['version'], '145.0.7632.109.2')
        for item in data['platforms'].values():
            self.assertEqual(len(item['sha256']), 64)
            self.assertTrue(item['url'].startswith('https://github.com/CloakHQ/CloakBrowser/releases/download/'))
    def test_checksum_failure_leaves_no_engine(self):
        with tempfile.TemporaryDirectory(dir=TEMP) as temp:
            root = Path(temp)
            archive = root / 'bad.tar.gz'
            archive.write_bytes(b'not-a-browser')
            dest = root / 'engine'
            with self.assertRaisesRegex(ValueError, 'checksum mismatch'):
                fetcher.fetch('linux-x64', dest, archive)
            self.assertFalse(dest.exists())
    def test_existing_engine_not_overwritten(self):
        with tempfile.TemporaryDirectory(dir=TEMP) as temp:
            with self.assertRaises(FileExistsError):
                fetcher.fetch('linux-x64', Path(temp))
    def test_archive_traversal_rejected(self):
        with tempfile.TemporaryDirectory(dir=TEMP) as temp:
            root = Path(temp)
            archive = root / 'escape.tar'
            with tarfile.open(archive, 'w') as writer:
                entry = tarfile.TarInfo('../escaped.txt')
                entry.size = 3
                writer.addfile(entry, io.BytesIO(b'bad'))
            with self.assertRaises(tarfile.FilterError):
                fetcher.extract(archive, root / 'unpack')
            self.assertFalse((root / 'escaped.txt').exists())
    def test_macos_build_rejects_non_mac_before_writes(self):
        with tempfile.TemporaryDirectory(dir=TEMP) as temp:
            root = Path(temp)
            args = argparse.Namespace(work=root / 'work', output=root / 'output')
            with patch.object(mac.sys, 'platform', 'linux'):
                with self.assertRaisesRegex(RuntimeError, 'Real Mac'):
                    mac.build(args)
            self.assertFalse(args.work.exists())
    def test_source_archive_can_be_staged_without_git(self):
        with tempfile.TemporaryDirectory(dir=TEMP) as temp:
            root = Path(temp)
            source = root / 'original'
            source.mkdir()
            config = source / 'src-tauri/tauri.conf.json'
            config.parent.mkdir()
            config.write_text(json.dumps({'bundle': {'macOS': {}}}), encoding='utf-8')
            (source / '.kit-source-inventory.json').write_text(json.dumps({'files': {'src-tauri/tauri.conf.json': mac.digest(config)}}))
            with patch.object(mac, 'REPO', source):
                mac.prepare_source(root / 'snapshot')
            copied = root / 'snapshot/src-tauri/tauri.conf.json'
            self.assertEqual(json.loads(copied.read_text())['identifier'], 'com.donutbrowser.agentkit')
            self.assertTrue((root / 'snapshot/.kit-source-inventory.json').is_file())
    def test_source_archive_rejects_escape_before_writes(self):
        with tempfile.TemporaryDirectory(dir=TEMP) as temp:
            root = Path(temp)
            source = root / 'original'
            source.mkdir()
            file = source / 'source.txt'
            file.write_text('public source')
            (source / '.kit-source-inventory.json').write_text(json.dumps({'files': {'../original/source.txt': mac.digest(file)}}))
            with patch.object(mac, 'REPO', source):
                with self.assertRaisesRegex(ValueError, 'inventory mismatch'):
                    mac.prepare_source(root / 'snapshot')
            self.assertFalse((root / 'snapshot').exists())
    def test_windows_build_rejects_other_hosts_before_writes(self):
        with tempfile.TemporaryDirectory(dir=TEMP) as temp:
            root = Path(temp)
            args = argparse.Namespace(work=root / 'work', output=root / 'output')
            with patch.object(windows.sys, 'platform', 'linux'):
                with self.assertRaisesRegex(RuntimeError, 'Native Windows'):
                    windows.build(args)
            self.assertFalse(args.work.exists())
    def test_fork_push_cannot_publish_production_sidecars(self):
        import yaml
        workflow = HERE.parent / '.github/workflows/publish-sidecars.yml'
        data = yaml.load(workflow.read_text(), Loader=yaml.BaseLoader)
        self.assertEqual(data['jobs']['build']['if'], "github.repository == 'zhom/donutbrowser'")
    def test_windows_workflow_is_manual_read_only(self):
        import yaml
        workflow = HERE.parent / '.github/workflows/agent-kit-windows.yml'
        data = yaml.load(workflow.read_text(), Loader=yaml.BaseLoader)
        self.assertEqual(set(data['on']), {'workflow_dispatch'})
        self.assertEqual(data['permissions'], {'contents': 'read'})
        self.assertNotIn('secrets.', json.dumps(data))
    def test_manual_ci_is_not_publish_or_secret_workflow(self):
        # BaseLoader keeps YAML1.1's 'on' from being interpreted as a boolean.
        import yaml
        data = yaml.load((HERE.parent / '.github/workflows/agent-kit-macos.yml').read_text(), Loader=yaml.BaseLoader)
        self.assertEqual(set(data['on']), {'workflow_dispatch'})
        self.assertEqual(data['permissions'], {'contents': 'read'})
        jobs = data['jobs']['build']
        targets = {p['target'] for p in jobs['strategy']['matrix']['include']}
        self.assertEqual(targets, {'aarch64-apple-darwin', 'x86_64-apple-darwin'})
        self.assertNotIn('secrets.', json.dumps(data))
        self.assertEqual(data['on']['workflow_dispatch']['inputs']['engine_mode']['default'], 'app-only')


if __name__ == '__main__':
    unittest.main(verbosity=2)
