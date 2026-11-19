"""Accepted C16.3 operator path runs championship at the B13 successor boundary."""
from contextlib import ExitStack, nullcontext
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


def _boundary_selection(target, group):
    return NS(
        option_id="fixture-option",
        lesson_grade=group,
        metadata={"cadence": {
            "schema": "bilqis.bamf.active-grade-cadence-authorization/v1",
            "disposition": "TEACHING",
            "phase_capability_ids": [target],
            "authorized_capability_ids": [target],
        }},
        visit=NS(identity=NS(
            visit_id="fixture-visit", policy_key="fixture-policy")))


def _first_title_operator_fixture():
    fixture, target, group, solver, assessment, evaluation = (
        _championship_evaluation_fixture())
    parent, _retained, successor, binding = _accepted_championship_successor(
        evaluation, solver, assessment, group)
    selection = _boundary_selection(target, group)
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
    return (
        fixture, target, group, assessment, evaluation, parent, successor,
        binding, selection, step, capture, cache,
    )


def _run_first_title_operator():
    (fixture, target, group, assessment, evaluation, parent, successor,
     binding, selection, step, capture, cache) = _first_title_operator_fixture()
    published = []

    def prepare(run_dir, *, observer=None, **_kwargs):
        from bilqis_mlx.runtime.bamf_operator.session_parts.native_session import (
            retention_result,
        )
        if observer is not None:
            observer.bind_parent(parent)
        return retention_result(
            run_dir, parent, fixture[0], "artifact", selection, target,
            cache, (step,), capture, 1, 1, {}, None, observer,
            emit_progress=lambda *_args: None)

    prefix = "bilqis_mlx.runtime.bamf_operator.session."
    native = "bilqis_mlx.runtime.bamf_operator.session_parts.native_session."
    patches = (
        (prefix + "prepare_bamf_visit", {"side_effect": prepare}),
        (native + "evaluate_factory_retention_candidate", {"return_value": evaluation}),
        (native + "derive_accepted_teacher_successor", {"return_value": successor}),
        (native + "bind_factory_baseline_successor",
         {"side_effect": lambda _evaluation, value: value}),
        (native + "derive_current_plasticity_escape_state", {"return_value": None}),
        ("bilqis_mlx.runtime.outcomes.issuance.build_outcome",
         {"return_value": {"schema": "fixture-outcome"}}),
        ("bilqis_mlx.runtime.outcomes.issuance.credited_visit",
         {"side_effect": lambda visit, _outcome: visit}),
        ("bilqis_mlx.runtime.outcomes.issuance.carry_credit_to_successor",
         {"side_effect": lambda _visit, value, _parent: value}),
        (native + "_resource_observation", {"return_value": {}}),
        (native + "candidate_identity_metrics_delta", {"return_value": {}}),
        (prefix + "accept_and_publish",
         {"side_effect": lambda _root, value, *_args, **_kwargs: published.append(value)}),
        (prefix + "load_accepted_generation", {"return_value": successor}),
        (prefix + "record_normal_stop_receipt", {"return_value": None}),
        (prefix + "record_active_grade_cadence_attempt", {"return_value": None}),
        ("bilqis_mlx.runtime.bamf_operator._championship_adjudication._current_binding",
         {"return_value": binding}),
        ("bilqis_mlx.runtime.bamf_operator.championship.capability_championship_evidence",
         {"return_value": (assessment.cohort, assessment)}),
        ("bilqis_mlx.runtime._factory_retention_support._training_exclusions",
         {"return_value": ((), ())}),
    )
    with TemporaryDirectory() as tmp, ExitStack() as stack:
        for target_name, kwargs in patches:
            stack.enter_context(patch(target_name, **kwargs))
        from bilqis_mlx.runtime.bamf_operator.session import operate_bamf
        result = operate_bamf(
            Path(tmp), minutes=1, max_visits=1, reserve_gib=0,
            source_prefetch_workers=0)
    return fixture, group, result, published


@patch("bilqis_mlx.runtime.bamf_operator.session._training_memory_context", nullcontext)
class CapabilityChampionshipOperatorPathTests(unittest.TestCase):
    def test_current_binding_canonicalizes_per_case_solver_contracts_for_replay(self):
        from bilqis_mlx.runtime.bamf_operator._championship_replay import _current_binding

        fixture, target, group, _solver_instance, assessment, _evaluation = (
            _championship_evaluation_fixture())
        self.assertGreater(len(assessment.solver_contracts), 1)
        self.assertEqual(len(set(assessment.solver_contracts)), 1)

        with patch(
                "bilqis_mlx.runtime.bamf_operator._championship_replay._solver_binding",
                return_value="binding") as solver_binding:
            result = _current_binding(
                fixture[0], "artifact", "run", "release", "parent", "cache",
                "successor", assessment.cohort, assessment, group)

        self.assertEqual(result, "binding")
        self.assertEqual(
            solver_binding.call_args.kwargs["solver_contracts"],
            tuple(sorted(set(assessment.solver_contracts))),
        )

    def test_ordinary_candidate_with_remaining_cadence_work_skips_championship_boundary(self):
        from bilqis_mlx.runtime.bamf_operator.championship import (
            championship_boundary_capabilities,
        )
        selection = NS(metadata={"cadence": {
            "schema": "bilqis.bamf.active-grade-cadence-authorization/v1",
            "disposition": "TEACHING",
            "phase_capability_ids": ["cap:a", "cap:b"],
            "authorized_capability_ids": ["cap:a", "cap:b"],
        }})

        self.assertEqual(
            championship_boundary_capabilities(selection, "cap:a"), ())

    def test_last_authorized_candidate_opens_existing_cadence_phase_boundary(self):
        from bilqis_mlx.runtime.bamf_operator.championship import (
            championship_boundary_capabilities,
        )
        selection = NS(metadata={"cadence": {
            "schema": "bilqis.bamf.active-grade-cadence-authorization/v1",
            "disposition": "TEACHING",
            "phase_capability_ids": ["cap:a", "cap:b"],
            "authorized_capability_ids": ["cap:b"],
        }})

        self.assertEqual(
            championship_boundary_capabilities(selection, "cap:b"),
            ("cap:a", "cap:b"))

    def test_operate_bamf_publishes_first_title_from_accepted_boundary_evidence(self):
        fixture, group, result, published = _run_first_title_operator()

        self.assertEqual((result.accepted, result.rejected), (1, 0))
        self.assertEqual(len(published), 1)
        role = published[0].championship_state["active_roles"][fixture[2]]
        self.assertEqual((role["correct"], role["total"]), (19, 20))
        self.assertEqual(role["capability_group"], group)


if __name__ == "__main__":
    unittest.main()
