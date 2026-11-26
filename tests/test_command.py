"""Command-layer field-count handling, record delivery and review."""

import json
from uuid import UUID
from typing import TYPE_CHECKING, Any, NoReturn
from datetime import datetime, timezone

import pytest

if TYPE_CHECKING:
    from pathlib import Path

    from nonebot_plugin_lavi.config import TextConfig
    from nonebot_plugin_lavi.storage import HistoryStore
    from nonebot_plugin_lavi.protocol import (
        Selector,
        Algorithm,
        DecisionRecord,
        DecisionContext,
    )

_TIMESTAMP = datetime(2024, 5, 6, 7, 8, 9, 123456, tzinfo=timezone.utc)
_RECORD_ID = UUID("00000000-0000-4000-8000-000000000001")
_SECOND_ID = UUID("00000000-0000-4000-8000-000000000002")
_ID_A = UUID("00000000-0000-4000-8000-00000000000a")
_ID_B = UUID("00000000-0000-4000-8000-00000000000b")
_ID_C = UUID("00000000-0000-4000-8000-00000000000c")


def _context() -> "DecisionContext":
    from nonebot_plugin_lavi.protocol import DecisionContext

    return DecisionContext(
        timestamp=_TIMESTAMP,
        pid=10,
        nonce1=1,
        nonce2=2,
        nonce3=3,
    )


def _store(tmp_path: "Path", limit: int = 1000) -> "HistoryStore":
    from nonebot_plugin_lavi.storage import HistoryStore

    return HistoryStore(tmp_path, limit)


def _fixed_record_ids(monkeypatch, *record_ids: UUID) -> None:
    import nonebot_plugin_lavi.command as command

    remaining = iter(record_ids)
    monkeypatch.setattr(command, "uuid4", lambda: next(remaining))


def _replace(record: "DecisionRecord", **updates: Any) -> "DecisionRecord":
    from nonebot_plugin_lavi.protocol import DecisionRecord

    fields: dict[str, Any] = {
        "record_id": record.record_id,
        "context": record.context,
        "options": record.options,
        "algorithm": record.algorithm,
        "algorithm_version": record.algorithm_version,
        "display_name": record.display_name,
        "affirmative_wins": record.affirmative_wins,
        "operator_count": record.operator_count,
    }
    fields.update(updates)
    return DecisionRecord(**fields)


def _trial_record(
    record_id: UUID = _RECORD_ID,
    *,
    arguments: str = "红茶 咖啡",
    text: "TextConfig | None" = None,
) -> "DecisionRecord":
    from nonebot_plugin_lavi.config import TextConfig
    from nonebot_plugin_lavi.decision import decide
    from nonebot_plugin_lavi.protocol import DecisionRecord
    from nonebot_plugin_lavi.decider_algorithms import ALGORITHMS

    trial = next(algorithm for algorithm in ALGORITHMS if algorithm.name == "trial")
    configured = text or TextConfig()
    context = _context()
    decision = decide(
        arguments,
        context=context,
        selector=lambda _context: trial,
        options=(configured.affirmative, configured.negative),
    )
    return DecisionRecord(
        record_id=record_id,
        context=context,
        options=decision.options,
        algorithm=decision.algorithm,
        algorithm_version=decision.algorithm_version,
        display_name=decision.display_name,
        affirmative_wins=decision.affirmative_wins,
        operator_count=decision.operator_count,
    )


def _configured_algorithm(result: bool) -> "Algorithm":
    from nonebot_plugin_lavi.protocol import Algorithm

    return Algorithm(
        name="configured",
        version=1,
        weight=1,
        calculate=lambda _: result,
        display_name="配置",
    )


def _counting_algorithm(result: bool) -> tuple["Algorithm", list["DecisionContext"]]:
    from nonebot_plugin_lavi.protocol import Algorithm

    calls: list["DecisionContext"] = []

    def calculate(context: "DecisionContext") -> bool:
        calls.append(context)
        return result

    algorithm = Algorithm(
        name="configured",
        version=1,
        weight=1,
        calculate=calculate,
        display_name="配置",
    )
    return algorithm, calls


