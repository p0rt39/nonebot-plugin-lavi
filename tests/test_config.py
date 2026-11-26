"""Configuration model constraints for customizable reply copy."""

import pytest


def test_scoped_config_builds_nested_text_config() -> None:
    from nonebot_plugin_lavi.config import TextConfig, ScopedConfig

    text = TextConfig(header="🎴 神谕：「{decider}」")

    config = ScopedConfig(text=text)

    assert config.text.header == "🎴 神谕：「{decider}」"


def test_dotenv_nested_keys_populate_text_config(monkeypatch) -> None:
    from nonebot import get_plugin_config

    from nonebot_plugin_lavi.config import Config

    monkeypatch.setenv("LAVI__TEXT__HEADER", "🎴 神谕：「{decider}」")
    monkeypatch.setenv("LAVI__TEXT__AFFIRMATIVE", "行")
    monkeypatch.setenv("LAVI__TEXT__STEPS_HEADER", "")

    config = get_plugin_config(Config)

    assert config.lavi.text.header == "🎴 神谕：「{decider}」"
    assert config.lavi.text.affirmative == "行"
    assert config.lavi.text.steps_header == ""


def test_invalid_dotenv_template_fails_config_loading(monkeypatch) -> None:
    from nonebot import get_plugin_config
    from pydantic import ValidationError

    from nonebot_plugin_lavi.config import Config

    monkeypatch.setenv("LAVI__TEXT__HEADER", "没有占位符")

    with pytest.raises(ValidationError):
        get_plugin_config(Config)


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("header", "🎴 神谕"),
        ("result", "🎯 结果"),
        ("operator_count", "📊 算子"),
        ("unknown_algorithm", "❌ 未知"),
        ("available_algorithms", "可选算法"),
        ("record_id", "记录 ID"),
        ("record_time", "决策时间"),
        ("record_algorithm", "原算法"),
        ("record_options", "原候选"),
        ("record_result", "原结果"),
        ("record_count", "原算子数量"),
    ],
)
def test_template_fields_require_their_placeholder(field: str, value: str) -> None:
    from pydantic import ValidationError

    from nonebot_plugin_lavi.config import TextConfig

    with pytest.raises(ValidationError):
        TextConfig(**{field: value})


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("header", "🎴 {decider.name}"),
        ("result", "🎯 {other}"),
        ("operator_count", "📊 {operator_count!r}"),
        ("unknown_algorithm", "❌ {requested:>8}"),
        ("available_algorithms", "可选 {available"),
        ("record_id", "记录 {record_id!r}"),
        ("record_time", "时间 {when}"),
        ("record_count", "数量 {operator_count:>4}"),
    ],
)
def test_template_fields_reject_unsupported_syntax(field: str, value: str) -> None:
    from pydantic import ValidationError

    from nonebot_plugin_lavi.config import TextConfig

    with pytest.raises(ValidationError):
        TextConfig(**{field: value})


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("unavailable", " \n\t "),
        ("affirmative", ""),
        ("negative", "  "),
        ("history_disabled_decision", " "),
        ("history_write_failed", ""),
        ("review_usage", "\n"),
        ("history_disabled", "  "),
        ("record_missing", ""),
        ("history_unavailable", " "),
        ("review_version_unavailable", ""),
        ("review_match", " "),
        ("review_mismatch", ""),
        ("review_failed", "\t"),
    ],
)
def test_plain_copy_fields_reject_blank_values(field: str, value: str) -> None:
    from pydantic import ValidationError

    from nonebot_plugin_lavi.config import TextConfig

    with pytest.raises(ValidationError):
        TextConfig(**{field: value})


def test_empty_steps_header_is_allowed() -> None:
    from nonebot_plugin_lavi.config import TextConfig

    assert TextConfig(steps_header="").steps_header == ""


def test_escaped_braces_are_accepted_in_templates() -> None:
    from nonebot_plugin_lavi.config import TextConfig

    text = TextConfig(header="{{LaVI}} 「{decider}」")

    assert text.header == "{{LaVI}} 「{decider}」"


def test_history_limit_defaults_to_one_thousand() -> None:
    from nonebot_plugin_lavi.config import ScopedConfig

    assert ScopedConfig().history_limit == 1000


def test_dotenv_history_limit_is_parsed(monkeypatch) -> None:
    from nonebot import get_plugin_config

    from nonebot_plugin_lavi.config import Config

    monkeypatch.setenv("LAVI__HISTORY_LIMIT", "2")

    assert get_plugin_config(Config).lavi.history_limit == 2


def test_negative_history_limit_is_rejected(monkeypatch) -> None:
    from nonebot import get_plugin_config
    from pydantic import ValidationError

    from nonebot_plugin_lavi.config import Config

    monkeypatch.setenv("LAVI__HISTORY_LIMIT", "-1")

    with pytest.raises(ValidationError):
        get_plugin_config(Config)
