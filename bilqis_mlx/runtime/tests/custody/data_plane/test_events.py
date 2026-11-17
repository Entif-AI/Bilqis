from .base import DataPlaneCase
from bilqis_mlx.data_plane import data_plane, event_observations, event_payload_digest, sync_event_ledger

class DataPlaneEventTests(DataPlaneCase):
    def test_event_index_incrementally_tracks_tail_and_duplicate_counts(self):
        import json
        first = {"event": "FIRST", "event_id": "a" * 64, "value": 1}
        second = {"event": "SECOND", "event_id": "b" * 64, "value": 2}
        ledger = self.root / "events.jsonl"
        ledger.write_text(json.dumps(first, sort_keys=True) + "\n")

        initial = sync_event_ledger(self.root)
        first_size = ledger.stat().st_size
        self.assertEqual(initial["scanned_bytes"], first_size)
        self.assertEqual(initial["indexed_bytes"], first_size)
        self.assertEqual(event_observations(
            self.root, (first["event_id"],))[first["event_id"]],
            (event_payload_digest(first), 1, False))

        with ledger.open("a") as stream:
            stream.write(json.dumps(second, sort_keys=True) + "\n")
        updated = sync_event_ledger(self.root)
        self.assertEqual(updated["scanned_bytes"], ledger.stat().st_size - first_size)
        observations = event_observations(
            self.root, (first["event_id"], second["event_id"]))
        self.assertEqual(observations[second["event_id"]],
                         (event_payload_digest(second), 1, False))

        with ledger.open("a") as stream:
            stream.write(json.dumps(first, sort_keys=True) + "\n")
        duplicate = event_observations(self.root, (first["event_id"],))
        self.assertEqual(duplicate[first["event_id"]],
                         (event_payload_digest(first), 2, False))

    def test_event_index_marks_conflicting_duplicate_payload(self):
        import json
        first = {"event": "FIRST", "event_id": "c" * 64, "value": 1}
        changed = {**first, "value": 99}
        ledger = self.root / "events.jsonl"
        ledger.write_text(
            json.dumps(first, sort_keys=True) + "\n" +
            json.dumps(changed, sort_keys=True) + "\n")

        observation = event_observations(self.root, (first["event_id"],))

        self.assertEqual(observation[first["event_id"]][1:], (2, True))

    def test_indexed_event_tail_replays_from_persistent_byte_frontier(self):
        import json
        first = {"event": "FIRST", "event_id": "d" * 64, "grade": "Q"}
        second = {"event": "SECOND", "event_id": "e" * 64, "grade": "Z"}
        ledger = self.root / "events.jsonl"
        ledger.write_text(json.dumps(first, sort_keys=True) + "\n")

        plane = data_plane()
        initial = plane.indexed_event_tail(self.root)
        frontier = initial["indexed_bytes"]
        self.assertEqual(initial["events"], (first,))

        with ledger.open("a") as stream:
            stream.write(json.dumps(second, sort_keys=True) + "\n")
        resumed = plane.indexed_event_tail(self.root, frontier)

        self.assertFalse(resumed["rebuilt"])
        self.assertEqual(resumed["events"], (second,))
        self.assertEqual(resumed["scanned_bytes"], ledger.stat().st_size - frontier)

    def test_event_projection_state_is_bound_to_current_indexed_ledger(self):
        import json
        event = {"event": "FIRST", "event_id": "f" * 64, "value": 1}
        ledger = self.root / "events.jsonl"
        ledger.write_text(json.dumps(event, sort_keys=True) + "\n")
        plane = data_plane()
        indexed = plane.indexed_event_tail(self.root)

        plane.remember_event_projection(
            self.root, "consumer", "v1", indexed["ledger_identity"],
            indexed["indexed_bytes"], {"count": 1})
        state = plane.event_projection_state(self.root, "consumer", "v1")

        self.assertEqual(state["indexed_bytes"], indexed["indexed_bytes"])
        self.assertEqual(state["payload"], {"count": 1})

        ledger.write_text(json.dumps({**event, "value": 2}, sort_keys=True) + "\n")
        rebuilt = plane.indexed_event_tail(self.root)
        self.assertTrue(rebuilt["rebuilt"])
        self.assertIsNone(plane.event_projection_state(self.root, "consumer", "v1"))
