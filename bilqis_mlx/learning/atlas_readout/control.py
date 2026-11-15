"""B01 finite CONTROL readout, separate from semantic and role selection."""
from enum import Enum
from typing import Mapping
import mlx.core as mx
from bilqis_mlx.runtime.autodiff_trace import host_tensor_validation_enabled
from .records import WIDTH, TypedHeadLogits, invalid, validate_hidden


class ControlAction(str, Enum):
    EMIT_VALUE = 'EMIT_VALUE'
    EMIT_UNKNOWN = 'EMIT_UNKNOWN'
    EMIT_ALTERNATIVES = 'EMIT_ALTERNATIVES'
    END_FRAME = 'END_FRAME'


def control_logits(hidden, parameters, semantic_release, *, can_end):
    validate_hidden(hidden)
    if not isinstance(parameters, Mapping) or type(can_end) is not bool:
        invalid()
    for name, shape in (('readout.control', (4, WIDTH)), ('readout.control_bias', (4,))):
        value = parameters.get(name)
        if (not isinstance(value, mx.array) or value.shape != shape
                or value.dtype != mx.float32 or (host_tensor_validation_enabled()
                and not bool(mx.all(mx.isfinite(value))))):
            invalid()
    actions = tuple(ControlAction) if can_end else tuple(ControlAction)[:-1]
    logits = hidden @ parameters['readout.control'].T + parameters['readout.control_bias']
    return TypedHeadLogits(logits[..., :len(actions)], tuple(x.value for x in actions),
                           'answer.control/v1', semantic_release)
