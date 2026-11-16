"""#1293 accepted resume parent-graph provenance boundary."""
from types import SimpleNamespace
from unittest.mock import patch

import pytest

from bilqis_mlx.errors import BilqisError
from bilqis_mlx.presentation.operator_cli.bamf_lifecycle import (
    _validated_resume_parent_graph,
)
from bilqis_mlx.runtime.state import _fingerprint


def test_resume_parent_graph_must_match_immutable_bamf_foundation_identity():
    graph = {"tokens": ["source"]}
    identity = SimpleNamespace(semantic_graph_sha256="f" * 64)
    args = SimpleNamespace(source_run_dir="/source")
    with patch(
            "bilqis_mlx.presentation.operator_cli.bamf_lifecycle.source_foundation",
            return_value=("/source", "release", graph)):
        with pytest.raises(BilqisError) as raised:
            _validated_resume_parent_graph(args, identity)
    assert raised.value.context["reason"] == "BAMF_OPERATOR_RESUME_SOURCE_GRAPH_CONFLICT"


def test_resume_parent_graph_reuses_the_exact_validated_graph_object():
    graph = {"tokens": ["source"]}
    identity = SimpleNamespace(semantic_graph_sha256=_fingerprint(graph))
    args = SimpleNamespace(source_run_dir="/source")
    with patch(
            "bilqis_mlx.presentation.operator_cli.bamf_lifecycle.source_foundation",
            return_value=("/source", "release", graph)):
        source, release, actual = _validated_resume_parent_graph(args, identity)
    assert (source, release) == ("/source", "release")
    assert actual is graph
