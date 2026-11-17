# R10: authenticated HOW outcome learning

Issue #1332 and its engineering-spec comment 6913540609 own this bounded repair.
Baseline: unified 1f077f2aaaf2c201b0105d510c7fa8463b399ccd.
Authority: ADR-051/080/101/102/104/107/115; IPR-0220.

## Observation and ownership

Native candidate evidence records policy, delivery and C05 decision but never
updates contextual or inherited HOW rewards. Rejection replay updates WHAT
recency and candidate horizon only. Keep those projections unchanged.

## Implementation contract

1. C05 Decision carries immutable observational score tuples (capability,
   before, after, total) and protected capability IDs from the actual paired
   assessments it already computes. Foundation uses fixed-school pairs; strict
   uses target plus fixed protected pairs. This adds no inference, changes no
   retention predicate, serialized decision or evidence digest, and grants no
   authority to callers. Factory evaluation issuance remains the authority.
2. After lawful WHAT ranking has selected an offer, replay current-generation
   authenticated rejection outcomes into the selected teacher projection BEFORE
   select_visit_policy. Reuse current_rejections receipt authentication and order;
   load exact receipt objects by digest. Old receipts with no HOW observation
   remain recency evidence only. Never invent historical credit. This fold is
   over an isolated teacher copy, not the accepted parent or student.
3. Bind a HOW selection context to the issued PriorityVisitResult metadata:
   phase, curriculum scope, diagnostics, explicit lesson grade, generated grade
   definition digest, source binding, release, parent student and policy epoch.
   CandidateEvidenceCapture stores this context and the exact selected C03
   teacher projection, including any newborn policy. Existing selected-policy
   keys/features and realized_action describe delivery, horizon and controls.
4. After C05 issuance and candidate evidence finalization, build one content-
   addressed TeacherOutcomeObservation from the evidence proposal/delivery,
   decision and measured C05 scores. It binds attempt ID (generation, parent
   manifest, visit, global attempt ordinal), grade/source/rubric/release,
   selected/effective/realized policy, parent learner, attempted/retained steps,
   C05 reason and evidence digest. Fail closed on changed identities.
5. Applying an outcome starts with the authenticated selected teacher snapshot,
   invokes existing observe_context, selection_credit, historical policy observe,
   and plasticity visit feedback once. Translate measured count deltas to
   fractions; no-target-gain/rejection penalties remain existing policy rules.
   Keep outcome IDs/digests and selection credit inside current_teacher state.
   Identical applied IDs are no-ops; changed payload for an ID fails closed.
   Require each new snapshot to extend the fold's already-applied outcome set
   and match parent student/teacher lineage, preventing dropped or reordered credit.
6. On acceptance, update only the issued visit's projection with credited teacher
   before derive_accepted_teacher_successor advances custody. Bind the observation
   into accepted delivery event and the successor teacher state atomically.
   On rejection, store it in the existing B13 authenticated rejection receipt;
   no accepted pointer, seed, student or AdamW change. The next selection folds
   it, including after cold resume. A later accepted checkpoint carries the fold;
   only its new generation's rejection tail is replayed. Unpublished observations
   alone cannot credit. Failed publication cannot commit credit.

## Compatibility and failure semantics

Historical candidate evidence and old rejection events stay readable. New native
operator candidates require context and C05 scores; missing inputs fail before
publication. The passive legacy ObservationCapture API remains unchanged.
Use existing typed SCHOOL errors for identity/content/lineage failures. No new
policy bank, reward coefficients, source gold, membership, prerequisite, admission,
retention authority or actual student neural updates are introduced.

## Proof

Red/green focused tests: retained and rejected exact-once credit; duplicate replay;
changed-payload failure; cold rejection fold then acceptance, followed by resume;
no-gain debt, rejection pressure and four-attempt same-checkpoint cooldown;
retained policy versus newborn selection; generated Grade Z with opaque capability
IDs; identical WHAT ranking despite changed HOW evidence; selected/newborn policy
survives rejection; missing/tampered identity/source/decision fails closed; parent
student/AdamW/pointer unchanged on rejection. Reuse C05 tests to show unchanged
retention results and no additional solver calls. Then owner tests and scoped
static/ABI gates, design drift, current-unified sync, ready PR and hosted checks.

## Exact interfaces and phases (review amendment)

