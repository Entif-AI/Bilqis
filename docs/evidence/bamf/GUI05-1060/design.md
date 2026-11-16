# GUI05 capability dossier implementation design

Authority: issue #1060, additive child of #1047; prerequisites #1056, #1057,
#1051 are merged. Baseline: reviewed unified bd181b3b7cae23e7e94af1a7784e2deb4b02944f.
No learner, teacher, optimizer, admission or semantic authority changes.

## Ownership and interfaces

The renderer consumes CP03 via existing `bamfMissionControl.querySnapshot`.
Extend its accepted request union with the exact CP03 QueryRequest shape.
Main forwards it to the existing private Python broker; Python constructs
QueryRequest, calls ControlPlaneClient.query, decodes every returned CP02 record
and strips service/session identities before returning the bounded page.
Keep the existing GUI01 fixture bootstrap explicitly labeled as a fixture.
A disconnected query errors visibly; never replace a missing generation with live.
No new filesystem, shell, network or command privileges reach the renderer.

Existing CapabilitySnapshot lacks detailed facts. Add a separate versioned
CapabilityDossier WireRecord to the CP02 registry and CP03 capability family.
Fields: meta, capability_id, name, now, top, total, debt (DataValue),
retention, eligibility, qualification, source_state (DataValue), entries
(tuple[DossierEntry]). Each entry has entry_id, section (performance, teaching,
sources, dependencies, history), kind, label, generation, observed_at,
values (tuple[DossierValue]: name + DataValue), refs (unique literal evidence
references), related_kind and related_id (both null or stable names).
All entries bind the same capability via their enclosing record; validate
entry generations are not later than the record generation. Enforce unique
entry/value IDs and a 128-entry upper bound. Sources carry held reasons,
source/rubric revisions and provenance as explicit named values. Teaching carries
explicit counts/rates, fidelity and lesson families. Performance includes exact
cohort kind/results and target/protected deltas. History explicitly records
regression, recovery, plateau, correction and candidate disposition. Never derive
causes, candidate outcomes, rates, TOP, retention or dependency direction from names
or scores. Missing values retain their DataValue state. Producers own facts;
this leaf ships a labeled representative fixture and no live trainer projection.
Existing v1 records remain unchanged; generate the additive schema projection.

## Renderer

Add a Capability Explorer destination and set capability's inspector owner to it.
A dedicated renderer/capability subdirectory owns model, query controller,
view markup, style and fixture modules (each under 240 lines). Use existing theme
and density tokens; high-density identity header, tab-like section links, exact
score tiles and progressive evidence rows. Semantic authority markers remain
textual. Use native buttons, links, details and labeled controls; no color-only
meaning, decorative animation or inferred narrative.

Query the capability family for an explicit run/generation, page size 8. Present
page state, markers, coverage and truncation. Load more only on user action.
Filter only matching capability dossiers after collection; show absence honestly.
Historical requests always use mode historical plus exact generation. Live lens
also pins the shell generation to avoid mixing sources. Run/generation selects
and URL query context persist across destinations; never relabel live data as old.
Display a selected record only if run/generation match the requested lens.
Cancel stale responses with a request epoch; clear old data before loading.
A fixture toggle is explicit; a fixture view labels the whole dossier and changes
shell to its fixture run/generation. It never silently replaces service errors.

All externally sourced text is escaped before HTML interpolation. Evidence links
open a local exact-reference panel and issue CP03 reference queries, displaying
raw returned records/links plus missing/denied state without inventing resolution.
Related capability links retain exact run/generation and open its dossier.
Episode/source/semantic/checkpoint links use existing owners and exact IDs.
Evidence raw panel preserves literal source references even when unresolved.
History sorts by generation, observed_at and entry_id, preserving separate rows.

## Structural interruption

