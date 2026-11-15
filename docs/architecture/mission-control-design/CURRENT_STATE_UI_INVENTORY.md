# Admin Main Frame current-state UI inventory

Status: descriptive map of the current implementation, not target-screen approval
Parent authority: GitHub issue #1124
Target-state atlas: `INFORMATION_ATLAS.md`
Cross-view relationships: `FLOWS.md`

This inventory deliberately describes the current renderer anatomy as a hierarchy. It is migration/substrate evidence, not the target UI specification. Cross-view navigation, state propagation, selection ownership, evidence return, compare, pinning, and command lifecycles are kept in `FLOWS.md` so this tree does not become spaghetti.

## ID grammar

- `CUR-SHELL-###`: persistent shell segment
- `CUR-VIEW-###`: destination
- `CUR-COMP-###`: published component/section inside a shell/view
- `CUR-COMP-###.<n>[.<n>…]`: recursive constituent below a published component; dotted descendants never renumber/reuse an existing parent ID
- `CUR-STATE-###`: important presentation state

Each component records **information → treatment → interaction → effect**. A component is **composite, not terminal**, while it still contains an independently meaningful subcomponent, repeated control family, presentation/state contract, interaction contract, or distinct effect. Recursion stops only at a true semantic leaf. Repeated controls with identical mechanics may share a family parent, but fixed instances are enumerated and behaviorally distinct instances/states are separate.

The register and nested outlines below preserve the source-grounded current renderer anatomy. They are deliberately not the target visual atlas. Target composition and intended UI content live in `INFORMATION_ATLAS.md`.

## Current renderer hierarchy outline

- Bilqis Admin Main Frame
  - CUR-SHELL-001 Application shell
    - CUR-COMP-015 Skip to main access path
    - CUR-COMP-001 Primary navigation
    - CUR-COMP-002 Context bar
    - CUR-COMP-003 Investigation strip
      - CUR-COMP-010 Time lens
      - CUR-COMP-011 Compare workspace
      - CUR-COMP-012 Pins
      - CUR-COMP-013 Annotations
      - CUR-COMP-014 App URI and deep link
    - CUR-COMP-004 Defensive banner
    - Workspace
      - CUR-COMP-005 Destination header
      - CUR-COMP-006 Local subnavigation
      - CUR-VIEW-001 Admin Main Frame
        - CUR-COMP-107 Startup state
        - CUR-COMP-101 Learner posture
        - CUR-COMP-102 Learning pulse
        - CUR-COMP-103 Actionable attention
        - CUR-COMP-104 Health strip
        - CUR-COMP-105 Current work
        - CUR-COMP-106 Compact School map
      - CUR-VIEW-002 School
        - CUR-COMP-201 Capability matrix
          - CUR-COMP-207 Matrix controls
        - CUR-COMP-202 Dependency graph
        - CUR-COMP-203 Curriculum semantic atlas
          - CUR-COMP-205 Curriculum controls
          - CUR-COMP-206 Topology and node dossier
          - CUR-COMP-208 Semantic equivalent table
          - CUR-COMP-209 Scale disclosure
        - CUR-COMP-204 Peer subnavigation
      - CUR-VIEW-003 Capability Explorer
        - CUR-COMP-301 Capability identity
        - CUR-COMP-302 Chronology
        - CUR-COMP-303 Source and evidence dossier
        - CUR-COMP-304 Source lens controls
        - CUR-COMP-305 Dossier sections
        - CUR-COMP-306 Inline evidence detail
      - CUR-VIEW-004 Learning
        - CUR-COMP-401 Episode selector
        - CUR-COMP-402 Candidate transaction
        - CUR-COMP-403 Retention rollback evidence
        - CUR-COMP-404 Challenger committed comparison
        - CUR-COMP-405 Lifecycle replay controls
      - CUR-VIEW-005 Atlas
        - CUR-COMP-521 View request state
        - CUR-COMP-501 Semantic overview
        - CUR-COMP-502 Semantic selection
        - CUR-COMP-503 Semantic authority lens
        - CUR-COMP-504 ABI bank map
        - CUR-COMP-505 Exact semantic lookup
      - CUR-VIEW-006 Model
        - CUR-COMP-601 Model local navigation
        - CUR-COMP-611 Neural Runtime
          - CUR-COMP-602 Neural topology
          - CUR-COMP-603 CCGQA attention AttnRes
          - CUR-COMP-604 Local refinement
          - CUR-COMP-605 Instrumentation coverage
        - CUR-COMP-606 Frame Compiler Explorer
          - CUR-COMP-607 Frame generation and query
          - CUR-COMP-608 Compiled provenance and packing
          - CUR-COMP-609 Prediction frontier
          - CUR-COMP-610 Aggregate packing disclosure
      - CUR-VIEW-007 Memory
        - CUR-COMP-733 Historical memory unavailable
        - CUR-COMP-701 Memory summary
        - CUR-COMP-702 Memory atlas pages
        - CUR-COMP-703 Motif inspector
        - CUR-COMP-704 Generation comparison
        - CUR-COMP-705 Rejected candidate boundary
      - CUR-VIEW-008 Teacher
        - CUR-COMP-801 Strategy population
        - CUR-COMP-802 Outcome cost fidelity
        - CUR-COMP-803 Fidelity ladder
        - CUR-COMP-804 Projection boundary
      - CUR-VIEW-009 SI SE SON
        - CUR-COMP-906 As-of snapshot selector
        - CUR-COMP-901 Salience observations
        - CUR-COMP-902 Provenance
        - CUR-COMP-903 Recursive aggregation
        - CUR-COMP-904 Routing rationale
        - CUR-COMP-905 Projection boundary
      - CUR-VIEW-010 Corrections
        - CUR-COMP-1001 Correction context
        - CUR-COMP-1002 Blast-radius graph
        - CUR-COMP-1003 Equivalent impact table
        - CUR-COMP-1004 Requalification state
        - CUR-COMP-1005 Append-only history
      - CUR-VIEW-011 Lineage
        - CUR-COMP-1101 Accepted lineage
        - CUR-COMP-1102 Generation comparison
        - CUR-COMP-1103 Rejected candidate boundary
        - CUR-COMP-1104 Exact generation node
      - CUR-VIEW-012 Resources
        - CUR-COMP-1201 Resource headline
        - CUR-COMP-1202 Metric semantics
        - CUR-COMP-1203 Memory decomposition
        - CUR-COMP-1204 Compute and length
        - CUR-COMP-1205 Timeline and correlation
        - CUR-COMP-1206 Historical comparison
      - CUR-VIEW-013 Evidence
        - CUR-COMP-1301 Query and filter
        - CUR-COMP-1305 Query and degraded state
        - CUR-COMP-1302 Result list
        - CUR-COMP-1306 Traversal and omission status
        - CUR-COMP-1303 Exact record and raw payload
        - CUR-COMP-1304 Return to origin
      - CUR-VIEW-014 Operate
        - CUR-COMP-1400 Command boundary posture
        - CUR-COMP-1401 Action catalog
        - CUR-COMP-1402 Exact request
        - CUR-COMP-1403 Preflight
        - CUR-COMP-1404 Deliberate authorization
        - CUR-COMP-1405 Receipt and reconciliation
    - CUR-COMP-007 Global inspector
    - CUR-COMP-008 Command palette
    - CUR-COMP-009 Fixture provenance boundary
    - CUR-COMP-016 Polite live announcer

## CUR-SHELL-001 · Application shell

### CUR-COMP-015 · Skip-to-main access path
- Information: keyboard bypass route to the main content focus target.
- Treatment: visually hidden until focused.
- Interaction: activate the skip link.
- Effect: moves keyboard focus past persistent shell chrome to `#main-content`.

### CUR-COMP-001 · Primary navigation rail
- Information: Bilqis/Admin Main Frame identity; current destination; fourteen destination actions; command-palette trigger.
- Treatment: persistent left rail with flat destination buttons.
- Interaction: click or roving keyboard navigation; command palette via keyboard shortcut.
- Effect: changes destination while preserving current run/generation context where allowed.
- Concerns: D-003 overload; eventual task/domain grouping; no ambiguous collapsed labels.

### CUR-COMP-002 · Context bar
- Information: posture, run, generation/manifest, freshness, topology, Factory release, semantic release, optimizer, lease, frontier, resources, coverage, run/time selectors.
- Treatment: persistent top context strip.
- Interaction: run/generation selection where supported; theme and density controls.
- Effect: changes inspected context/display settings.
- Concerns: excessive permanent metadata; operator-significant values must not truncate.

### CUR-COMP-003 · Global investigation strip
- Information: current/as-of lens plus entry points for compare, pins, annotations, and exact app/deep-link context.
- Treatment: persistent investigation toolbar with deliberately disclosed workspaces.
- Interaction: open one investigation workspace or change the time lens.
- Effect: coordinates the independent investigation subcomponents below.
- Concerns: must not compete visually with primary destination; exact context identity is mandatory.

### CUR-COMP-010 · Time lens
- Information: current verified context or exact historical generation.
- Treatment: compact generation input/current-context affordance.
- Interaction: choose exact generation; return to verified current when available.
- Effect: changes the global inspected context to historical or current and gates mutation accordingly.

### CUR-COMP-011 · Compare workspace
- Information: exact left/right stable object refs, comparison state, literal comparison rows and mismatch reasons.
- Treatment: disclosed two-slot comparison workspace plus analytical table.
- Interaction: clear either side or populate sides from the global inspector; comparison rows themselves are static.
- Effect: compares exact objects without implying equivalence when run/generation/kind differ.

### CUR-COMP-012 · Pins
- Information: locally stored exact object refs including run, generation, kind, ID and label.
- Treatment: disclosed pin list.
- Interaction: open exact pin; remove pin.
- Effect: returns to the pinned object's exact owning route/context without changing learner state.

### CUR-COMP-013 · Annotations
- Information: local operator notes attached to exact stable refs and explicitly marked non-authoritative.
- Treatment: note list plus bounded annotation form.
- Interaction: create/read notes for the selected exact object context.
- Effect: persists operator metadata locally without promoting it to evidence/source truth.

### CUR-COMP-014 · App URI / deep-link affordance
- Information: exact routable object/context identity.
- Treatment: compact exact URI rendered as code subordinate to investigation.
- Interaction: none directly in the current renderer; the URI is exposed for external/manual use.
- Effect: supplies a stable route string that can rehydrate exact destination, context, selection and Model subsection when consumed.

### CUR-COMP-004 · Defensive-state banner
- Information: current service/telemetry/availability posture and recovery guidance.
- Treatment: conditional status/alert banner with non-color cue.
- Interaction: reconnect where available.
- Effect: communicates boundary-specific failure/recovery and may gate mutation.

### CUR-COMP-005 · Destination header
- Information: destination eyebrow, title, concise purpose/current interpretation boundary.
- Treatment: top of workspace.
- Interaction: none, except focus target after navigation.
- Effect: establishes task hierarchy and reading context.

### CUR-COMP-006 · Destination-local subnavigation
- Information: peer modes within a destination, currently Model → Neural Runtime / Frame Compiler Explorer.
- Treatment: tab/segmented-like local controls.
- Interaction: switches peer surface.
- Effect: changes local working surface without changing global destination.

### CUR-COMP-007 · Global inspector
- Information: selected object kind, identity, posture, generation, exact details, owner/evidence actions.
- Treatment: non-modal side inspection plane.
- Interaction: close, open owner, open evidence, pin, compare left/right, annotate.
- Effect: cross-view navigation and investigation-state changes; focus returns to invoker.

### CUR-COMP-008 · Command palette
- Information: destination list and availability.
- Treatment: modal dialog.
- Interaction: keyboard open, roving selection, activate/close.
- Effect: fast destination navigation; mutation remains separately gated.

### CUR-COMP-009 · Fixture provenance boundary
- Information: whether a rich surface is live, historical, reference, or fixture-backed and which context owns it.
- Treatment: local provenance notice/status adjacent to the affected working surface.
- Interaction: usually none; may link to exact evidence where available.
- Effect: prevents checked-in diagnostic richness from being mistaken for live accepted learner telemetry.

### CUR-COMP-016 · Polite live announcer
- Information: transient operator-facing state-change announcements.
- Treatment: screen-reader-only `aria-live="polite"` / atomic region.
- Interaction: none directly.
- Effect: announces repeated navigation, selection, recovery, metadata and validation changes; content is cleared before the next microtask so repeated messages are voiced.

### CUR-STATE-001 · Bootstrap
- Four-stage startup: control plane, learner discovery, Admin Main Frame telemetry, trainer.
- Must not substitute fixtures for missing live telemetry.

### CUR-STATE-002 · Live verified context
- Fresh snapshot supports ordinary inspection; Operate is available only when mutation context is verified.

### CUR-STATE-003 · Historical / inspection-only
- Exact prior generation context; mutation disabled.

### CUR-STATE-004 · Defensive variants
- loading, progressive, empty, stale, partial, offline, denied, revoked, unavailable, incompatible-version, timeout, duplicate-action, session/service restarting, historical unavailable, malformed/unsupported payload, outcome unknown.

### CUR-STATE-005 · Route / deep-link state
- Destination, exact selected object, run/generation context, and Model subsection where applicable.

### CUR-STATE-006 · Global selection / inspector state
- Exact selected object plus focus-return origin and inspector-open posture.

### CUR-STATE-007 · Evidence-return origin state
- The destination/object context from which Evidence was opened, retained for explicit return.

