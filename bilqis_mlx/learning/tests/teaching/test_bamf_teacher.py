"""Pure successor binding reuses the replay teacher; no learner state is loaded."""
import copy
import random
from bilqis_mlx.errors import BilqisError
import unittest

from bilqis_mlx.learning.teacher_vnext_replay import bind_teacher_successor, select_canary
from bilqis_mlx.learning.tests.test_teacher_vnext_replay import _teacher
from bilqis_mlx.learning.teacher_strategy_population import active_effective_strategy_keys


class BamfTeacherTest(unittest.TestCase):
    def test_successor_preserves_prior_and_resets_checkpoint_local_evidence(self):
        teacher, _, _ = _teacher()
        teacher['causal_experiment']['student_policy_epoch'] = {'schema': 'bilqis.bamf.student-reference/v1', 'student_sha256': 'a' * 64, 'contexts': {'old': {'policy': 4}}}
        original = copy.deepcopy(teacher)
        epoch = bind_teacher_successor(teacher, {'schema': 'bilqis.bamf.student-reference/v1', 'student_sha256': 'b' * 64, 'region': 'new-region'},
            {'schema': 'bilqis.bamf.teacher-binding/v1', 'source_head': 'd21797e72365bf93ea7cad3a4ef9020ec9817f23', 'prior_region': 'old-region'})
        current = epoch.teacher()
        self.assertEqual(epoch.prior_teacher(), original)
        self.assertEqual(teacher, original)
        self.assertEqual(current['strategies'], original['strategies'])
        self.assertEqual(current['causal_experiment']['contexts'], {})
        self.assertEqual(current['causal_experiment']['student_policy_epoch']['student_sha256'], 'b' * 64)
        self.assertEqual(current['causal_experiment']['student_policy_epoch']['contexts'], {})
        self.assertEqual(epoch.prior_region, 'old-region')
        self.assertEqual(epoch.current_region, 'new-region')
        active, inventory = active_effective_strategy_keys(current, '', {})
        self.assertLessEqual(len(active), 16)
        self.assertEqual(set(inventory), set(active))
        canary = select_canary(current, capability='C.ADD', phase='RECOVERY_1', curriculum_scope='factory/7',
            candidate_ordinal=4, rng=random.Random(17), active_effective_policy_keys=active, inventory=inventory)
        self.assertEqual(canary['status'], 'FALLBACK_UNDERPOWERED')
        current['strategies'].clear()
        self.assertEqual(epoch.teacher()['strategies'], original['strategies'])


    def test_successor_bounds_ignore_dynamic_curriculum_size(self):
        teacher, _, _ = _teacher()
        base = next(iter(teacher['strategies'].values()))
        teacher['strategies'] = {str(i): {**base, 'lr': .00001 * (i + 1)} for i in range(30)}
        epoch = bind_teacher_successor(teacher, {'schema': 'bilqis.bamf.student-reference/v1', 'student_sha256': 'b' * 64, 'region': 'new'},
            {'schema': 'bilqis.bamf.teacher-binding/v1', 'source_head': 'd21797e72365bf93ea7cad3a4ef9020ec9817f23', 'prior_region': 'old'})
        active, _ = active_effective_strategy_keys(epoch.teacher(), '', {}, total_capabilities=20)
        self.assertLessEqual(len(active), 16)
        self.assertEqual(epoch.schema, 'bilqis.bamf.teacher-epoch/v1')

    def test_malformed_teacher_records_are_typed_failures(self):
        for mutation in ({'causal_experiment': None}, {'causal_experiment': {'student_policy_epoch': None}},
                         {'strategies': {'bad': None}}):
            teacher, _, _ = _teacher()
            with self.subTest(mutation=mutation), self.assertRaises(BilqisError):
                bind_teacher_successor({**teacher, **mutation}, {'schema': 'bilqis.bamf.student-reference/v1', 'student_sha256': 'b' * 64, 'region': 'new'},
                    {'schema': 'bilqis.bamf.teacher-binding/v1', 'source_head': 'd21797e72365bf93ea7cad3a4ef9020ec9817f23', 'prior_region': 'old'})


