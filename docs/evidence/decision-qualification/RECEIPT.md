# Issue #65 qualification receipt

Conclusion: **QUALITY_INADEQUATE**. The local engines are stable; no quality-qualified default is selected.

| Profile | Correct / labeled | Accuracy | Decision time ms | MLX peak bytes |
| --- | ---: | ---: | ---: | ---: |
| K1 | 11/23 | 0.478 | 3085.9 | not exposed |
| K2 | 11/23 | 0.478 | 4388.7 | not exposed |
| K3 | 11/23 | 0.478 | 4693.0 | not exposed |
| S1 | 12/23 | 0.522 | 6977.8 | 8787378192 |
| S2 | 12/23 | 0.522 | 6053.4 | 8872086526 |
| S3 | 12/23 | 0.522 | 4711.8 | 9586722438 |
| S4 | 12/23 | 0.522 | 4584.3 | 8960732680 |
| S5 | 11/23 | 0.478 | 4471.1 | 8749510152 |
| G2 | 13/23 | 0.565 | 8032.8 | 8834076266 |

Kev first state: 1964.6 ms; repeated identical state median: 77.7 ms. Twenty-four sequential three-question requests, complete SDK parsing, six standalone option permutations, and a missing-evidence request completed without crash. The missing-evidence option received probability 0.9952.

Kev retained all 25 choices under the tested permutation; SemIf changed six choices, and its 4-bit profile changed seven choices versus source precision. Both engines scored 6/6 on explicitly typed relation families. The finite-world evidence algebra and existing curriculum decisions did not meet the frozen aggregate accuracy gate. SemIf routed six diagnostic proposals locally with no labeled false confident completion; Kev calibrated routed none. These limited observations do not establish general reliability or truth authority.

The source-precision, quantized, cache/shared modes, and raw-temperature diagnostic remain separate profiles. The same pinned Qwen checkpoint supplies the generative control. ECE is omitted for insufficient sample size. Full per-item native metadata is retained losslessly in the compressed row files; artifact hashes and exact identities are in receipt.json.

The deterministic #69/#70 leaves proceeded independently. #71 requires a qualified #65 profile, #72 consumes #71, and optional #73 requires the usable navigation proof. Those dependency gates remain open. Kev-27B was not admitted or downloaded. No SYS-01 work, model-derived gold, protected mechanism, service exposure, merge, or issue closure occurred.

Known runtime difference: Kev uses MLX-LM 0.31.3; SemIf pins the upstream Qwen normalization fix. Its causal contribution to these failures was not isolated. The next qualification epoch should investigate rendering/runtime fidelity on the failed cases before changing any gate or enlarging the model.
