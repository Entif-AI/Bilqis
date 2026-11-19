"""C06 host signer binds private authority to the already-accepted C09 public root."""
import json
import hashlib
from pathlib import Path
from tempfile import TemporaryDirectory
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat
from types import SimpleNamespace
from unittest.mock import patch
import pytest

from bilqis_mlx.errors import BilqisError
from bilqis_mlx.runtime.atlas_source_authority import (
    SourceAuthorityKey, SourceAuthorityRegistry, SourceAuthorityScope,
)
from bilqis_mlx.runtime.bamf_bundle._darwin_salience_signer import (
    HostSourceAuthoritySigner,
)
from bilqis_mlx.semantics.cognitive_dependencies import DependencyKind, DependencyRef
from bilqis_mlx.learning.atlas_salience import DispatchTier, rank_attention_options
from bilqis_mlx.learning.salience_contracts import Ordinal
from bilqis_mlx.semantic_sampling import DEFAULT_BINARY_BALANCE
from bilqis_mlx.runtime import checkpoint_outbox
from bilqis_mlx.runtime import priority_rejection_replay as rejection_replay
from bilqis_mlx.runtime.bamf_bundle.records import canonical


def _registry(private_hex="44" * 32):
    key = Ed25519PrivateKey.from_private_bytes(bytes.fromhex(private_hex))
    public = key.public_key().public_bytes(Encoding.Raw, PublicFormat.Raw).hex()
    scopes = tuple(sorted((SourceAuthorityScope(kind, prefix) for kind, prefix in (
        (DependencyKind.POLICY, "salience-policy:"),
        (DependencyKind.SOURCE, "salience-fact:"),
        (DependencyKind.ARTIFACT, "salience-option:"),
        (DependencyKind.ARTIFACT, "salience-event:"),
    )), key=lambda scope: (scope.kind.value, scope.key_prefix)))
    return SourceAuthorityRegistry((SourceAuthorityKey("owner:c06", public, scopes),))


def _lawful_frontier(planning_generation, *ready):
    return SimpleNamespace(
        ready_capability_ids=tuple(ready),
        frontier_sha256="9" * 64,
        _planning_generation=planning_generation,
    )


def _cadence(*ready):
    return SimpleNamespace(
        authorized_capability_ids=tuple(ready),
        phase=SimpleNamespace(value="MAIN"),
        disposition=SimpleNamespace(value="TEACHING"),
    )


def _foundation_case():
    registry = _registry()
    signer = HostSourceAuthoritySigner("owner:c06", "44" * 32, registry)
    release = SimpleNamespace(
        release_sha256="a" * 64,
        execution_plan=SimpleNamespace(capabilities=(
            SimpleNamespace(capability_id="capability:alpha"),
            SimpleNamespace(capability_id="capability:beta"),
        )),
    )
    source_context = SimpleNamespace(release=release)
    planning = SimpleNamespace(selection=None)
    parent = SimpleNamespace(
        teacher_state={"next_seed": 7},
        correction_frontier={"rights_epoch": 0, "correction_generation": 0},
        retained_state=SimpleNamespace(optimizer_step=11),
    )
    planning_generation = object()

    def offer(_context, _parent, _path, *, capability, source_seed, source_each,
              planning_generation):
        return SimpleNamespace(
            capability_id=capability,
            source_seed=source_seed,
            source_each=source_each,
            source_family_id="family:" + capability,
            source_binding_digest=("b" if capability.endswith("alpha") else "c") * 64,
            release_sha256=release.release_sha256,
            generation_binding="d" * 64,
            source_authority=SimpleNamespace(content_sha256="e" * 64),
        )

    cache = SimpleNamespace(
        generation=2, accepted_manifest_sha256="f" * 64, run_id="run",
        _correction_registry=registry)
    lawful = _lawful_frontier(
        planning_generation, "capability:alpha", "capability:beta")
    return (
        registry, signer, source_context, planning, parent,
        planning_generation, offer, cache, lawful,
    )


def test_host_signer_must_match_registered_owner_key_and_scope():
    registry = _registry()
    signer = HostSourceAuthoritySigner("owner:c06", "44" * 32, registry)
    dependency = DependencyRef(DependencyKind.POLICY, "salience-policy:foundation")
    payload = b"signed-c06-record"
    signature = signer.sign(dependency, payload)
    registry.verify_detached(signer.owner_id, dependency, signature, payload)

    with pytest.raises(ValueError):
        signer.sign(DependencyRef(DependencyKind.POLICY, "other-policy:foundation"), payload)
    with pytest.raises(ValueError):
        HostSourceAuthoritySigner("owner:c06", "55" * 32, registry).sign(
            dependency, payload)


