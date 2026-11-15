"""Current observed trainer snapshots and bounded CP04 revision delivery."""
from .source import observed_records
from ..event_stream import EventFamily


def publish_observed_events(service, records):
    seen = getattr(service, '_trainer_observed_revisions', {})
    published = []
    for record in records:
        identity = (record.revision, record.connection_state)
        if seen.get(record.observation_id) == identity:
            continue
        event = service.publish_event(
            EventFamily.RUN_TRAINER_OBSERVED, record,
            event_id=record.meta.record_id,
        )
        if event is not None:
            published.append(event)
        seen[record.observation_id] = identity
    retained = {record.observation_id for record in records}
    service._trainer_observed_revisions = {
        key: value for key, value in seen.items() if key in retained}
    return tuple(published)


__all__ = ('observed_records', 'publish_observed_events')
