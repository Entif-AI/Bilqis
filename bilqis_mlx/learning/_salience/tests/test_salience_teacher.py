"""Priority chooses WHAT; the actual replay teacher still chooses every HOW knob."""
from dataclasses import replace
import json
import random
import unittest

from bilqis_mlx.errors import BilqisError
from bilqis_mlx.learning.salience_teacher import (
    AttentionFrontier, PrioritySchoolContext, PriorityStudentIdentity,
    choose_priority_teaching, propose_attention_options,
)
from bilqis_mlx.learning.salience_history import SalienceHistory
from bilqis_mlx.learning.tests.test_salience_history import _window_policy
from bilqis_mlx.learning.tests.test_atlas_salience import _CONTEXT, _REGISTRY, _signed, _policy, _fact
from bilqis_mlx.learning.tests.test_teacher_vnext_replay import _teacher
from bilqis_mlx.learning.tests.test_learning_experiment import schedule_program
from bilqis_mlx.learning.teacher_vnext_replay import bind_teacher_successor
from bilqis_mlx.learning.learning_experiment import Settings, _diagnostic_context
from bilqis_mlx.learning.teacher_strategy_population import BAMF_SUCCESSOR_SELECTION
from bilqis_mlx.learning.salience_contracts import AttentionOption, ActionKind, AuthoritySnapshot, Metric
from bilqis_mlx.learning.atlas_salience import derive_salience, verify_salience_inputs
from bilqis_mlx.curriculum.scheduler import start_new
from bilqis_mlx.learning.champions import Checkpoint
from bilqis_mlx.runtime.teacher_policy_selection import select_visit_policy
from bilqis_mlx.semantics.domains import contract_digest
import bilqis_mlx.compatibility.historical_teacher_policy as engine


def _fixture(*, held=False, correction=False):
    prior = _teacher()[0]
    prior.update(events=0, mutations=0, global_stats={key: engine._stats() for key in prior["strategies"]})
    epoch = bind_teacher_successor(prior,
        {"schema": "bilqis.bamf.student-reference/v1", "student_sha256": "9" * 64, "region": "successor"},
        {"schema": "bilqis.bamf.teacher-binding/v1", "source_head": "d21797e72365bf93ea7cad3a4ef9020ec9817f23", "prior_region": "prior"})
    context = replace(_CONTEXT, teacher_epoch_digest=contract_digest(epoch))
    snapshot = AuthoritySnapshot((context,), 100, _REGISTRY)
    policy = _policy()
    evidence = derive_salience(verify_salience_inputs(
        (_fact(Metric.DECLARED_IMPACT, 1, policy, context=context),
         _fact(Metric.BLOCKED_COUNT, 0, policy, context=context)), policy, snapshot, context))
    option = _signed(AttentionOption("one", context, evidence.basis.digest(),
        ActionKind.CORRECTION if correction else ActionKind.TEACHING, 80,
        True, not held, True, True, 0, correction, False, "fixture:salience-owner", "0" * 128))
    frontier = AttentionFrontier((option,), (("one", evidence),), snapshot)
    history = SalienceHistory(_window_policy(policy), ())
    school = start_new(schedule_program(("any-grade", (context.capability_id,))),
                       Checkpoint(epoch.student_sha256, "bundles/fixture.npz", 0, True))
    return epoch, frontier, history, school, evidence