def _configured_selector(result: bool) -> "Selector":
    algorithm = _configured_algorithm(result)
    return lambda _: algorithm


def _unused_selector(_: "DecisionContext") -> NoReturn:
    raise AssertionError("configured selector must not be used")


def _fail_context() -> NoReturn:
    raise AssertionError("rejected arguments must not sample a decision context")


def _fail(*_args: object, **_kwargs: object) -> NoReturn:
    raise AssertionError("review must not sample or reselect")


def _reply(body: str, record_id: UUID = _RECORD_ID) -> str:
    return f"{body}\n记录 ID：{record_id}"


@pytest.mark.parametrize("argument", ["missing", "明天会下雨吗？"])
async def test_single_unknown_argument_falls_back_to_configured_selector(
    argument: str, tmp_path, monkeypatch
) -> None:
    import nonebot_plugin_lavi.command as command

    monkeypatch.setattr(command, "capture_context", lambda: _context())
    _fixed_record_ids(monkeypatch, _RECORD_ID)
    store = _store(tmp_path)

    reply = await command.handle_lavi(
        argument,
        history=store,
        selector=_configured_selector(False),
    )

    assert reply == _reply("🔮 决断仪式：「配置」\n✨ 决断结果：「否」")
    record = await store.get(_RECORD_ID)
    assert record is not None
    assert record.options == ("是", "否")
    assert record.affirmative_wins is False


async def test_single_argument_selects_algorithm(tmp_path, monkeypatch) -> None:
    import nonebot_plugin_lavi.command as command
    from nonebot_plugin_lavi.decider_algorithms import ALGORITHMS

    context = _context()
    monkeypatch.setattr(command, "capture_context", lambda: context)
    _fixed_record_ids(monkeypatch, _RECORD_ID)
    trial = next(algorithm for algorithm in ALGORITHMS if algorithm.name == "trial")
    expected = "是" if trial.calculate(context) else "否"

    reply = await command.handle_lavi(
        "trial",
        history=_store(tmp_path),
        selector=_unused_selector,
    )

    assert reply == _reply(f"🔮 决断仪式：「裁判」\n✨ 决断结果：「{expected}」")


async def test_random_is_accepted_as_a_single_argument(tmp_path, monkeypatch) -> None:
    import nonebot_plugin_lavi.command as command
    from nonebot_plugin_lavi.decider_algorithms import ALGORITHMS

    monkeypatch.setattr(command, "capture_context", lambda: _context())
    _fixed_record_ids(monkeypatch, _RECORD_ID)

    reply = await command.handle_lavi(
        "random",
        history=_store(tmp_path),
        selector=_unused_selector,
    )

    assert any(f"「{algorithm.label}」" in reply for algorithm in ALGORITHMS)
    assert reply.endswith(f"记录 ID：{_RECORD_ID}")


async def test_two_arguments_keep_configured_selector_and_candidates(
    tmp_path, monkeypatch
) -> None:
    import nonebot_plugin_lavi.command as command

    monkeypatch.setattr(command, "capture_context", lambda: _context())
    _fixed_record_ids(monkeypatch, _RECORD_ID)
    store = _store(tmp_path)

    reply = await command.handle_lavi(
        "trial 咖啡",
        history=store,
        selector=_configured_selector(False),
    )

    assert reply == _reply("🔮 决断仪式：「配置」\n✨ 决断结果：「咖啡」")
    record = await store.get(_RECORD_ID)
    assert record is not None
    assert record.options == ("trial", "咖啡")


async def test_three_arguments_select_algorithm_and_keep_candidates(
    tmp_path, monkeypatch
) -> None:
    import nonebot_plugin_lavi.command as command
    from nonebot_plugin_lavi.decider_algorithms import ALGORITHMS

    context = _context()
    monkeypatch.setattr(command, "capture_context", lambda: context)
    _fixed_record_ids(monkeypatch, _RECORD_ID)
    trial = next(algorithm for algorithm in ALGORITHMS if algorithm.name == "trial")
    expected = "红茶" if trial.calculate(context) else "咖啡"

    reply = await command.handle_lavi(
        "trial 红茶 咖啡",
        history=_store(tmp_path),
        selector=_unused_selector,
    )

    assert reply == _reply(f"🔮 决断仪式：「裁判」\n✨ 决断结果：「{expected}」")


