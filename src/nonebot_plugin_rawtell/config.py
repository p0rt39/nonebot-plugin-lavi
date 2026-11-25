"""rAwTell plugin configuration model."""

from pydantic import BaseModel


class ScopedConfig(BaseModel):
    """Settings under the ``RAWTELL__`` dotenv scope."""

    algorithm: str = "random"
    """Registered algorithm name, or ``"random"`` to choose per decision."""


class Config(BaseModel):
    """Top-level config holder for NoneBot plugin loading."""

    rawtell: ScopedConfig = ScopedConfig()
