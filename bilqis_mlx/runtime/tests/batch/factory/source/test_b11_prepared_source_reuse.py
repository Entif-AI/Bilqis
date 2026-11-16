"""#1273 B11 consumes prepared source proofs instead of replaying cold owners."""
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import pytest

from bilqis_mlx.errors import BilqisError
from bilqis_mlx.runtime.b11_source_execution_authority import (
    _require_prepared_b11_source_proof,
    bind_b11_source_execution_authority,
    require_b11_source_execution_authority_current,
)
from bilqis_mlx.runtime.b11_source_execution_binding import (
    bind_prepared_motif_context, bind_prepared_source_handoff,
)
from bilqis_mlx.semantics.context_eligibility import SourceFrontier, TaskScope


def test_prepared_source_handoff_never_enters_cold_replay_builder():
    handoff = SimpleNamespace(embedding_ready=True)
    source = SimpleNamespace(
        selection="selection", source_row={"id": "row"}, graph={},
        source_root=Path("."))
    with patch(
            "bilqis_mlx.runtime.b11_source_execution_binding."
            "_build_source_atom_handoff_from_snapshot",
            side_effect=AssertionError("cold source replay")) as cold, patch(
                "bilqis_mlx.runtime.b11_source_execution_binding."
                "_build_source_atom_handoff_from_witness",
                return_value=handoff) as prepared:
        actual = bind_prepared_source_handoff(
            "compiled", "config", source, "snapshot", "witness")
    assert actual is handoff
    cold.assert_not_called()
    prepared.assert_called_once()


def test_prepared_motif_context_never_enters_public_formal_replay():
    task = TaskScope(
        "p", "t", "TRAINING", "a" * 64, "j", "s", 0, 0, 2)
    config = SimpleNamespace(task=task, frontier="frontier", policy="policy")
    compiled = SimpleNamespace(visible_end=2)
    source = SimpleNamespace(
        selection="selection", source_root=Path("."), graph={})
    result = ("projection", ("motif",), "issued-frontier")
    with patch(
            "bilqis_mlx.runtime.b11_source_execution_binding."
            "qualify_source_motif_context",
            side_effect=AssertionError("cold motif replay")) as cold, patch(
                "bilqis_mlx.runtime.b11_source_execution_binding."
                "qualify_prepared_source_motif_context",
                return_value=result) as prepared:
        actual = bind_prepared_motif_context(
            compiled, config, source, "adapter", "snapshot",
            "projection", "prepared-frontier")
    assert actual == (task, *result)
    cold.assert_not_called()
    prepared.assert_called_once()


def test_prepared_b11_authority_rejects_current_schema_rights_drift():
    authority = SimpleNamespace(motif_frontier=SourceFrontier(1, 1, ()))
    source = SimpleNamespace(selection="selection")
    with patch(
            "bilqis_mlx.runtime.b11_source_execution_authority."
            "require_b11_source_execution_authority",
            return_value=authority), patch(
                "bilqis_mlx.semantics.frame_adapters.public_formal_schema_rights."
                "issue_source_schema_rights_authority",
                return_value=SimpleNamespace(
                    rights_epoch=2, correction_generation=1)):
        with pytest.raises(BilqisError):
            require_b11_source_execution_authority_current(
                authority, "compiled", "config", source)


def test_caller_cannot_select_prepared_mode_on_public_b11_binder():
    with pytest.raises(TypeError):
        bind_b11_source_execution_authority(
            None, None, None, None, None, None,
            source_witness="caller", motif_projection="caller",
            motif_frontier="caller")


def test_caller_minted_prepared_artifacts_are_not_a_sealed_proof():
    with pytest.raises(BilqisError):
        _require_prepared_b11_source_proof(
            SimpleNamespace(
                source_witness="caller", motif_projection="caller",
                motif_frontier="caller"),
            SimpleNamespace(source_row={}), SimpleNamespace())