### CUR-STATE-008 · Investigation state
- Active panel, compare sides, pins, annotations, and exact stable object references.

### CUR-STATE-009 · Display / focus / fixture-custody state
- Theme, density, focus-return tokens, and temporary fixture/reference context ownership where a surface is not using the live shell context.

## CUR-VIEW-001 · Admin Main Frame

Purpose: outcome-first learner health, current work, learning pulse, actionable attention.

### CUR-COMP-107 · Startup state
- Information: accepted generation, optimizer step, trainer running/stopped/unknown, current stage, and whether the first accepted learning event exists.
- Treatment: dedicated startup panel used instead of the normal dashboard when startup projection is present.
- Interaction: no direct action control in the current panel; copy points to Operate or the documented CLI resume path.
- Effect: distinguishes generation-zero-ready, trainer-running/waiting, and accepted-idle/no-events conditions without rendering absent learning telemetry as failure.

### CUR-COMP-101 · Learner headline / current posture
- Information: accepted learner health and current state.
- Treatment: summary region.
- Interaction: inspect relevant object where exposed.
- Effect: establishes the most important current condition.

### CUR-COMP-102 · Learning pulse
- Information: recent accepted learning activity and progression signal.
- Treatment: compact trend/summary surface.
- Interaction: inspect/navigate to exact learning evidence.
- Effect: answers whether learning is currently advancing without requiring the operator to enter Learning first.

### CUR-COMP-103 · Actionable attention
- Information: items requiring operator attention.
- Treatment: prioritized attention list/status.
- Interaction: inspect or navigate.
- Effect: converts overview into next investigation.

### CUR-COMP-104 · Health strip
- Information: Learning, Curriculum, Runtime, and System health families.
- Treatment: compact status strip using the application-wide status grammar.
- Interaction: none in the current renderer; the four health cards are static summary sections.
- Effect: distinguishes where an issue lives at overview depth.

### CUR-COMP-105 · Current work
- Information: active candidate/training work and its exact target/context.
- Treatment: concise current-work summary.
- Interaction: none in the current renderer; the current-work details are a static definition list.
- Effect: exposes what the learner is doing now without conflating work-in-progress with retained learning.

### CUR-COMP-106 · Compact School map
- Information: current curriculum/capability position at overview depth.
- Treatment: reduced School summary rather than a second full matrix.
- Interaction: select a capability row; the current Home binding inspects that exact capability through the shared selection/inspector path.
- Effect: provides orientation without duplicating the full School destination.

## CUR-VIEW-002 · School

Purpose: exact capability comparison and declared prerequisite topology.

### CUR-COMP-201 · Capability matrix
- Information: capability rows; WAS/TOP/NOW/ALL; debt; retention probability where measured; source/implementation/qualification state.
- Treatment: dense analytical matrix.
- Interaction: select capability; sort/filter where implemented.
- Effect: opens capability in inspector and cross-highlights relationships.

### CUR-COMP-207 · Matrix controls
- Information: active filters, family grouping, sort key/direction, page position, displayed identity count, and export scope.
- Treatment: filter/group/export control row, sortable column headings, and bounded pagination footer around the matrix.
- Interaction: toggle filters, group by family, sort, page previous/next, export the displayed identities.
- Effect: changes the visible matrix projection or exports that exact projection without changing capability evidence.

### CUR-COMP-202 · Dependency graph
- Information: prerequisite and dependent relationships.
- Treatment: interactive graph plus accessible equivalent relationship table.
- Interaction: keyboard/pointer selection.
- Effect: changes selected capability and neighborhood.

### CUR-COMP-203 · Curriculum semantic atlas
- Information: curriculum/semantic relationships supplied by GUI22.
- Treatment: dedicated analytical surface within School.
- Interaction: inspect/select semantic/curriculum objects.
- Effect: bridges curriculum structure and capability context.

### CUR-COMP-204 · School peer subnavigation
- Information: Capability matrix / Curriculum Semantic Atlas peer modes.
- Treatment: local peer-mode navigation.
- Interaction: switch School mode without leaving the destination.
- Effect: changes the working surface while preserving School context.

### CUR-COMP-205 · Curriculum search / filter / trace controls
- Information: query/filter controls and trace selection for curriculum-semantic relationships.
- Treatment: compact control cluster local to the curriculum atlas.
- Interaction: search, filter, select trace.
- Effect: narrows the curriculum-semantic working set without mutating learner state.

### CUR-COMP-206 · Declared topology / node dossier
- Information: selected curriculum/topology node, semantic binding, and declared consequences.
- Treatment: detail/dossier surface adjacent to the atlas.
- Interaction: select node, inspect exact binding/evidence.
- Effect: explains the exact declared relationship behind the visual topology.

### CUR-COMP-208 · Curriculum semantic equivalent table
- Information: capability, semantic display identity, grade, state, prerequisites, dependents, and evidence for every atlas node.
- Treatment: scrollable tabular equivalent beneath the visual curriculum graph.
- Interaction: select a capability/node from the table.
- Effect: changes the selected curriculum node while providing an equivalent non-graph representation.

### CUR-COMP-209 · Scale / progressive disclosure
- Information: a 243-row representative School fixture summarized by grade and semantic family, with bounded family and semantic expansion.
- Treatment: collapsed `details` summary with bounded family buttons and selected-node descendant disclosure.
- Interaction: expand the scale section, choose a family, choose a semantic within the bounded expansion.
- Effect: demonstrates how large School scopes are progressively disclosed without rendering all 243 rows as one graph.

## CUR-VIEW-003 · Capability Explorer

Purpose: measured chronology, source support, literal evidence; no inferred causes.

### CUR-COMP-301 · Capability identity/header
- Information: exact capability and context.
- Treatment: dossier header/state.
- Interaction: time/context controls where supported.
- Effect: anchors evidence to exact capability.

### CUR-COMP-302 · Chronology / measurements
- Information: measured progression and events over time.
- Treatment: chronology/table/metric surfaces.
- Interaction: inspect exact evidence.
- Effect: supports temporal comparison without causal synthesis.

### CUR-COMP-303 · Source/evidence dossier
- Information: source support and literal evidence.
- Treatment: evidence sections/details.
- Interaction: open evidence or related object.
- Effect: moves from capability summary to provenance.

### CUR-COMP-304 · Source / lens / reload controls
- Information: selected source/lens and reload/query posture.
- Treatment: local control cluster.
- Interaction: change admitted lens or refresh the dossier query.
- Effect: changes what exact capability evidence is being inspected without changing capability identity.

### CUR-COMP-305 · Dossier sections
- Information: performance, teaching, sources, dependencies, and history sections.
- Treatment: structured dossier sections with progressive disclosure.
- Interaction: navigate/expand section and inspect exact entries.
- Effect: groups evidence by operator question instead of presenting one undifferentiated wall.

### CUR-COMP-306 · Inline evidence detail / pagination
- Information: selected evidence entry, provenance, related objects, page/cursor state.
- Treatment: bounded inline detail.
- Interaction: paginate and traverse the capability-local evidence records/related objects exposed by the dossier.
- Effect: supports local investigation without losing exact evidence identity.

## CUR-VIEW-004 · Learning

Purpose: durable candidate transaction replay with retention, rollback, and evidence boundaries.

### CUR-COMP-401 · Episode/candidate list
- Information: episode/candidate identities and terminal states.
- Treatment: timeline/list/table.
- Interaction: select episode/candidate.
- Effect: updates selection/inspector.

### CUR-COMP-402 · Candidate transaction narrative
- Information: target capability, parent generation, teaching/assessment/retention phases, terminal outcome.
- Treatment: staged episode detail.
- Interaction: inspect evidence at each stage.
- Effect: explains what happened without converting evidence into unsupported causal claims.

### CUR-COMP-403 · Retention / rollback evidence
- Information: retention result, reason, rollback boundary, receipts.
- Treatment: state/evidence block.
- Interaction: open exact evidence.
- Effect: traces candidate outcome to durable custody.

### CUR-COMP-404 · Challenger vs committed comparison
- Information: before/after or challenger/committed state for the candidate transaction.
- Treatment: literal comparison table.
- Interaction: inspect compared values/evidence.
- Effect: shows the measured difference without converting it into a causal story.

### CUR-COMP-405 · Lifecycle replay stage controls
- Information: the currently inspected candidate stage and available replay stages.
- Treatment: ordered stage navigation.
- Interaction: move between admitted replay stages.
- Effect: repositions the transaction narrative while preserving the same episode/candidate identity.

## CUR-VIEW-005 · Atlas

Purpose: source-authoritative semantic identity and generation-scoped ABI state; learned similarity is a separate lens.

### CUR-COMP-501 · Semantic overview
- Information: semantic identities/classes and release-scoped overview.
- Treatment: atlas/table/graph surface.
- Interaction: select semantic object.
- Effect: opens semantic detail and relationships.

### CUR-COMP-502 · Semantic selection detail
- Information: exact identity, source/ABI relationships, generation context.
- Treatment: detail surface/inspector bridge.
- Interaction: inspect/open related object.
- Effect: preserves source-authoritative semantic navigation.

### CUR-COMP-503 · Semantic authority lens
- Information: derived similarity where available.
- Treatment: explicitly separate derived view.
- Interaction: compare/explore.
- Effect: prevents learned geometry from masquerading as semantic identity.

### CUR-COMP-504 · ABI bank map / row resolver
- Information: bank layout, ABI row identity, and exact row resolution.
- Treatment: structured map/table.
- Interaction: select bank/row and inspect exact identity.
- Effect: connects semantic identity to generation-scoped ABI placement.

### CUR-COMP-505 · Exact semantic identity lookup
- Information: exact semantic identifier and resolution result.
- Treatment: bounded lookup control plus result.
- Interaction: enter/select identity and resolve.
- Effect: provides direct identity access without requiring graph traversal.

## CUR-VIEW-006 · Model

Purpose: measured model/runtime mechanisms and exact frame compiler inspection.

### CUR-COMP-601 · Model local navigation
- Information: Neural Runtime / Frame Compiler Explorer peer surfaces and active subsection.
- Treatment: local peer-mode navigation.
- Interaction: switch between Neural Runtime and Frame Compiler Explorer.
- Effect: changes the Model working surface while preserving/restoring the correct shell or fixture context boundary.

### CUR-COMP-611 · Neural Runtime subview
- Information: the current neural diagnostic mode and all topology/runtime/CCGQA/AttnRes/refinement/instrumentation descendants.
- Treatment: Model peer subview selected through CUR-COMP-601.
- Interaction: local current/historical fixture-mode selection plus evidence controls in descendant diagnostics.
- Effect: scopes neural diagnostic state separately from Frame Compiler Explorer custody.

### CUR-COMP-602 · Neural topology/runtime summary
- Information: topology and measured runtime summary.
- Treatment: diagnostic panels.
- Interaction: inspect evidence.
- Effect: situates mechanism telemetry.

### CUR-COMP-603 · CCGQA / attention / AttnRes
- Information: routing, attention health, recorded mixture weights where fixture-backed.
- Treatment: diagnostic grids/bars/tables.
- Interaction: inspect recorded evidence.
- Effect: mechanism inspection only; no semantic interpretation upgrade.

### CUR-COMP-604 · Local refinement
- Information: eligibility, quotas, passes, density, resource cost.
- Treatment: histogram + analytical table.
- Interaction: inspect episode receipt.
- Effect: traces local refinement to evidence.

### CUR-COMP-605 · Instrumentation coverage
- Information: present/unavailable instrumentation and its source explanation.
- Treatment: static coverage list/status.
- Interaction: none directly in the current renderer.
- Effect: prevents synthesized absent metrics.

### CUR-COMP-606 · Frame Compiler Explorer
- Information: exact frame packing/unpacking receipts and causal visibility.
- Treatment: specialized frame surface.
- Interaction: inspect frame/receipt.
- Effect: exposes exact compiler behavior distinct from neural telemetry.

### CUR-COMP-607 · Frame generation / query status
- Information: frame query context, generation, request status, and selected example/frontier.
- Treatment: query/status header local to the frame surface.
- Interaction: choose fixture generation; after a page loads, choose an exact compiled example and its prediction frontier.
- Effect: establishes exact frame-inspection custody.

### CUR-COMP-608 · Compiled-example provenance / packing
- Information: exact compiled example, provenance, packing receipts, and constituent visibility.
- Treatment: receipt-oriented analytical detail.
- Interaction: inspect exact packing/provenance entries.
- Effect: explains how the example was compiled without borrowing authority from the live shell.

### CUR-COMP-609 · Prediction frontier / legality
- Information: prediction-frontier position and the resulting constituent/codec visibility projection.
- Treatment: frontier selector governing the position disclosures below it.
- Interaction: choose the prediction frontier; position/constituent rows themselves are not selectable.
- Effect: recalculates which source atoms and codec fields are legally visible at the selected frontier.

### CUR-COMP-610 · Aggregate packing disclosure
- Information: aggregate packing summary across the selected frame/example.
- Treatment: progressively disclosed summary beneath exact frame evidence.
- Interaction: expand/collapse aggregate detail.
- Effect: provides orientation without replacing receipt-level truth.

## CUR-VIEW-007 · Memory

Purpose: retained Engram allocation/retrieval/correction state without promoting memory hits to truth/capability authority.

### CUR-COMP-701 · Memory summary
- Information: capacity/allocation, hits/misses, hit/gate-use rates, footprint, read-site receipts.
- Treatment: metric summary.
- Interaction: none/inspect receipts.
- Effect: establishes operational memory posture.

