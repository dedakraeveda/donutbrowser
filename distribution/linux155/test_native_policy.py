import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import struct
import tempfile
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location('linux_native_under_test', Path(__file__).with_name('native_policy.py'))
p = importlib.util.module_from_spec(spec)
spec.loader.exec_module(p)


def fixture():
    data = bytearray(512)
    data[:6] = bytes.fromhex('7f454c460201')
    struct.pack_into('<H', data, 18, 62)
    struct.pack_into('<Q', data, 32, 64)
    struct.pack_into('<HH', data, 54, 56, 1)
    struct.pack_into('<IIQQQQQQ', data, 64, 1, 5, 0, 0x1000, 0, 512, 512, 4096)
    data[256:258] = b'AB'
    after = bytearray(data)
    after[256:258] = b'CD'
    policy = {'sourceSha256': hashlib.sha256(data).hexdigest(),
              'outputSha256': hashlib.sha256(after).hexdigest(),
              'patches': [{'va': '0x1100', 'before': '4142', 'after': '4344'}]}
    return bytes(data), bytes(after), policy


class Tests(unittest.TestCase):
    def test_pinned_public_manifests(self):
        for engine in p.MANIFESTS:
            policy = p.policy(engine)
            self.assertEqual(policy['platform'], 'linux-x64')
            self.assertFalse(policy['sourceRebuilt'])
            self.assertFalse(policy['releaseEligible'])
            self.assertFalse(policy['managerIntegrationVerified'])

    def test_native_linux_marker_matches_manager_contract(self):
        policy = p.policy('wayfern')
        marker = p.marker(policy, 'wayfern')
        self.assertEqual(marker['platform'], 'linux-x64')
        self.assertEqual(marker['dllSha256'], '')
        self.assertEqual(marker['exeSha256'], policy['outputSha256'])
        self.assertFalse(marker['vendorCredentialsIncluded'])

    def test_exact_elf_patch_and_unchanged_nonpatch_bytes(self):
        before, after, policy = fixture()
        with tempfile.TemporaryDirectory() as tmp:
            f = Path(tmp) / 'chrome'
            f.write_bytes(before)
            p.patch_executable(f, policy, 'wayfern')
            self.assertEqual(f.read_bytes(), after)

    def test_unknown_original_fails(self):
        _, _, policy = fixture()
        with tempfile.TemporaryDirectory() as tmp:
            f = Path(tmp) / 'chrome'
            f.write_bytes(b'not ELF')
            with self.assertRaisesRegex(ValueError, 'unsupported-original'):
                p.patch_executable(f, policy, 'wayfern')

    def test_wrong_architecture_fails_even_with_matching_source_hash(self):
        before, _, policy = fixture()
        data = bytearray(before)
        struct.pack_into('<H', data, 18, 183)
        policy['sourceSha256'] = hashlib.sha256(data).hexdigest()
        with tempfile.TemporaryDirectory() as tmp:
            f = Path(tmp) / 'chrome'
            f.write_bytes(data)
            with self.assertRaisesRegex(ValueError, 'ELF-required'):
                p.patch_executable(f, policy, 'wayfern')

    def test_preimage_mandatory(self):
        before, _, policy = fixture()
        policy['patches'][0]['before'] = '0000'
        with tempfile.TemporaryDirectory() as tmp:
            f = Path(tmp) / 'chrome'
            f.write_bytes(before)
            with self.assertRaisesRegex(ValueError, 'preimage'):
                p.patch_executable(f, policy, 'wayfern')

    def test_overlapping_regions_fail(self):
        before, _, policy = fixture()
        policy['patches'].append(copy.deepcopy(policy['patches'][0]))
        # The overlap check happens before the second write/preimage check.
        with tempfile.TemporaryDirectory() as tmp:
            f = Path(tmp) / 'chrome'
            f.write_bytes(before)
            with self.assertRaisesRegex(ValueError, 'overlapping'):
                p.patch_executable(f, policy, 'wayfern')

    def test_postimage_mandatory(self):
        before, _, policy = fixture()
        policy['outputSha256'] = '0' * 64
        with tempfile.TemporaryDirectory() as tmp:
            f = Path(tmp) / 'chrome'
            f.write_bytes(before)
            with self.assertRaisesRegex(ValueError, 'postimage'):
                p.patch_executable(f, policy, 'wayfern')

    def test_private_state_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / 'Cookies').write_bytes(b'fixture only')
            with self.assertRaisesRegex(ValueError, 'private-state'):
                p.inventory(root)

    def test_result_rejects_extra_resource_without_trusting_self_manifest(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / 'chrome').write_bytes(b'reviewed fixture')
            sha = p.digest(root / 'chrome')
            policy = {'files': {'chrome': 'original fixture'}, 'outputSha256': sha}
            (root / p.marker_name('wayfern')).write_text(json.dumps(p.marker(policy, 'wayfern')))
            with patch.object(p, 'policy', return_value=policy):
                self.assertTrue(p.verify(root, 'wayfern')['ok'])
                (root / 'injected.txt').write_text('not reviewed')
                with self.assertRaisesRegex(ValueError, 'inventory-mismatch'):
                    p.verify(root, 'wayfern')


if __name__ == '__main__':
    unittest.main()
