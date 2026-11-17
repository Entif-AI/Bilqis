"""Fold B13-authenticated current-parent rejection credit before HOW selection."""
import json

from bilqis_mlx.data_plane import data_plane
from bilqis_mlx.learning.teacher_visit_identity import TeacherVisitIdentity, require_teacher_visit_receipt
from bilqis_mlx.runtime.bamf_operator.evidence_validation import read_candidate_horizon_evidence
from bilqis_mlx.runtime.priority_rejection_replay import current_rejections

from .observations import apply_outcome, invalid


def replay_rejected_outcomes(run_dir, parent, cache, teacher):
    for capability, visit_id, reason, receipt_sha in current_rejections(run_dir, parent, cache):
        receipt = json.loads(data_plane().get_object(receipt_sha))
        event = receipt['event']
        evidence = event['evidence']
        observation = evidence.get('how_outcome')
        if observation is None:
            continue
        visit = TeacherVisitIdentity.from_record(observation['teacher_visit'])
        require_teacher_visit_receipt(visit)
        payload = read_candidate_horizon_evidence(run_dir, evidence['candidate_evidence'])
        proposal = payload['proposal']
        decision = observation['decision']
        if (observation['attempt_id'] != payload['attempt_id']
                or observation['proposal_id'] != payload['proposal_id']
                or observation['candidate_evidence'] != evidence['candidate_evidence']['object']
                or observation['context'] != proposal.get('how_context')
                or observation['selected_teacher'] != proposal.get('selected_teacher')
                or observation['selected_policy'] != proposal['policy']
                or observation['teacher_visit'] != proposal['teacher_visit']
                or observation['context']['factory_release_sha256'] != proposal['factory_release_sha256']
                or visit.generation != cache.generation
                or visit.accepted_manifest_sha256 != cache.accepted_manifest_sha256
                or visit.capability_id != capability or visit.visit_id != visit_id
                or decision != evidence['decision']
                or decision['decision'] != 'REJECT' or decision['reason'] != reason
                or payload['outcome'] != {'accepted': False, 'decision': decision}
                or proposal['candidate_attempt_ordinal'] != evidence['rejection_journal_ordinal']
                or observation['attempted_steps'] != len(payload['steps'])
                or observation['retained_steps'] != 0):
            invalid()
        teacher = apply_outcome(teacher, observation)
        from bilqis_mlx.runtime.structural_weakness_replay import (
            apply_rejection_weaknesses,
        )
        teacher = apply_rejection_weaknesses(
            teacher, evidence, receipt_sha)
    return teacher