### CUR-COMP-702 · Memory atlas pages
- Information: aggregate → page → stable motif allocation.
- Treatment: page controls + slot list.
- Interaction: choose page/slot.
- Effect: changes exact memory selection.

### CUR-COMP-703 · Motif inspector
- Information: key digest, semantic release, address, eligibility, lifetime use, parameter bank, correction state, source/evidence refs, related capabilities/episodes.
- Treatment: exact detail list.
- Interaction: inspect/open relations through global mechanisms.
- Effect: exposes retained identity and provenance.

### CUR-COMP-704 · Generation comparison
- Information: created/removed/held/requalified identities and allocation/hit/gate deltas.
- Treatment: comparison controls and delta grid.
- Interaction: choose comparison generation.
- Effect: shows literal memory change.

### CUR-COMP-705 · Rejected candidate boundary
- Information: proposed identity, parent preservation, lack of committed generation/slot.
- Treatment: proof block.
- Interaction: none.
- Effect: demonstrates that candidate-local allocation is not retained memory.

## CUR-VIEW-008 · Teacher

Purpose: strategy population, measured outcomes, cost/fidelity observations without unsupported ranking.

### CUR-COMP-801 · Strategy population
- Information: strategy identity/role/status, measured outcomes/cost scope, episode links, checkpoint-role history.
- Treatment: strategy roster and repeated strategy cards.
- Interaction: inspect a strategy identity through the shared inspector path; comparison selection belongs to CUR-COMP-802.
- Effect: exposes descriptive strategy evidence without changing strategy policy.

### CUR-COMP-802 · Outcome/cost comparison
- Information: selected strategy set, comparison scope, attempts/retained/gain/no-gain/interference, wall time, steps, and per-row coverage.
- Treatment: strategy/scope controls plus a comparative analytical table.
- Interaction: choose strategies and comparison scope; the comparison rows themselves do not expose evidence-inspection controls.
- Effect: recomputes the descriptive comparison without policy mutation or winner synthesis. Fidelity observations remain separately owned by CUR-COMP-803.

### CUR-COMP-803 · Fidelity ladder
- Information: strategy evidence at declared fidelity levels such as 2/4/8/16 where the current Teacher projection provides it.
- Treatment: bounded comparative ladder rather than an implied universal ranking.
- Interaction: select/compare supported strategy evidence.
- Effect: shows measured fidelity evidence at common scope.

### CUR-COMP-804 · Projection boundary
- Information: what the current Teacher snapshot does and does not establish.
- Treatment: concise local guidance with deeper technical detail behind disclosure.
- Interaction: inspect exact evidence.
- Effect: blocks descriptive strategy telemetry from becoming policy authority.

## CUR-VIEW-009 · SÍ SÉ SON

Purpose: independent Impact, Exigency, and Osmotic Novelty evidence with reversible aggregation and admitted routing rationale.

### CUR-COMP-906 · As-of fixture selector
- Information: the available retained salience snapshots and which exact snapshot is selected.
- Treatment: compact toolbar of mutually exclusive as-of fixture buttons.
- Interaction: choose a snapshot.
- Effect: re-renders all SÍ SÉ SON evidence, aggregation, provenance and routing panels against that exact selected snapshot.

### CUR-COMP-901 · Salience observation set
- Information: exact observations and three independent axes.
- Treatment: salience table/cards/plot.
- Interaction: select observation.
- Effect: opens exact salience detail.

### CUR-COMP-902 · Provenance
- Information: source/evidence identity for the selected salience observation.
- Treatment: compact provenance affordance with exact detail available.
- Interaction: inspect/open evidence.
- Effect: grounds the three salience axes.

### CUR-COMP-903 · Recursive aggregation
- Information: observation → window → cluster → pattern → trend aggregation where present, including constituent observation identity.
- Treatment: nested progressive disclosure rather than a single “score.”
- Interaction: expand/collapse disclosure levels and inspect constituent observations where buttons exist; there is no persistent selected-aggregation-level state.
- Effect: preserves reversibility and scale without promoting aggregation to source truth.

### CUR-COMP-904 · Routing rationale
- Information: recorded route identity, tier/rule, ordering keys, hidden-weighting posture, and cited observation identities.
- Treatment: derived routing records separated from source axes.
- Interaction: inspect cited observations when they are available in the selected as-of snapshot; the rationale record itself is static.
- Effect: explains admitted routing input without pretending aggregate is source truth or inferring private weights.

### CUR-COMP-905 · Projection boundary
- Information: projection schema, PARTIAL coverage, projected field inventory, and explicitly fixture-backed/non-first-class detail.
- Treatment: static local authority explanation.
- Interaction: none directly in the current renderer.
- Effect: prevents salience telemetry from being read as universal decision authority.

## CUR-VIEW-010 · Corrections

Purpose: correction blast radius, append-only correction history, receipt-backed requalification without implying perfect neural unlearning.

### CUR-COMP-1001 · Correction history
- Information: correction records and status.
- Treatment: chronology/list.
- Interaction: select correction.
- Effect: opens correction detail.

### CUR-COMP-1002 · Blast-radius graph/list
- Information: affected artifact classes and exposure paths.
- Treatment: graph/relationship surface with evidence references.
- Interaction: inspect affected node.
- Effect: traces known exposure.

### CUR-COMP-1003 · Accessible equivalent impact table
- Information: the same affected relationships required to understand the impact graph.
- Treatment: captioned/tabular equivalent.
- Interaction: select affected artifact.
- Effect: preserves the relationship model without requiring graph perception.

### CUR-COMP-1004 · Requalification state
- Information: receipts and requalification status.
- Treatment: evidence/status surface.
- Interaction: none in the current renderer; the queue is a static descriptive list.
- Effect: shows what has actually been requalified.

### CUR-COMP-1005 · Append-only correction history
- Information: correction/source/generation history and prior states.
- Treatment: chronological record.
- Interaction: none in the current renderer; the history is a static ordered record.
- Effect: preserves the record rather than replacing prior assertions in place.

## CUR-VIEW-011 · Lineage

Purpose: immutable accepted-generation lineage and literal structured generation differences.

### CUR-COMP-1101 · Accepted-generation lineage
- Information: accepted generation nodes, compact manifests, parent/transition relations, checkpoint facts, exact transitions, and tabular equivalent.
- Treatment: read-only lineage node set plus transition list/table.
- Interaction: select an accepted generation node; checkpoint is a relation/fact, not a selectable control.
- Effect: changes the exact generation dossier/inspection context.

### CUR-COMP-1102 · Generation comparison
- Information: literal structured differences.
- Treatment: diff/comparison surface.
- Interaction: select compared generations.
- Effect: shows change without “winner” synthesis.

### CUR-COMP-1103 · Rejected-candidate non-lineage boundary
- Information: candidate state that did not become accepted lineage.
- Treatment: explicit non-lineage proof/state.
- Interaction: inspect supporting evidence.
- Effect: prevents rejected candidate activity from appearing as an accepted generation.

### CUR-COMP-1104 · Exact immutable generation node
- Information: selected generation/transition state, full manifest and parent custody, manifest fields with source refs, stable deep link, and exact CP03 query identity.
- Treatment: static exact node dossier with a separate historical-missing defensive state.
- Interaction: no local evidence or comparison-endpoint control; comparison endpoints are owned by CUR-COMP-1102.
- Effect: anchors lineage navigation to immutable accepted custody and refuses current-generation substitution when historical identity is missing.

## CUR-VIEW-012 · Resources

Purpose: measured resource budgets, exact historical comparison, and spike correlation.

### CUR-COMP-1201 · Resource headline
- Information: projection provenance, page state, headline metric identities/semantic states/values/evidence-strength notes, and the throughput≠learning boundary.
- Treatment: static primary metric/status surface with an explicit no-current-projection defensive replacement.
- Interaction: none directly in the headline surface.
- Effect: establishes current resource condition without synthesizing absent measurements.

### CUR-COMP-1202 · Metric semantics
- Information: measured-value, configured-limit, and forecast/estimate semantic classes with values and explanatory notes.
- Treatment: static semantic metric grouping.
- Interaction: none directly.
- Effect: separates measured/configured/estimated quantities before the operator reads the numerical values.

### CUR-COMP-1203 · Memory decomposition / remainder
- Information: reconciliation state, measured memory categories, unresolved remainder, and aggregate-vs-allocated explanation.
- Treatment: static grouped decomposition with explicit COMPLETE/PARTIAL/UNAVAILABLE and remainder states.
- Interaction: none directly; exact resource-sample inspection belongs to CUR-COMP-1205.
- Effect: avoids pretending an unexplained total has been causally attributed.

### CUR-COMP-1204 · Compute/length profile
- Information: CPU/workers/snapshot/compile/MLX-wall/cost measurements plus sequence/frame/batch/length statistics.
- Treatment: static compute/preparation and sequence/batch/length metric groups.
- Interaction: none directly.
- Effect: decomposes resource cost without implying causal attribution.

### CUR-COMP-1205 · Timeline and spike correlation
- Information: resource samples related to episode/batch/checkpoint/preparation/refinement.
- Treatment: wide analytical table.
- Interaction: select resource sample.
- Effect: opens exact related evidence.

### CUR-COMP-1206 · Historical comparison
- Information: exact generation metric comparison and deltas.
- Treatment: generation form + comparison table.
- Interaction: load exact generation.
- Effect: read-only historical query; no generation is inferred.

## CUR-VIEW-013 · Evidence

Purpose: exact Admin Main Frame records, provenance links, bounded pagination, literal raw payloads.

### CUR-COMP-1301 · Evidence query/filter
- Information: query constraints/context.
- Treatment: bounded search/filter controls.
- Interaction: query/paginate.
- Effect: changes evidence result set.

### CUR-COMP-1305 · Query / degraded state
- Information: loading, ready, query-unavailable/error, page state, coverage, truncation, returned/total counts, and operator-facing error detail.
- Treatment: live status/alert surface immediately below the search controls.
- Interaction: none directly; state changes as bounded queries start/resolve/fail.
- Effect: exposes query health without converting missing/disconnected evidence into an empty successful result.

### CUR-COMP-1302 · Evidence results
- Information: exact record results plus exact page-relationship results and their hydration posture.
- Treatment: record buttons and relationship articles, not a tabular result grid.
- Interaction: select an exact record or hydrate an exact relationship target when one is projected.
- Effect: opens exact evidence detail while preserving current query/origin context.

### CUR-COMP-1306 · Traversal / omission status
- Information: degraded/omission markers from the evidence page plus provenance-link traversal failures.
- Treatment: passive omission/degraded marker section and explicit traversal alert.
- Interaction: none directly in these status surfaces; reference-search controls belong to CUR-COMP-1303 provenance refs and target-hydration controls belong to CUR-COMP-1302/1303 links.
- Effect: preserves partial/degraded evidence semantics and keeps unresolved provenance visible instead of silently dropping it.

### CUR-COMP-1303 · Exact record/raw payload
- Information: literal payload and provenance links.
- Treatment: details/raw view.
- Interaction: follow provenance/related object.
- Effect: forensic inspection; never rewritten into friendlier facts.

### CUR-COMP-1304 · Return to origin
- Information: originating destination/object where Evidence was opened contextually.
- Treatment: return affordance.
- Interaction: activate return.
- Effect: restores investigation path.

## CUR-VIEW-014 · Operate

Purpose: command boundary, not another dashboard.

### CUR-COMP-1401 · Action catalog
- Information: supported actions, mutation/read-only posture.
- Treatment: selectable action set.
- Interaction: choose action.
- Effect: initializes exact request form.

### CUR-COMP-1402 · Exact request
- Information: parameters and dry-run option.
- Treatment: structured JSON/input panel.
- Interaction: edit parameters; run read-only preflight.
- Effect: asks CP05 to resolve target/consequence without mutation.

### CUR-COMP-1403 · Preflight
- Information: target ref, run/generation, manifest/topology/factory/semantic/source/admission identities, resource profile, expected postcondition, stale conflicts.
- Treatment: resolved consequence panel.
- Interaction: review only.
- Effect: establishes exact authorization target or blocks stale context.

### CUR-COMP-1404 · Deliberate authorization
- Information: HUMAN GATE versus READ ONLY posture, reviewed target binding, exact authorization phrase where mutation is permitted, input state, and submit enablement.
- Treatment: high-salience authorization region for mutating commands and explicit read-only execution posture otherwise.
- Interaction: mutating commands require the exact phrase before submit; read-only commands do not use the phrase gate.
- Effect: dispatches only the reviewed exact target; target drift and authorization mismatch fail closed.

### CUR-COMP-1405 · Receipt/readback/reconciliation
- Information: operation ID, receipt state, postcondition/error refs, bounded logs, literal inspection.
- Treatment: lifecycle + receipt actions.
- Interaction: open receipt/postcondition; reconcile unknown outcome.
- Effect: proves outcome or preserves uncertainty without blind retry.

## Concern overlay

Every component above inherits the concern profile for its containing shell/view unless the node text states a stricter rule. This overlay records both **current implementation posture** and **required redesign posture**. It must not be read as claiming that localization/test-hook work already exists: as of the #1124 baseline, human-facing strings remain largely inline and Admin Main Frame has zero implemented `data-test-id` hooks.

