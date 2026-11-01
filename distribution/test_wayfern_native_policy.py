import copy
import hashlib
import importlib.util
import json
import shutil
from pathlib import Path
import struct
import tempfile
import unittest
from unittest.mock import patch

SPEC = importlib.util.spec_from_file_location('wayfern_policy_tested', Path(__file__).with_name('wayfern_native_policy.py'))
p = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(p)


def fixture():
    # One small separate PE section per real patch RVA: never allocate a
    # Chromium-size image merely to test boundary checks.
    rows = p.POLICY['patches']
    data = bytearray(2048+len(rows)*64)
    data[:2] = b'MZ'
    struct.pack_into('<I', data, 60, 128)
    data[128:132] = b'PE\0\0'
    struct.pack_into('<HH', data, 132, 0x8664, len(rows))
    struct.pack_into('<H', data, 148, 0)
    result = bytearray(data)
    for i, row in enumerate(rows):
        raw = 2048+i*64
        rva = int(row['rva'], 16)
        struct.pack_into('<IIII', data, 152+i*40+8, 32, rva, 32, raw)
        data[raw:raw+len(bytes.fromhex(row['before']))] = bytes.fromhex(row['before'])
    result[:] = data
    for i, row in enumerate(rows):
        raw = 2048+i*64
        result[raw:raw+len(bytes.fromhex(row['after']))] = bytes.fromhex(row['after'])
    return bytes(data), bytes(result)


class PolicyTests(unittest.TestCase):
    def test_exact_supported_build_and_no_licence_server_claim(self):
        self.assertEqual(len(p.POLICY['patches']), 12)
        self.assertFalse(p.POLICY['ownSignedLicensingImplemented'])
        self.assertEqual(p.marker_body()['licenseMode'], 'offline-local')
        self.assertFalse(p.marker_body()['sourceRebuilt'])

    def test_exact_transform_all_twelve_regions(self):
        original, expected = fixture()
        with patch.object(p, 'BASELINE_SHA256', hashlib.sha256(original).hexdigest()), patch.object(p, 'OUTPUT_SHA256', hashlib.sha256(expected).hexdigest()):
            self.assertEqual(p.patched(original), expected)
        self.assertEqual(sum(a != b for a, b in zip(original, expected)), 50)

    def test_unknown_source_refused(self):
        with self.assertRaisesRegex(ValueError, 'unrecognized-original'):
            p.patched(b'anything')

    def test_wrong_preimage_refused_even_with_source_hash(self):
        original, _ = fixture()
        damaged = bytearray(original)
        damaged[2048] ^= 1
        with patch.object(p, 'BASELINE_SHA256', hashlib.sha256(damaged).hexdigest()):
            with self.assertRaisesRegex(ValueError, 'preimage'):
                p.patched(bytes(damaged))

    def test_postimage_hash_mandatory(self):
        original, _ = fixture()
        with patch.object(p, 'BASELINE_SHA256', hashlib.sha256(original).hexdigest()):
            with self.assertRaisesRegex(ValueError, 'postimage'):
                p.patched(original)

    def test_overlapping_patch_rejected(self):
        original, _ = fixture()
        policy = copy.deepcopy(p.POLICY)
        policy['patches'].append(policy['patches'][0])
        with patch.object(p, 'POLICY', policy), patch.object(p, 'BASELINE_SHA256', hashlib.sha256(original).hexdigest()):
            with self.assertRaisesRegex(ValueError, 'overlap'):
                p.patched(original)

    def test_section_bounds_and_machine_checked(self):
        original, _ = fixture()
        self.assertEqual(p.offset(original, int(p.POLICY['patches'][0]['rva'], 16), 2), 2048)
        for data, rva in [(b'', 0), (original, 0x7fffffff)]:
            with self.assertRaises(ValueError):
                p.offset(data, rva, 2)
        damaged = bytearray(original)
        struct.pack_into('<H', damaged, 132, 0x14c)
        with self.assertRaisesRegex(ValueError, 'unsupported'):
            p.offset(damaged, 0, 1)

    def test_private_source_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root/'Cookies').write_bytes(b'not real data')
            with self.assertRaisesRegex(ValueError, 'private'):
                p.source_inventory(root)

    def test_unknown_marker_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root/p.MARKER).write_text('{}')
            (root/'WAYFERN-MANIFEST.json').write_text(json.dumps({'files': {}}))
            with self.assertRaisesRegex(ValueError, 'marker'):
                p.verify(root)

    def test_stock_source_not_accepted_as_result(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(OSError):
                p.verify(Path(tmp))

    def test_missing_result_directory_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaisesRegex(ValueError, 'regular-result'):
                p.verify(Path(tmp)/'missing')

    def test_source_resources_are_pinned_not_just_engine(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root/'chrome.exe').write_bytes(b'exe')
            (root/'chrome.dll').write_bytes(b'dll')
            inventory = {n: p.digest(root/n) for n in ['chrome.exe', 'chrome.dll']}
            with patch.object(p, 'EXE_SHA256', inventory['chrome.exe']), patch.object(p, 'BASELINE_SHA256', inventory['chrome.dll']), patch.object(p, 'ORIGINAL_FILES', inventory):
                self.assertEqual(p.source_inventory(root), inventory)
                (root/'unexpected.txt').write_text('must not ship')
                with self.assertRaisesRegex(ValueError, 'original-resource'):
                    p.source_inventory(root)

    def test_rewritten_manifest_cannot_authorize_extra_resources(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root/'chrome.exe').write_bytes(b'exe')
            (root/'chrome.dll').write_bytes(b'dll')
            inventory = {n: p.digest(root/n) for n in ['chrome.exe', 'chrome.dll']}
            with patch.object(p, 'EXE_SHA256', inventory['chrome.exe']), patch.object(p, 'OUTPUT_SHA256', inventory['chrome.dll']), patch.object(p, 'ORIGINAL_FILES', inventory):
                (root/p.MARKER).write_text(json.dumps(p.marker_body()))
                def save_manifest():
                    files = {f.name: p.digest(f) for f in root.iterdir() if f.name != 'WAYFERN-MANIFEST.json'}
                    (root/'WAYFERN-MANIFEST.json').write_text(json.dumps({'files': files}))
                save_manifest()
                self.assertTrue(p.verify(root)['ok'])
                (root/'unexpected.txt').write_text('not reviewed')
                save_manifest()
                with self.assertRaisesRegex(ValueError, 'result-resource'):
                    p.verify(root)

    def test_failed_apply_cleans_only_own_stage(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root/'source'
            source.mkdir()
            (source/'chrome.dll').write_bytes(b'fixture')
            destination = root/'new-output'
            sentinel = root/'keep.txt'
            sentinel.write_text('untouched')
            with patch.object(p.os, 'name', 'nt'), patch.object(p, 'source_inventory', return_value={'chrome.dll':'unused'}), patch.object(p, 'patched', return_value=b'result'), patch.object(p.shutil, 'disk_usage', return_value=shutil.disk_usage(root)._replace(free=100*2**30)), patch.object(p.shutil, 'copy2', side_effect=OSError('simulated copy failure')):
                with self.assertRaisesRegex(OSError, 'simulated'):
                    p.apply(source, destination)
            self.assertFalse(destination.exists())
            self.assertEqual(list(root.glob('wayfern-policy-*')), [])
            self.assertEqual(sentinel.read_text(), 'untouched')
            self.assertEqual((source/'chrome.dll').read_bytes(), b'fixture')


if __name__ == '__main__':
    unittest.main()
