# Bilqis release and research archive

## Current source and historical releases

- [v0.1.0 source release](https://github.com/Entif-AI/Bilqis/releases/tag/v0.1.0): source/software SemVer only, at commit `4c1b54438cb61e600e732059a06183de05a1e24b`. It is **not** a neural golden-student release.
- [v0.0.0 research archive](https://github.com/Entif-AI/Bilqis/releases/tag/v0.0.0): the pre-cleanup public source tree at commit `a8d1360b75f42a637da5928863ed51c0178ddf21`. Existing tag identity and history remain unchanged.

The current checkout retains the bounded `bilqis_ref` implementation and its runnable reference tests. Older code, full experiment transcripts and generated outputs were removed from the current *tree*, not from Git history. Historical identifiers such as U7B or `logic-t0-t1` are original experiment names. They do not form a chronology to renumber.

## Find historical work

| Historical program | Exact paths at the immutable v0.0.0 tag |
| --- | --- |
| Typed micro-universes | [implementation](https://github.com/Entif-AI/Bilqis/tree/v0.0.0/bilqis_micro), [source guide](https://github.com/Entif-AI/Bilqis/tree/v0.0.0/docs/micro-universes), [evidence and checkpoints](https://github.com/Entif-AI/Bilqis/tree/v0.0.0/docs/evidence/micro-universes) |
| T0/T1 logic | [implementation](https://github.com/Entif-AI/Bilqis/tree/v0.0.0/bilqis_logic), [guide](https://github.com/Entif-AI/Bilqis/tree/v0.0.0/docs/logic-t0-t1), [evidence](https://github.com/Entif-AI/Bilqis/tree/v0.0.0/docs/evidence/logic-t0-t1) |
| U5/U6 development and U7 spiral | [development code](https://github.com/Entif-AI/Bilqis/tree/v0.0.0/bilqis_development), [U5/U6 evidence](https://github.com/Entif-AI/Bilqis/tree/v0.0.0/docs/evidence/u5-u6), [spiral evidence](https://github.com/Entif-AI/Bilqis/tree/v0.0.0/docs/evidence/spiral-u7) |
| U7B to U7F experiments | [U7B code](https://github.com/Entif-AI/Bilqis/tree/v0.0.0/bilqis_u7b), [U7C code](https://github.com/Entif-AI/Bilqis/tree/v0.0.0/bilqis_u7c), [U7D code](https://github.com/Entif-AI/Bilqis/tree/v0.0.0/bilqis_u7d), [U7E code](https://github.com/Entif-AI/Bilqis/tree/v0.0.0/bilqis_u7e), [U7F code](https://github.com/Entif-AI/Bilqis/tree/v0.0.0/bilqis_u7f), [evidence](https://github.com/Entif-AI/Bilqis/tree/v0.0.0/docs/evidence) |
| Adaptive/grade teachers and School50 | [teacher code](https://github.com/Entif-AI/Bilqis/tree/v0.0.0/bilqis_teacher), [School50 runner](https://github.com/Entif-AI/Bilqis/tree/v0.0.0/bilqis_school), [old active pointer records](https://github.com/Entif-AI/Bilqis/tree/v0.0.0/docs/development) |
| Formal Boolean, dialogue and semantic pilots | [formal code](https://github.com/Entif-AI/Bilqis/tree/v0.0.0/bilqis_formal), [guides](https://github.com/Entif-AI/Bilqis/tree/v0.0.0/docs/formal), [evidence](https://github.com/Entif-AI/Bilqis/tree/v0.0.0/docs/evidence/formal-foundations) |
| Alpha and bounded decision experiments | [alpha code](https://github.com/Entif-AI/Bilqis/tree/v0.0.0/bilqis_alpha), [alpha evidence](https://github.com/Entif-AI/Bilqis/tree/v0.0.0/docs/evidence/alpha), [decision evidence](https://github.com/Entif-AI/Bilqis/tree/v0.0.0/docs/evidence/decision-epoch-02), [qualification evidence](https://github.com/Entif-AI/Bilqis/tree/v0.0.0/docs/evidence/decision-qualification) |
| Historical studies, protocols and run logs | [research plans](https://github.com/Entif-AI/Bilqis/tree/v0.0.0/docs/research), [full documentation](https://github.com/Entif-AI/Bilqis/tree/v0.0.0/docs), [historical root log](https://github.com/Entif-AI/Bilqis/blob/v0.0.0/FEATURE_LOG.md), [original test suite](https://github.com/Entif-AI/Bilqis/tree/v0.0.0/tests) |

All other retired source paths are discoverable under the same tag with `git ls-tree`. Those include `docs/evidence/new-ithkuil-v0.1` and `docs/evidence/decision-runtime-epochs`. The release tag preserves original filenames, source Git blobs, and committed model bytes. Nothing was reserialized or renamed in the archive.

## Read or reproduce an archived experiment

For a separate working tree, without changing the current checkout:

```sh
git fetch origin tag v0.0.0
git worktree add --detach ../bilqis-v0-archive v0.0.0
```

For an exact file or an inventory of archived material:

```sh
git ls-tree -r -l v0.0.0 docs/evidence/micro-universes
git show v0.0.0:docs/evidence/micro-universes/run-01/after-U4.pt > /tmp/bilqis-after-U4.pt
```

The tag includes **only bytes committed to Git**. Ignored local `runs/` files, protected custodial models, and private research archives do not become publicly recoverable through a tag. Do not cite them as published artifacts without a separate verified retrieval path and hash.

Removing historical files from the present tree makes the checkout smaller, but ordinary full-history clones can still download their Git objects. For current source alone, use a shallow clone, for example `git clone --depth 1 https://github.com/Entif-AI/Bilqis.git`, or a source archive from the current commit. A shallow clone needs a separate fetch before accessing old tags.

## Next scientific release

The next golden-model PR must pass the [golden-release gate](GOLDEN_RELEASE_GATE.md). A version number, merged source PR, or historically best result does not by itself qualify a model.
