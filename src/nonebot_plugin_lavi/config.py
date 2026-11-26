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

    record_id: str = Field(default="记录 ID：{record_id}", min_length=1)
    """Record identifier line; must contain ``{record_id}``."""

    record_time: str = Field(default="决策时间：{timestamp}", min_length=1)
    """Record time line; must contain ``{timestamp}``."""

    record_algorithm: str = Field(default="原算法：{algorithm}", min_length=1)
    """Record algorithm line; must contain ``{algorithm}``."""

    record_options: str = Field(default="原候选：{options}", min_length=1)
    """Record candidate line; must contain ``{options}``."""

    record_result: str = Field(default="原结果：{result}", min_length=1)
    """Record result line; must contain ``{result}``."""

    record_count: str = Field(default="原算子数量：{operator_count}", min_length=1)
    """Record operator-count line; must contain ``{operator_count}``."""

    unavailable: str = Field(default="决策算法暂时不可用，请稍后再试。", min_length=1)
    """Reply used when the command handler fails unexpectedly."""

    affirmative: str = Field(default="是", min_length=1)
    """Reply for an affirmative yes/no decision."""

    negative: str = Field(default="否", min_length=1)
    """Reply for a negative yes/no decision."""

    history_disabled_decision: str = Field(
        default="历史记录已关闭，本次决策无法复查。",
        min_length=1,
    )
    """Notice appended when history is paused for a new decision."""

    history_write_failed: str = Field(
        default="记录未保存，本次决策无法复查。",
        min_length=1,
    )
    """Notice appended when the decision could not be persisted."""

    review_usage: str = Field(default="用法：/lavi-review <记录ID>", min_length=1)
    """Reply for a malformed review identifier."""

    history_disabled: str = Field(default="历史记录已关闭。", min_length=1)
    """Reply when history is paused and a review is requested."""

    record_missing: str = Field(default="记录不存在或已滚动移除。", min_length=1)
    """Reply when the identifier is valid but no record remains."""

    history_unavailable: str = Field(
        default="历史记录暂时不可用，请稍后再试。",
        min_length=1,
    )
    """Reply when the history file cannot be read."""

    review_version_unavailable: str = Field(
        default="无法复算：原算法版本不可用。",
        min_length=1,
    )
    """Review status when the recorded algorithm version is gone."""

    review_match: str = Field(default="复查一致。", min_length=1)
    """Review status when the replay matches the recorded result."""

    review_mismatch: str = Field(default="复查不一致。", min_length=1)
    """Review status when the replay differs from the recorded result."""

    review_failed: str = Field(default="复算失败。", min_length=1)
    """Review status when replaying the algorithm raised."""

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

    @_field_validator("record_id")
    @classmethod
    def _check_record_id(cls, value: str) -> str:
        return _validate_template(value, field="record_id", placeholder="record_id")

    @_field_validator("record_time")
    @classmethod
    def _check_record_time(cls, value: str) -> str:
        return _validate_template(value, field="record_time", placeholder="timestamp")

    @_field_validator("record_algorithm")
    @classmethod
    def _check_record_algorithm(cls, value: str) -> str:
        return _validate_template(
            value,
            field="record_algorithm",
            placeholder="algorithm",
        )

    @_field_validator("record_options")
    @classmethod
    def _check_record_options(cls, value: str) -> str:
        return _validate_template(value, field="record_options", placeholder="options")

    @_field_validator("record_result")
    @classmethod
    def _check_record_result(cls, value: str) -> str:
        return _validate_template(value, field="record_result", placeholder="result")

    @_field_validator("record_count")
    @classmethod
    def _check_record_count(cls, value: str) -> str:
        return _validate_template(
            value,
            field="record_count",
            placeholder="operator_count",
        )

    @_field_validator(
        "unavailable",
        "affirmative",
        "negative",
        "history_disabled_decision",
        "history_write_failed",
        "review_usage",
        "history_disabled",
        "record_missing",
        "history_unavailable",
        "review_version_unavailable",
        "review_match",
        "review_mismatch",
        "review_failed",
    )
    @classmethod
    def _check_not_blank_fields(cls, value: str) -> str:
        return _validate_not_blank(value)


class ScopedConfig(BaseModel):
    """Settings under the ``LAVI__`` dotenv scope."""

    algorithm: str = "random"
    """Registered algorithm name, or ``"random"`` to choose per decision."""

    detailed: bool = False
    """Show the selected decider, operator count and calculation steps."""

    history_limit: int = Field(default=1000, ge=0)
    """Recent decisions kept per data directory; ``0`` pauses history access."""

    text: TextConfig = Field(default_factory=TextConfig)
    """Customizable reply copy under the ``LAVI__TEXT__`` scope."""


class Config(BaseModel):
    """Top-level config holder for NoneBot plugin loading."""

    lavi: ScopedConfig = Field(default_factory=ScopedConfig)
