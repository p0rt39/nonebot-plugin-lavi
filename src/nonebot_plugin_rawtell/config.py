"""rAwTell plugin configuration model."""

from pydantic import BaseModel


class ScopedConfig(BaseModel):
    """rAwTell settings, scoped under ``RAWTELL__`` in dotenv.

    Add one field per user-visible setting, with a Pydantic validation bound
    where the value has a meaningful range.
    """

    algorithm: str = "random"
    """Registered algorithm name, or ``"random"`` to choose per decision."""


class Config(BaseModel):
    """Top-level config holder for NoneBot plugin loading."""

    rawtell: ScopedConfig = ScopedConfig()
