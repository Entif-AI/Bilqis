"""Accepted C16.3 operator path carries C05 championship evidence into B13 state."""
from contextlib import ExitStack
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace as NS
import unittest
from unittest.mock import patch

from bilqis_mlx.learning._atlas_candidate.identity_binding import (
    candidate_identity_for_canonical_consumer,
)
from bilqis_mlx.learning.capability_championship import ReplayBinding
from bilqis_mlx.learning.champions import Checkpoint
from bilqis_mlx.runtime.capability_retention import (
    EvidenceKind, EvidenceStage, EvaluationCohort, case_census_digest,
    evaluate_capabilities,
)
from bilqis_mlx.runtime.tests.capability.capability_retention_helpers import (
    _cases, _solver,
)
from bilqis_mlx.runtime.tests.capability.factory.owner.test_factory_retention_owner_adversarial import (
    _evaluate_foundation_owner, _foundation_owner_fixture,
)
from bilqis_mlx.runtime.tests.custody.bamf_bundle.helpers import (
    accepted_state, candidate, parent_state,
)


def _championship_evaluation_fixture():
    fixture = _foundation_owner_fixture()
    target, group = fixture[2], "B"
    cases, contexts = _cases(target, group, 20, "native-championship")
    cohort = EvaluationCohort(
        EvidenceKind.FIXED_SCHOOL, cases, ((target, group),),
        "1" * 64, "2" * 64, "3" * 64, "4" * 64, (), (),
        case_census_digest(cases),
        evidence_stage=EvidenceStage.FOUNDATION_ACQUISITION)
    solver = _solver(contexts, {case.case_id for case in cases[:19]})
    assessment = evaluate_capabilities(solver, cohort, "b" * 64)
    evaluation = _evaluate_foundation_owner(
        *fixture, championship_cohort=cohort,
        championship_assessment=assessment)
    return fixture, target, group, solver, assessment, evaluation


def _accepted_championship_successor(evaluation, solver, assessment, group):
    parent = candidate(parent_state())
    retained = accepted_state(parent.retained_state)
    successor = candidate(retained, generation=1, parent="0" * 64)
    object.__setattr__(evaluation, "parent_state", parent.retained_state)
    object.__setattr__(evaluation, "candidate_state", retained)
    checkpoint = Checkpoint(
        candidate_identity_for_canonical_consumer(retained),
        "bamf-generations/1", retained.optimizer_step, True)
    binding = ReplayBinding(
        solver, assessment.generation_digest, checkpoint, group,
        tuple(sorted(set(assessment.solver_contracts))),
        lambda generation, offered: (
            generation == assessment.generation_digest and offered == checkpoint))
    return parent, retained, successor, binding


class CapabilityChampionshipOperatorPathTests(unittest.TestCase):
    def test_operate_bamf_publishes_first_title_from_issued_c05_evidence(self):
        fixture, target, group, solver, assessment, evaluation = (
            _championship_evaluation_fixture())
        parent, retained, successor, binding = _accepted_championship_successor(
            evaluation, solver, assessment, group)
        selection = NS(
            option_id="fixture-option",
            lesson_grade=group,
            visit=NS(identity=NS(
                visit_id="fixture-visit", policy_key="fixture-policy")))
        step = NS(transaction=NS(training_authorities=()))
        capture = NS(finalize=lambda **_kwargs: {
            "schema": "bilqis.bamf.c16.3-candidate-evidence-reference/v1",
            "persistence": {
                "bytes_written": 0, "file_fsyncs": 0,
                "directory_fsyncs": 0, "evidence_objects": 0,
                "persistence_seconds": 0.0,
            },
        })
        cache = NS(generation=0, accepted_manifest_sha256="0" * 64)
        published = []

        def prepare(run_dir, *, observer=None, **_kwargs):
            from bilqis_mlx.runtime.bamf_operator.session import _retention_result
            if observer is not None:
                observer.bind_parent(parent)
            return _retention_result(
                run_dir, parent, fixture[0], "artifact", selection, target,
                cache, (step,), capture, 1, 1, {}, None, observer)

        def publish(_run_dir, bound_successor, *_args, **_kwargs):
            published.append(bound_successor)

        prefix = "bilqis_mlx.runtime.bamf_operator.session."
        with TemporaryDirectory() as tmp, ExitStack() as stack:
            for target_name, kwargs in (
                (prefix + "prepare_bamf_visit", {"side_effect": prepare}),
                (prefix + "evaluate_factory_retention_candidate",
                 {"return_value": evaluation}),
                (prefix + "derive_accepted_teacher_successor",
                 {"return_value": successor}),
                (prefix + "bind_factory_baseline_successor",
                 {"side_effect": lambda _evaluation, value: value}),
                ("bilqis_mlx.runtime.outcomes.issuance.build_outcome",
                 {"return_value": {"schema": "fixture-outcome"}}),
                ("bilqis_mlx.runtime.outcomes.issuance.credited_visit",
                 {"side_effect": lambda visit, _outcome: visit}),
                ("bilqis_mlx.runtime.outcomes.issuance.carry_credit_to_successor",
                 {"side_effect": lambda _visit, value, _parent: value}),
                (prefix + "_resource_observation", {"return_value": {}}),
                (prefix + "candidate_identity_metrics_delta", {"return_value": {}}),
                (prefix + "accept_and_publish", {"side_effect": publish}),
                (prefix + "load_accepted_generation", {"return_value": successor}),
                ("bilqis_mlx.runtime.bamf_operator._championship_adjudication._current_binding",
                 {"return_value": binding}),
            ):
                stack.enter_context(patch(target_name, **kwargs))
            from bilqis_mlx.runtime.bamf_operator.session import operate_bamf
            result = operate_bamf(
                Path(tmp), minutes=1, max_visits=1, reserve_gib=0,
                source_prefetch_workers=0)

        self.assertEqual((result.accepted, result.rejected), (1, 0))
        self.assertEqual(len(published), 1)
        role = published[0].championship_state["active_roles"][fixture[2]]
        self.assertEqual((role["correct"], role["total"]), (19, 20))
        self.assertEqual(role["capability_group"], group)


if __name__ == "__main__":
    unittest.main()
