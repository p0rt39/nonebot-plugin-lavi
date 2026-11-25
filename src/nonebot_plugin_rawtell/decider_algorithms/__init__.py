"""Explicit registry of decision algorithms."""

from . import dayan, obi_ifa, geomancy
from ..protocol import Algorithm

ALGORITHMS: tuple[Algorithm, ...] = (
    dayan.ALGORITHM,
    geomancy.ALGORITHM,
    obi_ifa.ALGORITHM,
)

__all__ = ["ALGORITHMS"]
