"""Single-die decision algorithm; an odd roll is affirmative."""

from random import Random

from ..protocol import Algorithm, DecisionContext, derive_algorithm_seed

NAME = "dice"
VERSION = 1
WEIGHT = 1


def calculate(context: DecisionContext) -> bool:
    """Roll one fair six-sided die; odd means the first option wins."""
    rng = Random(derive_algorithm_seed(context, name=NAME, version=VERSION))
    return rng.randrange(1, 7) % 2 == 1


ALGORITHM = Algorithm(
    name=NAME,
    version=VERSION,
    weight=WEIGHT,
    calculate=calculate,
)
