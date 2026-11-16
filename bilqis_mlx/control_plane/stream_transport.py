"""CP04 streaming loop kept off the publisher and CP01 transport paths."""
from __future__ import annotations

from bilqis_mlx.mission_control.codec import encode_record
from bilqis_mlx.mission_control.model import is_sha256

from .event_stream import EVENT_GAP_SCHEMA


def serve_event_subscription(service, session, request: dict, write_record) -> None:
    from .native_source import refresh_native_events

    after_cursor = request.get("after_cursor")
    if after_cursor is not None and not is_sha256(after_cursor):
        write_record(service.rejected_request(
            session, "CONTROL_PLANE_EVENT_CURSOR_INVALID"))
        return
    refresh_native_events(service)
    opened = service.events.open_subscription(after_cursor)
    write_record({
        **opened.acknowledgement,
        "service": service.identity.to_record(),
        "session": session.to_record(),
    })
    subscription = opened.subscription
    if subscription is None:
        return
    try:
        for event in opened.replay:
            write_record(encode_record(event))
        while True:
            refresh_native_events(service)
            record = subscription.next_record(service.event_heartbeat_seconds)
            if record is None:
                record = service.events.heartbeat_record()
            write_record(record)
            if record.get("schema") == EVENT_GAP_SCHEMA:
                return
    except (BrokenPipeError, ConnectionResetError, OSError):
        return
    finally:
        subscription.close()
