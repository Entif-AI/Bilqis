# Frozen navigation fixture

`fixtures/navigation-v1.json` owns the ten diagnostic families requested by #69.
It is a fixture-local subset subordinate to #7/#10/#27/#44, with independently
authored finite objects. It does not extend the existing finite-world ABI or
claim complete implementation of #7. No donor prose, lexical dataset, sealed
evaluation, or model-derived gold is included.

Semantic object IDs hash the recursively resolved canonical meaning. References
must exist, be acyclic, and retain that identity. Ambiguity retains a finite set
of live alternatives; an absent object and an unsupported distinction have
different expected terminal states. The later evidence schedule is evaluation
metadata and is excluded from the initial scorer view.

The paired surfaces contain identical objects, current hints, capabilities,
resolved references, and cue text. The Bilqis navigation prototype uses ordered
factor pairs; the generic control uses named fields. Both decode to identical
information. This bounded packaging comparison cannot establish an advantage
of Ithkuil-derived morphology or learned semantic addressing.

Run `python -m unittest discover -s tests -v`. Fixture generation is explicit:
`build_corpus()` must exactly reproduce the committed artifact. Change the
version and experimental epoch before materially changing its semantics or
evaluation expectations. #53/#67/#59 and Akasha remain optional future owners.
