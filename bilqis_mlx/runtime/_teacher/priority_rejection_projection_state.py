"""Durable codec for the hot BAMF rejection projection."""
from __future__ import annotations

SCHEMA = "bilqis.mlx.bamf-priority-rejection-projection/v1"
REJECTION_ROW_FIELDS = 4


def encode(projection) -> dict:
    return {
        "schema": SCHEMA,
        "rows": [list(row) for row in projection.rows],
        "weakness_rows": list(projection.weakness_rows),
        "seen_receipts": sorted(projection.seen_receipts),
        "capability_counts": dict(projection.capability_counts),
        "reason_counts": {
            capability: dict(reasons)
            for capability, reasons in projection.reason_counts.items()
        },
        "consecutive_interference": dict(projection.consecutive_interference),
        "last_positions": dict(projection.last_positions),
        "legacy_capabilities": sorted(projection.legacy_capabilities),
        "global_order_started": projection.global_order_started,
        "global_order_start": projection.global_order_start,
    }


def restore(projection, record: dict) -> bool:
    try:
        if record.get("schema") != SCHEMA:
            return False
        rows = [tuple(row) for row in record["rows"]]
        weakness_rows = list(record.get("weakness_rows", ()))
        if any(len(row) != REJECTION_ROW_FIELDS
               or any(not isinstance(value, str) for value in row)
               for row in rows) or any(not isinstance(row, dict) for row in weakness_rows):
            return False
        seen = set(record["seen_receipts"])
        capabilities = dict(record["capability_counts"])
        reasons = {
            str(capability): dict(values)
            for capability, values in record["reason_counts"].items()
        }
        interference = dict(record["consecutive_interference"])
        positions = dict(record["last_positions"])
        legacy = set(record["legacy_capabilities"])
        started = record["global_order_started"]
        start = record["global_order_start"]
        if (not all(isinstance(value, str) for value in seen | legacy)
                or type(started) is not bool
                or (start is not None and type(start) is not int)):
            return False
    except (AttributeError, KeyError, TypeError, ValueError):
        return False
    projection.rows[:] = rows
    projection.weakness_rows[:] = weakness_rows
    projection.seen_receipts.clear()
    projection.seen_receipts.update(seen)
    projection.capability_counts.clear()
    projection.capability_counts.update(capabilities)
    projection.reason_counts.clear()
    projection.reason_counts.update(reasons)
    projection.consecutive_interference.clear()
    projection.consecutive_interference.update(interference)
    projection.last_positions.clear()
    projection.last_positions.update(positions)
    projection.legacy_capabilities.clear()
    projection.legacy_capabilities.update(legacy)
    projection.global_order_started = started
    projection.global_order_start = start
    return True


__all__ = ("SCHEMA", "encode", "restore")
