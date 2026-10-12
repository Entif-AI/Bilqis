# Isolated Kev MLX-LM diagnostic

The unchanged 25-item fixture still yields **11/23** labeled decisions correct.
The predeclared runtime intervention changes only MLX-LM from 0.31.3 to the
SemIf source pin `a63e24c389382619eb6d9af656e3b46024be217a` (0.32.0).
All other installed distribution versions and Python match the released Kev
environment. Source, Kev checkpoint, BF16, calibrated temperature, labels and
qualification thresholds are unchanged.

All 25 probability distributions changed, while no selected candidate changed.
The fixed-seed candidate permutation changes no choice. There are zero local
proposals, zero confident wrong decisions, and zero labeled false local
completions. Accuracy 0.478 remains below the frozen 0.8 gate. ECE is omitted
because only 23 cases have deterministic labels. **QUALITY_INADEQUATE** remains
the qualification disposition; this diagnostic does not select a new default.

The experimental runtime passed SDK Choice/Noul/Score parsing and six standalone
permutations. Full native responses and per-item rows remain available. The first
attempt failed in the recorder's JSON serialization of the SDK HTTP wrapper;
that interrupted evidence is retained host-locally. It does not establish a model
or runtime failure. The fresh retry serialized the SDK's typed schema and native
response explicitly.

This override exceeds Kev's released `<0.32` dependency contract. A library
version comparison cannot isolate one normalization patch within that version.
The released K1/S1 qualification receipt remains byte-identical. The experimental
loopback listener was stopped; the original calibrated service remains intact.
#71–#73 remain dependency-gated and Kev-27B remains unattempted.

`receipt.json` binds identities, the frozen gate, unchanged baseline hash and
artifact hashes. `comparison.json` records every case; compressed row files
preserve complete native metadata. No weights, cache files or machine paths are
published. No SYS-01 or model-derived truth authority is granted.
