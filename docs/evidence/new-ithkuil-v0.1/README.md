# Frozen Kev-4B New Ithkuil battery (#77)

Open [RESULTS.md](RESULTS.md) first. [FAILURES.md](FAILURES.md) includes every wrong or unstable atomic decision with the exact prompt, all choices, both native probability distributions and source support. [CAPABILITY_MAP.md](CAPABILITY_MAP.md) summarizes the capability structure.

## Reproduce the contract

`fixtures/new-ithkuil-v0.1.issue.md` preserves the exact human-authored issue body. `fixtures/new-ithkuil-v0.1.json` is its deterministic transcription. Source/anchor/dimension memberships are audit annotations; missing separate rationales remain null. No model authors linguistic test content.

```sh
python -m bilqis_ref.ithkuil_fixture --issue fixtures/new-ithkuil-v0.1.issue.md --output /path/to/fresh-fixture.json
python -m unittest discover -s tests -p test_ithkuil_battery.py -v
```

The source manifest pins the supplied 86,942-byte context packet and the three official HTML snapshots. Full donor prose and HTML remain in private persistence because redistribution rights for raw chapters are unresolved under #35. The exact supplied packet is required for inference; it is never reconstructed or rewritten by the harness.

## Execute with a stable released loopback service

The service must match [runtime-identity.json](runtime-identity.json). No server/environment installation, model download, finetuning, secondary engine or tunnel is required.

```sh
python -m bilqis_ref.ithkuil_battery run --fixture fixtures/new-ithkuil-v0.1.json --context /path/to/new-ithkuil-kev-v0.1-source-packet.md --identity docs/evidence/new-ithkuil-v0.1/runtime-identity.json --output /path/to/new-epoch/A --epoch A
python -m bilqis_ref.ithkuil_battery run --fixture fixtures/new-ithkuil-v0.1.json --context /path/to/new-ithkuil-kev-v0.1-source-packet.md --identity docs/evidence/new-ithkuil-v0.1/runtime-identity.json --output /path/to/new-epoch/B --epoch B --paired-rows /path/to/new-epoch/A/rows.jsonl
```

Outputs must be new directories. Every atomic row is flushed and fsynced. Interrupted evidence is retained; it must be reconciled before any new declared run epoch. No post-hoc prompt tuning occurs.

There are 36 canonical cells and 42 atomic decisions per epoch: F10 contains 2, 3 and 4 steps. Epoch A feeds previous selected path choices into F10. Epoch B freezes each A input state so only option presentation changes, using seed 77. Final and joint correctness remain separate. Fixture-local candidate IDs never pass through the legacy 512-row token ABI.

## Replay reports without a model

```sh
python -m bilqis_ref.ithkuil_battery report --fixture fixtures/new-ithkuil-v0.1.json --evidence docs/evidence/new-ithkuil-v0.1
python -m unittest discover -s tests -v
```

Rows retain exact questions, descriptions, orders, gold/selected identities, provider-native rounded probability vectors, prompt/state/request hashes, runtime identity, cache telemetry and latency. Reconstruct requests using the unchanged packet, recorded sequence context and candidate order. Summary/confusion metrics and Markdown reports replay deterministically from the fixture, rows and source-verification notes. Checksums bind the complete evidence set. Historical #65 evidence remains byte-identical.

This PR is stacked on #76. Integration and any use of scores as bootstrap proposals require the owning review; #77 grants no gold, student-initialization or promotion authority.