| Scope | State concerns | Authority concerns | Accessibility concerns | Required i18n posture | Required test-hook posture |
| --- | --- | --- | --- | --- | --- |
| CUR-SHELL-001 / CUR-COMP-001..016 | CUR-STATE-001..009; route, selection, defensive, investigation, focus/display, fixture custody | Shell may display source/derived/operator-local facts but never upgrades their authority; mutation gating follows verified context | landmarks, skip link, roving navigation, dialog/inert semantics, focus return, live regions, target size, reduced motion/forced colors | all human labels, summaries, help, state explanations and recovery copy tokenized; machine IDs remain data | `shell-*`, `nav-destination-*`, `investigation-*`, `inspector-*`, `palette-*`; exact IDs unique |
| CUR-VIEW-001 Admin Main Frame / CUR-COMP-101..107 | live overview query families; startup projection; defensive projection; no historical event refresh | summary only; retained/current work/evidence distinctions remain explicit | heading/focus order, status non-color cues, inspectable summaries keyboard-reachable | all startup/overview questions, labels, health copy, attention guidance | `home-*` |
| CUR-VIEW-002 School / CUR-COMP-201..209 | matrix UI, curriculum mode, selected capability/node, filters/sort/page, context-bound async epoch | declared curriculum/topology and measured capability evidence stay distinct | matrix orientation, keyboard graph selection, equivalent relationship table, scale disclosure, scroll discoverability | filters, column labels, explanations, topology/scale guidance | `school-*`, `school-capability-row-*`, `curriculum-*` |
| CUR-VIEW-003 Capability Explorer / CUR-COMP-301..306 | selected capability, lens/source, cursor/page, evidence query epoch | measured chronology/source support only; no inferred causes | dossier navigation, bounded pagination, exact-value access, focus on loaded detail | section labels, helper copy, evidence controls | `capability-*`, `capability-evidence-*` |
| CUR-VIEW-004 Learning / CUR-COMP-401..405 | selected episode/candidate and replay stage | episode evidence, candidate state, retention/rollback custody remain separate | ordered stage controls, comparison tables, status announcements | stage labels, terminal/retention explanations, comparison labels | `learning-*`, `learning-stage-*` |
| CUR-VIEW-005 Atlas / CUR-COMP-501..505, 521 | overview/selection/lens/bank/request epoch | canonical semantic identity is source-authoritative; learned similarity remains derived | graph/table keyboard paths, exact lookup labels, nonvisual relationship access | lens/search/helper text tokenized; semantic IDs remain data | `atlas-*`, `atlas-semantic-*` |
| CUR-VIEW-006 Model / CUR-COMP-601..611 | model subsection, neural fixture mode, frame request epoch, saved return context | measured runtime vs fixture-backed diagnostics vs frame receipts remain explicit | peer-mode navigation, tables/progress readable by AT, fixture posture announced | diagnostic labels/help/state copy; raw IDs/receipts remain data | `model-*`, `neural-*`, `frame-*` |
| CUR-VIEW-007 Memory / CUR-COMP-701..705, 733 | generation, selected page/slot, compare generation | retrieval telemetry is operational evidence, never semantic/capability authority | page/slot controls, detail lists, comparison semantics, non-color held/rejected cues | labels/help/compare copy tokenized; stable motif IDs remain data | `memory-*`, `memory-slot-*` |
| CUR-VIEW-008 Teacher / CUR-COMP-801..804 | strategy roster, comparison strategy/scope selection, and static fidelity observations | descriptive strategy outcomes/cost/fidelity only; no unsupported winner/policy authority | strategy selection, comparison table/ladder reading order, state cues | strategy-role labels, comparison guidance, projection-boundary copy | `teacher-*`, `teacher-strategy-*` |
| CUR-VIEW-009 SÍ SÉ SON / CUR-COMP-901..906 | selected as-of snapshot plus transient observation inspection; aggregation disclosure is not persistent selection state | Impact, Exigency, Osmotic Novelty remain independent; aggregate/routing rationale derived | snapshot selector, axis labels not color-only, aggregation hierarchy navigable, evidence links named | snapshot labels, axis names/explanations/rationale labels tokenized; source IDs remain data | `salience-*`, `salience-observation-*` |
| CUR-VIEW-010 Corrections / CUR-COMP-1001..1005 | selected correction/affected artifact/requalification state | known exposure and receipt-backed requalification only; no perfect-unlearning claim | graph has equivalent table, history order explicit, state cues non-color | correction/requalification/history guidance tokenized | `corrections-*`, `correction-artifact-*` |
| CUR-VIEW-011 Lineage / CUR-COMP-1101..1104 | selected generation/checkpoint and diff endpoints | accepted immutable lineage only; rejected candidates explicitly excluded | DAG/table equivalence, exact node inspection, diff table orientation | lineage/diff guidance tokenized; hashes/checkpoints remain data | `lineage-*`, `lineage-generation-*` |
| CUR-VIEW-012 Resources / CUR-COMP-1201..1206 | current projection, exact comparison generation, resource-only live refresh | measured/derived/estimated/unavailable distinctions preserved; correlation is not causation | metric units/denominators announced, wide tables own overflow, comparison forms labeled | metric labels/units/help/status copy tokenized | `resources-*`, `resource-sample-*` |
| CUR-VIEW-013 Evidence / CUR-COMP-1301..1306 | criteria/page/results/selection/raw/traversal/query epoch; degraded/query/traversal failures | literal evidence/provenance is primary; raw payload may stay technical; missing/degraded records remain explicit | search/pagination/detail semantics, live query/traversal status, raw payload readable, explicit return origin | controls, states and explanations tokenized; literal payload/identifiers not translated | `evidence-*`, `evidence-record-*` |
| CUR-VIEW-014 Operate / CUR-COMP-1400..1405 | command phase, target conflicts, authorization, operation readback | CP05 exact target/consequence/receipt authority; unknown outcome remains unknown | deliberate gate focus/order, error association, no hidden mutation, receipt/readback announcements | action/help/error/reconciliation copy tokenized; exact target/operation IDs remain data | `operate-*`, `operate-action-*` |

For repeated elements, exact IDs are never duplicated. Repeated rows/nodes use a documented prefix plus a stable identity suffix. Functional `data-*` attributes used by runtime behavior are not substitutes for these test hooks.

## Atlas-derived task groups for later navigation design

These are design hypotheses for decomposition, not authorization to change navigation yet:

1. **Overview & learning**: CUR-VIEW-001 Admin Main Frame, CUR-VIEW-002 School, CUR-VIEW-003 Capability Explorer, CUR-VIEW-004 Learning.
2. **Representation & mechanisms**: CUR-VIEW-005 Atlas, CUR-VIEW-006 Model, CUR-VIEW-007 Memory.
3. **Decision & correction**: CUR-VIEW-008 Teacher, CUR-VIEW-009 SÍ SÉ SON, CUR-VIEW-010 Corrections.
4. **Provenance & operations**: CUR-VIEW-011 Lineage, CUR-VIEW-012 Resources, CUR-VIEW-013 Evidence, CUR-VIEW-014 Operate.

Any final grouping must be tested against real operator journeys and must preserve direct command-palette/deep-link access.

## Recursive current-renderer constituent outlines

These outlines preserve the source-grounded recursion discovered in the current renderer. They are migration evidence only. A target-state element survives only if `INFORMATION_ATLAS.md` intentionally retains or transforms it.

### CUR-SHELL-001 · Application shell

