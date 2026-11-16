"""Real-artifact C08 preflight that stops immediately before expensive gradients."""
from pathlib import Path
from tempfile import TemporaryDirectory

from bilqis_mlx.runtime.bamf_bundle.admission import load_accepted_generation
from bilqis_mlx.runtime.bamf_bundle.admission import bind_accepted_execution_cache
from bilqis_mlx.runtime.backbone_identity import execution_generation_digest
from bilqis_mlx.runtime.factory_candidate_training import _resource_plan
from bilqis_mlx.runtime.factory_task_authority import (
    bind_factory_task_compiled_batch,
    factory_task_authority,
    factory_task_training_goal,
)
from bilqis_mlx.runtime.factory_training_bridge import prepare_factory_training_batch
from bilqis_mlx.runtime.task_goal_readout import (
    task_goal_route_plan,
    task_goal_training_targets,
)
from bilqis_mlx.runtime.tests.batch.training.visit_provenance_support import (
    visit_provenance,
)

from .factory_training_bridge_support import FactoryTrainingBridgeFixture
from .factory_training_execution_support import (
    assert_prepared_logical_rows, draw, observation, publish, split_budget,
)


class FactoryTrainingPreflightTests(FactoryTrainingBridgeFixture):
    def test_split_real_rows_reaches_gradient_boundary(self):
        rows, delivery = draw(self, "A.IDENTITY", 37117, 2)
        with TemporaryDirectory() as run_dir_value:
            run_dir = Path(run_dir_value)
            publish(self, run_dir)
            source_context = self.accepted_source_context(run_dir)
            source_context.require_accepted_runtime(run_dir)
            parent = load_accepted_generation(run_dir)
            cache = bind_accepted_execution_cache(run_dir)
            generation = execution_generation_digest(
                parent.retained_state.optimizer.parameters,
                spec=parent.topology,
                extents=parent.extents,
            )
            self.assertEqual(cache.generation_binding, generation)
            prepared = prepare_factory_training_batch(
                source_context,
                parent,
                str(self.artifact),
                self.feature_receipt.path,
                rows,
                generation,
                capability="A.IDENTITY",
                delivery=delivery,
                requested_count=2,
                source_seed=37117,
                source_each=2,
                optimizer_step_seed=18,
                visit_provenance=visit_provenance("A.IDENTITY"),
                teacher_strategy={"policy": "c02-parent-production"},
            )
            row_ids = tuple(row["id"] for row in rows)
            assert_prepared_logical_rows(self, prepared, row_ids)
            _, delivery_observation = observation(
                run_dir, "A.IDENTITY", rows, 37117)
            delivery_observation.__post_init__()
            resource_plan, _ = _resource_plan(
                prepared, parent, split_budget(parent, prepared))
            self.assertEqual(resource_plan.groups, ((0,), (1,)))
            for compiled in prepared.compiled_rows:
                authority = factory_task_authority(source_context, compiled)
                self.assertEqual(
                    authority.training_authority_sha256,
                    compiled.training_authority.digest)
                bound = bind_factory_task_compiled_batch(compiled, authority)
                goal = factory_task_training_goal(source_context, bound, authority)
                self.assertEqual(goal.goal_id, authority.source_row_id)
                targets, mask = task_goal_training_targets(authority.goal, goal)
                plan = task_goal_route_plan(
                    authority.goal,
                    bound,
                    self.b11_snapshot(compiled),
                    generation,
                )
                self.assertTrue(targets)
                self.assertTrue(mask)
                self.assertTrue(plan.decisions)
