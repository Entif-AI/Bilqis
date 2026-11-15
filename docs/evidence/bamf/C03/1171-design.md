# C03 #1171 design: content-addressed planner reuse and one-time generation authentication

## Owned outcome

Reduce the neural-inert planning cost of one foundation-teacher visit without changing
planner meaning, source qualification, accepted-generation authority, correction
semantics, feature custody, or the selected C03 priority result.

The leaf owns two independent optimizations:

1. reuse an already generated candidate-frontier release when its existing manifest
   still proves the exact current builder, canonical Ithkuil source inputs, generated
   outputs, and release digest; and
2. authenticate one immutable accepted planning-generation transaction deeply once,
   then use bounded currentness guards during capability/offer fan-out instead of
   replaying full B13/C09 custody validation for every offer.

Cached planner artifacts and planning bindings remain evidence. They do not become
acceptance, source, correction, feature, or release authority.

## Existing seams

### Candidate frontier

`runtime._admission.atlas_flywheel_runtime._candidate_frontier()` currently runs
`lib/ithkuil/src/build_curriculum_frontier.py` unconditionally before calling
`factory.candidate_frontier.load_candidate_frontier()`.

The loader already has most of the byte/source verification #1171 needs. It validates:

- the exact builder SHA-256;
- all four canonical source-input file SHA-256 values and their aggregate input digest;
- all seven generated output file SHA-256 values and their aggregate output digest;
- candidate/sense/source-evidence linkage; and
- the content-addressed `CandidateFrontierRelease.release_sha256`.

It is **not sufficient by itself as reuse provenance**. The builder manifest lives in
the same mutable directory as the outputs, so a self-consistently rewritten output +
manifest could pass the loader even though the pinned builder did not produce that
cached release. Production is safe today because it always runs the canonical builder
immediately before loading. #1171 must preserve that provenance premise with a durable
owner-held anchor outside the mutable frontier directory.

### Planning generation

`runtime._source.priority_source_offer` currently owns
`PriorityPlanningGeneration`, `bind_priority_planning_generation()`, and
`_require_planning_generation()` in the same 356-line module as prepared source
offers. `_require_planning_generation()` currently mixes two different questions:

- **deep transaction authentication:** accepted B13 bundle custody, source-authority
  resolution, accepted feature replay, generation hash, and stable pointer/acceptance
  binding; and
- **downstream currentness:** is this exact in-memory parent/source context still the
  same accepted generation and has any bound pointer, acceptance, correction,
  feature, source, or release identity changed?

Because the same function is called by offer preparation, offer requalification and
visit selection, full bundle/source-authority validation is repeated across the
21-capability fan-out.

## Chosen architecture

### 1. Reuse only a builder-produced release anchored outside the mutable cache

Refactor `_candidate_frontier(run_dir)` into a small resolver with this order:

1. derive the canonical builder SHA-256 and aggregate digest of the four canonical
   source inputs without consulting the cached frontier manifest;
2. derive a `builder_sha256 + input_digest + executable_factory_release_sha256`
   trust key. The release component is the exact
   `ExecutableFactoryRelease.release_sha256` already consumed by A09. This is a
   deliberate cache-invalidation identity required by #1171 even though the source
   builder itself does not consume the Factory release;
3. resolve an **append-only workstation data-plane trust row** for that key. The row
   records the builder digest, input digest, output digest and
   `CandidateFrontierRelease.release_sha256`, plus a digest-bound canonical receipt;
4. only when that immutable trust row exists, call the ordinary
   `load_candidate_frontier(output, source_dir, expected_builder_sha256=...)` and
   require its builder/input/output/release identities to equal the trusted row before
   reusing it;
5. if the trust row is absent, or the local output directory is absent/stale/corrupt,
   run the canonical builder once, load and verify the result, then publish the trust
   row if absent;
6. if a trust row already exists and a rebuild for the same builder/input/release
   identity
   produces a different output/release identity, fail closed as deterministic planner
   provenance conflict. Never replace the prior trust row; and
7. propagate builder/post-build verification failure. A builder exit or invalid result
   is never converted into a cache hit.

