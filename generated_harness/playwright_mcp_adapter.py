from __future__ import annotations

import json
import uuid
from pathlib import Path
from typing import Any

from .document_gate import DocumentGateError
from .session_store import FileSessionStore
from .tool_gateway import ToolGateway


VALID_BROWSER_STATUSES = {"passed", "failed", "error", "unavailable"}


class PlaywrightMcpBridge:
    """File-backed bridge between the harness and an external Playwright MCP runner."""

    def __init__(self, repo_root: Path, store: FileSessionStore, gateway: ToolGateway) -> None:
        self.repo_root = repo_root
        self.store = store
        self.gateway = gateway
        self.review_dir = repo_root / ".harness" / "browser_reviews"
        self.review_dir.mkdir(parents=True, exist_ok=True)

    def _new_request_id(self) -> str:
        return f"browser_{uuid.uuid4().hex[:12]}"

    def _request_path(self, request_id: str) -> Path:
        return self.review_dir / f"{request_id}.request.json"

    def _load_turn(self, *, session_id: str, turn_id: str) -> dict[str, Any]:
        turn = self.store.latest_event(session_id, "turn.started", turn_id)
        if turn is None:
            raise RuntimeError(f"Turn not found: {turn_id}")
        return turn["payload"]

    def _load_required_documents(self, *, session_id: str, turn_id: str) -> list[dict[str, Any]]:
        required = self.store.latest_event(session_id, "docs.required", turn_id)
        if required is None:
            return []
        return required["payload"].get("documents", [])

    def _load_request(self, request_id: str) -> dict[str, Any]:
        path = self._request_path(request_id)
        if not path.exists():
            raise RuntimeError(f"Browser review request not found: {request_id}")
        return json.loads(path.read_text(encoding="utf-8"))

    def request_review(
        self,
        *,
        session_id: str,
        turn_id: str,
        app_url: str | None = None,
        agent_run_id: str | None = None,
    ) -> dict[str, Any]:
        turn = self._load_turn(session_id=session_id, turn_id=turn_id)
        required_documents = self._load_required_documents(session_id=session_id, turn_id=turn_id)
        request_id = self._new_request_id()
        request_path = self._request_path(request_id)
        payload = {
            "request_id": request_id,
            "session_id": session_id,
            "turn_id": turn_id,
            "agent_run_id": agent_run_id,
            "validator": "playwright-mcp",
            "tool_name": "validator.browser",
            "app_url": app_url,
            "user_input": turn.get("user_input", ""),
            "target_paths": turn.get("target_paths", []),
            "required_doc_ids": [document["doc_id"] for document in required_documents],
            "checks": [
                "open the app in a real browser",
                "check console errors",
                "verify the relevant screen renders",
                "exercise the primary interaction when one is obvious",
                "capture screenshot or artifact references when available",
            ],
        }
        request_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        event_payload = {
            "turn_id": turn_id,
            "agent_run_id": agent_run_id,
            "request_id": request_id,
            "validator": "playwright-mcp",
            "tool_name": "validator.browser",
            "request_path": str(request_path.relative_to(self.repo_root)),
            "app_url": app_url,
            "target_paths": payload["target_paths"],
            "status": "requested",
        }
        self.store.emit_event(session_id, "validation.requested", event_payload)
        return {**event_payload, "request": payload}

    def record_review_result(
        self,
        *,
        session_id: str,
        turn_id: str,
        status: str,
        summary: str,
        request_id: str | None = None,
        artifacts: dict[str, Any] | None = None,
        agent_run_id: str | None = None,
    ) -> dict[str, Any]:
        normalized_status = status.strip().lower()
        if normalized_status not in VALID_BROWSER_STATUSES:
            raise ValueError(f"Unsupported browser review status: {status}")
        if not summary.strip():
            raise ValueError("Browser review summary is required.")

        request: dict[str, Any] = {}
        if request_id:
            request = self._load_request(request_id)
            if request.get("session_id") != session_id or request.get("turn_id") != turn_id:
                raise RuntimeError("Browser review request does not match the supplied session and turn.")

        turn = self._load_turn(session_id=session_id, turn_id=turn_id)
        required_documents = self._load_required_documents(session_id=session_id, turn_id=turn_id)
        target_paths = request.get("target_paths", turn.get("target_paths", []))
        required_doc_ids = request.get(
            "required_doc_ids",
            [document["doc_id"] for document in required_documents],
        )
        resolved_agent_run_id = agent_run_id if agent_run_id is not None else request.get("agent_run_id")
        tool_payload = {
            "turn_id": turn_id,
            "agent_run_id": resolved_agent_run_id,
            "validator": "playwright-mcp",
            "request_id": request_id,
            "target_paths": target_paths,
            "required_doc_ids": required_doc_ids,
        }

        try:
            authorization = self.gateway.begin_tool_call(
                session_id=session_id,
                turn_id=turn_id,
                name="validator.browser",
                payload=tool_payload,
                agent_run_id=resolved_agent_run_id,
            )
        except DocumentGateError:
            raise

        result = {
            **tool_payload,
            "tool_call_id": authorization["tool_call_id"],
            "status": normalized_status,
            "applicability": "required",
            "summary": summary.strip(),
            "artifacts": artifacts or {},
        }
        if normalized_status in {"failed", "error"}:
            self.gateway.fail_tool_call(
                session_id=session_id,
                turn_id=turn_id,
                name="validator.browser",
                error=result["summary"],
                tool_call_id=authorization["tool_call_id"],
                agent_run_id=resolved_agent_run_id,
            )
        else:
            self.gateway.complete_tool_call(
                session_id=session_id,
                turn_id=turn_id,
                name="validator.browser",
                payload=tool_payload,
                result=result,
                tool_call_id=authorization["tool_call_id"],
                agent_run_id=resolved_agent_run_id,
            )
        self.store.emit_event(session_id, "validation.completed", result)
        return result
