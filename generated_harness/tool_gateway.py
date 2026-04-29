from __future__ import annotations

import uuid
from typing import Any, Callable

from .clarification import ensure_clarification_resolved
from .document_gate import DocumentGate
from .requirement_analysis import ensure_requirements_analyzed
from .session_store import FileSessionStore


ToolHandler = Callable[[dict[str, Any]], dict[str, Any]]

SENSITIVE_KEY_MARKERS = (
    "access_key",
    "api_key",
    "auth",
    "credential",
    "password",
    "private_key",
    "refresh_token",
    "secret",
    "token",
)

REDACTED_VALUE = "[redacted]"

DEFAULT_READ_ONLY_TOOLS = {
    "repo.read",
    "repo.search",
    "repo.list",
    "filesystem.read",
    "filesystem.search",
    "git.status",
    "git.diff",
    "git.show",
}

DEFAULT_MUTATING_TOOLS = {
    "repo.write",
    "filesystem.write",
    "filesystem.delete",
    "filesystem.move",
    "shell.run",
    "sandbox.execute",
    "git.apply_patch",
    "git.commit",
}

DEFAULT_DENIED_TOOLS = {
    "credential.dump",
}


class ToolPolicyError(RuntimeError):
    pass


class ToolGateway:
    def __init__(
        self,
        *,
        store: FileSessionStore,
        gate: DocumentGate,
        handlers: dict[str, ToolHandler] | None = None,
        read_only_tools: set[str] | None = None,
        mutating_tools: set[str] | None = None,
        denied_tools: set[str] | None = None,
        gate_unknown_tools: bool = True,
    ) -> None:
        self.store = store
        self.gate = gate
        self.handlers = handlers or {}
        self.read_only_tools = set(DEFAULT_READ_ONLY_TOOLS)
        if read_only_tools:
            self.read_only_tools.update(read_only_tools)
        self.mutating_tools = set(DEFAULT_MUTATING_TOOLS)
        if mutating_tools:
            self.mutating_tools.update(mutating_tools)
        self.denied_tools = set(DEFAULT_DENIED_TOOLS)
        if denied_tools:
            self.denied_tools.update(denied_tools)
        self.gate_unknown_tools = gate_unknown_tools

    def _requires_gate(self, name: str) -> bool:
        if name in self.read_only_tools:
            return False
        if name in self.mutating_tools:
            return True
        return self.gate_unknown_tools

    def _changed_paths(self, payload: dict[str, Any], result: dict[str, Any]) -> list[str]:
        paths: list[str] = []
        for source in (payload, result):
            for key in ("changed_paths", "target_paths", "paths"):
                value = source.get(key)
                if isinstance(value, list):
                    paths.extend(str(item) for item in value if str(item).strip())
                elif isinstance(value, str) and value.strip():
                    paths.append(value)
        return sorted(set(paths))

    def _new_tool_call_id(self) -> str:
        return f"tool_{uuid.uuid4().hex[:12]}"

    def _redact_sensitive(self, value: Any) -> Any:
        if isinstance(value, dict):
            redacted: dict[str, Any] = {}
            for key, child in value.items():
                normalized = str(key).lower().replace("-", "_")
                if any(marker in normalized for marker in SENSITIVE_KEY_MARKERS):
                    redacted[str(key)] = REDACTED_VALUE
                else:
                    redacted[str(key)] = self._redact_sensitive(child)
            return redacted
        if isinstance(value, list):
            return [self._redact_sensitive(item) for item in value]
        return value

    def _resolve_open_tool_call(
        self,
        *,
        session_id: str,
        turn_id: str,
        name: str,
        tool_call_id: str | None,
    ) -> dict[str, Any]:
        terminal_ids = {
            event.get("payload", {}).get("tool_call_id")
            for event in self.store.get_events(session_id)
            if event["event_type"] in {"tool.completed", "tool.failed"}
        }
        for event in reversed(self.store.get_events(session_id)):
            payload = event.get("payload", {})
            if event["event_type"] != "tool.called":
                continue
            if payload.get("turn_id") != turn_id or payload.get("tool_name") != name:
                continue
            if tool_call_id and payload.get("tool_call_id") != tool_call_id:
                continue
            if not tool_call_id and payload.get("tool_call_id") in terminal_ids:
                continue
            return payload
        return {
            "turn_id": turn_id,
            "tool_name": name,
            "tool_call_id": tool_call_id or self._new_tool_call_id(),
        }

    def begin_tool_call(
        self,
        *,
        session_id: str,
        turn_id: str,
        name: str,
        payload: dict[str, Any],
        agent_run_id: str | None = None,
        sandbox_ref: str | None = None,
        tool_call_id: str | None = None,
    ) -> dict[str, Any]:
        if name in self.denied_tools:
            self.store.emit_event(
                session_id,
                "tool.blocked",
                {
                    "turn_id": turn_id,
                    "agent_run_id": agent_run_id,
                    "sandbox_ref": sandbox_ref,
                    "tool_name": name,
                    "input": self._redact_sensitive(payload),
                    "reason": "tool_denied",
                },
            )
            raise ToolPolicyError(f"Tool '{name}' is denied by harness policy.")
        tool_call_id = tool_call_id or self._new_tool_call_id()
        requires_gate = self._requires_gate(name)
        if requires_gate:
            ensure_requirements_analyzed(self.store, session_id=session_id, turn_id=turn_id)
            ensure_clarification_resolved(self.store, session_id=session_id, turn_id=turn_id)
            self.gate.ensure_open(session_id, turn_id)
        event = self.store.emit_event(
            session_id,
            "tool.called",
            {
                "turn_id": turn_id,
                "tool_call_id": tool_call_id,
                "agent_run_id": agent_run_id,
                "sandbox_ref": sandbox_ref,
                "tool_name": name,
                "input": self._redact_sensitive(payload),
                "requires_gate": requires_gate,
            },
        )
        return {
            "status": "authorized",
            "event_sequence": event["sequence"],
            "tool_call_id": tool_call_id,
            "agent_run_id": agent_run_id,
            "sandbox_ref": sandbox_ref,
            "tool_name": name,
            "requires_gate": requires_gate,
            "payload": payload,
        }

    def complete_tool_call(
        self,
        *,
        session_id: str,
        turn_id: str,
        name: str,
        payload: dict[str, Any],
        result: dict[str, Any],
        tool_call_id: str | None = None,
        agent_run_id: str | None = None,
        sandbox_ref: str | None = None,
    ) -> dict[str, Any]:
        call_payload = self._resolve_open_tool_call(
            session_id=session_id,
            turn_id=turn_id,
            name=name,
            tool_call_id=tool_call_id,
        )
        resolved_tool_call_id = str(call_payload.get("tool_call_id"))
        resolved_agent_run_id = agent_run_id if agent_run_id is not None else call_payload.get("agent_run_id")
        resolved_sandbox_ref = sandbox_ref if sandbox_ref is not None else call_payload.get("sandbox_ref")
        self.store.emit_event(
            session_id,
            "tool.completed",
            {
                "turn_id": turn_id,
                "tool_call_id": resolved_tool_call_id,
                "agent_run_id": resolved_agent_run_id,
                "sandbox_ref": resolved_sandbox_ref,
                "tool_name": name,
                "result": self._redact_sensitive(result),
            },
        )
        result_payload = result if isinstance(result, dict) else {}
        changed_paths = self._changed_paths(payload, result_payload)
        if changed_paths and (name in self.mutating_tools or "changed_paths" in result_payload):
            self.store.emit_event(
                session_id,
                "repo.changed",
                {
                    "turn_id": turn_id,
                    "tool_call_id": resolved_tool_call_id,
                    "agent_run_id": resolved_agent_run_id,
                    "sandbox_ref": resolved_sandbox_ref,
                    "tool_name": name,
                    "changed_paths": changed_paths,
                    "source": "tool_gateway",
                },
            )
        return result

    def fail_tool_call(
        self,
        *,
        session_id: str,
        turn_id: str,
        name: str,
        error: str,
        tool_call_id: str | None = None,
        agent_run_id: str | None = None,
        sandbox_ref: str | None = None,
    ) -> dict[str, Any]:
        call_payload = self._resolve_open_tool_call(
            session_id=session_id,
            turn_id=turn_id,
            name=name,
            tool_call_id=tool_call_id,
        )
        payload = {
            "turn_id": turn_id,
            "tool_call_id": call_payload.get("tool_call_id"),
            "agent_run_id": agent_run_id if agent_run_id is not None else call_payload.get("agent_run_id"),
            "sandbox_ref": sandbox_ref if sandbox_ref is not None else call_payload.get("sandbox_ref"),
            "tool_name": name,
            "error": error,
        }
        self.store.emit_event(session_id, "tool.failed", payload)
        return payload

    def execute(
        self,
        *,
        session_id: str,
        turn_id: str,
        name: str,
        payload: dict[str, Any],
        agent_run_id: str | None = None,
        sandbox_ref: str | None = None,
    ) -> dict[str, Any]:
        authorization = self.begin_tool_call(
            session_id=session_id,
            turn_id=turn_id,
            name=name,
            payload=payload,
            agent_run_id=agent_run_id,
            sandbox_ref=sandbox_ref,
        )
        handler = self.handlers.get(name)
        try:
            result = handler(payload) if handler else {"status": "noop", "tool_name": name, "payload": payload}
        except Exception as exc:
            self.fail_tool_call(
                session_id=session_id,
                turn_id=turn_id,
                name=name,
                error=str(exc),
                tool_call_id=authorization["tool_call_id"],
                agent_run_id=agent_run_id,
                sandbox_ref=sandbox_ref,
            )
            raise
        return self.complete_tool_call(
            session_id=session_id,
            turn_id=turn_id,
            name=name,
            payload=payload,
            result=result,
            tool_call_id=authorization["tool_call_id"],
            agent_run_id=agent_run_id,
            sandbox_ref=sandbox_ref,
        )
