# #1238 Candidate Identity Binding Design v3

## Problem

The canonical #1169 raw-v2 digest scans about 953.8 MB for one full B01 candidate state. C05, acceptance, B13 and retry repeatedly hash the same process-live numerical state. #1238 must remove those duplicate scans without changing raw-v2 and without allowing stale identity reuse after mutation.

Object identity alone is insufficient because MLX arrays support same-object mutation and derived aliases. The first design's sealed subclass is rejected: MLX views shed the subclass, Python >=3.11 is supported, and a Python 3.14-only subclass buffer override is not a storage invariant.

## Controlling invariants

- Raw-v2 bytes and digest remain exactly #1169-compatible.
- Public candidate_identity_digest(state) remains a full-content canonical fallback and never silently memoizes mutable caller objects.
- Reuse exists only for process-local numerical storage placed behind the candidate-owner write barrier before a writable alias can escape.
- Unsupported runtimes or caller-owned numerical trees use canonical full hashing.
- #1231 continues to own accepted-parent visit/step currentness.
- #1237 continues to own publication hydration/load sequencing.
- Cold reconstruction never self-ratifies a fresh digest. A durable expected identity must match before a process-local binding is issued.

## Storage-range write barrier

Add a private candidate numerical-custody module under learning/_retention/_atlas_candidate/.

The module installs idempotent guards on the mutable mlx.core.array Python type while preserving the original methods in private closures.

A registry tracks protected storage address intervals and owner reference counts. Storage intervals are derived from the original MLX serialization-state bridge (`__getstate__`) before that hook is wrapped: current MLX 0.32.4 returns `(numpy_view, version)`, and that NumPy view exposes the backing pointer, shape, strides, and itemsize without hashing tensor contents. The guard retains the original C-extension methods only in private module closures. It MUST NOT call `np.asarray(self)` from a patched buffer/export hook, because that can recurse through the Python export machinery.

For any array whose current storage interval overlaps protected candidate storage:

- patched __setitem__ rejects writes;
- every current MLX in-place operator (__iadd__, __isub__, __imul__, __itruediv__, __ifloordiv__, __imod__, __ipow__, __imatmul__, bitwise and shift variants) rejects writes;
- patched __buffer__ returns a read-only view, so roots and derived aliases cannot yield writable NumPy or memoryview aliases;
- if the active MLX array type exposes `__array__`, patched `__array__` returns only a read-only view for protected storage; current pinned MLX 0.32.4 on the known-good host does not expose that Python attribute, but the guard capability probe treats any present zero-copy array export as mandatory coverage;
- patched __dlpack__ rejects export, preventing zero-copy writable DLPack aliases.
- patched __getstate__ and __reduce_ex__ return detached serialization state for protected arrays because current MLX otherwise exposes a writable shared NumPy alias through pickle state;
- patched __setstate__ rejects mutation of protected arrays.

The export wrappers are also fixed: guarded `__buffer__` returns `original_buffer(self, flags).toreadonly()` for protected overlap; guarded `__getstate__` calls the saved original and replaces its NumPy payload with `np.array(payload, copy=True)`; guarded `__reduce_ex__` calls the saved original reducer and replaces tuple element 2 with that detached protected state while preserving the reducer callable, constructor args, list iterator, and dict iterator; guarded `__array__`, when present, calls the saved original and marks the returned NumPy view non-writeable before returning it; guarded `__dlpack__` rejects protected overlap rather than exporting shared writable storage. Canonical identity hashing remains exactly in `identity.py`: its existing `np.asarray`/buffer read path sees only read-only protected views after guard installation, which is sufficient because hashing only reads bytes. The saved original `__getstate__` bridge is private metadata plumbing for span/currentness checks, not a second canonical byte reader.

The guard is storage-based, not subclass-based. Slice, reshape, view, stop-gradient, and transpose aliases that become plain mx.array objects remain protected when they share candidate storage.

Storage span calculation is normative. Let the saved original `__getstate__` return NumPy view `n`; let `p = n.__array_interface__["data"][0]`, `shape = n.shape`, `strides = n.strides`, and `item = n.itemsize`. For non-empty arrays, compute with unbounded Python integers:

`lo = sum(min(0, (dim - 1) * stride) for dim, stride in zip(shape, strides))`

`hi = sum(max(0, (dim - 1) * stride) for dim, stride in zip(shape, strides)) + item`

The protected half-open span is `[p + lo, p + hi)`. This covers contiguous, stepped, transposed, and negative-stride views. A rank-zero scalar has an empty shape/stride tuple and therefore protects `[p, p + item)`. A zero-element array contributes no address span because it contains no identity bytes, but its exact object/storage witness remains part of the binding. Every binding require recomputes every non-empty leaf span through the saved original bridge and requires exact equality with the issued span; a copy-on-write MLX mutation therefore fails currentness even if a mutation hook somehow did not reject it.

Current production execution documentation pins Python 3.14 + MLX 0.32.4, while current `quality.yml`/`release.yml` install MLX 0.31.1. #1238 does not choose support by version string and does not silently change either pin. `candidate_identity_binding_supported()` is a capability gate that must pass under both retained environments: local/native proof covers 0.32.4; hosted quality/release proof covers 0.31.1. If either environment lacks a required hook, that environment remains correct through canonical fallback and the optimization is reported unsupported there.

On first use the guard performs one locked, idempotent installation/self-test. The exact mutation slot inventory is `__setitem__`, `__iadd__`, `__iand__`, `__ifloordiv__`, `__ilshift__`, `__imatmul__`, `__imod__`, `__imul__`, `__ior__`, `__ipow__`, `__irshift__`, `__isub__`, `__itruediv__`, and `__ixor__`. The exact foreign-export/state inventory is `__buffer__`, `__dlpack__`, `__getstate__`, `__reduce_ex__`, and `__setstate__`, plus `__array__` whenever that attribute exists on the active MLX array type. The installer captures each original exactly once, creates each guard exactly once, verifies every required slot is replaceable, installs the full set while holding the installation lock, and rolls every changed slot back to its captured original if any installation or self-test step fails.

