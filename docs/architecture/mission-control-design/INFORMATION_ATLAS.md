# Mission Control current-state information atlas

Status: descriptive map of the current implementation, not target-screen approval
Parent authority: GitHub issue #1124
Cross-view relationships: `FLOWS.md`

The atlas deliberately describes composition as a hierarchy. Cross-view navigation, state propagation, selection ownership, evidence return, compare, pinning, and command lifecycles are kept in `FLOWS.md` so this tree does not become spaghetti.

## ID grammar

- `SHELL-D-###`: persistent shell segment
- `VIEW-D-###`: destination
- `COMP-D-###`: published component/section inside a shell/view
- `COMP-D-###.<n>[.<n>…]`: recursive constituent below a published component; dotted descendants never renumber/reuse an existing parent ID
- `STATE-D-###`: important presentation state

Each component records **information → treatment → interaction → effect**. A component is **composite, not terminal**, while it still contains an independently meaningful subcomponent, repeated control family, presentation/state contract, interaction contract, or distinct effect. Recursion stops only at a true semantic leaf. Repeated controls with identical mechanics may share a family parent, but fixed instances are enumerated and behaviorally distinct instances/states are separate.

The node register is not the visual atlas by itself. The mind map below is the requested composition-first tree. The register that follows supplies exact current-state detail, and the concern matrix at the end supplies the state/authority/accessibility/i18n/test-hook trace for every node.

## Visual mind-map tree

```mermaid
mindmap
  root((Bilqis Mission Control))
    SHELL-D-001 Application shell
      COMP-D-015 Skip to main access path
      COMP-D-001 Primary navigation
      COMP-D-002 Context bar
      COMP-D-003 Investigation strip
        COMP-D-010 Time lens
        COMP-D-011 Compare workspace
        COMP-D-012 Pins
        COMP-D-013 Annotations
        COMP-D-014 App URI and deep link
      COMP-D-004 Defensive banner
      Workspace
        COMP-D-005 Destination header
        COMP-D-006 Local subnavigation
        VIEW-D-001 Mission Control
          COMP-D-107 Startup state
          COMP-D-101 Learner posture
          COMP-D-102 Learning pulse
          COMP-D-103 Actionable attention
          COMP-D-104 Health strip
          COMP-D-105 Current work
          COMP-D-106 Compact School map
        VIEW-D-002 School
          COMP-D-201 Capability matrix
            COMP-D-207 Matrix controls
          COMP-D-202 Dependency graph
          COMP-D-203 Curriculum semantic atlas
            COMP-D-205 Curriculum controls
            COMP-D-206 Topology and node dossier
            COMP-D-208 Semantic equivalent table
            COMP-D-209 Scale disclosure
          COMP-D-204 Peer subnavigation
        VIEW-D-003 Capability Explorer
          COMP-D-301 Capability identity
          COMP-D-302 Chronology
          COMP-D-303 Source and evidence dossier
          COMP-D-304 Source lens controls
          COMP-D-305 Dossier sections
          COMP-D-306 Inline evidence detail
        VIEW-D-004 Learning
          COMP-D-401 Episode selector
          COMP-D-402 Candidate transaction
          COMP-D-403 Retention rollback evidence
          COMP-D-404 Challenger committed comparison
          COMP-D-405 Lifecycle replay controls
        VIEW-D-005 Atlas
          COMP-D-521 View request state
          COMP-D-501 Semantic overview
          COMP-D-502 Semantic selection
          COMP-D-503 Semantic authority lens
          COMP-D-504 ABI bank map
          COMP-D-505 Exact semantic lookup
        VIEW-D-006 Model
          COMP-D-601 Model local navigation
          COMP-D-611 Neural Runtime
            COMP-D-602 Neural topology
            COMP-D-603 CCGQA attention AttnRes
            COMP-D-604 Local refinement
            COMP-D-605 Instrumentation coverage
          COMP-D-606 Frame Compiler Explorer
            COMP-D-607 Frame generation and query
            COMP-D-608 Compiled provenance and packing
            COMP-D-609 Prediction frontier
            COMP-D-610 Aggregate packing disclosure
        VIEW-D-007 Memory
          COMP-D-733 Historical memory unavailable
          COMP-D-701 Memory summary
          COMP-D-702 Memory atlas pages
          COMP-D-703 Motif inspector
          COMP-D-704 Generation comparison
          COMP-D-705 Rejected candidate boundary
        VIEW-D-008 Teacher
          COMP-D-801 Strategy population
          COMP-D-802 Outcome cost fidelity
          COMP-D-803 Fidelity ladder
          COMP-D-804 Projection boundary
        VIEW-D-009 SI SE SON
          COMP-D-906 As-of snapshot selector
          COMP-D-901 Salience observations
          COMP-D-902 Provenance
          COMP-D-903 Recursive aggregation
          COMP-D-904 Routing rationale
          COMP-D-905 Projection boundary
        VIEW-D-010 Corrections
          COMP-D-1001 Correction context
          COMP-D-1002 Blast-radius graph
          COMP-D-1003 Equivalent impact table
          COMP-D-1004 Requalification state
          COMP-D-1005 Append-only history
        VIEW-D-011 Lineage
          COMP-D-1101 Accepted lineage
          COMP-D-1102 Generation comparison
          COMP-D-1103 Rejected candidate boundary
          COMP-D-1104 Exact generation node
        VIEW-D-012 Resources
          COMP-D-1201 Resource headline
          COMP-D-1202 Metric semantics
          COMP-D-1203 Memory decomposition
          COMP-D-1204 Compute and length
          COMP-D-1205 Timeline and correlation
          COMP-D-1206 Historical comparison
        VIEW-D-013 Evidence
          COMP-D-1301 Query and filter
          COMP-D-1305 Query and degraded state
          COMP-D-1302 Result list
          COMP-D-1306 Traversal and omission status
          COMP-D-1303 Exact record and raw payload
          COMP-D-1304 Return to origin
        VIEW-D-014 Operate
          COMP-D-1400 Command boundary posture
          COMP-D-1401 Action catalog
          COMP-D-1402 Exact request
          COMP-D-1403 Preflight
          COMP-D-1404 Deliberate authorization
          COMP-D-1405 Receipt and reconciliation
      COMP-D-007 Global inspector
      COMP-D-008 Command palette
      COMP-D-009 Fixture provenance boundary
      COMP-D-016 Polite live announcer
```

## SHELL-D-001 · Application shell

### COMP-D-015 · Skip-to-main access path
- Information: keyboard bypass route to the main content focus target.
- Treatment: visually hidden until focused.
- Interaction: activate the skip link.
- Effect: moves keyboard focus past persistent shell chrome to `#main-content`.

### COMP-D-001 · Primary navigation rail
- Information: Bilqis/Mission Control identity; current destination; fourteen destination actions; command-palette trigger.
- Treatment: persistent left rail with flat destination buttons.
- Interaction: click or roving keyboard navigation; command palette via keyboard shortcut.
- Effect: changes destination while preserving current run/generation context where allowed.
- Concerns: D-003 overload; eventual task/domain grouping; no ambiguous collapsed labels.

### COMP-D-002 · Context bar
- Information: posture, run, generation/manifest, freshness, topology, Factory release, semantic release, optimizer, lease, frontier, resources, coverage, run/time selectors.
- Treatment: persistent top context strip.
- Interaction: run/generation selection where supported; theme and density controls.
- Effect: changes inspected context/display settings.
- Concerns: excessive permanent metadata; operator-significant values must not truncate.

### COMP-D-003 · Global investigation strip
- Information: current/as-of lens plus entry points for compare, pins, annotations, and exact app/deep-link context.
- Treatment: persistent investigation toolbar with deliberately disclosed workspaces.
- Interaction: open one investigation workspace or change the time lens.
- Effect: coordinates the independent investigation subcomponents below.
- Concerns: must not compete visually with primary destination; exact context identity is mandatory.

### COMP-D-010 · Time lens
- Information: current verified context or exact historical generation.
- Treatment: compact generation input/current-context affordance.
- Interaction: choose exact generation; return to verified current when available.
- Effect: changes the global inspected context to historical or current and gates mutation accordingly.

### COMP-D-011 · Compare workspace
- Information: exact left/right stable object refs, comparison state, literal comparison rows and mismatch reasons.
- Treatment: disclosed two-slot comparison workspace plus analytical table.
- Interaction: clear either side or populate sides from the global inspector; comparison rows themselves are static.
- Effect: compares exact objects without implying equivalence when run/generation/kind differ.

### COMP-D-012 · Pins
- Information: locally stored exact object refs including run, generation, kind, ID and label.
- Treatment: disclosed pin list.
- Interaction: open exact pin; remove pin.
- Effect: returns to the pinned object's exact owning route/context without changing learner state.

### COMP-D-013 · Annotations
- Information: local operator notes attached to exact stable refs and explicitly marked non-authoritative.
- Treatment: note list plus bounded annotation form.
- Interaction: create/read notes for the selected exact object context.
- Effect: persists operator metadata locally without promoting it to evidence/source truth.

### COMP-D-014 · App URI / deep-link affordance
- Information: exact routable object/context identity.
- Treatment: compact exact URI rendered as code subordinate to investigation.
- Interaction: none directly in the current renderer; the URI is exposed for external/manual use.
- Effect: supplies a stable route string that can rehydrate exact destination, context, selection and Model subsection when consumed.

### COMP-D-004 · Defensive-state banner
- Information: current service/telemetry/availability posture and recovery guidance.
- Treatment: conditional status/alert banner with non-color cue.
- Interaction: reconnect where available.
- Effect: communicates boundary-specific failure/recovery and may gate mutation.

### COMP-D-005 · Destination header
- Information: destination eyebrow, title, concise purpose/current interpretation boundary.
- Treatment: top of workspace.
- Interaction: none, except focus target after navigation.
- Effect: establishes task hierarchy and reading context.

### COMP-D-006 · Destination-local subnavigation
- Information: peer modes within a destination, currently Model → Neural Runtime / Frame Compiler Explorer.
- Treatment: tab/segmented-like local controls.
- Interaction: switches peer surface.
- Effect: changes local working surface without changing global destination.

### COMP-D-007 · Global inspector
- Information: selected object kind, identity, posture, generation, exact details, owner/evidence actions.
- Treatment: non-modal side inspection plane.
- Interaction: close, open owner, open evidence, pin, compare left/right, annotate.
- Effect: cross-view navigation and investigation-state changes; focus returns to invoker.

### COMP-D-008 · Command palette
- Information: destination list and availability.
- Treatment: modal dialog.
- Interaction: keyboard open, roving selection, activate/close.
- Effect: fast destination navigation; mutation remains separately gated.

### COMP-D-009 · Fixture provenance boundary
- Information: whether a rich surface is live, historical, reference, or fixture-backed and which context owns it.
- Treatment: local provenance notice/status adjacent to the affected working surface.
- Interaction: usually none; may link to exact evidence where available.
- Effect: prevents checked-in diagnostic richness from being mistaken for live accepted learner telemetry.

### COMP-D-016 · Polite live announcer
- Information: transient operator-facing state-change announcements.
- Treatment: screen-reader-only `aria-live="polite"` / atomic region.
- Interaction: none directly.
- Effect: announces repeated navigation, selection, recovery, metadata and validation changes; content is cleared before the next microtask so repeated messages are voiced.

### STATE-D-001 · Bootstrap
- Four-stage startup: control plane, learner discovery, Mission Control telemetry, trainer.
- Must not substitute fixtures for missing live telemetry.

### STATE-D-002 · Live verified context
- Fresh snapshot supports ordinary inspection; Operate is available only when mutation context is verified.

### STATE-D-003 · Historical / inspection-only
- Exact prior generation context; mutation disabled.

### STATE-D-004 · Defensive variants
- loading, progressive, empty, stale, partial, offline, denied, revoked, unavailable, incompatible-version, timeout, duplicate-action, session/service restarting, historical unavailable, malformed/unsupported payload, outcome unknown.

### STATE-D-005 · Route / deep-link state
- Destination, exact selected object, run/generation context, and Model subsection where applicable.

### STATE-D-006 · Global selection / inspector state
- Exact selected object plus focus-return origin and inspector-open posture.

