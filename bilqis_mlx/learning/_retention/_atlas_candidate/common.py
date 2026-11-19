"""Shared candidate custody schemas and validation primitives."""
from bilqis_mlx.errors import ErrorBus, SCHOOL

STATE_SCHEMA = "bilqis.mlx.candidate-state/provisional-v1"
TRANSACTION_SCHEMA = "bilqis.mlx.candidate-transaction/provisional-v1"
LEGACY_STEP_PROOF_SCHEMA = "bilqis.mlx.candidate-step-proof/v1"
PREVIOUS_STEP_PROOF_SCHEMA = "bilqis.mlx.candidate-step-proof/v2"
STEP_PROOF_SCHEMA = "bilqis.mlx.candidate-step-proof/v3"
LOGICAL_BATCH_STEP_PROOF_SCHEMA = "bilqis.mlx.candidate-step-proof/v4"
CLOSURE_STEP_PROOF_SCHEMA = "bilqis.mlx.candidate-step-proof/v5"
LOGICAL_BATCH_CLOSURE_STEP_PROOF_SCHEMA = "bilqis.mlx.candidate-step-proof/v6"
OBJECTIVE_STEP_PROOF_SCHEMA = "bilqis.mlx.candidate-step-proof/v7"
OBJECTIVE_LOGICAL_BATCH_STEP_PROOF_SCHEMA = "bilqis.mlx.candidate-step-proof/v8"
OBJECTIVE_CLOSURE_STEP_PROOF_SCHEMA = "bilqis.mlx.candidate-step-proof/v9"
OBJECTIVE_LOGICAL_BATCH_CLOSURE_STEP_PROOF_SCHEMA = "bilqis.mlx.candidate-step-proof/v10"
OBJECTIVE_MINIMAL_STEP_PROOF_SCHEMA = "bilqis.mlx.candidate-step-proof/v11"
DIGEST_HEX_LENGTH = 64
TRANSACTION_ISSUER = object()
RETAINED_STATE_ISSUER = object()

def invalid():
    ErrorBus.Raise(SCHOOL.MODEL_TOPOLOGY.INVALID)

def is_digest(value) -> bool:
    return (isinstance(value, str) and len(value) == DIGEST_HEX_LENGTH
            and all(char in "0123456789abcdef" for char in value))
