# Reference architecture and engineering sequence

## Student identity

The implemented student is a causal decoder-only transformer with a restricted four-answer readout. It reads the entire serialized world and query and predicts TRUE, FALSE, UNKNOWN or CONFLICT from the final real input position. The output weights are the corresponding four reserved rows of its input embedding table. It is not trained as an open-vocabulary next-token language model. Consequently, the present engineering runs demonstrate a supervised reasoning interface, not general Bilqis fluency or successful later-English acquisition.

The reference-scale config uses vocabulary 512, context 384, width 192, six layers, six attention heads, expansion factor four and learned absolute position embeddings. There are no linear biases. Each block uses pre-LayerNorm, causal scaled dot-product attention, residual connections and a squared-ReLU feed-forward. Its exact trainable parameter count is 2,828,736. The smoke config uses width 32, two layers and four heads, for exactly 53,408 parameters. The model checks width/head divisibility and rejects context overflow rather than truncating a query silently.

The ternary branch holds FP32 master weights. For each linear tensor it computes an absolute-mean scale, rounds scaled weights and clips them to -1, 0 or +1, then applies a straight-through estimator. Activation quantization uses per-token absolute maxima and a symmetric 8-bit grid. Embeddings, position embeddings, LayerNorm, gradients, optimizer state and actual arithmetic remain FP32. This is W1.58A8 forward emulation, not a packed ternary kernel. It cannot support an inference-energy or RAM-savings claim from theoretical weight bit counts. The full-precision branch uses the same module dimensions and data interface with FP32 linear operations.

The recipe is BitNet-style, not a reproduction of BitNet b1.58 2B4T. In particular, this small reference uses learned absolute positions rather than RoPE and does not implement every sub-normalization or production kernel in that source. That distinction is intentional and must travel with any result. A native-kernel port is a separately validated implementation and cost experiment, not a filename change.

## Optimization and execution

AdamW is fixed in the config: learning rate 0.0003, betas 0.9/0.95, epsilon 1e-8, weight decay 0.1, global gradient clip norm 1.0. The reference uses no learning-rate schedule or dropout. CPU threads are fixed at one and deterministic PyTorch algorithms are enabled. A different backend may not reproduce tensor bytes, even with the same seeds; semantic and tolerance-based equivalence must then be assessed separately from bitwise identity.

The default reference run is 4,096 steps, batch size 16, and 64-step tranches. That is at most 65,536 learner example exposures. The smoke run is four steps, batch size four, two-step tranches and eight-case probes. The smoke promotion threshold is deliberately not reachable by eight successes under the chosen Wilson lower-bound gate. It should remain an execution check rather than a misleading graduation ceremony.

The primary comparison is not 'a trained English model versus an untrained Bilqis model'. Both students start from scratch with the same architecture, full token allocation and initialization policy. Ordinary pretrained-language baselines belong in a separately identified transfer comparison with their upstream cost and knowledge differences acknowledged.

## Component dependency sequence

1. Freeze the semantic schema, canonical bytes and oracle agreement policy. Exhaust small formal domains and reject red fixtures.
2. Freeze token IDs and both lossless codecs. Check scope, minimal pairs and permutation symmetry before optimizing a learner.
3. Instantiate both precision branches and verify actual parameter counts. Check causal padding and nonfinite loss/gradient handling.
4. Run tiny lineages with checkpoints at genesis and each tranche. Compare uninterrupted training with interruption/resume using the same config.
5. Verify teacher eligibility, mastery, prior-skill retention and transfer gates. Show that integrity failures force a hold.
6. Add the non-authoritative local-model adapter. Freeze its identity, prompt and replay schema; reject extra truth or executable-code fields.
7. Generate development data, then transfer unseen sealed families and their generation authority to a custodian. Do not infer independence from a directory name.
8. Lock the integrated SYS comparison, seed block, stopping policy and costs. Execute only after hardware, custody, assistance and spend requirements are satisfied.
9. Interpret the system outcome before assigning individual mechanisms. Run the attribution branches selected by the preregistered outcome map.
10. Extend the world, lexical families, full language-model head or native kernels only through explicit child versions with regression fixtures.

## Why a small reference is still useful

A formal generator, exact replay and clean restart make downstream experiments cheaper to debug and easier to falsify. They do not prove that the chosen toy worlds are ecologically adequate. The experiment should eventually test longer compositions, genuinely different relational generators, correlated latent variables, unaligned target functions and later natural-language codecs. Those are scientific extensions, not missing code to be silently improvised during a sealed evaluation.