### STATE-D-007 · Evidence-return origin state
- The destination/object context from which Evidence was opened, retained for explicit return.

### STATE-D-008 · Investigation state
- Active panel, compare sides, pins, annotations, and exact stable object references.

### STATE-D-009 · Display / focus / fixture-custody state
- Theme, density, focus-return tokens, and temporary fixture/reference context ownership where a surface is not using the live shell context.

## VIEW-D-001 · Mission Control

Purpose: outcome-first learner health, current work, learning pulse, actionable attention.

### COMP-D-107 · Startup state
- Information: accepted generation, optimizer step, trainer running/stopped/unknown, current stage, and whether the first accepted learning event exists.
- Treatment: dedicated startup panel used instead of the normal dashboard when startup projection is present.
- Interaction: no direct action control in the current panel; copy points to Operate or the documented CLI resume path.
- Effect: distinguishes generation-zero-ready, trainer-running/waiting, and accepted-idle/no-events conditions without rendering absent learning telemetry as failure.

### COMP-D-101 · Learner headline / current posture
- Information: accepted learner health and current state.
- Treatment: summary region.
- Interaction: inspect relevant object where exposed.
- Effect: establishes the most important current condition.

### COMP-D-102 · Learning pulse
- Information: recent accepted learning activity and progression signal.
- Treatment: compact trend/summary surface.
- Interaction: inspect/navigate to exact learning evidence.
- Effect: answers whether learning is currently advancing without requiring the operator to enter Learning first.

### COMP-D-103 · Actionable attention
- Information: items requiring operator attention.
- Treatment: prioritized attention list/status.
- Interaction: inspect or navigate.
- Effect: converts overview into next investigation.

### COMP-D-104 · Health strip
- Information: Learning, Curriculum, Runtime, and System health families.
- Treatment: compact status strip using the application-wide status grammar.
- Interaction: none in the current renderer; the four health cards are static summary sections.
- Effect: distinguishes where an issue lives at overview depth.

### COMP-D-105 · Current work
- Information: active candidate/training work and its exact target/context.
- Treatment: concise current-work summary.
- Interaction: none in the current renderer; the current-work details are a static definition list.
- Effect: exposes what the learner is doing now without conflating work-in-progress with retained learning.

### COMP-D-106 · Compact School map
- Information: current curriculum/capability position at overview depth.
- Treatment: reduced School summary rather than a second full matrix.
- Interaction: select a capability row; the current Home binding inspects that exact capability through the shared selection/inspector path.
- Effect: provides orientation without duplicating the full School destination.

## VIEW-D-002 · School

Purpose: exact capability comparison and declared prerequisite topology.

### COMP-D-201 · Capability matrix
- Information: capability rows; WAS/TOP/NOW/ALL; debt; retention probability where measured; source/implementation/qualification state.
- Treatment: dense analytical matrix.
- Interaction: select capability; sort/filter where implemented.
- Effect: opens capability in inspector and cross-highlights relationships.

### COMP-D-207 · Matrix controls
- Information: active filters, family grouping, sort key/direction, page position, displayed identity count, and export scope.
- Treatment: filter/group/export control row, sortable column headings, and bounded pagination footer around the matrix.
- Interaction: toggle filters, group by family, sort, page previous/next, export the displayed identities.
- Effect: changes the visible matrix projection or exports that exact projection without changing capability evidence.

### COMP-D-202 · Dependency graph
- Information: prerequisite and dependent relationships.
- Treatment: interactive graph plus accessible equivalent relationship table.
- Interaction: keyboard/pointer selection.
- Effect: changes selected capability and neighborhood.

### COMP-D-203 · Curriculum semantic atlas
- Information: curriculum/semantic relationships supplied by GUI22.
- Treatment: dedicated analytical surface within School.
- Interaction: inspect/select semantic/curriculum objects.
- Effect: bridges curriculum structure and capability context.

### COMP-D-204 · School peer subnavigation
- Information: Capability matrix / Curriculum Semantic Atlas peer modes.
- Treatment: local peer-mode navigation.
- Interaction: switch School mode without leaving the destination.
- Effect: changes the working surface while preserving School context.

### COMP-D-205 · Curriculum search / filter / trace controls
- Information: query/filter controls and trace selection for curriculum-semantic relationships.
- Treatment: compact control cluster local to the curriculum atlas.
- Interaction: search, filter, select trace.
- Effect: narrows the curriculum-semantic working set without mutating learner state.

### COMP-D-206 · Declared topology / node dossier
- Information: selected curriculum/topology node, semantic binding, and declared consequences.
- Treatment: detail/dossier surface adjacent to the atlas.
- Interaction: select node, inspect exact binding/evidence.
- Effect: explains the exact declared relationship behind the visual topology.

### COMP-D-208 · Curriculum semantic equivalent table
- Information: capability, semantic display identity, grade, state, prerequisites, dependents, and evidence for every atlas node.
- Treatment: scrollable tabular equivalent beneath the visual curriculum graph.
- Interaction: select a capability/node from the table.
- Effect: changes the selected curriculum node while providing an equivalent non-graph representation.

### COMP-D-209 · Scale / progressive disclosure
- Information: a 243-row representative School fixture summarized by grade and semantic family, with bounded family and semantic expansion.
- Treatment: collapsed `details` summary with bounded family buttons and selected-node descendant disclosure.
- Interaction: expand the scale section, choose a family, choose a semantic within the bounded expansion.
- Effect: demonstrates how large School scopes are progressively disclosed without rendering all 243 rows as one graph.

## VIEW-D-003 · Capability Explorer

Purpose: measured chronology, source support, literal evidence; no inferred causes.

### COMP-D-301 · Capability identity/header
- Information: exact capability and context.
- Treatment: dossier header/state.
- Interaction: time/context controls where supported.
- Effect: anchors evidence to exact capability.

### COMP-D-302 · Chronology / measurements
- Information: measured progression and events over time.
- Treatment: chronology/table/metric surfaces.
- Interaction: inspect exact evidence.
- Effect: supports temporal comparison without causal synthesis.

### COMP-D-303 · Source/evidence dossier
- Information: source support and literal evidence.
- Treatment: evidence sections/details.
- Interaction: open evidence or related object.
- Effect: moves from capability summary to provenance.

### COMP-D-304 · Source / lens / reload controls
- Information: selected source/lens and reload/query posture.
- Treatment: local control cluster.
- Interaction: change admitted lens or refresh the dossier query.
- Effect: changes what exact capability evidence is being inspected without changing capability identity.

### COMP-D-305 · Dossier sections
- Information: performance, teaching, sources, dependencies, and history sections.
- Treatment: structured dossier sections with progressive disclosure.
- Interaction: navigate/expand section and inspect exact entries.
- Effect: groups evidence by operator question instead of presenting one undifferentiated wall.

### COMP-D-306 · Inline evidence detail / pagination
- Information: selected evidence entry, provenance, related objects, page/cursor state.
- Treatment: bounded inline detail.
- Interaction: paginate and traverse the capability-local evidence records/related objects exposed by the dossier.
- Effect: supports local investigation without losing exact evidence identity.

## VIEW-D-004 · Learning

Purpose: durable candidate transaction replay with retention, rollback, and evidence boundaries.

### COMP-D-401 · Episode/candidate list
- Information: episode/candidate identities and terminal states.
- Treatment: timeline/list/table.
- Interaction: select episode/candidate.
- Effect: updates selection/inspector.

### COMP-D-402 · Candidate transaction narrative
- Information: target capability, parent generation, teaching/assessment/retention phases, terminal outcome.
- Treatment: staged episode detail.
- Interaction: inspect evidence at each stage.
- Effect: explains what happened without converting evidence into unsupported causal claims.

### COMP-D-403 · Retention / rollback evidence
- Information: retention result, reason, rollback boundary, receipts.
- Treatment: state/evidence block.
- Interaction: open exact evidence.
- Effect: traces candidate outcome to durable custody.

### COMP-D-404 · Challenger vs committed comparison
- Information: before/after or challenger/committed state for the candidate transaction.
- Treatment: literal comparison table.
- Interaction: inspect compared values/evidence.
- Effect: shows the measured difference without converting it into a causal story.

### COMP-D-405 · Lifecycle replay stage controls
- Information: the currently inspected candidate stage and available replay stages.
- Treatment: ordered stage navigation.
- Interaction: move between admitted replay stages.
- Effect: repositions the transaction narrative while preserving the same episode/candidate identity.

## VIEW-D-005 · Atlas

Purpose: source-authoritative semantic identity and generation-scoped ABI state; learned similarity is a separate lens.

### COMP-D-501 · Semantic overview
- Information: semantic identities/classes and release-scoped overview.
- Treatment: atlas/table/graph surface.
- Interaction: select semantic object.
- Effect: opens semantic detail and relationships.

### COMP-D-502 · Semantic selection detail
- Information: exact identity, source/ABI relationships, generation context.
- Treatment: detail surface/inspector bridge.
- Interaction: inspect/open related object.
- Effect: preserves source-authoritative semantic navigation.

### COMP-D-503 · Semantic authority lens
- Information: derived similarity where available.
- Treatment: explicitly separate derived view.
- Interaction: compare/explore.
- Effect: prevents learned geometry from masquerading as semantic identity.

### COMP-D-504 · ABI bank map / row resolver
- Information: bank layout, ABI row identity, and exact row resolution.
- Treatment: structured map/table.
- Interaction: select bank/row and inspect exact identity.
- Effect: connects semantic identity to generation-scoped ABI placement.

### COMP-D-505 · Exact semantic identity lookup
- Information: exact semantic identifier and resolution result.
- Treatment: bounded lookup control plus result.
- Interaction: enter/select identity and resolve.
- Effect: provides direct identity access without requiring graph traversal.

## VIEW-D-006 · Model

Purpose: measured model/runtime mechanisms and exact frame compiler inspection.

### COMP-D-601 · Model local navigation
- Information: Neural Runtime / Frame Compiler Explorer peer surfaces and active subsection.
- Treatment: local peer-mode navigation.
- Interaction: switch between Neural Runtime and Frame Compiler Explorer.
- Effect: changes the Model working surface while preserving/restoring the correct shell or fixture context boundary.

### COMP-D-611 · Neural Runtime subview
- Information: the current neural diagnostic mode and all topology/runtime/CCGQA/AttnRes/refinement/instrumentation descendants.
- Treatment: Model peer subview selected through COMP-D-601.
- Interaction: local current/historical fixture-mode selection plus evidence controls in descendant diagnostics.
- Effect: scopes neural diagnostic state separately from Frame Compiler Explorer custody.

### COMP-D-602 · Neural topology/runtime summary
- Information: topology and measured runtime summary.
- Treatment: diagnostic panels.
- Interaction: inspect evidence.
- Effect: situates mechanism telemetry.

### COMP-D-603 · CCGQA / attention / AttnRes
- Information: routing, attention health, recorded mixture weights where fixture-backed.
- Treatment: diagnostic grids/bars/tables.
- Interaction: inspect recorded evidence.
- Effect: mechanism inspection only; no semantic interpretation upgrade.

### COMP-D-604 · Local refinement
- Information: eligibility, quotas, passes, density, resource cost.
- Treatment: histogram + analytical table.
- Interaction: inspect episode receipt.
- Effect: traces local refinement to evidence.

### COMP-D-605 · Instrumentation coverage
- Information: present/unavailable instrumentation and its source explanation.
- Treatment: static coverage list/status.
- Interaction: none directly in the current renderer.
- Effect: prevents synthesized absent metrics.

### COMP-D-606 · Frame Compiler Explorer
- Information: exact frame packing/unpacking receipts and causal visibility.
- Treatment: specialized frame surface.
- Interaction: inspect frame/receipt.
- Effect: exposes exact compiler behavior distinct from neural telemetry.

### COMP-D-607 · Frame generation / query status
- Information: frame query context, generation, request status, and selected example/frontier.
- Treatment: query/status header local to the frame surface.
- Interaction: choose fixture generation; after a page loads, choose an exact compiled example and its prediction frontier.
- Effect: establishes exact frame-inspection custody.