The trust table follows the repository's existing append-only data-plane authority
pattern (`bamf_c05_fixed_school_trust`): update/delete triggers forbid mutation, and
publication is idempotent only for byte-identical canonical receipt content. This row
is **planner-cache provenance**, not model/admission/acceptance authority.

Only documented candidate-frontier validation failures emitted by the loader
(`CANDIDATE_FRONTIER_*` manifest/artifact/source/content invalidity) are classified as
reuse misses. Builder process failures, unexpected exceptions, data-plane trust
conflicts, programmer errors and unrelated I/O failures propagate; they are not
silently converted into rebuilds.

The output path remains a locator only. The current executable Factory release is a
reuse-key invalidator, not a new semantic input to `CandidateFrontierRelease`; A09
still owns the semantic binding between the verified source-grounded frontier and the
current executable release, staged realizations, closure, checkpoint and admission
evidence.

Progress text must distinguish `reusing` from `rebuilding` so timing evidence and
operator logs show which path ran.

### 2. Extract planning-generation custody into its own owner module

Move `PriorityPlanningGeneration`, retained-object guard, pointer/acceptance snapshot,
binding and currentness functions out of the current unified base's 357-line
source-offer module into
`runtime._source.priority_planning_generation` (canonical import name
`bilqis_mlx.runtime.priority_planning_generation`).

This is both an ownership clarification and a structural requirement: adding the new
transaction contract directly to `priority_source_offer.py` would cross the
repository's >360-LoC interruption threshold.

`priority_source_offer.py` continues to own source-row preparation and
`PreparedPrioritySourceOffer`. It imports the planning-generation owner rather than
duplicating custody logic.

The current unified base also includes #1174's source-prefetch contract:
`require_current(..., prepared_rows=...)` and
`execute_accepted_priority_candidate(..., prepared_source_rows=...)`. #1171 must
preserve those exact optional prepared-row semantics while extracting the generation
owner; it must not restore unconditional source redraws or invalidate native operator
prefetch.

### 3. Deep-authenticate exactly once at transaction binding

`bind_priority_planning_generation(source_context, parent, atlas_artifact_path)` is
the only deep-authentication entry point for the visit transaction. Before it issues
the non-caller-constructible binding it must prove, once:

- the source context is attached to the accepted runtime host;
- the parent is the exact published in-memory accepted student;
- the accepted execution cache matches run, generation and generation binding;
- the pointer and published acceptance file are stable across feature
  authentication;
- full accepted B13 bundle custody validates, bracketed by stable filesystem custody
  snapshots over the bundle tree **and** an owner-captured inventory of every
  content-addressed DataPlane dependency that the validator actually consumed;
- the source-authority registry resolves from the parent's accepted correction
  frontier and equals the accepted cache registry, bracketed by a stable stat identity
  for the actual host/provisioned trust-root file selected by C09 custody;
- the accepted feature context authenticates against the supplied Atlas locator and
  accepted generation; and
- the current executable release identity and correction-frontier identity are
  captured as transaction invariants.

The binding records the deep-authenticated identities plus two **currentness fences**:

- a **B13-owner-issued** bundle currentness witness whose deep bind brackets
  `validate_bamf_bundle_custody()` with equal pre/post bundle-tree stat snapshots
  (relative name + device/inode/size/mtime/ctime for the verified root/files) and
  captures the exact external DataPlane identities authenticated by that validation:
  the manifest node digest, every sidecar `object_sha256`, and the current tensor
  `object_sha256` when present; and
- a C09 trust-root stat witness issued by the source-authority custody owner for the
  exact fixed host/provisioned registry that was deeply resolved.

These filesystem/DataPlane identities are not semantic authority. They are cheap
evidence that the bytes and content-addressed dependencies deeply authenticated
moments earlier have not changed. The repository already uses the same stat-bound-
proof doctrine in the shared data plane's verified-file cache. The binding remains
process-live and grants no publication, admission, retention or neural-update
authority.

### 4. Downstream calls use a cheap fail-closed currentness guard

Replace repeated deep `_require_planning_generation()` behavior with a currentness
guard that performs no full bundle hash/parse, no parameter-tree generation rehash, no
source-authority registry reconstruction and no accepted feature replay.

