"""Durable, atomic replay claims for asynchronous C14.4 contribution receipts."""
from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
import os
from pathlib import Path

from .contracts import canonical_bytes, digest, invalid, text
from .receipts import ReplayLedger

CLAIM_SCHEMA = "bilqis.c14.replay-claim/v1"


@dataclass(frozen=True)
class ReplayClaim:
    replay_id: str
    manifest_digest: str
    receipt_digest: str
    schema: str = CLAIM_SCHEMA

    def __post_init__(self) -> None:
        if (not text(self.replay_id)
                or not digest(self.manifest_digest)
                or not digest(self.receipt_digest)
                or self.schema != CLAIM_SCHEMA):
            invalid("BAMF_C14_REPLAY_CLAIM_INVALID")

    def record(self) -> dict[str, str]:
        self.__post_init__()
        return {
            "schema": self.schema,
            "replay_id": self.replay_id,
            "manifest_digest": self.manifest_digest,
            "receipt_digest": self.receipt_digest,
        }


class DurableReplayStore:
    """Canonical-school-owned replay fence; remote workers never receive this path."""

    def __init__(self, root: Path):
        self.root = Path(root)
        self._require_root()

    def _require_root(self) -> None:
        if self.root.is_symlink() or (self.root.exists() and not self.root.is_dir()):
            invalid("BAMF_C14_REPLAY_STORE_INVALID")

    @staticmethod
    def _key(replay_id: str) -> str:
        if not text(replay_id):
            invalid("BAMF_C14_REPLAY_ID_INVALID")
        return sha256(replay_id.encode("utf-8")).hexdigest()

    def _path(self, replay_id: str) -> Path:
        return self.root / f"{self._key(replay_id)}.json"

    def _read_claim(self, path: Path) -> ReplayClaim:
        if path.is_symlink() or not path.is_file():
            invalid("BAMF_C14_REPLAY_CLAIM_INVALID")
        try:
            raw = path.read_bytes()
            payload = json.loads(raw.decode("utf-8"))
            if type(payload) is not dict or set(payload) != {
                    "schema", "replay_id", "manifest_digest", "receipt_digest"}:
                invalid("BAMF_C14_REPLAY_CLAIM_INVALID")
            claim = ReplayClaim(
                payload["replay_id"], payload["manifest_digest"],
                payload["receipt_digest"], payload["schema"])
            if (canonical_bytes(claim.record()) != raw
                    or path.name != f"{self._key(claim.replay_id)}.json"):
                invalid("BAMF_C14_REPLAY_CLAIM_INVALID")
            return claim
        except (OSError, UnicodeError, json.JSONDecodeError, KeyError, TypeError):
            invalid("BAMF_C14_REPLAY_CLAIM_INVALID")

    def snapshot(self) -> ReplayLedger:
        self._require_root()
        if not self.root.exists():
            return ReplayLedger()
        paths = tuple(sorted(self.root.iterdir()))
        if any(not path.name.endswith(".json") for path in paths):
            invalid("BAMF_C14_REPLAY_STORE_INVALID")
        claims = tuple(self._read_claim(path) for path in paths)
        if len({claim.replay_id for claim in claims}) != len(claims):
            invalid("BAMF_C14_REPLAY_STORE_DUPLICATE")
        return ReplayLedger(tuple(sorted(claim.replay_id for claim in claims)))

    def claim(
            self, replay_id: str, manifest_digest: str,
            receipt_digest: str) -> ReplayLedger:
        """Atomically consume one replay identity before downstream admission work."""
        claim = ReplayClaim(replay_id, manifest_digest, receipt_digest)
        self._require_root()
        self.root.mkdir(parents=True, exist_ok=True)
        self._require_root()
        path = self._path(replay_id)
        raw = canonical_bytes(claim.record())
        flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
        flags |= getattr(os, "O_NOFOLLOW", 0)
        try:
            descriptor = os.open(path, flags, 0o600)
        except FileExistsError:
            self._read_claim(path)
            invalid("BAMF_C14_CONTRIBUTION_REPLAYED")
        try:
            with os.fdopen(descriptor, "wb") as target:
                target.write(raw)
                target.flush()
                os.fsync(target.fileno())
            directory = os.open(self.root, os.O_RDONLY | os.O_DIRECTORY)
            try:
                os.fsync(directory)
            finally:
                os.close(directory)
        except BaseException:
            path.unlink(missing_ok=True)
            raise
        return self.snapshot()


def replay_store_for_run(run_dir: Path) -> "DurableReplayStore":
    run_dir = Path(run_dir)
    if run_dir.is_symlink() or not run_dir.is_dir():
        invalid("BAMF_C14_CANONICAL_RUN_DIR_INVALID")
    return DurableReplayStore(run_dir / "swarm-contribution-replay")