class BamfTeacherRegionTest(unittest.TestCase):
    def test_geometry_epoch_invalidates_context_and_archives_history(self):
        from dataclasses import replace
        import json
        from bilqis_mlx.learning.teacher_vnext_replay import refresh_teacher_region
        prior, _, _ = _teacher()
        epoch = bind_teacher_successor(prior,
            {'schema': 'bilqis.bamf.student-reference/v1', 'student_sha256': 'b' * 64, 'region': 'new'},
            {'schema': 'bilqis.bamf.teacher-binding/v1', 'source_head': 'd21797e72365bf93ea7cad3a4ef9020ec9817f23', 'prior_region': 'old'})
        active = epoch.teacher()
        active['causal_experiment'] = prior['causal_experiment']
        epoch = replace(epoch, current_json=json.dumps(active))
        changed = refresh_teacher_region(epoch, bank_identity='bank-2', plasticity_identity='FAST-v1')
        self.assertNotEqual(changed.current_region, epoch.current_region)
        self.assertEqual(changed.teacher()['causal_experiment']['contexts'], {})
        self.assertEqual(changed.teacher()['bamf_region_history'][-1]['evidence'], prior['causal_experiment'])
        self.assertEqual(refresh_teacher_region(changed, bank_identity='bank-2', plasticity_identity='FAST-v1'), changed)
        self.assertEqual(changed.prior_teacher(), prior)

    def test_shadow_ladder_does_not_issue_execution_authority(self):
        from bilqis_mlx.learning.teacher_multifidelity import DEFAULT_SHADOW_POLICY, evaluate_shadow
        review = evaluate_shadow(DEFAULT_SHADOW_POLICY, probes=((2, 0), (4, 0), (8, 0), (16, 1)),
                                 final_retained=True, full_budget_steps=16)
        self.assertEqual(review['mode'], 'SHADOW')
        self.assertFalse(review['actual_authority_changed'])
        self.assertEqual(review['actual_steps_spent'], 16)
        self.assertEqual(review['rungs'], [2, 4, 8, 16])

    def test_typed_mentor_votes_are_source_gold_gated(self):
        import numpy as np
        from bilqis_mlx.learning.champion_confidence import vote_targets_typed
        logits = np.array([[0., 10.], [0., 10.]])
        original = logits.copy()
        _, weight = vote_targets_typed(((1, logits),), np.array([1, 0]), classes=2,
                                      eligible_capabilities=1, teacher_distill=1.)
        self.assertGreater(weight[0], 0)
        self.assertEqual(weight[1], 0)
        self.assertTrue(np.array_equal(logits, original))

    def test_health_comes_from_recorded_outcome_counts(self):
        from bilqis_mlx.learning.teacher_observations import summarize_observations
        report = summarize_observations([{'retention': {'value': 'RETAINED'},
            'attempted_steps': 4, 'retained_steps': 4, 'wall_seconds': 2.0}])
        self.assertEqual(report['observation_count'], 1)
        self.assertEqual(report['retention_yield']['value'], 1.)
        self.assertEqual(report['wall_seconds']['value'], 2.)


class BamfHistoricalMentorTest(unittest.TestCase):
    def test_only_supported_read_only_source_bound_mentor_advice(self):
        from unittest.mock import patch
        from dataclasses import replace
        from bilqis_mlx.factory.tests.test_teaching import closed_source_fixture
        from bilqis_mlx.factory.executable_release import compile_executable_factory_release
        from bilqis_mlx.factory.execution import CurriculumProfile
        from bilqis_mlx.factory.curriculum_definition import from_legacy_course
        from bilqis_mlx.runtime.source_execution import SourceExecutionContext
        from bilqis_mlx.learning.teacher_vnext_replay import historical_mentor_advice
        course, graph, sources, answers, _ = closed_source_fixture()
        graph = {**graph, 'nodes': [{'id': name} for name in graph['tokens']], 'row_contract_sha256': {}}
        curriculum, bindings = from_legacy_course(course)
        release = compile_executable_factory_release(curriculum, bindings, CurriculumProfile.full(), sources,
            answers, source_root=None, graph=graph, verification_seed=17)
        context = SourceExecutionContext(release, graph, None, sources, answers)
        rows = [{**context.draw_rows(seed=17, capability='Z.C0', each=1)[0], 'tokens': [1]}]
        mentor = {'weights': {'sentinel': 'read-only'}, 'config': {'layers': 6, 'heads': 8},
                  'graph': graph, 'answer_ids': [1, 2]}
        before = copy.deepcopy(mentor)
        def infer(mx, weights, received, config, answer_ids):
            self.assertEqual(config['layers'], 6)
            self.assertEqual(received[0]['tokens'], rows[0]['tokens'])
            self.assertNotIn('record', received[0])
            self.assertEqual(received[0]['gold'], 'FALSE')
            return {rows[0]['id']: 'FALSE'}
        with patch('bilqis_mlx.learning.student_ops._predictions', side_effect=infer):
            self.assertEqual(historical_mentor_advice(None, mentor, rows, context), {rows[0]['id']: 'FALSE'})
        with patch('bilqis_mlx.learning.student_ops._predictions', return_value={rows[0]['id']: 'TRUE'}):
            self.assertEqual(historical_mentor_advice(None, mentor, rows, context), {})
        self.assertEqual(mentor, before)
        for purpose in ('RESUME', 'IMPORT_WEIGHTS', 'IMPORT_OPTIMIZER'):
            with self.subTest(purpose=purpose), self.assertRaises(BilqisError):
                historical_mentor_advice(None, mentor, rows, context, purpose=purpose)