The guard still rejects before downstream use if any of these change:

- binding issuer/type, source-context identity, parent object or run directory;
- parent run-identity digest or retained-state/object guard;
- accepted-cache manifest or generation binding;
- live pointer run/generation/manifest/acceptance identity or acceptance-file digest;
- parent correction-frontier canonical digest or accepted source-authority registry
  digest;
- any B13 bundle-tree stat change after the deep custody proof;
- any disappearance/corruption of the B13 manifest node or sidecar DataPlane objects
  captured by the witness. Currentness calls `data_plane().get_node(manifest_sha256)`
  and `data_plane().get_object(object_sha256)` for those small immutable records and
  therefore rechecks their content digest without re-parsing/revalidating the whole
  BAMF bundle;
- any disappearance/corruption of the current tensor CAS object captured by the
  witness. Currentness calls `data_plane().require_file_object(tensor_object_sha256)`,
  which uses the existing stat-bound digest proof and rehashes if its file identity
  changed;
- any selected C09 host/provisioned trust-root stat change after deep resolution;
- accepted feature receipt/content identity captured by the transaction; or
- current executable release SHA-256.

The pointer/acceptance, B13 bundle/DataPlane witness and C09 trust-root witness are
intentionally retained as cheap currentness checks. If any filesystem fence changes
or any captured DataPlane object fails its ordinary content-addressed read, the hot-
path guard fails closed; it does not silently reauthenticate/rebase the live
transaction. A new planning transaction may then perform fresh deep authentication.
This preserves same-manifest bundle drift, DataPlane node/sidecar/CAS custody drift,
and live trust-root drift detection without re-reading, reconstructing and validating
the complete BAMF bundle 21 times.

### 5. Offer-local checks remain authoritative at their existing boundary

`PreparedPrioritySourceOffer.require_current()` still runs before an offer can be
selected/executed. It continues to require:

- exact run directory, accepted manifest and generation binding;
- current executable release and capability membership;
- exact source-binding digest;
- deterministic row redraw/binding equality;
- accepted feature-owner eligibility/current content;
- salience/source evidence eligibility; and
- packed-row eligibility.

Thus #1171 removes repeated *generation-wide deep authentication*, not per-offer
source/currentness validation. A held/corrected feature or source row still fails at
the same offer boundary before candidate execution.

### 6. The C03 authority owner consumes one transaction result

`issue_foundation_priority_authority()` must:

1. compute A09 planning;
2. bind/deep-authenticate the accepted planning generation once;
3. obtain cache/registry from the already-authenticated binding through the cheap
   currentness guard;
4. prepare all capability offers with that same binding; and
5. rank/select exactly as today.

No capability may silently mint a new planning transaction during fan-out.

`select_accepted_priority_visit()` and `requalify_priority()` must consume that same
planning-generation transaction as well. Requalification may still validate salience,
policy, school/program, source-binding and per-offer eligibility, but it must not call
the accepted-runtime binder or correction-registry resolver as a second generation-wide
deep authentication. The already-authenticated transaction supplies the exact accepted
cache/registry after a cheap currentness guard, then each offer performs its existing
local source/feature/row checks.

## Failure semantics

- Existing frontier artifacts that fail exact loader verification are a reuse miss,
  not authority. The canonical builder may regenerate them once; the newly generated
  release must then verify or the operation fails.
- Builder execution failure, post-build verification failure, accepted-generation
  drift, source-authority drift, correction-frontier drift, feature hold/drift,
  release/source-binding drift and row drift remain hard failures/holds at their
  existing owner boundaries.
- A cached frontier never bypasses A09 deterministic planning, closure, staging,
  executable snapshot, or current-release binding.
- A planning-generation binding is process-live and non-serializable. Cold resume
  creates a fresh deep-authenticated binding; only the candidate-frontier release may
  be reused across processes, and only after its content/source manifest verifies.
- No actual neural optimizer update, human-run state mutation, C07 admission or B13
  generation publication is in scope.

## Implementation surfaces

- `bilqis_mlx/runtime/_admission/atlas_flywheel_runtime.py`
  - reuse an exactly verified + externally trusted candidate-frontier release before
    builder launch;
  - expose reuse/rebuild disposition only as operational telemetry/progress.
