"""Fail-closed adversarial cases for the native CP07 source bridge."""
from dataclasses import replace
import json
import shutil
import unittest
from unittest.mock import patch

from bilqis_mlx.control_plane import ControlPlaneService
from bilqis_mlx.control_plane.native_contracts import canonical, sha
from bilqis_mlx.control_plane.native_source import (
    materialize_native_projection, refresh_native_events,
)
from bilqis_mlx.errors import BilqisError, ErrorBus, SCHOOL
from bilqis_mlx.learning.teacher_visit_identity import (
    TeacherVisitIdentity, require_teacher_visit_receipt,
    teacher_visit_receipt_record,
)
from bilqis_mlx.mission_control import CandidateDecision
from bilqis_mlx.runtime import checkpoint_outbox
from bilqis_mlx.runtime.bamf_bundle import record_bamf_rejection
from bilqis_mlx.runtime.tests.custody.bamf_bundle.helpers import retention_decision

from .native_source_support import NativeSourceFixture


class NativeSourceAdversarialTests(NativeSourceFixture, unittest.TestCase):
    def rejection_evidence(self, parent, **overrides):
        visit = self.native_visit(parent)
        decision = retention_decision(
            accepted=False, parent=parent.retained_state, retained=parent.retained_state)
        evidence = {
            "schema": "bilqis.bamf.c16.3-rejection/v2",
            "visit_id": visit.visit_id,
            "teacher_visit": visit.to_record(),
            "selected_option_id": "option:native",
            "selected_policy_key": visit.policy_key,
            "candidate_optimizer_step": parent.retained_state.optimizer_step + 1,
            "retained_optimizer_step": parent.retained_state.optimizer_step,
            "retention_reason": decision.reason,
            "capability": visit.capability_id,
            "decision": decision.to_record(),
        }
        return {**evidence, **overrides}

    def test_forged_c03_student_is_rejected(self):
        source = self.successor()
        stored = dict(source.teacher_state["last_visit"])
        forged = TeacherVisitIdentity(
            stored["run_identity_sha256"], stored["run_seed"], stored["generation"],
            stored["accepted_manifest_sha256"], stored["teacher_identity"],
            stored["teacher_epoch"], "f" * 64, stored["selection_seed"],
            stored["cursor"], stored["capability_id"], stored["policy_key"])
        source = replace(source, teacher_state={**source.teacher_state,
                                                "last_visit": forged.to_record()})
        with self.assertRaises(BilqisError) as caught:
            self.publish(source, acceptance=self.binding(source))
        self.assertEqual(
            caught.exception.context.get("reason"),
            "TEACHER_VISIT_RECEIPT_DRIFT",
        )

    def test_unissued_c03_capability_policy_pair_is_rejected(self):
        source = self.successor()
        real = TeacherVisitIdentity.from_record(source.teacher_state["last_visit"])
        forged = replace(real, capability_id="A.FORGED", policy_key="policy:forged")
        source = replace(
            source,
            teacher_state={**source.teacher_state, "last_visit": forged.to_record()},
            outbox=({**source.outbox[0], "capability": "A.FORGED"},))
        with self.assertRaises(BilqisError) as caught:
            self.publish(source, acceptance=self.binding(source))
        self.assertEqual(caught.exception.context.get("reason"),
                         "TEACHER_VISIT_RECEIPT_DRIFT")

    def test_recomputed_portable_receipt_cannot_replace_c03_issuance(self):
        source = self.successor()
        stored = TeacherVisitIdentity.from_record(source.teacher_state["last_visit"])
        forged = TeacherVisitIdentity(
            stored.run_identity_sha256, stored.run_seed, stored.generation,
            stored.accepted_manifest_sha256, stored.teacher_identity,
            stored.teacher_epoch, stored.student_sha256, stored.selection_seed,
            stored.cursor, "A.FORGED", stored.policy_key,
        )
        with self.assertRaises(BilqisError) as missing:
            require_teacher_visit_receipt(forged)
        self.assertEqual(
            missing.exception.context.get("reason"),
            "TEACHER_VISIT_RECEIPT_MISSING",
        )
        source = replace(
            source,
            teacher_state={
                **source.teacher_state,
                "last_visit": forged.to_record(),
                "last_visit_receipt": teacher_visit_receipt_record(forged),
            },
            outbox=tuple(
                {**event, "capability": "A.FORGED"}
                if event.get("event") == "BAMF_C16_3_ACCEPTED" else event
                for event in source.outbox
            ),
        )
        with self.assertRaises(BilqisError) as caught:
            self.publish(source, acceptance=self.binding(source))
        self.assertEqual(
            caught.exception.context.get("reason"),
            "TEACHER_VISIT_RECEIPT_MISSING",
        )

    def test_portable_history_requires_exact_accepted_teacher_custody(self):
        _source, pointer = self.publish_successor()
        old_manifest_sha = pointer["manifest_sha256"]
        old_root = self.run / "bamf-bundles" / old_manifest_sha
        manifest = json.loads((old_root / "manifest.json").read_bytes())
        teacher_binding = manifest["sidecars"]["teacher_state"]
        teacher = json.loads(
            (old_root / teacher_binding["filename"]).read_bytes())
        teacher["next_seed"] += 100
        teacher_raw = canonical(teacher)
        teacher_sha = sha(teacher_raw)
        manifest["sidecars"]["teacher_state"] = {
            **teacher_binding,
            "sha256": teacher_sha,
            "object_sha256": teacher_sha,
        }
        manifest_raw = canonical(manifest)
        new_manifest_sha = sha(manifest_raw)
        new_root = self.run / "bamf-bundles" / new_manifest_sha
        shutil.copytree(old_root, new_root)
        (new_root / teacher_binding["filename"]).write_bytes(teacher_raw)
        (new_root / "manifest.json").write_bytes(manifest_raw)
        acceptance_dir = self.run / "bamf-acceptance"
        shutil.copyfile(
            acceptance_dir / f"{old_manifest_sha}.json",
            acceptance_dir / f"{new_manifest_sha}.json",
        )
        pointer = {
            **pointer,
            "bundle": f"bamf-bundles/{new_manifest_sha}",
            "manifest_sha256": new_manifest_sha,
        }
        (self.run / "bamf-state.json").write_bytes(canonical(pointer))

        with self.assertRaises(BilqisError) as caught:
            materialize_native_projection(self.run)
        self.assertEqual(
            caught.exception.context.get("reason"),
            "CONTROL_PLANE_NATIVE_HISTORY_ACCEPTANCE_DRIFT",
        )

    def test_accepted_event_optimizer_step_must_match_generation(self):
        source = self.successor()
        source = replace(source, outbox=({**source.outbox[0],
            "optimizer_step": source.retained_state.optimizer_step + 999},))
        self.publish(source, acceptance=self.binding(source))
        with self.assertRaises(BilqisError):
            materialize_native_projection(self.run)

    def test_divergent_duplicate_rejection_event_is_rejected(self):
        parent = self.parent()
        record_bamf_rejection(self.run, parent, self.rejection_evidence(parent))
        ledger = self.run / "events.jsonl"
        row = json.loads(ledger.read_text(encoding="utf-8").splitlines()[-1])
        divergent = {**row, "evidence": {**row["evidence"], "capability": "A.DRIFT"}}
        with ledger.open("a", encoding="utf-8") as stream:
            stream.write(json.dumps(divergent, sort_keys=True) + "\n")
        with self.assertRaises(BilqisError):
            materialize_native_projection(self.run, include_live_rejections=True)

    def test_forged_rejection_pair_cannot_become_live_authority(self):
        parent = self.parent()
        evidence = self.rejection_evidence(parent)
        authority = {
            "schema": "bilqis.mlx.bamf-rejection-authority/v1",
            "run_id": parent.run_id,
            "generation": parent.generation,
            "student_manifest_sha256": self._parent_pointer["manifest_sha256"],
            "optimizer_step": parent.retained_state.optimizer_step,
            "evidence": evidence,
        }
        payload = {
            "event": "BAMF_CANDIDATE_REJECTED",
            "generation": parent.generation,
            "student_manifest_sha256": self._parent_pointer["manifest_sha256"],
            "optimizer_step": parent.retained_state.optimizer_step,
            "evidence": evidence,
            "rejection_authority_sha256": sha(canonical(authority)),
        }
        forged = checkpoint_outbox.with_delivery_outbox(
            {"run_id": parent.run_id, "generation": parent.generation},
            (payload,),
        )["delivery_outbox"][0]
        with (self.run / "events.jsonl").open("a", encoding="utf-8") as stream:
            stream.write(json.dumps(forged, sort_keys=True) + "\n")

        portable = materialize_native_projection(self.run)
        self.assertFalse(any(
            isinstance(record, CandidateDecision) and record.outcome.value == "REJECTED"
            for record in portable.records))
        with self.assertRaises(BilqisError) as caught:
            materialize_native_projection(self.run, include_live_rejections=True)
        self.assertEqual(
            caught.exception.context.get("reason"),
            "CONTROL_PLANE_NATIVE_REJECTION_AUTHORITY_DRIFT",
        )

    def test_generic_rejection_is_authenticated_but_not_projected(self):
        parent = self.parent()
        record_bamf_rejection(self.run, parent, {"reason": "retention_gate"})
        material = materialize_native_projection(
            self.run, include_live_rejections=True)
        self.assertFalse(any(isinstance(record, CandidateDecision)
                             and record.outcome.value == "REJECTED"
                             for record in material.records))

    def test_c16_rejection_requires_source_retention_decision(self):
        parent = self.parent()
        evidence = self.rejection_evidence(
            parent, retention_reason="CLAIMED_REJECT", decision={"decision": "ACCEPT"})
        record_bamf_rejection(self.run, parent, evidence)
        with self.assertRaises(BilqisError):
            materialize_native_projection(self.run, include_live_rejections=True)

    def test_c16_rejection_requires_selected_option(self):
        parent = self.parent()
        record_bamf_rejection(
            self.run, parent, self.rejection_evidence(parent, selected_option_id=""))
        with self.assertRaises(BilqisError):
            materialize_native_projection(self.run, include_live_rejections=True)

    def test_whole_history_pointer_race_is_retried(self):
        self.parent()
        service = ControlPlaneService(self.run, self.root / "race.sock")
        def race(_run_dir, **_kwargs):
            ErrorBus.raise_(SCHOOL.BAMF_CONTROL_PLANE.INVALID,
                            reason="CONTROL_PLANE_NATIVE_HISTORY_POINTER_CHANGED")
        with patch("bilqis_mlx.control_plane.native_source.materialize_native_projection",
                   side_effect=race):
            self.assertEqual(refresh_native_events(service), ())

    def test_history_to_rejection_scan_pointer_advance_fails_transiently(self):
        self.parent()
        def advance(_run_dir, _history):
            self.publish_successor()
            return (), ()
        with patch("bilqis_mlx.control_plane.native_source.rejection_material",
                   side_effect=advance):
            with self.assertRaises(BilqisError) as caught:
                materialize_native_projection(
                    self.run, include_live_rejections=True)
        self.assertEqual(caught.exception.context.get("reason"),
                         "CONTROL_PLANE_NATIVE_HISTORY_POINTER_CHANGED")


if __name__ == "__main__":
    unittest.main()
