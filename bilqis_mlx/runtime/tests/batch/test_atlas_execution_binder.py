"""Fail-closed production authority tests for the B09.2 execution binder."""
from __future__ import annotations

import inspect
import unittest
from types import SimpleNamespace
from unittest.mock import patch

import mlx.core as mx

from bilqis_mlx.errors import BilqisError
from bilqis_mlx.learning.atlas_engram_reads import MotifReadResult
from bilqis_mlx.learning.atlas_execution_provenance import StepExecutionProvenance
from bilqis_mlx.learning.atlas_plasticity import GroupEligibility
from bilqis_mlx.runtime.atlas_execution_binder import (
    bind_distributed_execution_provenance, bind_execution_provenance,
    bind_execution_provenance_many,
)
from bilqis_mlx.runtime.c08_distributed_evidence import DistributedB11Evidence
from bilqis_mlx.runtime.model_topology_v2 import (
    GenerationExtents, Initializer, ModelTopologySpecV2, ParameterGroup,
    ParameterSpec,
)

BANK = "identity.bank.0"
MOTIF = "motif.page.0"
DECLARED = (
    ParameterSpec(BANK, (2, 2), Initializer.MATRIX,
                  ParameterGroup.IDENTITY_ROW_AGE, True),
    ParameterSpec(MOTIF, (8, 8), Initializer.MATRIX,
                  ParameterGroup.FAST, True),
)
EXTENTS = GenerationExtents(1, 1, "a" * 64, "b" * 64, "c" * 64)
CENSUS_SHAPE = (
    "bilqis_mlx.learning.atlas_participation_census.expected_bamf_shapes",
    "bilqis_mlx.learning._retention.atlas_participation_census.expected_bamf_shapes",
)


def motif_read(slot):
    return MotifReadResult(
        mx.zeros((1, 1, 768), dtype=mx.float32), (("EXACT",),),
        (slot,), ("a" * 64,))


def eligibility(mode="FULL", admitted=((0, 0),), eligible=(BANK, MOTIF)):
    return GroupEligibility(
        mode=mode,
        eligible_parameter_names=tuple(eligible),
        frozen_parameter_names=(),
        admitted_identity_rows=tuple(admitted),
        fast_identity_rows=tuple(admitted),
        established_identity_rows=(),
    )


