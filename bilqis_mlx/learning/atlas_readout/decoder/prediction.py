"""Causal bounded prediction and explicit source-validation fallback."""
from dataclasses import dataclass
from copy import deepcopy
import hashlib
import numpy as np
from enum import Enum
from weakref import WeakValueDictionary, finalize
import mlx.core as mx
from bilqis_mlx.errors import BilqisError
from bilqis_mlx.runtime.autodiff_trace import (
    defer_host_tensor_validation, host_tensor_validation_enabled,
)
from ..control import ControlAction
from ..decisions import (
    DecisionOutput, DecodeStatus, start_decoding, ready_decisions,
    parent_outputs, commit_decisions,
)
from ..frames import FrameAnswer, publish_frame
from ..plan import AnswerPlan, DecisionKind
from ..records import invalid
from .inputs import validate_decoder_inputs
from .execution import validate_execution
from .math import prepare_memory, decision_state
from .heads import decision_logits


def _logit_fingerprint(logits):
    """Snapshot evaluated FP32 bytes without replacing the differentiable tensor."""
    mx.eval(logits)
    values = np.array(logits, dtype=np.float32, copy=True, order='C')
    return hashlib.sha256(values.tobytes(order='C')).digest()


def _batched_logit_fingerprints(logits):
    """Fingerprint many materialized 1-D logits with one device-to-host transfer."""
    if not logits:
        return ()
    lengths = tuple(value.size for value in logits)
    flat = mx.concatenate(tuple(value.reshape(-1) for value in logits))
    finite = mx.all(mx.isfinite(flat))
    mx.eval(flat, finite)
    if not bool(finite):
        invalid()
    values = np.array(flat, dtype=np.float32, copy=True, order='C')
    offset = 0
    fingerprints = []
    for length in lengths:
        current = values[offset:offset + length]
        fingerprints.append(hashlib.sha256(current.tobytes(order='C')).digest())
        offset += length
    return tuple(fingerprints)


class _IssuanceRegistry:
    """Own ephemeral numerical receipts; no module-level mutable collection."""

    def __init__(self):
        self.outputs = WeakValueDictionary()
        self.records = {}

    def issue(self, output, meaning, *, fingerprint=True, freeze_meaning=True):
        key = id(output)
        self.outputs[key] = output
        self.records[key] = (
            tuple((record, record.logits,
                   _logit_fingerprint(record.logits) if fingerprint else None)
                  for record in output.decisions),
            deepcopy(meaning) if freeze_meaning else meaning,
        )
        finalize(output, self.records.pop, key, None)
        return output

    def contains(self, output, meaning):
        key = id(output)
        if self.outputs.get(key) is not output:
            return False
        records, frozen_meaning = self.records[key]
        return (meaning == frozen_meaning
                and len(output.decisions) == len(records)
                and all(record is issued and record.logits is logits
                        and (fingerprint is None
                             and not host_tensor_validation_enabled()
                             or fingerprint is not None
                             and _logit_fingerprint(record.logits) == fingerprint)
                        for record, (issued, logits, fingerprint) in zip(output.decisions, records)))

    def attest(self, output, meaning):
        if not host_tensor_validation_enabled():
            return False
        key = id(output)
        if self.outputs.get(key) is not output or key not in self.records:
            return False
        records, frozen_meaning = self.records[key]
        if meaning != frozen_meaning or len(output.decisions) != len(records):
            return False
        if any(record is not issued or record.logits is not logits
               for record, (issued, logits, _fingerprint) in zip(output.decisions, records)):
            return False
        output.__post_init__()
        attested = tuple(
            (record, logits, _logit_fingerprint(logits))
            for record, (_issued, logits, _fingerprint) in zip(output.decisions, records)
        )
        self.records[key] = (attested, frozen_meaning)
        return True

    def attest_many(self, outputs, meanings):
        if (not host_tensor_validation_enabled() or not outputs
                or len(outputs) != len(meanings)):
            return False
        pending = []
        all_logits = []
        for output, meaning in zip(outputs, meanings):
            key = id(output)
            if self.outputs.get(key) is not output or key not in self.records:
                return False
            records, frozen_meaning = self.records[key]
            if meaning != frozen_meaning or len(output.decisions) != len(records):
                return False
            if any(record is not issued or record.logits is not logits
                   for record, (issued, logits, _fingerprint)
                   in zip(output.decisions, records)):
                return False
            pending.append((key, records, frozen_meaning))
            all_logits.extend(record.logits for record in output.decisions)
        with defer_host_tensor_validation():
            for output in outputs:
                output.__post_init__()
        fingerprints = _batched_logit_fingerprints(tuple(all_logits))
        cursor = 0
        for key, records, frozen_meaning in pending:
            count = len(records)
            attested = tuple(
                (record, logits, fingerprints[cursor + index])
                for index, (record, logits, _fingerprint) in enumerate(records)
            )
            self.records[key] = (attested, frozen_meaning)
            cursor += count
        return True


