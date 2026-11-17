"""Public C05 retention routes and their fixed-school custody."""
from unittest.mock import patch

import mlx.core as mx
import numpy as np

from bilqis_mlx.runtime.tests.bamf_first_student._bamf_first_student_support import BamfFirstStudentCase
from bilqis_mlx.runtime.tests.custody.bamf_bundle.helpers import shape_patch


class BamfFixedSchoolPublicRouteTests(BamfFirstStudentCase):
    def test_public_c05_candidate_route_does_not_materialize_broad_fixed_school(self):
        target = self.root / "c05-native-public-candidate"
        self.preflight(target)
        from bilqis_mlx.factory.tests.test_executable_release import _answers
        from bilqis_mlx.factory.tests.test_execution_plan import _synthetic_registry
        from bilqis_mlx.learning.atlas_candidate import begin_candidate
        from bilqis_mlx.runtime.accepted_corrections import AcceptedRuntimeHost
        from bilqis_mlx.runtime.bamf_bundle.admission import (
            bind_accepted_execution_cache,
            load_accepted_generation,
        )
        import bilqis_mlx.runtime.factory_retention_owner as retention_owner

        with patch(
                "bilqis_mlx.source_adapters.school.live_source_registry",
                return_value=_synthetic_registry()), patch(
                "bilqis_mlx.factory.live_answers.live_answer_registry",
                return_value=_answers()), shape_patch():
            context = AcceptedRuntimeHost(target).source_context(
                graph=self.graph, source_root=None)
            parent = load_accepted_generation(target)
            cache = bind_accepted_execution_cache(target)
            retention_owner.bind_current_retention_protection_plan(
                context, parent, cache)
            retention_owner.bind_current_retention_source_rows(
                context, cache, self.release.execution_plan.capabilities[0].capability_id)
        transaction = begin_candidate(parent.retained_state)
        target_capability = self.release.execution_plan.capabilities[0].capability_id
        sentinel = object()

        with patch.object(
                retention_owner, "_training_exclusions",
                return_value=((), ())), patch.object(
                retention_owner, "_candidate_from_live_parent",
                return_value=(parent, parent, parent.retained_state, cache)), patch.object(
                retention_owner, "_fixed_school_instruments",
                side_effect=AssertionError("ordinary candidate entered broad fixed school")), patch.object(
                retention_owner, "_local_retention_instruments",
                return_value=(object(),)), patch.object(
                retention_owner, "_foundation_retention_evaluation",
                return_value=sentinel), shape_patch():
            result = retention_owner.evaluate_factory_retention_candidate(
                context, transaction, "artifact", target_capability,
                run_dir=target)

        self.assertIs(result, sentinel)
        self.assertFalse((target / "state.json").exists())
        self.assertFalse((
            target / "c05-fixed-school" / f"{parent.run_identity.digest}.json"
        ).is_file())

    def test_public_c05_package_import_route_shares_native_school_without_training_state(self):
        target = self.root / "c05-native-public-package"
        self.preflight(target)
        from bilqis_mlx.factory.tests.test_executable_release import _answers
        from bilqis_mlx.factory.tests.test_execution_plan import _synthetic_registry
        from bilqis_mlx.learning.atlas_package_import import (
            ImportSlice, prepare_package_import,
        )
        from bilqis_mlx.runtime.accepted_corrections import AcceptedRuntimeHost
        from bilqis_mlx.runtime.bamf_bundle.admission import (
            bind_accepted_execution_cache,
            load_accepted_generation,
        )
        import bilqis_mlx.runtime.factory_retention_owner as retention_owner

        with patch(
                "bilqis_mlx.source_adapters.school.live_source_registry",
                return_value=_synthetic_registry()), patch(
                "bilqis_mlx.factory.live_answers.live_answer_registry",
                return_value=_answers()), shape_patch():
            context = AcceptedRuntimeHost(target).source_context(
                graph=self.graph, source_root=None)
            parent = load_accepted_generation(target)
            cache = bind_accepted_execution_cache(target)
        parameters = dict(parent.retained_state.optimizer.parameters)
        name = next(iter(parameters))
        before = parameters[name]
        changed = np.asarray(before).copy().reshape(-1)
        changed[0] = changed[0] + 1e-6
        parameters[name] = mx.array(changed.reshape(before.shape), dtype=mx.float32)
        transaction = prepare_package_import(
            parent.retained_state, parameters, (ImportSlice(name, 0, 1),))
        target_capability = self.release.execution_plan.capabilities[0].capability_id
        sentinel = object()
        captured = {}
        def foundation(*args, **_kwargs):
            captured["training"] = args[7]
            return sentinel

        from types import SimpleNamespace
        full_instruments = tuple(
            SimpleNamespace(case=SimpleNamespace(capability_id=item.capability_id, group_id=item.grade_id))
            for item in self.release.execution_plan.capabilities)
        with patch.object(
                retention_owner, "_instruments",
                return_value=full_instruments), patch.object(
                retention_owner, "_broad_foundation_retention_evaluation",
                side_effect=foundation), shape_patch():
            result = retention_owner.evaluate_factory_package_import(
                context, transaction, "artifact", target_capability,
                run_dir=target)

        self.assertIs(result, sentinel)
        self.assertEqual(captured["training"], ((), ()))
        self.assertFalse((target / "state.json").exists())
        self.assertTrue((
            target / "c05-fixed-school" / f"{parent.run_identity.digest}.json"
        ).is_file())
