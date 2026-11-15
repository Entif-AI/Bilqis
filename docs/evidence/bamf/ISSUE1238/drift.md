# #1238 EGM Stage-6 drift report

## Review authority

- Reviewed design: `docs/evidence/bamf/ISSUE1238/design.md`
- Implementation base: `df58fd5b9716950472facd490541d38d54e35862`
- Initial implementation checkpoint: `c91eebb5c577c0e38bcaa564bb45efae912a472e`
- EGM authority: pinned `b3a35956759bf7f024af2ff061b2e0b44b438e4c`
- Protocol: `skills/egm_drift_report/SKILL.md`, sequential design-to-code comparison

## Current differences

No Blocker or Major drift remains after reconciliation.

| Classification | Severity | Current state |
|---|---|---|
| `DESIGN_EVOLUTION` | Info | The MLX storage barrier was split from `identity_binding.py` into sibling private `identity_guard.py` after the first implementation draft crossed the repository's 360-LoC structural intervention threshold. The semantic contract is unchanged and `design.md` now records the split. |
| `DOCUMENTATION_STALE` | Info | The refreshed unified base includes merged #1231 and reduced the pre-implementation production digest census from 81 to 80. The design census/base label and test-location table were corrected before this report. |
| `IMPLEMENTATION_BUG` | Resolved Major | Fresh/cold production owners initially required a binding even when the runtime guard capability was unsupported. All production seal/verify paths now use `bind_candidate_identity_or_fallback`: supported runtimes bind; unsupported/unbindable states prove canonically; a previously bound poisoned state still fails closed. |
| `VERIFICATION_GAP` | Resolved Major | The reviewed design required evidence for both the hosted MLX 0.31.1 line and the documented native MLX 0.32.4 line. The worktree suite exercises 0.31.1; an isolated temporary MLX 0.32.4 environment passed the capability probe plus the candidate identity/binding regression suites. |
| `VERIFICATION_GAP` | Nit | Repository-native live Factory/motif tests that require an external integration environment remain correctly skipped locally. Their exact-state contract is additionally covered by ungated operator/publication tests, direct identity assertions where fixtures are available, and hosted CI remains required before human review. |

## Reconciled implementation facts

- Canonical #1169 raw-v2 and legacy framing remain in `identity.py`; fixed vectors still pass.
- `CandidateIdentityBinding` carries exact state/optimizer/policy/allocation/proof/custody, topology/extents and numerical storage witnesses.
- The guarded runtime surface includes indexed mutation, every listed in-place slot, Python buffer/NumPy export, DLPack, pickle/state hooks, aliases, reverse/stepped/rank-zero views, and slot-drift poisoning.
- The threat boundary remains process-local custody, not hostile arbitrary native code execution.
- Ordinary and motif Factory paths carry the exact resolved candidate state into C05 evaluation; the accepted operator path reuses `evaluation.candidate_state` rather than resolving again.
- Cold accepted-state load performs one full content proof; same-process B13 publication with a live binding performs zero full candidate-identity computations and zero numerical identity bytes rehashed.
- Step and visit observations expose the seven reviewed identity counters/timers through the existing cost/resource channels, with accepted and rejected visit resources using `bilqis.bamf.c16.3-resource-observation/v2`.
- #1231 currentness callsites and #1237 hydration ordering remain separate ownership boundaries.

## Drift verdict

**PASS.** No current design/code difference requires redesign or blocks premerge. The remaining environment-gated integration skip is a verification note for hosted CI, not authority to self-merge.