The self-test reports supported only if: (1) original `__getstate__` yields `(numpy.ndarray, version)` and the root/alias span calculations agree; (2) root, reverse, stepped, slice, transpose, reshape, stop-gradient, rank-zero, `copy.copy`, and `copy.deepcopy` cases either share a recognized protected span or are demonstrably detached; (3) indexed and every listed in-place operation cannot change protected bytes; (4) direct NumPy/memoryview and any present `__array__` export cannot change protected bytes; (5) DLPack export of sharing protected storage fails; (6) serialization state is detached and `__setstate__` cannot mutate protected storage; and (7) an unprotected disposable array retains ordinary MLX behavior.

Successful installation issues one process-local `_CandidateIdentityGuardCapability` containing a monotonic generation, private token object, guarded type identity, and the exact `(slot_name, original_callable, guard_callable)` inventory. Every CandidateIdentityBinding stores that generation/token. Every require verifies the active array type and every live slot still equal the recorded guard callable. If any protected binding has ever been issued and slot integrity later drifts, the guard is **poisoned**: all existing bindings fail closed, new bindings are disabled, and canonical fallback is not used for those previously bound states because a writable escape may have existed. Fallback is allowed only when support was absent before binding issuance or the state was explicitly classified unbindable. A new guard generation may be installed only after all prior protected owners are gone; old-generation bindings never become valid again.

### Correctness / threat boundary for the process-local barrier

#1238 is an in-process **custody/currentness optimization**, not a sandbox against a malicious Python extension or hostile code already executing in the trainer process. Its unauthorized-mutation guarantee covers every repository-owned and supported-dependency path that reaches MLX arrays through the active Python type surface, NumPy/buffer export, DLPack, pickle/state hooks, normal indexing/in-place syntax, and aliases created from those paths. It also covers accidental later monkeypatch drift by poisoning bindings.

It does **not** claim to defeat an adversarial in-process actor that, before Bilqis installs the guard, deliberately saves an original MLX C-extension descriptor and later invokes that saved descriptor directly; nor raw-pointer/`ctypes` writes, arbitrary native extensions, debugger memory writes, or a transient monkeypatch that bypasses the active guarded slot and restores it before currentness inspection. Those mechanisms can already violate frozen dataclasses, mapping proxies, and every other Python-level custody invariant. Treating them as in-scope would require native memory protection / process isolation, which is not #1238 and would materially change the trainer architecture.

To keep this boundary honest rather than rhetorical:

- `identity_binding.py` is imported by the private CandidateState owner module at module initialization and installs/probes the guard before Bilqis can classify any CandidateState as `BINDABLE` or issue any binding;
- public/caller-owned numerical state that may predate that import is `UNBINDABLE` and receives canonical full hashing;
- a repository audit gate must find **zero** production occurrences that capture/call `mx.array` mutation/export descriptors (`mx.array.__setitem__`, `__i*__`, `__buffer__`, `__array__`, `__dlpack__`, `__getstate__`, `__reduce_ex__`, `__setstate__`) outside `identity_binding.py`, and zero `ctypes`/raw-pointer writes against candidate numerical storage;
- supported third-party code used in the candidate lifecycle is exercised through the alias/export self-tests; any future dependency that requires descriptor capture/raw writes makes the capability unsupported until separately reviewed;
- the guard capability record includes an `installed_before_bindable_state=True` invariant, and binding issuance rejects otherwise.

Under this explicit boundary, “unauthorized mutation cannot reuse a binding” means unauthorized mutation through the supported Bilqis/MLX execution surface. It is not a claim of tamper resistance against arbitrary code execution inside the same Python process.

Unprotected arrays retain ordinary MLX behavior. The write barrier is a Python runtime-integrity boundary, not protection against arbitrary native-memory corruption or a malicious C extension that bypasses Python mutation/export APIs.

## Protect only owner-controlled numerical storage

Protection must be registered before a writable alias can escape.

Owner-protected paths:

- Accepted cold load: _load_retained_candidate_state_with_parts receives freshly loaded MLX arrays. Protect the numerical tree before returning state/parts. Binding is delayed until durable acceptance or run-identity comparison succeeds.
- Generation zero: protect the fresh _create_unbound_bamf_optimizer tree before the initial CandidateState escapes.
- CandidateTransaction: _issue_transaction is private. Its optimizer consists of already-protected parent leaves plus fresh functional AdamW or motif leaves. Protect the transaction owner before return.
- resolve_candidate: when the issued transaction is protected, register the new CandidateState as another owner of those protected ranges.
- Private motif materialization uses fresh owner-local arrays before _issue_transaction and follows the same rule.

The protection owner records every numerical leaf range before returning the owning transaction/state. A later MLX indexed or in-place operation is expected to be copy-on-write on pinned MLX 0.32.4; the guard still rejects it when it targets protected storage. A sharing view created after protection remains covered because every guarded mutation/export hook derives the view's current storage interval from the saved original `__getstate__` bridge and checks interval overlap. A NumPy reshape that necessarily copies may remain writable because it no longer overlaps protected candidate storage; tests assert the candidate bytes remain unchanged rather than requiring all detached copies to be immutable.

Valid but not automatically bindable:

- public issue_parameter_extension_state(parent, optimizer, policy) accepts caller-owned arrays;
- public prepare_package_import(parent, parameters, slices) accepts caller-owned arrays and retains them;
- generic/test-created CandidateState objects may contain mutable or aliased arrays.

Those paths keep canonical full-content hashing unless a separate private production issuer proves fresh ownership. Bindability must be explicit; a generic validation error must never be treated as a cache miss.

## Process-local CandidateIdentityBinding

