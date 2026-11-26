"""Atomic rolling storage for recent decision records."""

import os
import asyncio
import tempfile
from uuid import UUID
from typing import Literal
from pathlib import Path

from filelock import Timeout, FileLock
from pydantic import BaseModel, ValidationError
from nonebot.compat import PYDANTIC_V2

from .protocol import DecisionRecord

LOCK_TIMEOUT = 5.0


class HistoryUnavailable(RuntimeError):
    """The history file cannot be read or written safely."""


class DuplicateRecordId(RuntimeError):
    """A record with the same identifier is already stored."""

    def __init__(self, record_id: UUID) -> None:
        super().__init__(f"duplicate record id: {record_id}")
        self.record_id = record_id


class _HistoryFile(BaseModel):
    schema_version: Literal[1]
    records: list[DecisionRecord]


def _parse_history(payload: bytes) -> _HistoryFile:
    if PYDANTIC_V2:
        return _HistoryFile.model_validate_json(payload)
    return _HistoryFile.parse_raw(payload)


def _dump_history(records: list[DecisionRecord]) -> bytes:
    history = _HistoryFile(schema_version=1, records=records)
    if PYDANTIC_V2:
        return history.model_dump_json().encode()
    return history.json().encode()


class HistoryStore:
    """Rolling history of recent decisions in one data directory.

    All disk access runs in a worker thread under one cross-process lock, so
    concurrent writers in this or another process cannot drop records. The
    file is validated as a whole before any write; a damaged file is never
    treated as empty or overwritten. A non-positive limit disables access and
    leaves the existing file untouched.
    """

    def __init__(self, data_dir: Path, limit: int) -> None:
        if limit < 0:
            raise ValueError("history limit must be non-negative")
        self.limit = limit
        self._path = data_dir / "history.json"
        self._lock_path = data_dir / "history.json.lock"

    async def append(self, record: DecisionRecord) -> None:
        """Store one record, trimming the file to the newest ``limit``."""
        await asyncio.to_thread(self._append_blocking, record)

    async def get(self, record_id: UUID) -> DecisionRecord | None:
        """Return one record from the active window without reordering."""
        return await asyncio.to_thread(self._get_blocking, record_id)

    def _append_blocking(self, record: DecisionRecord) -> None:
        if self.limit <= 0:
            raise HistoryUnavailable("history is disabled")
        try:
            with FileLock(str(self._lock_path), timeout=LOCK_TIMEOUT):
                records = self._load_blocking()
                if any(stored.record_id == record.record_id for stored in records):
                    raise DuplicateRecordId(record.record_id)
                records.append(record)
                self._write_blocking(records[-self.limit :])
        except (Timeout, OSError) as error:
            raise HistoryUnavailable("history is unavailable") from error

    def _get_blocking(self, record_id: UUID) -> DecisionRecord | None:
        if self.limit <= 0:
            return None
        try:
            with FileLock(str(self._lock_path), timeout=LOCK_TIMEOUT):
                records = self._load_blocking()[-self.limit :]
        except (Timeout, OSError) as error:
            raise HistoryUnavailable("history is unavailable") from error
        for record in records:
            if record.record_id == record_id:
                return record
        return None

    def _load_blocking(self) -> list[DecisionRecord]:
        try:
            payload = self._path.read_bytes()
        except FileNotFoundError:
            return []
        except OSError as error:
            raise HistoryUnavailable("history file cannot be read") from error
        if not payload.strip():
            raise HistoryUnavailable("history file is empty")
        try:
            history = _parse_history(payload)
        except ValidationError as error:
            raise HistoryUnavailable("history file is invalid") from error
        records = list(history.records)
        seen: set[UUID] = set()
        for record in records:
            if record.record_id in seen:
                raise HistoryUnavailable("history file has duplicate record ids")
            seen.add(record.record_id)
        return records

    def _write_blocking(self, records: list[DecisionRecord]) -> None:
        payload = _dump_history(records)
        temporary: Path | None = None
        try:
            with tempfile.NamedTemporaryFile(
                "wb",
                dir=self._path.parent,
                prefix="history.",
                suffix=".tmp",
                delete=False,
            ) as handle:
                temporary = Path(handle.name)
                handle.write(payload)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temporary, self._path)
            temporary = None
        finally:
            if temporary is not None:
                try:
                    temporary.unlink(missing_ok=True)
                except OSError:
                    pass
