"""New scratch-trained binary learner; token geometry extends operator prerequisites.

Its labels come from a training harness, never the encoded input. The model has
no pretrained state, no access to Kev probabilities and no formal evaluator.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict
import hashlib
import json

import torch
from torch import nn
from torch.nn import functional as F

from bilqis_ref.model import Block, ModelConfig, batch, state_hash
from .semantics import LAWS, TOKENS, TOKEN_ID, encode


@dataclass(frozen=True)
class StudentConfig:
    vocab_size: int = len(TOKENS)
    context: int = 96
    width: int = 64
    layers: int = 2
    heads: int = 4
    expansion: int = 4
    precision: str = "fp32"


class FoundationStudent(nn.Module):
    def __init__(self, cfg: StudentConfig):
        super().__init__()
        if cfg.vocab_size != len(TOKENS) or cfg.width % cfg.heads or cfg.context > 512:
            raise ValueError("FOUNDATION_MODEL_ABI")
        self.cfg = cfg
        block_cfg = ModelConfig(vocab_size=cfg.vocab_size, context=cfg.context,
                                width=cfg.width, layers=cfg.layers, heads=cfg.heads,
                                expansion=cfg.expansion, precision=cfg.precision)
        self.embedding = nn.Embedding(cfg.vocab_size, cfg.width, padding_idx=0)
        self.position = nn.Embedding(cfg.context, cfg.width)
        self.blocks = nn.ModuleList(Block(block_cfg) for _ in range(cfg.layers))
        self.norm = nn.LayerNorm(cfg.width, bias=False)
        self.register_buffer("answers", torch.tensor([TOKEN_ID["ATOM.FALSE"], TOKEN_ID["ATOM.TRUE"]]),
                             persistent=False)
        self.apply(self._init)

    @staticmethod
    def _init(mod):
        if isinstance(mod, (nn.Embedding, nn.Linear)):
            nn.init.normal_(mod.weight, 0., 0.02)

    def forward(self, ids, lengths):
        if ids.ndim != 2 or ids.size(1) > self.cfg.context or lengths.shape != (ids.size(0),):
            raise ValueError("FOUNDATION_CONTEXT")
        x = self.embedding(ids) + self.position(torch.arange(ids.size(1), device=ids.device))[None]
        for blk in self.blocks:
            x = blk(x)
        x = self.norm(x)[torch.arange(ids.size(0), device=ids.device), lengths - 1]
        return F.linear(x, self.embedding(self.answers))


def init_student(cfg=StudentConfig(), seed=211):
    torch.set_num_threads(1)
    torch.use_deterministic_algorithms(True)
    torch.manual_seed(seed)
    model = FoundationStudent(cfg)
    # First-generation, transparent semantic topology: every law starts near
    # the related operator(s), with distinct identity noise. No truth labels or
    # evaluation outputs appear in these features. Frozen before optimization.
    with torch.no_grad():
        initial = model.embedding.weight.detach().clone()
        model.embedding.weight[0].zero_()
        for law_id, law in LAWS.items():
            deps = [TOKEN_ID[v] for v in law.prerequisites]
            v = initial[deps].mean(dim=0)
            model.embedding.weight[TOKEN_ID[law_id]].copy_(
                0.55 * initial[TOKEN_ID[law_id]] + 0.45 * v)
    metadata = {"version": "topological-identity-v0.1", "seed": seed,
                "law_prerequisite_edges": {k: list(v.prerequisites) for k,v in LAWS.items()},
                "pretrained_weights": False, "oracle_answers_in_features": False,
                "token_hash": hashlib.sha256(json.dumps(TOKENS).encode()).hexdigest(),
                "state_hash": state_hash(model)}
    return model, metadata


@torch.no_grad()
def predict(model, rows):
    model.eval()
    inputs = [encode(r["input"]) for r in rows]
    if any(len(ids) > model.cfg.context for ids in inputs):
        raise ValueError("INPUT_TOO_LONG")
    logits = model(*batch(inputs)).cpu()
    probs = logits.softmax(-1)
    return [{"id": r["id"], "gold": r["gold"],
             "prediction": bool(torch.argmax(p).item()), "prob_true": float(p[1]),
             "tier": r["tier"], "family": r["family"]}
            for r, p in zip(rows, probs)]


def save_checkpoint(path, model, opt, stage, score, initializer):
    payload = {"version": "foundation-checkpoint-v0.1", "config": asdict(model.cfg),
               "model": model.state_dict(), "model_sha256": state_hash(model),
               "optimizer": opt.state_dict(), "torch_rng": torch.get_rng_state(),
               "stage": stage, "score": score, "initializer": initializer}
    with path.open("xb") as f:
        torch.save(payload, f)


def load_checkpoint(path):
    p = torch.load(path, map_location="cpu", weights_only=True)
    if p["version"] != "foundation-checkpoint-v0.1":
        raise ValueError("CHECKPOINT_VERSION")
    model = FoundationStudent(StudentConfig(**p["config"]))
    model.load_state_dict(p["model"], strict=True)
    if state_hash(model) != p["model_sha256"]:
        raise ValueError("CHECKPOINT_CORRUPT")
    return model, p
