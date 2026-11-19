"""Native issued outcome through B13 journal and cold HOW replay."""
from dataclasses import replace
import importlib
import json
import subprocess
import sys
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from bilqis_mlx.control_plane.tests.cp07.native_source_support import NativeSourceFixture
from bilqis_mlx.errors import BilqisError
from bilqis_mlx.factory.teaching import content_digest
from bilqis_mlx.learning.atlas_retention_decision import issue_factory_retention_decision
from bilqis_mlx.learning.teacher_lineage import restore_teacher_lineage
from bilqis_mlx.runtime.accepted_priority_visit import _issue_result
from bilqis_mlx.runtime.bamf_bundle import record_bamf_rejection, load_bamf_generation
from bilqis_mlx.runtime.tests.custody.bamf_bundle.cold_resume_probe import retained_digest
from bilqis_mlx.runtime.tests.custody.bamf_bundle.helpers import shape_patch
from bilqis_mlx.runtime.bamf_operator.evidence import CandidateEvidenceCapture, prepare_candidate_evidence_root
from bilqis_mlx.runtime.capability_retention import DecisionStatus
from bilqis_mlx.runtime.outcomes.issuance import build_outcome
from bilqis_mlx.runtime.tests.capability.factory.owner import test_factory_retention_owner_adversarial as factory_fixture
from bilqis_mlx.runtime.tests.custody.bamf_bundle.teacher_custody_fixtures import selection_teacher


def _structural_weakness_evidence(evidence):
    from bilqis_mlx.factory import weakness as weakness_contract
    from bilqis_mlx.runtime import structural_weakness_replay as weakness_replay

    outcome = evidence["how_outcome"]
    how = outcome["context"]
    context = {
        "schema": weakness_replay.CONTEXT_SCHEMA,
        "capability_id": evidence["capability"],
        "grade_id": how["grade"],
        "curriculum_scope": how["curriculum_scope"],
        "grade_definition_sha256": how["grade_definition_sha256"],
        "source_binding_sha256": how["source_binding_sha256"],
        "factory_release_sha256": how["factory_release_sha256"],
        "rubric_sha256": how["rubric_sha256"],
        "active_grade_activation_sha256": "1" * 64,
        "active_grade_definition_sha256": "2" * 64,
        "policy_epoch": 3,
        "rights_epoch": 4,
        "correction_generation": 5,
        "source_authority_registry_sha256": "6" * 64,
    }
    context["context_sha256"] = weakness_replay._digest(context)
    weakness_class = {
        "schema": weakness_contract.SCHEMA,
        "capability_id": evidence["capability"],
        "provider_id": "fixture",
        "provider_implementation_sha256": "f" * 64,
        "classifier_id": "fixture.weakness/v1",
        "classifier_sha256": "7" * 64,
        "signature": {"family": "fixture"},
    }
    weakness_class["class_sha256"] = weakness_replay._digest(weakness_class)
    weakness = {
        "schema": weakness_replay.EVIDENCE_SCHEMA,
        "state": "UNRESOLVED",
        "freshness": "FRESH_EQUIVALENT_REQUIRED",
        "capability_id": evidence["capability"],
        "weakness_class": weakness_class,
        "context": context,
        "candidate_evidence_sha256":
            evidence["candidate_evidence"]["object"]["sha256"],
        "outcome_sha256": outcome["outcome_sha256"],
        "retention_reason": evidence["retention_reason"],
    }
    weakness["weakness_evidence_sha256"] = weakness_replay._digest(weakness)
    return weakness


