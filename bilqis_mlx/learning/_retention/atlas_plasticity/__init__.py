"""B09 plasticity facade preserving the public retained-learning API."""
from bilqis_mlx.learning._atlas_plasticity_base import (
    ADAPTER_NAMES, ADAPTER_SCHEMA, AGE_SCHEMA, ELIGIBILITY_SCHEMA,
    ESTABLISHED_AGE, GROUP_COUNT, RANK, UPDATE_MODES, WIDTH,
    AdapterParameters, GroupEligibility, IdentityRowAge,
    adapter_forward, adapter_parameter_view, advance_accepted_row_ages,
    group_eligibility,
)
from bilqis_mlx.learning._atlas_plasticity_transition import (
    ACCEPTED_FAST_INTERVAL, ADAPTIVE_MODE, FAST_UPDATE, FOUNDATION_MODE,
    FULL_UPDATE, MODE_TRANSITION_SCHEMA, POLICY_STATE_SCHEMA, POLICY_VERSION,
    TRANSITIONED_POLICY_STATE_SCHEMA, TRANSITIONED_POLICY_VERSION,
    ModeTransition,
)
from bilqis_mlx.learning._atlas_plasticity_policy import (
    PlasticityPolicy, advance_candidate_policy, apply_promotion_transition,
    next_update_mode,
)
from bilqis_mlx.learning.atlas_participation import (
    ACTIVE_SCHEMA, DENOMINATOR_SCHEMA, INPUT_SCHEMA, MASK_SCHEMA,
    PARTICIPATION_SCHEMA, ROLE_READ_SCHEMA,
    ActiveAdmittedRows, ParameterMask, RoleReadParticipation,
    SemanticDenominator, StepParticipation, StepParticipationInputs, UpdateMask,
    mask_gradients, optimizer_participation_mask, parameter_update_mask,
    step_participation,
)
