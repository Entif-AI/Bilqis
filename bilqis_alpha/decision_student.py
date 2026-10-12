"""Scratch, candidate-equivariant scorer for decision panels."""
from __future__ import annotations

from dataclasses import asdict
from pathlib import Path

import torch
from torch import nn
from torch.nn import functional as F

from bilqis_ref.model import Block, ModelConfig, QLinear, state_hash
from .decision_features import compile_embeddings, token_manifest
from .features import tensor_hash

VERSION = "decision-student-0.1.0"


def deterministic_runtime(seed=202):
    torch.set_num_threads(1)
    torch.use_deterministic_algorithms(True)
    torch.manual_seed(seed)


class DecisionStudent(nn.Module):
    """One shared sequence encoder, followed by an independent score per candidate."""

    def __init__(self, config: ModelConfig):
        super().__init__()
        if (config.vocab_size != len(token_manifest()["tokens"]) or config.width % config.heads
                or config.layers < 1 or config.context < 1
                or config.precision not in ("fp32", "ternary")):
            raise ValueError("decision model architecture/ABI")
        self.config = config
        self.embedding = nn.Embedding(config.vocab_size, config.width, padding_idx=0)
        self.position = nn.Embedding(config.context, config.width)
        self.blocks = nn.ModuleList(Block(config) for _ in range(config.layers))
        self.norm = nn.LayerNorm(config.width, bias=False)
        self.score_in = QLinear(4 * config.width, config.width, config.precision)
        self.score_out = QLinear(config.width, 1, config.precision)
        self.apply(self._initialize)

    @staticmethod
    def _initialize(module):
        if isinstance(module, (nn.Linear, nn.Embedding)):
            nn.init.normal_(module.weight, mean=0, std=.02)

    def _encode(self, ids: torch.Tensor, lengths: torch.Tensor) -> torch.Tensor:
        x = self.embedding(ids) + self.position(torch.arange(ids.shape[1], device=ids.device))[None]
        for block in self.blocks:
            x = block(x)
        return self.norm(x)[torch.arange(ids.shape[0], device=ids.device), lengths - 1]

    def forward(self, state_ids, state_lengths, candidate_ids, candidate_lengths, candidate_mask):
        if (state_ids.ndim != 2 or candidate_ids.ndim != 3
                or state_lengths.shape != (state_ids.shape[0],)
                or candidate_lengths.shape != candidate_ids.shape[:2]
                or candidate_mask.shape != candidate_ids.shape[:2]
                or state_ids.shape[0] != candidate_ids.shape[0]):
            raise ValueError("decision shapes")
        batch_size, candidates_per_state, candidate_width = candidate_ids.shape
        state_width = state_ids.shape[1]
        if not batch_size or not candidates_per_state or not state_width or not candidate_width:
            raise ValueError("decision shapes")
        if state_width > self.config.context or candidate_width > self.config.context:
            raise ValueError("CONTEXT_OVERFLOW")
        if (bool((state_lengths < 1).any()) or bool((state_lengths > state_width).any())
                or bool((candidate_lengths < 0).any())
                or bool((candidate_lengths > candidate_width).any())):
            raise ValueError("decision lengths")
        if candidate_mask.dtype != torch.bool:
            raise ValueError("decision mask")
        if bool((candidate_mask & (candidate_lengths < 1)).any()):
            raise ValueError("decision lengths")
        if not bool(candidate_mask.any(dim=1).all()):
            raise ValueError("no offered candidates")

        state = self._encode(state_ids, state_lengths)
        flattened_ids = candidate_ids.reshape(batch_size * candidates_per_state, candidate_width)
        # Masked zero-length slots are discarded after scoring.
        flattened_lengths = candidate_lengths.reshape(-1).clamp_min(1)
        candidate = self._encode(flattened_ids, flattened_lengths).reshape(batch_size, candidates_per_state, -1)
        state = state[:, None, :].expand_as(candidate)
        combined = torch.cat((state, candidate, state * candidate, (state - candidate).abs()), dim=-1)
        logits = self.score_out(F.relu(self.score_in(combined))).squeeze(-1)
        return logits.masked_fill(~candidate_mask, float("-inf"))


def _default_config():
    return ModelConfig(vocab_size=len(token_manifest()["tokens"]), context=384, width=64,
                       layers=2, heads=4, expansion=2, precision="ternary")


def initialize(config: ModelConfig | None = None, seed=202):
    config = _default_config() if config is None else config
    deterministic_runtime(seed)
    model = DecisionStudent(config)
    table, initializer = compile_embeddings(config.width, seed=seed)
    with torch.no_grad():
        model.embedding.weight.copy_(table)
    if tensor_hash(model.embedding.weight) != initializer["tensor_sha256"]:
        raise ValueError("pre-step embedding distortion")
    return model, initializer


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
    if payload.get("model_version") != VERSION:
        raise ValueError("checkpoint model version")
    config = ModelConfig(**payload["config"])
    initializer = payload["initializer"]
    _, expected = compile_embeddings(config.width, seed=initializer["seed"])
    if initializer != expected:
        raise ValueError("checkpoint semantic/token/initializer binding")
    model = DecisionStudent(config)
    model.load_state_dict(payload["state_dict"], strict=True)
    if state_hash(model) != payload.get("state_sha256"):
        raise ValueError("checkpoint state hash")
    return model, payload
