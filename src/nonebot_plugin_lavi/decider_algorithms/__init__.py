"""Explicit registry of decision algorithms."""

from . import dayan, trial, obi_ifa, geomancy
from ..protocol import Algorithm

ALGORITHMS: tuple[Algorithm, ...] = (
    dayan.ALGORITHM,
    geomancy.ALGORITHM,
    obi_ifa.ALGORITHM,
    trial.ALGORITHM,
)

__all__ = ["ALGORITHMS"]
