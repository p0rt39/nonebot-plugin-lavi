"""Rendering for decision answers and detailed traces."""


def test_unknown_algorithm_lists_available_choices() -> None:
    from nonebot_plugin_lavi.render import render_unknown_algorithm

    assert render_unknown_algorithm(
        "missing",
        available=("dayan（大衍）", "trial（裁判）"),
    ) == (
        "⚠️ 未知算法：「missing」\n"
        "可用算法：dayan（大衍）、trial（裁判）；random（随机）"
    )


def test_answer_is_rendered_as_ritual_heading_and_result() -> None:
    from nonebot_plugin_lavi.render import render_answer

    assert (
        render_answer("是", decider="大衍")
        == "🔮 决断仪式：「大衍」\n✨ 决断结果：「是」"
    )
    assert (
        render_answer("红茶", decider="地占")
        == "🔮 决断仪式：「地占」\n✨ 决断结果：「红茶」"
    )


def test_answer_whitespace_is_collapsed_within_its_line() -> None:
    from nonebot_plugin_lavi.render import render_answer

    assert (
        render_answer("  红茶\n咖啡  ", decider="宝螺")
        == "🔮 决断仪式：「宝螺」\n✨ 决断结果：「红茶 咖啡」"
    )


def test_answer_text_is_preserved_verbatim_apart_from_whitespace() -> None:
    from nonebot_plugin_lavi.render import render_answer

    assert (
        render_answer("Earl-Grey！", decider="裁判")
        == "🔮 决断仪式：「裁判」\n✨ 决断结果：「Earl-Grey！」"
    )


def test_detailed_reply_separates_concise_and_detail_blocks() -> None:
    from nonebot_plugin_lavi.render import render_detailed

    result = render_detailed("红茶", decider="大衍", operator_count=24)

    assert result == ("🔮 决断仪式：「大衍」\n✨ 决断结果：「红茶」\n\n📊 算子数量：24")
    assert "演算过程" not in result


def test_detailed_reply_lists_calculation_steps_under_a_header() -> None:
    from nonebot_plugin_lavi.render import render_detailed

    result = render_detailed(
        "红茶",
        decider="大衍",
        operator_count=24,
        steps=("初爻：去 5+8+8，余 28，28÷4=7（阳）", "阳爻 3 枚 → 肯定"),
    )

    assert result == (
        "🔮 决断仪式：「大衍」\n"
        "✨ 决断结果：「红茶」\n"
        "\n"
        "📊 算子数量：24\n"
        "📜 演算过程：\n"
        "初爻：去 5+8+8，余 28，28÷4=7（阳）\n"
        "阳爻 3 枚 → 肯定"
    )


def test_custom_templates_replace_the_default_copy() -> None:
    from nonebot_plugin_lavi.config import TextConfig
    from nonebot_plugin_lavi.render import render_answer

    text = TextConfig(
        header="🎴 神谕：「{decider}」",
        result="🎯 结果：「{answer}」",
    )

    assert (
        render_answer("  红茶\n咖啡  ", decider="大衍", text=text)
        == "🎴 神谕：「大衍」\n🎯 结果：「红茶 咖啡」"
    )


def test_custom_detailed_labels_and_empty_steps_header() -> None:
    from nonebot_plugin_lavi.config import TextConfig
    from nonebot_plugin_lavi.render import render_detailed

    text = TextConfig(
        operator_count="🧮 {operator_count} 个算子",
        steps_header="",
    )

    result = render_detailed(
        "是",
        decider="裁判",
        operator_count=13,
        steps=("主算子：0x2a", "13 票 → 肯定"),
        text=text,
    )

    assert result == (
        "🔮 决断仪式：「裁判」\n"
        "✨ 决断结果：「是」\n"
        "\n"
        "🧮 13 个算子\n"
        "主算子：0x2a\n"
        "13 票 → 肯定"
    )


def test_custom_unknown_algorithm_copy_uses_both_placeholders() -> None:
    from nonebot_plugin_lavi.config import TextConfig
    from nonebot_plugin_lavi.render import render_unknown_algorithm

    text = TextConfig(
        unknown_algorithm="❌ 没有「{requested}」这个算法",
        available_algorithms="可用的有：{available}",
    )

    assert render_unknown_algorithm(
        "missing",
        available=("dayan（大衍）", "trial（裁判）"),
        text=text,
    ) == ("❌ 没有「missing」这个算法\n可用的有：dayan（大衍）、trial（裁判）")


def test_doubled_braces_render_literally() -> None:
    from nonebot_plugin_lavi.config import TextConfig
    from nonebot_plugin_lavi.render import render_answer

    text = TextConfig(header="{{LaVI}} 「{decider}」")

    assert (
        render_answer("是", decider="大衍", text=text)
        == "{LaVI} 「大衍」\n✨ 决断结果：「是」"
    )
