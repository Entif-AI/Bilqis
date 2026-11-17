# R19: native profile expansion and resume (design v1.0.0)

## Outcome and authority

Issue #1341 and its engineering specification restore compatible profile widening
on native BAMF. IPR-0220 remains governing; real student updates remain human-only.
The Factory owns compilation. Native runtime consumes an immutable, verified
successor; it never uses legacy Boolean-profile dispatch or legacy checkpoints.

## Interfaces and ownership

1. Factory `verify_profile_expansion(predecessor, successor)` validates the existing
   `compile_successor_profile_release` output: exact predecessor, unchanged canonical
   curriculum/source bindings/semantic catalog, unchanged answer/provider implementations,
   no removed enabled capability or narrowed dimension/answer domain, unchanged semantic
   geometry. Every changed dimension must already be declared by its provider. Existing
   release verification remains responsible for sources, prerequisites and answer labels.
2. Native `adopt_profile_release(run_dir, successor, reserve_gib)` is an explicit
   operator request for that exact immutable release, also callable by neural-inert
   disposable tests. It requires a current C07 v2 lease for the accepted run/source
   release, signed source approval with compatible rights/audit, and the exact accepted source release.
   Canonical source bindings, provider descriptors and answer modality implementations
   must remain identical; this action adds no new family/operator authority. Existing policy is `atlas-release`;
   the additional explicit successor request supplies profile-action consent. An
   autonomous A09 lease alone never triggers profile widening.
3. B13 uses a distinct profile transition and Factory-admission binding version.
   Its provenance is predecessor/successor, exact parent manifest, requested profile,
   lease/source approval, and profile-transition proof, **without fabricated A09
   handoff, proposal or selection identities**. Reuse the Factory-admission family,
   neural-inert parent/child validation, publication/CAS, event outbox and cold parsers.
   The transition schema v4/kind PROFILE_EXPANSION serializes schema, kind,
   invalidate_derived_caches=false, predecessor_factory_release_sha256,
   factory_release_sha256, profile_sha256, parent_manifest_sha256, lease_sha256,
   source_approval_sha256, and profile_transition_sha256. The Factory proof digest
   covers predecessor, successor, profile and verified execution-plan delta. The
   enclosing transition digest additionally binds parent manifest, lease and source
   approval.
   Factory binding v4 serializes run_id, generation, candidate_identity_sha256,
   parent_candidate_identity_sha256, feature_sha256, optimizer_step, predecessor_factory_release_sha256, factory_release_sha256, profile_sha256,
   parent_manifest_sha256, lease_sha256, source_approval_sha256,
   profile_transition_sha256, transition_sha256, adoption_event_sha256,
   accepted_obligation_keys (including empty), and schema_version. Its owner event
   contains event/schema/run/generation/step and the transition provenance. Missing,
   extra and malformed fields fail parsing. Issued live instances stay distinct
   from parsed historical records. Existing schemas remain readable. A profile binding carries inherited obligation
   credit; it supplies no new generated-grade proposal.
4. The runtime reads accepted predecessor/source/lease under existing operator and
   lease-publication locks, verifies current implementations and Factory compatibility,
   persists the release by content hash, derives generation N+1 with identical retained
   student, AdamW, topology/extents, semantic ABI, teacher, baseline/evaluation and
   correction state, then publishes through B13. Only active championship advice is
   cleared by the existing school-identity change rule.
5. Existing #1320/#1314 generated-grade ancestry stays authoritative. Added profile
   capabilities become release/planning-visible; no grade proposal or active membership
   is synthesized. Native `lawful_teaching_frontier` already intersects planning
   with `ensure_active_generated_grade` / `generated_grade_allowed_semantics`; test
   that exact seam after adoption. Additions require an existing frozen active grade,
   whose members must all remain enabled. Missing grade authority rejects additions.
   Existing championship/assessment paths gain no new score or title at adoption;
   release census is inventory, not proof of teaching/mastery. Active generated-grade
   custody must continue to cold-read correctly.
6. `operate_bamf(..., profile_release=...)` adopts once before its first visit under
   the operator lock. `npm run train -- --human-run --resume --factory-profile-release
   <artifact>` forwards the compiled release. Read-only dry-run verifies compatibility
   and reports the requested successor without publishing it. No option automatically
   compiles a grade or initiates an agent-owned neural run.

## Failure, retry and custody

Reject incompatible geometry, changed semantic definitions/source bindings, narrowed
scope, unknown dimensions/answers, stale parent, missing/revoked/mismatched lease or
source approval before accepted publication. B13 parent-CAS rejects races. A persisted
unaccepted release is an orphan artifact and never cold-resume authority. Exact retry
of an already accepted successor is a no-op after verifying the accepted transition
and its predecessor ancestry; retry cannot revive an old lease or replace a newer
accepted release. Preserve the configured disk reserve and ordinary B13 atomicity.
Cold resume resolves the nearest accepted release binding, never newest file or legacy
receipt, and refreshes generation-bound execution/source currentness.

## Implementation and acceptance

Extend Factory profile verification, B13 transition/binding versions, native profile
adoption and operator/CLI dispatch. Keep tests beside these owners. Red/green tests
cover historical reduced/full-B and independently named future Z fixtures; source-only
widening and extra admitted capabilities; exact student and native AdamW identity;
unchanged generated grade; release/source/currentness/cold-resume updates; invalid
geometry/narrowing/source/lease/parent; exact retry and interrupted publication.
Run focused Factory, B13, admission, generated-grade and CLI owner tests plus ABI and
required differential structural checks. No persistent owner learner is used.

## Alternatives and risks

Reusing legacy adoption loses native custody and changes grade membership. Reusing
A09 capability-only admission excludes zero-capability source widening and misstates
selection provenance. A separate profile binding version is the smallest honest
extension of the existing B13 family. Serialization compatibility and inherited grade
custody are the principal integration risks; cold-load and schema-negative tests are
required. Neural acquisition and retention remain unmeasured by this repair.

Files: Factory `profile_expansion.py` and owner tests; B13 `factory_release_adoption`,
`factory_release/admission_binding.py`, `factory_release/admission.py` plus shared
codec/publication dispatch as required; runtime `_release_adoption/native_profile.py`;
operator session and presentation CLI parser/command; adjacent tests.

### Founding C05 school compatibility

`factory_retention_owner._fixed_school_instruments` reaches the founding cohort.
Keep its immutable cohort, seed, receipt and founding run identity. After authenticating
current context/accepted parent, `factory_fixed_school._bamf_fixed_school_cohort`
resolves the founding content-addressed release from `parent.run_identity` and uses
that release for fixed-school scope/receipt readback and materialization only.
Require its unchanged canonical curriculum, source bindings, semantic catalog and
provider/answer implementations relative to the current accepted profile successor;
reject other transitions. Evaluate those old rows under the current compatible
superset context. Recheck the original accepted context at exit. Never rewrite the
founding receipt or run identity, never redraw an existing fixed school, and never
include newly exposed capabilities in the old cohort. Test post-adoption C05 readback
and native lawful-frontier selection/currentness, not only release decoding.

C05 authenticates the founding release using the accepted parent/run identity and
matching content digest, never a caller-selected artifact; missing/incompatible
founding custody fails closed. EGM focused Structural/Codebase Details review
passed after these mechanical clarifications (pinned b3a35956759bf7f024af2ff061b2e0b44b438e4c).
