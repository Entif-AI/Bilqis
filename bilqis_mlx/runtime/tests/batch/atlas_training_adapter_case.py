"""Reusable Atlas training adapter fixture without collected test methods."""
from dataclasses import replace
import unittest
from unittest.mock import patch

from bilqis_mlx.factory.adapters import SourceAdapterRegistry
from bilqis_mlx.factory.curriculum_definition import from_legacy_course
from bilqis_mlx.factory.executable_release import compile_executable_factory_release
from bilqis_mlx.factory.execution import CurriculumProfile
from bilqis_mlx.factory.teaching import describe_delivered_teaching
from bilqis_mlx.factory.tests.test_teaching import closed_source_fixture
from bilqis_mlx.runtime.atlas_training_adapter import compile_training_batch
from bilqis_mlx.runtime.model_topology_v2 import ModelTopologySpecV2
from bilqis_mlx.runtime.source_execution import SourceExecutionContext
from bilqis_mlx.runtime.tests.batch.training.visit_provenance_support import visit_provenance
from bilqis_mlx.semantics.frame_codec import SchemaTagMap
from bilqis_mlx.semantics.frame_compiler import FrameCompilerConfig

from .atlas_training_fixture_support import (
    _atlas_features, _source_context, _training_schema, answer_plan_for,
    source_ast_for,
)


class AtlasTrainingAdapterCase(unittest.TestCase):
    def setUp(self):
        course, graph, sources, answers, _ = closed_source_fixture()
        registered = sources.require('fixture.z-generator/v1', 'fixture.z-oracle/v1')

        def draw(**kwargs):
            return tuple(
                {**row, 'source_id': 'source-1', 'source_family_id': 'family-1',
                 'episode_id': 'episode-1', 'tokens': [1, 2, 1]}
                for row in registered.draw(**kwargs))

        def check(row, **kwargs):
            gold = row.get('gold')
            if isinstance(gold, dict):
                return gold == {'decisions': ['FALSE', 'END_FRAME']}
            return registered.check(row, **kwargs)

        sources = SourceAdapterRegistry((replace(registered, draw=draw, check=check),))
        curriculum, bindings = from_legacy_course(course)
        release = compile_executable_factory_release(
            curriculum, bindings, CurriculumProfile.full(),
            sources, answers, source_root=None, graph=graph, verification_seed=17)
        self.context = SourceExecutionContext(release, graph, None, sources, answers)
        self.model_generation = 'fixture-model-generation'
        self.rows = self.context.draw_rows(seed=17, capability='Z.C0', each=1)

    def source_owned_context(self, rows, *, seed=17):
        """Bind deliberate fixture variants as rows emitted by the source owner."""
        registered = self.context.source_registry.require(
            'fixture.z-generator/v1', 'fixture.z-oracle/v1')
        owned = tuple(dict(row) for row in rows)

        def draw(**kwargs):
            if (kwargs.get('capability') == 'Z.C0'
                    and kwargs.get('seed') == seed
                    and kwargs.get('each') == len(owned)):
                return owned
            return registered.draw(**kwargs)

        registry = SourceAdapterRegistry((replace(registered, draw=draw),))
        return replace(self.context, source_registry=registry)

    def compile(self, rows, *, release_sha=None, policy='allow',
                generation=None, sealed=(), context_mutator=None,
                frames_override=None, source_ast_override=None,
                delivery_override=None, extra_kwargs=None,
                source_context=None, source_seed=17, visit=None,
                optimizer_step_seed=42):
        context = source_context or self.context
        delivery = delivery_override or describe_delivered_teaching(
            context.release, 'Z.C0', 'source.direct/Z.C0', rows)
        visible_ends = {rows[0]['id']: 2}
        frames_for_ast, base_task, base_frontier, base_policy = _source_context(
            rows, context.release.release_sha256, visible_ends, policy,
            context.graph)
        task, frontier, context_policy = base_task, base_frontier, base_policy
        if context_mutator is not None:
            task, frontier, context_policy = context_mutator(
                task, frontier, context_policy)
        if frames_override is not None:
            frames_for_ast = frames_override
        legitimate_asts = tuple(source_ast_for(
            tuple(row['tokens'][:visible_ends.get(row['id'], len(row['tokens']))]),
            context.release.release_sha256, context.graph)
            for row in rows)
        inventories = {
            row['id']: (ast.source_instance_id, ast.frames)
            for row, ast in zip(rows, legitimate_asts)
        }
        schema = _training_schema()
        semantic_release = base_task.semantic_release
        compiler_config = FrameCompilerConfig(
            (schema,), SchemaTagMap.from_schemas(semantic_release, (schema,)),
            None, base_task, base_frontier, base_policy)
        with patch(
                'bilqis_mlx.runtime.atlas_training_adapter.rederive_training_authority',
                return_value=_atlas_features(legitimate_asts, semantic_release)), patch(
                    'bilqis_mlx.runtime.training_input_authority.source_frame_inventory',
                    side_effect=lambda _context, row, _selection:
                        inventories[row['id']]):
            return compile_training_batch(
                rows, context, ModelTopologySpecV2(),
                delivery=delivery, delivery_capability='Z.C0',
                delivery_release_sha256=release_sha or context.release.release_sha256,
                teacher_strategy={'policy': 'focused'}, requested_count=3,
                optimizer_step_seed=optimizer_step_seed,
                visit_provenance=(visit or visit_provenance('Z.C0')),
                source_authority=context.bind_rows(
                    rows, seed=source_seed, capability='Z.C0', each=len(rows)),
                rehearsal_by_id={rows[0]['id']: 'prior'}, visible_ends=visible_ends,
                source_ast_for=source_ast_override or (
                    lambda tokens: source_ast_for(
                        tokens, context.release.release_sha256,
                        context.graph)),
                compiler_config=compiler_config,
                feature_artifact_path='synthetic:feature-artifact',
                answer_plan_for=lambda *args: {
                    **answer_plan_for(*args),
                    'generation_binding': self.model_generation},
                frames_for_ast=frames_for_ast, task_scope=task,
                source_frontier=frontier, eligibility_policy=context_policy,
                generation_binding=generation or self.model_generation,
                sealed_holdout_ids=sealed, **(extra_kwargs or {}))
