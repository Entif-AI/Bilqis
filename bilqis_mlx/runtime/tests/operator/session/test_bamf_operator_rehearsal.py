"""R14 native rehearsal planning, custody, and provenance contracts."""
from types import SimpleNamespace as NS
from unittest.mock import patch

import pytest

from bilqis_mlx.errors import BilqisError
from bilqis_mlx.runtime.atlas_training_contracts import BamfDeliveryProvenance
from bilqis_mlx.runtime.factory_training_bridge import _target_source_count
from bilqis_mlx.runtime.bamf_operator.session_parts.rehearsal import (
    RehearsalPlan, RehearsalRows, compile_rehearsal_plan,
    materialize_rehearsal_rows,
)
from bilqis_mlx.runtime.bamf_operator.source_prefetch import (
    prepare_priority_source_packet, priority_source_request,
)
from bilqis_mlx.runtime.source_execution import source_content_digest
from bilqis_mlx.runtime.source_prefetch import thaw_source_packet
from bilqis_mlx.runtime.tests.batch.training.visit_provenance_support import (
    visit_provenance,
)
from bilqis_mlx.semantics.domains import contract_digest


def test_plan_is_grade_neutral_and_partitions_authorized_relationships():
    from bilqis_mlx.runtime.retention.protection_plan import (
        ProtectionReason,
    )
    target = NS(
        target_grade_id="GENERATED-ZETA",
        protected_capability_ids=("Z.C0", "Z.C1"),
        affected_edges=(
            NS(capability_id="Z.C0", reason=ProtectionReason.PREREQUISITE),
            NS(capability_id="Z.C1", reason=ProtectionReason.DEPENDENT),
        ),
    )
    protection = NS(digest="a" * 64)
    active = NS(
        member_capability_ids=("Z.C2",), activation_sha256="f" * 64,
        definition=NS(definition_sha256="1" * 64))
    release = NS(execution_plan=NS(capability_map={
        "Z.C2": NS(grade_id="GENERATED-ZETA")
    }))
    weakness = {
        "weakness_evidence_sha256": "b" * 64,
        "weakness_class": {
            "provider_id": "provider:z", "provider_implementation_sha256": "c" * 64,
            "classifier_id": "classifier:z", "classifier_sha256": "d" * 64,
            "structural_signature": {"shape": "novel"}, "class_sha256": "e" * 64,
        },
    }
    with patch(
            "bilqis_mlx.runtime.bamf_operator.session_parts.rehearsal.require_current_retention_plan",
            return_value=(protection, target)), patch(
            "bilqis_mlx.runtime.bamf_operator.session_parts.rehearsal.current_structural_weaknesses",
            return_value=({"weakness": weakness},)), patch(
            "bilqis_mlx.runtime.active_generated_grade.read_active_generated_grade",
            return_value=active):
        plan = compile_rehearsal_plan(
            "/run", object(), object(), NS(release=release),
            NS(offer=NS(capability_id="Z.C2")))

    assert plan.target_capability_id == "Z.C2"
    assert plan.target_grade_id == "GENERATED-ZETA"
    assert plan.prior_capability_ids == ("Z.C0",)
    assert plan.retention_support_capability_ids == ("Z.C1",)
    assert plan.weakness_records == (weakness,)
    assert plan.active_grade_definition_sha256 == "1" * 64
    assert plan.active_grade_activation_sha256 == "f" * 64


class _BoundSourceContext:
    def execution_for(self, capability):
        return NS(
            provider_id="provider:" + capability,
            provider_implementation_sha256=contract_digest({"capability": capability}),
        )

    def draw_bound_rows(self, *, seed, capability, each):
        assert each == 1
        row = {
            "id": f"{capability}:{seed}", "capability": capability,
            "source_family_id": f"family:{capability}", "episode_id": f"episode:{seed}",
        }
        authority = NS(
            capability_id=capability, seed=seed, each=1,
            source_family_id=row["source_family_id"],
        )
        return (row,), authority


def test_materialization_retains_one_row_source_authority_per_rehearsal_specimen():
    plan = RehearsalPlan(
        "Z.C2", "GENERATED-ZETA", ("Z.C0",), ("Z.C1",), (),
        "a" * 64, "c" * 64, "d" * 64, "b" * 64)
    rows = materialize_rehearsal_rows(_BoundSourceContext(), plan, 3)

    assert tuple(row["capability"] for row in rows.prior) == ("Z.C0",)
    assert tuple(row["capability"] for row in rows.retention_support) == ("Z.C1",)
    assert set(rows.bindings_by_id) == set(rows.authorities_by_id)
    for identity, binding in rows.bindings_by_id.items():
        authority = rows.authorities_by_id[identity]
        assert binding["seed"] == authority.seed
        assert binding["each"] == authority.each == 1
        assert binding["capability"] == authority.capability_id


def test_worker_packet_transports_roles_but_not_process_live_authority():
    direct = ({"id": "Z.C2:direct", "capability": "Z.C2"},)
    prior = ({"id": "Z.C0:prior", "capability": "Z.C0"},)
    binding = {
        "row_id": "Z.C0:prior", "role": "prior", "capability": "Z.C0",
        "seed": 31, "each": 1, "source_family_id": "family:Z.C0",
        "episode_id": "episode:31",
    }
    rehearsal = RehearsalRows(prior=prior, bindings=(binding,), authorities=((prior[0]["id"], object()),))
    source_binding = {"capability": "Z.C2", "provider": "fixture"}
    offer = NS(
        accepted_manifest_sha256="a" * 64, generation_binding="b" * 64,
        release_sha256="c" * 64, capability_id="Z.C2", source_seed=17,
        source_each=1, source_family_id="family:Z.C2",
        source_binding_digest=contract_digest(source_binding),
        source_authority=NS(content_sha256=source_content_digest(direct)),
        rows=lambda: direct,
    )
    selection = NS(offer=offer, visit=NS(identity=NS(visit_id="visit:z")))
    release = NS(
        release_sha256="c" * 64,
        source_bindings=NS(by_capability={"Z.C2": source_binding}))
    request = priority_source_request(
        selection, NS(release=release), NS(retained_state=NS(optimizer_step=7)), 1,
        enrichment_rows=(), rehearsal_plan=NS(identity="d" * 64), rehearsal=rehearsal)
    packet = prepare_priority_source_packet(request)
    payload = thaw_source_packet(packet)

    assert payload["prior"] == list(prior)
    assert "rehearsal_bindings" not in payload
    assert request["rehearsal_bindings"] == [binding]
    assert "authorities" not in request


def _delivery_provenance(row_capability, rehearsal):
    row = {"id": "row:z", "capability": row_capability}
    return BamfDeliveryProvenance(
        row["id"], source_content_digest((row,)), None, row_capability, None,
        (), 1, 1, rehearsal, 0, visit_provenance("Z.C2"), "family:z", "episode:z")


def test_cross_capability_delivery_requires_explicit_rehearsal_role():
    assert _delivery_provenance("Z.C0", "prior").rehearsal == "prior"
    with pytest.raises(BilqisError) as failure:
        _delivery_provenance("Z.C0", None)
    assert failure.value.context["reason"] == "VISIT_PROVENANCE_CAPABILITY_MISMATCH"


def test_rehearsal_rows_do_not_inflate_target_source_batch_count():
    rows = (
        {"id": "target", "capability": "Z.C2"},
        {"id": "prior", "capability": "Z.C0"},
        {"id": "enrichment", "capability": "Z.C2"},
    )
    assert _target_source_count(rows, {"prior": "prior"}) == 2

