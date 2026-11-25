"""LaVI plugin configuration model."""

from string import Formatter

from pydantic import Field, BaseModel

try:
    from pydantic import field_validator as _field_validator
except ImportError:  # pragma: no cover - pydantic v1 compatibility
    from pydantic import validator as _field_validator

_FORMATTER = Formatter()


def _validate_template(value: str, *, field: str, placeholder: str) -> str:
    try:
        parsed = list(_FORMATTER.parse(value))
    except ValueError as error:
        raise ValueError(f"{field} must use balanced braces: {error}") from error

    used = set()
    for _, name, conversion, format_spec in parsed:
        if name is None:
            continue
        if name != placeholder:
            raise ValueError(
                f"{field} supports only the {placeholder!r} placeholder, got {name!r}"
            )
        if conversion or format_spec:
            raise ValueError(
                f"{field} does not support conversions or format specs "
                f"for {placeholder!r}"
            )
        used.add(name)

    if placeholder not in used:
        raise ValueError(f"{field} must contain the {placeholder!r} placeholder")
    return value


def _validate_not_blank(value: str) -> str:
    if not value.strip():
        raise ValueError("must not be blank")
    return value


class TextConfig(BaseModel):
    """Customizable user-facing reply copy.

    Template fields use ``str.format`` placeholders; each listed placeholder
    must appear exactly as written, while literal braces are doubled.
    Conversions and format specs are rejected. Dynamic values are collapsed
    to one line before formatting.
    """

    header: str = Field(default="🔮 决断仪式：「{decider}」", min_length=1)
    """First line of a decision reply; must contain ``{decider}``."""

    result: str = Field(default="✨ 决断结果：「{answer}」", min_length=1)
    """Answer line; must contain ``{answer}``."""

    operator_count: str = Field(default="📊 算子数量：{operator_count}", min_length=1)
    """Detailed-mode line; must contain ``{operator_count}``."""

    steps_header: str = "📜 演算过程："
    """Detailed-mode step heading; an empty string hides the heading."""

    unknown_algorithm: str = Field(
        default="⚠️ 未知算法：「{requested}」",
        min_length=1,
    )
    """Unknown-algorithm line; must contain ``{requested}``."""

    available_algorithms: str = Field(
        default="可用算法：{available}；random（随机）",
        min_length=1,
    )
    """Available algorithm list line; must contain ``{available}``."""

    unavailable: str = Field(default="决策算法暂时不可用，请稍后再试。", min_length=1)
    """Reply used when the command handler fails unexpectedly."""

    affirmative: str = Field(default="是", min_length=1)
    """Reply for an affirmative yes/no decision."""

    negative: str = Field(default="否", min_length=1)
    """Reply for a negative yes/no decision."""

    @_field_validator("header")
    @classmethod
    def _check_header(cls, value: str) -> str:
        return _validate_template(value, field="header", placeholder="decider")

    @_field_validator("result")
    @classmethod
    def _check_result(cls, value: str) -> str:
        return _validate_template(value, field="result", placeholder="answer")

    @_field_validator("operator_count")
    @classmethod
    def _check_operator_count(cls, value: str) -> str:
        return _validate_template(
            value,
            field="operator_count",
            placeholder="operator_count",
        )

    @_field_validator("unknown_algorithm")
    @classmethod
    def _check_unknown_algorithm(cls, value: str) -> str:
        return _validate_template(
            value,
            field="unknown_algorithm",
            placeholder="requested",
        )

    @_field_validator("available_algorithms")
    @classmethod
    def _check_available_algorithms(cls, value: str) -> str:
        return _validate_template(
            value,
            field="available_algorithms",
            placeholder="available",
        )

    @_field_validator("unavailable", "affirmative", "negative")
    @classmethod
    def _check_not_blank_fields(cls, value: str) -> str:
        return _validate_not_blank(value)


class ScopedConfig(BaseModel):
    """Settings under the ``LAVI__`` dotenv scope."""

    algorithm: str = "random"
    """Registered algorithm name, or ``"random"`` to choose per decision."""

    detailed: bool = False
    """Show the selected decider, operator count and calculation steps."""

    text: TextConfig = Field(default_factory=TextConfig)
    """Customizable reply copy under the ``LAVI__TEXT__`` scope."""


class Config(BaseModel):
    """Top-level config holder for NoneBot plugin loading."""

    lavi: ScopedConfig = Field(default_factory=ScopedConfig)