_ISSUANCE = _IssuanceRegistry()

def _meaning(output):
    return (output.plan, tuple((r.decision_id, r.kind, r.candidates)
                               for r in output.decisions), output.committed,
            output.status, output.execution_mode, output.frame,
            output.fallback_requested, output.schema_version)


def issued_output(output):
    """Require the exact live decoder result and its frozen source meaning."""
    return _ISSUANCE.contains(output, _meaning(output))


def _issue_output(output, *, fingerprint=True, freeze_meaning=True):
    if not freeze_meaning and (
            not output.plan.route_only
            or output.frame is not None
            or any(record.kind not in (DecisionKind.OPERATOR, DecisionKind.OPERAND)
                   or any(type(candidate) is not str for candidate in record.candidates)
                   for record in output.decisions)
            or any(type(item.value) is not str for item in output.committed)):
        invalid()
    return _ISSUANCE.issue(
        output, _meaning(output), fingerprint=fingerprint, freeze_meaning=freeze_meaning)


def attest_issued_output(output):
    """Complete deferred decoder evidence after tensors leave autodiff."""
    return _ISSUANCE.attest(output, _meaning(output))


def attest_issued_outputs(outputs):
    """Attest a microbatch of deferred decoder outputs with one logit transfer."""
    if type(outputs) is not tuple:
        return False
    return _ISSUANCE.attest_many(outputs, tuple(_meaning(output) for output in outputs))


class ExecutionMode(str,Enum):
    INFERENCE='INFERENCE'
    TEACHER_FORCED='TEACHER_FORCED'


@dataclass(frozen=True)
class DecisionLogits:
    decision_id: str
    kind: DecisionKind
    candidates: tuple
    logits: mx.array

    def __post_init__(self):
        if (type(self.decision_id) is not str or not self.decision_id
                or type(self.kind) is not DecisionKind or type(self.candidates) is not tuple
                or not self.candidates or len(set(self.candidates))!=len(self.candidates)
                or not isinstance(self.logits,mx.array) or self.logits.dtype!=mx.float32
                or self.logits.shape!=(len(self.candidates),)
                or (host_tensor_validation_enabled()
                    and not bool(mx.all(mx.isfinite(self.logits))))):
            invalid()


@dataclass(frozen=True)
class ModelOutput:
    plan: AnswerPlan
    decisions: tuple[DecisionLogits,...]
    committed: tuple[DecisionOutput,...]
    status: DecodeStatus
    execution_mode: ExecutionMode
    frame: FrameAnswer|None
    fallback_requested: bool
    schema_version: str='bilqis.mlx.model-output/v1'

    def __post_init__(self):
        if (self.schema_version!='bilqis.mlx.model-output/v1' or type(self.plan) is not AnswerPlan
                or type(self.decisions) is not tuple or type(self.committed) is not tuple
                or any(type(d) is not DecisionLogits for d in self.decisions)
                or any(type(o) is not DecisionOutput for o in self.committed)
                or type(self.status) is not DecodeStatus or type(self.execution_mode) is not ExecutionMode
                or type(self.fallback_requested) is not bool
                or self.frame is not None and type(self.frame) is not FrameAnswer):
            invalid()

        self.plan.__post_init__()
        ids={d.decision_id for d in self.plan.decisions}
        if (len({d.decision_id for d in self.decisions})!=len(self.decisions)
                or not {d.decision_id for d in self.decisions}<=ids
                or len({o.decision_id for o in self.committed})!=len(self.committed)
                or not {o.decision_id for o in self.committed}<=ids
                or (not self.plan.route_only
                    and (self.status is DecodeStatus.COMPLETE)!=(self.frame is not None))
                or (self.plan.route_only and self.frame is not None)
                or self.fallback_requested!=(self.status is not DecodeStatus.COMPLETE)):
            invalid()
        for record in (*self.decisions,*self.committed):
            record.__post_init__()
        if self.frame is not None:
            self.frame.__post_init__()
            if self.frame.plan!=self.plan:
                invalid()

        validate_execution(self)

    @property
    def generation_binding(self):
        return self.plan.generation_binding


