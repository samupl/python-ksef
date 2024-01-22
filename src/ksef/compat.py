"""Compatibility libraries for python 3.x."""

try:
    from enum import StrEnum  # type: ignore[attr-defined]
except ImportError:
    from enum import Enum

    class StrEnum(str, Enum):  # type: ignore[no-redef]
        """Compatibility class for StrEnum for older python versions."""


__all__ = ["StrEnum"]
