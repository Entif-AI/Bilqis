"""Compatibility facade for evidence-seeded teacher-policy breeding."""
from __future__ import annotations

import hashlib
import json
import math

from .teacher_strategy_population import (
    active_effective_strategy_keys, checkpoint_active_effective_strategy_keys,
    effective_policy_features, effective_policy_key, effective_strategy_inventory,
    historical_policy_mean, BAMF_SUCCESSOR_SELECTION,
)
from ._teacher_breeding.selection import (
    UNPROVEN_BESPOKE_PER_CAPABILITY, _numeric_scope_family,
    portable_retained_challenger, pressure_challenger, selection_population,
    selection_metadata, filter_active_effective,
)
from ._teacher_breeding.ancestry import (
    _record_rank, _birth_novelty, _retained_parent_candidates,
)
from ._teacher_breeding.mutation import (
    _INEFFECTIVE_MUTATION_FIELDS, _ADAPTIVE_NUMERIC_FIELDS,
    _ADAPTIVE_OLD_RESOLUTION, _ADAPTIVE_LR_RESOLUTION,
    _ADAPTIVE_DISTILL_RESOLUTION, _one_knob_children, _quantized_midpoint,
    _adaptive_numeric_children, _register_child, mint_bespoke_effective_strategy,
)
from ._teacher_breeding.outcomes import (
    mark_bespoke_retained, record_policy_outcome_side_effects,
)
