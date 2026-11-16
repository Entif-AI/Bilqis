"""#1317 generation-bound local protection-plan contract."""
from types import SimpleNamespace as NS
import unittest
from unittest.mock import patch

from bilqis_mlx.runtime.capability_retention import EvidenceStage
from bilqis_mlx.runtime.retention.protection_plan import (
    RetentionProtectionPlan,
)
from bilqis_mlx.runtime.retention.protection_plan_compiler import _compile_plan
from bilqis_mlx.semantics.domains import contract_digest


def _capability(capability_id, grade_id="A", *, prerequisites=(), composed_of=()):
    return NS(
        capability_id=capability_id,
        grade_id=grade_id,
        prerequisites=tuple(prerequisites),
        composed_of=tuple(composed_of),
    )


class _Plan:
    def __init__(self, capabilities):
        self.capabilities = tuple(capabilities)
        self.profile_id = "fixture-profile"
        self.curriculum_sha256 = "1" * 64
        self.profile_sha256 = "2" * 64
        self.projection_digests = NS(source="3" * 64)
        self.grades = (
            NS(
                grade_id="A", capabilities=("TARGET",),
                teaching_stages=(("TARGET",),), cumulative_scope=("TARGET",),
                assessment_blueprint_sha256="4" * 64),
            NS(
                grade_id="Z", capabilities=(),
                teaching_stages=(), cumulative_scope=(),
                assessment_blueprint_sha256="5" * 64),
        )

    def digest(self):
        return contract_digest(tuple(
            (item.capability_id, item.grade_id, item.prerequisites, item.composed_of)
            for item in self.capabilities))


def _release(*, extra=0, target_grade="A", add_dependency=False):
    capabilities = [
        _capability(
            "TARGET", target_grade,
            prerequisites=("PRE", *((("NEW",) if add_dependency else ()))),
            composed_of=("PART",)),
        _capability("PRE"),
        _capability("PART"),
        _capability("DEPENDENT", prerequisites=("TARGET",)),
        _capability("SIBLING", composed_of=("PART",)),
        _capability("RAW_SKOS_NEIGHBOR"),
    ]
    if add_dependency:
        capabilities.append(_capability("NEW"))
    capabilities.extend(_capability(f"UNRELATED:{index}") for index in range(extra))
    return NS(
        release_sha256="a" * 64,
        semantic_catalog_sha256="b" * 64,
        execution_plan=_Plan(capabilities),
        raw_skos_neighbors={"TARGET": ("RAW_SKOS_NEIGHBOR",)},
    )


def _plan(release, established):
    return _compile_plan(
        release,
        established_capability_ids=tuple(established),
        retained_evidence_sha256="c" * 64,
        policy_sha256="d" * 64,
        accepted_generation=7,
        accepted_manifest_sha256="e" * 64,
        evidence_stage=EvidenceStage.FOUNDATION_ACQUISITION,
    )


class RetentionProtectionPlanTests(unittest.TestCase):
    def test_ordinary_scope_uses_only_compiled_factory_relations(self):
        plan = _plan(
            _release(),
            {"PRE", "PART", "DEPENDENT", "SIBLING", "RAW_SKOS_NEIGHBOR"})

        target = plan.for_target("TARGET")

        self.assertEqual(
            target.evaluated_capability_ids,
            ("TARGET", "DEPENDENT", "PART", "PRE", "SIBLING"),
        )
        self.assertNotIn("RAW_SKOS_NEIGHBOR", target.evaluated_capability_ids)

    def test_unrelated_school_growth_does_not_change_ordinary_scope(self):
        established = {"PRE", "PART", "DEPENDENT", "SIBLING"}
        small = _plan(_release(extra=0), established).for_target("TARGET")
        large = _plan(
            _release(extra=1000),
            established | {f"UNRELATED:{index}" for index in range(1000)},
        ).for_target("TARGET")

        self.assertEqual(
            large.evaluated_capability_ids,
            small.evaluated_capability_ids,
        )

    def test_one_real_dependency_adds_exactly_one_protected_capability(self):
        established = {"PRE", "PART", "DEPENDENT", "SIBLING"}
        before = _plan(_release(), established).for_target("TARGET")
        after = _plan(
            _release(add_dependency=True),
            established | {"NEW"},
        ).for_target("TARGET")

        self.assertEqual(
            set(after.evaluated_capability_ids)
            - set(before.evaluated_capability_ids),
            {"NEW"},
        )

    def test_grade_z_uses_the_same_plan_contract(self):
        target = _plan(
            _release(target_grade="Z"),
            {"PRE", "PART", "DEPENDENT", "SIBLING"},
        ).for_target("TARGET")

        self.assertEqual(target.target_grade_id, "Z")
        self.assertEqual(target.evaluated_capability_groups[0], ("TARGET", "Z"))

    def test_cold_record_round_trip_preserves_plan_digest(self):
        plan = _plan(
            _release(),
            {"PRE", "PART", "DEPENDENT", "SIBLING"})

        cold = RetentionProtectionPlan.from_record(plan.to_record())

        self.assertEqual(cold.digest, plan.digest)
        self.assertEqual(
            cold.for_target("TARGET").evaluated_capability_ids,
            plan.for_target("TARGET").evaluated_capability_ids,
        )

    def test_plan_compilation_never_uses_network_or_raw_skos_neighbors(self):
        release = _release()
        with patch(
                "socket.create_connection",
                side_effect=AssertionError("retention planning attempted network")):
            plan = _plan(
                release,
                {"PRE", "PART", "DEPENDENT", "SIBLING", "RAW_SKOS_NEIGHBOR"},
            )

        target = plan.for_target("TARGET")
        self.assertNotIn("RAW_SKOS_NEIGHBOR", target.evaluated_capability_ids)


if __name__ == "__main__":
    unittest.main()
