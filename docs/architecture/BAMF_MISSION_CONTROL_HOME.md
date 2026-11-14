# BAMF Mission Control GUI03 home

GUI03 is the outcome-first Mission Control home. Its job is not to prove that work
is happening. It must let an operator answer, in roughly one glance:

1. Is Bilqis running?
2. Is it learning, rather than merely processing work?
3. What is it working on?
4. Is anything regressing?
5. Is any evidence, custody, or control state invalid enough to require attention?

The home composes accepted GUI01/GUI02 shell semantics, CP03 bounded read queries,
CP04 resumable event delivery, and GUI19 defensive-state behavior. It does not own
scheduler policy, learner state, or mutation authority.

## Truth rule: throughput is not learning

GUI03 deliberately separates candidate throughput from demonstrated retained
improvement. A run that retains ten candidates while producing no fresh retained
improvement is `THROUGHPUT_ONLY`, not `IMPROVING`. Candidate counts, visit counts,
optimizer activity, and accepted steps are runtime evidence. They do not become a
learning claim by accumulation.

The home may say `IMPROVING` only when the projection has fresh retained-improvement
evidence. Missing best-score history, growth, G/RTN, P(RET), resource, warning, or
other telemetry remains `UNAVAILABLE`; it is never synthesized as zero or healthy.

## Initial projection

For a verified context the renderer issues bounded CP03 queries for:

- run;
- school;
- capability;
- episode;
- semantic;
- resource;
- correction;
- teacher.

The resulting page state (`PRESENT`, `EMPTY`, `MISSING`, `UNAVAILABLE`, `PARTIAL`,
`STALE`, `DENIED`, or `UNKNOWN`) remains attached to the corresponding home section.
A stale or partial query therefore changes the section's treatment instead of
becoming an ordinary zero-value metric.

Checked-in fixtures remain explicit test and reference surfaces. Production startup
never uses `fixture-run` as a substitute for a missing live OperatorView. The shell
derives its live identity from CP01 and CP03 only.

## Startup and sparse telemetry

Mission Control reports startup as separate service boundaries instead of rendering a
fully populated dashboard before evidence exists:

1. local CP01 connection;
2. accepted learner discovery;
3. first accepted Mission Control operator projection;
4. trainer activity.

CP01 status may prove that the service is healthy and an accepted learner exists even
when CP02 and CP03 telemetry has not materialized. In that state the shell shows the
real run ID, generation, optimizer step, and trainer activity from the bounded public
CP01 status. The main view reports that telemetry is starting. It does not fill metric
cards with repeated `UNAVAILABLE` values and does not load fixture data.

If startup fails, the defensive banner shows the failing boundary and bounded error
code. Mutation stays unavailable until a fresh verified OperatorView establishes the
accepted live command context.

## Incremental LIVE updates

GUI20 already exposed a renderer-safe subscription capability, but before GUI03 the
accepted production adapter did not connect it to CP04. GUI03 closes that private
boundary without introducing a public broker:

1. Electron main asks the accepted adapter to subscribe.
2. The private Node broker starts a dedicated Python event-stream process.
3. That process creates its own CP01 client session and consumes the accepted CP04
   `EventEnvelope` stream.
4. Only renderer-safe, schema-validated event envelopes cross the Electron bridge.
5. The home maps each event family to its owning CP03 family and refreshes only that
   family.

For example, `capability.changed` refreshes `capability`; candidate/lesson events
refresh `episode`; resource samples refresh `resource`. An event does not trigger a
full OperatorView or full-home polling loop.

CP04 remains delivery, not authority. The event says which accepted read projection
may have changed; CP03 supplies the readback used by the home.

## Historical mode

When the shell supplies a historical context, GUI03 binds every query to the exact
`run_id` and explicit `generation`, renders the same home structure as historical,
and does not open a CP04 live subscription.

GUI03 does not invent a historical-generation catalog. The existing GUI01 selector
surface must be backed by an authoritative generation choice before it can establish
that context. In particular, GUI03 never interprets `current generation - 1` as a
valid historical target.

## Drill-through

Home pulse, compact School Map, and attention items carry exact object identities.
Selecting a regression opens the global inspector on the exact capability or episode;
`Open in owning view` then reuses the accepted GUI01 owner routing. GUI03 does not
create a parallel inspector.

## Attention policy

`Attention Required` is a queue of actionable conditions represented by available
evidence. Ordinary healthy telemetry is not repeated there. Missing warning telemetry
is `UNAVAILABLE`, not `0 warnings`.

## Verification surfaces

Automated coverage includes:

- the five core home questions in one view;
- ten retained/no-growth events remaining throughput-only;
- fresh retained gain and regression drill-through identity;
- actionable-only attention fixtures;
- stale/partial query-state preservation;
- exact historical generation query binding;
- CP04 family-to-CP03 targeted refresh behavior;
- no live subscription in historical mode;
- a real CP01/CP04 service emitting a CP02 `EventEnvelope` through the private
  Python/Node/Electron boundary.

Manual browser acceptance uses the actual renderer with a temporary local bridge
harness and compares information hierarchy against the issue reference. The harness
is not part of the committed application.