Keep raw-v2 framing in identity.py unchanged.

Add private-issued CandidateIdentityBinding with:

- canonical raw-v2 digest;
- identity scheme and optimizer step;
- exact CandidateState weak reference;
- exact AdamWStateTree identity;
- exact weak references for every numerical leaf in parameters, m, v, and update_counts;
- topology and extents digests supplied by the authoritative caller;
- canonical small policy snapshot/digest;
- allocation object identity and allocation digest;
- step-proof object identities and proof-digest tuple;
- custody object/value snapshot;
- schema version and private issuer token.

A weak registry keyed by exact CandidateState identity stores only owner-issued bindings and does not extend state lifetime.

The same owner module maintains a second identity-safe weak status registry keyed as `id(state) -> (weakref.ref(state), status, reason, issuer_token)`. Status is exactly one of `BINDABLE` or `UNBINDABLE`; absence means `UNCLASSIFIED`, never implicit fallback. Callback cleanup removes an entry only if the stored weakref is the same weakref being finalized, so Python id reuse cannot delete a successor entry.

Status issuance is private and fixed at these owner boundaries:

- cold `_load_retained_candidate_state_with_parts`: `BINDABLE` only after the runtime guard is supported and every numerical leaf is protected; `UNBINDABLE` with reason `RUNTIME_UNSUPPORTED` if the guard is unavailable before any binding exists;
- fresh generation-zero preparation: same `BINDABLE`/`RUNTIME_UNSUPPORTED` rule immediately after CandidateState construction and before run identity;
- private `_issue_transaction` / `resolve_candidate`: `BINDABLE` only when the transaction's numerical owner is protected and the resolved state adopts that owner; otherwise owner code fails rather than silently downgrading;
- public `issue_parameter_extension_state` with caller-supplied optimizer: `UNBINDABLE` reason `CALLER_OWNED_NUMERICAL_STATE` unless a private production issuer supplied an already-protected owner token;
- package-import candidate preparation/adoption with caller-provided arrays: `UNBINDABLE` reason `CALLER_OWNED_NUMERICAL_STATE`;
- generic/test-created CandidateState: remains `UNCLASSIFIED` and continues to use the public canonical `candidate_identity_digest` directly. It may not pass through the private reuse helper.

`candidate_identity_for_state(...)` is therefore a private production convenience, not a new public hashing contract: explicit/saved binding -> strict require; no binding + `UNBINDABLE` -> canonical full hash; no binding + guard unsupported before issuance -> canonical full hash; no binding + `BINDABLE` or `UNCLASSIFIED` -> fail closed. A previously bound state whose guard capability is poisoned never transitions to `UNBINDABLE` and never falls back.

APIs:

- candidate_identity_binding_supported()
- bind_candidate_identity(state, topology_digest, extents_digest, expected_digest=None)
- require_candidate_identity_binding(binding, state, topology_digest, extents_digest)
- candidate_identity_for_state(state, topology_digest, extents_digest, binding=None)

Lifecycle semantics are exact:

- `bind_candidate_identity(...)` is idempotent for one exact registered state. If the registry already contains a binding, it calls `require_candidate_identity_binding(...)`, checks `expected_digest` when supplied, and returns that same binding without hashing again.
- `require_candidate_identity_binding(...)` never falls back. Any supplied binding that is stale, mismatched, malformed, no longer protected, or bound to another state/topology/extents raises the ordinary candidate-invalid authority error.
- `candidate_identity_for_state(...)` first requires an explicitly supplied binding; otherwise it requires an existing exact-state registry binding. If neither exists, canonical hashing is permitted only when the runtime is UNSUPPORTED or the state was explicitly classified UNBINDABLE at its owner boundary. A state that is marked owner-bindable but lacks its required binding is an error, not a cache miss.
- Binding registry lookup is by `id(state)` plus a weak reference equality check so Python id reuse cannot resurrect stale authority. Weak finalizers release storage-range owner references.

The nonnumerical witness schema is fixed, not implementation-defined:

- policy witness = canonical JSON bytes of `state.policy.to_record()` plus SHA-256 of those bytes;
- allocation witness = exact allocation object weak reference plus `state.allocations.digest`;
- proof witness = ordered tuple `(id(proof), weakref(proof), proof.digest)` for every step proof;
- custody witness = `None` or the exact tuple `(run_id, generation, manifest_sha256, topology_digest, extents_digest)` from `CandidateCustodyIdentity`;
- optimizer witness = exact AdamWStateTree object identity, sorted numerical key census for each raw-v2 group, exact weak reference for every numerical leaf, and each leaf's protected storage interval recorded at issuance;
- state witness = identity scheme, optimizer step, schema version, topology digest, and extents digest.

First bind:
1. require protected owner storage and authoritative topology/extents;
2. validate cheap structural and non-numerical witnesses;
3. compute existing canonical candidate_identity_digest(state) exactly once;
4. if expected_digest is supplied, require equality;
5. snapshot currentness witnesses and issue the binding.

Reuse:
1. exact state, optimizer, and tensor references;
2. protected storage remains registered;
3. scheme, step, topology, and extents unchanged;
4. policy, allocation, proof, and custody witnesses unchanged;
5. return stored raw-v2 digest with zero tensor-byte scan.

Unsupported, unavailable, or unbindable state uses explicit canonical fallback. Malformed bindings fail closed rather than becoming cache misses.

## Cold issuance

Generation zero:
- fresh genesis: `_create_unbound_bamf_optimizer` -> `CandidateState` -> protect owner storage -> `bind_candidate_identity(..., expected_digest=None)` exactly once -> use `binding.digest` as `BamfRunIdentity.initial_candidate_identity_sha256` -> reuse that same binding through preparation authority, initial binding, trust and publication;
- cold genesis: protect loaded storage before return, then replace the current `codec.py` raw digest comparison with `bind_candidate_identity(..., expected_digest=run_identity.initial_candidate_identity_sha256)`. That call itself is the one full cold proof; no pre-bind digest comparison is allowed.

