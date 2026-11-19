"""Serialized student execution, immutable artifacts and assessment custody.

Grouped runtime owners keep their established ``bilqis_mlx.runtime`` module
names and relative imports.
"""
from pathlib import Path

_OWNER_GROUPS = (
    "_projection", "_admission", "_capability", "_source", "_model", "_custody",
    "_operator", "_teacher", "_teacher/priority", "_teacher/cadence", "_certification",
    "_depth", "_correction", "_batch", "_batch/c08_distributed",
    "_batch/training", "_admission/v2", "_admission/jit", "_admission/lease",
    "_admission/generated_grade_runtime",
    "_capability/factory",
    "_model/cache", "_model/backbone", "_correction/owners",
    "_correction/accepted", "_correction/weakness",
)
__path__.extend(str(Path(__file__).parent / name) for name in _OWNER_GROUPS)
