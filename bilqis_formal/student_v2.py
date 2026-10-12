"""Scratch 4-label student: two truth values and two feedback judgments.

Responses are *typed*: a truth question never returns CORRECT/INCORRECT, and
a judgment question never returns TRUE/FALSE. No prior model state is imported.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json

import torch
from torch import nn
from torch.nn import functional as F

from bilqis_ref.model import Block, ModelConfig, batch, state_hash
from .dialogue import ALL_LABELS, IDS, TOKENS_V2, answer_domain, encode_prompt


@dataclass(frozen=True)
class StudentConfig:
    vocab_size: int = len(TOKENS_V2)
    context: int = 96
    width: int = 64
    layers: int = 2
    heads: int = 4
    expansion: int = 4
    precision: str = "fp32"


class DialogueStudent(nn.Module):
    def __init__(self, cfg: StudentConfig):
        super().__init__()
        if cfg.vocab_size != len(TOKENS_V2) or cfg.width % cfg.heads or cfg.context > 512:
            raise ValueError("DIALOGUE_MODEL_ABI")
        self.cfg = cfg
        c = ModelConfig(vocab_size=cfg.vocab_size, context=cfg.context,
                        width=cfg.width, layers=cfg.layers, heads=cfg.heads,
                        expansion=cfg.expansion, precision=cfg.precision)
        self.embedding = nn.Embedding(cfg.vocab_size, cfg.width, padding_idx=0)
        self.position = nn.Embedding(cfg.context, cfg.width)
        self.blocks = nn.ModuleList(Block(c) for _ in range(cfg.layers))
        self.norm = nn.LayerNorm(cfg.width, bias=False)
        self.register_buffer("answers", torch.tensor([IDS[k] for k in ALL_LABELS]),
                             persistent=False)
        self.apply(self._init)

    @staticmethod
    def _init(m):
        if isinstance(m, (nn.Embedding, nn.Linear)):
            nn.init.normal_(m.weight, mean=0., std=0.02)

    def forward(self, ids, lengths):
        if ids.ndim != 2 or ids.size(1) > self.cfg.context or lengths.shape != (ids.size(0),):
            raise ValueError("STUDENT_CONTEXT")
        x = self.embedding(ids) + self.position(torch.arange(ids.size(1), device=ids.device))[None]
        for blk in self.blocks:
            x = blk(x)
        x = self.norm(x)[torch.arange(ids.size(0), device=ids.device), lengths - 1]
        return F.linear(x, self.embedding(self.answers))


def initialize(seed=211, cfg=StudentConfig()):
    torch.set_num_threads(1)
    torch.use_deterministic_algorithms(True)
    torch.manual_seed(seed)
    model = DialogueStudent(cfg)
    with torch.no_grad():
        model.embedding.weight[0].zero_()
    return model, {"seed": seed, "pretrained_weights": False,
                   "token_hash": hashlib.sha256(json.dumps(TOKENS_V2).encode()).hexdigest(),
                   "initial_state_hash": state_hash(model), "topology_blend": False}


def typed_logits(logits, rows):
    if logits.shape != (len(rows), 4):
        raise ValueError("BAD_LABEL_DIMENSION")
    allowed = torch.tensor([[label in answer_domain(r["input"]) for label in ALL_LABELS]
                            for r in rows], device=logits.device)
    return logits.masked_fill(~allowed, -1e9)


def inputs_for(model, rows, histories=None, *, history_mode="full"):
    histories = histories if histories is not None else [()] * len(rows)
    if len(rows) != len(histories):
        raise ValueError("HISTORY_LENGTH_MISMATCH")
    seqs = [encode_prompt(r["input"], history, context=model.cfg.context,
                          history_mode=history_mode)
            for r, history in zip(rows, histories)]
    return batch(seqs), sum(map(len, seqs))


@torch.no_grad()
def predict(model, rows, histories=None, *, history_mode="full"):
    model.eval()
    (ids, lengths), _ = inputs_for(model, rows, histories, history_mode=history_mode)
    probs = typed_logits(model(ids, lengths), rows).softmax(-1)
    return [dict(id=r["id"], input=r["input"], gold=r["gold"],
                 prediction=ALL_LABELS[int(torch.argmax(p))],
                 prob_gold=float(p[ALL_LABELS.index(r["gold"])]),
                 tier=r["tier"], family=r["family"], task=r["input"]["task"])
            for r, p in zip(rows, probs)]


def save_checkpoint(path, model, optimizer, stage, metrics, initialization):
    payload = {"version": "foundation-dialogue-checkpoint/v0.2",
               "config": asdict(model.cfg), "model": model.state_dict(),
               "optimizer": optimizer.state_dict(), "torch_rng": torch.get_rng_state(),
               "state_hash": state_hash(model), "stage": stage,
               "metrics": metrics, "initialization": initialization}
    with path.open("xb") as f:
        torch.save(payload, f)


def load_checkpoint(path):
    saved = torch.load(path, map_location="cpu", weights_only=True)
    if saved["version"] != "foundation-dialogue-checkpoint/v0.2":
        raise ValueError("WRONG_DIALOGUE_CHECKPOINT_VERSION")
    model = DialogueStudent(StudentConfig(**saved["config"]))
    model.load_state_dict(saved["model"], strict=True)
    if state_hash(model) != saved["state_hash"]:
        raise ValueError("DIALOGUE_CHECKPOINT_CORRUPT")
    return model, saved
