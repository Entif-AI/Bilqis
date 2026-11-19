"""#329 public-fixture conformance for structured VieDay activity time logs."""
from dataclasses import replace
import unittest

from bilqis_mlx.errors import BilqisError
from bilqis_mlx.source_adapters.evidence.evidence_types import (
    EvidenceRights,
    PRIVATE_REAL,
    PUBLIC_FIXTURE,
    SourceSpan,
)
from bilqis_mlx.source_adapters.vieday.time_log_contracts import CategoryMapping
from bilqis_mlx.source_adapters.vieday.time_logs import (
    TimeLogSemanticAuthority,
    qualify_public_time_log_source,
)
from bilqis_mlx.source_adapters.vieday.time_log_qualification import _mark_overlaps, _relations


RELEASE = "58e0c281b5da18b9b7e6c803709b29eeeb0a88f16b06f48de692808e2fb88306"
STUDY = (
    "https://github.com/Entif-AI/Bilqis-MLX/id/sense/"
    "NI-LEXICON-CURRICULUM/LEXROOT-3e51e33b4a970f/STEM%203/BSC")
AUTHORITY = TimeLogSemanticAuthority(RELEASE, (CategoryMapping("study", STUDY),))
RIGHTS = EvidenceRights(PUBLIC_FIXTURE, "CONFORMANCE", False, True)


def qualify(source: str, *, release=RELEASE):
    return qualify_public_time_log_source(
        source, rights=RIGHTS, authority=AUTHORITY,
        expected_semantic_release=release)


