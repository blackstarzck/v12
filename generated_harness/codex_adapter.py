from __future__ import annotations

from typing import Any, Callable

from .tool_gateway import ToolGateway


CODEX_TOOL_ALIASES = {
    "apply_patch": "git.apply_patch",
    "functions.apply_patch": "git.apply_patch",
    "shell": "shell.run",
    "shell_command": "shell.run",
    "functions.shell_command": "shell.run",
    "browser_review": "validator.browser",
    "playwright": "validator.browser",
}


class CodexToolAdapter:
    """Small bridge for hosts that wrap real Codex tool calls with harness events."""

    def __init__(self, gateway: ToolGateway) -> None:
        self.gateway = gateway

    def canonical_tool_name(self, codex_tool_name: str) -> str:
        return CODEX_TOOL_ALIASES.get(codex_tool_name, codex_tool_name)

    def _coerce_result(self, result: Any) -> dict[str, Any]:
        if isinstance(result, dict):
            return result
        return {"status": "completed", "value": result}

    def begin(
        self,
        *,
        session_id: str,
        turn_id: str,
        codex_tool_name: str,
        payload: dict[str, Any],
        agent_run_id: str | None = None,
        sandbox_ref: str | None = None,
    ) -> dict[str, Any]:
        tool_name = self.canonical_tool_name(codex_tool_name)
        authorization = self.gateway.begin_tool_call(
            session_id=session_id,
            turn_id=turn_id,
            name=tool_name,
            payload={
                **payload,
                "codex_tool_name": codex_tool_name,
            },
            agent_run_id=agent_run_id,
            sandbox_ref=sandbox_ref,
        )
        authorization["codex_tool_name"] = codex_tool_name
        return authorization

    def complete(
        self,
        *,
        session_id: str,
        turn_id: str,
        codex_tool_name: str,
        payload: dict[str, Any],
        result: dict[str, Any],
        tool_call_id: str | None = None,
        agent_run_id: str | None = None,
        sandbox_ref: str | None = None,
    ) -> dict[str, Any]:
        tool_name = self.canonical_tool_name(codex_tool_name)
        return self.gateway.complete_tool_call(
            session_id=session_id,
            turn_id=turn_id,
            name=tool_name,
            payload={
                **payload,
                "codex_tool_name": codex_tool_name,
            },
            result={
                **result,
                "codex_tool_name": codex_tool_name,
            },
            tool_call_id=tool_call_id,
            agent_run_id=agent_run_id,
            sandbox_ref=sandbox_ref,
        )

    def fail(
        self,
        *,
        session_id: str,
        turn_id: str,
        codex_tool_name: str,
        error: str,
        tool_call_id: str | None = None,
        agent_run_id: str | None = None,
        sandbox_ref: str | None = None,
    ) -> dict[str, Any]:
        return self.gateway.fail_tool_call(
            session_id=session_id,
            turn_id=turn_id,
            name=self.canonical_tool_name(codex_tool_name),
            error=error,
            tool_call_id=tool_call_id,
            agent_run_id=agent_run_id,
            sandbox_ref=sandbox_ref,
        )

    def tool_call(
        self,
        *,
        session_id: str,
        turn_id: str,
        codex_tool_name: str,
        payload: dict[str, Any],
        agent_run_id: str | None = None,
        sandbox_ref: str | None = None,
    ) -> "CodexToolCall":
        return CodexToolCall(
            adapter=self,
            session_id=session_id,
            turn_id=turn_id,
            codex_tool_name=codex_tool_name,
            payload=payload,
            agent_run_id=agent_run_id,
            sandbox_ref=sandbox_ref,
        )

    def recorded_call(
        self,
        *,
        session_id: str,
        turn_id: str,
        codex_tool_name: str,
        payload: dict[str, Any],
        action: Callable[[dict[str, Any]], Any],
        agent_run_id: str | None = None,
        sandbox_ref: str | None = None,
    ) -> dict[str, Any]:
        with self.tool_call(
            session_id=session_id,
            turn_id=turn_id,
            codex_tool_name=codex_tool_name,
            payload=payload,
            agent_run_id=agent_run_id,
            sandbox_ref=sandbox_ref,
        ) as tool_call:
            result = self._coerce_result(action(tool_call.authorization))
            return tool_call.complete(result)


class CodexToolCall:
    """Context manager that keeps begin/complete/fail paired by tool_call_id."""

    def __init__(
        self,
        *,
        adapter: CodexToolAdapter,
        session_id: str,
        turn_id: str,
        codex_tool_name: str,
        payload: dict[str, Any],
        agent_run_id: str | None,
        sandbox_ref: str | None,
    ) -> None:
        self.adapter = adapter
        self.session_id = session_id
        self.turn_id = turn_id
        self.codex_tool_name = codex_tool_name
        self.payload = payload
        self.agent_run_id = agent_run_id
        self.sandbox_ref = sandbox_ref
        self.authorization: dict[str, Any] = {}
        self._closed = False

    @property
    def tool_call_id(self) -> str:
        return str(self.authorization["tool_call_id"])

    def __enter__(self) -> "CodexToolCall":
        self.authorization = self.adapter.begin(
            session_id=self.session_id,
            turn_id=self.turn_id,
            codex_tool_name=self.codex_tool_name,
            payload=self.payload,
            agent_run_id=self.agent_run_id,
            sandbox_ref=self.sandbox_ref,
        )
        return self

    def complete(self, result: dict[str, Any]) -> dict[str, Any]:
        self._closed = True
        return self.adapter.complete(
            session_id=self.session_id,
            turn_id=self.turn_id,
            codex_tool_name=self.codex_tool_name,
            payload=self.payload,
            result=result,
            tool_call_id=self.tool_call_id,
            agent_run_id=self.agent_run_id,
            sandbox_ref=self.sandbox_ref,
        )

    def fail(self, error: str) -> dict[str, Any]:
        self._closed = True
        return self.adapter.fail(
            session_id=self.session_id,
            turn_id=self.turn_id,
            codex_tool_name=self.codex_tool_name,
            error=error,
            tool_call_id=self.tool_call_id,
            agent_run_id=self.agent_run_id,
            sandbox_ref=self.sandbox_ref,
        )

    def __exit__(self, exc_type: object, exc: object, traceback: object) -> bool:
        if exc is not None and not self._closed:
            self.fail(str(exc))
        elif not self._closed:
            self.fail("Codex tool context exited without complete(...).")
        return False
