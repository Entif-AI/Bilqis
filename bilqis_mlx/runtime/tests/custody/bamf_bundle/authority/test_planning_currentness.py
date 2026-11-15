"""B13/C09 process-live currentness witnesses for priority planning."""
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import pytest

from bilqis_mlx.errors import BilqisError
from bilqis_mlx.runtime.bamf_bundle import bundle_currentness
from bilqis_mlx.runtime.bamf_bundle.source_authority_custody import currentness


class _Plane:
    def __init__(self):
        self.calls = []
        self.fail_node = False

    def get_node(self, digest):
        self.calls.append(("node", digest))
        if self.fail_node:
            raise ValueError("missing")
        return b"node"

    def get_object(self, digest):
        self.calls.append(("object", digest))
        return b"object"

    def require_file_object(self, digest):
        self.calls.append(("file", digest))
        return Path("/cas") / digest


def test_bundle_witness_rechecks_tree_and_external_dataplane_custody(tmp_path):
    root = tmp_path / "bundle"
    root.mkdir()
    (root / "manifest.json").write_text("{}", encoding="utf-8")
    sidecars = ("a" * 64, "b" * 64)
    tensor = "c" * 64
    manifest = {
        "sidecars": {
            "one": {"object_sha256": sidecars[0]},
            "two": {"object_sha256": sidecars[1]},
        },
        "tensors": {"object_sha256": tensor},
    }
    plane = _Plane()
    with patch.object(
            bundle_currentness, "validate_bamf_bundle_custody",
            return_value=manifest), patch.object(
                bundle_currentness, "data_plane", return_value=plane):
        witness = bundle_currentness.bind_bamf_bundle_currentness(
            root, expected_manifest_sha256="d" * 64)
        plane.calls.clear()
        assert bundle_currentness.require_bamf_bundle_currentness(witness) is witness
        assert plane.calls == [
            ("node", "d" * 64),
            ("object", sidecars[0]),
            ("object", sidecars[1]),
            ("file", tensor),
        ]

        plane.fail_node = True
        with pytest.raises(BilqisError):
            bundle_currentness.require_bamf_bundle_currentness(witness)

        plane.fail_node = False
        (root / "manifest.json").write_text("changed", encoding="utf-8")
        with pytest.raises(BilqisError):
            bundle_currentness.require_bamf_bundle_currentness(witness)


def test_source_authority_witness_resolves_once_and_rejects_live_root_drift(tmp_path):
    registry = SimpleNamespace(digest="e" * 64)
    frontier = {"source_authority_registry": {}, "source_authority_registry_sha256": "e" * 64}
    stable = ("PROVISIONED", 1, 2, 3, 4, 5)
    changed = ("PROVISIONED", 1, 2, 3, 4, 6)
    with patch.object(currentness, "_trust_root_snapshot", return_value=stable), patch.object(
            currentness, "resolve_source_authority_registry", return_value=registry) as resolve:
        witness = currentness.bind_source_authority_currentness(
            tmp_path, frontier, registry)
        assert currentness.require_source_authority_currentness(
            witness, tmp_path, frontier, registry) is registry
        assert currentness.require_source_authority_currentness(
            witness, tmp_path, frontier, registry) is registry
        assert resolve.call_count == 1

    with patch.object(currentness, "_trust_root_snapshot", return_value=changed):
        with pytest.raises(BilqisError):
            currentness.require_source_authority_currentness(
                witness, tmp_path, frontier, registry)


def test_currentness_witnesses_are_owner_only():
    with pytest.raises(BilqisError):
        bundle_currentness.BamfBundleCurrentness()
    with pytest.raises(BilqisError):
        currentness.SourceAuthorityCurrentness()
