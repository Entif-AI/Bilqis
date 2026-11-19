"""Portable C08 evidence reconstructs exact B11 execution-extended authority."""
import json
import unittest

from bilqis_mlx.runtime.atlas_training_authority import (
    extend_training_dependencies,
)
from bilqis_mlx.runtime.c08_distributed_evidence import (
    DistributedB11Evidence, evidence_training_extension,
    issue_distributed_b11_evidence,
)
from bilqis_mlx.runtime.atlas_model import BamfLossExecution
from bilqis_mlx.runtime.tests.correction.capability_support_owner_support import (
    training_authority,
)
from bilqis_mlx.semantics.cognitive_dependencies import (
    ArtifactKind, ArtifactNode, DependencyKind, DependencyRef,
)


class DistributedTrainingAuthorityTests(unittest.TestCase):
    def test_execution_extension_reconstructs_exact_final_b11_digest(self):
        base = training_authority()
        dependency = DependencyRef(DependencyKind.OPERATOR, "operator:runtime-read")
        node = ArtifactNode(
            "artifact:runtime-read", ArtifactKind.MOTIF, "a" * 64, True,
            (dependency,), 2, 1)
        final = extend_training_dependencies(
            base, (dependency, node.reference), artifact_nodes=(node,))
        artifact_json = json.dumps([{
            "artifact_id": node.artifact_id, "kind": node.kind.value,
            "content_digest": node.content_digest, "eligible": node.eligible,
            "immediate_dependencies": [
                [ref.kind.value, ref.key] for ref in node.immediate_dependencies],
            "impact": node.impact, "exigency": node.exigency,
        }], sort_keys=True, separators=(",", ":"))
        evidence = DistributedB11Evidence(
            "b" * 64, 0, 0, base.source_row_id, base.generation_binding,
            "fixture-run", 1, "c" * 64, ((0, 0),), (), (), (), (), (), (), (),
            (), final.digest,
            tuple((ref.kind.value, ref.key) for ref in final.immediate_dependencies),
            artifact_json)
        dependencies, artifacts = evidence_training_extension(evidence)
        reconstructed = extend_training_dependencies(
            base, dependencies, artifact_nodes=artifacts)
        self.assertEqual(reconstructed.digest, final.digest)
        self.assertEqual(reconstructed.artifact_nodes, final.artifact_nodes)

    def test_issued_evidence_transports_only_execution_extension(self):
        base = training_authority()
        dependency = DependencyRef(DependencyKind.OPERATOR, "operator:runtime-read")
        node = ArtifactNode(
            "artifact:runtime-read", ArtifactKind.MOTIF, "a" * 64, True,
            (dependency,), 2, 1)
        final = extend_training_dependencies(
            base, (dependency, node.reference), artifact_nodes=(node,))
        execution = object.__new__(BamfLossExecution)
        values = {
            "output": type("Output", (), {"generation_binding": base.generation_binding})(),
            "loss": object(),
            "custody_run_id": "fixture-run",
            "custody_generation": 1,
            "custody_manifest_sha256": "c" * 64,
            "visible_identity_rows": ((0, 0),),
            "feedback_identity_rows": (),
            "semantic_denominator_identity_rows": (),
            "feature_rows": (),
            "semantic_denominator_feature_rows": (),
            "role_read_feature_rows": (),
            "local_slot_rows": (),
            "dense_parameter_names": (),
            "motif_reads": (),
            "training_authority": final,
        }
        for name, value in values.items():
            object.__setattr__(execution, name, value)
        with unittest.mock.patch(
                "bilqis_mlx.runtime.c08_distributed_evidence.require_bamf_loss_execution",
                return_value=execution):
            evidence = issue_distributed_b11_evidence(
                execution, manifest_digest="b" * 64, rank=0, row_index=0,
                row_id=base.source_row_id, base_training_authority=base)
        dependencies, artifacts = evidence_training_extension(evidence)
        self.assertEqual(dependencies, tuple(sorted((dependency, node.reference))))
        self.assertEqual(artifacts, (node,))


if __name__ == "__main__":
    unittest.main()
