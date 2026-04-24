from __future__ import annotations

import json
import os
import re
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Iterator

if os.name == "nt":
    import msvcrt
else:
    import fcntl


SAFE_SESSION_ID = re.compile(r"^[A-Za-z0-9_.-]+$")


class FileSessionStore:
    def __init__(self, repo_root: Path) -> None:
        self.repo_root = repo_root
        self.session_dir = repo_root / ".harness" / "sessions"
        self.session_dir.mkdir(parents=True, exist_ok=True)
        self.lock_path = self.session_dir / ".sessions.lock"

    def _session_path(self, session_id: str) -> Path:
        if not session_id or not SAFE_SESSION_ID.fullmatch(session_id):
            raise ValueError("Session IDs may only contain letters, numbers, dot, underscore, and dash.")
        return self.session_dir / f"{session_id}.jsonl"

    def _read_events_unlocked(self, session_id: str) -> list[dict[str, Any]]:
        path = self._session_path(session_id)
        if not path.exists():
            return []
        return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]

    def _append_event_unlocked(
        self,
        *,
        session_id: str,
        event_type: str,
        payload: dict[str, Any],
        events: list[dict[str, Any]],
    ) -> dict[str, Any]:
        event = {
            "sequence": len(events) + 1,
            "timestamp": datetime.now(UTC).isoformat(),
            "event_type": event_type,
            "payload": payload,
        }
        path = self._session_path(session_id)
        with path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(event, ensure_ascii=False) + "\n")
        return event

    @contextmanager
    def _locked_sessions(self) -> Iterator[None]:
        self.session_dir.mkdir(parents=True, exist_ok=True)
        with self.lock_path.open("a+b") as lock_file:
            lock_file.seek(0)
            if os.name == "nt":
                msvcrt.locking(lock_file.fileno(), msvcrt.LK_LOCK, 1)
            else:
                fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX)
            try:
                yield
            finally:
                lock_file.seek(0)
                if os.name == "nt":
                    msvcrt.locking(lock_file.fileno(), msvcrt.LK_UNLCK, 1)
                else:
                    fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)

    def get_events(self, session_id: str, cursor: int | None = None) -> list[dict[str, Any]]:
        events = self._read_events_unlocked(session_id)
        if cursor is None:
            return events
        return [event for event in events if int(event.get("sequence", 0)) > cursor]

    def emit_event(self, session_id: str, event_type: str, payload: dict[str, Any]) -> dict[str, Any]:
        with self._locked_sessions():
            events = self._read_events_unlocked(session_id)
            return self._append_event_unlocked(
                session_id=session_id,
                event_type=event_type,
                payload=payload,
                events=events,
            )

    def emit_event_if(
        self,
        session_id: str,
        event_type: str,
        payload: dict[str, Any],
        predicate: Any,
    ) -> dict[str, Any] | None:
        """Emit one event only if predicate still passes under the session lock."""

        with self._locked_sessions():
            events = self._read_events_unlocked(session_id)
            if not predicate(events):
                return None
            return self._append_event_unlocked(
                session_id=session_id,
                event_type=event_type,
                payload=payload,
                events=events,
            )

    def latest_event(self, session_id: str, event_type: str | None = None, turn_id: str | None = None) -> dict[str, Any] | None:
        for event in reversed(self.get_events(session_id)):
            if event_type and event["event_type"] != event_type:
                continue
            if turn_id and event["payload"].get("turn_id") != turn_id:
                continue
            return event
        return None
