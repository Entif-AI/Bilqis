"""Shared issue #1168 compiled-evaluation fixtures."""
from types import SimpleNamespace

from bilqis_mlx.curriculum import AnswerFamily, BINARY
from bilqis_mlx.runtime.factory_compiled_cohort import (
    compiled_case_identity_digest, compiled_case_identity_record,
    compiled_frame_identity_digest,
)
from bilqis_mlx.runtime.factory_evaluation_compiler import CompiledFactoryEvaluationCase
from bilqis_mlx.runtime.factory_task_template import FactoryTaskTemplate
from bilqis_mlx.semantics.domains import contract_digest
from bilqis_mlx.semantics.frame_compiler import (
    compile_prefix_rows, validate_partial_visible_forest,
)
from bilqis_mlx.semantics.tests.test_frame_compiler import RELEASE, _mixed_case
from bilqis_mlx.source_adapters.answer_choice_task_goal import (
    lower_answer_choice_task_goal,
)


def case_record():
    return compiled_case_identity_record(
        factory_release_sha256="a" * 64,
        semantic_catalog_sha256="b" * 64,
        semantic_release_sha256="c" * 64,
        source_artifact_sha256="d" * 64,
        source_row_id="row-1",
        source_row_sha256="e" * 64,
        source_binding_sha256="f" * 64,
        lowerer_sha256="1" * 64,
        evaluator_policy_sha256="2" * 64,
        compiler_sha256="3" * 64,
        feature_schema_sha256="6" * 64,
        compiled_frame_sha256="4" * 64,
        goal_sha256="5" * 64,
        source_family_id="family-1",
        episode_id="episode-1",
    )


def compiled_case():
    ast, config = _mixed_case()
    rows = compile_prefix_rows(((ast, 4, config),), RELEASE)
    receipt = validate_partial_visible_forest(rows.rows[0], ast, config)
    capability = SimpleNamespace(
        capability_id="A.IDENTITY",
        answer_families=(AnswerFamily("binary", BINARY),))
    source = {
        "id": "row-1", "capability": "A.IDENTITY", "tokens": [1],
        "source_id": "source:cache-fixture",
    }
    goal, binding = lower_answer_choice_task_goal(
        source, semantic_release=RELEASE, capability=capability)
    template = FactoryTaskTemplate(
        goal, binding, "a" * 64, "A.IDENTITY", "row-1", "e" * 64,
        contract_digest(binding), "family-1", "episode-1", "1" * 64)
    record = compiled_case_identity_record(
        factory_release_sha256="a" * 64,
        semantic_catalog_sha256="b" * 64,
        semantic_release_sha256=RELEASE,
        source_artifact_sha256="d" * 64,
        source_row_id=template.source_row_id,
        source_row_sha256=template.source_row_sha256,
        source_binding_sha256=template.source_binding_sha256,
        lowerer_sha256=template.lowerer_sha256,
        evaluator_policy_sha256=contract_digest((
            config.task, config.frontier, config.policy)),
        compiler_sha256="3" * 64,
        feature_schema_sha256="6" * 64,
        compiled_frame_sha256=compiled_frame_identity_digest(rows),
        goal_sha256=contract_digest(goal),
        source_family_id=template.source_family_id,
        episode_id=template.episode_id,
    )
    items = tuple((key, value) for key, value in record.items() if key != "schema")
    return CompiledFactoryEvaluationCase(
        rows, (config,), (ast,), (receipt,), template, items,
        compiled_case_identity_digest(record))


__all__ = ("case_record", "compiled_case")
