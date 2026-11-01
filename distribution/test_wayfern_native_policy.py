import copy
import hashlib
import importlib.util
import json
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


if __name__ == '__main__':
    unittest.main()