The encountered mission_control directory has >=18 code files. Preserve current
issue/branch/head/context in local BIOS Work Stack. Move codec, model, envelopes,
events, snapshots, observability, operator, registry and schema into a cohesive
contracts package, updating internal relative imports. Preserve old deep imports
with module aliases installed by mission_control.__init__, without duplicate types.
Keep callers and existing tests unchanged to prove import compatibility. Do not
scan unrelated directories. Run portable mission_control and control_plane owner
tests before resuming GUI05. This is nonsemantic required structural remediation.

## Proof and failure behavior

Red/green tests: dossier codec/schema/validation and two-generation CP03 queries;
bridge exact requests and no service/session disclosure; renderer historical
isolation, pagination, delayed responses, absent/partial/stale/denied states;
retained vs rejected, no-gain vs interference, regression vs recovery, source hold
and revisions, exact dependencies, literal evidence drill-through. Add browser
journey checks for section navigation, historical switch, evidence click, related
capability navigation, theme/density and narrow layout. Browser runs use labeled
fixtures through injected preload-equivalent boundary; no training needed.

Run neural-inert static gates first, then focused Node and Python owner tests,
then bounded premerge policy. No required proof needs MLX. Any aggregate run with
unknown duration is not launched: select bounded claim-specific stages and record
remaining limitations. Required repository gates cannot be claimed passed from
scoped substitutes. Reconcile drift against this design, sync latest unified,
then create a ready PR only when all applicable gates are satisfied. Never merge
or close #1060 before human-reviewed merge readback.

## Exact contract and query amendment (review findings 1–5)

The additive schema is `bilqis.bamf.mission-control.capability-dossier/v1`.
All fields listed above are required. IDs, name, section, kind and label are
nonblank single-line Unicode strings. Metric/status fields are DataValue;
unknown values use {state: UNKNOWN, origin: null, value: null, units: null}.
DossierValue has only `name: str` (unique per entry) and `value: DataValue`.
Entry `generation` and `observed_at` are nonnegative safe integers. Related kind
and ID are nullable strings; kind is capability, episode, semantic, checkpoint,
source or evidence. Entry IDs are unique across a dossier. Sections are the five
literal section IDs above; kinds/labels remain literal producer observations,
not client classification rules. Canonical named values used by the fixture and
renderer are: performance (cohort, correct, total, target_delta, protected_delta,
candidate_outcome); teaching (strategy, visits, success_rate, no_gain_rate,
interference_rate, fidelity, lesson_family); sources (family, state, hold_reason,
source_revision, rubric_revision); dependencies (relation, semantic_id, frame_id);
history (event, candidate_outcome). Values are displayed as labeled facts without
client interpretation. Dependency relation is explicitly prerequisite or consumer.
No automatic numeric rates or prose are computed. Dates remain exact timestamps.

Dossier validation requires <=128 entries, <=16 named values and <=16 unique refs
per entry, <=512 characters per label/ID/name/ref/string metric; canonical JSON
row length must be <=48*1024 bytes. Oversize construction fails deterministically
before querying. Empty entry refs are allowed only for absent-data entries; any
entry containing PRESENT metrics requires at least one literal evidence ref.

The capability query always sets schema_version to the dossier schema. Collect
one page at a time, display matching rows, and keep Load more visible while cursor
exists. Do not claim absence while further pages exist. Duplicate matching dossier
rows are ambiguous: show invalid state rather than choose. A stale cursor clears
collected data and asks the user to reload the first page, never mixes versions.
No automatic unbounded scan. Evidence panel submits REFERENCE with the selected
literal ref and exact run/generation; shows returned links as links. For a resolved
target_record_id, a user may explicitly query CAPABILITY/EPISODE/GENERATION/etc.
by record_id (family selected from the dossier entry related kind), or inspect
literal returned links. Missing target_record_id is explicitly unresolved. The
GUI05 proof requires exact literal refs and query results; CP03 does not promise
arbitrary artifact-body hydration. Show link pagination by explicit Load more.