### COMP-D-608 · Compiled-example provenance / packing
- Information: exact compiled example, provenance, packing receipts, and constituent visibility.
- Treatment: receipt-oriented analytical detail.
- Interaction: inspect exact packing/provenance entries.
- Effect: explains how the example was compiled without borrowing authority from the live shell.

### COMP-D-609 · Prediction frontier / legality
- Information: prediction-frontier position and the resulting constituent/codec visibility projection.
- Treatment: frontier selector governing the position disclosures below it.
- Interaction: choose the prediction frontier; position/constituent rows themselves are not selectable.
- Effect: recalculates which source atoms and codec fields are legally visible at the selected frontier.

### COMP-D-610 · Aggregate packing disclosure
- Information: aggregate packing summary across the selected frame/example.
- Treatment: progressively disclosed summary beneath exact frame evidence.
- Interaction: expand/collapse aggregate detail.
- Effect: provides orientation without replacing receipt-level truth.

## VIEW-D-007 · Memory

Purpose: retained Engram allocation/retrieval/correction state without promoting memory hits to truth/capability authority.

### COMP-D-701 · Memory summary
- Information: capacity/allocation, hits/misses, hit/gate-use rates, footprint, read-site receipts.
- Treatment: metric summary.
- Interaction: none/inspect receipts.
- Effect: establishes operational memory posture.

### COMP-D-702 · Memory atlas pages
- Information: aggregate → page → stable motif allocation.
- Treatment: page controls + slot list.
- Interaction: choose page/slot.
- Effect: changes exact memory selection.

### COMP-D-703 · Motif inspector
- Information: key digest, semantic release, address, eligibility, lifetime use, parameter bank, correction state, source/evidence refs, related capabilities/episodes.
- Treatment: exact detail list.
- Interaction: inspect/open relations through global mechanisms.
- Effect: exposes retained identity and provenance.

### COMP-D-704 · Generation comparison
- Information: created/removed/held/requalified identities and allocation/hit/gate deltas.
- Treatment: comparison controls and delta grid.
- Interaction: choose comparison generation.
- Effect: shows literal memory change.

### COMP-D-705 · Rejected candidate boundary
- Information: proposed identity, parent preservation, lack of committed generation/slot.
- Treatment: proof block.
- Interaction: none.
- Effect: demonstrates that candidate-local allocation is not retained memory.

## VIEW-D-008 · Teacher

Purpose: strategy population, measured outcomes, cost/fidelity observations without unsupported ranking.

### COMP-D-801 · Strategy population
- Information: strategy identity/role/status.
- Treatment: cards/table/list.
- Interaction: select strategy.
- Effect: opens descriptive strategy evidence.

### COMP-D-802 · Outcome/cost/fidelity observations
- Information: attempts, retained/no-gain/interference, resource/fidelity evidence.
- Treatment: comparative analytical surface.
- Interaction: inspect related evidence.
- Effect: supports comparison without policy mutation or winner synthesis.

### COMP-D-803 · Fidelity ladder
- Information: strategy evidence at declared fidelity levels such as 2/4/8/16 where the current Teacher projection provides it.
- Treatment: bounded comparative ladder rather than an implied universal ranking.
- Interaction: select/compare supported strategy evidence.
- Effect: shows measured fidelity evidence at common scope.

### COMP-D-804 · Projection boundary
- Information: what the current Teacher snapshot does and does not establish.
- Treatment: concise local guidance with deeper technical detail behind disclosure.
- Interaction: inspect exact evidence.
- Effect: blocks descriptive strategy telemetry from becoming policy authority.

## VIEW-D-009 · SÍ SÉ SON

Purpose: independent Impact, Exigency, and Osmotic Novelty evidence with reversible aggregation and admitted routing rationale.

### COMP-D-906 · As-of fixture selector
- Information: the available retained salience snapshots and which exact snapshot is selected.
- Treatment: compact toolbar of mutually exclusive as-of fixture buttons.
- Interaction: choose a snapshot.
- Effect: re-renders all SÍ SÉ SON evidence, aggregation, provenance and routing panels against that exact selected snapshot.

### COMP-D-901 · Salience observation set
- Information: exact observations and three independent axes.
- Treatment: salience table/cards/plot.
- Interaction: select observation.
- Effect: opens exact salience detail.

### COMP-D-902 · Provenance
- Information: source/evidence identity for the selected salience observation.
- Treatment: compact provenance affordance with exact detail available.
- Interaction: inspect/open evidence.
- Effect: grounds the three salience axes.

### COMP-D-903 · Recursive aggregation
- Information: observation → cluster → pattern → trend aggregation where present.
- Treatment: progressive hierarchy rather than a single “score.”
- Interaction: expand/select aggregation level.
- Effect: preserves reversibility and scale.

### COMP-D-904 · Routing rationale
- Information: reversible aggregate and admitted rationale.
- Treatment: derived summary separated from source axes.
- Interaction: inspect rationale/evidence.
- Effect: explains routing input without pretending aggregate is source truth.

### COMP-D-905 · Projection boundary
- Information: the limits of the current salience projection.
- Treatment: local helper/disclosure.
- Interaction: inspect evidence.
- Effect: prevents salience telemetry from being read as universal decision authority.

## VIEW-D-010 · Corrections

Purpose: correction blast radius, append-only correction history, receipt-backed requalification without implying perfect neural unlearning.

### COMP-D-1001 · Correction history
- Information: correction records and status.
- Treatment: chronology/list.
- Interaction: select correction.
- Effect: opens correction detail.

### COMP-D-1002 · Blast-radius graph/list
- Information: affected artifact classes and exposure paths.
- Treatment: graph/relationship surface with evidence references.
- Interaction: inspect affected node.
- Effect: traces known exposure.

### COMP-D-1003 · Accessible equivalent impact table
- Information: the same affected relationships required to understand the impact graph.
- Treatment: captioned/tabular equivalent.
- Interaction: select affected artifact.
- Effect: preserves the relationship model without requiring graph perception.

### COMP-D-1004 · Requalification state
- Information: receipts and requalification status.
- Treatment: evidence/status surface.
- Interaction: none in the current renderer; the queue is a static descriptive list.
- Effect: shows what has actually been requalified.

### COMP-D-1005 · Append-only correction history
- Information: correction/source/generation history and prior states.
- Treatment: chronological record.
- Interaction: none in the current renderer; the history is a static ordered record.
- Effect: preserves the record rather than replacing prior assertions in place.

## VIEW-D-011 · Lineage

Purpose: immutable accepted-generation lineage and literal structured generation differences.

### COMP-D-1101 · Accepted-generation lineage
- Information: generation, manifest, parent, transition, checkpoint.
- Treatment: lineage graph/list.
- Interaction: select generation/checkpoint.
- Effect: opens exact custody identity.

### COMP-D-1102 · Generation comparison
- Information: literal structured differences.
- Treatment: diff/comparison surface.
- Interaction: select compared generations.
- Effect: shows change without “winner” synthesis.

### COMP-D-1103 · Rejected-candidate non-lineage boundary
- Information: candidate state that did not become accepted lineage.
- Treatment: explicit non-lineage proof/state.
- Interaction: inspect supporting evidence.
- Effect: prevents rejected candidate activity from appearing as an accepted generation.

### COMP-D-1104 · Exact immutable generation node
- Information: selected accepted generation, manifest, checkpoint, parent and transition identity.
- Treatment: exact node dossier.
- Interaction: inspect evidence or choose as a comparison endpoint.
- Effect: anchors lineage navigation to immutable accepted custody.

## VIEW-D-012 · Resources

Purpose: measured resource budgets, exact historical comparison, and spike correlation.

### COMP-D-1201 · Resource headline
- Information: current budget posture.
- Treatment: primary metrics/status.
- Interaction: none/inspect.
- Effect: establishes current resource condition.

### COMP-D-1202 · Metric semantics
- Information: evidence semantics and resource decomposition where instrumented.
- Treatment: grouped metrics.
- Interaction: inspect.
- Effect: separates measured/estimated/unavailable quantities.

### COMP-D-1203 · Memory decomposition / remainder
- Information: memory quantities that can be decomposed and any explicitly unresolved remainder.
- Treatment: grouped resource decomposition.
- Interaction: inspect supporting sample/evidence.
- Effect: avoids pretending an unexplained total has been causally attributed.

### COMP-D-1204 · Compute/length profile
- Information: CPU/memory/MLX/workers/compile/wall cost plus sequence/frame/batch/length statistics.
- Treatment: metric groups.
- Interaction: inspect.
- Effect: decomposes resource cost.

### COMP-D-1205 · Timeline and spike correlation
- Information: resource samples related to episode/batch/checkpoint/preparation/refinement.
- Treatment: wide analytical table.
- Interaction: select resource sample.
- Effect: opens exact related evidence.

### COMP-D-1206 · Historical comparison
- Information: exact generation metric comparison and deltas.
- Treatment: generation form + comparison table.
- Interaction: load exact generation.
- Effect: read-only historical query; no generation is inferred.

## VIEW-D-013 · Evidence

Purpose: exact Mission Control records, provenance links, bounded pagination, literal raw payloads.

### COMP-D-1301 · Evidence query/filter
- Information: query constraints/context.
- Treatment: bounded search/filter controls.
- Interaction: query/paginate.
- Effect: changes evidence result set.

### COMP-D-1305 · Query / degraded state
- Information: loading, ready, query-unavailable/error, page state, coverage, truncation, returned/total counts, and operator-facing error detail.
- Treatment: live status/alert surface immediately below the search controls.
- Interaction: none directly; state changes as bounded queries start/resolve/fail.
- Effect: exposes query health without converting missing/disconnected evidence into an empty successful result.

### COMP-D-1302 · Evidence result list/table
- Information: record identities/types/provenance.
- Treatment: analytical list/table.
- Interaction: select exact record.
- Effect: opens evidence detail and establishes return origin.

### COMP-D-1306 · Traversal / omission status
- Information: degraded/omission markers from the evidence page plus provenance-link traversal failures.
- Treatment: omission/degraded marker section and explicit traversal alert.
- Interaction: provenance/reference buttons remain available where exact refs are present; failed traversal itself has no synthetic fallback.
- Effect: preserves partial/degraded evidence semantics and keeps unresolved provenance visible instead of silently dropping it.

### COMP-D-1303 · Exact record/raw payload
- Information: literal payload and provenance links.
- Treatment: details/raw view.
- Interaction: follow provenance/related object.
- Effect: forensic inspection; never rewritten into friendlier facts.

### COMP-D-1304 · Return to origin
- Information: originating destination/object where Evidence was opened contextually.
- Treatment: return affordance.
- Interaction: activate return.
- Effect: restores investigation path.

## VIEW-D-014 · Operate

Purpose: command boundary, not another dashboard.

### COMP-D-1401 · Action catalog
- Information: supported actions, mutation/read-only posture.
- Treatment: selectable action set.
- Interaction: choose action.
- Effect: initializes exact request form.

### COMP-D-1402 · Exact request
- Information: parameters and dry-run option.
- Treatment: structured JSON/input panel.
- Interaction: edit parameters; run read-only preflight.
- Effect: asks CP05 to resolve target/consequence without mutation.

### COMP-D-1403 · Preflight
- Information: target ref, run/generation, manifest/topology/factory/semantic/source/admission identities, resource profile, expected postcondition, stale conflicts.
- Treatment: resolved consequence panel.
- Interaction: review only.
- Effect: establishes exact authorization target or blocks stale context.

### COMP-D-1404 · Deliberate authorization
- Information: exact phrase for mutation or read-only execution state.
- Treatment: high-salience human gate.
- Interaction: type exact authorization and submit.
- Effect: dispatches only the reviewed exact target; target drift fails closed.

### COMP-D-1405 · Receipt/readback/reconciliation
- Information: operation ID, receipt state, postcondition/error refs, bounded logs, literal inspection.
- Treatment: lifecycle + receipt actions.
- Interaction: open receipt/postcondition; reconcile unknown outcome.
- Effect: proves outcome or preserves uncertainty without blind retry.

## Concern overlay

Every component above inherits the concern profile for its containing shell/view unless the node text states a stricter rule. This overlay records both **current implementation posture** and **required redesign posture**. It must not be read as claiming that localization/test-hook work already exists: as of the #1124 baseline, human-facing strings remain largely inline and Mission Control has zero implemented `data-test-id` hooks.

