"""CP04 bounded live-event delivery over the accepted CP02 event envelope.

Ordering is ingestion order within one stream/epoch scope. Event timestamps are
evidence carried by CP02 records and are never used to reorder delivery.
Resource telemetry is coalesced before cursor assignment: only the latest
ingested sample in a materialized-time bucket is emitted when that bucket
closes, when a domain event arrives, or when flush_resource_samples is called.
The bucket span uses the same integer units as CP02 materialized_at and is
explicitly configurable by the service owner.
"""
from __future__ import annotations

from collections import deque
from dataclasses import dataclass, replace
from enum import StrEnum
import hashlib
import json
from threading import Condition, Lock
from typing import NamedTuple
from uuid import uuid4

from bilqis_mlx.errors import ErrorBus, SCHOOL
from bilqis_mlx.mission_control.codec import canonical_json, encode_record
from bilqis_mlx.mission_control.envelopes import (
    EventEnvelope, StreamPosition, event_cursor_sha256,
)
from bilqis_mlx.mission_control.model import RecordMeta, WireRecord


EVENT_SUBSCRIPTION_SCHEMA = "bilqis.bamf.control-plane.event-subscription/v1"
EVENT_FRONTIER_SCHEMA = "bilqis.bamf.control-plane.event-frontier/v1"
EVENT_GAP_SCHEMA = "bilqis.bamf.control-plane.event-gap/v1"
EVENT_HEARTBEAT_SCHEMA = "bilqis.bamf.control-plane.event-heartbeat/v1"


def _invalid(reason: str):
    ErrorBus.raise_(SCHOOL.BAMF_CONTROL_PLANE.INVALID, reason=reason)


class EventFamily(StrEnum):
    RUN_STATE_CHANGED = "run.state.changed"
    RUN_TRAINER_OBSERVED = "run.trainer.observed"
    LESSON_VISIT_STARTED = "lesson.visit.started"
    LESSON_VISIT_COMPLETED = "lesson.visit.completed"
    CANDIDATE_STARTED = "candidate.started"
    CANDIDATE_ASSESSED = "candidate.assessed"
    CANDIDATE_RETAINED = "candidate.retained"
    CANDIDATE_REJECTED = "candidate.rejected"
    CAPABILITY_CHANGED = "capability.changed"
    CHECKPOINT_COMMITTED = "checkpoint.committed"
    CHECKPOINT_RECOVERED = "checkpoint.recovered"
    SEMANTIC_COVERAGE_CHANGED = "semantic.coverage.changed"
    MEMORY_CHANGED = "memory.changed"
    TEACHER_STRATEGY_OUTCOME = "teacher.strategy.outcome"
    SALIENCE_OBSERVED = "salience.observed"
    CORRECTION_REQUALIFICATION_CHANGED = "correction.requalification.changed"
    RESOURCE_HEALTH_SAMPLE = "resource.health.sample"
    WARNING_FAILURE = "warning.failure"
    OPERATOR_ACTION_STATE = "operator.action.state"


class ReplayGapReason(StrEnum):
    CURSOR_UNAVAILABLE = "cursor-unavailable"
    SLOW_CONSUMER = "slow-consumer"


class EventIdentityDeduplicator:
    """Bounded projection-side duplicate filter keyed only by CP02 event identity."""

    def __init__(self, max_seen: int = 512):
        if max_seen <= 0:
            _invalid("EVENT_DEDUP_LIMIT_INVALID")
        self.max_seen = max_seen
        self._order: deque[str] = deque()
        self._seen: set[str] = set()

    def accept(self, event: EventEnvelope) -> bool:
        if event.event_id in self._seen:
            return False
        self._seen.add(event.event_id)
        self._order.append(event.event_id)
        if len(self._order) > self.max_seen:
            self._seen.remove(self._order.popleft())
        return True


@dataclass(frozen=True)
class StreamFrontier:
    stream_id: str
    epoch_id: str
    next_ordinal: int
    latest_cursor_sha256: str | None

    def to_record(self, *, schema: str = EVENT_FRONTIER_SCHEMA) -> dict:
        return {
            "schema": schema,
            "stream_id": self.stream_id,
            "epoch_id": self.epoch_id,
            "next_ordinal": self.next_ordinal,
            "latest_cursor_sha256": self.latest_cursor_sha256,
        }


@dataclass(frozen=True)
class _PendingReference:
    family: EventFamily
    meta: RecordMeta
    payload_schema_version: str
    payload_record_id: str
    payload_sha256: str
    payload_ref: str
    event_id: str | None


