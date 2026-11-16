"""CP03 query dispatch over the accepted CP01 local transport."""
from __future__ import annotations

import json

from bilqis_mlx.mission_control import (
    MissionControlContractError, MissionControlQueryCatalog, QueryRequest,
)


MAX_RESPONSE_BYTES = 64 * 1024


def serve_query(service, session, request: dict) -> dict:
    """Serve one bounded read-only CP03 query without owning query truth."""
    try:
        query = QueryRequest.from_mapping(request.get("query"))
    except MissionControlContractError:
        return service.rejected_request(session, "CONTROL_PLANE_QUERY_INVALID")
    try:
        catalog = service._query_source()
    except Exception:
        return service.rejected_request(
            session, "CONTROL_PLANE_QUERY_SOURCE_UNAVAILABLE")
    if not isinstance(catalog, MissionControlQueryCatalog):
        return service.rejected_request(
            session, "CONTROL_PLANE_QUERY_SOURCE_INVALID")
    try:
        page = catalog.query(query)
    except MissionControlContractError as error:
        reason = (
            "CONTROL_PLANE_QUERY_RESPONSE_TOO_LARGE"
            if error.detail == "QUERY_ROW_TOO_LARGE"
            else "CONTROL_PLANE_QUERY_INVALID"
        )
        return service.rejected_request(session, reason)
    response = {
        **catalog.encode_page(page),
        "accepted": True,
        "service": service.identity.to_record(),
        "session": session.to_record(),
    }
    encoded = json.dumps(
        response, separators=(",", ":"), sort_keys=True).encode("utf-8") + b"\n"
    if len(encoded) > MAX_RESPONSE_BYTES:
        return service.rejected_request(
            session, "CONTROL_PLANE_QUERY_RESPONSE_TOO_LARGE")
    return response
