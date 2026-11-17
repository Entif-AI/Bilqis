"""#1320 successor synthesis must bind exact predecessor certification."""
import hashlib
from dataclasses import replace

import pytest

from bilqis_mlx.factory.atlas_frontier_contracts import _bytes
from bilqis_mlx.factory.generated_grade import synthesize_generated_grade
from bilqis_mlx.factory.generated_grade.contracts import _issue_inputs
from bilqis_mlx.factory.generated_grade.definition import (
    GENERATED_GRADE_DEFINITION_V2,
    _seal_generated_grade,
)
from bilqis_mlx.factory.generated_grade.proposal_contracts import (
    GENERATED_GRADE_INPUTS_V2,
    GENERATED_GRADE_PROPOSAL_V2,
    GeneratedGradeProposal,
)
from bilqis_mlx.factory.tests.curriculum.generated_grade.fixtures import (
    _fixture,
    _inputs,
)
from bilqis_mlx.factory.tests.curriculum.generated_grade.test_definition import (
    _single_member_fixture,
)


def _certified_inputs(learner, evidence, policy, certification_sha256):
    values = dict(
        learner=learner,
        candidate_evidence=evidence,
        policy=policy,
        a09_progress_sha256="1" * 64,
        a09_status="PROPOSAL",
        a09_handoff_sha256="2" * 64,
        a09_proposal_sha256="3" * 64,
        predecessor_certification_sha256=certification_sha256,
        schema=GENERATED_GRADE_INPUTS_V2,
    )
    digest = hashlib.sha256(_bytes(values)).hexdigest()
    return _issue_inputs(**values, input_sha256=digest)


def test_certified_successor_binds_receipt_through_proposal_and_definition():
    snapshot, closure, release, evidence, policy, learner = _fixture()
    certification = "c" * 64
    inputs = _certified_inputs(learner, evidence, policy, certification)
    proposal = synthesize_generated_grade(
        snapshot, closure, release, inputs)

    assert proposal.schema == GENERATED_GRADE_PROPOSAL_V2
    assert proposal.predecessor_certification_sha256 == certification
    assert GeneratedGradeProposal.from_manifest(proposal.manifest()) == proposal

    exact_release, v1_proposal = _single_member_fixture(
        exact_release_semantic := release.semantic_catalog[0],
        next(iter(release.curriculum.capability_map)),
    )
    certified = replace(
        v1_proposal,
        predecessor_certification_sha256=certification,
        schema=GENERATED_GRADE_PROPOSAL_V2,
        proposal_sha256="0" * 64,
    )
    certified = replace(
        certified, proposal_sha256=certified.expected_digest())
    definition = _seal_generated_grade(
        certified, exact_release, release_lineage=(exact_release,))
    assert exact_release_semantic in definition.member_semantic_ids
    assert definition.schema == GENERATED_GRADE_DEFINITION_V2
    assert definition.predecessor_certification_sha256 == certification


def test_historical_v1_proposal_bytes_remain_certification_field_free():
    snapshot, closure, release, evidence, policy, learner = _fixture()
    proposal = synthesize_generated_grade(
        snapshot, closure, release, _inputs(learner, evidence, policy))
    assert proposal.schema == "bilqis.generated-grade-proposal/v1"
    assert proposal.predecessor_certification_sha256 is None
    assert "predecessor_certification_sha256" not in proposal.manifest()


def test_v1_parser_rejects_noncanonical_certification_or_unknown_fields():
    snapshot, closure, release, evidence, policy, learner = _fixture()
    proposal = synthesize_generated_grade(
        snapshot, closure, release, _inputs(learner, evidence, policy))
    polluted = {
        **proposal.manifest(),
        "predecessor_certification_sha256": "f" * 64,
    }
    with pytest.raises(Exception):
        GeneratedGradeProposal.from_manifest(polluted)
    with pytest.raises(Exception):
        GeneratedGradeProposal.from_manifest({
            **proposal.manifest(),
            "unexpected_authority": "opaque",
        })