def _targets(teacher_targets,plan):
    if teacher_targets is None:
        return {}
    if (type(teacher_targets) is not tuple
            or any(type(t) is not DecisionOutput for t in teacher_targets)
            or len({t.decision_id for t in teacher_targets})!=len(teacher_targets)):
        invalid()
    lookup={d.decision_id:d for d in plan.decisions}
    for target in teacher_targets:
        target.__post_init__()
        if target.decision_id not in lookup or not any(
                type(target.value) is type(value) and target.value==value
                for value in lookup[target.decision_id].legal_values):
            invalid()
    return {t.decision_id:t.value for t in teacher_targets}


def _ready_outputs(
        memory,state,semantics,parameters,prepared,targets,*,
        trace=False,replay_values=None):
    records,outputs=[],[]
    for decision in ready_decisions(state):
        z=decision_state(memory,decision,state,semantics,parameters,prepared)
        if not trace and not bool(mx.all(mx.isfinite(z))):
            return tuple(records),()
        try:
            candidates,logits=decision_logits(z,decision,state,semantics,parameters)
            records.append(DecisionLogits(decision.decision_id,decision.kind,candidates,logits))
        except BilqisError:
            return tuple(records),()
        if replay_values is not None:
            if decision.decision_id not in replay_values:
                continue
            value=replay_values[decision.decision_id]
        elif decision.decision_id in targets:
            value=targets[decision.decision_id]
        elif trace and len(candidates)==1:
            # Sparse supervised plans may omit deterministic ancestors. They
            # are safe to advance without a device-to-host argmax because the
            # legal value is already uniquely fixed by the plan contract.
            value=candidates[0]
        elif trace:
            # An unlabeled ambiguous ancestor would require a discrete model
            # choice inside autodiff. Fail the supervised path explicitly
            # rather than smuggling a host synchronization back into it.
            return tuple(records),()
        else:
            value=candidates[int(mx.argmax(logits).item())]
        if not any(type(value) is type(v) and value==v for v in candidates):
            invalid()
        outputs.append(DecisionOutput(decision.decision_id,value))
    end=tuple(o for o in outputs if o.value is ControlAction.END_FRAME)
    return tuple(records),(end[:1] if end else tuple(outputs))


def predict_typed(memory,eligible_context,answer_plan,active_semantics,readout_params,
                  teacher_targets=None,*,trace=False):
    validate_decoder_inputs(memory,eligible_context,answer_plan,active_semantics,readout_params)
    targets=_targets(teacher_targets,answer_plan)
    prepared=prepare_memory(memory,readout_params,active_semantics)
    state=start_decoding(answer_plan)
    records=[]
    while state.status is DecodeStatus.ACTIVE:
        batch,outputs=_ready_outputs(
            memory,state,active_semantics,readout_params,prepared,targets,trace=trace)
        if not outputs:
            return _issue_output(ModelOutput(answer_plan,tuple(records),state.committed,DecodeStatus.UNRESOLVED,
                ExecutionMode.TEACHER_FORCED if teacher_targets is not None else ExecutionMode.INFERENCE,
                None,True),fingerprint=not trace)
        try:
            state=commit_decisions(state,outputs)
        except BilqisError:
            return _issue_output(ModelOutput(answer_plan,tuple(records),state.committed,DecodeStatus.UNRESOLVED,
                ExecutionMode.TEACHER_FORCED if teacher_targets is not None else ExecutionMode.INFERENCE,
                None,True),fingerprint=not trace)
        committed_ids={o.decision_id for o in outputs}
        records.extend(record for record in batch if record.decision_id in committed_ids)
    status,frame=state.status,None
    if status is DecodeStatus.COMPLETE and not answer_plan.route_only:
        try:
            frame=publish_frame(state)
        except BilqisError:
            status=DecodeStatus.UNRESOLVED
    return _issue_output(ModelOutput(answer_plan,tuple(records),state.committed,status,
        ExecutionMode.TEACHER_FORCED if teacher_targets is not None else ExecutionMode.INFERENCE,
        frame,status is not DecodeStatus.COMPLETE),fingerprint=not trace)
