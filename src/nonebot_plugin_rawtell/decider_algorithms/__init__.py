"""Explicit registry of decision algorithms.

Each module in this package implements exactly one algorithm and exports an
``ALGORITHM`` object. Add it to the tuple below to make it selectable; do not
use import-time auto-discovery.
"""

from . import coin, dice
from ..protocol import Algorithm

ALGORITHMS: tuple[Algorithm, ...] = (
    coin.ALGORITHM,
    dice.ALGORITHM,
)

__all__ = ["ALGORITHMS"]
