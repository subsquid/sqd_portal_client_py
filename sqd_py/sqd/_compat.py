"""Compatibility utilities for Python 3.10+."""

import sys

if sys.version_info >= (3, 11):
    from enum import StrEnum
else:
    from enum import Enum

    class StrEnum(str, Enum):
        """String enum backport for Python 3.10."""

        def __str__(self) -> str:
            return str(self.value)

        @staticmethod
        def _generate_next_value_(
            name: str, start: int, count: int, last_values: list[str]
        ) -> str:
            return name


__all__ = ["StrEnum"]