| Scope | State concerns | Authority concerns | Accessibility concerns | Required i18n posture | Required test-hook posture |
| --- | --- | --- | --- | --- | --- |
| SHELL-D-001 / COMP-D-001..016 | STATE-D-001..009; route, selection, defensive, investigation, focus/display, fixture custody | Shell may display source/derived/operator-local facts but never upgrades their authority; mutation gating follows verified context | landmarks, skip link, roving navigation, dialog/inert semantics, focus return, live regions, target size, reduced motion/forced colors | all human labels, summaries, help, state explanations and recovery copy tokenized; machine IDs remain data | `shell-*`, `nav-destination-*`, `investigation-*`, `inspector-*`, `palette-*`; exact IDs unique |
| VIEW-D-001 Mission Control / COMP-D-101..107 | live overview query families; startup projection; defensive projection; no historical event refresh | summary only; retained/current work/evidence distinctions remain explicit | heading/focus order, status non-color cues, inspectable summaries keyboard-reachable | all startup/overview questions, labels, health copy, attention guidance | `home-*` |
| VIEW-D-002 School / COMP-D-201..209 | matrix UI, curriculum mode, selected capability/node, filters/sort/page, context-bound async epoch | declared curriculum/topology and measured capability evidence stay distinct | matrix orientation, keyboard graph selection, equivalent relationship table, scale disclosure, scroll discoverability | filters, column labels, explanations, topology/scale guidance | `school-*`, `school-capability-row-*`, `curriculum-*` |
| VIEW-D-003 Capability Explorer / COMP-D-301..306 | selected capability, lens/source, cursor/page, evidence query epoch | measured chronology/source support only; no inferred causes | dossier navigation, bounded pagination, exact-value access, focus on loaded detail | section labels, helper copy, evidence controls | `capability-*`, `capability-evidence-*` |
| VIEW-D-004 Learning / COMP-D-401..405 | selected episode/candidate and replay stage | episode evidence, candidate state, retention/rollback custody remain separate | ordered stage controls, comparison tables, status announcements | stage labels, terminal/retention explanations, comparison labels | `learning-*`, `learning-stage-*` |
| VIEW-D-005 Atlas / COMP-D-501..505, 521 | overview/selection/lens/bank/request epoch | canonical semantic identity is source-authoritative; learned similarity remains derived | graph/table keyboard paths, exact lookup labels, nonvisual relationship access | lens/search/helper text tokenized; semantic IDs remain data | `atlas-*`, `atlas-semantic-*` |
| VIEW-D-006 Model / COMP-D-601..611 | model subsection, neural fixture mode, frame request epoch, saved return context | measured runtime vs fixture-backed diagnostics vs frame receipts remain explicit | peer-mode navigation, tables/progress readable by AT, fixture posture announced | diagnostic labels/help/state copy; raw IDs/receipts remain data | `model-*`, `neural-*`, `frame-*` |
| VIEW-D-007 Memory / COMP-D-701..705, 733 | generation, selected page/slot, compare generation | retrieval telemetry is operational evidence, never semantic/capability authority | page/slot controls, detail lists, comparison semantics, non-color held/rejected cues | labels/help/compare copy tokenized; stable motif IDs remain data | `memory-*`, `memory-slot-*` |
| VIEW-D-008 Teacher / COMP-D-801..804 | strategy selection/comparison scope and fidelity level | descriptive strategy outcomes/cost/fidelity only; no unsupported winner/policy authority | strategy selection, comparison table/ladder reading order, state cues | strategy-role labels, comparison guidance, projection-boundary copy | `teacher-*`, `teacher-strategy-*` |
| VIEW-D-009 SÍ SÉ SON / COMP-D-901..906 | selected as-of snapshot/observation/aggregation level | Impact, Exigency, Osmotic Novelty remain independent; aggregate/routing rationale derived | snapshot selector, axis labels not color-only, aggregation hierarchy navigable, evidence links named | snapshot labels, axis names/explanations/rationale labels tokenized; source IDs remain data | `salience-*`, `salience-observation-*` |
| VIEW-D-010 Corrections / COMP-D-1001..1005 | selected correction/affected artifact/requalification state | known exposure and receipt-backed requalification only; no perfect-unlearning claim | graph has equivalent table, history order explicit, state cues non-color | correction/requalification/history guidance tokenized | `corrections-*`, `correction-artifact-*` |
| VIEW-D-011 Lineage / COMP-D-1101..1104 | selected generation/checkpoint and diff endpoints | accepted immutable lineage only; rejected candidates explicitly excluded | DAG/table equivalence, exact node inspection, diff table orientation | lineage/diff guidance tokenized; hashes/checkpoints remain data | `lineage-*`, `lineage-generation-*` |
| VIEW-D-012 Resources / COMP-D-1201..1206 | current projection, exact comparison generation, resource-only live refresh | measured/derived/estimated/unavailable distinctions preserved; correlation is not causation | metric units/denominators announced, wide tables own overflow, comparison forms labeled | metric labels/units/help/status copy tokenized | `resources-*`, `resource-sample-*` |
| VIEW-D-013 Evidence / COMP-D-1301..1306 | criteria/page/results/selection/raw/traversal/query epoch; degraded/query/traversal failures | literal evidence/provenance is primary; raw payload may stay technical; missing/degraded records remain explicit | search/pagination/detail semantics, live query/traversal status, raw payload readable, explicit return origin | controls, states and explanations tokenized; literal payload/identifiers not translated | `evidence-*`, `evidence-record-*` |
| VIEW-D-014 Operate / COMP-D-1400..1405 | command phase, target conflicts, authorization, operation readback | CP05 exact target/consequence/receipt authority; unknown outcome remains unknown | deliberate gate focus/order, error association, no hidden mutation, receipt/readback announcements | action/help/error/reconciliation copy tokenized; exact target/operation IDs remain data | `operate-*`, `operate-action-*` |

For repeated elements, exact IDs are never duplicated. Repeated rows/nodes use a documented prefix plus a stable identity suffix. Functional `data-*` attributes used by runtime behavior are not substitutes for these test hooks.

## Atlas-derived task groups for later navigation design

These are design hypotheses for decomposition, not authorization to change navigation yet:

1. **Overview & learning**: VIEW-D-001 Mission Control, VIEW-D-002 School, VIEW-D-003 Capability Explorer, VIEW-D-004 Learning.
2. **Representation & mechanisms**: VIEW-D-005 Atlas, VIEW-D-006 Model, VIEW-D-007 Memory.
3. **Decision & correction**: VIEW-D-008 Teacher, VIEW-D-009 SÍ SÉ SON, VIEW-D-010 Corrections.
4. **Provenance & operations**: VIEW-D-011 Lineage, VIEW-D-012 Resources, VIEW-D-013 Evidence, VIEW-D-014 Operate.

Any final grouping must be tested against real operator journeys and must preserve direct command-palette/deep-link access.

## Recursive constituent trees

These trees are the authoritative answer to **how far down the atlas descends**. Published parent IDs remain stable. Dotted descendants are structural children. A terminal node is tagged by what it actually contributes: **datum**, **control**, **state**, **treatment**, **interaction**, **effect**, or **contract**. If a node still contains several such things, it is not a leaf.

### SHELL-D-001 · Application shell

