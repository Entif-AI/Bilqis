"""Portable source-offer serialization and issuance boundaries."""
import pytest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from bilqis_mlx.errors import BilqisError
from bilqis_mlx.runtime.priority_source_offer import (
    PreparedPrioritySourceOffer, _canonical_rows, _decode_rows,
)


def test_rows_are_json_exact_and_decoded_fresh():
    rows = ({'id': 'é', 'values': [1, {'x': True}], 'capability': 'c'},)
    wire = _canonical_rows(rows)
    assert wire == '[{"capability":"c","id":"é","values":[1,{"x":true}]}]'
    first = _decode_rows(wire)
    first[0]['values'][1]['x'] = False
    assert _decode_rows(wire) == rows


@pytest.mark.parametrize('rows', [(), ({'x': float('nan')},), ({'x': (1,)},), ({1: 'x'},), ({'x': '\ud800'},)])
def test_rejects_noncanonical_source_rows(rows):
    with pytest.raises(BilqisError):
        _canonical_rows(rows)


def test_offer_construction_is_owner_only():
    with pytest.raises(BilqisError):
        PreparedPrioritySourceOffer()


def test_offer_rejects_context_without_accepted_host():
    from bilqis_mlx.runtime.priority_source_offer import prepare_priority_source_offer
    from bilqis_mlx.runtime.tests.batch import test_atlas_training_adapter as fixture_module
    fixture = fixture_module.AtlasTrainingAdapterTest()
    fixture.setUp()
    try:
        with pytest.raises(BilqisError) as error:
            prepare_priority_source_offer(fixture.context, None, 'unused', capability='Z.C0',
                                          source_seed=17, source_each=1)
        assert error.value.context['reason'] == 'FACTORY_SOURCE_CORRECTION_RUNTIME_REQUIRED'
    finally:
        fixture.doCleanups()


def test_planning_generation_rejects_acceptance_change_during_binding():
    from bilqis_mlx.runtime import priority_source_offer as offer_module
    from bilqis_mlx.runtime.source_execution import SourceExecutionContext

    pointer = {
        'run_id': 'run', 'generation': 0,
        'manifest_sha256': 'a' * 64, 'acceptance_sha256': 'b' * 64,
    }
    cache = SimpleNamespace(
        run_id='run', generation=0, accepted_manifest_sha256='a' * 64,
        generation_binding='c' * 64,
    )
    parent = SimpleNamespace(run_identity=SimpleNamespace(digest='d' * 64))
    context = object.__new__(SourceExecutionContext)
    object.__setattr__(context, 'run_dir', Path('/run'))
    with patch.object(
            SourceExecutionContext, 'require_accepted_runtime', return_value=None), patch.object(
            offer_module, '_planning_pointer_snapshot',
            side_effect=((pointer, 'e' * 64), (pointer, 'f' * 64))), patch.object(
            offer_module, '_current_cache', return_value=cache), patch(
            'bilqis_mlx.runtime.bamf_bundle.authenticate_bamf_execution_feature_context',
            return_value=object()):
        with pytest.raises(BilqisError) as error:
            offer_module.bind_priority_planning_generation(context, parent, '/atlas')
    assert error.value.context['reason'] == 'BAMF_PRIORITY_PLANNING_GENERATION_INVALID'


@pytest.mark.parametrize('kind', ['SOURCE', 'RIGHTS'])
def test_atom_only_offer_holds_on_exact_row_corrections(kind):
    from dataclasses import replace
    from bilqis_mlx.runtime.atlas_packed_frame_owner import PackedFrameArtifactOwner
    from bilqis_mlx.runtime.atlas_training_adapter import _row_immediate_dependencies
    from bilqis_mlx.runtime.salience_evidence_owner import SalienceEvidenceArtifactOwner
    from bilqis_mlx.runtime.tests.batch import test_atlas_training_adapter as fixture_module
    from bilqis_mlx.runtime.tests.test_atlas_revalidation import AUTHORITY, _event
    from bilqis_mlx.semantics.cognitive_dependencies import DependencyKind
    from bilqis_mlx.semantics.frame_compiler import CompiledFrameRows, _prefix_digest

    fixture = fixture_module.AtlasTrainingAdapterTest()
    fixture.setUp()
    try:
        batch = fixture.compile(fixture.rows)
        row = fixture.rows[0]
        original = batch.rows[0].model_input.prefix
        positions = tuple(position for position in original.positions if position.packed is None)
        key = _prefix_digest(original.source_instance_id, original.semantic_release,
                             original.visible_end, original.schema_map, original.context_digest,
                             positions, original.scope, original.policy_version)
        prefix = replace(original, positions=positions, cache_key=key)
        packed = PackedFrameArtifactOwner(CompiledFrameRows(
            (prefix,), (prefix.positions,), ((True,) * len(prefix.positions),)))
        assert not packed.index.nodes
        authority = fixture.context.bind_rows(fixture.rows, seed=17, capability='Z.C0', each=1)
        owner = SalienceEvidenceArtifactOwner.for_source_offer(authority, tuple(fixture.rows), (prefix,))
        deps = owner.require().immediate_dependencies
        expected = _row_immediate_dependencies(row['id'], row.get('source_id'),
            row['record']['operator'], replace(batch.rows[0].model_input, prefix=prefix))
        assert deps == expected
        assert {DependencyKind.SOURCE, DependencyKind.RIGHTS, DependencyKind.TIME} <= {d.kind for d in deps}
        target = next(d for d in deps if d.kind is DependencyKind(kind))
        if kind == 'SOURCE':
            from bilqis_mlx.runtime.atlas_revalidation import SourceAuthorityRegistry, SourceAuthorityScope
            key = AUTHORITY.keys[0]
            scopes = tuple(sorted((*key.allowed_scopes, SourceAuthorityScope(DependencyKind.SOURCE, 'Z.C0:')),
                                  key=lambda scope: (scope.kind.value, scope.key_prefix)))
            registry = SourceAuthorityRegistry((replace(key, allowed_scopes=scopes),))
        else:
            registry = AUTHORITY
        owner.apply_correction(_event(target), registry)
        with pytest.raises(BilqisError) as error:
            owner.require()
        assert error.value.context['reason'] == 'BAMF_C09_ARTIFACT_HELD'
    finally:
        fixture.doCleanups()


def test_source_offer_evidence_rejects_changed_source_content():
    from bilqis_mlx.runtime.salience_evidence_owner import SalienceEvidenceArtifactOwner
    from bilqis_mlx.runtime.tests.batch import test_atlas_training_adapter as fixture_module
    fixture = fixture_module.AtlasTrainingAdapterTest()
    fixture.setUp()
    try:
        batch = fixture.compile(fixture.rows)
        authority = fixture.context.bind_rows(fixture.rows, seed=17, capability='Z.C0', each=1)
        changed = ({**fixture.rows[0], 'gold': 'TRUE'},)
        with pytest.raises(BilqisError):
            SalienceEvidenceArtifactOwner.for_source_offer(
                authority, changed, (batch.rows[0].model_input.prefix,))
    finally:
        fixture.doCleanups()
