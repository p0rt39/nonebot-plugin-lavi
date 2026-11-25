"""Rendering for decision answers and detailed traces."""


def test_unknown_algorithm_lists_available_choices() -> None:
    from nonebot_plugin_rawtell.render import render_unknown_algorithm

    assert render_unknown_algorithm(
        "missing",
        available=("dayan（大衍）", "trial（裁判）"),
    ) == (
        "⚠️ 未知算法：「missing」\n"
        "可用算法：dayan（大衍）、trial（裁判）；random（随机）"
    )


def test_answer_is_rendered_as_ritual_heading_and_result() -> None:
    from nonebot_plugin_rawtell.render import render_answer

    assert (
        render_answer("是", decider="大衍")
        == "🔮 决断仪式：「大衍」\n✨ 决断结果：「是」"
    )
    assert (
        render_answer("红茶", decider="地占")
        == "🔮 决断仪式：「地占」\n✨ 决断结果：「红茶」"
    )


def test_answer_whitespace_is_collapsed_within_its_line() -> None:
    from nonebot_plugin_rawtell.render import render_answer

    assert (
        render_answer("  红茶\n咖啡  ", decider="宝螺")
        == "🔮 决断仪式：「宝螺」\n✨ 决断结果：「红茶 咖啡」"
    )


def test_answer_text_is_preserved_verbatim_apart_from_whitespace() -> None:
    from nonebot_plugin_rawtell.render import render_answer

    assert (
        render_answer("Earl-Grey！", decider="裁判")
        == "🔮 决断仪式：「裁判」\n✨ 决断结果：「Earl-Grey！」"
    )


def test_detailed_reply_separates_concise_and_detail_blocks() -> None:
    from nonebot_plugin_rawtell.render import render_detailed

    result = render_detailed("红茶", decider="大衍", operator_count=24)

    assert result == ("🔮 决断仪式：「大衍」\n✨ 决断结果：「红茶」\n\n📊 算子数量：24")
    assert "演算过程" not in result


def test_detailed_reply_lists_calculation_steps_under_a_header() -> None:
    from nonebot_plugin_rawtell.render import render_detailed

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
