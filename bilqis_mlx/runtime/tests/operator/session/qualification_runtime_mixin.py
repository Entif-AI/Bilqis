"""Runtime-facing qualification witnesses shared by the portable qualification suite."""
from types import SimpleNamespace
from unittest.mock import Mock, patch

from bilqis_mlx.runtime import qualification_manifest as contract


class QualificationRuntimeMixin:
    def test_actual_fresh_initialization_persists_the_frozen_release(self):
        try:
            import mlx.core as mx
        except ImportError:
            self.skipTest('MLX unavailable')
        from bilqis_mlx.runtime.tests.test_topology_lifecycle import _synthetic_release
        from bilqis_mlx.runtime import session
        from bilqis_mlx.runtime.mlx_checkpoint import load_semantically_bound_bundle
        from bilqis_mlx.state_dag import read_current
        fixture, release = _synthetic_release()
        prepared = contract.QualificationPreparation(
            self.manifest, self.manifest['arms'][0], release, fixture.graph)
        root = self.root/'fresh'
        root.mkdir()
        with patch.object(
                session._topology, 'initial_model',
                side_effect=AssertionError('HISTORICAL_MODEL_FORBIDDEN')), patch.object(
                session._compatibility_executable_projection,
                'compile_projected_executable_release',
                side_effect=AssertionError('SHADOW_RELEASE_FORBIDDEN')):
            _, optimizer, graph, receipt = session._init(
                root, {'manifest_sha256': 'a'*64, 'exam_rubric_sha256': 'c'*64},
                fixture.course, 'b'*64, {}, {}, None, source_root=None,
                reserve_gib=0., qualification=prepared)
        cold = read_current(root)
        self.assertEqual(cold['qualification'], prepared.receipt_fields()['qualification'])
        self.assertEqual(cold['numeric_maximum'], 7)
        self.assertEqual(cold['numeric_scope_final_maximum'], 7)
        self.assertEqual(cold['factory_release_sha256'], release.release_sha256)
        _, own, _, reloaded_graph = load_semantically_bound_bundle(root/cold['model_bundle'])
        self.assertEqual(int(optimizer.state['step'].item()), 0)
        self.assertEqual(int(own.state['step'].item()), 0)
        self.assertEqual(reloaded_graph, graph)

    def test_post_acquisition_sweeps_preserve_seed_scope_and_exposure_missingness(self):
        from bilqis_mlx.runtime.qualification_results import _evaluate_sweeps
        from bilqis_mlx.factory.tests.test_executable_release import ExecutableFactoryReleaseTests
        fixture = ExecutableFactoryReleaseTests()
        fixture.setUp()
        prepared = self.validate()
        prepared.manifest['source'] = {'root': str(self.root)}
        prepared.manifest['evaluation'].update(
            target_grade='Z', acquisition_seed=5,
            criterion={'numerator': 9, 'denominator': 10}, fresh_draw_rounds=2)
        prepared.manifest['workload']['grades'] = {
            'Z': list(prepared.release.execution_plan.capability_map)}

        def predictions(mx, parameters, rows, config, answer_ids):
            return {row['id']: row['gold'] for row in rows}

        with patch.dict(
                'sys.modules',
                {'bilqis_mlx.learning.student_ops': SimpleNamespace(_predictions=predictions)}):
            result = _evaluate_sweeps(
                prepared, {'config': {}, 'answer_ids': [1, 2]},
                {'sweeps': [], 'status': 'NOT_QUALIFIED'}, None, [], fixture.registry, None)
        self.assertEqual(result['status'], 'QUALIFIED')
        self.assertEqual([s['seed'] for s in result['sweeps']], [11, 13, 17])
        self.assertTrue(all(s['fresh_coverage'] for s in result['sweeps']))
        self.assertTrue(all(s['exact_training_overlap'] == 0 for s in result['sweeps']))

    def test_terminal_evaluation_uses_the_current_admitted_stage(self):
        from bilqis_mlx.runtime.qualification_results import evaluate_finished_arm
        current_release = SimpleNamespace(release_sha256='a' * 64)
        final_release = SimpleNamespace(
            release_sha256='b' * 64,
            execution_plan=SimpleNamespace(
                capabilities=(SimpleNamespace(capability_id='C.X'),)),
        )
        prepared = SimpleNamespace(
            arm={'id': 'baseline', 'run_dir': str(self.root / 'staged-run')},
            manifest={'digest': 'c' * 64}, release=final_release, graph={},
            stages=(current_release, final_release),
        )
        receipt = {
            'qualification': {'manifest_sha256': 'c' * 64},
            'school': {'current_student': {'sha256': 'd' * 64}},
        }
        stage_program = object()
        school = object()
        with patch('bilqis_mlx.state_dag.read_current', return_value=receipt), patch(
                'bilqis_mlx.runtime.admission._read_executable_factory_release_artifact',
                return_value=current_release), patch(
                'bilqis_mlx.factory.schedule.schedule_program_from_executable_release',
                return_value=stage_program) as schedule, patch(
                'bilqis_mlx.runtime.state._state_from_json', return_value=school) as restore, patch(
                'bilqis_mlx.curriculum.scheduler.assessment_capabilities', return_value=()), patch(
                'bilqis_mlx.runtime.teacher_observation_replay.read_committed_observations',
                return_value=[]), patch(
                'bilqis_mlx.learning.teacher_observations.summarize_observations',
                return_value={}), patch('bilqis_mlx.runtime.qualification_results._durable_json'):
            result = evaluate_finished_arm(prepared)
        schedule.assert_called_once_with(current_release)
        restore.assert_called_once_with(receipt['school'], stage_program)
        self.assertEqual(result['reason'], 'FULL_WORKLOAD_NOT_YET_INTRODUCED')

    def test_explicit_human_launch_maps_only_frozen_limits(self):
        from bilqis_mlx.runtime.qualification import execute
        prepared = self.validate()
        prepared.manifest['source'] = {
            'root': 'source', 'checkpoint': 'checkpoint', 'manifest': 'source-manifest'}
        prepared.manifest['policy']['value'].update(
            reserve_gib=100., source_prefetch_workers=2)
        launch = Mock(return_value={})
        with patch(
                'bilqis_mlx.runtime.qualification.preflight', return_value=prepared), patch.dict(
                'sys.modules',
                {'bilqis_mlx.runtime.operating_loop': SimpleNamespace(operate=launch)}), patch(
                'bilqis_mlx.runtime.qualification_results.evaluate_finished_arm',
                return_value={'status': 'NOT_QUALIFIED'}):
            execute(None, 'base', prepared.manifest['digest'], root=self.root, human_run=True)
        args = launch.call_args.kwargs
        self.assertFalse(args['resume'])
        self.assertTrue(args['retention_enabled'])
        self.assertEqual(args['max_visits'], prepared.manifest['budget']['max_visits'])
        self.assertEqual(args['steps_per_visit'], prepared.manifest['budget']['steps_per_visit'])
        self.assertFalse(args['numeric_staircase'])
        self.assertFalse(args['autonomous_curriculum'])
        self.assertIs(args['qualification'], prepared)

    def test_staged_workload_examines_only_its_introduced_prefix(self):
        from dataclasses import replace
        from scripts.bamf.freeze_learning_qualification import compile_stages
        from bilqis_mlx.factory.tests.test_executable_release import ExecutableFactoryReleaseTests
        from bilqis_mlx.factory.curriculum_definition import GradeSpec
        from bilqis_mlx.factory.executable_release import compile_executable_factory_release
        from bilqis_mlx.factory.execution import CurriculumProfile
        from bilqis_mlx.factory.schedule import schedule_program_from_executable_release
        from bilqis_mlx.curriculum.scheduler import start_new, assessment_capabilities
        from bilqis_mlx.learning.champions import Checkpoint
        fixture = ExecutableFactoryReleaseTests()
        fixture.setUp()
        original = fixture.curriculum.grades[0]
        grades = tuple(
            GradeSpec(name, original.capabilities[offset:offset+2],
                      original.exam_item_counts[offset:offset+2])
            for name, offset in (('A', 0), ('B', 2), ('C', 4)))
        curriculum = replace(fixture.curriculum, grades=grades)
        release = compile_executable_factory_release(
            curriculum, fixture.bindings, CurriculumProfile.full(), fixture.registry,
            fixture.answers, source_root=None, graph=fixture.graph, verification_seed=5)
        with patch(
                'bilqis_mlx.source_adapters.school.live_source_registry',
                return_value=fixture.registry), patch(
                'bilqis_mlx.factory.live_answers.live_answer_registry',
                return_value=fixture.answers):
            stages = compile_stages(release, fixture.graph, None)
        self.assertEqual([len(s.execution_plan.grades) for s in stages], [1, 2, 3])
        program = schedule_program_from_executable_release(stages[0])
        school = start_new(program, Checkpoint('a'*64, 'bundles/fixture', 0, True))
        self.assertEqual(
            assessment_capabilities(program, school),
            tuple(c.capability_id for c in grades[0].capabilities))
        for previous, successor in zip(stages, stages[1:]):
            successor.verify_successor_of(previous)

    def test_prequalified_transition_uses_the_existing_admission_owner(self):
        from bilqis_mlx.runtime.qualification import advance_frozen_boundary
        receipt = {
            'qualification': {'allowed_releases': [self.release.release_sha256, 'b'*64]}}
        with patch(
                'bilqis_mlx.runtime.admission._read_executable_factory_release_artifact',
                return_value=self.release), patch(
                'bilqis_mlx.runtime.release_adoption._adopt_executable_profile',
                return_value=(receipt, None, None, None)) as adopt:
            result = advance_frozen_boundary(
                None, self.root, receipt, None, None, None, None, None, self.graph,
                self.release, SimpleNamespace(stage='AWAITING_NEXT_GRADE'), {})
        self.assertIs(adopt.call_args.kwargs['compiled_successor'], self.release)
        self.assertFalse(adopt.call_args.kwargs['allow_mastery_debt'])
        self.assertTrue(result[-1])

    def test_freezer_reuses_the_current_operator_manifest_location(self):
        from scripts.bamf.freeze_learning_qualification import source_inputs
        from bilqis_mlx.runtime.qualification_manifest import file_digest
        source = self.root/'source'
        folder = source/'runs/primitive-consolidation-v16-triplets'
        folder.mkdir(parents=True)
        checkpoint = folder/'fixture.pt'
        checkpoint.write_bytes(b'source metadata fixture')
        (folder/'state.json').write_text('{}')
        (source/'bilqis_school').mkdir()
        (source/'bilqis_school/engine.py').write_text('# fixture')
        current = self.root/'current-authority.json'
        current.write_text('{}')
        payload = {
            'optimizer': {
                'param_groups': [
                    {'lr': .001, 'betas': [.9, .95], 'eps': 1e-8, 'weight_decay': .1}]}}
        with patch.dict(
                'sys.modules', {'torch': SimpleNamespace(load=lambda *a, **k: payload)}), patch(
                'bilqis_mlx.source.AUDITED_PARENT',
                SimpleNamespace(basename='fixture.pt', sha256=file_digest(checkpoint))), patch(
                'bilqis_mlx.cli.GRADE_A_MANIFEST', current):
            inputs, _, _ = source_inputs(source)
        self.assertEqual(inputs['manifest'], str(current))


__all__ = ("QualificationRuntimeMixin",)
