"""Reference transformer blocks with an alpha-local semantic embedding/readout.

The prediction path imports validation and the lossless codec, never an evaluator.
"""
from __future__ import annotations

from dataclasses import asdict
from pathlib import Path

import torch
from torch import nn
from torch.nn import functional as F

from bilqis_ref.model import Block, ModelConfig, batch, state_hash
from .codec import encode, token_manifest
from .features import compile_embeddings, tensor_hash
from .semantics import LABELS, sid

VERSION = "alpha-student-0.1.0"


class AlphaStudent(nn.Module):
    def __init__(self, config: ModelConfig):
        super().__init__()
        if (config.vocab_size != len(token_manifest()["tokens"]) or config.width % config.heads
                or config.layers < 1 or config.precision not in ("fp32", "ternary")):
            raise ValueError("alpha model architecture/ABI")
        self.config = config
        self.embedding = nn.Embedding(config.vocab_size, config.width, padding_idx=0)
        self.position = nn.Embedding(config.context, config.width)
        self.blocks = nn.ModuleList(Block(config) for _ in range(config.layers))
        self.norm = nn.LayerNorm(config.width, bias=False)
        answers = [token_manifest()["tokens"].index(sid(s.lower())) for s in LABELS]
        self.register_buffer("answer_ids", torch.tensor(answers, dtype=torch.long), persistent=False)
        self.apply(self._initialize)

    @staticmethod
    def _initialize(module):
        if isinstance(module, (nn.Linear, nn.Embedding)):
            nn.init.normal_(module.weight, mean=0, std=.02)

    def forward(self, ids, lengths):
        if (ids.ndim != 2 or ids.shape[1] > self.config.context or lengths.shape != (ids.shape[0],)
                or bool((lengths < 1).any()) or bool((lengths > ids.shape[1]).any())):
            raise ValueError("alpha context/lengths")
        x = self.embedding(ids) + self.position(torch.arange(ids.shape[1], device=ids.device))[None]
        for block in self.blocks:
            x = block(x)
        h = self.norm(x)[torch.arange(ids.shape[0], device=ids.device), lengths - 1]
        return F.linear(h, self.embedding(self.answer_ids))


def deterministic_runtime(seed=102):
    torch.set_num_threads(1)
    torch.use_deterministic_algorithms(True)
    torch.manual_seed(seed)


def initialize(config: ModelConfig, seed=102, profile="semantic_aligned"):
    deterministic_runtime(seed)
    model = AlphaStudent(config)
    table, manifest = compile_embeddings(config.width, profile, seed)
    with torch.no_grad():
        model.embedding.weight.copy_(table)
    if tensor_hash(model.embedding.weight) != manifest["tensor_sha256"]:
        raise ValueError("pre-step embedding distortion")
    return model, manifest


@torch.no_grad()
def predict(model: AlphaStudent, semantics: list[dict]) -> list[dict]:
    model.eval()
    inputs, lengths = batch([encode(s) for s in semantics])
    logits = model(inputs, lengths).cpu()
    if not bool(torch.isfinite(logits).all()):
        raise ValueError("nonfinite neural logits")
    probabilities = logits.softmax(-1)
    return [{"prediction": LABELS[int(p.argmax())], "logits": z.tolist(),
             "probabilities": p.tolist(), "provenance": "live neural inference"}
            for z, p in zip(logits, probabilities)]


def save_checkpoint(path: Path, model, initializer, metadata, *, optimizer=None):
    payload = {"model_version": VERSION, "config": asdict(model.config),
               "state_dict": model.state_dict(), "state_sha256": state_hash(model),
               "initializer": initializer, "metadata": metadata}
    if optimizer is not None:
        payload["optimizer_state_dict"] = optimizer.state_dict()
    torch.save(payload, path)


def load_checkpoint(path: Path):
    deterministic_runtime()
    payload = torch.load(path, map_location="cpu", weights_only=True)
    if payload["model_version"] != VERSION:
        raise ValueError("checkpoint model version")
    c = ModelConfig(**payload["config"])
    _, expected = compile_embeddings(c.width, payload["initializer"]["profile"], payload["initializer"]["seed"])
    if payload["initializer"] != expected:
        raise ValueError("checkpoint semantic/token/initializer binding")
    model = AlphaStudent(c)
    model.load_state_dict(payload["state_dict"], strict=True)
    if state_hash(model) != payload["state_sha256"]:
        raise ValueError("checkpoint state hash")
    return model, payload
