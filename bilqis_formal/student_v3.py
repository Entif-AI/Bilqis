"""Fresh v0.3 scratch causal student with distinct teacher/student verdict IDs."""
from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
import os

import torch
from torch import nn
from torch.nn import functional as F

from bilqis_ref.model import Block, ModelConfig, batch, state_hash
from .dialogue_v3 import (TOKENS_V3, IDS, STUDENT_LABELS,
                          answer_domain, encode_prompt)


@dataclass(frozen=True)
class StudentConfig:
    vocab_size: int = len(TOKENS_V3)
    context: int = 96
    width: int = 64
    layers: int = 2
    heads: int = 4
    expansion: int = 4
    precision: str = "fp32"


class FormalStudent(nn.Module):
    def __init__(self, cfg=StudentConfig()):
        super().__init__()
        if cfg.vocab_size != len(TOKENS_V3) or cfg.context > 512 or cfg.width % cfg.heads:
            raise ValueError("BAD_STUDENT_ABI")
        self.cfg = cfg
        native = ModelConfig(vocab_size=cfg.vocab_size, context=cfg.context,
                             width=cfg.width, layers=cfg.layers, heads=cfg.heads,
                             expansion=cfg.expansion, precision=cfg.precision)
        self.embedding = nn.Embedding(cfg.vocab_size, cfg.width, padding_idx=0)
        self.position = nn.Embedding(cfg.context, cfg.width)
        self.blocks = nn.ModuleList(Block(native) for _ in range(cfg.layers))
        self.norm = nn.LayerNorm(cfg.width, bias=False)
        self.register_buffer("answer_ids", torch.tensor([IDS[x] for x in STUDENT_LABELS]),
                             persistent=False)
        self.apply(self._init)

    @staticmethod
    def _init(module):
        if isinstance(module, (nn.Embedding, nn.Linear)):
            nn.init.normal_(module.weight, mean=0., std=.02)

    def forward(self, ids, lengths):
        if ids.ndim != 2 or ids.size(1) > self.cfg.context or lengths.shape != (ids.size(0),):
            raise ValueError("INVALID_INPUT_SHAPE")
        x = self.embedding(ids) + self.position(
            torch.arange(ids.size(1), device=ids.device))[None]
        for layer in self.blocks:
            x = layer(x)
        x = self.norm(x)[torch.arange(ids.size(0), device=ids.device), lengths - 1]
        return F.linear(x, self.embedding(self.answer_ids))


def initialize(*, seed):
    torch.set_num_threads(1)
    torch.use_deterministic_algorithms(True)
    torch.manual_seed(seed)
    model = FormalStudent()
    with torch.no_grad():
        model.embedding.weight[0].zero_()
    return model, {"seed": seed, "pretrained_weights": False,
                   "token_sha256": hashlib.sha256(json.dumps(TOKENS_V3).encode()).hexdigest(),
                   "initial_sha256": state_hash(model), "topology_blend": False}


def typed_logits(raw, rows):
    if raw.shape != (len(rows), len(STUDENT_LABELS)):
        raise ValueError("INVALID_PREDICTION_DIMENSIONS")
    mask = torch.tensor(
        [[answer in answer_domain(row["input"]) for answer in STUDENT_LABELS]
         for row in rows], device=raw.device)
    return raw.masked_fill(~mask, -1e9)


def inputs_for(model, rows, histories=None, *, mode="full"):
    histories = [()] * len(rows) if histories is None else histories
    if len(rows) != len(histories):
        raise ValueError("CONTEXT_PAIRING_ERROR")
    seqs = [encode_prompt(row["input"], history, context=model.cfg.context, mode=mode)
            for row, history in zip(rows, histories)]
    return batch(seqs), seqs


@torch.no_grad()
def predict_tokens(model, rows, seqs):
    """Uses caller-supplied *complete* inputs only for frozen diagnostic probes."""
    if len(rows) != len(seqs) or any(not seq or len(seq) > model.cfg.context for seq in seqs):
        raise ValueError("INVALID_DIAGNOSTIC_INPUT")
    model.eval()
    (ids, lengths) = batch(seqs)
    probabilities = typed_logits(model(ids, lengths), rows).softmax(-1)
    return [
        {"id": r["id"], "gold": r["gold"], "prediction": STUDENT_LABELS[int(p.argmax())],
         "prob_gold": float(p[STUDENT_LABELS.index(r["gold"])]),
         "task": r["input"]["task"], "family": r["family"], "tier": r["tier"],
         "input": r["input"]}
        for r, p in zip(rows, probabilities)]


def predict(model, rows, histories=None, *, mode="full"):
    (_, _), seqs = inputs_for(model, rows, histories, mode=mode)
    return predict_tokens(model, rows, seqs)


def save_checkpoint(path, model, optimizer, stage, gate, initializer):
    snapshot = {
        "version": "bilqis.formal.checkpoint/v0.3.0", "config": asdict(model.cfg),
        "model": model.state_dict(), "optimizer": optimizer.state_dict(),
        "torch_rng": torch.get_rng_state(), "state_hash": state_hash(model),
        "stage": stage, "gate": gate, "initializer": initializer,
    }
    if path.exists():
        raise FileExistsError(str(path))
    partial = path.with_name(path.name + ".partial")
    with partial.open("xb") as f:
        torch.save(snapshot, f)
        f.flush()
        os.fsync(f.fileno())
    # A complete stage checkpoint only appears under its final name after
    # the full bytes were flushed. Abnormal termination leaves .partial.
    os.replace(partial, path)


def load_checkpoint(path):
    snapshot = torch.load(path, map_location="cpu", weights_only=True)
    if snapshot["version"] != "bilqis.formal.checkpoint/v0.3.0":
        raise ValueError("WRONG_CHECKPOINT_VERSION")
    model = FormalStudent(StudentConfig(**snapshot["config"]))
    model.load_state_dict(snapshot["model"], strict=True)
    if state_hash(model) != snapshot["state_hash"]:
        raise ValueError("CHECKPOINT_HASH_MISMATCH")
    return model, snapshot
