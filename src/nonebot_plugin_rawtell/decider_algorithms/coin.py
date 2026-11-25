"""Fair coin-flip decision algorithm."""

from random import Random

from ..protocol import Algorithm, DecisionContext, derive_algorithm_seed

NAME = "coin"
VERSION = 1
WEIGHT = 1


def calculate(context: DecisionContext) -> bool:
    """Return one fair coin bit derived from the shared decision context."""
    rng = Random(derive_algorithm_seed(context, name=NAME, version=VERSION))
    return bool(rng.getrandbits(1))


ALGORITHM = Algorithm(
    name=NAME,
    version=VERSION,
    weight=WEIGHT,
    calculate=calculate,
)