class ExecutionBinderProductionTests(unittest.TestCase):
    def bind(self, **overrides):
        evidence = {
            "loss_bearing_target": False,
            "group_eligible": eligibility(),
            "spec": ModelTopologySpecV2(),
            "extents": EXTENTS,
            "run_id": "fixture-run",
            "generation": 1,
            "parent_manifest_sha256": "6" * 64,
            "parent_candidate_identity_sha256": "7" * 64,
            "parent_optimizer_step": 11,
            "topology_digest": "8" * 64,
            "candidate_step_ordinal": 1,
        }
        evidence.update(overrides)
        with patch(CENSUS_SHAPE[0], return_value=DECLARED), \
                patch(CENSUS_SHAPE[1], return_value=DECLARED):
            return bind_execution_provenance(**evidence)

    def test_binder_accepts_no_caller_execution_or_motif_facts(self):
        parameters = set(inspect.signature(bind_execution_provenance).parameters)
        for forbidden in (
                "motif_reads", "executed_parameter_names", "visible_identity_rows",
                "feedback_identity_rows", "local_slot_rows", "active_admitted"):
            self.assertNotIn(forbidden, parameters)

    def test_no_loss_binder_issues_empty_non_authorizing_provenance(self):
        provenance = self.bind()
        self.assertFalse(provenance.mask.has_loss_bearing_target)
        self.assertEqual(provenance.participation.dense_parameter_names, ())
        for item in provenance.mask.parameters:
            self.assertFalse(item.whole_parameter)
            self.assertEqual(item.row_indices, ())

    def test_loss_bearing_step_requires_exact_b11_execution_owner(self):
        with self.assertRaises(BilqisError):
            self.bind(loss_bearing_target=True)

    def test_logical_batch_binder_unions_disjoint_row_participation(self):
        executions = (
            SimpleNamespace(
                visible_identity_rows=((0, 0),),
                feedback_identity_rows=(),
                feature_rows=(("type", 1),),
                local_slot_rows=(1,),
                dense_parameter_names=("dense.alpha",),
                semantic_denominator_identity_rows=((0, 1),),
                semantic_denominator_feature_rows=(("schema", 3),),
                motif_reads=(motif_read(1),),
                role_read_feature_rows=(("role", 5),),
            ),
            SimpleNamespace(
                visible_identity_rows=((0, 1),),
                feedback_identity_rows=((0, 0),),
                feature_rows=(("role", 2),),
                local_slot_rows=(2,),
                dense_parameter_names=("dense.beta",),
                semantic_denominator_identity_rows=(),
                semantic_denominator_feature_rows=(("type", 4),),
                motif_reads=(motif_read(2),),
                role_read_feature_rows=(("schema", 6),),
            ),
        )
        with patch(CENSUS_SHAPE[0], return_value=DECLARED), \
                patch(CENSUS_SHAPE[1], return_value=DECLARED), \
                patch(
                    "bilqis_mlx.runtime.atlas_execution_binder.require_bamf_loss_execution",
                    side_effect=lambda value: value,
                ):
            provenance = bind_execution_provenance_many(
                loss_executions=executions,
                group_eligible=eligibility(admitted=((0, 0), (0, 1))),
                spec=ModelTopologySpecV2(), extents=EXTENTS,
                run_id="fixture-run", generation=1,
                parent_manifest_sha256="6" * 64,
                parent_candidate_identity_sha256="7" * 64,
                parent_optimizer_step=11, topology_digest="8" * 64,
                candidate_step_ordinal=1,
            )
        self.assertEqual(
            provenance.participation.identity_rows, ((0, 0), (0, 1)))
        self.assertEqual(provenance.participation.motif_slots, (1, 2))
        self.assertEqual(
            provenance.participation.feature_rows,
            tuple(sorted({
                ("type", 1), ("role", 2), ("schema", 3),
                ("type", 4), ("role", 5), ("schema", 6),
            })),
        )
        self.assertEqual(provenance.participation.local_slot_rows, (1, 2))
        self.assertEqual(
            provenance.participation.dense_parameter_names,
            ("dense.alpha", "dense.beta"),
        )
        self.assertEqual(
            provenance.mask.parameter(BANK).row_indices, (0, 1))
        self.assertEqual(provenance.mask.parameter(MOTIF).row_indices, (1, 2))
        self.assertEqual(
            provenance.mask.participating_identity_rows, ((0, 0), (0, 1)))

    def test_distributed_active_feature_rows_match_visible_b11_rows_only(self):
        evidence = (
            DistributedB11Evidence(
                "a" * 64, 0, 0, "row:0", "b" * 64, "fixture-run", 1, "c" * 64,
                ((0, 0),), (), (), (("type", 1),),
                (("schema", 3),), (("role", 5),), (), (), (), "d" * 64,
                (("SOURCE", "fixture-source:0"),), "[]"),
            DistributedB11Evidence(
                "a" * 64, 1, 1, "row:1", "b" * 64, "fixture-run", 1, "c" * 64,
                ((0, 1),), (), (), (("role", 2),),
                (("type", 4),), (("schema", 6),), (), (), (), "e" * 64,
                (("SOURCE", "fixture-source:1"),), "[]"),
        )
        with patch(
                "bilqis_mlx.runtime.atlas_execution_binder.validate_group_census"), \
                patch(
                    "bilqis_mlx.runtime.atlas_execution_binder.issue_execution_provenance",
                    side_effect=lambda _inputs, _denominator, _motif, _roles,
                    _eligible, active, **_kwargs: active):
            active = bind_distributed_execution_provenance(
                evidence=evidence, group_eligible=eligibility(),
                spec=ModelTopologySpecV2(), extents=EXTENTS,
                run_id="fixture-run", generation=1,
                parent_manifest_sha256="6" * 64,
                parent_candidate_identity_sha256="7" * 64,
                parent_optimizer_step=11, topology_digest="8" * 64,
                candidate_step_ordinal=1)
        self.assertEqual(active.feature_rows, (("role", 2), ("type", 1)))

    def test_forged_fast_reclassification_of_slow_parameter_is_refused(self):
        forged = eligibility(mode="FAST", admitted=((0, 0),), eligible=(BANK, MOTIF))
        with self.assertRaises(BilqisError):
            self.bind(group_eligible=forged)

    def test_caller_cannot_construct_the_provenance(self):
        provenance = self.bind()
        with self.assertRaises(BilqisError):
            StepExecutionProvenance(
                provenance.participation, provenance.mask,
                provenance.eligible_parameter_names, provenance.extents_sha256,
                provenance.run_id, provenance.generation,
                provenance.parent_manifest_sha256,
                provenance.parent_candidate_identity_sha256,
                provenance.parent_optimizer_step, provenance.topology_digest,
                provenance.candidate_step)


if __name__ == "__main__":
    unittest.main()