def test_foundation_priority_issuer_emits_unknown_evidence_and_c06_rotation_only():
    from bilqis_mlx.runtime import priority_authority as authority

    (registry, signer, source_context, planning, parent,
     planning_generation, offer, cache, lawful) = _foundation_case()
    plane = SimpleNamespace(sync_event_ledger=lambda *_args: None)
    with patch.object(rejection_replay, "data_plane", return_value=plane), patch(
        "bilqis_mlx.runtime.bamf_bundle.accepted_runtime._accepted_correction_registry",
        return_value=(cache, registry),
    ), patch(
        "bilqis_mlx.runtime.bamf_bundle._darwin_salience_signer.read_host_system_source_authority_signer",
        return_value=signer,
    ), patch.object(
        authority, "bind_priority_planning_generation",
        return_value=planning_generation,
    ), patch.object(
        authority, "_require_planning_generation",
        return_value=(cache, None),
    ), patch.object(authority, "prepare_priority_source_offer", side_effect=offer), patch.object(
        authority, "priority_rotation_state",
        return_value=(1, {"capability:alpha": 1}),
    ), patch.object(
        authority, "_build_priority_planning_epoch", return_value="epoch",
    ), patch.object(
        authority, "_priority_planning_from_epoch", return_value=planning,
    ), patch(
        "bilqis_mlx.runtime.lawful_teaching_frontier._issue_lawful_teaching_frontier_from_epoch",
        return_value=lawful,
    ), patch(
        "bilqis_mlx.runtime.active_grade_cadence.issue_active_grade_cadence",
        return_value=_cadence("capability:alpha", "capability:beta"),
    ), patch.object(
        authority, "_ordered_rejections", return_value=(),
    ), patch.object(
        authority, "_rejection_recency", return_value=(0, {}),
    ):
        issued = authority.issue_foundation_priority_authority(
            "/run", source_context, parent, {"epoch": 1}, "/atlas",
            teacher_state=parent.teacher_state)

    evidence = dict(issued.frontier.evidence)
    assert issued.now == 1
    assert {item.impact.ordinal for item in evidence.values()} == {Ordinal.UNKNOWN}
    assert {item.exigency.ordinal for item in evidence.values()} == {Ordinal.UNKNOWN}
    assert {item.novelty.ordinal for item in evidence.values()} == {Ordinal.UNKNOWN}
    ranked = rank_attention_options(
        issued.frontier.options, evidence, issued.frontier.snapshot)
    assert tuple(item.stable_id for item in ranked.ordered) == (
        "capability:beta", "capability:alpha")
    assert {tier for _, tier in ranked.tiers} == {DispatchTier.FAIR_ROTATION}
    assert {offer.source_each for _, offer in issued.offers} == {
        DEFAULT_BINARY_BALANCE.minimum_total}
    assert len({offer.source_seed for _, offer in issued.offers}) == 2
    assert issued.planning is planning
    assert issued.lawful_frontier is lawful
    assert issued.lawful_frontier_sha256 == lawful.frontier_sha256


def test_all_held_frontier_issues_empty_priority_authority_without_source_rows():
    from bilqis_mlx.runtime import priority_authority as authority

    release = SimpleNamespace(
        release_sha256="a" * 64,
        execution_plan=SimpleNamespace(capabilities=(
            SimpleNamespace(capability_id="capability:alpha"),
            SimpleNamespace(capability_id="capability:beta"),
        )),
    )
    source_context = SimpleNamespace(release=release)
    parent = SimpleNamespace(
        teacher_state={"next_seed": 7},
        retained_state=SimpleNamespace(optimizer_step=11),
    )
    cache = SimpleNamespace(_correction_registry=_registry())
    planning_generation = object()
    planning = SimpleNamespace(selection=None)
    lawful = _lawful_frontier(planning_generation)

    with patch.object(
            authority, "priority_rotation_state", return_value=(3, {})), patch.object(
            authority, "bind_priority_planning_generation",
            return_value=planning_generation), patch.object(
            authority, "_require_planning_generation",
            return_value=(cache, None)), patch.object(
            authority, "_build_priority_planning_epoch", return_value="epoch"), patch.object(
            authority, "_priority_planning_from_epoch", return_value=planning), patch(
            "bilqis_mlx.runtime.lawful_teaching_frontier."
            "_issue_lawful_teaching_frontier_from_epoch",
                return_value=lawful), patch(
                "bilqis_mlx.runtime.active_grade_cadence.issue_active_grade_cadence",
                return_value=_cadence()), patch.object(
            authority, "prepare_priority_source_offer") as prepare, patch(
            "bilqis_mlx.runtime.bamf_bundle._darwin_salience_signer."
            "read_host_system_source_authority_signer") as signer:
        issued = authority.issue_foundation_priority_authority(
            "/run", source_context, parent, {"epoch": 1}, "/atlas",
            teacher_state=parent.teacher_state)

    assert issued.frontier is None
    assert issued.history is None
    assert issued.offers == ()
    assert issued.now == 3
    assert issued.lawful_frontier is lawful
    prepare.assert_not_called()
    signer.assert_not_called()
