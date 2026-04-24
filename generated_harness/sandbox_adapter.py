from __future__ import annotations

import uuid
from pathlib import Path
from typing import Any, Callable, Protocol

from .requirement_analysis import ensure_requirements_analyzed
from .session_store import FileSessionStore
from .tool_gateway import ToolGateway


SandboxHandler = Callable[[dict[str, Any]], dict[str, Any]]


class SandboxBackend(Protocol):
    def provision(self, *, sandbox_ref: str, resources: dict[str, Any] | None = None) -> dict[str, Any]:
        ...

    def execute(
        self,
        *,
        sandbox_ref: str,
        command: str,
        input_payload: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        ...

    def dispose(self, *, sandbox_ref: str) -> dict[str, Any]:
        ...


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


class SandboxPolicyError(RuntimeError):
    """Raised when sandbox lifecycle or credential boundary rules are violated."""


class SandboxAdapter:
    """Replaceable sandbox boundary reached through the tool gateway."""

    def __init__(
        self,
        repo_root: Path,
        store: FileSessionStore,
        gateway: ToolGateway,
        *,
        handler: SandboxHandler | None = None,
        backend: SandboxBackend | None = None,
    ) -> None:
        if handler and backend:
            raise ValueError("Configure either sandbox handler or sandbox backend, not both.")
        self.repo_root = repo_root
        self.store = store
        self.gateway = gateway
        self.handler = handler
        self.backend = backend

    def _new_sandbox_ref(self) -> str:
        return f"sandbox_{uuid.uuid4().hex[:12]}"

    def _sensitive_paths(self, value: Any, prefix: str = "input") -> list[str]:
        paths: list[str] = []
        if isinstance(value, dict):
            for key, child in value.items():
                key_text = str(key)
                normalized = key_text.lower().replace("-", "_")
                path = f"{prefix}.{key_text}" if prefix else key_text
                if any(marker in normalized for marker in SENSITIVE_KEY_MARKERS):
                    paths.append(path)
                    continue
                paths.extend(self._sensitive_paths(child, path))
        elif isinstance(value, list):
            for index, child in enumerate(value):
                paths.extend(self._sensitive_paths(child, f"{prefix}[{index}]"))
        return paths

    def _emit_blocked(
        self,
        *,
        session_id: str,
        turn_id: str,
        sandbox_ref: str | None,
        reason: str,
        agent_run_id: str | None = None,
        tool_call_id: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        self.store.emit_event(
            session_id,
            "sandbox.blocked",
            {
                "turn_id": turn_id,
                "agent_run_id": agent_run_id,
                "sandbox_ref": sandbox_ref,
                "tool_call_id": tool_call_id,
                "reason": reason,
                "details": details or {},
            },
        )

    def _sandbox_status(self, *, session_id: str, sandbox_ref: str) -> str | None:
        status: str | None = None
        for event in self.store.get_events(session_id):
            payload = event.get("payload", {})
            if payload.get("sandbox_ref") != sandbox_ref:
                continue
            if event["event_type"] == "sandbox.provisioned":
                status = "provisioned"
            elif event["event_type"] == "sandbox.executed":
                status = "active"
            elif event["event_type"] == "sandbox.failed":
                status = "failed"
            elif event["event_type"] == "sandbox.disposed":
                status = "disposed"
        return status

    def _ensure_active_sandbox(
        self,
        *,
        session_id: str,
        turn_id: str,
        sandbox_ref: str,
        agent_run_id: str | None = None,
        tool_call_id: str | None = None,
    ) -> None:
        status = self._sandbox_status(session_id=session_id, sandbox_ref=sandbox_ref)
        if status is None:
            self._emit_blocked(
                session_id=session_id,
                turn_id=turn_id,
                sandbox_ref=sandbox_ref,
                agent_run_id=agent_run_id,
                tool_call_id=tool_call_id,
                reason="unknown_sandbox",
            )
            raise SandboxPolicyError(f"Sandbox {sandbox_ref} has not been provisioned.")
        if status in {"disposed", "failed"}:
            self._emit_blocked(
                session_id=session_id,
                turn_id=turn_id,
                sandbox_ref=sandbox_ref,
                agent_run_id=agent_run_id,
                tool_call_id=tool_call_id,
                reason="sandbox_not_active",
                details={"status": status},
            )
            raise SandboxPolicyError(f"Sandbox {sandbox_ref} is not active: {status}.")

    def _reject_sensitive_payload(
        self,
        *,
        session_id: str,
        turn_id: str,
        sandbox_ref: str | None,
        payload: dict[str, Any],
        payload_name: str,
        agent_run_id: str | None = None,
        tool_call_id: str | None = None,
    ) -> None:
        sensitive_paths = self._sensitive_paths(payload, payload_name)
        if not sensitive_paths:
            return
        self._emit_blocked(
            session_id=session_id,
            turn_id=turn_id,
            sandbox_ref=sandbox_ref,
            agent_run_id=agent_run_id,
            tool_call_id=tool_call_id,
            reason="credentials_not_allowed",
            details={"sensitive_paths": sensitive_paths},
        )
        raise SandboxPolicyError("Credentials and secrets must stay outside the sandbox payload.")

    def provision(
        self,
        *,
        session_id: str,
        turn_id: str,
        resources: dict[str, Any] | None = None,
        agent_run_id: str | None = None,
    ) -> dict[str, Any]:
        sandbox_ref = self._new_sandbox_ref()
        safe_resources = resources or {}
        ensure_requirements_analyzed(self.store, session_id=session_id, turn_id=turn_id)
        self.gateway.gate.ensure_open(session_id, turn_id)
        self._reject_sensitive_payload(
            session_id=session_id,
            turn_id=turn_id,
            sandbox_ref=sandbox_ref,
            payload=safe_resources,
            payload_name="resources",
            agent_run_id=agent_run_id,
        )
        backend_result = self.backend.provision(sandbox_ref=sandbox_ref, resources=safe_resources) if self.backend else {}
        payload = {
            "turn_id": turn_id,
            "agent_run_id": agent_run_id,
            "sandbox_ref": sandbox_ref,
            "resources": safe_resources,
            "backend": backend_result or {"backend": "noop", "status": "not_configured"},
            "credentials_visible": False,
            "credential_policy": "blocked_by_default",
            "status": "provisioned",
        }
        self.store.emit_event(session_id, "sandbox.provisioned", payload)
        return payload

    def execute(
        self,
        *,
        session_id: str,
        turn_id: str,
        sandbox_ref: str,
        command: str,
        input_payload: dict[str, Any] | None = None,
        agent_run_id: str | None = None,
    ) -> dict[str, Any]:
        payload = {
            "sandbox_ref": sandbox_ref,
            "command": command,
            "input": input_payload or {},
        }
        authorization = self.gateway.begin_tool_call(
            session_id=session_id,
            turn_id=turn_id,
            name="sandbox.execute",
            payload=payload,
            agent_run_id=agent_run_id,
            sandbox_ref=sandbox_ref,
        )
        try:
            self._ensure_active_sandbox(
                session_id=session_id,
                turn_id=turn_id,
                sandbox_ref=sandbox_ref,
                agent_run_id=agent_run_id,
                tool_call_id=authorization["tool_call_id"],
            )
            self._reject_sensitive_payload(
                session_id=session_id,
                turn_id=turn_id,
                sandbox_ref=sandbox_ref,
                payload=input_payload or {},
                payload_name="input",
                agent_run_id=agent_run_id,
                tool_call_id=authorization["tool_call_id"],
            )
            if self.handler:
                result = self.handler(payload)
            elif self.backend:
                result = self.backend.execute(
                    sandbox_ref=sandbox_ref,
                    command=command,
                    input_payload=input_payload or {},
                )
            else:
                result = {"status": "noop", "sandbox_ref": sandbox_ref}
        except Exception as exc:
            self.gateway.fail_tool_call(
                session_id=session_id,
                turn_id=turn_id,
                name="sandbox.execute",
                error=str(exc),
                tool_call_id=authorization["tool_call_id"],
                agent_run_id=agent_run_id,
                sandbox_ref=sandbox_ref,
            )
            if not isinstance(exc, SandboxPolicyError):
                self.store.emit_event(
                    session_id,
                    "sandbox.failed",
                    {
                        "turn_id": turn_id,
                        "agent_run_id": agent_run_id,
                        "sandbox_ref": sandbox_ref,
                        "tool_call_id": authorization["tool_call_id"],
                        "error": str(exc),
                    },
                )
            raise
        completed = self.gateway.complete_tool_call(
            session_id=session_id,
            turn_id=turn_id,
            name="sandbox.execute",
            payload=payload,
            result=result,
            tool_call_id=authorization["tool_call_id"],
            agent_run_id=agent_run_id,
            sandbox_ref=sandbox_ref,
        )
        self.store.emit_event(
            session_id,
            "sandbox.executed",
            {
                "turn_id": turn_id,
                "agent_run_id": agent_run_id,
                "sandbox_ref": sandbox_ref,
                "tool_call_id": authorization["tool_call_id"],
                "status": completed.get("status", "completed"),
                "result": completed,
            },
        )
        return {
            **completed,
            "sandbox_ref": sandbox_ref,
            "tool_call_id": authorization["tool_call_id"],
        }

    def dispose(
        self,
        *,
        session_id: str,
        turn_id: str,
        sandbox_ref: str,
        agent_run_id: str | None = None,
    ) -> dict[str, Any]:
        self._ensure_active_sandbox(
            session_id=session_id,
            turn_id=turn_id,
            sandbox_ref=sandbox_ref,
            agent_run_id=agent_run_id,
        )
        backend_result = self.backend.dispose(sandbox_ref=sandbox_ref) if self.backend else {}
        payload = {
            "turn_id": turn_id,
            "agent_run_id": agent_run_id,
            "sandbox_ref": sandbox_ref,
            "backend": backend_result or {"backend": "noop", "status": "not_configured"},
            "status": "disposed",
        }
        self.store.emit_event(session_id, "sandbox.disposed", payload)
        return payload
