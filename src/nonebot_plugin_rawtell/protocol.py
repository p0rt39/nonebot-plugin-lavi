"""Data models shared across rAwTell submodules.

Keep contracts here rather than passing ad-hoc dicts between submodules. Add a
Pydantic model per cross-module payload (config-independent), and keep
timestamps timezone-aware UTC.
"""

import os
from typing import TypeAlias
from datetime import datetime, timezone
from collections.abc import Callable

from pydantic import BaseModel


class DecisionContext(BaseModel):
    """One sampling of runtime state shared by a selector and its calculator.

    ``timestamp`` is timezone-aware UTC and ``pid`` is the process running the
    plugin. Both layers receive this exact object, so neither captures its own
    sample and the command text never reaches them.
    """

    timestamp: datetime
    pid: int


Calculator: TypeAlias = Callable[[DecisionContext], bool]
"""Return ``True`` for the affirmative/first option, ``False`` otherwise."""

Selector: TypeAlias = Callable[[DecisionContext], Calculator]
"""Pick one calculator from a context; it cannot see the command text."""


def capture_context() -> DecisionContext:
    """Sample the current UTC time and process id exactly once each."""
    return DecisionContext(timestamp=datetime.now(timezone.utc), pid=os.getpid())
