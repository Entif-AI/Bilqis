"""Native BAMF capability-title lifecycle over accepted championship state."""
from __future__ import annotations

import json
from dataclasses import asdict, replace
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from bilqis_mlx.learning._atlas_candidate.identity_binding import (
    candidate_identity_for_canonical_consumer,
)
from bilqis_mlx.learning.capability_championship import ReplayBinding
from bilqis_mlx.learning.capability_championship_state import (
    active_checkpoint_references,
)
from bilqis_mlx.learning.champions import Checkpoint
from bilqis_mlx.runtime.bamf_operator.championship import (
    bind_accepted_championship_successor,
)
from bilqis_mlx.runtime.capability_retention import (
    EvidenceKind, EvaluationCohort, case_census_digest, evaluate_capabilities,
)
from bilqis_mlx.runtime.tests.capability.capability_retention_helpers import (
    _cases, _solver,
)
from bilqis_mlx.runtime.tests.custody.bamf_bundle.helpers import (
    candidate, next_accepted_step, parent_state,
)


CAPABILITY = "future:capability"
GROUP = "factory-group-zeta"
CASE_COUNT = 20


def _source_context():
    release = SimpleNamespace(
        release_sha256="1" * 64,
        semantic_catalog_sha256="2" * 64,
        execution_plan=SimpleNamespace(curriculum_sha256="3" * 64),
    )
    return SimpleNamespace(release=release)


def _cohort():
    cases, contexts = _cases(CAPABILITY, GROUP, CASE_COUNT, "future-title")
    cohort = EvaluationCohort(
        EvidenceKind.FIXED_SCHOOL,
        cases,
        ((CAPABILITY, GROUP),),
        "4" * 64,
        "5" * 64,
        "6" * 64,
        "7" * 64,
        (),
        (),
        case_census_digest(cases),
    )
    return cohort, contexts


def _measurement(bundle, cohort, contexts, correct_count, generation_digest):
    correct = {case.case_id for case in cohort.cases[:correct_count]}
    solver = _solver(contexts, correct)
    assessment = evaluate_capabilities(solver, cohort, generation_digest)
    checkpoint = Checkpoint(
        candidate_identity_for_canonical_consumer(bundle.retained_state),
        f"bamf-generations/{bundle.generation}",
        bundle.retained_state.optimizer_step,
        True,
    )
    binding = ReplayBinding(
        solver,
        generation_digest,
        checkpoint,
        GROUP,
        tuple(sorted(set(assessment.solver_contracts))),
        lambda generation, offered: (
            generation == generation_digest and offered == checkpoint),
    )
    return assessment, binding


def _evaluation(cohort, assessment):
    return SimpleNamespace(
        championship_cohort=cohort,
        championship_assessment=assessment,
    )