- CUR-SHELL-001 Application shell
  - CUR-COMP-015 Skip-to-main access path
    - CUR-COMP-015.1 Skip to main content link control
    - CUR-COMP-015.2 main-content focus target effect-target
    - CUR-COMP-015.3 hidden-until-focus treatment
  - CUR-COMP-001 Primary navigation rail
    - CUR-COMP-001.1 Brand identity
      - CUR-COMP-001.1.1 B brand mark datum
      - CUR-COMP-001.1.2 Bilqis product name datum
      - CUR-COMP-001.1.3 Admin Main Frame subtitle datum
    - CUR-COMP-001.2 Destination navigator
      - CUR-COMP-001.2.01 Admin Main Frame control-instance
      - CUR-COMP-001.2.02 School control-instance
      - CUR-COMP-001.2.03 Capability Explorer control-instance
      - CUR-COMP-001.2.04 Learning control-instance
      - CUR-COMP-001.2.05 Atlas control-instance
      - CUR-COMP-001.2.06 Model control-instance
      - CUR-COMP-001.2.07 Memory control-instance
      - CUR-COMP-001.2.08 Teacher control-instance
      - CUR-COMP-001.2.09 SI SE SON control-instance
      - CUR-COMP-001.2.10 Corrections control-instance
      - CUR-COMP-001.2.11 Lineage control-instance
      - CUR-COMP-001.2.12 Resources control-instance
      - CUR-COMP-001.2.13 Evidence control-instance
      - CUR-COMP-001.2.14 Operate control-instance
    - CUR-COMP-001.3 Destination interaction-state contract
      - CUR-COMP-001.3.1 aria-current active-page state
      - CUR-COMP-001.3.2 availability and Operate mutation gate state
      - CUR-COMP-001.3.3 click navigation and title-focus effect
      - CUR-COMP-001.3.4 roving Arrow Home End keyboard interaction
    - CUR-COMP-001.4 Command utility trigger
      - CUR-COMP-001.4.1 Command label datum
      - CUR-COMP-001.4.2 CmdK CtrlK shortcut hint datum
      - CUR-COMP-001.4.3 click-open palette effect
    - CUR-COMP-001.5 Rail treatment states
      - CUR-COMP-001.5.1 desktop sticky full-height scroll treatment
      - CUR-COMP-001.5.2 <=980 first-letter collapsed-label treatment
  - CUR-COMP-002 Context bar
    - CUR-COMP-002.1 Identity cluster
      - CUR-COMP-002.1.1 mode-posture badge datum-state
      - CUR-COMP-002.1.2 run identity datum
      - CUR-COMP-002.1.3 generation-manifest identity datum
    - CUR-COMP-002.2 Context fact grid
      - CUR-COMP-002.2.1 visible-hidden context-grid state
      - CUR-COMP-002.2.2 Service bootstrap fact datum
      - CUR-COMP-002.2.3 Learner bootstrap fact datum
      - CUR-COMP-002.2.4 Optimizer bootstrap fact datum
      - CUR-COMP-002.2.5 Telemetry bootstrap fact datum
      - CUR-COMP-002.2.6 Topology datum
      - CUR-COMP-002.2.7 Factory release datum
      - CUR-COMP-002.2.8 Semantic release datum
      - CUR-COMP-002.2.9 Optimizer datum
      - CUR-COMP-002.2.10 Admission lease datum
      - CUR-COMP-002.2.11 Correction frontier datum
      - CUR-COMP-002.2.12 Resource health datum
      - CUR-COMP-002.2.13 Coverage datum
    - CUR-COMP-002.3 Context actions
      - CUR-COMP-002.3.1 Run selector disabled single-option control
      - CUR-COMP-002.3.2 As-of generation selector control
      - CUR-COMP-002.3.3 generation-change to historical-lens effect
      - CUR-COMP-002.3.4 freshness badge datum-state
      - CUR-COMP-002.3.5 density cycle control-effect
      - CUR-COMP-002.3.6 theme toggle control-effect
    - CUR-COMP-002.4 Context posture treatment
      - CUR-COMP-002.4.1 verified-vs-empty layout state
      - CUR-COMP-002.4.2 live treatment
      - CUR-COMP-002.4.3 historical pattern-double-border treatment
      - CUR-COMP-002.4.4 stale dashed treatment
      - CUR-COMP-002.4.5 unknown dotted treatment
    - CUR-COMP-002.5 Responsive context layouts
      - CUR-COMP-002.5.1 >1320 three-column treatment
      - CUR-COMP-002.5.2 981-1320 second-row facts treatment
      - CUR-COMP-002.5.3 <=980 wrapped two-column treatment
      - CUR-COMP-002.5.4 <=640 single-column treatment
  - CUR-COMP-003 Global investigation strip
    - CUR-COMP-003.1 toolbar row layout host treatment
    - CUR-COMP-003.2 disclosed panel host state
    - CUR-COMP-003.3 stable object-ref projection contract
    - CUR-COMP-003.4 global selected-related highlight interaction-effect
    - CUR-COMP-003.5 inspector-open geometry effect
    - CUR-COMP-010 Time lens
      - CUR-COMP-010.1 exact generation number input control
      - CUR-COMP-010.2 Apply historical control
      - CUR-COMP-010.3 Use verified current control-state
      - CUR-COMP-010.4 invalid-generation announcement state
      - CUR-COMP-010.5 historical lens mutation-disable effect
      - CUR-COMP-010.6 verified-current restore effect
    - CUR-COMP-011 Compare workspace
      - CUR-COMP-011.1 Compare toggle and slot count control
      - CUR-COMP-011.2 left stable-ref slot and Clear control
      - CUR-COMP-011.3 right stable-ref slot and Clear control
      - CUR-COMP-011.4 comparison doctrine-status datum
      - CUR-COMP-011.5 Dimension Left Right State table treatment
      - CUR-COMP-011.6 mismatch-unavailable reason datum
      - CUR-COMP-011.7 comparison adapter-state contract
    - CUR-COMP-012 Pins
      - CUR-COMP-012.1 Pins toggle and count control
      - CUR-COMP-012.2 empty-pins state
      - CUR-COMP-012.3 pin list
        - CUR-COMP-012.3.1 kind-generation datum
        - CUR-COMP-012.3.2 label-run datum
        - CUR-COMP-012.3.3 Open exact pin control-effect
        - CUR-COMP-012.3.4 Remove pin control-effect
      - CUR-COMP-012.4 local persistence identity-limit contract
      - CUR-COMP-012.5 open-pin historical rehydration effect
    - CUR-COMP-013 Annotations
      - CUR-COMP-013.1 Notes toggle and count control
      - CUR-COMP-013.2 exact-context filter state
      - CUR-COMP-013.3 empty-note state
      - CUR-COMP-013.4 note list
        - CUR-COMP-013.4.1 non-authoritative marker datum
        - CUR-COMP-013.4.2 author timestamp scope datum
        - CUR-COMP-013.4.3 note body datum
        - CUR-COMP-013.4.4 exact target identity datum
      - CUR-COMP-013.5 annotation form
        - CUR-COMP-013.5.1 target label datum
        - CUR-COMP-013.5.2 required max-2000 textarea control
        - CUR-COMP-013.5.3 local-authority disclaimer datum
        - CUR-COMP-013.5.4 Save note control
        - CUR-COMP-013.5.5 no-selection prompt state
      - CUR-COMP-013.6 validation-save announcement effect
      - CUR-COMP-013.7 local persistence schema-limit-authority contract
      - CUR-COMP-013.8 persistence-failure announcement effect
    - CUR-COMP-014 App URI and deep link
      - CUR-COMP-014.1 no-selection prompt state
      - CUR-COMP-014.2 Exact app URI label datum
      - CUR-COMP-014.3 rendered bilqis URI datum
      - CUR-COMP-014.4 URI run-generation-kind-id-fixture construction contract
      - CUR-COMP-014.5 object-kind owner resolution contract
      - CUR-COMP-014.6 URI hydration to historical selection effect
      - CUR-COMP-014.7 hash route serialization contract
      - CUR-COMP-014.8 hash parsing-hydration contract
      - CUR-COMP-014.9 hashchange rerender effect
      - CUR-COMP-014.10 replaceState hash-sync effect
      - CUR-COMP-014.11 Model subsection derivation contract
  - CUR-COMP-004 Defensive-state banner
    - CUR-COMP-004.1 visibility and status-alert role state
    - CUR-COMP-004.2 bootstrap title-description-run-generation-error payload datum
    - CUR-COMP-004.3 bootstrap phases
      - CUR-COMP-004.3.1 connecting state
      - CUR-COMP-004.3.2 discovering state
      - CUR-COMP-004.3.3 telemetry-pending state
      - CUR-COMP-004.3.4 learner-unavailable state
      - CUR-COMP-004.3.5 failed state
    - CUR-COMP-004.4 ready defensive label-description-source-mutation payload datum
    - CUR-COMP-004.5 defensive profile family
      - CUR-COMP-004.5.01 live
      - CUR-COMP-004.5.02 loading
      - CUR-COMP-004.5.03 progressive
      - CUR-COMP-004.5.04 empty
      - CUR-COMP-004.5.05 stale
      - CUR-COMP-004.5.06 partial
      - CUR-COMP-004.5.07 offline
      - CUR-COMP-004.5.08 denied
      - CUR-COMP-004.5.09 revoked
      - CUR-COMP-004.5.10 unavailable
      - CUR-COMP-004.5.11 incompatible-version
      - CUR-COMP-004.5.12 timeout
      - CUR-COMP-004.5.13 duplicate-action
      - CUR-COMP-004.5.14 session-restarting
      - CUR-COMP-004.5.15 service-restarting
      - CUR-COMP-004.5.16 historical-unavailable
      - CUR-COMP-004.5.17 malformed-payload
      - CUR-COMP-004.5.18 unsupported-payload
      - CUR-COMP-004.5.19 outcome-unknown
      - CUR-COMP-004.5.20 unknown
    - CUR-COMP-004.6 reconnect availability gate state
    - CUR-COMP-004.7 Reconnect control
    - CUR-COMP-004.8 reconnect transition
      - CUR-COMP-004.8.1 reset frame custody-disable mutation effect
      - CUR-COMP-004.8.2 preserve route effect
      - CUR-COMP-004.8.3 loading-connecting render effect
      - CUR-COMP-004.8.4 CP01 connect-discover interaction
      - CUR-COMP-004.8.5 OperatorView validate-cache effect
      - CUR-COMP-004.8.6 validated cache fallback effect
      - CUR-COMP-004.8.7 live-no-projection progressive branch
      - CUR-COMP-004.8.8 total-failure defensive branch
      - CUR-COMP-004.8.9 verified-success branch
      - CUR-COMP-004.8.10 recovery announcement effect
    - CUR-COMP-004.9 bounded validated OperatorView cache contract
    - CUR-COMP-004.10 non-color dashed-double-dotted treatment families
  - CUR-COMP-005 Destination header
    - CUR-COMP-005.1 Current destination eyebrow datum
    - CUR-COMP-005.2 dynamic destination H1 datum-focus-target
    - CUR-COMP-005.3 dynamic purpose-boundary summary datum
    - CUR-COMP-005.4 aria-labelledby host relationship contract
    - CUR-COMP-005.5 post-navigation title-focus effect
  - CUR-COMP-006 Destination-local subnavigation
    - CUR-COMP-006.1 Model-only visibility gate state
    - CUR-COMP-006.2 Neural Runtime control
    - CUR-COMP-006.3 Frame Compiler Explorer control
    - CUR-COMP-006.4 aria-pressed subsection state
    - CUR-COMP-006.5 subsection-switch clear-selection effect
    - CUR-COMP-006.6 route-derived subsection contract
    - CUR-COMP-006.7 frame context-custody save-install-restore contract
  - CUR-COMP-007 Global inspector
    - CUR-COMP-007.1 open-closed inert aria-hidden slide state-treatment
    - CUR-COMP-007.2 Global inspector eyebrow datum
    - CUR-COMP-007.3 selected title or No selection datum
    - CUR-COMP-007.4 Close control
    - CUR-COMP-007.5 exact detail list
      - CUR-COMP-007.5.1 object class datum
      - CUR-COMP-007.5.2 identity datum
      - CUR-COMP-007.5.3 posture datum
      - CUR-COMP-007.5.4 generation datum
      - CUR-COMP-007.5.5 evidence posture datum
      - CUR-COMP-007.5.6 domain supplied details datum-family
    - CUR-COMP-007.6 action group
      - CUR-COMP-007.6.1 Open in owning view control
      - CUR-COMP-007.6.2 Open evidence control
      - CUR-COMP-007.6.3 Pin-Unpin control
      - CUR-COMP-007.6.4 Compare left control
      - CUR-COMP-007.6.5 Compare right control
      - CUR-COMP-007.6.6 Add operator note control
    - CUR-COMP-007.7 action enablement and pin-label state
    - CUR-COMP-007.8 open capture-focus announce effect
    - CUR-COMP-007.9 close restore-focus Escape effect
    - CUR-COMP-007.10 owner navigation effect
    - CUR-COMP-007.11 Evidence origin-preservation effect
    - CUR-COMP-007.12 pin-compare-note interaction effects
    - CUR-COMP-007.13 fixed side-plane geometry treatment
  - CUR-COMP-008 Command palette
    - CUR-COMP-008.1 modal dialog-backdrop treatment
    - CUR-COMP-008.2 Keyboard navigation eyebrow datum
    - CUR-COMP-008.3 Command palette title datum
    - CUR-COMP-008.4 Close control
    - CUR-COMP-008.5 destination-jump mutation-gate guidance datum
    - CUR-COMP-008.6 destination option family
      - CUR-COMP-008.6.01 Admin Main Frame
      - CUR-COMP-008.6.02 School
      - CUR-COMP-008.6.03 Capability Explorer
      - CUR-COMP-008.6.04 Learning
      - CUR-COMP-008.6.05 Atlas
      - CUR-COMP-008.6.06 Model
      - CUR-COMP-008.6.07 Memory
      - CUR-COMP-008.6.08 Teacher
      - CUR-COMP-008.6.09 SI SE SON
      - CUR-COMP-008.6.10 Corrections
      - CUR-COMP-008.6.11 Lineage
      - CUR-COMP-008.6.12 Resources
      - CUR-COMP-008.6.13 Evidence
      - CUR-COMP-008.6.14 Operate
    - CUR-COMP-008.7 null-shell and Operate availability state
    - CUR-COMP-008.8 global CmdK CtrlK interaction
    - CUR-COMP-008.9 open capture-focus first-enabled effect
    - CUR-COMP-008.10 roving Arrow Home End interaction
    - CUR-COMP-008.11 option activation navigate-close-focus effect
    - CUR-COMP-008.12 explicit-native close interaction
    - CUR-COMP-008.13 close focus-restoration effect
  - CUR-COMP-009 Fixture provenance boundary
    - CUR-COMP-009.1 independent-fixture context note
      - CUR-COMP-009.1.1 provenance warning datum
      - CUR-COMP-009.1.2 School-Learning-Model-Memory-Teacher visibility state
    - CUR-COMP-009.2 Reference fixture card
      - CUR-COMP-009.2.1 status-dot treatment
      - CUR-COMP-009.2.2 Reference fixture label datum
      - CUR-COMP-009.2.3 test-reference disclaimer datum
      - CUR-COMP-009.2.4 demo inspect action family
        - CUR-COMP-009.2.4.01 capability
        - CUR-COMP-009.2.4.02 episode
        - CUR-COMP-009.2.4.03 semantic
        - CUR-COMP-009.2.4.04 frame
        - CUR-COMP-009.2.4.05 memory
        - CUR-COMP-009.2.4.06 checkpoint
        - CUR-COMP-009.2.4.07 evidence
        - CUR-COMP-009.2.4.08 correction
        - CUR-COMP-009.2.4.09 warning
      - CUR-COMP-009.2.5 demo inspect to global-inspector effect
    - CUR-COMP-009.3 visual-language catalog reference surface
    - CUR-COMP-009.4 mapped-fallback-Operate visibility override state
  - CUR-COMP-016 Polite live announcer
    - CUR-COMP-016.1 sr-only aria-live atomic region treatment
    - CUR-COMP-016.2 clear-then-microtask repeated-message announcement effect

### CUR-VIEW-001 · Admin Main Frame

- CUR-VIEW-001 Admin Main Frame
  - CUR-COMP-107 Startup state
    - CUR-COMP-107.1 startup posture narrative datum
    - CUR-COMP-107.2 startup fact set
      - CUR-COMP-107.2.1 accepted generation datum
      - CUR-COMP-107.2.2 optimizer step datum
      - CUR-COMP-107.2.3 trainer running-stopped-unknown state
      - CUR-COMP-107.2.4 stage datum
      - CUR-COMP-107.2.5 learning telemetry waiting-none state
    - CUR-COMP-107.3 next-step Operate-CLI guidance datum
  - CUR-COMP-101 Learner posture
    - CUR-COMP-101.1 provenance and learning verdict datum-state
    - CUR-COMP-101.2 five-question strip
      - CUR-COMP-101.2.1 RUNNING datum
      - CUR-COMP-101.2.2 LEARNING datum
      - CUR-COMP-101.2.3 WORK datum
      - CUR-COMP-101.2.4 REGRESSION datum
      - CUR-COMP-101.2.5 INVALIDITY datum
  - CUR-COMP-104 Health strip
    - CUR-COMP-104.1 Learning card
      - CUR-COMP-104.1.1 latest school score datum
      - CUR-COMP-104.1.2 best school score datum
      - CUR-COMP-104.1.3 whole-school growth datum
      - CUR-COMP-104.1.4 G-RTN datum
      - CUR-COMP-104.1.5 P-RET datum
      - CUR-COMP-104.1.6 retained optimizer steps datum
      - CUR-COMP-104.1.7 capability-state badge datum-state
    - CUR-COMP-104.2 Curriculum card
      - CUR-COMP-104.2.1 qualified capabilities datum
      - CUR-COMP-104.2.2 observed debt datum
      - CUR-COMP-104.2.3 active concepts datum
      - CUR-COMP-104.2.4 ready datum
      - CUR-COMP-104.2.5 held datum
      - CUR-COMP-104.2.6 implementation-uncovered datum
      - CUR-COMP-104.2.7 school-state badge datum-state
    - CUR-COMP-104.3 Runtime card
      - CUR-COMP-104.3.1 elapsed datum
      - CUR-COMP-104.3.2 visits datum
      - CUR-COMP-104.3.3 visit rate datum
      - CUR-COMP-104.3.4 retained candidates datum
      - CUR-COMP-104.3.5 rejected candidates datum
      - CUR-COMP-104.3.6 accepted steps per hour datum
      - CUR-COMP-104.3.7 run-state badge datum-state
    - CUR-COMP-104.4 System card
      - CUR-COMP-104.4.1 unified memory pressure datum
      - CUR-COMP-104.4.2 peak memory datum
      - CUR-COMP-104.4.3 disk reserve datum
      - CUR-COMP-104.4.4 correction-requal debt datum
      - CUR-COMP-104.4.5 hard warnings datum
      - CUR-COMP-104.4.6 resource-state badge datum-state
  - CUR-COMP-102 Learning pulse
    - CUR-COMP-102.1 pulse header and event-count datum
    - CUR-COMP-102.2 repeated event action family
      - CUR-COMP-102.2.1 event kind datum
      - CUR-COMP-102.2.2 event label datum
      - CUR-COMP-102.2.3 event detail datum
      - CUR-COMP-102.2.4 inspect target control-effect
    - CUR-COMP-102.3 no-evidenced-events state
  - CUR-COMP-105 Current work
    - CUR-COMP-105.1 OBSERVED-UNAVAILABLE header state
    - CUR-COMP-105.2 transaction identity facts
      - CUR-COMP-105.2.1 target capability datum
      - CUR-COMP-105.2.2 strategy datum
      - CUR-COMP-105.2.3 candidate intent datum
      - CUR-COMP-105.2.4 source family datum
    - CUR-COMP-105.3 assessment facts
      - CUR-COMP-105.3.1 target assessment datum
      - CUR-COMP-105.3.2 protected assessment datum
  - CUR-COMP-106 Compact School map
    - CUR-COMP-106.1 header and row-count datum
    - CUR-COMP-106.2 capability table
      - CUR-COMP-106.2.1 capability identity drill-through control
      - CUR-COMP-106.2.2 Now datum
      - CUR-COMP-106.2.3 Best datum
      - CUR-COMP-106.2.4 Delta datum
      - CUR-COMP-106.2.5 Debt datum
      - CUR-COMP-106.2.6 Retention datum
      - CUR-COMP-106.2.7 Status datum
  - CUR-COMP-103 Actionable attention
    - CUR-COMP-103.1 attention count datum
    - CUR-COMP-103.2 repeated actionable item family
      - CUR-COMP-103.2.1 kind datum
      - CUR-COMP-103.2.2 label datum
      - CUR-COMP-103.2.3 detail datum
      - CUR-COMP-103.2.4 inspect target control-effect
    - CUR-COMP-103.3 no-actionable-concerns state

