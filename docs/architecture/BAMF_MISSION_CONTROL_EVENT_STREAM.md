# BAMF Admin Main Frame CP04 event stream

CP04 is a bounded delivery layer over the versioned CP02
`EventEnvelope`/`StreamPosition` contract. It is not a learner database,
checkpoint owner, event-sourced training runtime, or durable evidence store.

## Ordering and cursor scope

- Event order is ingestion order within one declared `stream_id` and
  `epoch_id`.
- The broker assigns monotonically increasing ordinals and a cursor digest that
  binds the ordinal, predecessor cursor, event identity and payload identity.
- Evidence timestamps are serialized literally. They do not reorder the
  stream.
- A service restart starts a new epoch. A cursor that cannot be reconciled
  against retained events returns `fresh-snapshot-required`; the service does
  not guess across a replay gap.

## Snapshot and replay

Clients bootstrap authoritative view state through the snapshot/query side of
Admin Main Frame and then subscribe after an event cursor/frontier. CP04 retains
only a bounded in-memory replay window. Reconnect with a retained cursor
replays events after that cursor and then joins the live stream without a
snapshot polling loop.

Duplicate transport delivery is tolerated. The projection side deduplicates by
the CP02 `event_id`; replay position is not event identity.

If the cursor is expired, belongs to an unavailable epoch, or otherwise cannot
close the replay interval, the response is an explicit
`fresh-snapshot-required` gap state. The client must refresh its snapshot
rather than silently substituting current state for missing history.

## Backpressure

Every subscriber has an independent bounded queue. Publishing only appends to
the replay buffer and those queues; it never performs client socket I/O.
Therefore a slow or crashed GUI cannot block learner-side event publication.

When a subscriber exhausts its queue, queued deltas are discarded for that
subscriber and the stream transitions to `fresh-snapshot-required` with
reason `slow-consumer`. The learner and other subscribers continue.

## Resource telemetry coalescing

`resource.health.sample` is intentionally lower fidelity than domain events.
Samples are grouped by configurable buckets over CP02 `materialized_at`.
Within a bucket, only the latest ingested sample is retained. A pending sample
is emitted before the next bucket, before a non-resource domain event, or on an
explicit telemetry flush. Cursor ordinals are assigned only when the
coalesced sample is emitted, so suppressed samples never create replay holes.

The default bucket span is five `materialized_at` units. Tests use explicit
spans where deterministic compression matters.

## Authority and recovery

The replay buffer is disposable. Losing it may force a fresh snapshot, but it
cannot destroy or rewrite learner state, checkpoints, generation manifests,
semantic releases, receipts or evidence. Recovery comes from those existing
authoritative artifacts. CP04 only delivers references and identities already
represented by CP02 records.
