"""Process-local execution-epoch trust after one B11 source-currentness gate."""
from contextlib import contextmanager
from contextvars import ContextVar


_LAUNCH_TRUST = ContextVar("b11_source_authority_launch_trust", default=())


def source_authority_launch_trusted(authority, compiled_row, config, source):
    return any(
        record[0] is authority and record[1] is compiled_row
        and record[2] is config and record[3] is source
        for record in _LAUNCH_TRUST.get())


def compiled_input_launch_trusted(compiled):
    records = _LAUNCH_TRUST.get()
    if not records:
        return False
    rows = getattr(getattr(compiled, "compiled", None), "rows", ())
    configs = getattr(compiled, "compiler_configs", ())
    return bool(rows) and len(rows) == len(configs) and all(
        any(record[1] is row and record[2] is config for record in records)
        for row, config in zip(rows, configs))


@contextmanager
def source_authority_launch_epoch(batches):
    from bilqis_mlx.runtime.b11_source_execution_authority import (
        require_b11_source_execution_authority,
    )

    records = []
    for batch in batches:
        authority = getattr(batch, "source_execution_authority", None)
        if authority is None:
            continue
        row = batch.compiled.compiled.rows[0]
        config = batch.compiled.compiler_configs[0]
        source = batch.sources[0]
        require_b11_source_execution_authority(authority, row, config, source)
        records.append((authority, row, config, source))
    token = _LAUNCH_TRUST.set(tuple(records))
    try:
        yield
    finally:
        _LAUNCH_TRUST.reset(token)