Non-genesis:
- load_bamf_bundle protects storage but does not self-issue identity authority;
- require_published_acceptance parses the persisted acceptance record, then replaces its current direct `candidate_identity_digest(student.retained_state)` equality with `bind_candidate_identity(..., expected_digest=acceptance.candidate_identity_sha256)`. The bind itself performs the one full-content verification and only issues on equality;
- subsequent _identity_from_pointer, accepted runtime, and same-process B13 consumers reuse that exact binding.

Hydration sequencing remains #1237-owned.

## C05 exact-state continuity

Current ordinary C05 creates a preview CandidateState, but prepare_bamf_visit later calls resolve_candidate again and constructs a second equivalent state. Motif C05 is worse: `_candidate_from_live_parent` creates `preview = resolve_candidate(...)`, then `derive_motif_successor_bundle(...)` calls `resolve_candidate(...)` again, so the bundle actually screened by C05 already contains a second CandidateState. Both duplicate resolutions break exact-object binding continuity.

Change live FactoryRetentionEvaluation to retain privately and non-serially:
- exact parent CandidateState plus parent CandidateIdentityBinding when bindable;
- exact CandidateState actually carried by the C05-screened successor bundle plus candidate CandidateIdentityBinding when bindable.

Its retention decision still persists only digest strings.

For ordinary successors, `_candidate_from_live_parent` resolves exactly once and passes that state into `derive_successor_bundle`. For motif successors, change `derive_motif_successor_bundle` to accept the already-resolved state produced by `_candidate_from_live_parent`; it still consumes the transaction for motif transition authority, but it MUST NOT resolve the transaction again. FactoryRetentionEvaluation records `candidate_bundle.retained_state` and requires it to be the exact resolved state. `prepare_bamf_visit` uses `evaluation.candidate_state` for the accepted retained state instead of rebuilding it. Rejected visits keep the existing rollback behavior. Tests require `is` identity continuity through ordinary and motif C05 -> decision -> acceptance -> B13.

Package-import evaluation shares the same evaluation owner, but caller-owned package-import candidate arrays remain explicitly unbindable unless a future private issuer proves ownership. That path uses canonical full hashing and carries no reusable candidate binding.

## Acceptance capability threading

accept_and_publish owns the authoritative successor bundle, topology and extents.

Extend mint_acceptance_binding to receive the explicit candidate identity binding plus authoritative topology/extents from accept_and_publish. It must require:
- exact retained CandidateState object;
- authoritative successor topology/extents;
- bound digest equals the retention decision candidate identity.

Do not infer successor extents from CandidateState custody because motif successors may change extents while preserving parent custody fields.

A live AcceptedCandidateBinding may carry the process-local CandidateIdentityBinding in a private non-public field. _public_record, persisted digest, and historical parsing remain byte-for-byte unchanged. Parsed historical acceptances never gain live process-local identity authority.

B13 require_acceptance consumes that private capability for the exact in-memory candidate. If absent because the authority is historical, cold, unbindable, or running on an unsupported Python runtime, it uses the canonical proof path.

## Successor-generation authority

successor_candidate_identity_digest and initial_generation_candidate_identity_digest remain durable generation authorities with unchanged canonical payloads.

Allow their internal payload builder to consume an already-validated raw candidate digest when an exact CandidateIdentityBinding is supplied. Serialized fields and resulting generation hashes must remain identical.

## Production callsite matrix

Before migration, classify every production candidate_identity_digest call as one of:

- #1238 bind/reuse: C05 training parent/candidate evidence, parent-assessment cache identity, adaptive retention seed, live acceptance, successor-generation authority, same-process B13 acceptance validation, and same-process retry where the exact bound state is already loaded.
- Cold full proof then bind: generation-zero run identity validation and non-genesis persisted acceptance validation.
- Canonical fallback: caller-owned package import, public parameter-extension states, generic mutable/test states, unsupported Python runtime.
- #1231: visit/step accepted-parent currentness including _identity_from_pointer, _validated_step_decay, _admit_loaded_candidate_step, and teacher/current-visit checks unless #1231 has already introduced its own binding consumer.
- #1237: publication parent/child load sequencing and post-write reload. #1238 may reuse identity on those already-loaded objects but must not alter hydration orchestration.
- Intentional full validation: external or cold custody comparisons where no live process-local binding exists.

Record the final matrix in tests or turn-in evidence.

The initial exact migration surface for this issue is deliberately narrower than the repository-wide 80-call census on refreshed unified base `df58fd5b`. Modify only these live-path consumers unless implementation proof exposes another duplicate scan on the same exact state:

- `learning/_retention/_atlas_candidate/identity.py`: canonical raw-v2 remains authoritative; add counters only, no memoization.
- new `learning/_retention/_atlas_candidate/identity_binding.py`: guard capability, protected-storage ownership, binding issue/require/fallback, metrics snapshots.
- `learning/_retention/_atlas_candidate/state.py` and `transaction.py`: protect owner-created numerical trees and transfer owner references through exact state issuance; do not change #1231 step-currentness comparisons.
- `runtime/_capability/factory/_factory_retention_support.py`: resolve one exact candidate state, bind parent/candidate where owner-proven, and remove motif double resolution.
- new private `runtime/_capability/factory/_factory_identity_evaluation.py` is mandatory: move the FactoryRetentionEvaluation type/issuer there before adding #1238 fields so `factory_retention_owner.py` shrinks below the repository >360 LoC interruption threshold. This structural move is the first implementation mutation after the required Work Stack checkpoint.
- `runtime/_capability/factory/_factory_parent_assessment_cache.py`: consume the already-required parent binding instead of rehashing.
- `learning/_retention/atlas_acceptance.py`: mint live acceptance from explicit candidate binding when available, with historical/public serialization unchanged.
- `runtime/_custody/bamf_bundle/genesis/records.py`: allow generation-payload construction to consume an already-required raw candidate digest without changing canonical bytes.
- `runtime/_custody/bamf_bundle/admission.py`: thread the exact retained state/binding into live acceptance and ordinary/motif successor derivation; leave #1231 candidate-step currentness untouched.
- `runtime/_custody/bamf_bundle/publication/authority.py`: live B13 acceptance consumes the live binding; canonical fallback remains for historical/unbindable paths.
- `runtime/_custody/bamf_bundle/publication/acceptance.py`: cold persisted acceptance performs one full proof and only then issues the process-local binding for the loaded state; parent hydration ordering remains #1237-owned.
- `runtime/bamf_operator/session.py` and `session_support.py`: preserve evaluation.candidate_state and report visit deltas; do not change scheduling/retention policy.
- `runtime/_batch/factory_candidate_training.py`: report per-step identity metric deltas in existing `FactoryCandidateStep.realized_cost` only.