```mermaid
mindmap
  root((SHELL-D-001 Application shell))
    COMP-D-015 Skip-to-main access path
      COMP-D-015.1 Skip to main content link control
      COMP-D-015.2 main-content focus target effect-target
      COMP-D-015.3 hidden-until-focus treatment
    COMP-D-001 Primary navigation rail
      COMP-D-001.1 Brand identity
        COMP-D-001.1.1 B brand mark datum
        COMP-D-001.1.2 Bilqis product name datum
        COMP-D-001.1.3 Mission Control subtitle datum
      COMP-D-001.2 Destination navigator
        COMP-D-001.2.01 Mission Control control-instance
        COMP-D-001.2.02 School control-instance
        COMP-D-001.2.03 Capability Explorer control-instance
        COMP-D-001.2.04 Learning control-instance
        COMP-D-001.2.05 Atlas control-instance
        COMP-D-001.2.06 Model control-instance
        COMP-D-001.2.07 Memory control-instance
        COMP-D-001.2.08 Teacher control-instance
        COMP-D-001.2.09 SI SE SON control-instance
        COMP-D-001.2.10 Corrections control-instance
        COMP-D-001.2.11 Lineage control-instance
        COMP-D-001.2.12 Resources control-instance
        COMP-D-001.2.13 Evidence control-instance
        COMP-D-001.2.14 Operate control-instance
      COMP-D-001.3 Destination interaction-state contract
        COMP-D-001.3.1 aria-current active-page state
        COMP-D-001.3.2 availability and Operate mutation gate state
        COMP-D-001.3.3 click navigation and title-focus effect
        COMP-D-001.3.4 roving Arrow Home End keyboard interaction
      COMP-D-001.4 Command utility trigger
        COMP-D-001.4.1 Command label datum
        COMP-D-001.4.2 CmdK CtrlK shortcut hint datum
        COMP-D-001.4.3 click-open palette effect
      COMP-D-001.5 Rail treatment states
        COMP-D-001.5.1 desktop sticky full-height scroll treatment
        COMP-D-001.5.2 <=980 first-letter collapsed-label treatment
    COMP-D-002 Context bar
      COMP-D-002.1 Identity cluster
        COMP-D-002.1.1 mode-posture badge datum-state
        COMP-D-002.1.2 run identity datum
        COMP-D-002.1.3 generation-manifest identity datum
      COMP-D-002.2 Context fact grid
        COMP-D-002.2.1 visible-hidden context-grid state
        COMP-D-002.2.2 Service bootstrap fact datum
        COMP-D-002.2.3 Learner bootstrap fact datum
        COMP-D-002.2.4 Optimizer bootstrap fact datum
        COMP-D-002.2.5 Telemetry bootstrap fact datum
        COMP-D-002.2.6 Topology datum
        COMP-D-002.2.7 Factory release datum
        COMP-D-002.2.8 Semantic release datum
        COMP-D-002.2.9 Optimizer datum
        COMP-D-002.2.10 Admission lease datum
        COMP-D-002.2.11 Correction frontier datum
        COMP-D-002.2.12 Resource health datum
        COMP-D-002.2.13 Coverage datum
      COMP-D-002.3 Context actions
        COMP-D-002.3.1 Run selector disabled single-option control
        COMP-D-002.3.2 As-of generation selector control
        COMP-D-002.3.3 generation-change to historical-lens effect
        COMP-D-002.3.4 freshness badge datum-state
        COMP-D-002.3.5 density cycle control-effect
        COMP-D-002.3.6 theme toggle control-effect
      COMP-D-002.4 Context posture treatment
        COMP-D-002.4.1 verified-vs-empty layout state
        COMP-D-002.4.2 live treatment
        COMP-D-002.4.3 historical pattern-double-border treatment
        COMP-D-002.4.4 stale dashed treatment
        COMP-D-002.4.5 unknown dotted treatment
      COMP-D-002.5 Responsive context layouts
        COMP-D-002.5.1 >1320 three-column treatment
        COMP-D-002.5.2 981-1320 second-row facts treatment
        COMP-D-002.5.3 <=980 wrapped two-column treatment
        COMP-D-002.5.4 <=640 single-column treatment
    COMP-D-003 Global investigation strip
      COMP-D-003.1 toolbar row layout host treatment
      COMP-D-003.2 disclosed panel host state
      COMP-D-003.3 stable object-ref projection contract
      COMP-D-003.4 global selected-related highlight interaction-effect
      COMP-D-003.5 inspector-open geometry effect
      COMP-D-010 Time lens
        COMP-D-010.1 exact generation number input control
        COMP-D-010.2 Apply historical control
        COMP-D-010.3 Use verified current control-state
        COMP-D-010.4 invalid-generation announcement state
        COMP-D-010.5 historical lens mutation-disable effect
        COMP-D-010.6 verified-current restore effect
      COMP-D-011 Compare workspace
        COMP-D-011.1 Compare toggle and slot count control
        COMP-D-011.2 left stable-ref slot and Clear control
        COMP-D-011.3 right stable-ref slot and Clear control
        COMP-D-011.4 comparison doctrine-status datum
        COMP-D-011.5 Dimension Left Right State table treatment
        COMP-D-011.6 mismatch-unavailable reason datum
        COMP-D-011.7 comparison adapter-state contract
      COMP-D-012 Pins
        COMP-D-012.1 Pins toggle and count control
        COMP-D-012.2 empty-pins state
        COMP-D-012.3 pin list
          COMP-D-012.3.1 kind-generation datum
          COMP-D-012.3.2 label-run datum
          COMP-D-012.3.3 Open exact pin control-effect
          COMP-D-012.3.4 Remove pin control-effect
        COMP-D-012.4 local persistence identity-limit contract
        COMP-D-012.5 open-pin historical rehydration effect
      COMP-D-013 Annotations
        COMP-D-013.1 Notes toggle and count control
        COMP-D-013.2 exact-context filter state
        COMP-D-013.3 empty-note state
        COMP-D-013.4 note list
          COMP-D-013.4.1 non-authoritative marker datum
          COMP-D-013.4.2 author timestamp scope datum
          COMP-D-013.4.3 note body datum
          COMP-D-013.4.4 exact target identity datum
        COMP-D-013.5 annotation form
          COMP-D-013.5.1 target label datum
          COMP-D-013.5.2 required max-2000 textarea control
          COMP-D-013.5.3 local-authority disclaimer datum
          COMP-D-013.5.4 Save note control
          COMP-D-013.5.5 no-selection prompt state
        COMP-D-013.6 validation-save announcement effect
        COMP-D-013.7 local persistence schema-limit-authority contract
        COMP-D-013.8 persistence-failure announcement effect
      COMP-D-014 App URI and deep link
        COMP-D-014.1 no-selection prompt state
        COMP-D-014.2 Exact app URI label datum
        COMP-D-014.3 rendered bilqis URI datum
        COMP-D-014.4 URI run-generation-kind-id-fixture construction contract
        COMP-D-014.5 object-kind owner resolution contract
        COMP-D-014.6 URI hydration to historical selection effect
        COMP-D-014.7 hash route serialization contract
        COMP-D-014.8 hash parsing-hydration contract
        COMP-D-014.9 hashchange rerender effect
        COMP-D-014.10 replaceState hash-sync effect
        COMP-D-014.11 Model subsection derivation contract
    COMP-D-004 Defensive-state banner
      COMP-D-004.1 visibility and status-alert role state
      COMP-D-004.2 bootstrap title-description-run-generation-error payload datum
      COMP-D-004.3 bootstrap phases
        COMP-D-004.3.1 connecting state
        COMP-D-004.3.2 discovering state
        COMP-D-004.3.3 telemetry-pending state
        COMP-D-004.3.4 learner-unavailable state
        COMP-D-004.3.5 failed state
      COMP-D-004.4 ready defensive label-description-source-mutation payload datum
      COMP-D-004.5 defensive profile family
        COMP-D-004.5.01 live
        COMP-D-004.5.02 loading
        COMP-D-004.5.03 progressive
        COMP-D-004.5.04 empty
        COMP-D-004.5.05 stale
        COMP-D-004.5.06 partial
        COMP-D-004.5.07 offline
        COMP-D-004.5.08 denied
        COMP-D-004.5.09 revoked
        COMP-D-004.5.10 unavailable
        COMP-D-004.5.11 incompatible-version
        COMP-D-004.5.12 timeout
        COMP-D-004.5.13 duplicate-action
        COMP-D-004.5.14 session-restarting
        COMP-D-004.5.15 service-restarting
        COMP-D-004.5.16 historical-unavailable
        COMP-D-004.5.17 malformed-payload
        COMP-D-004.5.18 unsupported-payload
        COMP-D-004.5.19 outcome-unknown
        COMP-D-004.5.20 unknown
      COMP-D-004.6 reconnect availability gate state
      COMP-D-004.7 Reconnect control
      COMP-D-004.8 reconnect transition
        COMP-D-004.8.1 reset frame custody-disable mutation effect
        COMP-D-004.8.2 preserve route effect
        COMP-D-004.8.3 loading-connecting render effect
        COMP-D-004.8.4 CP01 connect-discover interaction
        COMP-D-004.8.5 OperatorView validate-cache effect
        COMP-D-004.8.6 validated cache fallback effect
        COMP-D-004.8.7 live-no-projection progressive branch
        COMP-D-004.8.8 total-failure defensive branch
        COMP-D-004.8.9 verified-success branch
        COMP-D-004.8.10 recovery announcement effect
      COMP-D-004.9 bounded validated OperatorView cache contract
      COMP-D-004.10 non-color dashed-double-dotted treatment families
    COMP-D-005 Destination header
      COMP-D-005.1 Current destination eyebrow datum
      COMP-D-005.2 dynamic destination H1 datum-focus-target
      COMP-D-005.3 dynamic purpose-boundary summary datum
      COMP-D-005.4 aria-labelledby host relationship contract
      COMP-D-005.5 post-navigation title-focus effect
    COMP-D-006 Destination-local subnavigation
      COMP-D-006.1 Model-only visibility gate state
      COMP-D-006.2 Neural Runtime control
      COMP-D-006.3 Frame Compiler Explorer control
      COMP-D-006.4 aria-pressed subsection state
      COMP-D-006.5 subsection-switch clear-selection effect
      COMP-D-006.6 route-derived subsection contract
      COMP-D-006.7 frame context-custody save-install-restore contract
    COMP-D-007 Global inspector
      COMP-D-007.1 open-closed inert aria-hidden slide state-treatment
      COMP-D-007.2 Global inspector eyebrow datum
      COMP-D-007.3 selected title or No selection datum
      COMP-D-007.4 Close control
      COMP-D-007.5 exact detail list
        COMP-D-007.5.1 object class datum
        COMP-D-007.5.2 identity datum
        COMP-D-007.5.3 posture datum
        COMP-D-007.5.4 generation datum
        COMP-D-007.5.5 evidence posture datum
        COMP-D-007.5.6 domain supplied details datum-family
      COMP-D-007.6 action group
        COMP-D-007.6.1 Open in owning view control
        COMP-D-007.6.2 Open evidence control
        COMP-D-007.6.3 Pin-Unpin control
        COMP-D-007.6.4 Compare left control
        COMP-D-007.6.5 Compare right control
        COMP-D-007.6.6 Add operator note control
      COMP-D-007.7 action enablement and pin-label state
      COMP-D-007.8 open capture-focus announce effect
      COMP-D-007.9 close restore-focus Escape effect
      COMP-D-007.10 owner navigation effect
      COMP-D-007.11 Evidence origin-preservation effect
      COMP-D-007.12 pin-compare-note interaction effects
      COMP-D-007.13 fixed side-plane geometry treatment
    COMP-D-008 Command palette
      COMP-D-008.1 modal dialog-backdrop treatment
      COMP-D-008.2 Keyboard navigation eyebrow datum
      COMP-D-008.3 Command palette title datum
      COMP-D-008.4 Close control
      COMP-D-008.5 destination-jump mutation-gate guidance datum
      COMP-D-008.6 destination option family
        COMP-D-008.6.01 Mission Control
        COMP-D-008.6.02 School
        COMP-D-008.6.03 Capability Explorer
        COMP-D-008.6.04 Learning
        COMP-D-008.6.05 Atlas
        COMP-D-008.6.06 Model
        COMP-D-008.6.07 Memory
        COMP-D-008.6.08 Teacher
        COMP-D-008.6.09 SI SE SON
        COMP-D-008.6.10 Corrections
        COMP-D-008.6.11 Lineage
        COMP-D-008.6.12 Resources
        COMP-D-008.6.13 Evidence
        COMP-D-008.6.14 Operate
      COMP-D-008.7 null-shell and Operate availability state
      COMP-D-008.8 global CmdK CtrlK interaction
      COMP-D-008.9 open capture-focus first-enabled effect
      COMP-D-008.10 roving Arrow Home End interaction
      COMP-D-008.11 option activation navigate-close-focus effect
      COMP-D-008.12 explicit-native close interaction
      COMP-D-008.13 close focus-restoration effect
    COMP-D-009 Fixture provenance boundary
      COMP-D-009.1 independent-fixture context note
        COMP-D-009.1.1 provenance warning datum
        COMP-D-009.1.2 School-Learning-Model-Memory-Teacher visibility state
      COMP-D-009.2 Reference fixture card
        COMP-D-009.2.1 status-dot treatment
        COMP-D-009.2.2 Reference fixture label datum
        COMP-D-009.2.3 test-reference disclaimer datum
        COMP-D-009.2.4 demo inspect action family
          COMP-D-009.2.4.01 capability
          COMP-D-009.2.4.02 episode
          COMP-D-009.2.4.03 semantic
          COMP-D-009.2.4.04 frame
          COMP-D-009.2.4.05 memory
          COMP-D-009.2.4.06 checkpoint
          COMP-D-009.2.4.07 evidence
          COMP-D-009.2.4.08 correction
          COMP-D-009.2.4.09 warning
        COMP-D-009.2.5 demo inspect to global-inspector effect
      COMP-D-009.3 visual-language catalog reference surface
      COMP-D-009.4 mapped-fallback-Operate visibility override state
    COMP-D-016 Polite live announcer
      COMP-D-016.1 sr-only aria-live atomic region treatment
      COMP-D-016.2 clear-then-microtask repeated-message announcement effect
```

### VIEW-D-001 · Mission Control

```mermaid
mindmap
  root((VIEW-D-001 Mission Control))
    COMP-D-107 Startup state
      COMP-D-107.1 startup posture narrative datum
      COMP-D-107.2 startup fact set
        COMP-D-107.2.1 accepted generation datum
        COMP-D-107.2.2 optimizer step datum
        COMP-D-107.2.3 trainer running-stopped-unknown state
        COMP-D-107.2.4 stage datum
        COMP-D-107.2.5 learning telemetry waiting-none state
      COMP-D-107.3 next-step Operate-CLI guidance datum
    COMP-D-101 Learner posture
      COMP-D-101.1 provenance and learning verdict datum-state
      COMP-D-101.2 five-question strip
        COMP-D-101.2.1 RUNNING datum
        COMP-D-101.2.2 LEARNING datum
        COMP-D-101.2.3 WORK datum
        COMP-D-101.2.4 REGRESSION datum
        COMP-D-101.2.5 INVALIDITY datum
    COMP-D-104 Health strip
      COMP-D-104.1 Learning card
        COMP-D-104.1.1 latest school score datum
        COMP-D-104.1.2 best school score datum
        COMP-D-104.1.3 whole-school growth datum
        COMP-D-104.1.4 G-RTN datum
        COMP-D-104.1.5 P-RET datum
        COMP-D-104.1.6 retained optimizer steps datum
        COMP-D-104.1.7 capability-state badge datum-state
      COMP-D-104.2 Curriculum card
        COMP-D-104.2.1 qualified capabilities datum
        COMP-D-104.2.2 observed debt datum
        COMP-D-104.2.3 active concepts datum
        COMP-D-104.2.4 ready datum
        COMP-D-104.2.5 held datum
        COMP-D-104.2.6 implementation-uncovered datum
        COMP-D-104.2.7 school-state badge datum-state
      COMP-D-104.3 Runtime card
        COMP-D-104.3.1 elapsed datum
        COMP-D-104.3.2 visits datum
        COMP-D-104.3.3 visit rate datum
        COMP-D-104.3.4 retained candidates datum
        COMP-D-104.3.5 rejected candidates datum
        COMP-D-104.3.6 accepted steps per hour datum
        COMP-D-104.3.7 run-state badge datum-state
      COMP-D-104.4 System card
        COMP-D-104.4.1 unified memory pressure datum
        COMP-D-104.4.2 peak memory datum
        COMP-D-104.4.3 disk reserve datum
        COMP-D-104.4.4 correction-requal debt datum
        COMP-D-104.4.5 hard warnings datum
        COMP-D-104.4.6 resource-state badge datum-state
    COMP-D-102 Learning pulse
      COMP-D-102.1 pulse header and event-count datum
      COMP-D-102.2 repeated event action family
        COMP-D-102.2.1 event kind datum
        COMP-D-102.2.2 event label datum
        COMP-D-102.2.3 event detail datum
        COMP-D-102.2.4 inspect target control-effect
      COMP-D-102.3 no-evidenced-events state
    COMP-D-105 Current work
      COMP-D-105.1 OBSERVED-UNAVAILABLE header state
      COMP-D-105.2 transaction identity facts
        COMP-D-105.2.1 target capability datum
        COMP-D-105.2.2 strategy datum
        COMP-D-105.2.3 candidate intent datum
        COMP-D-105.2.4 source family datum
      COMP-D-105.3 assessment facts
        COMP-D-105.3.1 target assessment datum
        COMP-D-105.3.2 protected assessment datum
    COMP-D-106 Compact School map
      COMP-D-106.1 header and row-count datum
      COMP-D-106.2 capability table
        COMP-D-106.2.1 capability identity drill-through control
        COMP-D-106.2.2 Now datum
        COMP-D-106.2.3 Best datum
        COMP-D-106.2.4 Delta datum
        COMP-D-106.2.5 Debt datum
        COMP-D-106.2.6 Retention datum
        COMP-D-106.2.7 Status datum
    COMP-D-103 Actionable attention
      COMP-D-103.1 attention count datum
      COMP-D-103.2 repeated actionable item family
        COMP-D-103.2.1 kind datum
        COMP-D-103.2.2 label datum
        COMP-D-103.2.3 detail datum
        COMP-D-103.2.4 inspect target control-effect
      COMP-D-103.3 no-actionable-concerns state
```