CP03 snapshot union discriminator is `schema` equal to
`bilqis.bamf.control-plane.query/v1`; GUI01 keeps its existing schemaVersion
request branch. CP03 requests have exactly QueryRequest.to_record keys and obey
its type/enum/limit constraints. Main validates this shape before broker call;
Python repeats QueryRequest.from_mapping. Allowed families remain the CP03 enum.
Broker adds only query op and a query payload, retaining private session ownership.
Return exactly encode_query_page fields: schema, query_id, state, coverage,
request, family, mode, total_matches, returned, truncated, next_cursor, records,
markers, links. Python
rejects accepted=false, decodes records/markers, verifies page schema and strips
accepted/service/session transport fields. Main validates the public page's exact
keys, enums, arrays/counts and wire record shapes before renderer delivery.
Renderer verifies requested run/generation and schema on selected dossiers.
Errors remain errors; GUI displays unavailable and offers retry. No CP01 fixture
fallback is used for CP03. Owned bridge files: accepted-contracts.cjs,
accepted-control-plane-adapter.cjs, cp01-python-broker.cjs, electron_bridge.py,
plus a focused query validation module. Existing preload/IPCs stay unchanged.

Structural baseline reconciliation: at bd181b3b the nine named files were direct
children. The nonsemantic directory repair has now moved them to contracts/;
root __init__ imports all contracts first, then installs aliases in sys.modules.
The aliases point at identical module objects, preserving class identity. No caller
API changes. Add an explicit old/new import identity regression. Existing
query catalog, support, fixtures, events and consumers now import contracts.*.

## Final query details

Use the exact CP03 row encoder for the size guard:
len(json.dumps(encode_record(record), sort_keys=True, separators=(",", ":")).encode("utf-8"))
<=48*1024. This uses default ensure_ascii=True and no newline; test non-ASCII.
Every entry ref must also occur in the enclosing meta source_refs, evidence_refs
or receipt_refs; enforce this invariant. CP03 already discovers those references.
No implicit evidence-body hydration or family inference from related_kind exists.
The evidence panel shows the exact originating entry and its literal values,
plus paged CP03 REFERENCE links, resolved target IDs or explicit unresolved state.
For every returned link offer a labeled CP03 family selector (record-bearing RUN through RESOURCE only; exclude REFERENCE and LINKS)
and an explicit Inspect record button using target_record_id with reference/cursor null; absent target ID
has no Inspect button. A wrong selected family returns MISSING, never substitutes
another object. No source/checkpoint query family is invented. The fixture's fresh
and protected refs resolve to CapabilitySnapshot records in family capability,
whose literal scores and meta pins can be inspected. This explicit family choice
also covers null/unmapped/mismatched related kinds without guessing.

## Implementation reconciliation

Generated fixture pages use an ECMAScript data module because strict connect-src
'none' also blocks JSON module imports in the actual Chromium path. The fixture
is generated by tests/dossier_fixture.py through the typed CP03 catalog.
Main validates CP02 record/marker shapes using Ajv's Draft 2020-12 validator and
the checked-in generated schema bundle, rather than a handwritten shape copy.
Python retains semantic invariant validation and exact query/record identity checks.
These preserve the approved read-only interfaces and existing renderer policy.

## GUI07 intake compatibility

The canonical Python broker owner is now mission_control/electron/bridge.py;
electron_bridge.py preserves its accepted import/CLI path. One typed query method
serves GUI07's accepted-page operation and GUI05's snapshot-query compatibility
operation. The latter strips the transport acceptance flag before its existing
public page validation. Both paths retain the same record validation and private
session filtering. Registry/schema convenience exports are lazy to avoid import
cycles after the independently reviewed directory moves converge.

Sibling School/Episodes/Neural/Atlas rendering moved to domain-views.mjs when
unified intake made renderer.mjs oversized. The shell still owns navigation,
context and selection; the extracted views report selection through onState.
These are compatibility and ownership repairs, not new dossier semantics.
