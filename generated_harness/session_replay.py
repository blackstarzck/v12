from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from .session_store import FileSessionStore


SAFE_COMPACT_NAME = re.compile(r"[^A-Za-z0-9_.-]+")


class SessionReplayer:
    """Rebuild turn state and compact context from the durable event log."""

    def __init__(self, repo_root: str | Path, store: FileSessionStore) -> None:
        self.repo_root = Path(repo_root).resolve()
        self.store = store
        self.compact_dir = self.repo_root / ".harness" / "compact"

    def _compact_path(self, session_id: str, turn_id: str) -> Path:
        safe_session = SAFE_COMPACT_NAME.sub("_", session_id)
        safe_turn = SAFE_COMPACT_NAME.sub("_", turn_id)
        return self.compact_dir / f"{safe_session}-{safe_turn}.json"

    def _agent_statuses(self, events: list[dict[str, Any]]) -> tuple[dict[str, dict[str, Any]], list[dict[str, Any]]]:
        agents: dict[str, dict[str, Any]] = {}
        for event in events:
            if not event["event_type"].startswith("agent."):
                continue
            payload = event.get("payload", {})
            agent_run_id = payload.get("agent_run_id")
            if not agent_run_id:
                continue
            entry = agents.setdefault(
                str(agent_run_id),
                {
                    "agent_run_id": agent_run_id,
                    "role": payload.get("role"),
                    "status": "running",
                    "started_at": None,
                    "last_seen_at": event.get("timestamp"),
                },
            )
            entry["role"] = payload.get("role") or entry.get("role")
            entry["last_seen_at"] = event.get("timestamp")
            if event["event_type"] == "agent.started":
                entry["started_at"] = event.get("timestamp")
                entry["status"] = "running"
            elif event["event_type"] == "agent.completed":
                entry["status"] = "completed"
                entry["summary"] = payload.get("summary")
            elif event["event_type"] == "agent.failed":
                entry["status"] = "failed"
                entry["error"] = payload.get("error")
            elif event["event_type"] == "agent.timed_out":
                entry["status"] = "timed_out"
        open_agents = [agent for agent in agents.values() if agent.get("status") == "running"]
        return agents, open_agents

    def _tool_statuses(self, events: list[dict[str, Any]]) -> tuple[dict[str, dict[str, Any]], list[dict[str, Any]]]:
        tools: dict[str, dict[str, Any]] = {}
        for event in events:
            if event["event_type"] not in {"tool.called", "tool.completed", "tool.failed"}:
                continue
            payload = event.get("payload", {})
            tool_call_id = payload.get("tool_call_id")
            if not tool_call_id:
                continue
            entry = tools.setdefault(
                str(tool_call_id),
                {
                    "tool_call_id": tool_call_id,
                    "tool_name": payload.get("tool_name"),
                    "agent_run_id": payload.get("agent_run_id"),
                    "sandbox_ref": payload.get("sandbox_ref"),
                    "status": "called",
                },
            )
            entry["tool_name"] = payload.get("tool_name") or entry.get("tool_name")
            entry["agent_run_id"] = payload.get("agent_run_id") or entry.get("agent_run_id")
            entry["sandbox_ref"] = payload.get("sandbox_ref") or entry.get("sandbox_ref")
            if event["event_type"] == "tool.completed":
                entry["status"] = "completed"
                entry["result"] = payload.get("result")
            elif event["event_type"] == "tool.failed":
                entry["status"] = "failed"
                entry["error"] = payload.get("error")
        open_tools = [tool for tool in tools.values() if tool.get("status") == "called"]
        return tools, open_tools

    def _sandbox_statuses(self, events: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
        sandboxes: dict[str, dict[str, Any]] = {}
        for event in events:
            payload = event.get("payload", {})
            sandbox_ref = payload.get("sandbox_ref")
            if not sandbox_ref:
                continue
            entry = sandboxes.setdefault(
                str(sandbox_ref),
                {
                    "sandbox_ref": sandbox_ref,
                    "status": "unknown",
                    "backend": None,
                    "last_tool_call_id": None,
                },
            )
            entry["last_tool_call_id"] = payload.get("tool_call_id") or entry.get("last_tool_call_id")
            if event["event_type"] == "sandbox.provisioned":
                entry["status"] = "provisioned"
                entry["backend"] = payload.get("backend")
            elif event["event_type"] == "sandbox.executed":
                entry["status"] = "active"
                entry["last_result_status"] = payload.get("status")
            elif event["event_type"] == "sandbox.failed":
                entry["status"] = "failed"
                entry["error"] = payload.get("error")
            elif event["event_type"] == "sandbox.disposed":
                entry["status"] = "disposed"
        return sandboxes

    def _next_action(self, state: dict[str, Any]) -> str:
        if state["turn_completed"]:
            return "already_completed"
        if not state["requirements_analyzed"]:
            return "analyze_requirements"
        if state["clarification_required"] and not state["clarification_resolved"]:
            return "resolve_clarification"
        if state["required_documents"] and not state["docs_acknowledged"]:
            return "acknowledge_required_docs"
        if state["open_tool_calls"]:
            return "close_open_tool_calls"
        if state["open_agent_runs"]:
            return "check_agent_heartbeats"
        if not state["quality_review"]:
            return "continue_orchestrator"
        return "complete_turn"

    def replay_turn(self, *, session_id: str, turn_id: str) -> dict[str, Any]:
        events = [
            event
            for event in self.store.get_events(session_id)
            if event.get("payload", {}).get("turn_id") == turn_id or event["event_type"] == "session.started"
        ]
        turn_started = next((event for event in events if event["event_type"] == "turn.started"), None)
        requirements = next((event for event in events if event["event_type"] == "requirements.analyzed"), None)
        clarification_required = next((event for event in events if event["event_type"] == "clarification.required"), None)
        clarification_resolved = next(
            (event for event in reversed(events) if event["event_type"] == "clarification.resolved"),
            None,
        )
        docs_required = next((event for event in events if event["event_type"] == "docs.required"), None)
        docs_acknowledged = next((event for event in events if event["event_type"] == "docs.acknowledged"), None)
        quality_review = next(
            (event for event in reversed(events) if event["event_type"] == "quality.review_completed"),
            None,
        )
        turn_completed = next((event for event in reversed(events) if event["event_type"] == "turn.completed"), None)
        changed_paths = sorted(
            {
                str(path)
                for event in events
                if event["event_type"] == "repo.changed"
                for path in event.get("payload", {}).get("changed_paths", [])
            }
        )
        agents, open_agents = self._agent_statuses(events)
        tools, open_tools = self._tool_statuses(events)
        sandboxes = self._sandbox_statuses(events)
        validations = [
            event.get("payload", {})
            for event in events
            if event["event_type"] in {"validation.requested", "validation.completed"}
        ]
        state = {
            "session_id": session_id,
            "turn_id": turn_id,
            "cursor": max([int(event.get("sequence", 0)) for event in events], default=0),
            "event_count": len(events),
            "turn_started": turn_started.get("payload") if turn_started else None,
            "requirements_analyzed": requirements.get("payload") if requirements else None,
            "clarification_required": clarification_required.get("payload") if clarification_required else None,
            "clarification_resolved": clarification_resolved.get("payload") if clarification_resolved else None,
            "required_documents": docs_required.get("payload", {}).get("documents", []) if docs_required else [],
            "docs_acknowledged": docs_acknowledged.get("payload") if docs_acknowledged else None,
            "agents": list(agents.values()),
            "open_agent_runs": open_agents,
            "tools": list(tools.values()),
            "open_tool_calls": open_tools,
            "sandboxes": list(sandboxes.values()),
            "changed_paths": changed_paths,
            "validations": validations,
            "quality_review": quality_review.get("payload") if quality_review else None,
            "turn_completed": turn_completed.get("payload") if turn_completed else None,
        }
        state["next_recommended_action"] = self._next_action(state)
        return state

    def compact_turn(self, *, session_id: str, turn_id: str) -> dict[str, Any]:
        state = self.replay_turn(session_id=session_id, turn_id=turn_id)
        required_doc_ids = [doc.get("doc_id") for doc in state["required_documents"]]
        acknowledged_doc_ids = [
            doc.get("doc_id")
            for doc in (state["docs_acknowledged"] or {}).get("documents", [])
            if isinstance(doc, dict)
        ]
        validation_statuses = [
            validation.get("status")
            for validation in state["validations"]
            if validation.get("status")
        ]
        sandbox_statuses = {
            sandbox["sandbox_ref"]: sandbox.get("status")
            for sandbox in state["sandboxes"]
        }
        summary_parts = [
            f"Turn {turn_id} next action: {state['next_recommended_action']}.",
            f"Required docs: {', '.join(required_doc_ids) if required_doc_ids else 'none'}.",
            f"Acknowledged docs: {', '.join(acknowledged_doc_ids) if acknowledged_doc_ids else 'none'}.",
            f"Changed paths: {', '.join(state['changed_paths']) if state['changed_paths'] else 'none'}.",
        ]
        if state["clarification_required"]:
            summary_parts.append(
                "Clarification: "
                + ("resolved." if state["clarification_resolved"] else "pending.")
            )
        if state["quality_review"]:
            summary_parts.append(f"Quality fallback: {state['quality_review'].get('fallback_action')}.")
        compact = {
            "session_id": session_id,
            "turn_id": turn_id,
            "cursor": state["cursor"],
            "event_count": state["event_count"],
            "summary": " ".join(summary_parts),
            "required_doc_ids": required_doc_ids,
            "acknowledged_doc_ids": acknowledged_doc_ids,
            "clarification_status": "resolved" if state["clarification_resolved"] else ("pending" if state["clarification_required"] else "not_required"),
            "changed_paths": state["changed_paths"],
            "open_tool_calls": state["open_tool_calls"],
            "open_agent_runs": state["open_agent_runs"],
            "sandbox_statuses": sandbox_statuses,
            "validation_statuses": validation_statuses,
            "quality_fallback_action": (state["quality_review"] or {}).get("fallback_action"),
            "next_recommended_action": state["next_recommended_action"],
        }
        self.compact_dir.mkdir(parents=True, exist_ok=True)
        compact_path = self._compact_path(session_id, turn_id)
        compact_path.write_text(json.dumps(compact, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        self.store.emit_event(
            session_id,
            "session.compacted",
            {
                "turn_id": turn_id,
                "cursor": compact["cursor"],
                "compact_path": str(compact_path.relative_to(self.repo_root)),
                "summary": compact["summary"],
                "next_recommended_action": compact["next_recommended_action"],
            },
        )
        return {**compact, "compact_path": str(compact_path)}