### VIEW-D-002 · School

```mermaid
mindmap
  root((VIEW-D-002 School))
    COMP-D-204 Peer subnavigation
      COMP-D-204.1 Capability matrix control
      COMP-D-204.2 Curriculum Semantic Atlas control
      COMP-D-204.3 current-peer state
    COMP-D-201 Capability matrix
      COMP-D-207 Matrix controls
        COMP-D-207.1 filter-set controls
        COMP-D-207.2 Group by family control
        COMP-D-207.3 Export displayed identities control-effect
        COMP-D-207.4 sortable header controls
        COMP-D-207.5 previous-next pagination controls
      COMP-D-201.1 matrix coverage and range datum
      COMP-D-201.2 metric-definition guidance datum
      COMP-D-201.3 matrix table
        COMP-D-201.3.1 family grouping row datum
        COMP-D-201.3.2 capability identity select control
        COMP-D-201.3.3 WAS-TOP-NOW-ALL-growth-debt-retention metrics datum-family
        COMP-D-201.3.4 visits-retained-last-gain-last-regression datum-family
        COMP-D-201.3.5 strategy-source-family datum-family
        COMP-D-201.3.6 source-implementation-qualification state stack
    COMP-D-202 Dependency graph
      COMP-D-202.1 graph-vs-table toggle control
      COMP-D-202.2 legend and screen-reader operation guidance
      COMP-D-202.3 graph canvas
        COMP-D-202.3.1 prerequisite-dependent edge family
        COMP-D-202.3.2 capability node family
          COMP-D-202.3.2.1 identity datum
          COMP-D-202.3.2.2 lifecycle-eligibility-mastery-debt state datum
          COMP-D-202.3.2.3 keyboard-pointer select interaction
      COMP-D-202.4 equivalent dependency table
        COMP-D-202.4.1 relation datum
        COMP-D-202.4.2 capability identity datum
    COMP-D-203 Curriculum semantic atlas
      COMP-D-203.1 fixture-context provenance boundary datum
      COMP-D-205 Curriculum controls
        COMP-D-205.1 search-find control
        COMP-D-205.2 Jump to active control
        COMP-D-205.3 prerequisite-both-unlocks trace-mode controls
        COMP-D-205.4 grade-state-family-attention-new-only filter controls
        COMP-D-205.5 Reset-focus-all control
        COMP-D-205.6 async search-trace live status
      COMP-D-203.2 Topology panel
        COMP-D-203.2.1 legend and declared-edge doctrine datum
        COMP-D-203.2.2 foundation-current-forward grade strata treatment
        COMP-D-203.2.3 declared prerequisite edge canvas
        COMP-D-203.2.4 curriculum node family
          COMP-D-203.2.4.1 capability identity datum
          COMP-D-203.2.4.2 semantic label-ID-authority datum
          COMP-D-203.2.4.3 grade-lifecycle-qualification datum
          COMP-D-203.2.4.4 NOW-TOP-debt datum
          COMP-D-203.2.4.5 blocker-state datum
          COMP-D-203.2.4.6 select interaction
        COMP-D-203.2.5 prerequisite-dependent relationship summary datum
      COMP-D-206 Selected-node dossier
        COMP-D-206.1 identity-state header datum
        COMP-D-206.2 identity-metrics-provenance fact list
        COMP-D-206.3 Why blocked rationale datum-state
        COMP-D-206.4 bounded event history datum-family
        COMP-D-206.5 downstream-consequence disclosure control-state
        COMP-D-206.6 canonical semantic binding resolver control-state-effect
        COMP-D-206.7 cross-view School-Capability-Atlas-Lineage-Evidence actions
      COMP-D-208 Semantic equivalent table
        COMP-D-208.1 row family
          COMP-D-208.1.1 capability select control
          COMP-D-208.1.2 semantic identity datum
          COMP-D-208.1.3 grade-state datum
          COMP-D-208.1.4 prerequisite-dependent datum
          COMP-D-208.1.5 evidence datum
      COMP-D-209 Scale disclosure
        COMP-D-209.1 243-row grade-family summary disclosure
        COMP-D-209.2 family focus control
        COMP-D-209.3 bounded family expansion
        COMP-D-209.4 selected semantic prerequisite-dependent datum
        COMP-D-209.5 bounded transitive-unlocks datum-state
```

### VIEW-D-003 · Capability Explorer

```mermaid
mindmap
  root((VIEW-D-003 Capability Explorer))
    COMP-D-304 Source-lens controls
      COMP-D-304.1 data-source selector control
      COMP-D-304.2 exact Run Generation Capability as-of form control
    COMP-D-301 Capability identity-header
      COMP-D-301.1 dossier status-provenance notice datum-state
      COMP-D-301.2 exact name and capability ID datum
      COMP-D-301.3 Reload dossier control-effect
      COMP-D-301.4 Load more capabilities cursor control-effect
    COMP-D-302 Measurements and history
      COMP-D-302.1 metric strip
        COMP-D-302.1.1 NOW datum-origin
        COMP-D-302.1.2 TOP datum-origin
        COMP-D-302.1.3 Total datum-origin
        COMP-D-302.1.4 Debt datum-origin
        COMP-D-302.1.5 Retention datum-origin
        COMP-D-302.1.6 Eligibility datum-origin
        COMP-D-302.1.7 Qualification datum-origin
        COMP-D-302.1.8 Source datum-origin
      COMP-D-302.2 Learning-history chronology
    COMP-D-305 Dossier sections
      COMP-D-305.1 section navigation controls
      COMP-D-305.2 performance section
      COMP-D-305.3 teaching section
      COMP-D-305.4 sources section
      COMP-D-305.5 dependencies section
      COMP-D-305.6 history section
      COMP-D-305.7 repeated dossier-entry family
        COMP-D-305.7.1 entry kind-label-generation-time datum
        COMP-D-305.7.2 fact list with origin-state datum-family
        COMP-D-305.7.3 evidence-related-object disclosure controls
    COMP-D-303 Source-evidence layer
      COMP-D-303.1 exact dossier identity-provenance disclosure
      COMP-D-303.2 projection marker disclosure
    COMP-D-306 Inline evidence detail
      COMP-D-306.1 evidence identity-query state datum
      COMP-D-306.2 selected entry literal payload datum
      COMP-D-306.3 evidence-link family
        COMP-D-306.3.1 record-family selector control
        COMP-D-306.3.2 exact-record traversal control-effect
      COMP-D-306.4 next-page evidence-links control-effect
      COMP-D-306.5 returned-record payload datum
```

### VIEW-D-004 · Learning

```mermaid
mindmap
  root((VIEW-D-004 Learning))
    COMP-D-401 Episode selector
      COMP-D-401.1 repeated episode option
        COMP-D-401.1.1 CP03 record identity datum
        COMP-D-401.1.2 capability datum
        COMP-D-401.1.3 terminal state datum
        COMP-D-401.1.4 retention reason datum
        COMP-D-401.1.5 choose-episode interaction-effect
    COMP-D-401.2 exact CP03 record deep-link datum
    COMP-D-402 Candidate transaction
      COMP-D-402.1 episode identity and terminal header datum-state
      COMP-D-402.2 Inspect candidate control-effect
      COMP-D-402.3 custody facts
        COMP-D-402.3.1 candidate ID datum
        COMP-D-402.3.2 CP03 record ID datum
        COMP-D-402.3.3 target capability datum
        COMP-D-402.3.4 parent generation datum
      COMP-D-402.4 teaching-work facts
        COMP-D-402.4.1 strategy datum
        COMP-D-402.4.2 source family datum
        COMP-D-402.4.3 lesson family datum
        COMP-D-402.4.4 intended-attempted-retained steps datum
      COMP-D-402.5 terminal-resource facts
        COMP-D-402.5.1 duration datum
        COMP-D-402.5.2 command state datum
        COMP-D-402.5.3 retention reason datum
        COMP-D-402.5.4 peak memory datum
        COMP-D-402.5.5 step rate datum
        COMP-D-402.5.6 resource coverage datum
    COMP-D-403 Retention-rollback evidence
      COMP-D-403.1 retained accepted-generation transition state-datum
      COMP-D-403.2 pending-unknown reconciliation state
      COMP-D-403.3 rejected classification and reason state-datum
      COMP-D-403.4 rollback invariant proof grid
        COMP-D-403.4.1 parent neural identity unchanged datum
        COMP-D-403.4.2 parent optimizer identity unchanged datum
        COMP-D-403.4.3 parent allocation identity unchanged datum
        COMP-D-403.4.4 retained optimizer steps zero datum
        COMP-D-403.4.5 child generation none datum
    COMP-D-404 Challenger-committed comparison
      COMP-D-404.1 before-challenger-committed-coverage table datum-family
      COMP-D-404.2 rejected-candidate interpretation boundary datum
    COMP-D-405 Lifecycle replay
      COMP-D-405.1 stage range slider control
      COMP-D-405.2 ordered stage button list control-family
      COMP-D-405.3 selected-stage detail
        COMP-D-405.3.1 stage label-state-detail datum
        COMP-D-405.3.2 stage evidence action family
        COMP-D-405.3.3 no-durable-evidence state
```

### VIEW-D-005 · Atlas

```mermaid
mindmap
  root((VIEW-D-005 Atlas))
    COMP-D-521 Whole-view request state
      COMP-D-521.1 LOADING state
      COMP-D-521.2 ERROR state
      COMP-D-521.3 stale-detail replacement effect
    COMP-D-501 Semantic overview
      COMP-D-501.1 Active count datum
      COMP-D-501.2 Source eligible count datum
      COMP-D-501.3 Held count datum
      COMP-D-501.4 Learned edges count datum
    COMP-D-503 Semantic authority lens
      COMP-D-503.1 canonical-vs-learned lens control
      COMP-D-503.2 canonical-equivalence warning datum
    COMP-D-504 ABI bank map-row resolver
      COMP-D-504.1 bank-card list control-family
      COMP-D-504.2 no-bank state
      COMP-D-504.3 exact bank-row resolver form control
    COMP-D-505 Exact semantic lookup
      COMP-D-505.1 exact semantic ID form control
      COMP-D-505.2 held-source-mappings preview
      COMP-D-505.3 no-held-mappings state
    COMP-D-502 Semantic selection detail
      COMP-D-502.1 selected identity-kind heading datum
      COMP-D-502.2 HELD identity state
      COMP-D-502.3 source revision-loci-ABI facts datum-family
      COMP-D-502.4 generation admission-new-exercised-requal facts datum-family
      COMP-D-502.5 capability-frame bindings datum-family
      COMP-D-502.6 lens-dependent canonical-similarity relationships datum-family
      COMP-D-502.7 no-selection guidance state
```

### VIEW-D-006 · Model