class NativeCapabilityChampionshipTests(unittest.TestCase):
    def setUp(self):
        self.cohort, self.contexts = _cohort()
        self.context = _source_context()
        self.parent = candidate(parent_state())
        self.cache = SimpleNamespace(accepted_manifest_sha256="a" * 64)

    def _bind(self, parent, successor, assessment, binding, incumbent=None):
        with patch(
                "bilqis_mlx.runtime.bamf_operator.championship."
                "_require_factory_evaluation",
                side_effect=lambda value: value), patch(
                "bilqis_mlx.runtime.bamf_operator.championship._current_binding",
                return_value=binding), patch(
                "bilqis_mlx.runtime.bamf_operator.championship._incumbent_binding",
                **({"return_value": incumbent} if incumbent is not None else {
                    "side_effect": AssertionError("unexpected incumbent replay")})):
            return bind_accepted_championship_successor(
                Path("unused"), parent, self.cache, successor, self.context,
                "artifact", CAPABILITY, _evaluation(self.cohort, assessment))

    def test_exact_ninety_percent_keeps_no_active_title_or_checkpoint_custody(self):
        successor = candidate(
            next_accepted_step(self.parent.retained_state), generation=1,
            parent="a" * 64)
        assessment, binding = _measurement(
            successor, self.cohort, self.contexts, 18, "8" * 64)
        result = self._bind(self.parent, successor, assessment, binding)
        self.assertEqual(result.championship_state["active_roles"], {})
        self.assertEqual(active_checkpoint_references(result.championship_state), ())

    def test_nineteen_of_twenty_earns_first_title_without_grade_ontology(self):
        successor = candidate(
            next_accepted_step(self.parent.retained_state), generation=1,
            parent="a" * 64)
        assessment, binding = _measurement(
            successor, self.cohort, self.contexts, 19, "8" * 64)
        result = self._bind(self.parent, successor, assessment, binding)
        role = result.championship_state["active_roles"][CAPABILITY]
        self.assertEqual((role["correct"], role["total"]), (19, 20))
        self.assertEqual(role["capability_group"], GROUP)
        self.assertEqual(
            active_checkpoint_references(result.championship_state),
            (role["checkpoint"],))

    def _titled_state_with_settlement(self):
        first = candidate(
            next_accepted_step(self.parent.retained_state), generation=1,
            parent="a" * 64)
        first_assessment, first_binding = _measurement(
            first, self.cohort, self.contexts, 20, "8" * 64)
        titled = self._bind(
            self.parent, first, first_assessment, first_binding)
        titled_state = json.loads(json.dumps(
            titled.championship_state, sort_keys=True))
        titled_state["settled_matchups"] = {
            CAPABILITY + "|" + "1" * 64 + "|" + "2" * 64: {
                "capability": CAPABILITY,
                "winner_sha256": "1" * 64,
            },
        }
        return replace(titled, championship_state=titled_state)

    def test_semantic_epoch_change_clears_live_roles_and_pair_suppression(self):
        resumed = self._titled_state_with_settlement()
        changed_context = _source_context()
        changed_context.release.semantic_catalog_sha256 = "f" * 64
        successor = candidate(
            next_accepted_step(resumed.retained_state), generation=2,
            parent="b" * 64)
        assessment, binding = _measurement(
            successor, self.cohort, self.contexts, 18, "9" * 64)
        with patch(
                "bilqis_mlx.runtime.bamf_operator.championship."
                "_require_factory_evaluation",
                side_effect=lambda value: value), patch(
                "bilqis_mlx.runtime.bamf_operator.championship._current_binding",
                return_value=binding), patch(
                "bilqis_mlx.runtime.bamf_operator.championship._incumbent_binding",
                side_effect=AssertionError("old-epoch incumbent must not replay")):
            result = bind_accepted_championship_successor(
                Path("unused"), resumed, self.cache, successor,
                changed_context, "artifact", CAPABILITY,
                _evaluation(self.cohort, assessment))
        self.assertEqual(result.championship_state["active_roles"], {})
        self.assertEqual(result.championship_state["settled_matchups"], {})
        self.assertEqual(active_checkpoint_references(result.championship_state), ())

    def test_nonsemantic_identity_reset_clears_titles_but_preserves_pair_suppression(self):
        resumed = self._titled_state_with_settlement()
        changed_context = _source_context()
        changed_context.release.release_sha256 = "f" * 64
        changed_context.release.execution_plan.curriculum_sha256 = "e" * 64
        successor = candidate(
            next_accepted_step(resumed.retained_state), generation=2,
            parent="b" * 64)
        assessment, binding = _measurement(
            successor, self.cohort, self.contexts, 18, "9" * 64)
        with patch(
                "bilqis_mlx.runtime.bamf_operator.championship."
                "_require_factory_evaluation",
                side_effect=lambda value: value), patch(
                "bilqis_mlx.runtime.bamf_operator.championship._current_binding",
                return_value=binding), patch(
                "bilqis_mlx.runtime.bamf_operator.championship._incumbent_binding",
                side_effect=AssertionError("reset titles must not replay")):
            result = bind_accepted_championship_successor(
                Path("unused"), resumed, self.cache, successor,
                changed_context, "artifact", CAPABILITY,
                _evaluation(self.cohort, assessment))
        self.assertEqual(result.championship_state["active_roles"], {})
        self.assertEqual(
            result.championship_state["settled_matchups"],
            resumed.championship_state["settled_matchups"])

    def test_title_survives_cold_resume_failed_challenge_then_tie_transfers(self):
        first = candidate(
            next_accepted_step(self.parent.retained_state), generation=1,
            parent="a" * 64)
        first_assessment, incumbent = _measurement(
            first, self.cohort, self.contexts, 20, "8" * 64)
        titled = self._bind(self.parent, first, first_assessment, incumbent)
        role = titled.championship_state["active_roles"][CAPABILITY]
        self.assertEqual(role["capability_group"], GROUP)
        self.assertEqual(
            active_checkpoint_references(titled.championship_state),
            (role["checkpoint"],))

        cold_state = json.loads(json.dumps(
            titled.championship_state, sort_keys=True))
        resumed_parent = replace(titled, championship_state=cold_state)

        failed = candidate(
            next_accepted_step(resumed_parent.retained_state), generation=2,
            parent="b" * 64)
        failed_assessment, failed_binding = _measurement(
            failed, self.cohort, self.contexts, 19, "9" * 64)
        defended = self._bind(
            resumed_parent, failed, failed_assessment, failed_binding,
            incumbent=incumbent)
        self.assertEqual(
            defended.championship_state["active_roles"][CAPABILITY]["checkpoint"],
            role["checkpoint"])
        self.assertEqual(
            active_checkpoint_references(defended.championship_state),
            (role["checkpoint"],))

        tied = candidate(
            next_accepted_step(defended.retained_state), generation=3,
            parent="c" * 64)
        tied_assessment, challenger = _measurement(
            tied, self.cohort, self.contexts, 20, "a" * 64)
        transferred = self._bind(
            defended, tied, tied_assessment, challenger, incumbent=incumbent)
        winner = transferred.championship_state["active_roles"][CAPABILITY]
        self.assertEqual(winner["checkpoint"], asdict(challenger.checkpoint))
        self.assertNotEqual(winner["checkpoint"], role["checkpoint"])
        self.assertEqual(
            active_checkpoint_references(transferred.championship_state),
            (winner["checkpoint"],))
        self.assertTrue(transferred.championship_state["settled_matchups"])


if __name__ == "__main__":
    unittest.main()
