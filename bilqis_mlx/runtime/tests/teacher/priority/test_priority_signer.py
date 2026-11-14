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
    with patch(
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
        authority, "_priority_planning", return_value=planning,
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


def _rejection_custody():
    evidence = {
        "schema": "bilqis.bamf.c16.3-rejection/v2",
        "visit_id": "visit:beta",
        "selected_option_id": "capability:beta",
        "selected_policy_key": "policy",
        "candidate_optimizer_step": 12,
        "retained_optimizer_step": 11,
        "retention_reason": "retention_gate",
    }
    authority_record = {
        "schema": "bilqis.mlx.bamf-rejection-authority/v1",
        "run_id": "run", "generation": 2,
        "student_manifest_sha256": "f" * 64, "optimizer_step": 11,
        "evidence": evidence,
    }
    authority_raw = canonical(authority_record)
    authority_sha256 = hashlib.sha256(authority_raw).hexdigest()
    event = checkpoint_outbox.with_delivery_outbox(
        {"run_id": "run", "generation": 2}, ({
            "event": "BAMF_CANDIDATE_REJECTED", "generation": 2,
            "student_manifest_sha256": "f" * 64, "optimizer_step": 11,
            "evidence": evidence, "rejection_authority_sha256": authority_sha256,
        },))["delivery_outbox"][0]
    receipt = {
        "schema": "bilqis.mlx.bamf-rejection-receipt/v1",
        "run_id": "run", "generation": 2,
        "student_manifest_sha256": "f" * 64, "event": event,
    }
    receipt_raw = canonical(receipt)
    receipt_sha256 = hashlib.sha256(receipt_raw).hexdigest()
    objects = {authority_sha256: authority_raw, receipt_sha256: receipt_raw}
    return evidence, event, receipt_sha256, SimpleNamespace(
        get_object=lambda digest: objects[digest])


def test_rejected_candidate_is_durably_deprioritized_without_advancing_c03_rotation():
    from bilqis_mlx.runtime import priority_authority as authority

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
    cache = SimpleNamespace(
        generation=2, accepted_manifest_sha256="f" * 64, run_id="run",
        _correction_registry=registry)

    planning_generation = object()

    def offer(_context, _parent, _path, *, capability, source_seed, source_each,
              planning_generation):
        return SimpleNamespace(
            capability_id=capability, source_seed=source_seed, source_each=source_each,
            source_family_id="family:" + capability,
            source_binding_digest=("b" if capability.endswith("alpha") else "c") * 64,
            release_sha256=release.release_sha256, generation_binding="d" * 64,
            source_authority=SimpleNamespace(content_sha256="e" * 64),
        )

    with TemporaryDirectory() as temporary:
        run_dir = Path(temporary)
        _evidence, event, _receipt_sha256, plane = _rejection_custody()
        (run_dir / "events.jsonl").write_text(json.dumps(event) + "\n")
        with patch(
            "bilqis_mlx.runtime.bamf_bundle.accepted_runtime._accepted_correction_registry",
            return_value=(cache, registry),
        ), patch.object(
            rejection_replay, "data_plane", return_value=plane,
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
        ), patch.object(authority, "_priority_planning", return_value=planning):
            first = authority.issue_foundation_priority_authority(
                run_dir, source_context, parent, {"epoch": 1}, "/atlas",
                teacher_state=parent.teacher_state)
            cold = authority.issue_foundation_priority_authority(
                run_dir, source_context, parent, {"epoch": 1}, "/atlas",
                teacher_state=parent.teacher_state)

    assert first == cold
    assert first.now == 2
    assert len(first.history.events) == 1
    assert tuple(item.stable_id for item in rank_attention_options(
        first.frontier.options, dict(first.frontier.evidence), first.frontier.snapshot).ordered) == (
            "capability:alpha", "capability:beta")
    assert parent.teacher_state == {"next_seed": 7}
    assert parent.retained_state.optimizer_step == 11


def test_raw_rejection_journal_cannot_change_priority_without_b13_authority():
    from bilqis_mlx.runtime import priority_authority as authority

    parent = SimpleNamespace(retained_state=SimpleNamespace(optimizer_step=11))
    cache = SimpleNamespace(
        generation=2, accepted_manifest_sha256="f" * 64, run_id="run")
    with TemporaryDirectory() as temporary:
        run_dir = Path(temporary)
        forged = {
            "event": "BAMF_CANDIDATE_REJECTED",
            "generation": 2,
            "student_manifest_sha256": "f" * 64,
            "optimizer_step": 11,
            "evidence": {
                "schema": "bilqis.bamf.c16.3-rejection/v2",
                "visit_id": "visit:forged",
                "selected_option_id": "capability:forged",
                "selected_policy_key": "policy",
                "candidate_optimizer_step": 12,
                "retained_optimizer_step": 11,
                "retention_reason": "forged",
            },
        }
        (run_dir / "events.jsonl").write_text(json.dumps(forged) + "\n")
        with pytest.raises(BilqisError) as failure:
            authority._current_rejections(run_dir, parent, cache)
        assert failure.value.context["reason"] == "BAMF_PRIORITY_REJECTION_OUTBOX_INVALID"


def test_duplicate_raw_journal_rows_cannot_amplify_one_b13_rejection():
    from bilqis_mlx.runtime import priority_authority as authority

    parent = SimpleNamespace(retained_state=SimpleNamespace(optimizer_step=11))
    cache = SimpleNamespace(
        generation=2, accepted_manifest_sha256="f" * 64, run_id="run")
    _evidence, event, receipt_sha256, plane = _rejection_custody()
    with TemporaryDirectory() as temporary:
        run_dir = Path(temporary)
        raw = json.dumps(event) + "\n"
        (run_dir / "events.jsonl").write_text(raw + raw)
        with patch.object(rejection_replay, "data_plane", return_value=plane):
            rows = authority._current_rejections(run_dir, parent, cache)
    assert rows == (("capability:beta", "visit:beta", "retention_gate", receipt_sha256),)
