"""Retention support prefetch."""
import unittest

from bilqis_mlx.learning.tests.test_fragile_replay import (
    Path, _direct_u7c_replay_rows, fragile_preservation_capabilities, select_preservation_rows,
)


class RetentionSupportPrefetchTests(unittest.TestCase):
    def test_common_fresh_selector_preserves_three_draw_seed_order_and_serial_prefetch_parity(self):
        from copy import deepcopy
        from types import SimpleNamespace
        from unittest.mock import patch
        from bilqis_mlx.learning.fragile_replay import fresh_preservation_rows
        from bilqis_mlx.runtime import candidate_evidence, source_prefetch
        fixed = _direct_u7c_replay_rows()
        capabilities = fragile_preservation_capabilities()
        targets = select_preservation_rows(fixed, capabilities=capabilities)
        calls = []
        def draw(*, capability, seed, each):
            calls.append((capability, seed, each))
            selected = [row for row in targets if row["capability"] == capability]
            attempt = seed % 10
            group = selected[:1] if attempt == 0 else selected[1:2] if attempt == 1 else selected[2:]
            return tuple({**deepcopy(row), "id": "fresh:" + row["id"]} for row in group)
        seeds = {name: (10, 11, 12) for name in capabilities}
        expected = fresh_preservation_rows(
            fixed, capabilities=capabilities, draw_rows=draw,
            seed_for=lambda name, attempt: seeds[name][attempt], rotation=8, batch_size=40)
        expected_calls = [(name, seed, 120) for name in capabilities for seed in seeds[name]]
        self.assertEqual(calls, expected_calls)
        self.assertEqual(len(expected), 8)
        self.assertFalse({row["id"] for row in expected} & {row["id"] for row in fixed})
        request = {"fragile_fixed_rows": fixed, "fragile_requested": capabilities,
                   "fragile_seeds": seeds, "fragile_rotation": 8, "batch_size": 40,
                   "source_root": "unused", "graph": {}, "course": None}
        calls.clear()
        with patch.object(source_prefetch, "_source_rows", side_effect=lambda _request, **kw:
                          draw(**{key: value for key, value in kw.items() if key != "source_context"})):
            self.assertEqual(source_prefetch._fragile_rows(request), expected)
        self.assertEqual(calls, expected_calls)
        calls.clear()
        with patch.object(candidate_evidence._runtime_release_adoption, "_schedule_for_receipt", return_value=None), \
                patch.object(candidate_evidence._curriculum_scheduler, "assessment_capabilities", return_value=capabilities), \
                patch.object(candidate_evidence._runtime_state, "_seed",
                             side_effect=lambda receipt, *, capability, step: 10 + int(capability.rsplit(":", 1)[1])), \
                patch.object(candidate_evidence._runtime_assessment, "_draw_live_rows",
                             side_effect=lambda *args, **kw: draw(**{key: kw[key] for key in ("capability", "seed", "each")})):
            self.assertEqual(candidate_evidence._fresh_fragile_preservation_rows(
                Path("unused"), Path("unused"), {}, {}, None, SimpleNamespace(), "X",
                step=3, batch_size=40, fixed_rows=fixed), expected)
        self.assertEqual(calls, expected_calls)
