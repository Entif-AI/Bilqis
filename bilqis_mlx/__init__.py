"""Private, neural-inert Bilqis MLX school controls."""
__version__ = "1.2.6"  # x-release-please-version

from pathlib import Path

_OWNER_GROUPS = ('_boolean_sources', '_numeric_sources', '_source_evidence', '_release_views', '_semantic_tools', '_operations')
__path__.extend(str(Path(__file__).parent / name) for name in _OWNER_GROUPS)
