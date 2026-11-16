"""Compatibility entry point for the canonical Electron bridge owner."""
import sys
from .electron import bridge

if __name__ == "__main__":
    raise SystemExit(bridge.main())
sys.modules[__name__] = bridge
