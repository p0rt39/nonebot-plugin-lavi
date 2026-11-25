"""Explicit registry of decision algorithms."""

from . import obi_ifa, geomancy
from ..protocol import Algorithm

ALGORITHMS: tuple[Algorithm, ...] = (
    geomancy.ALGORITHM,
    obi_ifa.ALGORITHM,
)

__all__ = ["ALGORITHMS"]
