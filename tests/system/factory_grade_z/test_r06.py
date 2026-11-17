"""R06 proof that championship epoch history is generic for disposable Grade Z."""
from bilqis_mlx.learning.capability_championship_state import (
    championship_epoch_identity,
    compact_championship_state,
    reset_championship_state,
)
from tests.system.factory_grade_z.fixture import CAPABILITIES, fixture


def _identity(release):
    projections = release.execution_plan.projection_digests
    return championship_epoch_identity(
        factory_release_sha256=release.release_sha256,
        semantic_catalog_sha256=release.semantic_catalog_sha256,
        curriculum_sha256=release.execution_plan.curriculum_sha256,
        capability_groups_sha256=projections.roster,
        fixed_cohort_sha256=projections.assessment,
        rubric_sha256=projections.assessment,
        scope_sha256=projections.coverage,
        source_sha256=projections.source,
        policy_sha256="8" * 64,
        topology_sha256="9" * 64,
        extents_sha256="a" * 64,
        semantic_abi={"schema": "grade-z-r06"},
    )


def test_grade_z_settlement_lifetime_resets_only_at_a_fresh_championship_epoch():
    _registry, _graph, release = fixture()
    capability = CAPABILITIES[0]
    identity = _identity(release)
    key = capability + "|" + "1" * 64 + "|" + "2" * 64
    state = compact_championship_state({
        "active_roles": {},
        "settled_matchups": {key: {
            "capability": capability, "winner_sha256": "1" * 64,
        }},
    }, identity)

    source_drift = {**identity, "source_sha256": "b" * 64}
    same_epoch = reset_championship_state(
        state, source_drift, source_manifest_sha256="c" * 64,
        source_generation=7)
    assert same_epoch["settled_matchups"] == state["settled_matchups"]
    assert len(same_epoch["epoch_history"]) == 1

    new_semantics = {**source_drift, "semantic_catalog_sha256": "d" * 64}
    next_epoch = reset_championship_state(
        same_epoch, new_semantics, source_manifest_sha256="e" * 64,
        source_generation=8)
    assert next_epoch["settled_matchups"] == {}
    assert len(next_epoch["epoch_history"]) == 2
    assert next_epoch["active_roles"] == {}