Phase 1 (cheap C05 regression): add `Decision.outcome_scores`, default empty tuple,
with entries `(capability_id: str, before: int, after: int, total: int)`; retain
existing serialized `CandidateRetentionDecision`. Foundation `_evaluate_fixed_school`
attaches its actual measured pairs with `dataclasses.replace`; strict `retain_candidate`
attaches target plus fixed-school pairs. Counts require `total > 0` and
`0 <= before, after <= total`; duplicate capability IDs fail. C05 score capture
is observational. It never authorizes a candidate or schedules extra inference.
Files: runtime/_capability/{capability_retention,capability_retention_foundation,
capability_retention_strict}.py. Focused C05 owner fixtures must return identical
reason, evidence/policy digests and solver-call count before/after.

Phase 2 (red/green outcome unit tests): create runtime/_teacher/outcomes/ package
with `observations.py` and `replay.py`. Public internal functions are
`selection_context(release, program, grade, phase, scope, diagnostics) -> dict`,
`build_outcome(run_dir, selection, evaluation, decision, candidate_evidence) -> dict`,
`apply_outcome(teacher, observation) -> dict`, and
`replay_rejected_outcomes(run_dir, parent, cache, teacher) -> dict`.
All functions copy inputs; no persisted accepted state is mutated.

Wire schema `bilqis.bamf.teacher-outcome/v1` is a JSON object with:
`attempt_id`, `proposal_id`, `candidate_evidence` (existing sidecar reference),
`teacher_visit` (existing typed identity record), `context`, `selected_teacher`,
`selected_policy`, `effective_policy_key`, `realized_action`, `attempted_steps`,
`retained_steps`, `decision` (C05 serialized record), `scores` (arrays of the
C05 tuples), and `protected_capabilities` (string array). `outcome_sha256` is the
existing state._fingerprint of all preceding fields, excluding itself.
The enclosing receipt/outbox authenticates this complete content; a standalone
object is staging evidence only. Attempt uniqueness uses the existing evidence
attempt ID, including the global rejection journal ordinal. Context has strings
`grade`, `phase`, `curriculum_scope`, digests `grade_definition_sha256`,
`source_binding_sha256`, `factory_release_sha256`, `rubric_sha256`, plus dict
`diagnostics`; grade identity is the canonical admitted ScheduleGrade projection
and release digest, not a name parsed from capability. Teacher epoch and parent
learner come from teacher_visit. Decision carries policy/evidence epochs.

The teacher's `how_outcomes` is `{parent_manifest_sha256, head, applied}`.
`applied` maps attempt IDs to outcome digests; `head` is the most recently
applied digest or null. A new parent manifest starts an empty map. The selected
snapshot's prior ledger must equal the fold's ledger (including ordered head),
not merely contain its set. A duplicate matching ID/digest returns the unchanged
teacher; any mismatched digest fails. This detects reorder/fork/drop of credit.
Validate selected teacher policy equals the proposal policy, parsed visit matches
proposal visit/capability/parent, selected effective key matches canonical policy,
source/release/decision agree with authenticated enclosing evidence, and horizon
cost equals delivered step count. Require issued evaluation and PriorityVisitResult
at live build. Require receipt authentication at rejection replay. No public
API accepts an unauthenticated disk path as a teacher outcome authority.

`apply_outcome` adapter creates the existing causal decision dict:
`version=learning_experiment.VERSION`, `active_capability=visit.capability_id`,
`phase=context.phase`, `decision=C05.decision`, `reason=C05.reason`,
`deltas={cap:(after-before)/total}`, `protected_capabilities` from C05 baseline
coverage (or measured non-targets when no baseline contract),
`paired_scores_sha256=C05.evidence_sha256`,
`source_cohort_sha256=context.rubric_sha256`.
`local_gain` is the measured target fraction delta; a missing target is an error,
not zero. Invoke observe_context with exact scope, diagnostics, realized action,
parent student SHA, and explicit lesson grade; then selection_credit(local_gain,
causal_decision, contextual_result); then historical_teacher_policy.observe with
context.grade and selected key; then plasticity_escape.record_school_visit with
retained=C05.decision==PROVISIONAL. Existing reward coefficients stay untouched.
Add optional lesson_grade to existing contextual_pick/observe_context, preserving
legacy name-derived default; native selection and feedback always supply the
explicit admitted grade. vNext reads the same restored causal_experiment records.

Phase 3 (runtime integration): modify accepted_priority_visit.py to replay only
AFTER WHAT requalification/ranking and before HOW selection and to bind context
into its existing authenticated metadata. Modify bamf_operator/evidence.py to
include context and selected teacher snapshot in new proposals when the issued
native selection supplies them (legacy fixture/read compatibility remains).
Modify bamf_operator/_session_execution.py after C05 issuance to build outcome,
apply credit to a new BoundTeacherVisit projection via existing _selection_projection
and _issue_bound_visit, and include the outcome in accepted delivery events.
Modify session_support.BamfPreparedVisit with optional outcome field and session.py
to place the same outcome in rejection evidence. Existing B13 record_bamf_rejection
and accept_and_publish own commit; no new journal or state pointer is created.