async def test_three_arguments_reject_unknown_algorithm(tmp_path, monkeypatch) -> None:
    import nonebot_plugin_lavi.command as command

    monkeypatch.setattr(command, "capture_context", _fail_context)

    reply = await command.handle_lavi(
        "missing 红茶 咖啡",
        history=_store(tmp_path),
        selector=_unused_selector,
    )

    assert reply == (
        "⚠️ 未知算法：「missing」\n"
        "可用算法：dayan（大衍）、geomancy（地占）、obi-ifa（宝螺）、"
        "trial（裁判）；random（随机）"
    )
    assert not (tmp_path / "history.json").exists()


async def test_four_or_more_arguments_keep_configured_behavior(
    tmp_path, monkeypatch
) -> None:
    import nonebot_plugin_lavi.command as command

    monkeypatch.setattr(command, "capture_context", lambda: _context())
    _fixed_record_ids(monkeypatch, _RECORD_ID)

    reply = await command.handle_lavi(
        "trial 红茶 咖啡 加奶",
        history=_store(tmp_path),
        selector=_configured_selector(True),
    )

    assert reply == _reply("🔮 决断仪式：「配置」\n✨ 决断结果：「是」")


async def test_detailed_reply_ends_with_the_record_id(tmp_path, monkeypatch) -> None:
    import nonebot_plugin_lavi.command as command

    monkeypatch.setattr(command, "capture_context", lambda: _context())
    _fixed_record_ids(monkeypatch, _RECORD_ID)

    reply = await command.handle_lavi(
        "trial 红茶 咖啡",
        history=_store(tmp_path),
        selector=_unused_selector,
        detailed=True,
    )

    assert "📊 算子数量：13" in reply
    assert "📜 演算过程：" in reply
    assert reply.endswith(f"记录 ID：{_RECORD_ID}")


async def test_custom_text_and_reply_words_are_used(tmp_path, monkeypatch) -> None:
    import nonebot_plugin_lavi.command as command
    from nonebot_plugin_lavi.config import TextConfig

    monkeypatch.setattr(command, "capture_context", lambda: _context())
    _fixed_record_ids(monkeypatch, _RECORD_ID)
    text = TextConfig(
        header="🎴 神谕：「{decider}」",
        result="🎯 结果：「{answer}」",
        affirmative="行",
        negative="不行",
        record_id="记录：{record_id}",
    )

    reply = await command.handle_lavi(
        "",
        history=_store(tmp_path),
        selector=_configured_selector(True),
        text=text,
    )

    assert reply == f"🎴 神谕：「配置」\n🎯 结果：「行」\n记录：{_RECORD_ID}"


async def test_custom_unknown_algorithm_text_is_used(tmp_path, monkeypatch) -> None:
    import nonebot_plugin_lavi.command as command
    from nonebot_plugin_lavi.config import TextConfig

    monkeypatch.setattr(command, "capture_context", _fail_context)
    text = TextConfig(
        unknown_algorithm="❌ 没有「{requested}」",
        available_algorithms="可选：{available}；random（随机）",
    )

    reply = await command.handle_lavi(
        "missing 红茶 咖啡",
        history=_store(tmp_path),
        selector=_unused_selector,
        text=text,
    )

    assert reply == (
        "❌ 没有「missing」\n"
        "可选：dayan（大衍）、geomancy（地占）、obi-ifa（宝螺）、"
        "trial（裁判）；random（随机）"
    )


async def test_history_limit_zero_keeps_the_answer_and_warns(
    tmp_path, monkeypatch
) -> None:
    import nonebot_plugin_lavi.command as command

    monkeypatch.setattr(command, "capture_context", lambda: _context())
    _fixed_record_ids(monkeypatch, _RECORD_ID)
    store = _store(tmp_path, limit=0)

    reply = await command.handle_lavi(
        "红茶 咖啡",
        history=store,
        selector=_configured_selector(True),
    )

    assert (
        reply
        == _reply("🔮 决断仪式：「配置」\n✨ 决断结果：「红茶」")
        + "\n历史记录已关闭，本次决策无法复查。"
    )
    assert not (tmp_path / "history.json").exists()
    assert await store.get(_RECORD_ID) is None