class VieDayTimeLogTests(unittest.TestCase):
    def test_qualified_row_preserves_source_temporal_and_category_assertions(self):
        source = (
            "interval=09:30-10:00; activity=reading notes; category=study; "
            "status=occurred; duration=0.5 h; aggregate=2 h")
        manifest = qualify(source)
        self.assertEqual(manifest.status, "STRUCTURAL_PASS")
        self.assertEqual(manifest.claim, "PUBLIC_FIXTURE_ONLY_NOT_REAL_PILOT_EVIDENCE")
        self.assertEqual(manifest.publication_class, "PUBLIC_FIXTURE")
        self.assertFalse(manifest.allowed_training)
        self.assertEqual(manifest.semantic_release, RELEASE)
        self.assertEqual(manifest.expected_semantic_release, RELEASE)
        record = manifest.records[0]
        self.assertEqual(record.source_span, SourceSpan(0, len(source)))
        self.assertEqual(source[record.source_span.start:record.source_span.end], source)
        self.assertEqual(record.raw_interval_text, "09:30-10:00")
        self.assertEqual((record.start_time, record.end_time), ("09:30", "10:00"))
        self.assertFalse(record.day_rollover)
        self.assertEqual(record.raw_activity_phrase, "reading notes")
        self.assertEqual(record.raw_category_label, "study")
        self.assertEqual(record.category_ref, STUDY)
        self.assertEqual(record.status, "OCCURRED")
        self.assertEqual(record.reported_duration.decimal, "0.5")
        self.assertEqual(record.calculated_duration_minutes, 30)
        self.assertEqual(record.aggregate_notation.raw_text, "2 h")
        self.assertEqual(record.conflicts, ())

    def test_reported_duration_conflict_stays_visible_and_never_overwrites_source(self):
        manifest = qualify(
            "interval=09:30-10:00; activity=reading; category=study; "
            "status=occurred; duration=1 h")
        record = manifest.records[0]
        self.assertEqual(record.reported_duration.decimal, "1")
        self.assertEqual(record.calculated_duration_minutes, 30)
        self.assertEqual(record.conflicts, ("REPORTED_CALCULATED_DURATION_MISMATCH",))

    def test_explicit_day_rollover_is_required_when_end_clock_moves_backward(self):
        held = qualify(
            "interval=23:30-00:30; activity=late review; category=study; "
            "status=occurred; duration=1 h")
        self.assertEqual(held.status, "HELD")
        self.assertEqual(held.holds[0].reason, "AMBIGUOUS_DAY_ROLLOVER")
        qualified = qualify(
            "interval=23:30-00:30+1d; activity=late review; category=study; "
            "status=occurred; duration=1 h")
        self.assertTrue(qualified.records[0].day_rollover)
        self.assertEqual(qualified.records[0].calculated_duration_minutes, 60)

    def test_cross_midnight_relation_without_next_row_day_context_is_held(self):
        source = "\n".join((
            "interval=23:30-00:30+1d; activity=late review; category=study; status=occurred; duration=1 h",
            "interval=00:45-01:00; activity=early notes; category=study; status=occurred; duration=0.25 h",
        ))
        manifest = qualify(source)
        self.assertEqual(manifest.status, "STRUCTURAL_PARTIAL")
        self.assertEqual(manifest.relations, ())
        self.assertEqual(
            tuple(row.reason for row in manifest.holds),
            ("RELATION_DAY_CONTEXT_AMBIGUOUS",))

    def test_planned_and_occurred_records_remain_distinct(self):
        source = "\n".join((
            "interval=09:00-09:30; activity=planned reading; category=study; status=planned; duration=0.5 h",
            "interval=10:00-10:30; activity=actual reading; category=study; status=occurred; duration=0.5 h",
        ))
        manifest = qualify(source)
        self.assertEqual(tuple(row.status for row in manifest.records), ("PLANNED", "OCCURRED"))
        self.assertEqual(manifest.relations[0].kind, "GAP")
        self.assertEqual(manifest.relations[0].minutes, 30)
        self.assertEqual(
            (manifest.relations[0].left_status, manifest.relations[0].right_status),
            ("PLANNED", "OCCURRED"))

    def test_overlaps_are_relationship_evidence_and_record_conflicts(self):
        source = "\n".join((
            "interval=09:00-10:00; activity=reading; category=study; status=occurred; duration=1 h",
            "interval=09:30-10:30; activity=review; category=study; status=occurred; duration=1 h",
        ))
        manifest = qualify(source)
        self.assertEqual(manifest.relations[0].kind, "OVERLAP")
        self.assertEqual(manifest.relations[0].minutes, 30)
        self.assertTrue(all("INTERVAL_OVERLAP" in row.conflicts for row in manifest.records))

    def test_nonadjacent_overlap_is_not_lost_behind_nested_interval(self):
        source = "\n".join((
            "interval=09:00-12:00; activity=long block; category=study; status=occurred; duration=3 h",
            "interval=10:00-10:30; activity=short block; category=study; status=occurred; duration=0.5 h",
            "interval=11:00-13:00; activity=later block; category=study; status=occurred; duration=2 h",
        ))
        manifest = qualify(source)
        overlaps = {(row.left_record_id, row.right_record_id): row.minutes
                    for row in manifest.relations if row.kind == "OVERLAP"}
        self.assertEqual(overlaps[("time-log-0001", "time-log-0002")], 30)
        self.assertEqual(overlaps[("time-log-0001", "time-log-0003")], 60)

    def test_missing_or_unknown_category_is_held_without_guessing(self):
        missing = qualify(
            "interval=09:00-09:30; activity=reading; status=occurred; duration=0.5 h")
        unknown = qualify(
            "interval=09:00-09:30; activity=reading; category=unknown; "
            "status=occurred; duration=0.5 h")
        self.assertEqual(missing.holds[0].reason, "MISSING_CATEGORY")
        self.assertEqual(unknown.holds[0].reason, "CATEGORY_MAPPING_UNKNOWN")

    def test_stale_semantic_release_holds_every_row(self):
        manifest = qualify(
            "interval=09:00-09:30; activity=reading; category=study; "
            "status=occurred; duration=0.5 h",
            release="b" * 64)
        self.assertEqual(manifest.status, "HELD")
        self.assertEqual(manifest.records, ())
        self.assertEqual(manifest.semantic_release, RELEASE)
        self.assertEqual(manifest.expected_semantic_release, "b" * 64)
        self.assertEqual(manifest.holds[0].reason, "SEMANTIC_RELEASE_STALE")

    def test_unsupported_template_shape_is_held_not_free_form_interpreted(self):
        manifest = qualify("09:00-09:30 read for half an hour")
        self.assertEqual(manifest.status, "HELD")
        self.assertEqual(manifest.holds[0].reason, "MALFORMED_KEY_VALUE_ROW")

    def test_private_real_is_blocked_until_privacy_gate_owns_execution(self):
        rights = EvidenceRights(PRIVATE_REAL, "CONFORMANCE", False, False)
        with self.assertRaises(BilqisError) as caught:
            qualify_public_time_log_source(
                "interval=09:00-09:30; activity=protected; category=study; "
                "status=occurred; duration=0.5 h",
                rights=rights, authority=AUTHORITY, expected_semantic_release=RELEASE)
        self.assertEqual(
            caught.exception.context["reason"],
            "VIEDAY_TIME_LOG_PUBLIC_FIXTURE_REQUIRED")

    def test_public_fixture_cannot_opt_into_training_through_this_stratum(self):
        rights = EvidenceRights(PUBLIC_FIXTURE, "TRAINING", True, True)
        with self.assertRaises(BilqisError) as caught:
            qualify_public_time_log_source(
                "interval=09:00-09:30; activity=reading; category=study; "
                "status=occurred; duration=0.5 h",
                rights=rights, authority=AUTHORITY, expected_semantic_release=RELEASE)
        self.assertEqual(
            caught.exception.context["reason"],
            "VIEDAY_TIME_LOG_PUBLIC_FIXTURE_REQUIRED")

    def test_record_contract_rejects_forged_calculated_duration(self):
        record = qualify(
            "interval=09:00-09:30; activity=reading; category=study; "
            "status=occurred; duration=0.5 h").records[0]
        with self.assertRaises(BilqisError) as caught:
            replace(record, calculated_duration_minutes=31)
        self.assertEqual(
            caught.exception.context["reason"],
            "VIEDAY_TIME_LOG_CALCULATED_DURATION_INVALID")

    def test_manifest_rejects_forged_temporal_relation_magnitude(self):
        source = "\n".join((
            "interval=09:00-09:30; activity=reading; category=study; status=occurred; duration=0.5 h",
            "interval=10:00-10:30; activity=review; category=study; status=occurred; duration=0.5 h",
        ))
        manifest = qualify(source)
        forged = replace(manifest.relations[0], minutes=31)
        with self.assertRaises(BilqisError) as caught:
            replace(manifest, relations=(forged,))
        self.assertEqual(
            caught.exception.context["reason"],
            "VIEDAY_TIME_LOG_RELATION_DERIVATION_INVALID")

    def test_duplicate_source_spans_are_held_by_qualification_contract(self):
        source = "\n".join((
            "interval=09:00-09:30; activity=reading; category=study; status=occurred; duration=0.5 h",
            "interval=10:00-10:30; activity=review; category=study; status=occurred; duration=0.5 h",
        ))
        manifest = qualify(source)
        duplicate = replace(manifest.records[1], source_span=manifest.records[0].source_span)
        relations = _relations((manifest.records[0], duplicate))
        marked = _mark_overlaps((manifest.records[0], duplicate), relations)
        self.assertEqual(marked[0].source_span, marked[1].source_span)
        with self.assertRaises(BilqisError):
            replace(manifest, records=marked)


if __name__ == "__main__":
    unittest.main()