class NativeRejectionOutcomeTests(NativeSourceFixture, unittest.TestCase):
    def fixture(self, *, accepted=False):
        parent = self.parent()
        original_teacher = selection_teacher()
        for stat in original_teacher['global_stats'].values():
            stat.setdefault('latest', None)
        with patch('bilqis_mlx.control_plane.tests.cp07.native_source_support.selection_teacher', return_value=original_teacher):
            visit = self.bound_native_visit(parent)
        identity = visit.identity
        teacher = restore_teacher_lineage(visit.projection.teacher_state).teacher()
        policy = teacher['strategies'][identity.policy_key]
        cap = identity.capability_id
        release_sha = 'a' * 64
        offer = SimpleNamespace(capability_id=cap, source_seed=17, release_sha256=release_sha)
        context = {'grade': 'A', 'phase': 'RECOVERY_1', 'curriculum_scope': 'factory/7',
                   'rubric_sha256': 'd' * 64, 'factory_release_sha256': release_sha, 'diagnostics': {},
                   'grade_definition_sha256': 'e' * 64, 'source_binding_sha256': 'f' * 64}
        selection = _issue_result('TEACHER_SELECTED', cap, offer, visit, policy,
                                  {'how_context': context}, 'A', (), self.run, object())
        fixture = list(factory_fixture._foundation_owner_fixture())
        fixture[-1] = replace(fixture[-1], status=DecisionStatus.ELIGIBLE if accepted else DecisionStatus.REJECT,
                              reason='PAIRED_SCREEN_WITHIN_BUDGET' if accepted else 'NO_MEASURABLE_TARGET_GAIN',
                              outcome_scores=((cap, 1, 2 if accepted else 1, 4),))
        def fixture_mock(*args, **kwargs):
            if kwargs.get('return_value') == 'd' * 64:
                kwargs['return_value'] = identity.student_sha256
            return Mock(*args, **kwargs)
        with patch.object(factory_fixture, 'Mock', side_effect=fixture_mock):
            evaluation = factory_fixture._evaluate_foundation_owner(*fixture)
        decision = issue_factory_retention_decision(evaluation)
        prepare_candidate_evidence_root(self.run)
        capture = CandidateEvidenceCapture(self.run, selection, generation=parent.generation,
                  accepted_manifest_sha256=identity.accepted_manifest_sha256,
                  candidate_attempt_ordinal=1, parent_optimizer_step=parent.retained_state.optimizer_step)
        execution = SimpleNamespace(teaching_option_ids=(cap,), provider_id='fixture',
                                    provider_implementation_sha256='f' * 64, variation_axes=('seed',))
        release = SimpleNamespace(release_sha256=release_sha,
                    execution_plan=SimpleNamespace(capability_map={cap: execution}))
        row = {'id': 'row', 'capability': cap, 'tokens': [1]}
        capture.delivery(release, cap, parent.retained_state.optimizer_step + 1, (row,),
                         seed=17, controls={"delivered_content_sha256": content_digest((row,))}, option_rows=())
        evidence_ref = capture.finalize(accepted=accepted, decision=decision.to_record())
        observation = build_outcome(self.run, selection, evaluation, decision, evidence_ref)
        evidence = {'schema': 'bilqis.bamf.c16.3-rejection/v2',
            'rejection_attempt_ordinal': 1, 'rejection_journal_ordinal': 1,
            'visit_id': identity.visit_id, 'teacher_visit': identity.to_record(),
            'selected_option_id': cap, 'selected_policy_key': identity.policy_key,
            'candidate_optimizer_step': parent.retained_state.optimizer_step + 1,
            'retained_optimizer_step': parent.retained_state.optimizer_step,
            'retention_reason': decision.reason, 'capability': cap,
            'decision': decision.to_record(), 'candidate_evidence': evidence_ref,
            'how_outcome': observation}
        cache = SimpleNamespace(run_id=parent.run_id, generation=parent.generation,
                                accepted_manifest_sha256=identity.accepted_manifest_sha256)
        return parent, teacher, cache, evidence

    def test_committed_rejection_replays_exactly_once_after_cold_reload(self):
        from bilqis_mlx.runtime.outcomes import replay
        parent, teacher, cache, evidence = self.fixture()
        evidence["structural_weaknesses"] = [_structural_weakness_evidence(evidence)]
        pointer = (self.run / 'bamf-state.json').read_bytes()
        step = parent.retained_state.optimizer_step
        retained_before = retained_digest(parent.retained_state)
        self.assertEqual(replay.replay_rejected_outcomes(self.run, parent, cache, teacher), teacher)
        record_bamf_rejection(self.run, parent, evidence)
        hot = replay.replay_rejected_outcomes(self.run, parent, cache, teacher)
        self.assertEqual(replay.replay_rejected_outcomes(self.run, parent, cache, hot), hot)
        import bilqis_mlx.runtime.priority_rejection_replay as projection
        projection._projection.cache_clear()
        cold = importlib.reload(replay).replay_rejected_outcomes(self.run, parent, cache, teacher)
        self.assertEqual(hot, cold)
        self.assertEqual(len(hot["structural_weaknesses"]["classes"]), 1)
        input_path = self.root / 'cold-teacher-input.json'
        output_path = self.root / 'cold-teacher-output.json'
        input_path.write_text(json.dumps(teacher))
        script = """import json, sys
from pathlib import Path
from types import SimpleNamespace
import mlx.core as mx
mx.set_memory_limit(1024**3)
mx.set_cache_limit(0)
from bilqis_mlx.runtime.bamf_bundle import load_bamf_generation
from bilqis_mlx.runtime.outcomes.replay import replay_rejected_outcomes
from bilqis_mlx.runtime.tests.custody.bamf_bundle.helpers import shape_patch
run, source, destination = map(Path, sys.argv[1:])
pointer = json.loads((run / 'bamf-state.json').read_text())
with shape_patch():
    parent = load_bamf_generation(run / 'bamf-state.json')
cache = SimpleNamespace(run_id=parent.run_id, generation=parent.generation,
                        accepted_manifest_sha256=pointer['manifest_sha256'])
teacher = json.loads(source.read_text())
result = replay_rejected_outcomes(run, parent, cache, teacher)
destination.write_text(json.dumps(result, sort_keys=True, allow_nan=False))
"""
        process = subprocess.run([sys.executable, '-c', script, str(self.run),
                                  str(input_path), str(output_path)],
                                 capture_output=True, text=True, timeout=30)
        self.assertEqual(process.returncode, 0, process.stderr)
        self.assertEqual(json.loads(output_path.read_text()), hot)
        self.assertEqual(hot['causal_experiment']['events'], 1)
        self.assertEqual((self.run / 'bamf-state.json').read_bytes(), pointer)
        self.assertEqual(parent.retained_state.optimizer_step, step)
        with shape_patch():
            restored = load_bamf_generation(self.run / 'bamf-state.json')
        self.assertEqual(retained_digest(restored.retained_state), retained_before)

    def test_committed_rejection_is_current_for_the_next_hot_and_cold_teacher_visit(self):
        from bilqis_mlx.learning.teacher_lineage import restore_teacher_lineage
        from bilqis_mlx.learning.teacher_lineage_records import digest

        parent, _teacher, _cache, evidence = self.fixture()
        pointer = (self.run / 'bamf-state.json').read_bytes()
        record_bamf_rejection(self.run, parent, evidence)
        observation = evidence['how_outcome']

        hot = self.bound_native_visit(parent)
        hot_teacher = restore_teacher_lineage(hot.projection.teacher_state).teacher()
        self.assertEqual(
            hot_teacher['how_outcomes']['applied'][observation['attempt_id']],
            observation['outcome_sha256'])
        self.assertEqual(len(hot_teacher['how_outcomes']['applied']), 1)

        import bilqis_mlx.runtime.priority_rejection_replay as projection
        projection._projection.cache_clear()
        cold = self.bound_native_visit(parent)
        cold_teacher = restore_teacher_lineage(cold.projection.teacher_state).teacher()

        self.assertEqual(cold_teacher, hot_teacher)
        self.assertEqual(
            digest(cold.projection.teacher_state),
            digest(hot.projection.teacher_state))
        self.assertEqual(cold.identity.policy_key, hot.identity.policy_key)
        self.assertEqual(cold.identity.visit_id, hot.identity.visit_id)
        self.assertEqual((self.run / 'bamf-state.json').read_bytes(), pointer)

    def test_mutated_issued_observation_cannot_commit(self):
        parent, _, _, evidence = self.fixture()
        pointer = (self.run / 'bamf-state.json').read_bytes()
        evidence['how_outcome']['attempted_steps'] += 1
        with self.assertRaises(BilqisError):
            record_bamf_rejection(self.run, parent, evidence)
        self.assertEqual((self.run / 'bamf-state.json').read_bytes(), pointer)

    def test_live_issued_accepted_mapping_credits_retention_exactly_once(self):
        from bilqis_mlx.runtime.outcomes.observations import apply_outcome
        _, teacher, _, evidence = self.fixture(accepted=True)
        observation = evidence['how_outcome']
        self.assertEqual(observation['decision']['decision'], 'PROVISIONAL')
        self.assertEqual(observation['retained_steps'], observation['attempted_steps'])
        credited = apply_outcome(teacher, observation)
        self.assertEqual(credited['causal_experiment']['events'], 1)
        self.assertEqual(credited['causal_experiment']['school_attempts_since_retained'], 0)
        self.assertGreater(credited['global_stats'][observation['teacher_visit']['policy_key']]['latest'], 0)
        self.assertEqual(apply_outcome(credited, observation), credited)
