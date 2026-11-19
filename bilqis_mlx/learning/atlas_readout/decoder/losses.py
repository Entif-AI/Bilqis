"""Stable kind-balanced losses over executed, labelled legal decisions."""
from collections.abc import Mapping
from dataclasses import dataclass
import mlx.core as mx
from ..plan import DecisionKind
from ..records import invalid, TypedHeadLogits
from ..control import ControlAction
from ..causal_training import typed_decision_loss
from .prediction import ModelOutput, _targets, issued_output


AUXILIARY_WEIGHT=.10


@dataclass(frozen=True)
class LossParts:
    primary: mx.array
    role: mx.array
    epistemic: mx.array
    total: mx.array
    impact: mx.array | None = None
    exigency: mx.array | None = None
    novelty: mx.array | None = None
    routing: mx.array | None = None


def answer_loss(output,targets,mask):
    if type(output) is not ModelOutput or not issued_output(output) or not isinstance(mask,Mapping):
        invalid()
    output.__post_init__()
    labels=_targets(targets,output.plan)
    lookup={d.decision_id:d for d in output.plan.decisions}
    if any(key not in lookup or type(value) is not bool for key,value in mask.items()):
        invalid()
    zero=sum((mx.sum(d.logits)*0 for d in output.decisions),mx.array(0.,dtype=mx.float32))
    losses={kind:[] for kind in DecisionKind}
    for record in output.decisions:
        record.__post_init__()
        spec=lookup.get(record.decision_id)
        if spec is None or record.kind is not spec.kind or any(not any(
                type(candidate) is type(value) and candidate==value for value in spec.legal_values)
                for candidate in record.candidates):
            invalid()
        if not mask.get(record.decision_id,False) or record.decision_id not in labels:
            continue
        target=labels[record.decision_id]
        matches=tuple(i for i,value in enumerate(record.candidates)
                      if type(target) is type(value) and target==value)
        if len(matches)!=1:
            invalid()
        candidates=tuple(value.value if type(value) is ControlAction else value
                         for value in record.candidates)
        head=TypedHeadLogits(record.logits,candidates,output.plan.modality_id,
                             output.plan.snapshot.release_sha256)
        losses[record.kind].append(typed_decision_loss(head,target,legal_values=record.candidates))
    means={kind:(mx.mean(mx.stack(items)) if items else zero) for kind,items in losses.items()}
    primary=(means[DecisionKind.VALUE]+means[DecisionKind.CONTROL]
             +means[DecisionKind.OPERATOR]+means[DecisionKind.OPERAND])
    role=means[DecisionKind.ROLE]*AUXILIARY_WEIGHT
    epistemic=means[DecisionKind.EPISTEMIC]*AUXILIARY_WEIGHT
    return LossParts(primary,role,epistemic,primary+role+epistemic)