All other production `candidate_identity_digest(...)` calls remain canonical full proof in #1238 unless the exact same bound object is already present at that call and a focused migration is necessary to satisfy one of the acceptance bullets. In particular, teacher/current-visit and candidate-step guards remain #1231-owned; persisted bundle hydration/reload orchestration remains #1237-owned; public Atlas/factory-release/package-import/parameter-extension paths remain canonical fallback unless they already receive a private owner-issued binding without changing their authority boundary.

### Exhaustive current production census at base `cde85fe9`

Categories: `CORE` = canonical definition/wrapper; `R` = #1238 live bind/reuse migration; `C` = cold full-proof performed by first bind against durable expected digest; `F` = canonical fallback intentionally unchanged; `P` = intentional independent full-content proof unchanged; `#1231` = sibling currentness ownership unchanged. A row with several line numbers accounts for every occurrence in that function.

| Base callsite | Function | Category / exact treatment |
|---|---|---|
| `learning/_retention/_atlas_candidate/identity.py:94` | `candidate_identity_digest` | `CORE`; raw-v2/legacy canonical implementation stays byte-identical; add metrics only. |
| `learning/_retention/_atlas_candidate/state.py:270` | `_issue_promotion_transition_state` | `F`; public transition validation keeps canonical proof. The newly issued state has no inherited binding and may be separately bound by a private owner later. |
| `learning/_retention/_atlas_candidate/transaction.py:142` | `_issue_transaction` | `#1231`; current unified base now binds parent currentness at transaction issuance. #1238 may consume an existing full-state binding here only if it preserves #1231's object-guard/currentness authority. |
| `learning/_retention/atlas_acceptance.py:273` | `mint_acceptance_binding` | `R`; replace raw call with strict supplied/live registry binding require, fallback only for explicitly unbindable/unsupported state. |
| `runtime/_admission/atlas_flywheel_runtime.py:131` | `_accepted_checkpoint` | `#1231`; accepted-runtime currentness remains sibling-owned. |
| `runtime/_admission/jit/jit_adoption_native.py:61` | `_authenticate_native_staged_candidate` | `P`; native staged-adoption boundary remains an independent full proof. |
| `runtime/_admission/jit/jit_adoption_native.py:115,116,118` | `_accepted_native_retry` | `P`; cross-artifact retry comparison remains independent full proof. |
| `runtime/_capability/_plasticity_promotion/issuance.py:42,43` | `validated_promotion_transition_fields` | `F`; public policy-transition surface remains canonical and produces a distinct state/binding lifecycle. |
| `runtime/_capability/factory/_factory_parent_assessment_cache.py:232` | `factory_parent_assessment_identity` | `R`; consume required parent binding. |
| `runtime/_capability/factory/_factory_retention_support.py:83,84` | `_candidate_from_live_parent` | `R`; bind/reuse exact transaction parent and authenticated loaded parent; preserve equality semantics. |
| `runtime/_capability/factory/_factory_retention_support.py:114,115` | `_package_import_from_live_parent` | `F`; caller-owned package-import candidate remains unbindable. |
| `runtime/_capability/factory/factory_retention_owner.py:57` | evaluation `issue` | `R`; generation-authority builder consumes already-required candidate raw binding. |
| `runtime/_capability/factory/factory_retention_owner.py:63,65` | evaluation `issue` | `R`; parent/candidate digests come from exact carried bindings. |
| `runtime/_capability/factory/factory_retention_owner.py:177` | `_adaptive_retention_screen` | `R`; fresh-seed identity uses the same exact candidate binding. |
| `runtime/_custody/bamf_bundle/accepted_runtime.py:86` | `_identity_from_pointer` | `#1231`; unchanged. |
| `runtime/_custody/bamf_bundle/admission.py:95,96` | `derive_motif_successor_bundle` | `#1231` for parent-currentness comparison; #1238 only removes duplicate `resolve_candidate` and threads the already-resolved state. |
| `runtime/_custody/bamf_bundle/admission.py:294` | `accept_and_publish` | `R`; successor-generation payload consumes the required candidate binding. |
| `runtime/_custody/bamf_bundle/atlas_admission.py:182,184,218` | `_issue_atlas_admission_binding`, `require_atlas_admission_binding` | `F`; public Atlas extension/admission remains canonical. |
| `runtime/_custody/bamf_bundle/codec.py:273` | `load_bamf_bundle` genesis run-identity check | `C`; replace the direct raw equality with first bind against persisted `initial_candidate_identity_sha256`. Non-genesis codec load protects storage but does not self-ratify. |
| `runtime/_custody/bamf_bundle/factory_release/admission.py:57,58,120,121,148,175` | inert-state/admission validators | `F`; factory-release adoption is a distinct public admission surface. |
| `runtime/_custody/bamf_bundle/feature/acceptance.py:79,133,149` | retention/feature acceptance | `P`; feature manifest acceptance remains an independent durable proof path and does not become #1238 authority. |
| `runtime/_custody/bamf_bundle/genesis/preparation.py:63` | `_build_initial_candidate` | `R`; fresh protect + first bind once, then populate `BamfRunIdentity` from binding digest. |
| `runtime/_custody/bamf_bundle/genesis/preparation.py:143` | `validate_initial_generation_binding` | `R`; reuse the fresh live binding through initial issuance. |
| `runtime/_custody/bamf_bundle/genesis/preparation.py:175` | `validate_parsed_initial_generation_binding` | `C`; cold parsed genesis binds once against persisted run identity, then generation payload reuses. |
| `runtime/_custody/bamf_bundle/genesis/preparation_authority.py:171` | `_validate_candidate_source_authority` | `R`; fresh genesis candidate uses registry binding created before run identity. |
| `runtime/_custody/bamf_bundle/genesis/preparation_authority.py:237` | `_validate_candidate_b01_authority` candidate side | `R`; reuse fresh candidate binding. |
| `runtime/_custody/bamf_bundle/genesis/preparation_authority.py:238` | `_validate_candidate_b01_authority` independently reconstructed expected state | `P`; expected-state oracle remains full proof and is not granted live authority. |
| `runtime/_custody/bamf_bundle/genesis/records.py:122` | `_candidate_identity_payload` | `R`; accept/lookup already-required live raw binding when available, otherwise canonical fallback. Canonical payload bytes unchanged. |
| `runtime/_custody/bamf_bundle/genesis/records.py:144,150` | initial/successor generation digest definitions | `CORE`; wrapper definitions unchanged except optional validated raw identity input to payload builder. |
| `runtime/_custody/bamf_bundle/genesis/records.py:164` | `_mint_initial_generation_binding` | `R`; generation digest builder reuses fresh binding via payload builder. |
| `runtime/_custody/bamf_bundle/motif/source_continuation.py:190,191` | `stage_source_qualified_motif_allocation` | `#1231`; parent currentness remains sibling-owned. |
| `runtime/_custody/bamf_bundle/motif/transition.py:124` | transition `derive` | `R`; final motif state is sealed/bound once here using B12 candidate extents + parent topology supplied by owner, and C05 reuses that binding. |
| `runtime/_custody/bamf_bundle/publication/acceptance.py:49` | `require_accepted_parent` | `C`; loaded parent may first-bind against `acceptance.parent_candidate_identity_sha256`; loading order remains #1237. |
| `runtime/_custody/bamf_bundle/publication/acceptance.py:120` | `_require_non_genesis_acceptance_identity` | `C`; replace raw equality with first bind against persisted child acceptance digest. |
| `runtime/_custody/bamf_bundle/publication/acceptance.py:142,159` | `_require_non_genesis_acceptance_identity` generation authority | `R`; once child raw binding is established, generation payload reuses it; durable generation hash remains independently recomputed. |
| `runtime/_custody/bamf_bundle/publication/acceptance.py:205` | `require_published_acceptance` parent identity | `R` if accepted parent object is already bound, otherwise `C` against the persisted parent digest; hydration choice/order remains #1237. |
| `runtime/_custody/bamf_bundle/publication/authority.py:82` | `require_acceptance` | `R`; live binding is strict authority for exact in-memory candidate. |
| `runtime/_custody/bamf_bundle/publication/authority.py:91` | `require_acceptance` generation authority | `R`; generation payload consumes the same raw binding. |
| `runtime/_custody/bamf_bundle/publication/authority.py:131` | `validate_parent_transition` motif candidate | `R`; exact live motif candidate binding. |
| `runtime/_custody/bamf_bundle/publication/authority.py:194,195` | `authenticate_current_successor_retry` generation identities | `R`; current child/candidate generation payloads reuse any already-bound raw state; durable generation hash comparison still occurs. |
| `runtime/_custody/bamf_bundle/publication/authority.py:208` | `authenticate_current_successor_retry` parent raw identity | `R` on already-authenticated loaded parent; no hydration sequencing change. |
| `runtime/_custody/bamf_bundle/publication/events.py:31` | `_validated_c03_rejection_evidence` | `#1231`; accepted/current visit evidence remains sibling-owned. |
| `runtime/_custody/bamf_bundle/publication/genesis_trust.py:48` | `_trust_record` fresh candidate | `R`; reuse fresh genesis binding. |
| `runtime/_custody/bamf_bundle/publication/genesis_trust.py:161` | `require_initial_generation_trust_root` cold student | `C/R`; codec/run-identity first bind must already exist and is required here; no second raw hash. |
| `runtime/_custody/bamf_bundle/publication/retry.py:46,47` | `_same_initial_candidate` | `R` when exact live/cold-bound states exist; otherwise `C` first-bind each against their durable genesis identity before comparison. |
| `runtime/_custody/bamf_bundle/publication/retry.py:229` | `_sealed_genesis_binding` | `R`; generation payload reuses established genesis raw binding. |
| `runtime/_custody/bamf_bundle/vocabulary/admission.py:241` | `_stage_vocabulary_extension_from_accepted` | `F`; public vocabulary extension remains canonical. |
| `runtime/_custody/bamf_bundle/vocabulary/admission_records.py:26` | `_candidate_handoff_digest` | `P`; portable handoff authority remains independent full generation proof. |
| `runtime/_custody/bamf_bundle/vocabulary/admission_records.py:123` | `__post_init__` | `F`; public admission record validation remains canonical. |
| `runtime/_custody/bamf_bundle/vocabulary/registry_export.py:201` | `read_accepted_vocabulary_registry_export` | `P`; exported-registry validation remains independent full proof. |
| `runtime/_projection/owner_generation_projection.py:53` | `_teacher_visit` | `#1231`; unchanged. |
| `runtime/_teacher/accepted_priority_visit.py:111,131` | `accepted_priority_school`, `select_accepted_priority_visit` | `#1231`; unchanged. |
| `runtime/_teacher/accepted_teacher_custody.py:107,215,251,276` | `_student_reference`, visit currentness, successor derivation | `#1231`; unchanged. |
| `runtime/cognitive_package/delta.py:131,133` | package delta `__post_init__` | `F`; caller-owned package/cognitive-delta state remains canonical. |