@pytest.mark.parametrize(
    "payload",
    [
        b'{"schema_version": 1, "records": [',
        b'{"schema_version": 2, "records": []}',
    ],
)
async def test_write_failure_keeps_the_answer_and_warns(
    tmp_path, monkeypatch, payload
) -> None:
    import nonebot_plugin_lavi.command as command

    monkeypatch.setattr(command, "capture_context", lambda: _context())
    _fixed_record_ids(monkeypatch, _RECORD_ID)
    path = tmp_path / "history.json"
    path.write_bytes(payload)
    before = path.read_bytes()
    store = _store(tmp_path)

    reply = await command.handle_lavi(
        "红茶 咖啡",
        history=store,
        selector=_configured_selector(True),
    )

    assert reply == (
        "🔮 决断仪式：「配置」\n"
        "✨ 决断结果：「红茶」\n"
        f"记录 ID：{_RECORD_ID}\n"
        "记录未保存，本次决策无法复查。"
    )
    assert path.read_bytes() == before
    assert (
        await command.handle_review(str(_RECORD_ID), history=store)
        == "历史记录暂时不可用，请稍后再试。"
    )


async def test_replace_failure_keeps_the_answer_and_warns(
    tmp_path, monkeypatch
) -> None:
    import nonebot_plugin_lavi.command as command
    from nonebot_plugin_lavi import storage

    monkeypatch.setattr(command, "capture_context", lambda: _context())
    _fixed_record_ids(monkeypatch, _RECORD_ID)
    store = _store(tmp_path)
    await store.append(_trial_record(_ID_A))
    path = tmp_path / "history.json"
    before = path.read_bytes()

    def fail_replace(*_args: object, **_kwargs: object) -> None:
        raise OSError("disk is full")

    monkeypatch.setattr(storage.os, "replace", fail_replace)

    reply = await command.handle_lavi(
        "红茶 咖啡",
        history=store,
        selector=_configured_selector(True),
    )

    assert reply == (
        "🔮 决断仪式：「配置」\n"
        "✨ 决断结果：「红茶」\n"
        f"记录 ID：{_RECORD_ID}\n"
        "记录未保存，本次决策无法复查。"
    )
    assert path.read_bytes() == before
    assert await store.get(_ID_A) is not None


async def test_duplicate_record_id_is_reissued_without_recomputing(
    tmp_path, monkeypatch
) -> None:
    import nonebot_plugin_lavi.command as command

    store = _store(tmp_path)
    await store.append(_trial_record(_RECORD_ID))
    algorithm, calls = _counting_algorithm(True)
    _fixed_record_ids(monkeypatch, _RECORD_ID, _SECOND_ID)
    monkeypatch.setattr(command, "capture_context", lambda: _context())

    reply = await command.handle_lavi(
        "红茶 咖啡",
        history=store,
        selector=lambda _context: algorithm,
    )

    assert reply == _reply(
        "🔮 决断仪式：「配置」\n✨ 决断结果：「红茶」",
        record_id=_SECOND_ID,
    )
    assert calls == [_context()]
    assert await store.get(_RECORD_ID) is not None
    created = await store.get(_SECOND_ID)
    assert created is not None
    assert created.affirmative_wins is True
    assert created.context == _context()


@pytest.mark.parametrize(
    "arguments",
    [
        "",
        "   ",
        "00000000-0000-4000-8000-00000000000",
        f"{_RECORD_ID} {_SECOND_ID}",
        "C:\\records\\00000000-0000-4000-8000-000000000001",
        "00000000-0000-4000-8000-000000000001.txt",
    ],
)
async def test_review_rejects_malformed_identifiers(tmp_path, arguments) -> None:
    import nonebot_plugin_lavi.command as command

    reply = await command.handle_review(arguments, history=_store(tmp_path))

    assert reply == "用法：/lavi-review <记录ID>"


