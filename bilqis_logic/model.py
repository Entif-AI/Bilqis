"""Scratch Boolean student; prediction is syntax encoding plus neural inference."""
from __future__ import annotations

from dataclasses import asdict

import torch
from torch import nn
from torch.nn import functional as F

from bilqis_ref.model import Block, ModelConfig, batch, state_hash
from .geometry import compile_embeddings, tensor_hash
from .kernel import TOKENS, encode

VERSION = "cogal-student-0.1.0"


class LogicStudent(nn.Module):
    def __init__(self, config):
        super().__init__()
        if (config.vocab_size != len(TOKENS) or config.width < 1 or config.heads < 1
                or config.width % config.heads or config.layers < 1 or config.context < 1
                or config.precision not in ("fp32", "ternary")):
            raise ValueError("logic architecture/token ABI")
        self.config = config
        self.embedding = nn.Embedding(config.vocab_size, config.width, padding_idx=0)
        self.position = nn.Embedding(config.context, config.width)
        self.blocks = nn.ModuleList(Block(config) for _ in range(config.layers))
        self.norm = nn.LayerNorm(config.width, bias=False)
        self.register_buffer("answer_ids", torch.tensor([6, 7]), persistent=False)
        self.apply(self._initialize)

    @staticmethod
    def _initialize(module):
        if isinstance(module, (nn.Linear, nn.Embedding)):
            nn.init.normal_(module.weight, mean=0, std=.02)

    def forward(self, ids, lengths):
        if (ids.ndim != 2 or ids.shape[1] > self.config.context or lengths.shape != (ids.shape[0],)
                or bool((lengths < 1).any()) or bool((lengths > ids.shape[1]).any())):
            raise ValueError("logic context/lengths")
        x = self.embedding(ids) + self.position(torch.arange(ids.shape[1], device=ids.device))[None]
        for block in self.blocks:
            x = block(x)
        h = self.norm(x)[torch.arange(ids.shape[0], device=ids.device), lengths - 1]
        return F.linear(h, self.embedding(self.answer_ids))


def initialize(config, seed=111, profile="semantic_aligned"):
    torch.set_num_threads(1)
    torch.use_deterministic_algorithms(True)
    torch.manual_seed(seed)
    model = LogicStudent(config)
    table, initializer = compile_embeddings(config.width, profile, seed)
    with torch.no_grad():
        model.embedding.weight.copy_(table)
    if tensor_hash(model.embedding.weight) != initializer["tensor_sha256"]:
        raise ValueError("initial embedding distortion")
    return model, initializer


@torch.no_grad()
def predict(model, records):
    model.eval()
    logits = model(*batch([encode(r) for r in records])).cpu()
    if not bool(torch.isfinite(logits).all()):
        raise ValueError("nonfinite neural prediction")
    return [{"prediction": bool(p.argmax()), "logits": z.tolist(), "probabilities": p.tolist()}
            for z, p in zip(logits, logits.softmax(-1))]


def save_checkpoint(path, model, initializer, metadata, optimizer=None):
    payload = {"version": VERSION, "config": asdict(model.config), "model": model.state_dict(),
               "state_sha256": state_hash(model), "initializer": initializer, "metadata": metadata,
               "torch_rng": torch.get_rng_state()}
    if optimizer is not None:
        payload["optimizer"] = optimizer.state_dict()
    with path.open("xb") as stream:
        torch.save(payload, stream)


def load_checkpoint(path):
    payload = torch.load(path, map_location="cpu", weights_only=True)
    if payload["version"] != VERSION:
        raise ValueError("checkpoint version")
    config = ModelConfig(**payload["config"])
    model, expected = initialize(config, payload["initializer"]["seed"], payload["initializer"]["profile"])
    if expected != payload["initializer"]:
        raise ValueError("checkpoint initializer binding")
    model.load_state_dict(payload["model"], strict=True)
    if state_hash(model) != payload["state_sha256"]:
        raise ValueError("checkpoint state hash")
    return model, payload