class OpenedSubscription(NamedTuple):
    acknowledgement: dict
    replay: tuple[EventEnvelope, ...]
    subscription: "BrokerSubscription | None"


class BrokerSubscription:
    """Per-client bounded queue; socket I/O never runs on the publisher path."""

    def __init__(self, broker: "EventStreamBroker", queue_limit: int):
        self._broker = broker
        self._queue_limit = queue_limit
        self._condition = Condition()
        self._queue: deque[EventEnvelope] = deque()
        self._gap: dict | None = None
        self._closed = False
        self._removed = False

    def push(self, event: EventEnvelope, frontier: StreamFrontier) -> None:
        with self._condition:
            if self._closed or self._gap is not None:
                return
            if len(self._queue) >= self._queue_limit:
                self._queue.clear()
                self._gap = self._broker.gap_record(
                    ReplayGapReason.SLOW_CONSUMER, frontier)
            else:
                self._queue.append(event)
            self._condition.notify()

    def next_record(self, timeout: float) -> dict | None:
        with self._condition:
            if not self._queue and self._gap is None and not self._closed:
                self._condition.wait(timeout)
            if self._queue:
                return encode_record(self._queue.popleft())
            if self._gap is not None:
                gap, self._gap = self._gap, None
                self._closed = True
                return gap
            return None

    def close(self) -> None:
        with self._condition:
            if self._removed:
                return
            self._closed = True
            self._removed = True
            self._condition.notify_all()
        self._broker.remove_subscription(self)


