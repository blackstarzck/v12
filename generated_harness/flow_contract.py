from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .session_store import FileSessionStore


@dataclass
class FlowCheckResult:
    status: str
    findings: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {"status": self.status, "findings": self.findings}


class ExecutionFlowVerifier:
    """Checks the event stream against docs/harness/execution-flow.md."""

    def __init__(self, store: FileSessionStore) -> None:
        self.store = store

    def verify_turn(self, *, session_id: str, turn_id: str) -> FlowCheckResult:
        events = [
            event
            for event in self.store.get_events(session_id)
            if event.get("payload", {}).get("turn_id") == turn_id
        ]
        findings: list[dict[str, Any]] = []
        first_sequence: dict[str, int] = {}
        for event in events:
            first_sequence.setdefault(event["event_type"], int(event["sequence"]))
        has_required_documents = any(
            event["event_type"] == "docs.required" and event.get("payload", {}).get("documents")
            for event in events
        )

        self._check_required_order(first_sequence, findings)
        self._check_clarification(events, first_sequence, findings)
        self._check_agents(events, findings)
        self._check_tools(
            events,
            findings,
            has_required_documents=has_required_documents,
            turn_completed_sequence=first_sequence.get("turn.completed"),
        )
        self._check_sandboxes(events, findings, has_required_documents=has_required_documents)
        self._check_work(events, findings)
        self._check_turn_completion(first_sequence, findings)
        return FlowCheckResult(status="passed" if not findings else "failed", findings=findings)

    def emit_check(self, *, session_id: str, turn_id: str) -> dict[str, Any]:
        result = self.verify_turn(session_id=session_id, turn_id=turn_id).to_dict()
        return self.store.emit_event(session_id, "flow.checked", {"turn_id": turn_id, **result})

    def _add_finding(self, findings: list[dict[str, Any]], *, code: str, message: str, event: dict[str, Any] | None = None) -> None:
        finding: dict[str, Any] = {"code": code, "message": message}
        if event is not None:
            finding["sequence"] = event["sequence"]
            finding["event_type"] = event["event_type"]
        findings.append(finding)

    def _check_required_order(self, first_sequence: dict[str, int], findings: list[dict[str, Any]]) -> None:
        analyzed = first_sequence.get("requirements.analyzed")
        required = first_sequence.get("docs.required")
        if required is not None and analyzed is None:
            self._add_finding(
                findings,
                code="missing_requirements_analysis",
                message="docs.required exists before any requirements.analyzed event.",
            )
        if analyzed is not None and required is not None and analyzed > required:
            self._add_finding(
                findings,
                code="requirements_after_docs",
                message="requirements.analyzed must appear before docs.required.",
            )

    def _check_clarification(
        self,
        events: list[dict[str, Any]],
        first_sequence: dict[str, int],
        findings: list[dict[str, Any]],
    ) -> None:
        clarification_required = first_sequence.get("clarification.required")
        clarification_resolved = first_sequence.get("clarification.resolved")
        analyzed = first_sequence.get("requirements.analyzed")
        required_docs = first_sequence.get("docs.required")

        if clarification_required is not None and analyzed is not None and clarification_required < analyzed:
            self._add_finding(
                findings,
                code="clarification_before_analysis",
                message="clarification.required must appear after requirements.analyzed.",
            )
        if clarification_resolved is not None and clarification_required is None:
            self._add_finding(
                findings,
                code="clarification_resolved_without_request",
                message="clarification.resolved exists without an earlier clarification.required event.",
            )
        if (
            clarification_required is not None
            and clarification_resolved is not None
            and clarification_resolved < clarification_required
        ):
            self._add_finding(
                findings,
                code="clarification_resolved_before_request",
                message="clarification.resolved must appear after clarification.required.",
            )
        if clarification_required is not None and required_docs is not None:
            if clarification_resolved is None:
                self._add_finding(
                    findings,
                    code="docs_required_before_clarification_resolved",
                    message="docs.required must not appear before clarification.resolved on clarification-gated turns.",
                )
            elif clarification_resolved > required_docs:
                self._add_finding(
                    findings,
                    code="docs_required_before_clarification_resolved",
                    message="docs.required must appear after clarification.resolved on clarification-gated turns.",
                )

    def _check_agents(self, events: list[dict[str, Any]], findings: list[dict[str, Any]]) -> None:
        started: set[str] = set()
        for event in events:
            payload = event.get("payload", {})
            agent_run_id = payload.get("agent_run_id")
            if event["event_type"] == "agent.started" and agent_run_id:
                started.add(str(agent_run_id))
                continue
            if event["event_type"] in {"agent.completed", "agent.failed", "agent.timed_out"}:
                if not agent_run_id or str(agent_run_id) not in started:
                    self._add_finding(
                        findings,
                        code="agent_terminal_without_start",
                        message="Agent terminal event has no earlier agent.started event.",
                        event=event,
                    )

    def _check_tools(
        self,
        events: list[dict[str, Any]],
        findings: list[dict[str, Any]],
        *,
        has_required_documents: bool,
        turn_completed_sequence: int | None,
    ) -> None:
        tool_calls: dict[str, dict[str, Any]] = {}
        terminal_tool_ids: set[str] = set()
        analyzed_sequences = [
            int(event["sequence"])
            for event in events
            if event["event_type"] == "requirements.analyzed"
        ]
        ack_sequences = [
            int(event["sequence"])
            for event in events
            if event["event_type"] == "docs.acknowledged"
        ]
        clarification_required_sequences = [
            int(event["sequence"])
            for event in events
            if event["event_type"] == "clarification.required"
        ]
        clarification_resolved_sequences = [
            int(event["sequence"])
            for event in events
            if event["event_type"] == "clarification.resolved"
        ]
        for event in events:
            payload = event.get("payload", {})
            tool_call_id = payload.get("tool_call_id")
            if event["event_type"] == "tool.called":
                if tool_call_id:
                    tool_calls[str(tool_call_id)] = event
                else:
                    self._add_finding(
                        findings,
                        code="tool_called_missing_tool_call_id",
                        message="tool.called must include a tool_call_id.",
                        event=event,
                    )
                if payload.get("requires_gate") is True:
                    sequence = int(event["sequence"])
                    if not any(item < sequence for item in analyzed_sequences):
                        self._add_finding(
                            findings,
                            code="gated_tool_without_analysis",
                            message="Gated tool call has no earlier requirements.analyzed event.",
                            event=event,
                        )
                    if has_required_documents and not any(item < sequence for item in ack_sequences):
                        self._add_finding(
                            findings,
                            code="gated_tool_without_ack",
                            message="Gated tool call has no earlier docs.acknowledged event.",
                            event=event,
                        )
                    if clarification_required_sequences and not any(
                        item < sequence for item in clarification_resolved_sequences
                    ):
                        self._add_finding(
                            findings,
                            code="gated_tool_without_clarification",
                            message="Gated tool call has no earlier clarification.resolved event.",
                            event=event,
                        )
                continue
            if event["event_type"] in {"tool.completed", "tool.failed"}:
                if not tool_call_id or str(tool_call_id) not in tool_calls:
                    self._add_finding(
                        findings,
                        code="tool_terminal_without_call",
                        message="Tool terminal event has no earlier tool.called event.",
                        event=event,
                    )
                else:
                    terminal_tool_ids.add(str(tool_call_id))
                if turn_completed_sequence is not None and int(event["sequence"]) < turn_completed_sequence:
                    continue
                if turn_completed_sequence is not None and int(event["sequence"]) > turn_completed_sequence:
                    self._add_finding(
                        findings,
                        code="tool_terminal_after_turn_completed",
                        message="Tool terminal event appeared after turn.completed.",
                        event=event,
                    )
            if event["event_type"] == "repo.changed" and tool_call_id and str(tool_call_id) not in tool_calls:
                self._add_finding(
                    findings,
                    code="repo_changed_without_tool_call",
                    message="repo.changed references a tool_call_id without earlier tool.called.",
                    event=event,
                )
            if event["event_type"] == "repo.changed" and not tool_call_id:
                self._add_finding(
                    findings,
                    code="repo_changed_missing_tool_call_id",
                    message="repo.changed must include the tool_call_id that caused the file change.",
                    event=event,
                )
            if event["event_type"] == "validation.completed" and tool_call_id and str(tool_call_id) not in tool_calls:
                self._add_finding(
                    findings,
                    code="validation_without_tool_call",
                    message="validation.completed references a tool_call_id without earlier tool.called.",
                    event=event,
                )
        if turn_completed_sequence is not None:
            for tool_call_id, event in tool_calls.items():
                if tool_call_id not in terminal_tool_ids and int(event["sequence"]) < turn_completed_sequence:
                    self._add_finding(
                        findings,
                        code="tool_call_without_terminal",
                        message="tool.called must have tool.completed or tool.failed before turn.completed.",
                        event=event,
                    )

    def _check_sandboxes(
        self,
        events: list[dict[str, Any]],
        findings: list[dict[str, Any]],
        *,
        has_required_documents: bool,
    ) -> None:
        status_by_ref: dict[str, str] = {}
        analyzed_sequences = [
            int(event["sequence"])
            for event in events
            if event["event_type"] == "requirements.analyzed"
        ]
        ack_sequences = [
            int(event["sequence"])
            for event in events
            if event["event_type"] == "docs.acknowledged"
        ]
        clarification_required_sequences = [
            int(event["sequence"])
            for event in events
            if event["event_type"] == "clarification.required"
        ]
        clarification_resolved_sequences = [
            int(event["sequence"])
            for event in events
            if event["event_type"] == "clarification.resolved"
        ]
        for event in events:
            payload = event.get("payload", {})
            sandbox_ref = payload.get("sandbox_ref")
            if not sandbox_ref:
                continue
            sandbox_ref = str(sandbox_ref)
            event_type = event["event_type"]
            if event_type == "sandbox.provisioned":
                sequence = int(event["sequence"])
                if not any(item < sequence for item in analyzed_sequences):
                    self._add_finding(
                        findings,
                        code="sandbox_provision_without_analysis",
                        message="sandbox.provisioned has no earlier requirements.analyzed event.",
                        event=event,
                    )
                if has_required_documents and not any(item < sequence for item in ack_sequences):
                    self._add_finding(
                        findings,
                        code="sandbox_provision_without_ack",
                        message="sandbox.provisioned has no earlier docs.acknowledged event.",
                        event=event,
                    )
                if clarification_required_sequences and not any(
                    item < sequence for item in clarification_resolved_sequences
                ):
                    self._add_finding(
                        findings,
                        code="sandbox_provision_without_clarification",
                        message="sandbox.provisioned has no earlier clarification.resolved event.",
                        event=event,
                    )
                status_by_ref[sandbox_ref] = "active"
                continue
            if event_type not in {"sandbox.executed", "sandbox.failed", "sandbox.disposed"}:
                continue
            previous_status = status_by_ref.get(sandbox_ref)
            if previous_status is None:
                self._add_finding(
                    findings,
                    code="sandbox_event_without_provision",
                    message="Sandbox lifecycle event references a sandbox_ref without earlier sandbox.provisioned.",
                    event=event,
                )
                continue
            if event_type == "sandbox.executed" and previous_status in {"disposed", "failed"}:
                self._add_finding(
                    findings,
                    code="sandbox_executed_after_terminal",
                    message="sandbox.executed appeared after the sandbox was disposed or failed.",
                    event=event,
                )
                continue
            if event_type == "sandbox.failed":
                status_by_ref[sandbox_ref] = "failed"
            elif event_type == "sandbox.disposed":
                status_by_ref[sandbox_ref] = "disposed"
            else:
                status_by_ref[sandbox_ref] = "active"

    def _check_work(self, events: list[dict[str, Any]], findings: list[dict[str, Any]]) -> None:
        queued_ids: set[str] = set()
        leased_ids: set[str] = set()
        for event in events:
            if not event["event_type"].startswith("work."):
                continue
            payload = event.get("payload", {})
            work_item_id = payload.get("work_item_id")
            if not work_item_id:
                self._add_finding(
                    findings,
                    code="work_event_missing_work_item_id",
                    message="Work event must include work_item_id.",
                    event=event,
                )
                continue
            work_item_id = str(work_item_id)
            if event["event_type"] == "work.queued":
                queued_ids.add(work_item_id)
                continue
            if event["event_type"] == "work.lease_acquired":
                if work_item_id not in queued_ids:
                    self._add_finding(
                        findings,
                        code="work_lease_without_queue",
                        message="work.lease_acquired has no earlier work.queued event.",
                        event=event,
                    )
                leased_ids.add(work_item_id)
                continue
            if event["event_type"] == "work.started":
                if work_item_id not in queued_ids:
                    self._add_finding(
                        findings,
                        code="work_started_without_queue",
                        message="work.started has no earlier work.queued event.",
                        event=event,
                    )
                if work_item_id not in leased_ids:
                    self._add_finding(
                        findings,
                        code="work_started_without_lease",
                        message="work.started has no earlier work.lease_acquired event.",
                        event=event,
                    )
            if event["event_type"] == "work.retry_scheduled":
                retry_of = payload.get("retry_of")
                if not retry_of or str(retry_of) not in queued_ids:
                    self._add_finding(
                        findings,
                        code="work_retry_without_original_queue",
                        message="work.retry_scheduled has no earlier queued retry_of work item.",
                        event=event,
                    )
                continue
            if event["event_type"] in {"work.completed", "work.failed"}:
                if work_item_id not in queued_ids:
                    self._add_finding(
                        findings,
                        code="work_terminal_without_queue",
                        message="Work terminal or retry event has no earlier work.queued event.",
                        event=event,
                    )

    def _check_turn_completion(self, first_sequence: dict[str, int], findings: list[dict[str, Any]]) -> None:
        completed = first_sequence.get("turn.completed")
        quality = first_sequence.get("quality.review_completed")
        if completed is not None and quality is None:
            self._add_finding(
                findings,
                code="turn_completed_without_quality_review",
                message="turn.completed exists without quality.review_completed.",
            )
        if completed is not None and quality is not None and quality > completed:
            self._add_finding(
                findings,
                code="turn_completed_before_quality_review",
                message="turn.completed must appear after quality.review_completed.",
            )
