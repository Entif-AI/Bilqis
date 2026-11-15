# Admin Main Frame cross-view flows

Status: target-state cross-view relationship map for the Admin Main Frame redesign
Atlas authority: `INFORMATION_ATLAS.md`
Parent authority: GitHub issue #1124

The target atlas owns composition. This file owns target relationships between atlas nodes. Current renderer relationships are migration evidence in `CURRENT_STATE_UI_INVENTORY.md` and source code; a current flow survives only when it remains useful and authority-safe in the target.

## FLOW-D-001 · Ordinary destination navigation

```mermaid
flowchart LR
  A[COMP-D-001 Primary navigation] --> B[VIEW-D-001..014 Destination]
  C[COMP-D-008 Command palette] --> B
  B --> D[COMP-D-005 Destination header]
  D --> E[Primary working components]
```

Rules:
- destination changes preserve the current verified/historical context where valid;
- Operate remains unavailable without verified live mutation context;
- keyboard focus moves to the destination heading;
- direct/deep-link navigation must remain possible even if visible navigation becomes grouped.

## FLOW-D-002 · Object selection → inspector → owner

```mermaid
flowchart LR
  A[Selectable atlas component] --> B[COMP-D-007 Global inspector]
  B --> C{Open owning view}
  C -->|capability| D[VIEW-D-003 Capability Explorer]
  C -->|episode/candidate| E[VIEW-D-004 Learning]
  C -->|semantic| F[VIEW-D-005 Atlas]
  C -->|frame/neural| G[VIEW-D-006 Model]
  C -->|memory| H[VIEW-D-007 Memory]
  C -->|strategy| I[VIEW-D-008 Teacher]
  C -->|salience observation| J[VIEW-D-009 SÍ SÉ SON]
  C -->|correction| K[VIEW-D-010 Corrections]
  C -->|generation/checkpoint| L[VIEW-D-011 Lineage]
  C -->|resource/warning| M[VIEW-D-012 Resources]
  C -->|evidence/source| N[VIEW-D-013 Evidence]
  C -->|operation| O[VIEW-D-014 Operate]
```

The selected object identity is run + generation + kind + ID. Opening an owner must not silently rebind the object to a different context.

## FLOW-D-003 · Object selection → Evidence → return

```mermaid
flowchart LR
  A[Any selected object] --> B[COMP-D-007 Inspector]
  B --> C[Open evidence]
  C --> D[VIEW-D-013 Evidence]
  D --> E[COMP-D-1302 Result]
  E --> F[COMP-D-1303 Exact record]
  F --> G[COMP-D-1304 Return to origin]
  G --> A
```

Evidence preserves an explicit origin when opened contextually. Return restores the investigation path rather than guessing from object type.

## FLOW-D-004 · Time lens

```mermaid
flowchart LR
  A[STATE-D-002 Live context] --> B[COMP-D-010 Time lens]
  B --> C[STATE-D-003 Historical context]
  C --> D[Destination historical projection]
  D --> E[Mutation unavailable]
  C --> F[Return to current]
  F -->|verified live context exists| A
```

Changing generation makes the context historical and clears/invalidates live-only authority fields until a view obtains exact historical evidence. Returning to current requires a verified live context.

## FLOW-D-005 · Compare

```mermaid
flowchart LR
  A[COMP-D-007 Inspector] --> B[Set compare left]
  A --> C[Set compare right]
  B --> D[COMP-D-011 Compare workspace]
  C --> D
  D --> E{Comparable?}
  E -->|yes| F[Literal comparison rows]
  E -->|no/partial| G[Explicit mismatch / unavailable reason]
```

Compare must state differences in run/generation/kind/context. Visual symmetry does not imply semantic equivalence.

## FLOW-D-006 · Pin and reopen exact context

```mermaid
flowchart LR
  A[COMP-D-007 Inspector] --> B[Pin exact object]
  B --> C[COMP-D-012 Pins]
  C --> D[Open exact pin]
  D --> E[Owning destination + pinned context]
```

Pins are operator metadata keyed to exact object context. They do not promote evidence or alter learner state.

## FLOW-D-007 · Operator annotation

```mermaid
flowchart LR
  A[COMP-D-007 Inspector] --> B[Add operator note]
  B --> C[COMP-D-013 Operator notes]
  C --> D[Local operator metadata]
  D --> E[Displayed as NON-AUTHORITATIVE]
```

Annotations remain local/non-authoritative and must never acquire source or learned-state styling.

## FLOW-D-008 · School → Capability Explorer

```mermaid
flowchart LR
  A[COMP-D-201 Capability matrix] --> B[Select capability]
  C[COMP-D-202 Dependency graph] --> B
  B --> D[COMP-D-007 Inspector]
  D --> E[VIEW-D-003 Capability Explorer]
  E --> F[COMP-D-305 Dossier sections]
  E --> G[COMP-D-306 Inline evidence detail]
```

School answers comparative/topological questions. Capability Explorer owns exact longitudinal dossier detail.

## FLOW-D-009 · Learning evidence path

```mermaid
flowchart LR
  A[COMP-D-401 Episode/candidate] --> B[COMP-D-402 Transaction detail]
  B --> C[COMP-D-403 Retention/rollback evidence]
  C --> D[VIEW-D-013 Evidence]
  B --> E[VIEW-D-003 Capability Explorer]
  B --> F[VIEW-D-011 Lineage]
```

