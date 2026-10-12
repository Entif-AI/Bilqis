# U7F: Continue from the best U7E descendant, not from U6

U7E retained a functioning step-13,528 successor after the 640-step practical
teaching pass. Its new direct/chain meaning-aware counterfactuals were answered
jointly 57/184 rather than the U6 parent's 33/184. The original ten-link
diagnostic rose from 4/10 to 5/10 and Boolean primitives stayed 26/26. U0/U4
composition and U5 varied declined slightly within the stated U7E guardrails,
so the next priority is improving retention while growing the new skill.

U7F loads the EXACT U7E best checkpoint, including its full 13,528-step AdamW
optimizer state, immutable 113-identity semantic graph and source RNG. It does
not return to U6 or initialize a new model. Its lesson generator is the existing
U7E deterministic semantic teacher, with stronger old-skill rehearsal:
12 paired new-world cases plus 20 previous-world examples per gradient update,
including 5 U0 and 8 U4. Predictive distillation anchors old knowledge to the
immediately preceding *U7E best student*, not a generic pretrained model.
No new gold/answers enter student inputs. AdamW learning rate is 0.00013,
without moment or weight reset.

This is a DEVELOPMENT loop. Existing test examples may influence adaptation,
and no scientific attribution claim follows from improvements. Every 32
updates we record actual old and new skill performance. A successor is retained
only if it is useful and meets stricter old-skill conservation bounds; otherwise
we keep the U7E best checkpoint as the living parent.

Execute in the local worktree after the U7E source/parent checkpoint is present:

    python3 -m unittest tests.test_u7f -v
    python3 -m bilqis_u7f.run

Outputs under ignored runs/u7f-cumulative-memory-20261012/. No model
binaries are committed to Git or copied into public issue/PR content.
