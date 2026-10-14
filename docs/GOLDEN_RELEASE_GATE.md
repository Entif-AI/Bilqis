# Golden-student release gate

**Status:** Pending evidence and human approval. This document defines the conditions for a later scientific release. No currently published Bilqis tag qualifies a golden student.

A golden student is one cumulative FP32 checkpoint and its **own complete AdamW optimizer state** that scores 100% on **every currently taught capability in every current grade**, under one approved assessment inventory at the same model checkpoint and optimizer step. Historical peak scores from different steps cannot be combined to qualify it.

## Required release evidence

1. **Approved scope.** Name the active curriculum, grade IDs, full taught-capability inventory, prerequisites, independent assessment rules, and rubric version. The human operator approves this inventory before it is used for graduation.
2. **One model state.** Record the checkpoint hash, architecture, semantic/token ABI, model state, optimizer state and step, and parent/teacher lineage. Verify that model and optimizer are from the same actual training state.
3. **Complete qualification.** Bind each capability's scored questions, numerator, denominator, scoring method, and assessment provenance to that exact state. Show 100% on all current capabilities. Separate training replay from held-out evidence without exaggerating either.
4. **Reproduction.** Supply the source commit, immutable checkpoint access path, hashes, dependencies, deterministic checks where possible, and enough instructions to verify the complete record. Clearly identify unavailable or rights-restricted artifacts.
5. **Baseline handoff.** Freeze the qualifying model/optimizer. For the next training revision, use a verified full-state clone as the starting student and the frozen ancestor as the baseline for previously mastered capabilities. One common model supplies one qualified grade-scoped vote per grade, but that is not independent model diversity.
6. **Protected promotion.** Submit a reviewed PR against protected `main`, pass the required checks, verify the merged head, then use the ordinary release automation for the correct SemVer, changelog, immutable tag and public release notes. Record the exact qualifications and hashes in the canonical research registry.

Neural training runs are human-operated. The repository cleanup PR does not run a trainer, change optimizer state, promote a model, or certify a golden student. A later PR may claim a golden milestone only when each requirement has an independently inspectable receipt.
