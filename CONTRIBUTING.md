# Contributing

Bilqis is an experimental research repository. Contributions are welcome, especially those that make the hypotheses easier to falsify, the implementation easier to reproduce, or the comparison conditions more credible.

## Before changing behavior

1. Identify the issue or experimental claim the change affects.
2. Preserve the separation between latent semantic worlds, representation codecs, the truth oracle, the developmental teacher, and the student.
3. Do not give an LLM or teacher authority over gold labels, sealed evaluation, or promotion criteria.
4. Add or update deterministic fixtures for semantic, codec, oracle, and checkpoint changes.
5. Treat changes to experimental endpoints, thresholds, budgets, seeds, or sealed-family handling as research-plan changes, not refactors.

## Tests

Run:

```sh
python -m unittest discover -s tests -v
```

A behavioral change should include a regression test. A semantic-ABI change should also explain compatibility with historical examples or explicitly version the ABI.

## Generated artifacts

Do not commit local run directories, checkpoints, sealed private gold material, or model binaries. The root `.gitignore` excludes the common cases.

## Claims

Keep engineering evidence, scientific results, and hypotheses distinct. Passing the reference suite means the bounded implementation behaved as tested. It does not establish a Bilqis learning advantage.
