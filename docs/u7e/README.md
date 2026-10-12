# U7E: Keep teaching the same Bilqis

Developmental engineering, not a fresh-start attribution matrix. **The
existing U6 step-13,400 model is the parent.** Do not reset learned weights,
optimizer state, token IDs or embedding geometry. The user wants a capable
continuously developing learner, with scientific reverse-engineering later
only when useful.

The parent checkpoint (docs/evidence/u5-u6/run-01/after-U6.pt, SHA256
248a82ac92005f7b245751d6ea211d8296189de797f702349451f74383d75799)
contains actual U0-U6 learned knowledge, the typed 113-identity semantic
graph and all AdamW moments from 13,400 optimizer updates.

## Make one semantic distinction work

U6 currently scores 4/10 on its ten-event diagnostic. DERIVED_FROM records
provenance ancestry and can be transitive; SUPERSEDES explicitly replaces a
same-proposition earlier event, is not provenance ancestry, and changes which
reports are current; DEPENDS_ON indicates a proof-premise dependency.

U7E compiles same-world counterfactual pairs that change **one link only**
and flip the correct answer. Every pair is checked against both independent
finite-world oracles. First teach direct two-event distinctions; then three-
event chains, with recurring practice. The student receives the same original
typed world/question, not the answer, hidden oracle result or an English
story. This builds on already initialized semantic coordinates.

Every 32-example gradient step contains 16 new paired examples and 16 actual
earlier-skill exercises (3 U0, 1 U1, 1 U2, 1 U3, 6 U4, 2 U5, 2 U6).
The inherited model's predictions provide an additional modest memory
distillation signal only on earlier exercises. The AdamW learning rate drops
from 0.0015 to 0.0003, but its moments and step counter remain inherited.

Every 32 updates, a practical skill dashboard checks Boolean primitives,
U0/U4 compositions, U4 variations, U5/U6 variation, the original ten-event
problem and separate generated direct/chain contrast pairs. These are
development dashboards, **not** sealed science endpoints. Select and save
the strongest new descendant whose previous skills remain healthy; if no
descendant beats the parent, **keep the original U6 model**.

Run in the supported Python environment:

    python3 -m unittest tests.test_u7e -v
    python3 -m bilqis_u7e.run

Generated checkpoint artifacts remain in ignored runs/ and are not committed
into repository history. Never overwrite or mutate original U6 run files.
Future rounds must load this epoch's **best functioning descendant**, not
reinitialize or rerun from U6. Teacher-derived embeddings and knowledge
distillation can be admitted in future versioned enhancements instead of
being categorically banned by earlier attribution-only policies.
