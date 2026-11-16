"""Read one bind-time-qualified B11 feature row without source replay."""

from bilqis_mlx.errors import ErrorBus, SCHOOL
from bilqis_mlx.learning.frame_embeddings.requests import FeatureRequest


def _invalid():
    ErrorBus.Raise(
        SCHOOL.MODEL_TOPOLOGY.INVALID,
        reason="B11_SOURCE_EXECUTION_FEATURE_AUTHORITY_INVALID")


def require_source_feature_row(authority, request: FeatureRequest):
    from bilqis_mlx.runtime.b11_source_execution_authority import (
        B11SourceExecutionAuthority, _ISSUER,
    )

    if (type(authority) is not B11SourceExecutionAuthority
            or authority._issuance is not _ISSUER
            or type(request) is not FeatureRequest):
        _invalid()
    request.__post_init__()
    if request.projection.digest != authority.motif_projection.digest:
        _invalid()
    matches = tuple(
        row for frame_handle, member_handle, row in authority.motif_feature_rows
        if (frame_handle, member_handle)
        == (request.frame_handle, request.member_handle))
    if len(matches) != 1:
        _invalid()
    row = matches[0]
    if (row.semantic_id != request.concept.semantic_id
            or row.abi_index != request.concept.abi_index
            or row.role_id != request.role_id
            or row.schema_id != request.schema_id
            or row.scope != request.scope):
        _invalid()
    return row