This census includes the two generation-digest function definitions because the repository grep matches their names. There are no unclassified production matches at this base. Implementation must rerun the AST/function census before turn-in; any new occurrence introduced by the refreshed unified base is classified before premerge rather than silently inherited.

### Target scope

| Action | Path | Responsibility |
|---|---|---|
| Create | `bilqis_mlx/learning/_retention/_atlas_candidate/identity_binding.py` | Guard installation/capability, protected-storage owners, binding issuer/registry/currentness, metrics snapshot/delta. |
| Modify | `.../_atlas_candidate/identity.py` | Canonical hash metrics only; raw-v2/legacy framing unchanged. |
| Modify | `.../_retention/atlas_candidate.py` | Private/runtime exports needed by owning production modules; do not expose a caller mint. |
| Modify | `.../_atlas_candidate/state.py` | Protect cold/fresh owner-created state and preserve/release owner references; no public auto-binding. |
| Modify | `.../_atlas_candidate/transaction.py` | Protect private transaction numerical storage and exact resolved-state ownership; #1231 currentness call stays canonical. |
| Create | `bilqis_mlx/runtime/_capability/factory/_factory_identity_evaluation.py` | Move the live FactoryRetentionEvaluation issuer/state-binding payload out of the 355-LoC owner before feature edits would cross 360. |
| Modify | `.../factory/_factory_retention_support.py` | One ordinary/motif resolved state, parent/candidate binding, package fallback. |
| Modify | `.../factory/factory_retention_owner.py` | Import delegated evaluation issuer and reuse exact carried state/bindings; net shrink below structural threshold. |
| Modify | `.../factory/_factory_parent_assessment_cache.py` | Required parent binding reuse. |
| Modify | `bilqis_mlx/learning/_retention/atlas_acceptance.py` | Live binding threading; private non-serialized capability only. |
| Modify | `.../bamf_bundle/admission.py` | One motif resolved state; acceptance/generation binding threading. |
| Modify | `.../bamf_bundle/motif/transition.py` | Seal/bind final motif state once with authoritative topology/extents supplied by owner. |
| Modify | `.../bamf_bundle/genesis/preparation.py` | Fresh protect -> bind -> run identity order; fresh validation reuse. |
| Modify | `.../bamf_bundle/genesis/preparation_authority.py` | Fresh candidate binding reuse, expected-state full oracle unchanged. |
| Modify | `.../bamf_bundle/genesis/records.py` | Optional/registry validated raw identity input to canonical generation payload. |
| Modify | `.../bamf_bundle/codec.py` | Cold genesis first-bind replaces pre-bind raw equality; non-genesis remains protected but unbound until persisted acceptance. |
| Modify | `.../bamf_bundle/publication/acceptance.py` | Cold first-bind against persisted acceptance; parent bind/reuse without changing loads. |
| Modify | `.../bamf_bundle/publication/authority.py` | Live acceptance/transition/retry binding reuse. |
| Modify | `.../bamf_bundle/publication/genesis_trust.py` | Fresh/cold genesis binding reuse. |
| Modify | `.../bamf_bundle/publication/retry.py` | Same-process/cold-bound retry reuse; no new hydration. |
| Modify | `bilqis_mlx/runtime/_batch/factory_candidate_training.py` | Per-step metric snapshot/delta fields in existing realized cost. |
| Modify | `bilqis_mlx/runtime/bamf_operator/session_support.py` | Resource observation v2 with exact identity metrics. |
| Modify | `bilqis_mlx/runtime/bamf_operator/session.py` | Visit snapshot/delta; identical resource object on accepted/rejected visits; exact evaluation state reuse. |
| Create | `bilqis_mlx/learning/_retention/tests/test_candidate_identity_binding.py` | Guard capability, geometry, currentness, fallback, raw-v2 compatibility. |
| Create | `bilqis_mlx/runtime/tests/capability/factory/retention/identity_reuse/` focused test package | C05 ordinary/motif exact-state continuity, acceptance/B13/retry hash-count proofs without pushing the parent test directory to the >=18-file trigger. |
| Modify | Existing directly affected genesis/publication/operator tests | Update schema/version expectations and add cold/fresh single-hash assertions beside their owners. |
| Create | `scripts/bamf/benchmark_candidate_identity_binding.py` | Disposable full-B01 first-bind vs repeated-require benchmark; no learner mutation. |

