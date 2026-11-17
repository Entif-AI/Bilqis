"""Shared native championship fixtures for operator-observed tests."""
from __future__ import annotations

from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from bilqis_mlx.learning._atlas_candidate.identity_binding import (
    candidate_identity_for_canonical_consumer,
)
from bilqis_mlx.learning.capability_championship import ReplayBinding
from bilqis_mlx.learning.champions import Checkpoint
from bilqis_mlx.runtime.bamf_operator.championship import (
    bind_accepted_championship_successor,
)
from bilqis_mlx.runtime.capability_retention import (
    EvidenceKind, EvaluationCohort, case_census_digest, evaluate_capabilities,
)
from bilqis_mlx.runtime.tests.capability.capability_retention_helpers import (
    _cases, _solver,
)
from bilqis_mlx.runtime.tests.custody.bamf_bundle.helpers import (
    candidate, next_accepted_step, parent_state,
)


CAPABILITY = "future:capability"
SIBLING = "future:sibling"
GROUP = "factory-group-zeta"
OTHER_GROUP = "factory-group-omega"
CASE_COUNT = 20
ADJUDICATION = "bilqis_mlx.runtime.bamf_operator._championship_adjudication."


def source_context(*, include_sibling=False, sibling_group=GROUP):
    capability = SimpleNamespace(capability_id=CAPABILITY, grade_id=GROUP)
    capabilities = (capability,)
    if include_sibling:
        capabilities += (SimpleNamespace(
            capability_id=SIBLING, grade_id=sibling_group),)
    grades = (SimpleNamespace(
        grade_id=GROUP, assessment_blueprint_sha256="8" * 64),)
    if include_sibling and sibling_group != GROUP:
        grades += (SimpleNamespace(
            grade_id=sibling_group, assessment_blueprint_sha256="d" * 64),)
    release = SimpleNamespace(
        release_sha256="1" * 64,
        semantic_catalog_sha256="2" * 64,
        execution_plan=SimpleNamespace(
            curriculum_sha256="3" * 64,
            profile_id="future-profile",
            capabilities=capabilities,
            grades=grades,
            projection_digests=SimpleNamespace(
                roster="a" * 64, assessment="b" * 64,
                coverage="c" * 64, source="9" * 64)),
    )
    return SimpleNamespace(release=release)


def capability_cohort(capability=CAPABILITY, group=GROUP):
    cases, contexts = _cases(capability, group, CASE_COUNT, "future-title-" + capability)
    cohort = EvaluationCohort(
        EvidenceKind.FIXED_SCHOOL, cases, ((capability, group),),
        "4" * 64, "5" * 64, "6" * 64, "7" * 64, (), (),
        case_census_digest(cases))
    return cohort, contexts


def measurement(bundle, cohort, contexts, correct_count, generation_digest):
    correct = {case.case_id for case in cohort.cases[:correct_count]}
    solver = _solver(contexts, correct)
    assessment = evaluate_capabilities(solver, cohort, generation_digest)
    checkpoint = Checkpoint(
        candidate_identity_for_canonical_consumer(bundle.retained_state),
        f"bamf-generations/{bundle.generation}",
        bundle.retained_state.optimizer_step,
        True,
    )
    binding = ReplayBinding(
        solver, generation_digest, checkpoint, GROUP,
        tuple(sorted(set(assessment.solver_contracts))),
        lambda generation, offered: (
            generation == generation_digest and offered == checkpoint),
    )
    return assessment, binding


def evaluation(cohort, assessment, *, evaluated_capability_ids=()):
    return SimpleNamespace(
        decision=SimpleNamespace(evaluated_capability_ids=evaluated_capability_ids),
        championship_cohort=cohort,
        championship_assessment=assessment,
    )


class NativeChampionshipCase(unittest.TestCase):
    def setUp(self):
        self.cohort, self.contexts = capability_cohort()
        self.context = source_context()
        self.parent = candidate(parent_state())
        self.cache = SimpleNamespace(accepted_manifest_sha256="a" * 64)

    def successor(self, parent=None, generation=1, manifest="a"):
        parent = parent or self.parent
        return candidate(
            next_accepted_step(parent.retained_state), generation=generation,
            parent=manifest * 64)

    def bind(self, parent, successor, assessment, binding, incumbent=None,
             checkpoint_origin_group=GROUP):
        with patch(
                "bilqis_mlx.runtime.bamf_operator.championship."
                "_require_factory_evaluation", side_effect=lambda value: value), patch(
                ADJUDICATION + "_current_binding", return_value=binding), patch(
                ADJUDICATION + "_incumbent_binding",
                **({"return_value": incumbent} if incumbent is not None else {
                    "side_effect": AssertionError("unexpected incumbent replay")})):
            return bind_accepted_championship_successor(
                Path("unused"), parent, self.cache, successor, self.context,
                "artifact", CAPABILITY, evaluation(self.cohort, assessment),
                checkpoint_origin_group=checkpoint_origin_group)


__all__ = (
    "ADJUDICATION", "CAPABILITY", "GROUP", "OTHER_GROUP", "SIBLING",
    "NativeChampionshipCase", "capability_cohort", "evaluation", "measurement",
    "source_context", "candidate", "next_accepted_step", "replace", "patch",
    "Path", "bind_accepted_championship_successor",
)
