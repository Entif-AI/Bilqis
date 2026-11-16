"""Retained checkpoint and frozen-soup custody verification."""
from __future__ import annotations

import json

import bilqis_mlx.data_plane as _data_plane
import bilqis_mlx.learning.capability_frontier as _learning_capability_frontier
import bilqis_mlx.learning.epoch_championships as _learning_epoch_championships
import bilqis_mlx.learning.grade_soup as _learning_grade_soup


def mentor_epoch_references(receipt):
    if receipt.get("mentor_epoch") is None:
        return ()
    from bilqis_mlx.learning.mentor_epoch import reference_checkpoints
    epochs = (*receipt.get("championship_epoch_history", ()), receipt["mentor_epoch"])
    return tuple(pointer for epoch in epochs
                 for pointer in (
                     *reference_checkpoints(epoch),
                     *(item["checkpoint"] for item in
                       _learning_epoch_championships.active_frontier(epoch).values())))


def regression_recovery_checkpoint(receipt):
    """Keep the explicitly abandoned terminal student as forensic custody."""
    recovery = receipt.get("student_regression_recovery")
    return (recovery.get("abandoned_student")
            if isinstance(recovery, dict) else None)


def verify_frozen_soup_custody(run_dir, receipt):
    """Verify current soup bytes and rollback predecessor; history is metadata."""
    for grade, soup in sorted(_data_plane.live_grade_soups(receipt).items()):
        if grade != soup.get("grade"):
            raise ValueError("GRADE_SOUP_CUSTODY_GRADE_DRIFT")
        _learning_grade_soup.verify_frozen_soup(run_dir, soup)
        if soup.get("previous"):
            older = soup["previous"] if isinstance(soup["previous"], list) else [soup["previous"]]
            for old in older:
                previous = run_dir / old["filename"]
                if (previous.parent != run_dir / "soups" or previous.is_symlink() or
                        not previous.is_file() or not _data_plane.verify_file_digest(
                            previous, old["sha256"])):
                    raise ValueError("GRADE_SOUP_PREVIOUS_BACKUP_DRIFT")


def verify_best_custody(run_dir, receipt):
    school = receipt["school"]
    historical_pending = (receipt.get("historical_capability_best", {})
                          if receipt.get("legacy_frontier_pending_replay") else {})
    sources = [school["current_student"], *school["champions"].values(),
               *receipt.get("historical_grade_champions", {}).values(),
               *(cap["checkpoint"] for cap in receipt.get("capability_best", {}).values()),
               *(cap["checkpoint"] for cap in receipt.get("graduation_perfect", {}).values()),
               *(cap["checkpoint"] for cap in historical_pending.values())]
    protected = _learning_capability_frontier.pinned(
        receipt.get("capability_best", {}), school["current_student"], school["champions"])
    protected |= _learning_capability_frontier.pinned(
        receipt.get("graduation_perfect", {}), school["current_student"], school["champions"])
    abandoned = regression_recovery_checkpoint(receipt)
    if abandoned is not None:
        sources.append(abandoned)
        protected |= _learning_capability_frontier.pinned({}, abandoned, {})
    if historical_pending:
        protected |= _learning_capability_frontier.pinned(
            historical_pending, school["current_student"], school["champions"])
    for item in receipt.get("historical_grade_champions", {}).values():
        protected |= _learning_capability_frontier.pinned({}, item, {})
    if receipt.get("curriculum_parent"):
        sources.append(receipt["curriculum_parent"])
        protected |= _learning_capability_frontier.pinned({}, receipt["curriculum_parent"], {})
    for peak in receipt.get("whole_student_peaks", ()):
        if peak.get("schema") != "bilqis.mlx.whole-student-retention/v1":
            raise ValueError("WHOLE_STUDENT_PEAK_SCHEMA_DRIFT")
        source = peak["checkpoint"]
        sources.append(source)
        protected |= _learning_capability_frontier.pinned({}, source, {})
    for source in mentor_epoch_references(receipt):
        sources.append(source)
        protected |= _learning_capability_frontier.pinned({}, source, {})
    for name in sorted(protected):
        root = run_dir / name
        if root.is_symlink() or root.parent != run_dir / "bundles":
            raise ValueError("HUMAN_TRAINER_CAPABILITY_CUSTODY_PATH_DRIFT")
        manifest = json.loads((root / "manifest.json").read_text())
        if not _data_plane.verify_file_digest(
                root / "model-and-own-adamw.safetensors", manifest["safetensors_sha256"]):
            raise ValueError("HUMAN_TRAINER_CAPABILITY_CUSTODY_SHA_DRIFT")
        for ref in sources:
            if (ref["filename"] == name and
                    (manifest["safetensors_sha256"] != ref["sha256"] or
                     manifest["optimizer_step"] != ref["optimizer_step"])):
                raise ValueError("HUMAN_TRAINER_CAPABILITY_CUSTODY_REFERENCE_DRIFT")
    verify_frozen_soup_custody(run_dir, receipt)