class BamfGradeNeutralSelectionTest(unittest.TestCase):
    def teacher(self):
        from bilqis_mlx.learning.teacher_strategy_population import BAMF_SUCCESSOR_SELECTION
        teacher, _, _ = _teacher()
        teacher['selection_contract'] = BAMF_SUCCESSOR_SELECTION
        from bilqis_mlx.learning.learning_experiment import VERSION
        teacher['causal_experiment']['version'] = VERSION
        teacher['events'] = 100
        teacher['global_stats'] = {key: {'trials': 10, 'reward_sum': index, 'reward_ema': index}
                                   for index, key in enumerate(teacher['strategies'])}
        teacher['grade_stats'] = {
            'A': {'p-strong': {'trials': 1, 'reward_sum': 1000., 'reward_ema': 1000.}},
            'B': {'p-weak': {'trials': 1, 'reward_sum': 1000., 'reward_ema': 1000.}}}
        return teacher

    def test_bamf_priors_and_runtime_default_ignore_grade_labels(self):
        from bilqis_mlx.learning.teacher_strategy_population import historical_policy_mean
        from bilqis_mlx.runtime.teacher_policy_selection import select_visit_policy
        from bilqis_mlx.compatibility import historical_teacher_policy as engine
        teacher = self.teacher()
        self.assertEqual(historical_policy_mean(teacher, 'A', 'p-strong'),
                         historical_policy_mean(teacher, 'B', 'p-strong'))
        selected = []
        for grade in ('A', 'B', 'C', 'Z'):
            state = copy.deepcopy(teacher)
            result = select_visit_policy(engine, state, 'semantic.capability', None, random.Random(17),
                None, 'same-scope', None, grade, total_capabilities=20)
            selected.append((result, state))
        self.assertTrue(all(item == selected[0] for item in selected))

    def test_contextual_runtime_selection_is_grade_permutation_invariant(self):
        import json
        from types import SimpleNamespace
        from bilqis_mlx.runtime.teacher_policy_selection import select_visit_policy
        from bilqis_mlx.learning.learning_experiment import Settings
        from bilqis_mlx.compatibility import historical_teacher_policy as engine
        from bilqis_mlx.factory.tests.test_teaching import closed_source_fixture
        from bilqis_mlx.runtime.source_execution import SourceExecutionContext
        _, graph, sources, answers, release = closed_source_fixture()
        context = SourceExecutionContext(release, graph, None, sources, answers)
        teacher = self.teacher()
        school = SimpleNamespace(stage='RECOVERY_1', current_student=SimpleNamespace(sha256='b' * 64))
        results = []
        for cold in (False, True):
            for grade in ('A', 'B', 'C', 'Z'):
                state = json.loads(json.dumps(teacher)) if cold else copy.deepcopy(teacher)
                result = select_visit_policy(engine, state, 'Z.C0', school, random.Random(17),
                    Settings(), 'factory/7', {}, grade, total_capabilities=20)
                delivered = context.draw_rows(seed=17, capability='Z.C0', each=2)
                results.append((result, state, delivered))
        self.assertTrue(all(item == results[0] for item in results))
        self.assertEqual([row['id'] for row in results[0][2]], ['Z.C0:17:0', 'Z.C0:17:1'])

    def test_bound_sibling_penalty_does_not_use_capability_letter(self):
        from bilqis_mlx.learning.learning_experiment import _channel
        from bilqis_mlx.learning.teacher_strategy_population import (
            record_checkpoint_policy_outcome, effective_policy_key, sibling_cooldown_penalty,
            durable_policy_cooldown_status)
        teacher = self.teacher()
        channel = _channel(teacher)
        channel['capability_stagnation'] = {'C.ADD|factory/7': {'total_rejections': 0, 'total_retained': 0}}
        key = effective_policy_key(teacher['strategies']['p-strong'])
        for sha in ('a' * 64, 'b' * 64):
            for _ in range(4):
                channel['capability_stagnation']['C.ADD|factory/7']['total_rejections'] += 1
                record_checkpoint_policy_outcome(channel, 'C.ADD|RECOVERY_1|factory/7', key, sha,
                                                 no_target_gain=True, retained=False)
        self.assertTrue(durable_policy_cooldown_status(channel, 'C.ADD', 'factory/7', key)['active'])
        for capability in ('A.SUB', 'B.SUB', 'C.SUB', 'Z.SUB'):
            self.assertEqual(sibling_cooldown_penalty(channel, capability, 'factory/7', key), 0.)


    def test_bamf_canary_does_not_use_another_capability_same_grade(self):
        from bilqis_mlx.learning.teacher_strategy_population import active_effective_strategy_keys
        teacher = self.teacher()
        active, inventory = active_effective_strategy_keys(teacher, 'C', {})
        result = select_canary(teacher, capability='C.UNTOLD', phase='RECOVERY_1', curriculum_scope='factory/7',
            candidate_ordinal=4, rng=random.Random(17), active_effective_policy_keys=active, inventory=inventory)
        self.assertEqual(result['status'], 'FALLBACK_UNDERPOWERED')


if __name__ == '__main__':
    unittest.main()
