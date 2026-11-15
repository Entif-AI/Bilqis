# Replayable Factory teacher observations

Issue #333 adds evidence to the existing visit path. It does not select an action,
change teacher credit, draw source rows, run inference or alter candidate retention.
The six-field `DeliveredTeaching` contract remains unchanged.

## Evidence chain

`runtime.teacher_observation_capture` records a pre-construction proposal after the
existing selector returns. Its immutable sidecar includes the released option and
provider, offered options/policies, effective controls, selection route, source
context, pre-action region, policy/evidence epoch and experimental partition.
The initial diagnostic source draw retains its original position before selection.

Each optimizer step records ordered content-addressed row references, including
repeated rows, role membership, source/provider identity, actual guidance and its
mentor provenance, and realized controls. The selected-option subrecord reuses
`DeliveredTeaching`; support, replay, prior rehearsal and enrichment remain visible
in the enclosing batch. Storing row bytes does not grant teaching or gold authority.

After the existing retention decision and teacher update, the observation records
raw paired scores/denominators, target and protected effects, fixed-grade/frontier
measurement states, attempted/retained steps and monotonic host wall time. The cost
boundary begins at visit entry and ends at observation finalization, including
existing source work/inference and capture overhead before finalization. It is not
GPU-only time or a prediction of cost. No additional inference is introduced.

The event initially describes a RAM outcome. Canonical checkpoint publication adds
a checkpoint/generation join through the existing outbox. `read_committed_observations`
verifies exact membership in the immutable generation before treating an observation
as durable. Journal plus current outbox read back as one logical observation, even
if the process stopped after state commit but before journal emission. Reconciliation
uses the existing idempotent outbox; the reader never repeats optimizer or teacher
work. Unpublished sidecars are staging evidence, not durable learner outcomes.

### C16.3 candidate-horizon durability

The persistent BAMF operator applies that same boundary to speculative optimizer
steps. During one candidate horizon, C16.3 keeps the exact proposal, ordered
deliveries, realized controls/costs, and content-addressed source-row objects in
memory. It does not make an independent durability promise after each speculative
step. After C05 reaches the retention decision, the complete horizon is installed as
one immutable content-addressed sidecar. Repeated identical row bytes are stored once
inside that horizon object while step records retain their original order and
multiplicity by digest reference.

Before candidate execution, the operator durably installs the sidecar directory
hierarchy once and reuses it for later horizons. That one-time directory setup is not
charged to per-horizon persistence metrics. A candidate attempt is identified by the
accepted generation and manifest, C03 visit identity, and the next authenticated
rejection-journal ordinal. A crash before accepted/rejected publication therefore
reuses the same attempt identity, while a later same-parent rejection receives the
next ordinal and cannot collapse into the earlier attempt.

The durability states are explicit:

- before finalization, a crash loses only speculative candidate evidence together
  with the speculative candidate itself; the accepted parent remains authoritative;
- a failure while installing the horizon object leaves no declared object reference;
- after the horizon object is durable but before accepted/rejected event commitment,
  the object is staging evidence only and carries no learner-outcome authority. A
  cold restart may recompute that still-speculative candidate; an orphaned staging
  object must never be credited or replayed as an observation;
- the accepted-generation outbox or authenticated rejection event publishes the
  horizon reference and remains the commit/replay authority;
- after that authority is committed, cold outbox/rejection replay reuses the exact
  referenced content-addressed object and cannot create a second logical observation
  or repeat optimizer/teacher work.

C16.3 reports the horizon object's bytes written, file fsyncs, directory fsyncs,
physical evidence objects written, logical record count, unique source-object count,
delivery-record count and persistence time. A fresh horizon therefore reports one
physical object even though that object can contain many logical step records and
deduplicated source rows; a content-addressed replay can report zero new objects.
These metrics describe evidence persistence only; they do not replace candidate
compute/resource telemetry or claim end-to-end training throughput.

## Identities and missingness

Factory envelope: `bilqis.factory.teacher-observation/v1`.
Proposal: `bilqis.factory.teacher-proposal/v1`.
Policy/evidence epoch: `bilqis.factory.teacher-evidence-epoch/v1`.
Outcome: `bilqis.factory.teacher-outcome/v1`.
Summary: `bilqis.factory.teacher-observation-summary/v1`.