Rejected recovery: evidence sidecar write alone grants no credit; B13 rejection
authority+receipt object must exist AND exact event be present in verified journal.
Reuse current_rejections to validate order and membership, then load its receipt
objects. Duplicated exact delivery credits once. A crash before journal append has
no committed outcome; a crash after append reconstructs from the current generation.
Accepted recovery: RAM successor has credit provisionally; accept_and_publish
commits the generation containing BOTH event and credited teacher state at its
existing pointer transition. A failed pre-pointer publication leaves old teacher
and current-generation rejected tail authoritative. Post-pointer/pre-delivery crash
loads credited teacher from bundle; outbox emission cannot credit again. Fault
injection tests cover both boundaries and duplicate journal/outbox delivery.

Phase 4: focused selection/feedback/custody/operator suites, static gates, drift
and turn-in. No unrelated cleanup. Every added file stays under structural limits.

Adapter clarification: `evaluation.decision` is C05 `Decision`, whose status is
ELIGIBLE/REJECT. The operator's existing `issue_factory_retention_decision`
returns `CandidateRetentionDecision`, mapping ELIGIBLE to PROVISIONAL. The
observation's `decision` is the latter's exact `to_record()`, not the raw C05
Decision. Build verifies evaluation status agrees with this issued decision;
application and plasticity use that serialized PROVISIONAL/REJECT consistently.
Explicit lesson grade must reach `_stagnation_feedback` as well as
`observe_context` and `_pick_context`; the legacy default is used only when the
optional grade is absent. Test opaque capability ID feedback equals a named ID
in the same admitted grade with the same inherited grade statistics.

## Accepted-epoch evidence preservation amendment

Trace of `bind_next_teacher_epoch` shows that it intentionally resets contextual
counters for a fresh learner region. Native accepted visits use the same causal
student lineage, so resetting those counters would erase newly restored retained
policy evidence before the next choice. After the ordinary C03 successor derivation,
`issuance.carry_credit_to_successor(credited_visit, successor)` preserves the
credited teacher's `causal_experiment` and `grade_stats` in that successor's current
teacher, retaining the newly bound `student_policy_epoch` from the successor.
Thus checkpoint-local retirement resets normally while shared capability debt,
contextual retained/rejected outcomes, ecology and vNext evidence survive. Preserve
the successor's other lineage/region fields and immutable prior teacher. This is
called only for the native operator's credited accepted visit before B13 publication;
bootstrap, imports, semantic release transitions and unrelated lineage callers keep
their existing fresh-region policy. Regression must verify one retained contextual
record survives accepted checkpoint cold read and same-checkpoint counts are fresh.

Carry is permitted only while bank identity, plasticity policy identity and source
identity match the accepted parent. When these compatibility identities change,
keep the ordinary fresh-region reset; the credited teacher remains immutable prior
evidence and the committed outcome remains recorded. Do not activate incompatible
context evidence. Tests cover that transition separately. Strengthen proof with
ADR-102 two-checkpoint rejection/cooldown/expiry/retained-clearing sequence and
ADR-115 post-carry selector/population behavior under newborn pressure.

New HOW dictionaries are live-issued weak-referenceable dict subclasses, registered
by object identity plus content digest by build_outcome. B13's existing rejection
validator requires that live issuance before accepting a non-null HOW observation,
and checks its visit/decision/evidence bindings. No registry survives cold resume:
B13's authenticated committed receipt is then the authority. Registry entries are
weak and released with the prepared candidate; no unbounded in-process snapshot
retention. Historical rejections without HOW remain valid.

Scope audit: the changed owners all map to #1332's existing clauses: paired C05
scores supply authenticated outcome measurements; issued selection/evidence and
B13 bind publication; replay and accepted custody enforce exactly-once credit;
explicit grade mapping supports generated future grades; existing contextual,
bandit, breeding and vNext consumers use restored evidence. No additional feature,
source admission, retention predicate or training authorization is added.

Independent implementation review correction: native selection's canonical
`diagnostic_contexts[metadata.diagnostic_context_key]` is serialized in context
`diagnostics`, alongside `diagnostic_context_key`. Feedback's new optional
`observe_context(diagnostic_context_key=...)` requires that exact payload already
exist in the selected teacher and recomputes its existing key hash before credit.
This preserves verified salience features without attempting to JSON-serialize
live authority objects, and avoids recomputing a different diagnostic key. Legacy
callers without the key retain their current diagnostic normalization behavior.
