"""Cross-module data models, seed derivation and bit derivation for LaVI."""

import os
import hashlib
import secrets
from typing import TypeAlias
from datetime import datetime, timezone
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass
from collections.abc import Callable, Iterator

from pydantic import Field, BaseModel

OPERATOR_COUNT = 13
OPERATOR_BITS = 64


class DecisionContext(BaseModel):
    """One sampling of runtime state shared by a selector and its calculator.

    ``timestamp`` is timezone-aware UTC, ``pid`` is the process running the
    plugin, and ``nonce1``/``nonce2``/``nonce3`` are three independent 64-bit
    CSPRNG samples. Both layers receive this exact object, so neither captures
    its own sample and the command text never reaches them.
    """

    timestamp: datetime
    pid: int
    nonce1: int = Field(default=0, ge=0, lt=1 << 64)
    nonce2: int = Field(default=0, ge=0, lt=1 << 64)
    nonce3: int = Field(default=0, ge=0, lt=1 << 64)


Calculator: TypeAlias = Callable[[DecisionContext], bool]
"""Return ``True`` for the affirmative/first option, ``False`` otherwise."""


@dataclass(frozen=True, slots=True)
class Explanation:
    """One algorithm result with human-readable calculation steps."""

    answer: bool
    steps: tuple[str, ...]


Explain: TypeAlias = Callable[[DecisionContext], Explanation]
"""Return the answer plus the intermediate values that produced it."""


@dataclass(frozen=True, slots=True)
class Algorithm:
    """Runtime metadata for one selectable decision algorithm.

    This object is never serialized: ``calculate`` is a callable. The registry
    and persistence layers may store ``name``/``version`` instead.
    """

    name: str
    version: int
    weight: int
    calculate: Calculator
    display_name: str | None = None
    explain: Explain | None = None

    def __post_init__(self) -> None:
        if not self.name or self.name == "random":
            raise ValueError(f"invalid algorithm name: {self.name!r}")
        if self.version < 1:
            raise ValueError(f"{self.name}: version must be >= 1")
        if self.weight < 0:
            raise ValueError(f"{self.name}: weight must be >= 0")
        if not callable(self.calculate):
            raise TypeError(f"{self.name}: calculate must be callable")
        if self.display_name is not None and not self.display_name:
            raise ValueError(f"{self.name}: display_name must be non-empty")
        if self.explain is not None and not callable(self.explain):
            raise TypeError(f"{self.name}: explain must be callable")

    @property
    def label(self) -> str:
        """Return the user-facing name, falling back to the stable name."""
        return self.display_name or self.name


Selector: TypeAlias = Callable[[DecisionContext], Algorithm]
"""Pick one algorithm from a context; it cannot see the command text."""


@dataclass(frozen=True, slots=True)
class Decision:
    """The answer together with the algorithm and operator count behind it."""

    answer: str
    algorithm: str
    display_name: str
    operator_count: int
    steps: tuple[str, ...] = ()


@dataclass(slots=True)
class OperatorTally:
    """Mutable count of 64-bit operators derived within one decision."""

    count: int = 0

    def increment(self) -> None:
        self.count += 1


_operator_tally: ContextVar[OperatorTally | None] = ContextVar(
    "lavi_operator_tally", default=None
)


@contextmanager
def count_operators() -> Iterator[OperatorTally]:
    """Count the operators derived inside the block without changing values."""
    tally = OperatorTally()
    token = _operator_tally.set(tally)
    try:
        yield tally
    finally:
        _operator_tally.reset(token)


def capture_context() -> DecisionContext:
    """Sample UTC time, process id and three fresh 64-bit nonces exactly once."""
    return DecisionContext(
        timestamp=datetime.now(timezone.utc),
        pid=os.getpid(),
        nonce1=secrets.randbits(64),
        nonce2=secrets.randbits(64),
        nonce3=secrets.randbits(64),
    )


def derive_seed(context: DecisionContext, *, purpose: str) -> int:
    """Hash one decision context into a stable 64-bit seed for ``purpose``.

    The purpose string keeps selector and algorithm randomness independent.
    Callers must not sample entropy themselves; the context is the only input.
    """
    material = "|".join(
        (
            purpose,
            context.timestamp.isoformat(),
            str(context.pid),
            str(context.nonce1),
            str(context.nonce2),
            str(context.nonce3),
        )
    )
    digest = hashlib.blake2b(material.encode(), digest_size=8, person=b"lavi")
    tally = _operator_tally.get()
    if tally is not None:
        tally.increment()
    return int.from_bytes(digest.digest(), "big")


def _algorithm_purpose(name: str, version: int) -> str:
    return f"algorithm:{name}:v{version}"


def derive_algorithm_seed(context: DecisionContext, *, name: str, version: int) -> int:
    """Derive the seed for one algorithm, separated by its stable identity."""
    return derive_seed(context, purpose=_algorithm_purpose(name, version))


def derive_algorithm_operators(
    context: DecisionContext,
    *,
    name: str,
    version: int,
    stage: str,
    count: int,
) -> tuple[int, ...]:
    """Derive independent full-width operators for one algorithm stage."""
    if not stage:
        raise ValueError("stage must be non-empty")
    if count < 0:
        raise ValueError("count must be non-negative")
    return tuple(
        derive_seed(
            context,
            purpose=f"{_algorithm_purpose(name, version)}:{stage}:operator:{index}",
        )
        for index in range(1, count + 1)
    )


def derive_bits(
    context: DecisionContext, *, purpose: str, count: int
) -> tuple[int, ...]:
    """Derive ``count`` independent bits for ``purpose``.

    Each bit is the most significant bit of its own BLAKE2b operator, so the
    sampled context data participates directly in the computation instead of
    seeding a separate PRNG. Separate operators keep the marks independent.
    """
    if count < 0:
        raise ValueError("count must be non-negative")
    return tuple(
        (derive_seed(context, purpose=f"{purpose}:operator:{index}") >> 63) & 1
        for index in range(1, count + 1)
    )


def derive_algorithm_bits(
    context: DecisionContext,
    *,
    name: str,
    version: int,
    stage: str,
    count: int,
) -> tuple[int, ...]:
    """Derive independent bits for one stage of a named algorithm version."""
    if not stage:
        raise ValueError("stage must be non-empty")
    return derive_bits(
        context,
        purpose=f"{_algorithm_purpose(name, version)}:{stage}",
        count=count,
    )