Delete: none. Public raw identity schemas: none. Durable acceptance/bundle bytes: none.

## Instrumentation

Add process-local counters in the identity owner:
- full raw-v2 computations;
- numerical bytes hashed;
- binding issues;
- binding reuses;
- binding require calls;
- require-path wall time.

Counters are observability only. They are monotonic process-local counters protected by one `RLock`; every increment and snapshot is atomic with respect to that lock. Production code never resets them. A private `_reset_candidate_identity_metrics_for_tests()` exists only for isolated tests. `candidate_identity_digest()` increments full-computation count, numerical bytes hashed, and full-hash wall seconds exactly once per canonical invocation; binding issue/reuse/require counters are incremented only by the binding owner.

Expose `candidate_identity_metrics_snapshot()` and `candidate_identity_metrics_delta(before)` returning integer counters plus `candidate_identity_full_hash_wall_seconds` and `candidate_identity_require_wall_seconds` floats. In `_execute_prepared_candidate`, take a snapshot immediately before the existing step work and append that step's delta to `FactoryCandidateStep.realized_cost` under additive keys `candidate_identity_full_computations`, `candidate_identity_numerical_bytes_hashed`, `candidate_identity_binding_issues`, `candidate_identity_binding_reuses`, `candidate_identity_require_calls`, `candidate_identity_full_hash_wall_seconds`, and `candidate_identity_require_wall_seconds`.

