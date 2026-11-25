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
