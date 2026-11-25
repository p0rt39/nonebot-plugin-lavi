"""Explicit registry of decision algorithms."""

from . import coin, dice
from ..protocol import Algorithm

ALGORITHMS: tuple[Algorithm, ...] = (
    coin.ALGORITHM,
    dice.ALGORITHM,
)

__all__ = ["ALGORITHMS"]