`prepare_bamf_visit` takes a second snapshot before `_execute_horizon` and computes the visit delta only after C05 has issued its evaluation/decision, so the visit total includes step-currentness hashing that still exists under #1231 plus the #1238 candidate seal/bind work. `BamfPreparedVisit` carries this immutable visit delta. `session_support._resource_observation` accepts it and emits `bilqis.bamf.c16.3-resource-observation/v2`, preserving all v1 fields and adding the seven fields above. The accepted delivery event uses that v2 resource object. The rejected journal now also records the same v2 resource object under `resource`. Thus accepted and rejected visits have one identical metrics schema and no new parallel event family.

Add a disposable full-B01 benchmark reporting first-bind versus repeated-require costs and bytes.

## Implementation phases and proof checkpoints

1. **Guard capability and storage ownership.** Add the private storage guard plus runtime capability self-test. Gate: focused tests prove supported root/alias mutation and foreign-export behavior, unprotected behavior, rollback to UNSUPPORTED, owner refcounts and no raw-v2 change.
2. **Binding owner/currentness.** Add metrics, binding dataclass/issuer/weak registry, idempotent bind, strict require and canonical fallback rules. Gate: first bind = one hash; second bind/require = zero hash; tensor substitution/storage change and all nonnumerical witness drift reject.
3. **Fresh and cold lifecycle.** Wire owner protection into CandidateState/Transaction issuance, fresh genesis bind-before-run-identity, cold genesis bind-against-run-identity, and non-genesis bind-against-persisted acceptance. Gate: fresh and cold fixtures each perform exactly one full proof per immutable state and existing bundle corruption negatives still fail.
4. **C05 exact-state continuity.** First checkpoint the active Work Stack, then move FactoryRetentionEvaluation/issuer into `_factory_identity_evaluation.py` so the 355-LoC owner shrinks before feature edits. Eliminate ordinary and motif duplicate resolution, carry exact screened state/binding in FactoryRetentionEvaluation, and reuse binding in parent-assessment/adaptive seed/evaluation evidence. Gate: original owner remains <360 LoC, new private module <240 LoC, ordinary and motif `is` continuity, bounded hash count.
5. **Acceptance/B13 hot reuse.** Thread explicit binding through mint acceptance, generation-authority payload, live require_acceptance and same-process retry without changing persisted bytes or #1237 hydration sequencing. Gate: decision -> acceptance -> publication/retry uses one raw digest, generation hashes match canonical oracle, historical acceptances remain parse-only.
6. **Census closure and telemetry.** Apply the exhaustive matrix below, add per-step and v2 accepted/rejected visit metrics, benchmark first-bind/repeated-require. Gate: matrix audit has no unclassified production occurrence, #1169 raw/legacy vectors identical, focused owner/integration tests green, no persistent human learner.

## Tests

Failing-before:
- one exact C05 preview -> acceptance/B13 path performs repeated full numerical hashing.

Storage barrier on supported runtime:
- root indexed and in-place mutation rejected;
- slice/reshape/view/stop-gradient aliases sharing storage cannot mutate it;
- NumPy/memoryview exports from roots and aliases are read-only;
- any runtime-provided `__array__` zero-copy export is also read-only for protected roots and sharing aliases;
- DLPack export from protected roots and aliases fails closed;
- pickle/getstate exports cannot mutate protected storage, and protected setstate fails closed;
- unprotected arrays preserve ordinary behavior;
- protection reference counts survive shared parent leaves and owner release.
- the disposable capability self-test restores original hooks and reports UNSUPPORTED if any required hook/alias check fails.

Unsupported runtime:
- binding issuance refuses and callers use canonical hashing with unchanged semantics.

Binding currentness:
- first bind hashes once;
- repeated require scans zero tensor bytes;
- tensor substitution rejects;
- optimizer update/new CandidateState requires a new binding;
- topology/extents drift rejects;
- policy/allocation/proof/custody drift rejects;
- cold reconstruction has no prior binding and hashes once against durable expected identity.

End-to-end:
- C05 evaluation carries the exact preview CandidateState forward;
- decision, acceptance and B13 consume the same digest/binding;
- accepted and rejected visits have bounded full-hash counts;
- package import uses canonical fallback unless explicitly owner-proven;
- #1231/#1237 behavior unchanged.

Compatibility:
- all existing #1169 raw-v2 and legacy-v1 vectors remain identical;
- generic mutable fixture still rehashes changed bytes;
- generation identity digests remain identical with and without a live binding.

## Alternatives rejected

- weakrefs/object witness only: cannot detect same-object mutation;
- tensor subclass sealing: derived MLX views shed subtype and expose writable aliases;
- pointer/hash(mx.array) witness: unchanged across mutation;
- device checksum/content scan: still rescans full state;
- full detach copy per candidate: replaces hashing with another full-state operation;
- auto-memoizing public candidate_identity_digest: unsafe for mutable states and overlaps #1231.

## Residual threat boundary

The write barrier covers supported Python MLX mutation/export surfaces used by this repository: indexed writes, in-place operators, Python buffer exports, and DLPack exports, including derived aliases sharing protected storage.

It does not claim protection against arbitrary native-memory corruption, a malicious extension retaining a raw pointer before owner protection, or deliberate exfiltration of private original C-extension methods from the custody module closure. Owner protection occurs before any supported writable alias escapes.

If fresh EGM cannot accept this runtime-integrity boundary as satisfying live acceptance #3, implementation stops and the controlling issue must be amended or decomposed before code.