### CUR-VIEW-002 · School

- CUR-VIEW-002 School
  - CUR-COMP-204 Peer subnavigation
    - CUR-COMP-204.1 Capability matrix control
    - CUR-COMP-204.2 Curriculum Semantic Atlas control
    - CUR-COMP-204.3 current-peer state
  - CUR-COMP-201 Capability matrix
    - CUR-COMP-207 Matrix controls
      - CUR-COMP-207.1 filter-set controls
      - CUR-COMP-207.2 Group by family control
      - CUR-COMP-207.3 Export displayed identities control-effect
      - CUR-COMP-207.4 sortable header controls
      - CUR-COMP-207.5 previous-next pagination controls
    - CUR-COMP-201.1 matrix coverage and range datum
    - CUR-COMP-201.2 metric-definition guidance datum
    - CUR-COMP-201.3 matrix table
      - CUR-COMP-201.3.1 family grouping row datum
      - CUR-COMP-201.3.2 capability identity select control
      - CUR-COMP-201.3.3 WAS-TOP-NOW-ALL-growth-debt-retention metrics datum-family
      - CUR-COMP-201.3.4 visits-retained-last-gain-last-regression datum-family
      - CUR-COMP-201.3.5 strategy-source-family datum-family
      - CUR-COMP-201.3.6 source-implementation-qualification state stack
  - CUR-COMP-202 Dependency graph
    - CUR-COMP-202.1 graph-vs-table toggle control
    - CUR-COMP-202.2 legend and screen-reader operation guidance
    - CUR-COMP-202.3 graph canvas
      - CUR-COMP-202.3.1 prerequisite-dependent edge family
      - CUR-COMP-202.3.2 capability node family
        - CUR-COMP-202.3.2.1 identity datum
        - CUR-COMP-202.3.2.2 lifecycle-eligibility-mastery-debt state datum
        - CUR-COMP-202.3.2.3 keyboard-pointer select interaction
    - CUR-COMP-202.4 equivalent dependency table
      - CUR-COMP-202.4.1 relation datum
      - CUR-COMP-202.4.2 capability identity datum
  - CUR-COMP-203 Curriculum semantic atlas
    - CUR-COMP-203.1 fixture-context provenance boundary datum
    - CUR-COMP-205 Curriculum controls
      - CUR-COMP-205.1 search-find control
      - CUR-COMP-205.2 Jump to active control
      - CUR-COMP-205.3 prerequisite-both-unlocks trace-mode controls
      - CUR-COMP-205.4 grade-state-family-attention-new-only filter controls
      - CUR-COMP-205.5 Reset-focus-all control
      - CUR-COMP-205.6 async search-trace live status
    - CUR-COMP-203.2 Topology panel
      - CUR-COMP-203.2.1 legend and declared-edge doctrine datum
      - CUR-COMP-203.2.2 foundation-current-forward grade strata treatment
      - CUR-COMP-203.2.3 declared prerequisite edge canvas
      - CUR-COMP-203.2.4 curriculum node family
        - CUR-COMP-203.2.4.1 capability identity datum
        - CUR-COMP-203.2.4.2 semantic label-ID-authority datum
        - CUR-COMP-203.2.4.3 grade-lifecycle-qualification datum
        - CUR-COMP-203.2.4.4 NOW-TOP-debt datum
        - CUR-COMP-203.2.4.5 blocker-state datum
        - CUR-COMP-203.2.4.6 select interaction
      - CUR-COMP-203.2.5 prerequisite-dependent relationship summary datum
    - CUR-COMP-206 Selected-node dossier
      - CUR-COMP-206.1 identity-state header datum
      - CUR-COMP-206.2 identity-metrics-provenance fact list
      - CUR-COMP-206.3 Why blocked rationale datum-state
      - CUR-COMP-206.4 bounded event history datum-family
      - CUR-COMP-206.5 downstream-consequence disclosure control-state
      - CUR-COMP-206.6 canonical semantic binding resolver control-state-effect
      - CUR-COMP-206.7 cross-view School-Capability-Atlas-Lineage-Evidence actions
    - CUR-COMP-208 Semantic equivalent table
      - CUR-COMP-208.1 row family
        - CUR-COMP-208.1.1 capability select control
        - CUR-COMP-208.1.2 semantic identity datum
        - CUR-COMP-208.1.3 grade-state datum
        - CUR-COMP-208.1.4 prerequisite-dependent datum
        - CUR-COMP-208.1.5 evidence datum
    - CUR-COMP-209 Scale disclosure
      - CUR-COMP-209.1 243-row grade-family summary disclosure
      - CUR-COMP-209.2 family focus control
      - CUR-COMP-209.3 bounded family expansion
      - CUR-COMP-209.4 selected semantic prerequisite-dependent datum
      - CUR-COMP-209.5 bounded transitive-unlocks datum-state

### CUR-VIEW-003 · Capability Explorer

- CUR-VIEW-003 Capability Explorer
  - CUR-COMP-304 Source-lens controls
    - CUR-COMP-304.1 data-source selector control
    - CUR-COMP-304.2 exact Run Generation Capability as-of form control
  - CUR-COMP-301 Capability identity-header
    - CUR-COMP-301.1 dossier status-provenance notice datum-state
    - CUR-COMP-301.2 exact name and capability ID datum
    - CUR-COMP-301.3 Reload dossier control-effect
    - CUR-COMP-301.4 Load more capabilities cursor control-effect
  - CUR-COMP-302 Measurements and history
    - CUR-COMP-302.1 metric strip
      - CUR-COMP-302.1.1 NOW datum-origin
      - CUR-COMP-302.1.2 TOP datum-origin
      - CUR-COMP-302.1.3 Total datum-origin
      - CUR-COMP-302.1.4 Debt datum-origin
      - CUR-COMP-302.1.5 Retention datum-origin
      - CUR-COMP-302.1.6 Eligibility datum-origin
      - CUR-COMP-302.1.7 Qualification datum-origin
      - CUR-COMP-302.1.8 Source datum-origin
    - CUR-COMP-302.2 Learning-history chronology
  - CUR-COMP-305 Dossier sections
    - CUR-COMP-305.1 section navigation controls
    - CUR-COMP-305.2 performance section
    - CUR-COMP-305.3 teaching section
    - CUR-COMP-305.4 sources section
    - CUR-COMP-305.5 dependencies section
    - CUR-COMP-305.6 history section
    - CUR-COMP-305.7 repeated dossier-entry family
      - CUR-COMP-305.7.1 entry kind-label-generation-time datum
      - CUR-COMP-305.7.2 fact list with origin-state datum-family
      - CUR-COMP-305.7.3 evidence-related-object disclosure controls
  - CUR-COMP-303 Source-evidence layer
    - CUR-COMP-303.1 exact dossier identity-provenance disclosure
    - CUR-COMP-303.2 projection marker disclosure
  - CUR-COMP-306 Inline evidence detail
    - CUR-COMP-306.1 evidence identity-query state datum
    - CUR-COMP-306.2 selected entry literal payload datum
    - CUR-COMP-306.3 evidence-link family
      - CUR-COMP-306.3.1 record-family selector control
      - CUR-COMP-306.3.2 exact-record traversal control-effect
    - CUR-COMP-306.4 next-page evidence-links control-effect
    - CUR-COMP-306.5 returned-record payload datum

### CUR-VIEW-004 · Learning

- CUR-VIEW-004 Learning
  - CUR-COMP-401 Episode selector
    - CUR-COMP-401.1 repeated episode option
      - CUR-COMP-401.1.1 CP03 record identity datum
      - CUR-COMP-401.1.2 capability datum
      - CUR-COMP-401.1.3 terminal state datum
      - CUR-COMP-401.1.4 retention reason datum
      - CUR-COMP-401.1.5 choose-episode interaction-effect
  - CUR-COMP-401.2 exact CP03 record deep-link datum
  - CUR-COMP-402 Candidate transaction
    - CUR-COMP-402.1 episode identity and terminal header datum-state
    - CUR-COMP-402.2 Inspect candidate control-effect
    - CUR-COMP-402.3 custody facts
      - CUR-COMP-402.3.1 candidate ID datum
      - CUR-COMP-402.3.2 CP03 record ID datum
      - CUR-COMP-402.3.3 target capability datum
      - CUR-COMP-402.3.4 parent generation datum
    - CUR-COMP-402.4 teaching-work facts
      - CUR-COMP-402.4.1 strategy datum
      - CUR-COMP-402.4.2 source family datum
      - CUR-COMP-402.4.3 lesson family datum
      - CUR-COMP-402.4.4 intended-attempted-retained steps datum
    - CUR-COMP-402.5 terminal-resource facts
      - CUR-COMP-402.5.1 duration datum
      - CUR-COMP-402.5.2 command state datum
      - CUR-COMP-402.5.3 retention reason datum
      - CUR-COMP-402.5.4 peak memory datum
      - CUR-COMP-402.5.5 step rate datum
      - CUR-COMP-402.5.6 resource coverage datum
  - CUR-COMP-403 Retention-rollback evidence
    - CUR-COMP-403.1 retained accepted-generation transition state-datum
    - CUR-COMP-403.2 pending-unknown reconciliation state
    - CUR-COMP-403.3 rejected classification and reason state-datum
    - CUR-COMP-403.4 rollback invariant proof grid
      - CUR-COMP-403.4.1 parent neural identity unchanged datum
      - CUR-COMP-403.4.2 parent optimizer identity unchanged datum
      - CUR-COMP-403.4.3 parent allocation identity unchanged datum
      - CUR-COMP-403.4.4 retained optimizer steps zero datum
      - CUR-COMP-403.4.5 child generation none datum
  - CUR-COMP-404 Challenger-committed comparison
    - CUR-COMP-404.1 before-challenger-committed-coverage table datum-family
    - CUR-COMP-404.2 rejected-candidate interpretation boundary datum
  - CUR-COMP-405 Lifecycle replay
    - CUR-COMP-405.1 stage range slider control
    - CUR-COMP-405.2 ordered stage button list control-family
    - CUR-COMP-405.3 selected-stage detail
      - CUR-COMP-405.3.1 stage label-state-detail datum
      - CUR-COMP-405.3.2 stage evidence action family
      - CUR-COMP-405.3.3 no-durable-evidence state

### CUR-VIEW-005 · Atlas

- CUR-VIEW-005 Atlas
  - CUR-COMP-521 Whole-view request state
    - CUR-COMP-521.1 LOADING state
    - CUR-COMP-521.2 ERROR state
    - CUR-COMP-521.3 stale-detail replacement effect
  - CUR-COMP-501 Semantic overview
    - CUR-COMP-501.1 Active count datum
    - CUR-COMP-501.2 Source eligible count datum
    - CUR-COMP-501.3 Held count datum
    - CUR-COMP-501.4 Learned edges count datum
  - CUR-COMP-503 Semantic authority lens
    - CUR-COMP-503.1 canonical-vs-learned lens control
    - CUR-COMP-503.2 canonical-equivalence warning datum
  - CUR-COMP-504 ABI bank map-row resolver
    - CUR-COMP-504.1 bank-card list control-family
    - CUR-COMP-504.2 no-bank state
    - CUR-COMP-504.3 exact bank-row resolver form control
  - CUR-COMP-505 Exact semantic lookup
    - CUR-COMP-505.1 exact semantic ID form control
    - CUR-COMP-505.2 held-source-mappings preview
    - CUR-COMP-505.3 no-held-mappings state
  - CUR-COMP-502 Semantic selection detail
    - CUR-COMP-502.1 selected identity-kind heading datum
    - CUR-COMP-502.2 HELD identity state
    - CUR-COMP-502.3 source revision-loci-ABI facts datum-family
    - CUR-COMP-502.4 generation admission-new-exercised-requal facts datum-family
    - CUR-COMP-502.5 capability-frame bindings datum-family
    - CUR-COMP-502.6 lens-dependent canonical-similarity relationships datum-family
    - CUR-COMP-502.7 no-selection guidance state

### CUR-VIEW-006 · Model

