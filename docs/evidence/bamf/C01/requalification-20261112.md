# C01 dependency requalification — 12 November 2026

Provenance clarification (13 November, #1063, PM-2026-11-07-002): the
legacy-trainer authority check named in this historical receipt refers to
`/Users/emilie/Code/.worktrees/bilqis-mlx/337-replay-349-20261026/runs/microspenics-349-replay`.
This pointer correction does not constitute a fresh live audit or change the
qualification evidence below.

Issue: #347 (`BAMF-0.2 C01`)

Reviewed-unified base: `c672c62113108695a2a60cd0eb0d7f19d085f838`

This is a bounded requalification receipt. It does **not** declare C01 complete and
does not replace the 1 November dependency-evidence review. The controlling rule
from that review remains: do not guess dependency edges or equate implementation
closure with complete dependency normalization.

## Live mirror repair

The live A13 owner body contains the 7 November post-decomposition remediation
amendment for #906. Reviewed unified still carried the older A13 mirror. The
canonical owner-mirror reconciler was run only for A13 and preserved the existing
A13.1-A13.3 child census:

```text
python3 -B scripts/bamf/reconcile_owner_mirrors.py --keys A13
python3 -B scripts/bamf/reconcile_owner_mirrors.py --keys A13 --apply \
  --preserve .local/c01-requal-owner-mirrors
```

Dry-run and apply both reported old owner SHA-256
`49c6a1d9d7daa30dc19f1ee9494c56931ab73f7715fd452a4eb54c2491db706f`
and new SHA-256
`fb2464fbce8d5cc93c357ca926d35b24f403c1c5ceb8a762b1e46ae488c235d0`.
The three canonical A13 child packets retain their existing identities and now bind
the new parent-source digest. No new BAMF leaf is added for #906 because the live
amendment explicitly classifies it as `new_acceptance=false` remediation.

## Dependency requalification result

After the live mirror repair:

```text
python3 -B scripts/check_bamf_workstack.py --live \
  docs/tasks/bamf-0.2/workstack.json
```

reports:

```text
child_count=172
registry_integrity=valid
live_owner_mirrors=valid (43 checked)
issues=[]
dependency_resolution=held
order=[]
held_keys=A03.4,A05.4,A05.5,A08.1b.2,A08.1b.5,B02.4,B11.1a,B13.6
```

The eight holds remain intentionally nonzero. All eight implementation issues are
now closed, but their C01 evidence records preserve dependency-meaning questions
that closure alone does not answer:

- `A03.4 #578` — the body says it consumes accepted A03/A04 schema serialization,
  while the pinned graph has only A01 and the accepted A03/A04 serialization
  receipts remain unnamed in the C01 evidence packet.
- `A05.4 #575` — A03/A04/A13 are named, but the required current A05 compiler
  receipt is still not identified at dependency-evidence granularity.
- `A05.5 #594` — accepted implementation PR #618 is pinned, but neither the issue
  body nor its repository specification declares a complete direct-prerequisite
  list. `deps=[]` therefore remains an unknown-list hold, not a claim of zero
  prerequisites.
- `A08.1b.2 #554` — the issue body names A08.1a/A07.1/A07.2/A13, while the pinned
  repository specification additionally requires an A13.1 receipt. That extra
  dependency/receipt has not been normalized into the C01 graph.
- `A08.1b.5 #557` — the body names A08.1b.1 through A08.1b.4, while the pinned
  specification also requires the A08.1a frozen census and source-owner
  obligations. Those obligations are not represented by the four-edge range.
- `B02.4 #576` — B01 and A05.4 are named, but the required actual A05 compiled
  child-handle receipt remains unidentified in the C01 evidence packet.
- `B11.1a #586` — B01/B04 and accepted A05.5 PR #618 are preserved, but the exact
  B05 numerical-operation/source-cycle obligations are not fully normalized into
  a complete direct dependency contract.
- `B13.6 #904` — B13.1/B13.4 are explicit direct prerequisites; the hold requires
  the final accepted dependency receipts to be named and pinned rather than
  inferring acceptance from closed issue state.

No hold was promoted merely because its implementation issue is closed.

## Release boundary

The 10 November C01 amendment remains intact: C08.4 #558 and C14.4 #559 are
BAMF-0.3 work and are excluded from the BAMF-0.2 canonical child registry,
required-leaf denominator, parent-closeout graph and live-issue-tree
reconciliation. This requalification does not re-register either issue.

## Inherited live-audit debt

Two stricter/read-only census tools remain non-green, but the same failures
reproduce on an untouched detached checkout of the exact reviewed-unified base
`c672c621...`:

```text
python3 -B scripts/bamf/audit_child_registry.py --strict
python3 -B scripts/bamf/workstack/bamf02_verify_live_issue_tree.py
```

The raw child audit sees later follow-up/mitigation issues outside the current
172-entry canonical release-scoped registry, including duplicate-key historical
issues. The older live-issue-tree checker also disagrees with already-reviewed
supplemental-child relationships and reports pre-existing C02 cycles. These are
not introduced by this requalification. On the candidate, the A13 live-body
mismatch from the base checker is removed; the other baseline failures remain.
They are recorded here rather than silently relabeled as C01 acceptance success.

## Verification

Bounded checks used for this requalification:

```text
python3 -B scripts/check_bamf_workstack.py \
  docs/tasks/bamf-0.2/workstack.json
python3 -B scripts/check_bamf_workstack.py --live \
  docs/tasks/bamf-0.2/workstack.json
python3 -B scripts/verify_bamf_0_2_contracts.py
git diff --check
```

The focused registry/contract/reconciler unit selection passes **30/30**. A
base-pinned `npm run verify:leaf` passes structure/governance, legacy-trainer and
flow-control gates plus its **15/15** differential tests. The contract verifier
remains green for checked-in identity/fingerprint integrity; the workstack
validator remains deliberately held with the eight exact keys above.
No learner, optimizer, checkpoint, source-admission, Factory release, graph state,
or persistent BAMF runtime was started or mutated.

## Disposition

`C01_REQUALIFIED_HELD`.

The A13 live-owner mirror is repaired. C01 remains open until the eight dependency
evidence questions are resolved against exact owning evidence. Because C01 is an
integration/normalization hold rather than a reason to idle an otherwise
independent worker, the Parallel Workstreams plan may continue WS2 with bounded
C10.1/#519 preparation while #380 owns its separate final-turn-in gate.