```mermaid
mindmap
  root((VIEW-D-006 Model))
    COMP-D-601 Model local navigation
      COMP-D-601.1 Neural Runtime peer control
      COMP-D-601.2 Frame Compiler Explorer peer control
      COMP-D-601.3 pressed subsection state
    COMP-D-611 Neural Runtime
      COMP-D-611.1 current-historical fixture-mode controls
      COMP-D-602 Topology-runtime
        COMP-D-602.1 topology manifest
          COMP-D-602.1.1 ordered topology path datum
          COMP-D-602.1.2 topology fact grid datum-family
        COMP-D-602.2 runtime projection summary
          COMP-D-602.2.1 runtime metric strip datum-family
      COMP-D-603 CCGQA-attention-AttnRes
        COMP-D-603.1 CCGQA diagnostics
          COMP-D-603.1.1 unavailable-historical state
          COMP-D-603.1.2 repeated layer card
            COMP-D-603.1.2.1 evidence-invalid banner datum-state
            COMP-D-603.1.2.2 Q-K-V-channel-conv-entropy-sequence-cache-finite metrics datum-family
            COMP-D-603.1.2.3 inspect evidence control-effect
        COMP-D-603.2 AttnRes diagnostics
          COMP-D-603.2.1 unavailable-historical state
          COMP-D-603.2.2 repeated boundary-layer card
            COMP-D-603.2.2.1 routing weight bars gate-sum datum
            COMP-D-603.2.2.2 inspect recorded weights control-effect
      COMP-D-604 Local refinement
        COMP-D-604.1 unavailable state
        COMP-D-604.2 expansion-pass histogram datum
        COMP-D-604.3 reconciliation-cost summary datum
        COMP-D-604.4 receipt table
          COMP-D-604.4.1 frame-receipt-eligible-quota-passes-density-cost datum-row
          COMP-D-604.4.2 receipt inspect control-effect
      COMP-D-605 Instrumentation coverage
        COMP-D-605.1 repeated instrument-source-state row datum-family
    COMP-D-606 Frame Compiler Explorer
      COMP-D-607 Frame generation-query
        COMP-D-607.1 fixture generation selector control
        COMP-D-607.2 LOADING-PRESENT-ERROR request state
        COMP-D-607.3 coverage-returned-count datum
        COMP-D-607.4 compiled-example selector control
        COMP-D-607.5 missing-no-selection state
      COMP-D-608 Compiled provenance-packing
        COMP-D-608.1 selected-example packing metrics datum-family
        COMP-D-608.2 receipt provenance disclosure
        COMP-D-608.3 repeated position disclosure
          COMP-D-608.3.1 position metadata datum-family
          COMP-D-608.3.2 constituent legality table datum-family
          COMP-D-608.3.3 codec-field visibility datum-family
        COMP-D-608.4 unavailable sidecar-compiler state
      COMP-D-609 Prediction frontier
        COMP-D-609.1 frontier selector control
        COMP-D-609.2 legality-visibility projection effect
      COMP-D-610 Aggregate packing
        COMP-D-610.1 aggregate disclosure control-state
        COMP-D-610.2 aggregate packing metrics datum-family
```

### VIEW-D-007 · Memory

```mermaid
mindmap
  root((VIEW-D-007 Memory))
    COMP-D-733 Historical-memory unavailable
      COMP-D-733.1 requested generation datum
      COMP-D-733.2 MISSING-UNAVAILABLE state
      COMP-D-733.3 no-current-substitution effect
    COMP-D-701 Memory summary
      COMP-D-701.1 generation-PRESENT header datum-state
      COMP-D-701.2 allocated-capacity datum
      COMP-D-701.3 eligible-hit exact structural miss counts datum
      COMP-D-701.4 hit-rate gate-use-rate datum
      COMP-D-701.5 state-parameter-optimizer footprint datum
      COMP-D-701.6 repeated read-site receipt datum-family
      COMP-D-701.7 operational-evidence authority doctrine datum
    COMP-D-702 Memory atlas
      COMP-D-702.1 page-count header datum
      COMP-D-702.2 page selector card family control
      COMP-D-702.3 slot list
        COMP-D-702.3.1 repeated slot control
          COMP-D-702.3.1.1 address datum
          COMP-D-702.3.1.2 stable identity datum
          COMP-D-702.3.1.3 frame schema datum
          COMP-D-702.3.1.4 allocation state datum
          COMP-D-702.3.1.5 capability-episode object relations contract
      COMP-D-702.4 empty-page state
    COMP-D-703 Motif inspector
      COMP-D-703.1 missing-selection state
      COMP-D-703.2 selected identity-allocation header datum-state
      COMP-D-703.3 identity-key-semantic-address-eligibility facts datum-family
      COMP-D-703.4 creation-last-use-hit-gate telemetry datum-family
      COMP-D-703.5 parameter-optimizer-correction facts datum-family
      COMP-D-703.6 source-evidence refs datum-family
      COMP-D-703.7 related capability-episode refs datum-family
      COMP-D-703.8 capability interpretation datum
    COMP-D-704 Generation comparison
      COMP-D-704.1 comparison-generation selector control
      COMP-D-704.2 Created-Removed-Held-Requalified identity groups datum-family
      COMP-D-704.3 allocation-capacity-hit-miss-gate deltas datum-family
      COMP-D-704.4 append-only HELD interpretation doctrine datum
    COMP-D-705 Rejected candidate boundary
      COMP-D-705.1 candidate-REJECTED header datum-state
      COMP-D-705.2 four-invariant proof grid datum-family
      COMP-D-705.3 rejection reason candidate-local-not-retained doctrine datum
```

### VIEW-D-008 · Teacher

```mermaid
mindmap
  root((VIEW-D-008 Teacher))
    COMP-D-801 Strategy population
      COMP-D-801.1 incumbent-challenger-canary-retired role-count summary datum
      COMP-D-801.2 repeated strategy card
        COMP-D-801.2.1 identity-role-status datum
        COMP-D-801.2.2 attempts-retained-gain-no-gain-interference-wall metrics datum
        COMP-D-801.2.3 capability-source-lifecycle-canary-resource scope datum
        COMP-D-801.2.4 Learning Episode links or no-link state
        COMP-D-801.2.5 checkpoint role-state history datum
        COMP-D-801.2.6 Inspect strategy control-effect
    COMP-D-802 Outcome-cost comparison
      COMP-D-802.1 strategy selection controls
        COMP-D-802.1.1 option identity-pressed state
        COMP-D-802.1.2 selection update invalid-scope fallback effect
      COMP-D-802.2 comparison-scope controls
        COMP-D-802.2.1 whole-school capability source-family option family
        COMP-D-802.2.2 pressed-state rerender effect
      COMP-D-802.3 comparison coverage-context datum
      COMP-D-802.4 comparison table
        COMP-D-802.4.1 strategy-observed-retained-gain datum
        COMP-D-802.4.2 no-gain-interference datum
        COMP-D-802.4.3 wall-time attempted-steps datum
        COMP-D-802.4.4 per-row coverage datum-state
      COMP-D-802.5 descriptive no-winner doctrine datum
    COMP-D-803 Fidelity ladder
      COMP-D-803.1 OBSERVATIONAL panel state
      COMP-D-803.2 fidelity-card identity-mode datum
      COMP-D-803.3 rung-delta sequence datum
      COMP-D-803.4 stop-retained-steps-savings-false-kill outcomes datum
      COMP-D-803.5 authority-change no-early-termination boundary datum
    COMP-D-804 Projection boundary
      COMP-D-804.1 projection schema datum
      COMP-D-804.2 coverage state
      COMP-D-804.3 exposed field inventory datum
      COMP-D-804.4 fixture-backed limitation-authority explanation datum
```

### VIEW-D-009 · SÍ SÉ SON

```mermaid
mindmap
  root((VIEW-D-009 SI SE SON))
    COMP-D-906 As-of snapshot selector
      COMP-D-906.1 retained snapshot option family control
      COMP-D-906.2 selected pressed state
      COMP-D-906.3 choose-snapshot full-view-rerender effect
    COMP-D-901 Observation set
      COMP-D-901.1 event identity-context-timestamps datum
      COMP-D-901.2 independent axis cell family
        COMP-D-901.2.1 axis label-ordinal datum
        COMP-D-901.2.2 expected-missing reported-negative unknown note state
        COMP-D-901.2.3 inspect axis control-effect
      COMP-D-901.3 scope-source-associated-object context datum
      COMP-D-901.4 stable link datum
      COMP-D-901.5 three-axis no-scalar doctrine and lane headings datum
    COMP-D-902 Provenance
      COMP-D-902.1 event-capability-salience identity datum
      COMP-D-902.2 policy owner-version-digest datum
      COMP-D-902.3 window policy-version-size datum
      COMP-D-902.4 per-axis provenance
        COMP-D-902.4.1 sourceRef-ruleId datum
        COMP-D-902.4.2 basis refs datum
    COMP-D-903 Recursive aggregation
      COMP-D-903.1 historical aggregation-unavailable state
      COMP-D-903.2 window identity-size-append-bounds-late datum
      COMP-D-903.3 cluster
        COMP-D-903.3.1 identity-partition datum
        COMP-D-903.3.2 rule-posture-lineage-count datum
        COMP-D-903.3.3 constituent observation controls
      COMP-D-903.4 pattern identity-status-nomination-sourceGold-qualified datum
      COMP-D-903.5 trend
        COMP-D-903.5.1 supported-rule datum
        COMP-D-903.5.2 window points datum-family
        COMP-D-903.5.3 constituent controls vs outside-as-of state
      COMP-D-903.6 reversible no-authority-upgrade doctrine datum
    COMP-D-904 Routing rationale
      COMP-D-904.1 historical routing-unavailable state
      COMP-D-904.2 route identity-tier-rule datum
      COMP-D-904.3 ordering keys hidden-weighting datum
      COMP-D-904.4 cited observation family
        COMP-D-904.4.1 inspect available citation control-effect
        COMP-D-904.4.2 outside-as-of citation state
      COMP-D-904.5 no-private-weight inference doctrine datum
    COMP-D-905 Projection boundary
      COMP-D-905.1 schema datum
      COMP-D-905.2 PARTIAL coverage state
      COMP-D-905.3 projected field inventory datum
      COMP-D-905.4 non-first-class fixture-backed boundary datum
```

### VIEW-D-010 · Corrections

```mermaid
mindmap
  root((VIEW-D-010 Corrections))
    COMP-D-1001 Correction context
      COMP-D-1001.1 view-purpose epistemic boundary datum
      COMP-D-1001.2 projection fixture notice datum
      COMP-D-1001.3 correction-state glossary datum
      COMP-D-1001.4 selected correction summary
        COMP-D-1001.4.1 correction ID datum
        COMP-D-1001.4.2 prior-current source revision datum
        COMP-D-1001.4.3 correction generation datum
        COMP-D-1001.4.4 explicit unknown-influence count datum
    COMP-D-1002 Blast-radius graph-list
      COMP-D-1002.1 explicit-edge traversal doctrine datum
      COMP-D-1002.2 affected-node control family
        COMP-D-1002.2.1 kind-label datum
        COMP-D-1002.2.2 state datum
        COMP-D-1002.2.3 evidence refs unknown-receipt state
        COMP-D-1002.2.4 click inspect control-effect
      COMP-D-1002.3 dependency-edge list
        COMP-D-1002.3.1 from datum
        COMP-D-1002.3.2 relation datum
        COMP-D-1002.3.3 to datum
    COMP-D-1003 Equivalent impact table
      COMP-D-1003.1 equivalence statement datum
      COMP-D-1003.2 impact row family
        COMP-D-1003.2.1 identity inspect control
        COMP-D-1003.2.2 class datum
        COMP-D-1003.2.3 state datum
        COMP-D-1003.2.4 evidence refs-untracked state
    COMP-D-1004 Requalification state
      COMP-D-1004.1 descriptive non-certifying queue boundary datum
      COMP-D-1004.2 task identity urgency owner status datum
      COMP-D-1004.3 generation checkpoint source-revision custody datum
      COMP-D-1004.4 implicated refs datum
      COMP-D-1004.5 evidence refs UNKNOWN state
      COMP-D-1004.6 receipt refs NONE-NOT-REQUALIFIED state
    COMP-D-1005 Append-only correction history
      COMP-D-1005.1 tracked artifact identity datum
      COMP-D-1005.2 append-only non-rewrite doctrine datum
      COMP-D-1005.3 history entry family
        COMP-D-1005.3.1 generation-phase datum
        COMP-D-1005.3.2 state datum
        COMP-D-1005.3.3 receipt datum
```