async def test_review_reports_a_missing_record(tmp_path) -> None:
    import nonebot_plugin_lavi.command as command

    store = _store(tmp_path)

    assert (
        await command.handle_review(str(_RECORD_ID), history=store)
        == "记录不存在或已滚动移除。"
    )


async def test_review_reports_disabled_history(tmp_path) -> None:
    import nonebot_plugin_lavi.command as command

    store = _store(tmp_path, limit=0)

    assert (
        await command.handle_review(str(_RECORD_ID), history=store)
        == "历史记录已关闭。"
    )


async def test_review_accepts_an_uppercase_identifier(tmp_path, monkeypatch) -> None:
    import nonebot_plugin_lavi.command as command

    store = _store(tmp_path)
    await store.append(_trial_record())
    monkeypatch.setattr(command, "capture_context", _fail)

    reply = await command.handle_review(str(_RECORD_ID).upper(), history=store)

    assert f"记录 ID：{_RECORD_ID}" in reply
    assert reply.endswith("复查一致。")


async def test_review_replays_without_new_sampling_or_reselection(
    tmp_path, monkeypatch
) -> None:
    import nonebot_plugin_lavi.command as command

    store = _store(tmp_path)
    await store.append(_trial_record())
    before = (tmp_path / "history.json").read_bytes()
    monkeypatch.setattr(command, "capture_context", _fail)
    monkeypatch.setattr(command, "build_selector", _fail)
    monkeypatch.setattr(command, "uuid4", _fail)

    reply = await command.handle_review(str(_RECORD_ID), history=store)

    assert f"记录 ID：{_RECORD_ID}" in reply
    assert f"决策时间：{_TIMESTAMP.isoformat()}" in reply
    assert "原算法：裁判（trial v1）" in reply
    assert "原候选：1「红茶」 / 2「咖啡」" in reply
    assert "原算子数量：13" in reply
    assert "📊 算子数量：13" in reply
    assert "📜 演算过程：" in reply
    assert reply.endswith("复查一致。")
    assert (tmp_path / "history.json").read_bytes() == before


async def test_review_detects_a_flipped_winner_with_identical_options(
    tmp_path,
) -> None:
    import nonebot_plugin_lavi.command as command

    record = _trial_record(arguments="茶 茶")
    flipped = _replace(record, affirmative_wins=not record.affirmative_wins)
    store = _store(tmp_path)
    await store.append(flipped)

    reply = await command.handle_review(str(_RECORD_ID), history=store)

    position = 1 if flipped.affirmative_wins else 2
    assert f"原结果：第 {position} 项「茶」" in reply
    assert "复查不一致。" in reply
    assert reply.endswith("复查不一致。")


async def test_review_detects_an_operator_count_difference(tmp_path) -> None:
    import nonebot_plugin_lavi.command as command

    record = _trial_record()
    modified = _replace(record, operator_count=record.operator_count + 1)
    store = _store(tmp_path)
    await store.append(modified)

    reply = await command.handle_review(str(_RECORD_ID), history=store)

    assert f"原算子数量：{modified.operator_count}" in reply
    assert "复查不一致。" in reply


async def test_review_shows_the_original_when_the_version_is_gone(
    tmp_path,
) -> None:
    import nonebot_plugin_lavi.command as command

    record = _trial_record()
    stale = _replace(record, algorithm_version=99)
    store = _store(tmp_path)
    await store.append(stale)

    reply = await command.handle_review(str(_RECORD_ID), history=store)

    position = 1 if stale.affirmative_wins else 2
    assert "原算法：裁判（trial v99）" in reply
    assert f"原结果：第 {position} 项「{stale.options[position - 1]}」" in reply
    assert reply.endswith("无法复算：原算法版本不可用。")
    assert "演算过程" not in reply