The flow must preserve the difference between an episode, a capability claim, accepted lineage, and raw evidence.

## FLOW-D-010 · Memory relation path

```mermaid
flowchart LR
  A[COMP-D-702 Memory slot] --> B[COMP-D-703 Motif inspector]
  B --> C[Related capability]
  B --> D[Related episode]
  C --> E[VIEW-D-003 Capability Explorer]
  D --> F[VIEW-D-004 Learning]
  B --> G[VIEW-D-013 Evidence]
```

Memory retrieval is operational evidence, not source truth. Navigation may reveal related claims but must not visually collapse the authority boundary.

## FLOW-D-011 · Correction blast-radius investigation

```mermaid
flowchart LR
  A[COMP-D-1001 Correction context] --> B[COMP-D-1002 Affected object]
  B --> C[Owning destination]
  A --> D[COMP-D-1004 Requalification queue]
  D --> E[VIEW-D-013 Evidence]
  B --> F[VIEW-D-011 Lineage]
```

Corrections reveal known exposure and requalification evidence. The UI must not claim perfect neural unlearning.

## FLOW-D-012 · Resource spike investigation

```mermaid
flowchart LR
  A[COMP-D-1205 Resource sample] --> B[COMP-D-007 Inspector]
  B --> C[Related episode/batch/checkpoint/preparation refs]
  C --> D[VIEW-D-004 Learning]
  C --> E[VIEW-D-011 Lineage]
  C --> F[VIEW-D-013 Evidence]
```

Correlation is literal. The interface must not turn temporal/resource association into a causal explanation.

## FLOW-D-013 · Operate command lifecycle

```mermaid
flowchart LR
  A[VIEW-D-014 Operate] --> B[COMP-D-1401 Choose action]
  B --> C[COMP-D-1402 Exact request]
  C --> D[Read-only preflight]
  D --> E[COMP-D-1403 Review resolved target]
  E --> F{Target current and action allowed?}
  F -->|no| G[Fail closed / refresh]
  F -->|yes, read-only| H[Submit exact request]
  F -->|yes, mutating| I[COMP-D-1404 Human authorization]
  I --> H
  H --> J[COMP-D-1405 Receipt/readback]
  J --> K{Terminal proof?}
  K -->|yes| L[Open receipt/postcondition]
  K -->|unknown| M[Reconcile, never blind retry]
```

This flow is a safety boundary. Visual simplification may not skip, merge, pre-authorize, or imply completion of any unproven stage.

## FLOW-D-014 · Defensive reconnect

```mermaid
flowchart LR
  A[STATE-D-004 Offline/restarting/etc.] --> B[COMP-D-004 Defensive banner]
  B --> C[Reconnect]
  C --> D[STATE-D-001 Bootstrap sequence]
  D --> E{Fresh verified snapshot?}
  E -->|no| A
  E -->|yes| F[STATE-D-002 Live verified context]
```

The current view/selection may be retained when safe, but mutation stays unavailable until the fresh snapshot re-establishes command context.

## FLOW-D-015 · Display settings

```mermaid
flowchart LR
  A[COMP-D-002 View settings] --> B[Dark / light]
  A --> D[Comfortable / compact]
  B --> E[Same semantic hierarchy]
  D --> E
```

Theme and density may alter visual presentation only. They may not hide a state, change semantic priority, or make a required control inaccessible.

## FLOW-D-016 · Deep link / app URI

```mermaid
flowchart LR
  A[Hash or bamf-mc app URI] --> B[Decode route + exact selected ref]
  B --> C[Destination]
  B --> D[Run/generation context]
  B --> E[Selected object]
  E --> F[COMP-D-007 Inspector or local selection]
  C -->|frame/neural| G[VIEW-D-006 correct Model subsection]
```

Deep links preserve destination, exact context, and selection. Target UI exposes `Copy deep link` from the global inspector rather than dedicating permanent shell chrome to the URI. The route must not silently discard run/generation identity or route a frame into the wrong Model subsection.

## FLOW-D-017 · Model neural ↔ frame context custody

```mermaid
flowchart LR
  A[VIEW-D-006 Neural Runtime] --> B[Enter Frame Compiler Explorer]
  B --> C[Save shell return context]
  C --> D[Install exact fixture/reference context]
  D --> E[Disable mutation]
  E --> F[Frame queries / selected frontier]
  F --> G[Exit Frames]
  G --> H[Invalidate stale frame responses]
  H --> I[Restore saved shell context]
```

The frame surface is not allowed to borrow the live shell's authority merely because it is visually inside the same destination.

## FLOW-D-018 · Selective live event refresh

```mermaid
flowchart LR
  A[Accepted CP04 event] --> B{Affected family}
  B -->|home families| C[VIEW-D-001 refresh affected overview query]
  B -->|resource events| D[VIEW-D-012 refresh resource projection]
  B -->|operation action-state| E[VIEW-D-014 request authoritative readback]
  B -->|unrelated| F[No destination refresh]
```

Event delivery is effect plumbing, not a new authority layer. Visual activity indicators must not imply that an event changed semantic truth merely because a view refreshed.