### VIEW-D-011 · Lineage

```mermaid
mindmap
  root((VIEW-D-011 Lineage))
    COMP-D-1101 Accepted lineage
      COMP-D-1101.1 READ_ONLY posture header state
      COMP-D-1101.2 generation node family
        COMP-D-1101.2.1 generation-transition-compact-manifest datum
        COMP-D-1101.2.2 checkpoint-parent semantic relations contract
        COMP-D-1101.2.3 selected pressed state
        COMP-D-1101.2.4 click select-rerender-inspect effect
      COMP-D-1101.3 exact parent-child transition list datum-family
      COMP-D-1101.4 tabular lineage equivalent datum-family
    COMP-D-1102 Generation comparison
      COMP-D-1102.1 comparison relation-state header datum
      COMP-D-1102.2 endpoint controls
        COMP-D-1102.2.1 From selector control
        COMP-D-1102.2.2 To selector control
        COMP-D-1102.2.3 generation-manifest option datum
        COMP-D-1102.2.4 change rerender effect
      COMP-D-1102.3 interpretation no-winner doctrine datum
      COMP-D-1102.4 structured dimension diff
        COMP-D-1102.4.1 dimension datum
        COMP-D-1102.4.2 before-after datum
        COMP-D-1102.4.3 state-reason datum
        COMP-D-1102.4.4 source datum
      COMP-D-1102.5 capability-evidence diff datum-family
    COMP-D-1103 Rejected-candidate boundary
      COMP-D-1103.1 REJECTED state-header
      COMP-D-1103.2 candidate ID rejection reason committed-generation-NONE datum
    COMP-D-1104 Exact immutable generation node
      COMP-D-1104.1 generation-transition-state header datum
      COMP-D-1104.2 full manifest-parent custody identity datum
      COMP-D-1104.3 manifest field dossier
        COMP-D-1104.3.1 label datum
        COMP-D-1104.3.2 value datum
        COMP-D-1104.3.3 source ref datum
      COMP-D-1104.4 stable deep-link datum
      COMP-D-1104.5 exact CP03 mode-generation-record query identity datum
      COMP-D-1104.6 historical generation missing defensive state
```

### VIEW-D-012 · Resources

```mermaid
mindmap
  root((VIEW-D-012 Resources))
    COMP-D-1201 Resource headline
      COMP-D-1201.1 no-current-projection defensive state
      COMP-D-1201.2 fixture-live-historical generation-window provenance datum
      COMP-D-1201.3 page-state badge datum-state
      COMP-D-1201.4 headline metric family
        COMP-D-1201.4.1 metric identity datum
        COMP-D-1201.4.2 semantic state datum
        COMP-D-1201.4.3 value datum
        COMP-D-1201.4.4 evidence-strength note datum
      COMP-D-1201.5 throughput-not-learning boundary datum
    COMP-D-1202 Metric semantics
      COMP-D-1202.1 measured-value semantic-value-note datum
      COMP-D-1202.2 configured-limit semantic-value-note datum
      COMP-D-1202.3 forecast-estimate semantic-value-note datum
    COMP-D-1203 Memory decomposition
      COMP-D-1203.1 COMPLETE-PARTIAL-UNAVAILABLE reconciliation state
      COMP-D-1203.2 measured category family
        COMP-D-1203.2.1 category identity datum
        COMP-D-1203.2.2 value-or-UNAVAILABLE datum
        COMP-D-1203.2.3 category state datum
      COMP-D-1203.3 unresolved remainder value-state datum
      COMP-D-1203.4 allocated-sum aggregate reconciliation explanation datum
    COMP-D-1204 Compute-length profile
      COMP-D-1204.1 compute-preparation metrics datum-family
      COMP-D-1204.2 sequence-batch-length metrics datum-family
    COMP-D-1205 Timeline-correlation
      COMP-D-1205.1 no-samples UNAVAILABLE no-synthesis state
      COMP-D-1205.2 sample-count datum
      COMP-D-1205.3 sample row family
        COMP-D-1205.3.1 sample ID-time inspect control
        COMP-D-1205.3.2 memory-MLX datum
        COMP-D-1205.3.3 batch-density-steps-expansion datum
        COMP-D-1205.3.4 peak-vs-sample state
      COMP-D-1205.4 exact related-evidence global-inspector effect
    COMP-D-1206 Historical comparison
      COMP-D-1206.1 EMPTY-LOADING-PRESENT-UNAVAILABLE state
      COMP-D-1206.2 exact-generation form
        COMP-D-1206.2.1 numeric generation input control
        COMP-D-1206.2.2 Load exact generation submit control
        COMP-D-1206.2.3 read-only no-inference guidance datum
      COMP-D-1206.3 no-comparison empty state
      COMP-D-1206.4 metric historical-inspected-delta table datum-family
      COMP-D-1206.5 bounded historical CP03 query rerender effect
```

### VIEW-D-013 · Evidence

```mermaid
mindmap
  root((VIEW-D-013 Evidence))
    COMP-D-1301 Query-filter
      COMP-D-1301.1 forensic-query help datum
      COMP-D-1301.2 criteria controls
        COMP-D-1301.2.1 search-kind selector control
        COMP-D-1301.2.2 exact-identity input control
      COMP-D-1301.3 Search fresh-query reset effect
      COMP-D-1301.4 Load-next bounded-page cursor-merge effect
      COMP-D-1301.5 context-bound query identity stale-response cancellation contract
    COMP-D-1305 Query-degraded state
      COMP-D-1305.1 error-loading-page-coverage-truncated semantic state
      COMP-D-1305.2 returned-total waiting-error detail datum
      COMP-D-1305.3 alert-vs-status live-region treatment
      COMP-D-1305.4 failure clears stale non-append results effect
    COMP-D-1302 Result list
      COMP-D-1302.1 exact record result
        COMP-D-1302.1.1 record ID datum
        COMP-D-1302.1.2 schema datum
        COMP-D-1302.1.3 authority-coverage-generation datum
        COMP-D-1302.1.4 select detail-return-origin effect
      COMP-D-1302.2 page relationship result
        COMP-D-1302.2.1 relation-source-target refs datum
        COMP-D-1302.2.2 exact-target hydrate control-effect
        COMP-D-1302.2.3 EXTERNAL-NOT-HYDRATED state
    COMP-D-1306 Traversal-omission
      COMP-D-1306.1 degraded marker family
        COMP-D-1306.1.1 schema datum
        COMP-D-1306.1.2 marker record ID datum
        COMP-D-1306.1.3 missing-reason-resource-stale-as-of details datum
      COMP-D-1306.2 traversal failure alert datum-state
      COMP-D-1306.3 selected-link hydration unavailable-no-links state
    COMP-D-1303 Exact record-raw payload
      COMP-D-1303.1 exact-record identity-header datum
      COMP-D-1303.2 readable-raw mode
        COMP-D-1303.2.1 current-mode label datum
        COMP-D-1303.2.2 toggle repaint control-effect
      COMP-D-1303.3 readable record dossier
        COMP-D-1303.3.1 record-schema-authority-coverage-verification datum
        COMP-D-1303.3.2 materialized-observed-as-of datum
        COMP-D-1303.3.3 literal metadata datum
        COMP-D-1303.3.4 literal body fields datum-family
      COMP-D-1303.4 provenance refs
        COMP-D-1303.4.1 SOURCE-EVIDENCE-RECEIPT groups datum
        COMP-D-1303.4.2 ref exact-reference-search control-effect
        COMP-D-1303.4.3 no-refs state
      COMP-D-1303.5 exact selected-record links
        COMP-D-1303.5.1 relation-source-target datum
        COMP-D-1303.5.2 open exact record control-effect
        COMP-D-1303.5.3 unresolved-no-link state
      COMP-D-1303.6 raw structured payload datum
    COMP-D-1304 Return to origin
      COMP-D-1304.1 return-available state
      COMP-D-1304.2 Return to inspected object control
      COMP-D-1304.3 origin restoration effect
```

### VIEW-D-014 · Operate

```mermaid
mindmap
  root((VIEW-D-014 Operate))
    COMP-D-1400 Command-boundary posture
      COMP-D-1400.1 MUTATION ZONE datum
      COMP-D-1400.2 LIVE COMMAND CONTEXT REQUIRED blocker state
      COMP-D-1400.3 global command-error alert state
    COMP-D-1401 Action catalog
      COMP-D-1401.1 action identity-label-description datum
      COMP-D-1401.2 supported-vs-disabled state
      COMP-D-1401.3 AUTHORIZATION REQUIRED READ ONLY UNAVAILABLE posture datum-state
      COMP-D-1401.4 selected aria-pressed state
      COMP-D-1401.5 selection initializes request defaults effect
    COMP-D-1402 Exact request
      COMP-D-1402.1 action-phase header datum-state
      COMP-D-1402.2 conditional dry-run toggle control-effect
      COMP-D-1402.3 JSON parameters textarea control
      COMP-D-1402.4 admitted-parameter no-shell boundary datum
      COMP-D-1402.5 Run read-only preflight control
      COMP-D-1402.6 invalid JSON-object-key-scalar validation states
    COMP-D-1403 Preflight
      COMP-D-1403.1 no-preflight empty state
      COMP-D-1403.2 preview mode state
      COMP-D-1403.3 mutating-vs-read-only consequence posture
      COMP-D-1403.4 exact target fact family
        COMP-D-1403.4.1 target ref datum
        COMP-D-1403.4.2 run-generation datum
        COMP-D-1403.4.3 generation manifest datum
        COMP-D-1403.4.4 topology Factory semantic datum
        COMP-D-1403.4.5 source identity datum
        COMP-D-1403.4.6 admission policy datum
        COMP-D-1403.4.7 expected postcondition datum
      COMP-D-1403.5 resource profile fact family
      COMP-D-1403.6 stale-context blocker
        COMP-D-1403.6.1 conflicting identity label datum
        COMP-D-1403.6.2 shell-expected vs target-actual datum
        COMP-D-1403.6.3 refresh-repreflight guidance datum
      COMP-D-1403.7 PREVIEWING-to-REVIEW-STALE-ERROR transition effect
    COMP-D-1404 Deliberate authorization
      COMP-D-1404.1 HUMAN GATE vs READ ONLY state
      COMP-D-1404.2 expectedTargetRef reviewed-target binding datum
      COMP-D-1404.3 exact authorization phrase datum
      COMP-D-1404.4 authorization input control
      COMP-D-1404.5 submit label-enabled state control
      COMP-D-1404.6 mutation-preview-conflict-phrase-target dispatch guard effect
    COMP-D-1405 Receipt-readback-reconciliation
      COMP-D-1405.1 lost-ack outcome-unknown state
        COMP-D-1405.1.1 operation identity datum
        COMP-D-1405.1.2 no-blind-retry doctrine datum
        COMP-D-1405.1.3 Reconcile operation control
      COMP-D-1405.2 operation ID-receipt state header datum
      COMP-D-1405.3 lifecycle stage strip datum
      COMP-D-1405.4 receipt record-target-postcondition-error facts datum
      COMP-D-1405.5 receipt actions
        COMP-D-1405.5.1 Open receipt inspector control-effect
        COMP-D-1405.5.2 Open postcondition inspector control-effect
        COMP-D-1405.5.3 conditional Reconcile authoritative-readback control-effect
      COMP-D-1405.6 stderr-stdout trainer log disclosure
      COMP-D-1405.7 literal bounded inspection JSON disclosure
      COMP-D-1405.8 matching operator event reconciliation effect
      COMP-D-1405.9 terminal-pending-lost-unknown phase effect
```

## Recursive-scope rule for redesign leaves

A child issue that cites a published atlas node owns the full dotted subtree beneath that node unless the issue explicitly excludes a descendant with a source-grounded reason. This prevents a leaf from “satisfying” a subsystem-sized parent while leaving one of its real controls, states, treatments, or effects unreviewed.

