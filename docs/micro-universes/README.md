# Developmental micro-universes

This exploratory path extends the Boolean pilot with entities and directional relations, finite quantifiers and composition, declared rule inference, and evidence states. The controlling scope is [CONTRACT.md](CONTRACT.md), supplied for Bilqis #108. It preserves #107 and all older evidence.

The semantic catalog keeps the first 17 Boolean token IDs and appends 51 typed identities. Features include families, subtypes, signatures, roles, arity, truth signatures, inverses, complements, binding, prerequisites, composition and proof links. Each feature key independently determines signed coordinates through SHA-256. Each node sums only its own immutable features, normalizes to RMS 0.02 and casts to FP32. New incoming edges never rewrite old feature contracts. `append_catalog` preserves old IDs, descriptors and initial rows exactly; expansion to a live trained model is future work.

The kernel enforces nonempty 2–5 entity domains, typed argument roles, at most two de Bruijn binders and exact record fields. PARENT is directional and not transitive; CHILD is its inverse; LINK is symmetric. The declared rule derives GRANDPARENT from two consecutive PARENT edges. Entailment evaluates the finite least rule closure; countermodel checks the submitted world against the submitted premises and conclusion. This is bounded proof-state learning, not a general theorem prover.

Evidence names Boolean propositions but reports remain independent from closed-world fact satisfaction. Support/refutation bits distinguish TRUE, FALSE, UNKNOWN and CONFLICT; each live interpretation is evaluated separately and differing final outcomes give AMBIGUOUS. Separate evidence operators preserve Boolean meanings. The two gold paths use sets and truth tables versus adjacency matrices and operational Boolean/bit algebra. They share typed syntax traversal, not the relation closure or truth algebra.

The codec is lossless. It emits raw asserted facts, admitted rules, proposition ASTs, reports and an unreduced query. It rejects answer fields. Neural prediction calls the codec and transformer only, never a gold oracle. The student reuses `bilqis_ref.model.Block`, batching and state hashing. All initial neural weights are new; only project-owned symbolic structure initializes embeddings.

Every 32-example batch contains 12 new-focus lessons, 8 new-plus-old compositions, 4 examples from two gold-changing contrast pairs, and 8 rehearsal examples. Four rehearsal positions always carry Boolean primitives; four carry earlier worlds (Boolean compositions in U0). Gold-stratified sampling balances new-focus and composition labels. One model and one AdamW optimizer live outside the stage loop. The constant learning rate and parameter map preserve optimizer moments across stage transitions.

Use the already-installed Python 3.13/PyTorch CPU environment. From this checkout:

```sh
python -m unittest discover -s tests -v
python -m bilqis_micro.run freeze --out runs/micro-development
python -m bilqis_micro.run train --run runs/micro-development
python -m bilqis_micro.run replay --run runs/micro-development
python -m bilqis_micro.run report --run runs/micro-development
```

Freeze prints actual U1/U2 numeric inputs and gold outputs before training. Artifacts bind the graph, geometry, token map, source hashes, initial tensors, lessons and provenance. Training records every row exposure in compressed JSONL, saves optimizer-bearing stage checkpoints with parent hashes, and measures all previously introduced families after each stage. Fresh-process replay checks all predictions, lineage and exposures.

Freeze and train use exclusive creation. Reissuing train against a completed or interrupted directory fails rather than overwriting its evidence. Retain such a directory; an interrupted continuation must start from its last complete optimizer-bearing stage checkpoint under a recorded new continuation, rather than silently restarting genesis.

Committed results use `docs/evidence/micro-universes/run-01/`. Checkpoint files are deliberately versioned for portable replay. Familiar evaluations overlap training; varied/composite inputs are excluded from every training pool. No sealed evaluation, control arm, attribution claim or efficiency claim is made. See [RESULTS.md](../evidence/micro-universes/RESULTS.md) and [HANDOFF.md](HANDOFF.md).