`MeasurementStatus` distinguishes `MEASURED` from `NOT_MEASURED`. Target-only
rejection and empty protected measurement scopes never imply zero loss. Partial
grade evidence is not a whole-grade band. Missing costs/predictions, undefined
ratios, calibration and shadow probes retain explicit missingness.

The bounded region uses portable v1 bands and declared capability ownership;
checkpoint/run/cohort/specimen identifiers remain provenance. #320's actual
`ModelTopologySpec` record, implementation and initialization origin/seed remain
separate experimental context. Topology and policy epochs partition comparisons,
without becoming predictive region keys. Evolving teacher statistics do not mint
a new policy epoch. Changed implementation, baseline controls or source/release
bindings do. Policy configuration is evidence, not teacher truth.

For fully measured compatible records, `portable_v1` uses the unchanged #321 v1
contract and fixture. Partial records carry `NOT_MEASURED` instead of a fabricated
fully measured portable record. No estimator or learned controller is imported.

## Read-only reconstruction

```python
from bilqis_mlx.runtime.teacher_observation_replay import read_committed_observations
from bilqis_mlx.learning.teacher_observations import summarize_observations

observations = read_committed_observations(run_directory)
summary = summarize_observations(observations)
```

This is an offline forensic/reporting API. It validates the immutable generation,
proposal and ordered delivery joins. It does not repair a corrupt artifact or
reinterpret a historical pre-v2 lineage as executable. The existing operator retains
neural-update authority. Three disposable test owners cover missingness, native
instrumentation-on/off equivalence, topology/epoch partitioning and crash replay.


## Acceptance coverage and qualification use

The existing tests exercise the actual generic visit boundary with typed disposable
Factory releases. Each ordinary/autonomy attempt is committed through the canonical
checkpoint outbox, cold-read before journal delivery, replayed twice and summarized.
The enabled/disabled comparison covers retained, rejected, target-only rejected and
perfect-target skipped visits in both routes. It compares selector/reward calls,
RNG state, source draws, ordered optimizer rows, candidate decisions, complete learner
values, native AdamW state and published checkpoint identity. Only capture artifacts
and elapsed capture time may differ.

| Obligation | Proof owner |
| --- | --- |
| Ordinary and autonomy delivery, support, changed realization | `runtime/tests/test_teacher_observation_capture.py::VisitObservationTests` |
| Eight route/outcome combinations with capture on/off | `VisitObservationTests::test_enabled_disabled_orchestration_is_behaviorally_identical` |
| Ordered duplicate rows and actual delivered roles | `CaptureIdentityTests::test_realized_step_preserves_multiplicity_and_changed_composition` |
| Topology partition, stable statistics, changed policy epoch | `CaptureIdentityTests::test_topology_is_partition_and_statistics_do_not_change_policy_epoch` |
| Policy/source-context sidecar integrity | `CaptureIdentityTests::test_readback_verifies_policy_and_selection_context_objects` |
| Skip before-score with no fabricated after-score | `CaptureIdentityTests::test_skip_scores_preserve_only_valid_pre_action_measurements` |
| Zero denominators, partial grades, empty protected scope | `learning/tests/test_teacher_observations.py` |
| Unchanged portable v1 fixture | `TeacherObservationTests::test_fully_measured_fixture_bridges_to_unchanged_portable_v1` |
| Crash/cold read, repeated replay, distinct attempts on one checkpoint | `runtime/tests/test_teacher_observation_replay.py` |
| Forged publication, divergent duplicate attempt, unpublished sidecars | `ObservationReplayTests` |

Readback verifies the policy epoch and selection-source objects as well as the
proposal, delivery rows and immutable generation. Missing/corrupt objects fail
readback. Valid skip scores retain the measured pre-action score/denominator;
a post-action score and protected safety remain unmeasured.

Before #324 begins, its qualification manifest must pin the policy/evidence epoch,
resolved controls, release/source identities and seed/cost contract from this
adapter. Freeze the same baseline policy in both topology arms. Raw observations
retain topology and policy partition identities; callers must partition before
summarizing. The summary does not merge experimental arms automatically.

A verified #333 engineering receipt supplies one prerequisite to #324. It does not
close #150/#320, authorize a merge or start either neural qualification arm. The
human must still freeze the workload/budget and initiate the real runs. Learning,
calibration and shadow-controller quality remain unmeasured by these tests.