class EventStreamBroker:
    """In-memory replay cache only; authoritative learner state stays elsewhere."""

    def __init__(
        self, *, stream_id: str = "mission-control", epoch_id: str | None = None,
        retention_limit: int = 256, subscriber_queue_limit: int = 64,
        resource_bucket_span: int = 5,
    ):
        if min(retention_limit, subscriber_queue_limit, resource_bucket_span) <= 0:
            _invalid("EVENT_STREAM_LIMIT_INVALID")
        self.stream_id = stream_id
        self.epoch_id = epoch_id or str(uuid4())
        self.retention_limit = retention_limit
        self.subscriber_queue_limit = subscriber_queue_limit
        self.resource_bucket_span = resource_bucket_span
        self._lock = Lock()
        self._retained: deque[EventEnvelope] = deque(maxlen=retention_limit)
        self._subscribers: set[BrokerSubscription] = set()
        self._next_ordinal = 0
        self._last_cursor_sha256: str | None = None
        self._pending_resource: tuple[int, _PendingReference] | None = None
        self._coalesced_resource_samples = 0

    @property
    def coalesced_resource_samples(self) -> int:
        with self._lock:
            return self._coalesced_resource_samples

    def frontier(self) -> StreamFrontier:
        with self._lock:
            return self._frontier_locked()

    def _frontier_locked(self) -> StreamFrontier:
        return StreamFrontier(
            self.stream_id, self.epoch_id, self._next_ordinal,
            self._last_cursor_sha256)

    @staticmethod
    def _default_event_id(reference: _PendingReference) -> str:
        material = json.dumps({
            "event_family": reference.family.value,
            "payload_record_id": reference.payload_record_id,
            "payload_schema_version": reference.payload_schema_version,
            "payload_sha256": reference.payload_sha256,
        }, sort_keys=True, separators=(",", ":")).encode("utf-8")
        return "event:" + hashlib.sha256(material).hexdigest()

    def _emit_locked(
        self, reference: _PendingReference,
    ) -> tuple[EventEnvelope, tuple[BrokerSubscription, ...], StreamFrontier]:
        event_id = reference.event_id or self._default_event_id(reference)
        ordinal = self._next_ordinal
        cursor = event_cursor_sha256(
            stream_id=self.stream_id,
            epoch_id=self.epoch_id,
            ordinal=ordinal,
            event_id=event_id,
            payload_schema_version=reference.payload_schema_version,
            payload_record_id=reference.payload_record_id,
            payload_sha256=reference.payload_sha256,
            previous_cursor_sha256=self._last_cursor_sha256,
        )
        position = StreamPosition(
            self.stream_id, self.epoch_id, ordinal, cursor,
            self._last_cursor_sha256)
        meta = replace(
            reference.meta,
            record_id=f"event-envelope:{event_id}",
        )
        event = EventEnvelope(
            meta=meta,
            event_id=event_id,
            position=position,
            event_family=reference.family.value,
            payload_schema_version=reference.payload_schema_version,
            payload_record_id=reference.payload_record_id,
            payload_sha256=reference.payload_sha256,
            payload_ref=reference.payload_ref,
        )
        self._retained.append(event)
        self._next_ordinal += 1
        self._last_cursor_sha256 = cursor
        return event, tuple(self._subscribers), self._frontier_locked()

    @staticmethod
    def _fan_out(emitted) -> None:
        for event, subscribers, frontier in emitted:
            for subscriber in subscribers:
                subscriber.push(event, frontier)

    def _flush_resource_locked(self, emitted: list) -> None:
        if self._pending_resource is None:
            return
        _, reference = self._pending_resource
        self._pending_resource = None
        emitted.append(self._emit_locked(reference))

    def publish_record(
        self, family: EventFamily, payload: WireRecord, *, event_id: str | None = None,
    ) -> EventEnvelope | None:
        if not isinstance(payload, WireRecord):
            _invalid("EVENT_PAYLOAD_RECORD_REQUIRED")
        digest = hashlib.sha256(canonical_json(payload)).hexdigest()
        return self.publish_reference(
            family,
            meta=payload.meta,
            payload_schema_version=payload.schema_version,
            payload_record_id=payload.meta.record_id,
            payload_sha256=digest,
            payload_ref=f"record:{payload.meta.record_id}",
            event_id=event_id,
        )

    def publish_reference(
        self, family: EventFamily, *, meta: RecordMeta,
        payload_schema_version: str, payload_record_id: str, payload_sha256: str,
        payload_ref: str, event_id: str | None = None,
    ) -> EventEnvelope | None:
        if type(family) is not EventFamily:
            _invalid("EVENT_FAMILY_REQUIRED")
        reference = _PendingReference(
            family, meta, payload_schema_version, payload_record_id,
            payload_sha256, payload_ref, event_id)
        emitted = []
        with self._lock:
            if family is EventFamily.RESOURCE_HEALTH_SAMPLE:
                bucket = meta.materialized_at // self.resource_bucket_span
                if self._pending_resource is not None:
                    pending_bucket, _ = self._pending_resource
                    if bucket == pending_bucket:
                        self._pending_resource = (bucket, reference)
                        self._coalesced_resource_samples += 1
                        return None
                    self._flush_resource_locked(emitted)
                self._pending_resource = (bucket, reference)
            else:
                self._flush_resource_locked(emitted)
                emitted.append(self._emit_locked(reference))
        self._fan_out(emitted)
        return emitted[-1][0] if emitted else None

    def flush_resource_samples(self) -> EventEnvelope | None:
        emitted = []
        with self._lock:
            self._flush_resource_locked(emitted)
        self._fan_out(emitted)
        return emitted[-1][0] if emitted else None

    def gap_record(
        self, reason: ReplayGapReason, frontier: StreamFrontier | None = None,
    ) -> dict:
        frontier = frontier or self.frontier()
        return {
            **frontier.to_record(schema=EVENT_GAP_SCHEMA),
            "state": "fresh-snapshot-required",
            "reason": reason.value,
        }

    def open_subscription(self, after_cursor: str | None) -> OpenedSubscription:
        with self._lock:
            frontier = self._frontier_locked()
            if after_cursor is None:
                replay = ()
            else:
                match = next((
                    index for index, event in enumerate(self._retained)
                    if event.position.cursor_sha256 == after_cursor
                ), None)
                if match is None:
                    acknowledgement = {
                        **self.gap_record(
                            ReplayGapReason.CURSOR_UNAVAILABLE, frontier),
                        "accepted": False,
                    }
                    return OpenedSubscription(acknowledgement, (), None)
                replay = tuple(list(self._retained)[match + 1:])
            subscription = BrokerSubscription(
                self, self.subscriber_queue_limit)
            self._subscribers.add(subscription)
            acknowledgement = {
                **frontier.to_record(schema=EVENT_SUBSCRIPTION_SCHEMA),
                "accepted": True,
                "state": "streaming",
                "after_cursor": after_cursor,
                "replay_count": len(replay),
            }
            return OpenedSubscription(acknowledgement, replay, subscription)

    def remove_subscription(self, subscription: BrokerSubscription) -> None:
        with self._lock:
            self._subscribers.discard(subscription)

    def heartbeat_record(self) -> dict:
        return self.frontier().to_record(schema=EVENT_HEARTBEAT_SCHEMA)
