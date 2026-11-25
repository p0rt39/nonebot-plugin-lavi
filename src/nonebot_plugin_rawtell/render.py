"""Render decision answers and detailed traces as adapter-safe text."""

HEADER = "🔮 决断仪式"


def _single_line(text: str) -> str:
    return " ".join(text.split())


def render_answer(answer: str, *, decider: str) -> str:
    """Return the ritual heading and a clearly labelled result."""
    return (
        f"{HEADER}：「{_single_line(decider)}」\n"
        f"✨ 决断结果：「{_single_line(answer)}」"
    )


def render_detailed(
    answer: str,
    *,
    decider: str,
    operator_count: int,
    steps: tuple[str, ...] = (),
) -> str:
    """Separate concise text from the operator count and optional steps."""
    lines = [
        render_answer(answer, decider=decider),
        "",
        f"📊 算子数量：{operator_count}",
    ]
    if steps:
        lines.append("📜 演算过程：")
        lines.extend(_single_line(step) for step in steps)
    return "\n".join(lines)
