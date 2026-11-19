# #1454 production hydration audit

This audit covers the default native BAMF source path used by CP03 and Mission Control. It separates records that the accepted portable custody can prove from records that require another producer or a newer projection contract.

| Domain | Accepted producer evidence | Native CP03 result | Disposition |
| --- | --- | --- | --- |
| Capability | C16 accepted outbox and `how_outcome.scores/context` | `PARTIAL`; exact grade and target score when present | Provider gap repaired |
| Resources | C16 resource observation | `PARTIAL`; current generation only | Stale-marker gap repaired |
| Teacher | accepted `teacher_state` identity, epoch, and last visit policy | `PARTIAL`; identity, epoch, strategy present; counts `MISSING` | Provider gap repaired |
| School | no portable record with complete admitted grades and mastery counts | `EMPTY / COMPLETE` | Legitimately not produced by this contract |
| Atlas / Semantic | semantic ABI proves active-set and bank state, but not Atlas bundle/source identity plus eligible/held counts | `EMPTY / COMPLETE` | Legitimately not produced by this contract |
| Neural / Model | accepted manifest proves optimizer step, but not runtime duration, active-parameter, and refinement measurements | `EMPTY / COMPLETE` | Legitimately not produced by this contract |
| Memory | resource evidence is not the logical MemorySnapshot hit/miss/requalification contract | `EMPTY / COMPLETE` | Legitimately not produced by this contract |
| Salience | accepted diagnostics contain salience ordinals, but not a complete SalienceEvent action/provenance record | `EMPTY / COMPLETE` | Legitimately not produced by this contract |
| Corrections | authenticated correction frontier exists and is empty on current generations | `EMPTY / COMPLETE` | Legitimately no correction event |
| Generation / Lineage | accepted generation manifest and joint candidate identity exist; no separately named optimizer-state digest exists | `UNKNOWN` with explicit unavailable marker | Projection-contract gap, not synthesized |

Frame records are also `EMPTY / COMPLETE` on this native path. The current accepted bundle does not contain a CP02 `FrameCompileReceipt` producer record.

## Repairs

Capability hydration now reads the exact accepted target score and grade from `how_outcome` when those fields exist. Missing score or debt remains `MISSING`.

Resource current queries no longer inherit `UnavailableEnvelope` markers from older generations. Historical queries keep historical markers.

Teacher hydration now projects accepted teacher identity, teacher epoch, and the last accepted policy key as a partial `TeacherSnapshot`. The provider does not equate the fair-rotation counter with teaching attempts. Attempts, accepted count, and rejected count therefore remain `MISSING`.

The current read-only `aspirant` witness projects `A.LINK` as grade A with a measured score of 4/6. Its debt remains `MISSING`. The current Resource page is `PARTIAL` with no stale marker.

## State semantics

The provider regression test `test_native_family_hydration_matrix_distinguishes_present_absent_and_contract_gap` fixes the production-shaped matrix above. It distinguishes present partial records, accepted empty families, and the explicit Generation contract gap.

The affected renderer ring passes 189/189 tests across Corrections, Lineage, Memory, Neural, Salience, School, Atlas, Teacher, and Resources. Those tests preserve these states without fixture substitution: accepted empty remains empty, unavailable lineage remains unavailable, and partial evidence remains partial.

No synthetic record is created for a field that accepted custody cannot prove. The audit is read-only with respect to the live student.
