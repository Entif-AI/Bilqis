"""Independent content framing and historical identity compatibility."""
import hashlib
import json
import os
from pathlib import Path
import struct
import subprocess
import sys
from types import SimpleNamespace
import unittest
from unittest.mock import patch

import numpy as np

from bilqis_mlx.learning.atlas_acceptance import candidate_identity_digest

RAW = 'bilqis.mlx.candidate-identity/raw-v2'
LEGACY = 'bilqis.mlx.candidate-identity/hex-json-v1'
GROUPS = ('parameters', 'm', 'v', 'update_counts')


def state(value=None, *, name='w', step=7, scheme=RAW):
    value = np.array([[1., -0.], [3., 4.]], dtype=np.float32) if value is None else value
    return SimpleNamespace(optimizer=SimpleNamespace(**{
        group: {name: value.copy()} for group in GROUPS}),
        optimizer_step=step, identity_scheme=scheme)


def legacy_oracle(value):
    parts = {group: {name: np.asarray(array).tobytes().hex()
                     for name, array in sorted(getattr(value.optimizer, group).items())}
             for group in GROUPS}
    raw = (json.dumps({'state': parts, 'optimizer_step': value.optimizer_step},
                     sort_keys=True, separators=(',', ':'), ensure_ascii=False,
                     allow_nan=False) + '\n').encode()
    return hashlib.sha256(raw).hexdigest()


def raw_oracle(value):
    """Small fixture only: assemble the documented framing independently."""
    def u64(number):
        return struct.pack('>Q', number)
    def text(text):
        encoded = text.encode()
        return u64(len(encoded)) + encoded
    data = RAW.encode() + b'\0' + u64(value.optimizer_step)
    for group in GROUPS:
        values = getattr(value.optimizer, group)
        data += text(group) + u64(len(values))
        for name in sorted(values):
            array = np.asarray(values[name])
            data += text(name) + text(array.dtype.str) + u64(array.ndim)
            data += b''.join(u64(dimension) for dimension in array.shape)
            data += u64(array.nbytes) + array.tobytes(order='C')
    return hashlib.sha256(data).hexdigest()


class CandidateIdentityTests(unittest.TestCase):
    def test_documented_raw_framing_matches_independent_oracle(self):
        value = state(name='é"\\\n')
        self.assertEqual(candidate_identity_digest(value), raw_oracle(value))

    def test_fixed_versioned_identity_vectors(self):
        self.assertEqual(candidate_identity_digest(state()),
                         '8b6d53806ae1eb5729ad96a340845ae3798176fdd824e08c1999c7f66d64540e')
        self.assertEqual(candidate_identity_digest(state(scheme=LEGACY)),
                         'db66ffd777735e64e01b818baf8689cc0cfd4fcb3d700c5a6885ae1f6fb80693')

    def test_each_identity_dimension_changes_digest(self):
        baseline = state()
        expected = candidate_identity_digest(baseline)
        variants = [state(step=8), state(name='other'),
                    state(baseline.optimizer.parameters['w'].reshape(4)),
                    state(baseline.optimizer.parameters['w'].view(np.int32))]
        for group in GROUPS:
            value = state()
            getattr(value.optimizer, group)['w'].view(np.uint8).flat[0] ^= 1
            variants.append(value)
        swapped = state()
        swapped.optimizer.m['w'] = np.zeros((2, 2), dtype=np.float32)
        moved = state()
        moved.optimizer.v['w'] = np.zeros((2, 2), dtype=np.float32)
        self.assertNotEqual(candidate_identity_digest(swapped), candidate_identity_digest(moved))
        for value in variants:
            with self.subTest(value=value):
                self.assertNotEqual(candidate_identity_digest(value), expected)

    def test_name_order_and_strides_preserve_logical_content(self):
        value = state(np.arange(12, dtype=np.float32).reshape(3, 4).T)
        for group in GROUPS:
            getattr(value.optimizer, group)['z'] = np.array(1, dtype=np.uint64)
        other = state()
        for group in GROUPS:
            setattr(other.optimizer, group, dict(reversed([
                (key, np.ascontiguousarray(array))
                for key, array in getattr(value.optimizer, group).items()])))
            # ascontiguousarray promotes scalar rank; preserve it explicitly.
            getattr(other.optimizer, group)['z'] = np.array(1, dtype=np.uint64)
        self.assertEqual(candidate_identity_digest(value), candidate_identity_digest(other))

    def test_mutable_values_are_rehashed(self):
        value = state()
        before = candidate_identity_digest(value)
        value.optimizer.parameters['w'][0, 0] = 5
        self.assertNotEqual(candidate_identity_digest(value), before)

    def test_legacy_exact_bytes_with_escaped_names_and_multiple_chunks(self):
        for array in (np.array(3, dtype=np.uint64),
                      np.arange(40000, dtype=np.float32)[::2], np.zeros((0, 3))):
            value = state(array, name='é"\\\n', scheme=LEGACY)
            self.assertEqual(candidate_identity_digest(value), legacy_oracle(value))

    def test_historical_hex_encoding_is_bounded_per_chunk(self):
        from bilqis_mlx.learning._retention._atlas_candidate import identity as owner
        sizes = []
        original = owner._bytes
        class ObservedBytes:
            def __init__(self, raw):
                self.raw = raw
            def __len__(self):
                return len(self.raw)
            def __getitem__(self, key):
                return ObservedBytes(self.raw[key])
            def hex(self):
                sizes.append(len(self.raw))
                return self.raw.hex()
        value = state(np.arange(40000, dtype=np.float32), scheme=LEGACY)
        with patch.object(owner, '_bytes', side_effect=lambda a: ObservedBytes(original(a))):
            actual = candidate_identity_digest(value)
        self.assertEqual(actual, legacy_oracle(value))
        self.assertGreater(len(sizes), len(GROUPS))
        self.assertLessEqual(max(sizes), 64 * 1024)
        self.assertEqual(sum(sizes), 4 * value.optimizer.parameters['w'].nbytes)

    def test_raw_path_does_not_use_json_or_legacy_serializer(self):
        with patch('json.dumps', side_effect=AssertionError('raw bytes required')):
            candidate_identity_digest(state())

    def test_invalid_scheme_or_step_fails_closed(self):
        for changes in ({'scheme': None}, {'scheme': 'unknown'}, {'step': -1},
                        {'step': True}, {'step': 2**64}):
            with self.subTest(changes=changes), self.assertRaises(Exception):
                candidate_identity_digest(state(**changes))

    def test_cold_process_restart(self):
        code = ('from bilqis_mlx.learning._retention.tests.test_candidate_identity '
                'import state; from bilqis_mlx.learning.atlas_acceptance '
                'import candidate_identity_digest; print(candidate_identity_digest(state()))')
        root = Path(__file__).resolve().parents[4]
        result = subprocess.run([sys.executable, '-B', '-c', code], cwd=root,
                                env={**os.environ, 'PYTHONDONTWRITEBYTECODE': '1'},
                                capture_output=True, text=True, check=True)
        self.assertEqual(result.stdout.strip(), candidate_identity_digest(state()))

    def test_historical_acceptance_records_import_without_numerical_runtime(self):
        code = ("import sys; sys.modules['numpy'] = None; "
                "import bilqis_mlx.learning.atlas_acceptance; print('OK')")
        result = subprocess.run([sys.executable, '-B', '-c', code],
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.strip(), 'OK')
