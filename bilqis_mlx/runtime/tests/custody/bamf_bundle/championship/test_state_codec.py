"""Cold B13 codec witnesses for native championship lifecycle state."""
import json
import os
import unittest
from dataclasses import replace
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

import bilqis_mlx.runtime.mlx_checkpoint as mlx_checkpoint
from bilqis_mlx.learning.capability_championship_state import (
    SCHEMA_V1,
    active_checkpoint_references,
    championship_epoch_identity,
    clear_championship_epoch,
    compact_championship_state,
)
from bilqis_mlx.runtime.bamf_bundle import load_bamf_bundle, save_bamf_bundle
from bilqis_mlx.runtime.tests.custody.bamf_bundle.helpers import (
    candidate, parent_state, shape_patch,
)


def _identity():
    return championship_epoch_identity(
        factory_release_sha256="1" * 64,
        semantic_catalog_sha256="2" * 64,
        curriculum_sha256="3" * 64,
        capability_groups=(("future:capability", "future:group"),),
        fixed_cohort_sha256="4" * 64, rubric_sha256="5" * 64,
        scope_sha256="6" * 64, source_sha256="7" * 64,
        policy_sha256="8" * 64, topology_sha256="9" * 64,
        extents_sha256="a" * 64, semantic_abi={"schema": "fixture"})


class ChampionshipStateCodecTests(unittest.TestCase):
    def setUp(self):
        self.temporary = TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.environment = patch.dict(
            os.environ, {"BILQIS_DATA_PLANE": str(self.root / "plane.sqlite3")})
        self.environment.start()

    def tearDown(self):
        self.environment.stop()
        self.temporary.cleanup()

    def _round_trip(self, state, name):
        source = replace(
            candidate(parent_state(), generation=1, parent="a" * 64),
            championship_state=state)
        with shape_patch(), patch.object(mlx_checkpoint, "assert_headroom"):
            manifest = save_bamf_bundle(source, self.root / name, reserve_gib=0.)
            return load_bamf_bundle(
                self.root / name,
                expected_manifest_sha256=manifest["manifest_sha256"])

    def test_active_title_round_trips_with_only_live_custody(self):
        pointer = {
            "sha256": "b" * 64, "filename": "bamf-generations/1",
            "optimizer_step": 7, "model_and_native_adamw": True,
        }
        state = compact_championship_state({
            "active_roles": {"future:capability": {
                "capability": "future:capability",
                "capability_group": "future:group",
                "checkpoint_origin_group": "future:group",
                "complete_solver_provenance": {
                    "weight_sha256": "b" * 64,
                    "generation_digest": "c" * 64,
                    "solver_contracts": ["d" * 64],
                },
                "checkpoint": pointer, "correct": 10, "total": 10,
                "championship_qualification_correct": 10,
                "championship_qualification_total": 10,
                "surviving_battery": [],
            }},
            "settled_matchups": {},
        }, _identity())
        loaded = self._round_trip(state, "championship-bundle")
        self.assertEqual(loaded.championship_state, json.loads(json.dumps(state)))
        self.assertEqual(active_checkpoint_references(loaded.championship_state), (pointer,))

    def test_archived_epoch_round_trips_without_live_custody(self):
        live = compact_championship_state({
            "active_roles": {},
            "settled_matchups": {
                "future:capability|" + "b" * 64 + "|" + "c" * 64: {
                    "capability": "future:capability", "winner_sha256": "b" * 64,
                },
            },
        }, _identity())
        archived = clear_championship_epoch(
            live, source_manifest_sha256="d" * 64, source_generation=7)
        loaded = self._round_trip(archived, "championship-history-bundle")
        self.assertEqual(loaded.championship_state, json.loads(json.dumps(archived)))
        self.assertEqual(loaded.championship_state["settled_matchups"], {})
        self.assertEqual(len(loaded.championship_state["epoch_history"]), 1)
        self.assertEqual(active_checkpoint_references(loaded.championship_state), ())

    def test_historical_v1_state_remains_exactly_cold_readable(self):
        legacy = {
            "schema": SCHEMA_V1,
            "identity": _identity(),
            "active_roles": {},
            "settled_matchups": {
                "future:capability|" + "b" * 64 + "|" + "c" * 64: {
                    "capability": "future:capability", "winner_sha256": "b" * 64,
                },
            },
        }
        loaded = self._round_trip(legacy, "championship-v1-bundle")
        self.assertEqual(loaded.championship_state, legacy)
