# Issue #1317 — Local retention cadence design and proof map

## Problem

Ordinary C05 candidate retention inherited the whole fixed-school evaluation
shape. That made visit-time retention work scale with admitted-school size even
when one candidate could only affect a small dependency neighborhood.

Measurement coverage is not protection authority. Raw SKOS adjacency is not
Factory dependency authority. Filtering a whole-school cohort after loading it
is still a whole-school operation.

## Selected structure

RetentionProtectionPlan is compiled once per accepted-generation execution
cache. Its identity binds:

- accepted generation and accepted manifest;
- executable Factory release and execution-plan digest;
- complete compiled GradeExecution definitions;
- retained baseline/correction/evaluation evidence;
- C05 policy epoch, rubric and source identities.

The compiler derives only admitted Factory relations:

- prerequisite;
- constituent;
- direct dependent construction;
- shared constituent.

For each target it stores a directly indexed RetentionTargetPlan. The target
entry contains the exact affected relation edges, currently protected related
capabilities, exact evaluated capability/group list and local comparison/evidence
scope identities. plan.for_target(capability_id) is a direct map lookup.

## Ordinary visit path

Production prepare_bamf_visit() binds the accepted-generation plan before
teacher selection. After a target is selected, it binds that target's immutable
local source rows before candidate training. Ordinary retention then requires
both precomputed artifacts. It cannot lazily compile the plan, redraw source
rows, materialize c05-fixed-school, or enumerate the execution plan.

The accepted SourceExecutionContext owns one prevalidated execution index.
Local C05 instrument compile/bind operations reuse that accepted validation;
generic callers retain full release/catalog verification.

The local evaluator runs:

target + plan-selected protected related capabilities

Direct target and protected-capability vetoes remain active. Grade aggregate and
whole-school aggregate predicates are broad-certification predicates and do not
run on the ordinary local path.

## Baseline preservation

Protection authority and exact comparator history remain separate.

Existing retained evidence can keep a related capability protected after the
cadence migration when release/policy/source/correction/evaluation authority is
still current. Comparator-dependent target predicates, however, use
BaselineComparisonEpoch against the exact local target cases. A different
comparison scope therefore remains UNMEASURED until the local baseline is
lawfully established, preserving the #1316 first-measurement rule.

## Broad certification

The existing fixed-school evaluator remains available only through an explicit
BroadCertificationTrigger:

- GRADE_BOUNDARY;
- MATERIAL_PROTECTION_CHANGE;
- CONFIGURED_INTERVAL;
- DECLARED_BROAD_BLAST_RADIUS;
- COLD_REVIEW.

Package import currently owns DECLARED_BROAD_BLAST_RADIUS. Grade-boundary
advancement remains the separate #1334 owner.

## Observable evidence

The live C05 decision receipt records:

- exact evaluated_capability_ids;
- retention_protection_plan_sha256 for ordinary local checks; or
- broad_certification_trigger for broad checks.

Operator telemetry records the evaluated capability count, plan digest and broad
trigger at the same boundary measured by retention_wall_seconds.

## Acceptance witnesses

The targeted suite proves:

- adding 1,000 unrelated semantics does not change a target's evaluated set;
- adding one real Factory dependency adds exactly one affected/protected member;
- a raw SKOS neighbor cannot enter the local scope;
- protection-plan compilation performs no network call;
- Grade Z uses the identical plan/index contract;
- a cold record round-trip preserves the plan digest and target scope;
- local C05 reports exact evaluated IDs and still vetoes protected regression;
- local C05 does not apply whole-grade/whole-school aggregate vetoes;
- ordinary candidate retention cannot materialize the broad fixed-school artifact;
- package import names an explicit broad-certification trigger;
- the operator prebinds the plan and target source evidence before candidate work.

No persistent learner or optimizer mutation is required by these witnesses.
