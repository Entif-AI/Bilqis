"""Cold accepted-history progression authority regressions for C09."""
from __future__ import annotations

import os
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from bilqis_mlx.errors import BilqisError
from bilqis_mlx.learning.capability_championship import ReplayBinding
from bilqis_mlx.runtime.accepted_corrections import (
    AcceptedRuntimeHost, _reset_accepted_correction_runtime_for_tests,
)
from bilqis_mlx.runtime.capability_authority import (
    AuthorityKind, evaluate_accepted_progression_authority,
)
from bilqis_mlx.runtime.tests.capability.test_capability_authority import (
    GENERATION, GRAPH, _authority, _evidence, _release,
)
from bilqis_mlx.runtime.tests.correction.capability_support_owner_support import (
    publish_support_fixture,
)
from bilqis_mlx.runtime.tests.custody.bamf_bundle.helpers import shape_patch
from bilqis_mlx.runtime.tests.test_atlas_revalidation import (
    AUTHORITY, _event, _ref,
)
from bilqis_mlx.semantics.cognitive_dependencies import DependencyKind


SOURCE_ROW = "source:accepted-progression:target"


class AcceptedProgressionHistoryTests(unittest.TestCase):
    def setUp(self):
        self.temporary = TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.run = self.root / "run"
        self.environment = patch.dict(
            os.environ, {"BILQIS_DATA_PLANE": str(self.root / "plane.sqlite3")})
        self.environment.start()

    def tearDown(self):
        self.environment.stop()
        self.temporary.cleanup()

    def _publish_support_and_correction(self):
        with shape_patch(AUTHORITY):
            publish_support_fixture(
                self.run,
                capability="target",
                source_row=SOURCE_ROW,
                source_family="source-family:accepted-progression",
                episode="episode:accepted-progression",
                generation_binding=GENERATION,
                authority_registry=AUTHORITY,
            )
            AcceptedRuntimeHost(self.run).record_correction(
                _event(_ref(DependencyKind.SOURCE, SOURCE_ROW)))
        _reset_accepted_correction_runtime_for_tests()

    def _evaluate(self, correction_registry=None):
        release, checkpoint, admission = _release()
        solver, target = _evidence(release, "target")
        replay = ReplayBinding(
            solver, GENERATION, checkpoint, "C",
            tuple(sorted(set(target.assessment.solver_contracts))),
            lambda generation, pointer:
                generation == GENERATION and pointer == checkpoint,
        )
        authorities = dict(
            admission=admission,
            semantic_graph_sha256=GRAPH,
            prerequisite_thresholds=(),
            source_rights=_authority(AuthorityKind.SOURCE_RIGHTS),
            promotion_policy=_authority(AuthorityKind.PROMOTION_POLICY),
            admission_lease=_authority(AuthorityKind.ADMISSION_LEASE),
        )
        if correction_registry is not None:
            authorities["correction_authority_registry"] = correction_registry
        with shape_patch(AUTHORITY):
            return evaluate_accepted_progression_authority(
                self.run, release, "target", target, (), replay, **authorities)

    def test_cold_accepted_correction_history_uses_accepted_authority_only(self):
        self._publish_support_and_correction()
        gate = self._evaluate()
        self.assertEqual(gate.status, "HELD")
        self.assertEqual(gate.reason, "CURRENT_CAPABILITY_SUPPORT_HELD")

        with self.assertRaises(BilqisError) as rejected:
            self._evaluate(AUTHORITY)
        self.assertEqual(
            rejected.exception.context["reason"],
            "BAMF_PROGRESSION_CALLER_CORRECTION_AUTHORITY_FORBIDDEN",
        )


if __name__ == "__main__":
    unittest.main()
