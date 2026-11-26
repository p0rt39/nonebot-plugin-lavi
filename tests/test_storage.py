"""Atomic rolling persistence for decision records."""

import json
import asyncio
from uuid import UUID
from typing import TYPE_CHECKING, Any
from datetime import datetime, timezone, timedelta

import pytest
from pydantic import ValidationError

if TYPE_CHECKING:
    from pathlib import Path

    from nonebot_plugin_lavi.protocol import DecisionRecord, DecisionContext

_TIMESTAMP = datetime(2024, 5, 6, 7, 8, 9, 123456, tzinfo=timezone.utc)
_ID_A = UUID("00000000-0000-4000-8000-00000000000a")
_ID_B = UUID("00000000-0000-4000-8000-00000000000b")
_ID_C = UUID("00000000-0000-4000-8000-00000000000c")
_ID_D = UUID("00000000-0000-4000-8000-00000000000d")


def _context() -> "DecisionContext":
    from nonebot_plugin_lavi.protocol import DecisionContext

    return DecisionContext(
        timestamp=_TIMESTAMP,
        pid=10,
        nonce1=(1 << 63) + 1,
        nonce2=2,
        nonce3=3,
    )


def _record(record_id: UUID, **overrides: Any) -> "DecisionRecord":
    from nonebot_plugin_lavi.protocol import DecisionRecord

    fields: dict[str, Any] = {
        "record_id": record_id,
        "context": _context(),
        "options": ("红茶", "咖啡"),
        "algorithm": "trial",
        "algorithm_version": 1,
        "display_name": "裁判",
        "affirmative_wins": True,
        "operator_count": 13,
    }
    fields.update(overrides)
    return DecisionRecord(**fields)


def _store(data_dir: Path, limit: int = 1000):
    from nonebot_plugin_lavi.storage import HistoryStore

    return HistoryStore(data_dir, limit)


def _file(data_dir: Path) -> Path:
    return data_dir / "history.json"


async def test_append_then_get_roundtrips_every_field(tmp_path) -> None:
    store = _store(tmp_path)
    record = _record(_ID_A)

    await store.append(record)

    loaded = await store.get(_ID_A)

    assert loaded == record
    assert loaded is not None
    assert loaded.context.timestamp == _TIMESTAMP
    assert loaded.context.timestamp.microsecond == 123456
    assert loaded.context.pid == 10
    assert loaded.context.nonce1 == (1 << 63) + 1
    raw = json.loads(_file(tmp_path).read_text(encoding="utf-8"))
    assert raw["schema_version"] == 1
    assert raw["records"][0]["record_id"] == str(_ID_A)
    assert raw["records"][0]["record_id"] == str(_ID_A).lower()
    assert "123456" in raw["records"][0]["context"]["timestamp"]


async def test_missing_file_reads_as_empty_and_first_append_creates_it(
    tmp_path,
) -> None:
    store = _store(tmp_path)

    assert await store.get(_ID_A) is None
    assert not _file(tmp_path).exists()

    await store.append(_record(_ID_A))

    assert _file(tmp_path).exists()
    assert await store.get(_ID_A) is not None


async def test_append_keeps_newest_records_in_order(tmp_path) -> None:
    store = _store(tmp_path)

    await store.append(_record(_ID_A))
    await store.append(_record(_ID_B))
    await store.append(_record(_ID_C))

    raw = json.loads(_file(tmp_path).read_text(encoding="utf-8"))
    assert [item["record_id"] for item in raw["records"]] == [
        str(_ID_A),
        str(_ID_B),
        str(_ID_C),
    ]


async def test_limit_trims_the_oldest_record_on_append(tmp_path) -> None:
    store = _store(tmp_path, limit=2)
    await store.append(_record(_ID_A))
    await store.append(_record(_ID_B))

    assert await store.get(_ID_A) is not None

    await store.append(_record(_ID_C))

    assert await store.get(_ID_A) is None
    assert await store.get(_ID_B) is not None
    assert await store.get(_ID_C) is not None
    raw = json.loads(_file(tmp_path).read_text(encoding="utf-8"))
    assert [item["record_id"] for item in raw["records"]] == [
        str(_ID_B),
        str(_ID_C),
    ]


async def test_lowered_limit_windows_reads_until_the_next_append(tmp_path) -> None:
    writer = _store(tmp_path)
    for record_id in (_ID_A, _ID_B, _ID_C):
        await writer.append(_record(record_id))
    before = _file(tmp_path).read_bytes()

    smaller = _store(tmp_path, limit=2)

    assert await smaller.get(_ID_A) is None
    assert await smaller.get(_ID_B) is not None
    assert await smaller.get(_ID_C) is not None
    assert _file(tmp_path).read_bytes() == before

    await smaller.append(_record(_ID_D))

    raw = json.loads(_file(tmp_path).read_text(encoding="utf-8"))
    assert [item["record_id"] for item in raw["records"]] == [
        str(_ID_C),
        str(_ID_D),
    ]


