# Mission Control current-state information atlas

Status: descriptive map of the current implementation, not target-screen approval
Parent authority: GitHub issue #1124
Cross-view relationships: `FLOWS.md`

The atlas deliberately describes composition as a hierarchy. Cross-view navigation, state propagation, selection ownership, evidence return, compare, pinning, and command lifecycles are kept in `FLOWS.md` so this tree does not become spaghetti.

## ID grammar

- `SHELL-D-###`: persistent shell segment
- `VIEW-D-###`: destination
- `COMP-D-###`: component/section inside a shell/view
- `STATE-D-###`: important presentation state

Each component records **information → treatment → interaction → effect**.

## SHELL-D-001 · Application shell

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
- Information: current/as-of lens, compare slots/results, pins, annotations, exact object context/deep-link affordance.
- Treatment: persistent global investigation region with expandable panels.
- Interaction: time lens, compare, pin/open/remove, annotate, copy/open deep link.
- Effect: changes historical context, cross-highlighting, local operator metadata, or cross-view selection.
- Concerns: must not compete visually with primary destination; exact context identity is mandatory.

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

### STATE-D-001 · Bootstrap
- Four-stage startup: control plane, learner discovery, Mission Control telemetry, trainer.
- Must not substitute fixtures for missing live telemetry.

### STATE-D-002 · Live verified context
- Fresh snapshot supports ordinary inspection; Operate is available only when mutation context is verified.

### STATE-D-003 · Historical / inspection-only
- Exact prior generation context; mutation disabled.

### STATE-D-004 · Defensive variants
- loading, progressive, empty, stale, partial, offline, denied, revoked, unavailable, incompatible-version, timeout, duplicate-action, session/service restarting, historical unavailable, malformed/unsupported payload, outcome unknown.

## VIEW-D-001 · Mission Control

Purpose: outcome-first learner health, current work, learning pulse, actionable attention.

### COMP-D-101 · Learner headline / current posture
- Information: accepted learner health and current state.
- Treatment: summary region.
- Interaction: inspect relevant object where exposed.
- Effect: establishes the most important current condition.

### COMP-D-102 · Current work / learning pulse
- Information: current candidate/training activity and recent progress.
- Treatment: compact summary/metric surfaces.
- Interaction: inspect/navigate to owning detail.
- Effect: bridges overview to deeper destinations.

### COMP-D-103 · Actionable attention
- Information: items requiring operator attention.
- Treatment: prioritized attention list/status.
- Interaction: inspect or navigate.
- Effect: converts overview into next investigation.

## VIEW-D-002 · School

Purpose: exact capability comparison and declared prerequisite topology.

### COMP-D-201 · Capability matrix
- Information: capability rows; WAS/TOP/NOW/ALL; debt; retention probability where measured; source/implementation/qualification state.
- Treatment: dense analytical matrix.
- Interaction: select capability; sort/filter where implemented.
- Effect: opens capability in inspector and cross-highlights relationships.

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

### COMP-D-503 · Learned-similarity lens
- Information: derived similarity where available.
- Treatment: explicitly separate derived view.
- Interaction: compare/explore.
- Effect: prevents learned geometry from masquerading as semantic identity.

## VIEW-D-006 · Model

Purpose: measured model/runtime mechanisms and exact frame compiler inspection.

### COMP-D-601 · Model local navigation
- Neural Runtime / Frame Compiler Explorer peer surfaces.

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
- Information: present/unavailable instrumentation.
- Treatment: coverage list/status.
- Interaction: none/inspect.
- Effect: prevents synthesized absent metrics.

### COMP-D-606 · Frame Compiler Explorer
- Information: exact frame packing/unpacking receipts and causal visibility.
- Treatment: specialized frame surface.
- Interaction: inspect frame/receipt.
- Effect: exposes exact compiler behavior distinct from neural telemetry.

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
- Interaction: open evidence.
- Effect: shows what has actually been requalified.

### COMP-D-1005 · Append-only correction history
- Information: correction/source/generation history and prior states.
- Treatment: chronological record.
- Interaction: select historical correction evidence.
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

## VIEW-D-012 · Resources

Purpose: measured resource budgets, exact historical comparison, and spike correlation.

### COMP-D-1201 · Resource headline
- Information: current budget posture.
- Treatment: primary metrics/status.
- Interaction: none/inspect.
- Effect: establishes current resource condition.

### COMP-D-1202 · Semantics/decomposition
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

### COMP-D-1302 · Evidence result list/table
- Information: record identities/types/provenance.
- Treatment: analytical list/table.
- Interaction: select exact record.
- Effect: opens evidence detail and establishes return origin.

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

## Atlas-derived task groups for later navigation design

These are design hypotheses for decomposition, not authorization to change navigation yet:

1. **Overview & learning**: VIEW-D-001 Mission Control, VIEW-D-002 School, VIEW-D-003 Capability Explorer, VIEW-D-004 Learning.
2. **Representation & mechanisms**: VIEW-D-005 Atlas, VIEW-D-006 Model, VIEW-D-007 Memory.
3. **Decision & correction**: VIEW-D-008 Teacher, VIEW-D-009 SÍ SÉ SON, VIEW-D-010 Corrections.
4. **Provenance & operations**: VIEW-D-011 Lineage, VIEW-D-012 Resources, VIEW-D-013 Evidence, VIEW-D-014 Operate.

Any final grouping must be tested against real operator journeys and must preserve direct command-palette/deep-link access.