- CUR-VIEW-006 Model
  - CUR-COMP-601 Model local navigation
    - CUR-COMP-601.1 Neural Runtime peer control
    - CUR-COMP-601.2 Frame Compiler Explorer peer control
    - CUR-COMP-601.3 pressed subsection state
  - CUR-COMP-611 Neural Runtime
    - CUR-COMP-611.1 current-historical fixture-mode controls
    - CUR-COMP-602 Topology-runtime
      - CUR-COMP-602.1 topology manifest
        - CUR-COMP-602.1.1 ordered topology path datum
        - CUR-COMP-602.1.2 topology fact grid datum-family
      - CUR-COMP-602.2 runtime projection summary
        - CUR-COMP-602.2.1 runtime metric strip datum-family
    - CUR-COMP-603 CCGQA-attention-AttnRes
      - CUR-COMP-603.1 CCGQA diagnostics
        - CUR-COMP-603.1.1 unavailable-historical state
        - CUR-COMP-603.1.2 repeated layer card
          - CUR-COMP-603.1.2.1 evidence-invalid banner datum-state
          - CUR-COMP-603.1.2.2 Q-K-V-channel-conv-entropy-sequence-cache-finite metrics datum-family
          - CUR-COMP-603.1.2.3 inspect evidence control-effect
      - CUR-COMP-603.2 AttnRes diagnostics
        - CUR-COMP-603.2.1 unavailable-historical state
        - CUR-COMP-603.2.2 repeated boundary-layer card
          - CUR-COMP-603.2.2.1 routing weight bars gate-sum datum
          - CUR-COMP-603.2.2.2 inspect recorded weights control-effect
    - CUR-COMP-604 Local refinement
      - CUR-COMP-604.1 unavailable state
      - CUR-COMP-604.2 expansion-pass histogram datum
      - CUR-COMP-604.3 reconciliation-cost summary datum
      - CUR-COMP-604.4 receipt table
        - CUR-COMP-604.4.1 frame-receipt-eligible-quota-passes-density-cost datum-row
        - CUR-COMP-604.4.2 receipt inspect control-effect
    - CUR-COMP-605 Instrumentation coverage
      - CUR-COMP-605.1 repeated instrument-source-state row datum-family
  - CUR-COMP-606 Frame Compiler Explorer
    - CUR-COMP-607 Frame generation-query
      - CUR-COMP-607.1 fixture generation selector control
      - CUR-COMP-607.2 LOADING-PRESENT-ERROR request state
      - CUR-COMP-607.3 coverage-returned-count datum
      - CUR-COMP-607.4 compiled-example selector control
      - CUR-COMP-607.5 missing-no-selection state
    - CUR-COMP-608 Compiled provenance-packing
      - CUR-COMP-608.1 selected-example packing metrics datum-family
      - CUR-COMP-608.2 receipt provenance disclosure
      - CUR-COMP-608.3 repeated position disclosure
        - CUR-COMP-608.3.1 position metadata datum-family
        - CUR-COMP-608.3.2 constituent legality table datum-family
        - CUR-COMP-608.3.3 codec-field visibility datum-family
      - CUR-COMP-608.4 unavailable sidecar-compiler state
    - CUR-COMP-609 Prediction frontier
      - CUR-COMP-609.1 frontier selector control
      - CUR-COMP-609.2 legality-visibility projection effect
    - CUR-COMP-610 Aggregate packing
      - CUR-COMP-610.1 aggregate disclosure control-state
      - CUR-COMP-610.2 aggregate packing metrics datum-family

### CUR-VIEW-007 · Memory

- CUR-VIEW-007 Memory
  - CUR-COMP-733 Historical-memory unavailable
    - CUR-COMP-733.1 requested generation datum
    - CUR-COMP-733.2 MISSING-UNAVAILABLE state
    - CUR-COMP-733.3 no-current-substitution effect
  - CUR-COMP-701 Memory summary
    - CUR-COMP-701.1 generation-PRESENT header datum-state
    - CUR-COMP-701.2 allocated-capacity datum
    - CUR-COMP-701.3 eligible-hit exact structural miss counts datum
    - CUR-COMP-701.4 hit-rate gate-use-rate datum
    - CUR-COMP-701.5 state-parameter-optimizer footprint datum
    - CUR-COMP-701.6 repeated read-site receipt datum-family
    - CUR-COMP-701.7 operational-evidence authority doctrine datum
  - CUR-COMP-702 Memory atlas
    - CUR-COMP-702.1 page-count header datum
    - CUR-COMP-702.2 page selector card family control
    - CUR-COMP-702.3 slot list
      - CUR-COMP-702.3.1 repeated slot control
        - CUR-COMP-702.3.1.1 address datum
        - CUR-COMP-702.3.1.2 stable identity datum
        - CUR-COMP-702.3.1.3 frame schema datum
        - CUR-COMP-702.3.1.4 allocation state datum
        - CUR-COMP-702.3.1.5 capability-episode object relations contract
    - CUR-COMP-702.4 empty-page state
  - CUR-COMP-703 Motif inspector
    - CUR-COMP-703.1 missing-selection state
    - CUR-COMP-703.2 selected identity-allocation header datum-state
    - CUR-COMP-703.3 identity-key-semantic-address-eligibility facts datum-family
    - CUR-COMP-703.4 creation-last-use-hit-gate telemetry datum-family
    - CUR-COMP-703.5 parameter-optimizer-correction facts datum-family
    - CUR-COMP-703.6 source-evidence refs datum-family
    - CUR-COMP-703.7 related capability-episode refs datum-family
    - CUR-COMP-703.8 capability interpretation datum
  - CUR-COMP-704 Generation comparison
    - CUR-COMP-704.1 comparison-generation selector control
    - CUR-COMP-704.2 Created-Removed-Held-Requalified identity groups datum-family
    - CUR-COMP-704.3 allocation-capacity-hit-miss-gate deltas datum-family
    - CUR-COMP-704.4 append-only HELD interpretation doctrine datum
  - CUR-COMP-705 Rejected candidate boundary
    - CUR-COMP-705.1 candidate-REJECTED header datum-state
    - CUR-COMP-705.2 four-invariant proof grid datum-family
    - CUR-COMP-705.3 rejection reason candidate-local-not-retained doctrine datum

### CUR-VIEW-008 · Teacher

- CUR-VIEW-008 Teacher
  - CUR-COMP-801 Strategy population
    - CUR-COMP-801.1 incumbent-challenger-canary-retired role-count summary datum
    - CUR-COMP-801.2 repeated strategy card
      - CUR-COMP-801.2.1 identity-role-status datum
      - CUR-COMP-801.2.2 attempts-retained-gain-no-gain-interference-wall metrics datum
      - CUR-COMP-801.2.3 capability-source-lifecycle-canary-resource scope datum
      - CUR-COMP-801.2.4 Learning Episode links or no-link state
      - CUR-COMP-801.2.5 checkpoint role-state history datum
      - CUR-COMP-801.2.6 Inspect strategy control-effect
  - CUR-COMP-802 Outcome-cost comparison
    - CUR-COMP-802.1 strategy selection controls
      - CUR-COMP-802.1.1 option identity-pressed state
      - CUR-COMP-802.1.2 selection update invalid-scope fallback effect
    - CUR-COMP-802.2 comparison-scope controls
      - CUR-COMP-802.2.1 whole-school capability source-family option family
      - CUR-COMP-802.2.2 pressed-state rerender effect
    - CUR-COMP-802.3 comparison coverage-context datum
    - CUR-COMP-802.4 comparison table
      - CUR-COMP-802.4.1 strategy-observed-retained-gain datum
      - CUR-COMP-802.4.2 no-gain-interference datum
      - CUR-COMP-802.4.3 wall-time attempted-steps datum
      - CUR-COMP-802.4.4 per-row coverage datum-state
    - CUR-COMP-802.5 descriptive no-winner doctrine datum
  - CUR-COMP-803 Fidelity ladder
    - CUR-COMP-803.1 OBSERVATIONAL panel state
    - CUR-COMP-803.2 fidelity-card identity-mode datum
    - CUR-COMP-803.3 rung-delta sequence datum
    - CUR-COMP-803.4 stop-retained-steps-savings-false-kill outcomes datum
    - CUR-COMP-803.5 authority-change no-early-termination boundary datum
  - CUR-COMP-804 Projection boundary
    - CUR-COMP-804.1 projection schema datum
    - CUR-COMP-804.2 coverage state
    - CUR-COMP-804.3 exposed field inventory datum
    - CUR-COMP-804.4 fixture-backed limitation-authority explanation datum

### CUR-VIEW-009 · SÍ SÉ SON

- CUR-VIEW-009 SI SE SON
  - CUR-COMP-906 As-of snapshot selector
    - CUR-COMP-906.1 retained snapshot option family control
    - CUR-COMP-906.2 selected pressed state
    - CUR-COMP-906.3 choose-snapshot full-view-rerender effect
  - CUR-COMP-901 Observation set
    - CUR-COMP-901.1 event identity-context-timestamps datum
    - CUR-COMP-901.2 independent axis cell family
      - CUR-COMP-901.2.1 axis label-ordinal datum
      - CUR-COMP-901.2.2 expected-missing reported-negative unknown note state
      - CUR-COMP-901.2.3 inspect axis control-effect
    - CUR-COMP-901.3 scope-source-associated-object context datum
    - CUR-COMP-901.4 stable link datum
    - CUR-COMP-901.5 three-axis no-scalar doctrine and lane headings datum
  - CUR-COMP-902 Provenance
    - CUR-COMP-902.1 event-capability-salience identity datum
    - CUR-COMP-902.2 policy owner-version-digest datum
    - CUR-COMP-902.3 window policy-version-size datum
    - CUR-COMP-902.4 per-axis provenance
      - CUR-COMP-902.4.1 sourceRef-ruleId datum
      - CUR-COMP-902.4.2 basis refs datum
  - CUR-COMP-903 Recursive aggregation
    - CUR-COMP-903.1 historical aggregation-unavailable state
    - CUR-COMP-903.2 window identity-size-append-bounds-late datum
    - CUR-COMP-903.3 cluster
      - CUR-COMP-903.3.1 identity-partition datum
      - CUR-COMP-903.3.2 rule-posture-lineage-count datum
      - CUR-COMP-903.3.3 constituent observation controls
    - CUR-COMP-903.4 pattern identity-status-nomination-sourceGold-qualified datum
    - CUR-COMP-903.5 trend
      - CUR-COMP-903.5.1 supported-rule datum
      - CUR-COMP-903.5.2 window points datum-family
      - CUR-COMP-903.5.3 constituent controls vs outside-as-of state
    - CUR-COMP-903.6 reversible no-authority-upgrade doctrine datum
  - CUR-COMP-904 Routing rationale
    - CUR-COMP-904.1 historical routing-unavailable state
    - CUR-COMP-904.2 route identity-tier-rule datum
    - CUR-COMP-904.3 ordering keys hidden-weighting datum
    - CUR-COMP-904.4 cited observation family
      - CUR-COMP-904.4.1 inspect available citation control-effect
      - CUR-COMP-904.4.2 outside-as-of citation state
    - CUR-COMP-904.5 no-private-weight inference doctrine datum
  - CUR-COMP-905 Projection boundary
    - CUR-COMP-905.1 schema datum
    - CUR-COMP-905.2 PARTIAL coverage state
    - CUR-COMP-905.3 projected field inventory datum
    - CUR-COMP-905.4 non-first-class fixture-backed boundary datum

### CUR-VIEW-010 · Corrections

- CUR-VIEW-010 Corrections
  - CUR-COMP-1001 Correction context
    - CUR-COMP-1001.1 view-purpose epistemic boundary datum
    - CUR-COMP-1001.2 projection fixture notice datum
    - CUR-COMP-1001.3 correction-state glossary datum
    - CUR-COMP-1001.4 selected correction summary
      - CUR-COMP-1001.4.1 correction ID datum
      - CUR-COMP-1001.4.2 prior-current source revision datum
      - CUR-COMP-1001.4.3 correction generation datum
      - CUR-COMP-1001.4.4 explicit unknown-influence count datum
  - CUR-COMP-1002 Blast-radius graph-list
    - CUR-COMP-1002.1 explicit-edge traversal doctrine datum
    - CUR-COMP-1002.2 affected-node control family
      - CUR-COMP-1002.2.1 kind-label datum
      - CUR-COMP-1002.2.2 state datum
      - CUR-COMP-1002.2.3 evidence refs unknown-receipt state
      - CUR-COMP-1002.2.4 click inspect control-effect
    - CUR-COMP-1002.3 dependency-edge list
      - CUR-COMP-1002.3.1 from datum
      - CUR-COMP-1002.3.2 relation datum
      - CUR-COMP-1002.3.3 to datum
  - CUR-COMP-1003 Equivalent impact table
    - CUR-COMP-1003.1 equivalence statement datum
    - CUR-COMP-1003.2 impact row family
      - CUR-COMP-1003.2.1 identity inspect control
      - CUR-COMP-1003.2.2 class datum
      - CUR-COMP-1003.2.3 state datum
      - CUR-COMP-1003.2.4 evidence refs-untracked state
  - CUR-COMP-1004 Requalification state
    - CUR-COMP-1004.1 descriptive non-certifying queue boundary datum
    - CUR-COMP-1004.2 task identity urgency owner status datum
    - CUR-COMP-1004.3 generation checkpoint source-revision custody datum
    - CUR-COMP-1004.4 implicated refs datum
    - CUR-COMP-1004.5 evidence refs UNKNOWN state
    - CUR-COMP-1004.6 receipt refs NONE-NOT-REQUALIFIED state
  - CUR-COMP-1005 Append-only correction history
    - CUR-COMP-1005.1 tracked artifact identity datum
    - CUR-COMP-1005.2 append-only non-rewrite doctrine datum
    - CUR-COMP-1005.3 history entry family
      - CUR-COMP-1005.3.1 generation-phase datum
      - CUR-COMP-1005.3.2 state datum
      - CUR-COMP-1005.3.3 receipt datum

