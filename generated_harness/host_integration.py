from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from .flow_contract import ExecutionFlowVerifier
from .runtime import HarnessRuntime


@dataclass(frozen=True)
class HostToolExample:
    codex_tool_name: str
    canonical_tool_name: str
    classification: str
    preferred_wrapper: str
    purpose: str


CODEX_HOST_TOOL_EXAMPLES = [
    HostToolExample(
        codex_tool_name="apply_patch",
        canonical_tool_name="git.apply_patch",
        classification="mutating",
        preferred_wrapper="recorded_call",
        purpose="Record one source edit and any changed paths.",
    ),
    HostToolExample(
        codex_tool_name="functions.shell_command",
        canonical_tool_name="shell.run",
        classification="mutating_or_external",
        preferred_wrapper="recorded_call",
        purpose="Record one host shell command, including failures.",
    ),
    HostToolExample(
        codex_tool_name="browser_review",
        canonical_tool_name="validator.browser",
        classification="validation",
        preferred_wrapper="recorded_call",
        purpose="Record reviewer-owned browser validation.",
    ),
]


class HostAuditError(RuntimeError):
    def __init__(self, audit: dict[str, Any]) -> None:
        self.audit = audit
        codes = ", ".join(str(finding.get("code")) for finding in audit.get("findings", []))
        message = "Pre-final audit failed"
        if codes:
            message = f"{message}: {codes}"
        super().__init__(message)


def audit_runtime_turn(
    *,
    runtime: HarnessRuntime,
    session_id: str,
    turn_id: str,
    compact: bool = False,
) -> dict[str, Any]:
    replay = runtime.replay_turn(session_id=session_id, turn_id=turn_id)
    flow = ExecutionFlowVerifier(runtime.store).verify_turn(session_id=session_id, turn_id=turn_id)
    findings: list[dict[str, Any]] = []
    if flow.status != "passed":
        findings.extend({"source": "flow", **finding} for finding in flow.findings)
    if not replay.get("turn_completed"):
        findings.append({"source": "pre_final", "code": "turn_not_completed", "message": "Turn is not completed."})
    if replay.get("open_tool_calls"):
        findings.append(
            {
                "source": "pre_final",
                "code": "open_tool_calls",
                "message": "Turn still has open tool calls.",
                "tool_call_ids": [tool["tool_call_id"] for tool in replay["open_tool_calls"]],
            }
        )
    if not replay.get("quality_review"):
        findings.append(
            {
                "source": "pre_final",
                "code": "quality_review_missing",
                "message": "Quality review has not completed.",
            }
        )
    compact_result = runtime.compact_turn(session_id=session_id, turn_id=turn_id) if compact else None
    return {
        "status": "passed" if not findings else "failed",
        "session_id": session_id,
        "turn_id": turn_id,
        "flow_status": flow.status,
        "next_recommended_action": replay.get("next_recommended_action"),
        "findings": findings,
        "compact": compact_result,
    }


class CodexHostGuard:
    """Host-facing helper that keeps Codex tool calls and final audits together."""

    def __init__(self, runtime: HarnessRuntime, *, session_id: str, turn_id: str) -> None:
        self.runtime = runtime
        self.session_id = session_id
        self.turn_id = turn_id

    def recorded_call(
        self,
        *,
        codex_tool_name: str,
        payload: dict[str, Any],
        action: Callable[[dict[str, Any]], Any],
        agent_run_id: str | None = None,
        sandbox_ref: str | None = None,
    ) -> dict[str, Any]:
        return self.runtime.codex.recorded_call(
            session_id=self.session_id,
            turn_id=self.turn_id,
            codex_tool_name=codex_tool_name,
            payload=payload,
            action=action,
            agent_run_id=agent_run_id,
            sandbox_ref=sandbox_ref,
        )

    def tool_call(
        self,
        *,
        codex_tool_name: str,
        payload: dict[str, Any],
        agent_run_id: str | None = None,
        sandbox_ref: str | None = None,
    ) -> Any:
        return self.runtime.codex.tool_call(
            session_id=self.session_id,
            turn_id=self.turn_id,
            codex_tool_name=codex_tool_name,
            payload=payload,
            agent_run_id=agent_run_id,
            sandbox_ref=sandbox_ref,
        )

    def audit_final(self, *, compact: bool = False) -> dict[str, Any]:
        return audit_runtime_turn(
            runtime=self.runtime,
            session_id=self.session_id,
            turn_id=self.turn_id,
            compact=compact,
        )

    def require_final_audit(self, *, compact: bool = False) -> dict[str, Any]:
        audit = self.audit_final(compact=compact)
        if audit["status"] != "passed":
            raise HostAuditError(audit)
        return audit
