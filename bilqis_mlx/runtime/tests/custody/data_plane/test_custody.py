from .base import DataPlaneCase
from bilqis_mlx.data_plane import dedupe_bundle_payloads, referenced_custody_files

class DataPlaneCustodyTests(DataPlaneCase):
    def test_custody_file_discovery_is_bounded_to_bundle_and_soup_payloads(self):
        receipt = {
            "school": {"current_student": {
                "filename": "bundles/working-1", "sha256": "a" * 64}},
            "mentor_epoch": {"active_grade_soups": {"C": {
                "filename": "soups/C-current.safetensors", "sha256": "b" * 64,
                "previous": {"filename": "soups/C-previous.safetensors",
                             "sha256": "d" * 64}}}},
            "championship_epoch_history": [{"active_grade_soups": {"C": {
                "filename": "soups/C-archived.safetensors", "sha256": "e" * 64}}}],
            "unrelated": {"filename": "cohorts/x.json", "sha256": "c" * 64},
        }
        found = referenced_custody_files(self.root, receipt)
        self.assertEqual(found, (
            ((self.root / "bundles/working-1/model-and-own-adamw.safetensors").resolve(),
             "a" * 64),
            ((self.root / "soups/C-current.safetensors").resolve(), "b" * 64),
            ((self.root / "soups/C-previous.safetensors").resolve(), "d" * 64),
        ))

    def test_bundle_deduper_preserves_alias_paths_and_shares_identical_payload(self):
        import hashlib
        import json
        bundles = self.root / "bundles"
        payload = b"same-model-and-adamw" * 100
        digest = hashlib.sha256(payload).hexdigest()
        paths = []
        for name in ("best-one", "best-two"):
            folder = bundles / name
            folder.mkdir(parents=True)
            blob = folder / "model-and-own-adamw.safetensors"
            blob.write_bytes(payload)
            (folder / "manifest.json").write_text(json.dumps({
                "safetensors_sha256": digest, "optimizer_step": 17,
            }))
            paths.append(blob)

        result = dedupe_bundle_payloads(self.root)

        self.assertEqual(result["linked_aliases"], 1)
        self.assertEqual(result["reclaimed_bytes"], len(payload))
        self.assertEqual(paths[0].read_bytes(), payload)
        self.assertEqual(paths[1].read_bytes(), payload)
        self.assertEqual(paths[0].stat().st_ino, paths[1].stat().st_ino)
        self.assertEqual(dedupe_bundle_payloads(self.root)["linked_aliases"], 0)