### CUR-VIEW-011 · Lineage

- CUR-VIEW-011 Lineage
  - CUR-COMP-1101 Accepted lineage
    - CUR-COMP-1101.1 READ_ONLY posture header state
    - CUR-COMP-1101.2 generation node family
      - CUR-COMP-1101.2.1 generation-transition-compact-manifest datum
      - CUR-COMP-1101.2.2 checkpoint-parent semantic relations contract
      - CUR-COMP-1101.2.3 selected pressed state
      - CUR-COMP-1101.2.4 click select-rerender-inspect effect
    - CUR-COMP-1101.3 exact parent-child transition list datum-family
    - CUR-COMP-1101.4 tabular lineage equivalent datum-family
  - CUR-COMP-1102 Generation comparison
    - CUR-COMP-1102.1 comparison relation-state header datum
    - CUR-COMP-1102.2 endpoint controls
      - CUR-COMP-1102.2.1 From selector control
      - CUR-COMP-1102.2.2 To selector control
      - CUR-COMP-1102.2.3 generation-manifest option datum
      - CUR-COMP-1102.2.4 change rerender effect
    - CUR-COMP-1102.3 interpretation no-winner doctrine datum
    - CUR-COMP-1102.4 structured dimension diff
      - CUR-COMP-1102.4.1 dimension datum
      - CUR-COMP-1102.4.2 before-after datum
      - CUR-COMP-1102.4.3 state-reason datum
      - CUR-COMP-1102.4.4 source datum
    - CUR-COMP-1102.5 capability-evidence diff datum-family
  - CUR-COMP-1103 Rejected-candidate boundary
    - CUR-COMP-1103.1 REJECTED state-header
    - CUR-COMP-1103.2 candidate ID rejection reason committed-generation-NONE datum
  - CUR-COMP-1104 Exact immutable generation node
    - CUR-COMP-1104.1 generation-transition-state header datum
    - CUR-COMP-1104.2 full manifest-parent custody identity datum
    - CUR-COMP-1104.3 manifest field dossier
      - CUR-COMP-1104.3.1 label datum
      - CUR-COMP-1104.3.2 value datum
      - CUR-COMP-1104.3.3 source ref datum
    - CUR-COMP-1104.4 stable deep-link datum
    - CUR-COMP-1104.5 exact CP03 mode-generation-record query identity datum
    - CUR-COMP-1104.6 historical generation missing defensive state

### CUR-VIEW-012 · Resources

- CUR-VIEW-012 Resources
  - CUR-COMP-1201 Resource headline
    - CUR-COMP-1201.1 no-current-projection defensive state
    - CUR-COMP-1201.2 fixture-live-historical generation-window provenance datum
    - CUR-COMP-1201.3 page-state badge datum-state
    - CUR-COMP-1201.4 headline metric family
      - CUR-COMP-1201.4.1 metric identity datum
      - CUR-COMP-1201.4.2 semantic state datum
      - CUR-COMP-1201.4.3 value datum
      - CUR-COMP-1201.4.4 evidence-strength note datum
    - CUR-COMP-1201.5 throughput-not-learning boundary datum
  - CUR-COMP-1202 Metric semantics
    - CUR-COMP-1202.1 measured-value semantic-value-note datum
    - CUR-COMP-1202.2 configured-limit semantic-value-note datum
    - CUR-COMP-1202.3 forecast-estimate semantic-value-note datum
  - CUR-COMP-1203 Memory decomposition
    - CUR-COMP-1203.1 COMPLETE-PARTIAL-UNAVAILABLE reconciliation state
    - CUR-COMP-1203.2 measured category family
      - CUR-COMP-1203.2.1 category identity datum
      - CUR-COMP-1203.2.2 value-or-UNAVAILABLE datum
      - CUR-COMP-1203.2.3 category state datum
    - CUR-COMP-1203.3 unresolved remainder value-state datum
    - CUR-COMP-1203.4 allocated-sum aggregate reconciliation explanation datum
  - CUR-COMP-1204 Compute-length profile
    - CUR-COMP-1204.1 compute-preparation metrics datum-family
    - CUR-COMP-1204.2 sequence-batch-length metrics datum-family
  - CUR-COMP-1205 Timeline-correlation
    - CUR-COMP-1205.1 no-samples UNAVAILABLE no-synthesis state
    - CUR-COMP-1205.2 sample-count datum
    - CUR-COMP-1205.3 sample row family
      - CUR-COMP-1205.3.1 sample ID-time inspect control
      - CUR-COMP-1205.3.2 memory-MLX datum
      - CUR-COMP-1205.3.3 batch-density-steps-expansion datum
      - CUR-COMP-1205.3.4 peak-vs-sample state
    - CUR-COMP-1205.4 exact related-evidence global-inspector effect
  - CUR-COMP-1206 Historical comparison
    - CUR-COMP-1206.1 EMPTY-LOADING-PRESENT-UNAVAILABLE state
    - CUR-COMP-1206.2 exact-generation form
      - CUR-COMP-1206.2.1 numeric generation input control
      - CUR-COMP-1206.2.2 Load exact generation submit control
      - CUR-COMP-1206.2.3 read-only no-inference guidance datum
    - CUR-COMP-1206.3 no-comparison empty state
    - CUR-COMP-1206.4 metric historical-inspected-delta table datum-family
    - CUR-COMP-1206.5 bounded historical CP03 query rerender effect

### CUR-VIEW-013 · Evidence

- CUR-VIEW-013 Evidence
  - CUR-COMP-1301 Query-filter
    - CUR-COMP-1301.1 forensic-query help datum
    - CUR-COMP-1301.2 criteria controls
      - CUR-COMP-1301.2.1 search-kind selector control
      - CUR-COMP-1301.2.2 exact-identity input control
    - CUR-COMP-1301.3 Search fresh-query reset effect
    - CUR-COMP-1301.4 Load-next bounded-page cursor-merge effect
    - CUR-COMP-1301.5 context-bound query identity stale-response cancellation contract
  - CUR-COMP-1305 Query-degraded state
    - CUR-COMP-1305.1 error-loading-page-coverage-truncated semantic state
    - CUR-COMP-1305.2 returned-total waiting-error detail datum
    - CUR-COMP-1305.3 alert-vs-status live-region treatment
    - CUR-COMP-1305.4 failure clears stale non-append results effect
  - CUR-COMP-1302 Result list
    - CUR-COMP-1302.1 exact record result
      - CUR-COMP-1302.1.1 record ID datum
      - CUR-COMP-1302.1.2 schema datum
      - CUR-COMP-1302.1.3 authority-coverage-generation datum
      - CUR-COMP-1302.1.4 select detail-return-origin effect
    - CUR-COMP-1302.2 page relationship result
      - CUR-COMP-1302.2.1 relation-source-target refs datum
      - CUR-COMP-1302.2.2 exact-target hydrate control-effect
      - CUR-COMP-1302.2.3 EXTERNAL-NOT-HYDRATED state
  - CUR-COMP-1306 Traversal-omission
    - CUR-COMP-1306.1 degraded marker family
      - CUR-COMP-1306.1.1 schema datum
      - CUR-COMP-1306.1.2 marker record ID datum
      - CUR-COMP-1306.1.3 missing-reason-resource-stale-as-of details datum
    - CUR-COMP-1306.2 traversal failure alert datum-state
    - CUR-COMP-1306.3 selected-link hydration unavailable-no-links state
  - CUR-COMP-1303 Exact record-raw payload
    - CUR-COMP-1303.1 exact-record identity-header datum
    - CUR-COMP-1303.2 readable-raw mode
      - CUR-COMP-1303.2.1 current-mode label datum
      - CUR-COMP-1303.2.2 toggle repaint control-effect
    - CUR-COMP-1303.3 readable record dossier
      - CUR-COMP-1303.3.1 record-schema-authority-coverage-verification datum
      - CUR-COMP-1303.3.2 materialized-observed-as-of datum
      - CUR-COMP-1303.3.3 literal metadata datum
      - CUR-COMP-1303.3.4 literal body fields datum-family
    - CUR-COMP-1303.4 provenance refs
      - CUR-COMP-1303.4.1 SOURCE-EVIDENCE-RECEIPT groups datum
      - CUR-COMP-1303.4.2 ref exact-reference-search control-effect
      - CUR-COMP-1303.4.3 no-refs state
    - CUR-COMP-1303.5 exact selected-record links
      - CUR-COMP-1303.5.1 relation-source-target datum
      - CUR-COMP-1303.5.2 open exact record control-effect
      - CUR-COMP-1303.5.3 unresolved-no-link state
    - CUR-COMP-1303.6 raw structured payload datum
  - CUR-COMP-1304 Return to origin
    - CUR-COMP-1304.1 return-available state
    - CUR-COMP-1304.2 Return to inspected object control
    - CUR-COMP-1304.3 origin restoration effect

### CUR-VIEW-014 · Operate

- CUR-VIEW-014 Operate
  - CUR-COMP-1400 Command-boundary posture
    - CUR-COMP-1400.1 MUTATION ZONE datum
    - CUR-COMP-1400.2 LIVE COMMAND CONTEXT REQUIRED blocker state
    - CUR-COMP-1400.3 global command-error alert state
  - CUR-COMP-1401 Action catalog
    - CUR-COMP-1401.1 action identity-label-description datum
    - CUR-COMP-1401.2 supported-vs-disabled state
    - CUR-COMP-1401.3 AUTHORIZATION REQUIRED READ ONLY UNAVAILABLE posture datum-state
    - CUR-COMP-1401.4 selected aria-pressed state
    - CUR-COMP-1401.5 selection initializes request defaults effect
  - CUR-COMP-1402 Exact request
    - CUR-COMP-1402.1 action-phase header datum-state
    - CUR-COMP-1402.2 conditional dry-run toggle control-effect
    - CUR-COMP-1402.3 JSON parameters textarea control
    - CUR-COMP-1402.4 admitted-parameter no-shell boundary datum
    - CUR-COMP-1402.5 Run read-only preflight control
    - CUR-COMP-1402.6 invalid JSON-object-key-scalar validation states
  - CUR-COMP-1403 Preflight
    - CUR-COMP-1403.1 no-preflight empty state
    - CUR-COMP-1403.2 preview mode state
    - CUR-COMP-1403.3 mutating-vs-read-only consequence posture
    - CUR-COMP-1403.4 exact target fact family
      - CUR-COMP-1403.4.1 target ref datum
      - CUR-COMP-1403.4.2 run-generation datum
      - CUR-COMP-1403.4.3 generation manifest datum
      - CUR-COMP-1403.4.4 topology Factory semantic datum
      - CUR-COMP-1403.4.5 source identity datum
      - CUR-COMP-1403.4.6 admission policy datum
      - CUR-COMP-1403.4.7 expected postcondition datum
    - CUR-COMP-1403.5 resource profile fact family
    - CUR-COMP-1403.6 stale-context blocker
      - CUR-COMP-1403.6.1 conflicting identity label datum
      - CUR-COMP-1403.6.2 shell-expected vs target-actual datum
      - CUR-COMP-1403.6.3 refresh-repreflight guidance datum
    - CUR-COMP-1403.7 PREVIEWING-to-REVIEW-STALE-ERROR transition effect
  - CUR-COMP-1404 Deliberate authorization
    - CUR-COMP-1404.1 HUMAN GATE vs READ ONLY state
    - CUR-COMP-1404.2 expectedTargetRef reviewed-target binding datum
    - CUR-COMP-1404.3 exact authorization phrase datum
    - CUR-COMP-1404.4 authorization input control
    - CUR-COMP-1404.5 submit label-enabled state control
    - CUR-COMP-1404.6 mutation-preview-conflict-phrase-target dispatch guard effect
  - CUR-COMP-1405 Receipt-readback-reconciliation
    - CUR-COMP-1405.1 lost-ack outcome-unknown state
      - CUR-COMP-1405.1.1 operation identity datum
      - CUR-COMP-1405.1.2 no-blind-retry doctrine datum
      - CUR-COMP-1405.1.3 Reconcile operation control
    - CUR-COMP-1405.2 operation ID-receipt state header datum
    - CUR-COMP-1405.3 lifecycle stage strip datum
    - CUR-COMP-1405.4 receipt record-target-postcondition-error facts datum
    - CUR-COMP-1405.5 receipt actions
      - CUR-COMP-1405.5.1 Open receipt inspector control-effect
      - CUR-COMP-1405.5.2 Open postcondition inspector control-effect
      - CUR-COMP-1405.5.3 conditional Reconcile authoritative-readback control-effect
    - CUR-COMP-1405.6 stderr-stdout trainer log disclosure
    - CUR-COMP-1405.7 literal bounded inspection JSON disclosure
    - CUR-COMP-1405.8 matching operator event reconciliation effect
    - CUR-COMP-1405.9 terminal-pending-lost-unknown phase effect

## Source-inventory scope rule

A redesign leaf that references a current-state inventory node must account for the full dotted subtree as migration evidence: preserve it, intentionally transform it, or intentionally remove it in the target atlas. The inventory does not by itself authorize an element to survive into the redesigned UI.
