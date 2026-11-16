"""Historical B01 topology API; cohesive owners preserve its exact contracts."""
from __future__ import annotations
from bilqis_mlx.errors import ErrorBus
from bilqis_mlx.errors import SCHOOL
from bilqis_mlx.runtime.model_topology import DEFAULT_OPTIMIZER
from bilqis_mlx.runtime.model_topology import ModelTopologySpec
from bilqis_mlx.runtime.model_topology import SCHEMA as LEGACY_SCHEMA
from dataclasses import asdict
from dataclasses import dataclass
from dataclasses import fields
from enum import Enum
from typing import Mapping
import hashlib
import json
import math
from .topology_v2.spec import (
    SCHEMA,
    BAMF_ARCHITECTURE_ID,
    LEGACY_ARCHITECTURE_ID,
    EXTENTS_SCHEMA,
    PROVENANCE_SCHEMA,
    IDENTITY_ESTABLISHED_AGE,
    _digest,
    ModelTopologySpecV2,
    deserialize_topology,
    initializer_seed,
)
from .topology_v2.dimensions import (
    MATRIX_RANK,
    FEATURE_NONE_ROW,
    FEATURE_RESERVED_ROWS,
    FEATURE_ROWS,
    FEATURE_DIM,
    GRAPH_FEATURE_DIM,
    MOTIF_CHANNELS,
    SHA256_HEX_LENGTH,
    IDENTITY_BANK_SHAPE,
    MOTIF_PAGE_SHAPE,
)
from .topology_v2.records import (
    ParameterGroup,
    ParameterCategory,
    AdapterMatrixComponent,
    ADAPTER_MATRIX_SUFFIXES,
    Initializer,
    GenerationExtents,
    GenerationProvenance,
    _generation_from_record,
    ParameterSpec,
    ParameterCensus,
)
from .topology_v2.ledger import (
    _parameter,
    _input_parameters,
    _block_parameters,
    _depth_parameters,
    _motif_site_parameters,
    _plastic_parameters,
    _output_parameters,
    expected_bamf_shapes,
    bamf_parameter_census,
    print_bamf_parameter_census,
)
from .topology_v2.initialization import (
    initialize_bamf_parameter,
    initialize_bamf_row,
)
from .topology_v2.factors import (
    project_identity_source_factor,
)
from .topology_v2.validation import (
    validate_bamf_parameters,
)
from .topology_v2.construction import (
    create_unbound_bamf_state,
)
from .topology_v2.serialization import (
    bamf_storage_key,
    bamf_serialization_arrays,
    bamf_deserialize_arrays,
)
from .topology_v2.authority import (
    AUTHORITY_SCHEMA as B01_GENERATION_AUTHORITY_SCHEMA,
    B01GenerationAuthority,
    b01_generation_authority,
    b01_generation_extents,
    b01_model_implementation_sha256,
    validate_b01_generation_authority,
)

# Preserve historical serialized type and pickle resolution.
for _record in (
    ModelTopologySpecV2,
    ParameterGroup,
    ParameterCategory,
    AdapterMatrixComponent,
    Initializer,
    GenerationExtents,
    GenerationProvenance,
    ParameterSpec,
    ParameterCensus,
):
    _record.__module__ = __name__
