from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

from .flow_contract import ExecutionFlowVerifier
from .runtime import HarnessRuntime


class WorkOrchestrator:
    """Small durable queue coordinator outside the runtime loop."""

    def __init__(self, runtime: HarnessRuntime) -> None:
        self.runtime = runtime
        self.store = runtime.store
        self.flow = ExecutionFlowVerifier(self.store)

    def _new_work_item_id(self) -> str:
        return f"work_{uuid.uuid4().hex[:12]}"

    def _new_worker_id(self) -> str:
        return f"worker_{uuid.uuid4().hex[:12]}"

    def _now(self, now: datetime | None = None) -> datetime:
        return now or datetime.now(UTC)

    def _parse_time(self, value: Any) -> datetime | None:
        if not value:
            return None
        try:
            parsed = datetime.fromisoformat(str(value))
        except ValueError:
            return None
        if parsed.tzinfo is None:
            return parsed.replace(tzinfo=UTC)
        return parsed

    def _retry_delay_seconds(self, attempt: int) -> int:
        return min(60, 2 ** max(attempt - 1, 0))

    def _is_work_claimable(
        self,
        *,
        events: list[dict[str, Any]],
        work_item_id: str,
        now: datetime,
    ) -> bool:
        queued: dict[str, Any] | None = None
        for event in events:
            payload = event.get("payload", {})
            if payload.get("work_item_id") != work_item_id:
                continue
            if event["event_type"] == "work.queued":
                queued = payload
            if event["event_type"] in {"work.completed", "work.failed", "work.cancelled"}:
                return False
            if event["event_type"] in {"work.lease_acquired", "work.started"}:
                lease_expires_at = self._parse_time(payload.get("lease_expires_at"))
                if lease_expires_at and lease_expires_at > now:
                    return False
        if queued is None:
            return False
        available_at = self._parse_time(queued.get("available_at"))
        return not (available_at and available_at > now)

    def enqueue_continue_turn(
        self,
        *,
        session_id: str,
        turn_id: str,
        reason: str = "continue_turn",
        max_attempts: int = 2,
    ) -> dict[str, Any]:
        work_item = {
            "turn_id": turn_id,
            "work_item_id": self._new_work_item_id(),
            "kind": "continue_turn",
            "status": "queued",
            "attempt": 1,
            "max_attempts": max_attempts,
            "reason": reason,
        }
        return self.store.emit_event(session_id, "work.queued", work_item)["payload"]

    def cancel_work(
        self,
        *,
        session_id: str,
        work_item_id: str,
        reason: str = "operator_cancelled",
    ) -> dict[str, Any]:
        return self.store.emit_event(
            session_id,
            "work.cancelled",
            {
                "work_item_id": work_item_id,
                "status": "cancelled",
                "reason": reason,
            },
        )["payload"]

    def acquire_lease(
        self,
        *,
        session_id: str,
        work_item: dict[str, Any],
        worker_id: str | None = None,
        lease_seconds: int = 300,
        now: datetime | None = None,
    ) -> dict[str, Any]:
        current = self._now(now)
        lease = {
            **work_item,
            "worker_id": worker_id or self._new_worker_id(),
            "lease_seconds": lease_seconds,
            "lease_expires_at": (current + timedelta(seconds=lease_seconds)).isoformat(),
            "status": "leased",
        }
        work_item_id = str(work_item["work_item_id"])
        event = self.store.emit_event_if(
            session_id,
            "work.lease_acquired",
            lease,
            lambda events: self._is_work_claimable(events=events, work_item_id=work_item_id, now=current),
        )
        if event is None:
            return {
                **work_item,
                "status": "lease_denied",
                "worker_id": lease["worker_id"],
                "reason": "work_item_not_claimable",
            }
        return event["payload"]

    def pending_work(self, *, session_id: str, now: datetime | None = None) -> list[dict[str, Any]]:
        current = self._now(now)
        events = self.store.get_events(session_id)
        terminal_ids = {
            event.get("payload", {}).get("work_item_id")
            for event in events
            if event["event_type"] in {"work.completed", "work.failed", "work.cancelled"}
        }
        active_lease_ids: set[Any] = set()
        for event in events:
            if event["event_type"] not in {"work.lease_acquired", "work.started"}:
                continue
            payload = event.get("payload", {})
            work_item_id = payload.get("work_item_id")
            if work_item_id in terminal_ids:
                continue
            lease_expires_at = self._parse_time(payload.get("lease_expires_at"))
            if lease_expires_at and lease_expires_at > current:
                active_lease_ids.add(work_item_id)
        pending: list[dict[str, Any]] = []
        for event in events:
            if event["event_type"] != "work.queued":
                continue
            payload = event.get("payload", {})
            work_item_id = payload.get("work_item_id")
            if work_item_id in terminal_ids or work_item_id in active_lease_ids:
                continue
            available_at = self._parse_time(payload.get("available_at"))
            if available_at and available_at > current:
                continue
            pending.append(payload)
        return pending

    def run_next(
        self,
        *,
        session_id: str,
        worker_id: str | None = None,
        lease_seconds: int = 300,
        now: datetime | None = None,
    ) -> dict[str, Any]:
        current = self._now(now)
        pending = self.pending_work(session_id=session_id, now=current)
        if not pending:
            return {"status": "idle", "session_id": session_id}
        work_item = pending[0]
        work_item_id = str(work_item["work_item_id"])
        turn_id = str(work_item["turn_id"])
        lease = self.acquire_lease(
            session_id=session_id,
            work_item=work_item,
            worker_id=worker_id,
            lease_seconds=lease_seconds,
            now=current,
        )
        if lease.get("status") != "leased":
            return {
                "status": "idle",
                "session_id": session_id,
                "reason": "work_item_already_claimed",
                "work_item_id": work_item_id,
            }
        self.store.emit_event(
            session_id,
            "work.started",
            {
                **work_item,
                "worker_id": lease["worker_id"],
                "lease_expires_at": lease["lease_expires_at"],
                "status": "running",
            },
        )
        timed_out = self.runtime.mark_timed_out_agent_runs(
            session_id=session_id,
            turn_id=turn_id,
        )
        try:
            if work_item["kind"] != "continue_turn":
                raise ValueError(f"Unsupported work item kind: {work_item['kind']}")
            output = self.runtime.continue_turn(session_id=session_id, turn_id=turn_id)
            flow_event = self.flow.emit_check(session_id=session_id, turn_id=turn_id)
            completed = self.store.emit_event(
                session_id,
                "work.completed",
                {
                    **work_item,
                    "status": "completed",
                    "timed_out_agent_runs": timed_out,
                    "flow_check": flow_event["payload"],
                    "turn_completed": output.get("turn_completed"),
                },
            )
            return {
                "status": "completed",
                "work_item": completed["payload"],
                "output": output,
            }
        except Exception as exc:
            failed = self.store.emit_event(
                session_id,
                "work.failed",
                {
                    **work_item,
                    "status": "failed",
                    "error": str(exc),
                    "timed_out_agent_runs": timed_out,
                },
            )
            if int(work_item.get("attempt", 1)) < int(work_item.get("max_attempts", 1)):
                next_attempt = int(work_item.get("attempt", 1)) + 1
                retry_delay_seconds = self._retry_delay_seconds(next_attempt)
                retry = {
                    **work_item,
                    "work_item_id": self._new_work_item_id(),
                    "attempt": next_attempt,
                    "status": "queued",
                    "retry_of": work_item_id,
                    "reason": "retry_after_work_failed",
                    "retry_delay_seconds": retry_delay_seconds,
                    "available_at": (current + timedelta(seconds=retry_delay_seconds)).isoformat(),
                }
                self.store.emit_event(session_id, "work.retry_scheduled", retry)
                self.store.emit_event(session_id, "work.queued", retry)
            return {"status": "failed", "work_item": failed["payload"]}