async def test_review_shows_the_original_when_replay_raises(
    tmp_path, monkeypatch
) -> None:
    import nonebot_plugin_lavi.command as command
    from nonebot_plugin_lavi.protocol import Algorithm

    def fail(_context: "DecisionContext") -> bool:
        raise RuntimeError("replay failed")

    broken = Algorithm(name="probe", version=1, weight=1, calculate=fail)
    record = _replace(
        _trial_record(),
        algorithm="probe",
        algorithm_version=1,
        display_name="探测",
    )
    store = _store(tmp_path)
    await store.append(record)
    monkeypatch.setattr(command, "ALGORITHMS", (broken,))

    reply = await command.handle_review(str(_RECORD_ID), history=store)

    position = 1 if record.affirmative_wins else 2
    assert "原算法：探测（probe v1）" in reply
    assert f"原结果：第 {position} 项「{record.options[position - 1]}」" in reply
    assert reply.endswith("复算失败。")
    assert "🔮" not in reply


async def test_review_restores_recorded_options_after_text_changes(
    tmp_path,
) -> None:
    import nonebot_plugin_lavi.command as command
    from nonebot_plugin_lavi.config import TextConfig
    from nonebot_plugin_lavi.decision import decide
    from nonebot_plugin_lavi.protocol import DecisionRecord
    from nonebot_plugin_lavi.decider_algorithms import ALGORITHMS

    trial = next(algorithm for algorithm in ALGORITHMS if algorithm.name == "trial")
    context = _context()
    decision = decide(
        "",
        context=context,
        selector=lambda _context: trial,
        options=("行 吧", "不 行"),
    )
    record = DecisionRecord(
        record_id=_RECORD_ID,
        context=context,
        options=decision.options,
        algorithm=decision.algorithm,
        algorithm_version=decision.algorithm_version,
        display_name=decision.display_name,
        affirmative_wins=decision.affirmative_wins,
        operator_count=decision.operator_count,
    )
    store = _store(tmp_path)
    await store.append(record)
    changed = TextConfig(affirmative="好", negative="不好")

    reply = await command.handle_review(
        str(_RECORD_ID),
        history=store,
        text=changed,
    )

    position = 1 if decision.affirmative_wins else 2
    assert "原候选：1「行 吧」 / 2「不 行」" in reply
    assert f"原结果：第 {position} 项「{decision.options[position - 1]}」" in reply
    assert reply.endswith("复查一致。")


async def test_rolling_limit_removes_the_oldest_review(tmp_path) -> None:
    import nonebot_plugin_lavi.command as command

    store = _store(tmp_path, limit=2)
    await store.append(_trial_record(_ID_A))
    await store.append(_trial_record(_ID_B))
    assert (await command.handle_review(str(_ID_A), history=store)).endswith(
        "复查一致。"
    )

    reopened = _store(tmp_path, limit=2)
    await reopened.append(_trial_record(_ID_C))

    assert (
        await command.handle_review(str(_ID_A), history=reopened)
        == "记录不存在或已滚动移除。"
    )
    assert (await command.handle_review(str(_ID_B), history=reopened)).endswith(
        "复查一致。"
    )
    assert (await command.handle_review(str(_ID_C), history=reopened)).endswith(
        "复查一致。"
    )


async def test_lavi_review_arguments_are_two_candidates(tmp_path, monkeypatch) -> None:
    import nonebot_plugin_lavi.command as command

    monkeypatch.setattr(command, "capture_context", lambda: _context())
    _fixed_record_ids(monkeypatch, _RECORD_ID)

    reply = await command.handle_lavi(
        "review 咖啡",
        history=_store(tmp_path),
        selector=_configured_selector(False),
    )

    assert reply == _reply("🔮 决断仪式：「配置」\n✨ 决断结果：「咖啡」")


async def test_history_file_keeps_a_stable_json_shape(tmp_path) -> None:
    store = _store(tmp_path)
    record = _trial_record()
    await store.append(record)

    raw = json.loads((tmp_path / "history.json").read_text(encoding="utf-8"))

    assert set(raw) == {"schema_version", "records"}
    assert set(raw["records"][0]) == {
        "record_id",
        "context",
        "options",
        "algorithm",
        "algorithm_version",
        "display_name",
        "affirmative_wins",
        "operator_count",
    }