async def test_duplicate_incoming_id_is_rejected_without_writing(tmp_path) -> None:
    from nonebot_plugin_lavi.storage import DuplicateRecordId

    store = _store(tmp_path)
    await store.append(_record(_ID_A))
    before = _file(tmp_path).read_bytes()

    with pytest.raises(DuplicateRecordId):
        await store.append(_record(_ID_A, affirmative_wins=False))

    assert _file(tmp_path).read_bytes() == before
    loaded = await store.get(_ID_A)
    assert loaded is not None
    assert loaded.affirmative_wins is True


async def test_existing_duplicate_ids_make_history_unavailable(tmp_path) -> None:
    from nonebot_plugin_lavi.storage import HistoryUnavailable

    store = _store(tmp_path)
    await store.append(_record(_ID_A))
    raw = json.loads(_file(tmp_path).read_text(encoding="utf-8"))
    raw["records"].append(raw["records"][0])
    _file(tmp_path).write_text(json.dumps(raw), encoding="utf-8")
    before = _file(tmp_path).read_bytes()

    with pytest.raises(HistoryUnavailable):
        await store.get(_ID_A)

    with pytest.raises(HistoryUnavailable):
        await store.append(_record(_ID_B))

    assert _file(tmp_path).read_bytes() == before


@pytest.mark.parametrize(
    "payload",
    [
        b"",
        b"   \n\t",
        b'{"schema_version": 1, "records": [',
        b'{"schema_version": 2, "records": []}',
        b"{}",
        b'{"schema_version": 1, "records": [{"record_id": "nope"}]}',
    ],
)
async def test_unreadable_files_are_never_overwritten(tmp_path, payload) -> None:
    from nonebot_plugin_lavi.storage import HistoryUnavailable

    _file(tmp_path).write_bytes(payload)
    store = _store(tmp_path)

    with pytest.raises(HistoryUnavailable):
        await store.get(_ID_A)

    with pytest.raises(HistoryUnavailable):
        await store.append(_record(_ID_A))

    assert _file(tmp_path).read_bytes() == payload


async def test_limit_zero_disables_access_and_preserves_the_file(tmp_path) -> None:
    from nonebot_plugin_lavi.storage import HistoryUnavailable

    writer = _store(tmp_path, limit=5)
    await writer.append(_record(_ID_A))
    before = _file(tmp_path).read_bytes()

    paused = _store(tmp_path, limit=0)

    assert await paused.get(_ID_A) is None
    with pytest.raises(HistoryUnavailable):
        await paused.append(_record(_ID_B))
    assert _file(tmp_path).read_bytes() == before

    resumed = _store(tmp_path, limit=5)

    assert await resumed.get(_ID_A) is not None
    assert await resumed.get(_ID_B) is None


async def test_get_never_rewrites_the_file(tmp_path) -> None:
    store = _store(tmp_path)
    await store.append(_record(_ID_A))
    before = _file(tmp_path).read_bytes()

    assert await store.get(_ID_A) is not None
    assert await store.get(_ID_B) is None
    assert _file(tmp_path).read_bytes() == before


async def test_concurrent_stores_keep_every_record(tmp_path) -> None:
    record_ids = [
        UUID(f"00000000-0000-4000-8000-{index:012d}") for index in range(1, 9)
    ]
    stores = [_store(tmp_path, limit=100) for _ in record_ids]

    await asyncio.gather(
        *(
            store.append(_record(record_id))
            for store, record_id in zip(stores, record_ids)
        )
    )

    fresh = _store(tmp_path, limit=100)
    for record_id in record_ids:
        assert await fresh.get(record_id) is not None


async def test_atomic_replace_failure_preserves_the_previous_file(
    tmp_path, monkeypatch
) -> None:
    from nonebot_plugin_lavi import storage

    store = _store(tmp_path)
    await store.append(_record(_ID_A))
    before = _file(tmp_path).read_bytes()

    def fail_replace(*_args: object, **_kwargs: object) -> None:
        raise OSError("disk is full")

    monkeypatch.setattr(storage.os, "replace", fail_replace)

    with pytest.raises(storage.HistoryUnavailable):
        await store.append(_record(_ID_B))

    assert _file(tmp_path).read_bytes() == before
    assert list(tmp_path.glob("history.*.tmp")) == []
    assert await store.get(_ID_A) is not None


def test_negative_limit_is_rejected(tmp_path) -> None:
    with pytest.raises(ValueError, match="non-negative"):
        _store(tmp_path, limit=-1)


@pytest.mark.parametrize(
    "context",
    [
        {"timestamp": _TIMESTAMP, "pid": 10},
        {
            "timestamp": _TIMESTAMP.replace(tzinfo=timezone(timedelta(hours=8))),
            "pid": 10,
            "nonce1": 1,
            "nonce2": 2,
            "nonce3": 3,
        },
    ],
)
def test_record_requires_a_complete_utc_context(context: dict[str, Any]) -> None:
    from nonebot_plugin_lavi.protocol import DecisionContext

    with pytest.raises(ValidationError):
        _record(_ID_A, context=DecisionContext(**context))
