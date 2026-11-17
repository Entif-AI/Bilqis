"""A01-backed proof that Factory enrichment joins one truthful C02 delivery."""
from unittest.mock import patch

from bilqis_mlx.factory.teaching import describe_delivered_teaching
import bilqis_mlx.runtime.source_batch_authority as source_batch_authority
from bilqis_mlx.runtime.factory_training_bridge import prepare_factory_training_batch
from bilqis_mlx.runtime.tests.batch.training.visit_provenance_support import (
    visit_provenance,
)

from .factory_training_bridge_support import FactoryTrainingBridgeFixture


class FactoryTrainingEnrichmentTests(FactoryTrainingBridgeFixture):
    def test_source_valid_enrichment_joins_base_option_without_relabeling_it(self):
        capability, seed = "A.IDENTITY", 37131
        direct = tuple(self.context.draw_rows(seed=seed, capability=capability, each=2))
        expanded = tuple(self.context.draw_rows(seed=seed, capability=capability, each=4))
        self.assertEqual(expanded[:2], direct)
        extra = (expanded[2],)
        delivered = (*direct, *extra)
        execution = self.context.release.execution_plan.capability_map[capability]
        teaching = describe_delivered_teaching(
            self.context.release, capability, execution.teaching_option_ids[0], direct)

        with patch.object(source_batch_authority, "optional_teaching_rows", return_value=extra):
            prepared = prepare_factory_training_batch(
                self.context, self.candidate, str(self.artifact),
                self.feature_receipt.path, delivered, self.generation,
                capability=capability, delivery=teaching, requested_count=3,
                source_seed=seed, source_each=3, optimizer_step_seed=7,
                visit_provenance=visit_provenance(capability),
                teacher_strategy={"policy": "enrichment-conformance"})

        self.assertEqual(
            tuple(row.provenance.row_id for row in prepared.training_batch.rows),
            tuple(row["id"] for row in delivered))
        self.assertEqual(teaching.specimen_ids, tuple(row["id"] for row in direct))
        self.assertEqual(len(prepared.compiled_rows), 3)
