"""One scratch transformer; syntax-only inference and lineage-bound checkpoints."""
from __future__ import annotations

from dataclasses import asdict

import torch
from torch import nn
from torch.nn import functional as F

from bilqis_ref.model import Block, ModelConfig, batch, state_hash
from bilqis_logic.model import LogicStudent
from bilqis_logic.geometry import tensor_hash
from .graph import catalog, compile_embeddings, ID, STATES
from .kernel import encode

VERSION = "micro-student-0.1.0"


class MicroStudent(nn.Module):
    def __init__(self, config):
        super().__init__()
        if (config.vocab_size < len(catalog()["tokens"]) or config.width < 1 or config.heads < 1
                or config.width % config.heads or config.layers < 1 or config.context < 1 or config.precision != "fp32"):
            raise ValueError("micro architecture/token ABI")
        self.config = config
        self.embedding = nn.Embedding(config.vocab_size, config.width, padding_idx=0)
        self.position = nn.Embedding(config.context, config.width)
        self.blocks = nn.ModuleList(Block(config) for _ in range(config.layers))
        self.norm = nn.LayerNorm(config.width, bias=False)
        self.register_buffer("answer_ids", torch.tensor([6, 7] + [ID["micro.state." + s] for s in STATES[2:]]), persistent=False)
        self.apply(LogicStudent._initialize)

    def forward(self, ids, lengths):
        if (ids.ndim != 2 or ids.shape[1] > self.config.context or lengths.shape != (ids.shape[0],)
                or bool((lengths < 1).any()) or bool((lengths > ids.shape[1]).any())):
            raise ValueError("micro context/lengths")
        x = self.embedding(ids) + self.position(torch.arange(ids.shape[1], device=ids.device))[None]
        for block in self.blocks:
            x = block(x)
        h = self.norm(x)[torch.arange(ids.shape[0], device=ids.device), lengths - 1]
        return F.linear(h, self.embedding(self.answer_ids))


def initialize(config, seed=108, graph=None):
    graph = catalog() if graph is None else graph
    if config.vocab_size != len(graph["tokens"]):
        raise ValueError("frozen token map/architecture mismatch")
    torch.set_num_threads(1)
    torch.use_deterministic_algorithms(True)
    torch.manual_seed(seed)
    model = MicroStudent(config)
    table, initializer = compile_embeddings(config.width, graph)
    initializer = dict(initializer, seed=seed, graph=graph)
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
    return [{"prediction": STATES[int(p.argmax())], "logits": z.tolist(), "probabilities": p.tolist()}
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
    model, expected = initialize(ModelConfig(**payload["config"]), payload["initializer"]["seed"], payload["initializer"]["graph"])
    if expected != payload["initializer"]:
        raise ValueError("checkpoint initializer binding")
    model.load_state_dict(payload["model"], strict=True)
    if state_hash(model) != payload["state_sha256"]:
        raise ValueError("checkpoint state hash")
    return model, payload