class PriorityTeacherTests(unittest.TestCase):
    def test_actual_selector_equivalence_and_immutable_input(self):
        epoch, frontier, history, school, evidence = _fixture()
        original = epoch.current_json
        result = choose_priority_teaching(frontier, history, epoch, engine, school,
                                         random.Random(12), Settings(), program=schedule_program(("any-grade", (_CONTEXT.capability_id,))))
        teacher = epoch.teacher()
        key, policy, metadata = select_visit_policy(engine, teacher, evidence.scope.capability_id,
            school, random.Random(12), Settings(), evidence.scope.scope,
            {"salience_evidence": evidence, "teacher_epoch_digest": contract_digest(epoch)}, "any-grade")
        self.assertEqual(result.status, "TEACHER_SELECTED")
        self.assertEqual(result.policy_key, key)
        self.assertEqual(json.loads(result.policy_json), policy)
        self.assertEqual(json.loads(result.metadata_json), metadata)
        self.assertEqual(result.teacher_epoch.teacher(), teacher)
        self.assertEqual(epoch.current_json, original)
        self.assertEqual(result.teacher_epoch.prior_json, epoch.prior_json)
        contexts = teacher['causal_experiment']['diagnostic_contexts'].values()
        self.assertTrue(any(row.get('salience', {}).get('ordinals') == [1, 1, 0] for row in contexts))

    def test_bamf_priority_context_matches_legacy_school_selection(self):
        epoch, frontier, history, school, _ = _fixture()
        program = schedule_program(("any-grade", (_CONTEXT.capability_id,)))
        projected = PrioritySchoolContext(
            program.digest(), tuple(grade.id for grade in program.grades),
            PriorityStudentIdentity(epoch.student_sha256))
        legacy = choose_priority_teaching(
            frontier, history, epoch, engine, school, random.Random(12), Settings(),
            program=program)
        bamf = choose_priority_teaching(
            frontier, history, epoch, engine, projected, random.Random(12), Settings(),
            program=program)
        self.assertEqual(bamf, legacy)
        self.assertFalse(hasattr(projected, "grade_index"))
        self.assertFalse(hasattr(projected, "first_recovery"))

    def test_holds_and_correction_do_not_select_teaching(self):
        for held, correction, expected in ((True, False, "NO_ADMISSIBLE_TEACHING"),
                                            (True, True, "ACTION_REQUIRED")):
            epoch, frontier, history, school, _ = _fixture(held=held, correction=correction)
            rng = random.Random(1)
            before = rng.getstate()
            result = choose_priority_teaching(frontier, history, epoch, engine, school, rng,
                                             Settings(), program=schedule_program(("any-grade", (_CONTEXT.capability_id,))))
            self.assertEqual(result.status, expected)
            self.assertIsNone(result.policy_json)
            self.assertEqual(rng.getstate(), before)
            self.assertEqual(result.teacher_epoch, epoch)
            self.assertEqual(len(propose_attention_options(frontier, history).held), int(held and not correction))

    def test_reject_stale_teacher_and_no_contextual_settings(self):
        epoch, frontier, history, school, _ = _fixture()
        for stale, settings in ((replace(epoch, replay_head="0" * 40), Settings()),
                                (replace(epoch, student_sha256="8" * 64), Settings()),
                                (epoch, None)):
            with self.assertRaises(BilqisError):
                choose_priority_teaching(frontier, history, stale, engine, school, random.Random(1),
                                         settings, program=schedule_program(("any-grade", (_CONTEXT.capability_id,))))

    def test_stable_features_do_not_fragment_on_receipt_identity(self):
        epoch, frontier, _, _, evidence = _fixture()
        channel = {"selection_contract": BAMF_SUCCESSOR_SELECTION}
        diagnostics = {"salience_evidence": evidence, "teacher_epoch_digest": contract_digest(epoch)}
        first, payload = _diagnostic_context(channel, evidence.scope.capability_id, evidence.scope.scope, diagnostics)
        self.assertEqual(payload['salience']['known'], [True, True, False])
        changed = replace(evidence.basis.facts[0], source_receipt_sha256="7" * 64)
        second_evidence = derive_salience(verify_salience_inputs(
            (_signed(changed), evidence.basis.facts[1]), evidence.basis.policy,
            frontier.snapshot, evidence.scope))
        second, _ = _diagnostic_context(channel, evidence.scope.capability_id, evidence.scope.scope,
                                       {**diagnostics, "salience_evidence": second_evidence})
        self.assertEqual(first, second)

    def test_selected_capability_resolves_grade_from_actual_factory_roster(self):
        epoch, frontier, history, school, evidence = _fixture()
        program = schedule_program(("caller-start-grade", ("different-capability",)),
                                   ("selected-grade", (evidence.scope.capability_id,)))
        school = start_new(program, school.current_student)
        result = choose_priority_teaching(frontier, history, epoch, engine, school,
                                         random.Random(12), Settings(), program=program)
        self.assertEqual(result.lesson_grade, "selected-grade")
        direct_teacher = epoch.teacher()
        key, policy, _ = select_visit_policy(engine, direct_teacher, evidence.scope.capability_id,
            school, random.Random(12), Settings(), evidence.scope.scope,
            {"salience_evidence": evidence, "teacher_epoch_digest": contract_digest(epoch)}, "selected-grade")
        self.assertEqual(result.policy_key, key)
        self.assertEqual(json.loads(result.policy_json), policy)
        self.assertEqual(result.teacher_epoch.teacher(), direct_teacher)

    def test_priority_school_active_grades_are_reporting_only(self):
        epoch, frontier, history, _school, evidence = _fixture()
        program = schedule_program(
            ("reporting-grade", ("different-capability",)),
            ("selected-grade", (evidence.scope.capability_id,)))
        school = PrioritySchoolContext(
            program.digest(), ("reporting-grade",),
            PriorityStudentIdentity(epoch.student_sha256))
        result = choose_priority_teaching(
            frontier, history, epoch, engine, school, random.Random(12),
            Settings(), program=program)
        self.assertEqual(result.status, "TEACHER_SELECTED")
        self.assertEqual(result.lesson_grade, "selected-grade")
