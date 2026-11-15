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

The loader already has the reuse proof #1171 needs. It validates:

- the exact builder SHA-256;
- all four canonical source-input file SHA-256 values and their aggregate input digest;
- all seven generated output file SHA-256 values and their aggregate output digest;
- candidate/sense/source-evidence linkage; and
- the content-addressed `CandidateFrontierRelease.release_sha256`.

Therefore reuse must call that existing verifier, not introduce another cache index or
path-based trust record.

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

### 1. Reuse the verified frontier release before invoking the builder

Refactor `_candidate_frontier(run_dir)` into a small resolver with this order:

1. derive the canonical builder path, canonical source directory, output directory,
   and current builder SHA-256;
2. if an output directory already exists, call the existing
   `load_candidate_frontier(output, source_dir, expected_builder_sha256=...)`;
3. if that exact verification succeeds, return the verified release without launching
   the builder;
4. if no usable release exists because the manifest/artifacts are absent, stale,
   malformed, source-mismatched, builder-mismatched, or output-mismatched, run the
   canonical builder once and then call the same loader again; and
5. propagate any failure from the post-build verification. A builder exit or a
   still-invalid release is never converted into a cache hit.

The output path remains a locator only. Reuse is granted solely by the loader's
content/source checks. A current executable Factory release is *not* added as an
input to the candidate-frontier release because the frontier is the upstream
source-grounded research projection; the downstream A09 snapshot already binds the
verified frontier release to the current executable Factory release, staged
realizations, closure, checkpoint and admission evidence.

Progress text must distinguish `reusing` from `rebuilding` so timing evidence and
operator logs show which path ran.

### 2. Extract planning-generation custody into its own owner module

Move `PriorityPlanningGeneration`, retained-object guard, pointer/acceptance snapshot,
binding and currentness functions out of the 356-line source-offer module into
`runtime._source.priority_planning_generation` (canonical import name
`bilqis_mlx.runtime.priority_planning_generation`).

This is both an ownership clarification and a structural requirement: adding the new
transaction contract directly to `priority_source_offer.py` would cross the
repository's >360-LoC interruption threshold.

`priority_source_offer.py` continues to own source-row preparation and
`PreparedPrioritySourceOffer`. It imports the planning-generation owner rather than
duplicating custody logic.

### 3. Deep-authenticate exactly once at transaction binding

`bind_priority_planning_generation(source_context, parent, atlas_artifact_path)` is
the only deep-authentication entry point for the visit transaction. Before it issues
the non-caller-constructible binding it must prove, once:

- the source context is attached to the accepted runtime host;
- the parent is the exact published in-memory accepted student;
- the accepted execution cache matches run, generation and generation binding;
- the pointer and published acceptance file are stable across feature
  authentication;
- full accepted B13 bundle custody validates;
- the source-authority registry resolves from the parent's accepted correction
  frontier and equals the accepted cache registry;
- the accepted feature context authenticates against the supplied Atlas locator and
  accepted generation; and
- the current executable release identity and correction-frontier identity are
  captured as transaction invariants.

The binding records only immutable identities plus owner-held object references
needed for the same process transaction. It does not grant publication, admission,
retention or neural-update authority.

### 4. Downstream calls use a cheap fail-closed currentness guard

Replace repeated deep `_require_planning_generation()` behavior with a currentness
guard that performs no full bundle reload, no parameter-tree generation rehash, no
source-authority registry reconstruction and no accepted feature replay.

The guard still rejects before downstream use if any of these change:

- binding issuer/type, source-context identity, parent object or run directory;
- parent run-identity digest or retained-state/object guard;
- accepted-cache manifest or generation binding;
- live pointer run/generation/manifest/acceptance identity or acceptance-file digest;
- parent correction-frontier canonical digest or accepted source-authority registry
  digest;
- accepted feature receipt/content identity captured by the transaction; or
- current executable release SHA-256.

The pointer/acceptance snapshot is intentionally retained as a cheap filesystem
currentness check. It is small compared with full bundle custody and source-authority
reconstruction and preserves fail-closed detection if another accepted generation is
published during a visit.

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
  - reuse an exactly verified candidate-frontier release before builder launch;
  - expose reuse/rebuild disposition only as operational telemetry/progress.
- `bilqis_mlx/runtime/_source/priority_planning_generation.py` (new)
  - own planning-generation binding, one-time deep authentication and cheap
    currentness validation.
- `bilqis_mlx/runtime/_source/priority_source_offer.py`
  - remove extracted generation-custody code; consume the new owner; preserve offer
    local validation.
- `bilqis_mlx/runtime/_teacher/priority_authority.py`
  - reuse the one authenticated transaction across the complete capability fan-out.
- focused tests under the mirrored runtime test owners.

## Proof obligations

1. Two planner visits with unchanged builder and canonical source inputs launch the
   candidate-frontier builder only on the first visit and return the same verified
   frontier release identity on the second.
2. Builder-byte change, canonical source-input change, missing/malformed artifact or
   generated-output change prevents reuse and causes one rebuild; the rebuilt release
   must pass the ordinary loader.
3. On the 21-capability foundation path, full B13 bundle custody validation,
   source-authority resolution, accepted feature authentication and parameter-tree
   generation hashing each occur once per planning transaction, not once per offer.
4. Cheap downstream guards independently reject pointer/acceptance, in-memory parent,
   correction-frontier/source-authority and executable-release drift; offer-local
   owners still reject feature/source/row holds or drift before candidate execution.
5. A fresh process can reuse a valid frontier directory by content identity, but
   cannot reuse a process-live planning-generation binding.
6. Scalar observable outcome is unchanged: same planning progress/closure/selection,
   signed priority option ordering and selected visit for the same inputs.
7. A bounded 21-capability timing witness records builder launches, deep-auth call
   counts and wall time for cold then warm planning. It must show a material warm-path
   reduction without neural updates.

## Review identity

Design authority: live GitHub issue #1171 plus this artifact. Pinned EGM checkout:
`b3a35956759bf7f024af2ff061b2e0b44b438e4c`.