- `bilqis_mlx/runtime/_admission/planner_frontier_trust.py` (new)
  - publish/load the append-only data-plane trust receipt keyed by builder + canonical
    source-input + executable Factory release identity.
- `bilqis_mlx/_data_plane/store.py`
  - add the narrow immutable planner-frontier trust table/triggers alongside existing
    append-only BAMF trust records.
- `bilqis_mlx/runtime/_source/priority_planning_generation.py` (new)
  - own planning-generation binding, one-time deep authentication and cheap
    currentness validation.
- `bilqis_mlx/runtime/_custody/bamf_bundle/bundle_currentness.py` (new)
  - B13-owned non-caller-constructible witness: deep-validate once under stable
    pre/post bundle stat snapshots; retain the exact manifest-node, sidecar-object and
    tensor-CAS identities consumed by that validation; then require exact cheap
    filesystem + DataPlane currentness.
- `bilqis_mlx/runtime/_custody/bamf_bundle/source_authority_custody/__init__.py`
  - issue/check the stat witness for the exact host/provisioned C09 trust-root file;
    do not expose a caller-selectable authority path.
- `bilqis_mlx/runtime/_source/priority_source_offer.py`
  - remove extracted generation-custody code; consume the new owner; preserve offer
    local validation.
- `bilqis_mlx/runtime/_teacher/priority_authority.py`
  - reuse the one authenticated transaction across the complete capability fan-out.
- `bilqis_mlx/runtime/_teacher/accepted_priority_visit.py`
  - pass the existing planning-generation binding through requalification rather than
    causing a second deep accepted-runtime lookup.
- `bilqis_mlx/runtime/_teacher/priority_qualification.py`
  - consume cache/registry from the current planning transaction; retain salience,
    program, release, source-binding and offer-local qualification checks.
- focused tests under the mirrored runtime test owners.

## Proof obligations

1. Two planner visits with unchanged builder and canonical source inputs launch the
   candidate-frontier builder only on the first visit and return the same verified
   frontier release identity on the second.
2. Builder-byte, canonical source-input or executable Factory release change selects a
   new trust key and forces a rebuild. Missing/malformed/tampered local artifacts under
   an existing trust row rebuild once but may be reused only if the rebuilt
   output/release equals that immutable row. A self-consistently rewritten cache
   directory must never be a hit.
3. On the 21-capability foundation path, generation-wide full B13 bundle custody and
   live C09 registry resolution occur once before fan-out. The already-once
   `_current_cache` generation hashing and accepted feature authentication remain
   once-per-transaction regressions, not claimed new savings. Requalification consumes
   the same transaction and no offer repeats generation-wide deep authentication.
4. Cheap downstream guards independently reject pointer/acceptance, in-memory parent,
   correction-frontier/source-authority, same-manifest B13 bundle-file change,
   B13 DataPlane manifest-node/sidecar-object/tensor-CAS drift, live C09 trust-root
   change and executable-release drift; offer-local owners still reject
   feature/source/row holds or drift before candidate execution.
5. A fresh process can reuse a valid frontier directory by content identity, but
   cannot reuse a process-live planning-generation binding.
6. Scalar observable outcome is unchanged: same planning progress/closure/selection,
   signed priority option ordering and selected visit for the same inputs.
7. A bounded 21-capability timing witness uses the existing neural-inert
   `PreNeuralJourneyGuardTests` foundation fixture. Before implementation, record three
   wall-time samples for the exact priority-planning subtest and use their median as
   the frozen control. After implementation, record three warm-path samples on the
   same host/fixture after one cold trust/frontier population. PASS requires both
   **>=20% median wall-time reduction** and **>=2.0 seconds absolute median reduction**,
   plus identical selected priority/visit identity. Record builder launches, B13
   deep-custody calls and C09 deep-registry resolutions. No neural updates are
   permitted. The witness must also preserve #1174 prepared-row behavior.

## Review identity

Design authority: live GitHub issue #1171 plus this artifact. Pinned EGM checkout:
`b3a35956759bf7f024af2ff061b2e0b44b438e4c`.
