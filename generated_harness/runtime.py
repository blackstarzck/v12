from __future__ import annotations

import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from .agents import AgentExecutor, DefaultAgentExecutor, build_packet
from .browser_review import BrowserReviewHandler, BrowserReviewRunner
from .checklists import build_post_run_questions
from .codex_adapter import CodexToolAdapter
from .document_gate import DocumentGate, DocumentGateError
from .document_registry import DocumentRegistry
from .quality_review import QualityReviewer
from .requirement_analysis import RequirementAnalyzer, ensure_requirements_analyzed
from .requirement_memory import RequirementMemory
from .sandbox_adapter import SandboxAdapter, SandboxBackend, SandboxHandler
from .session_replay import SessionReplayer
from .session_store import FileSessionStore
from .skill_registry import SkillRegistry
from .tool_gateway import ToolGateway


class HarnessRuntime:
    def __init__(
        self,
        repo_root: str | Path,
        *,
        executor: AgentExecutor | None = None,
        tool_handlers: dict[str, Any] | None = None,
        browser_review_handler: BrowserReviewHandler | None = None,
        sandbox_handler: SandboxHandler | None = None,
        sandbox_backend: SandboxBackend | None = None,
        agent_timeout_seconds: float = 300,
    ) -> None:
        self.repo_root = Path(repo_root).resolve()
        self.store = FileSessionStore(self.repo_root)
        self.memory = RequirementMemory(self.repo_root)
        self.registry = DocumentRegistry(self.repo_root)
        self.skills = SkillRegistry(self.repo_root)
        self.gate = DocumentGate(self.repo_root, self.store)
        self.analyzer = RequirementAnalyzer(self.repo_root, self.store, self.registry, self.memory, self.skills)
        self.tool_gateway = ToolGateway(store=self.store, gate=self.gate, handlers=tool_handlers)
        self.codex = CodexToolAdapter(self.tool_gateway)
        self.sandbox = SandboxAdapter(
            self.repo_root,
            self.store,
            self.tool_gateway,
            handler=sandbox_handler,
            backend=sandbox_backend,
        )
        self.replayer = SessionReplayer(self.repo_root, self.store)
        self.browser_review = BrowserReviewRunner(
            self.repo_root,
            self.store,
            handler=browser_review_handler,
            gateway=self.tool_gateway,
        )
        self.quality = QualityReviewer(self.repo_root, self.store)
        self.executor = executor or DefaultAgentExecutor()
        self.agent_timeout_seconds = agent_timeout_seconds

    def _ensure_session(self, session_id: str) -> None:
        if self.store.get_events(session_id):
            return
        self.store.emit_event(session_id, "session.started", {"session_id": session_id})

    def _new_agent_run_id(self, role: str) -> str:
        return f"{role}_{uuid.uuid4().hex[:12]}"

    def _event_timestamp(self, event: dict[str, Any]) -> datetime:
        return datetime.fromisoformat(str(event["timestamp"]))

    def record_agent_heartbeat(
        self,
        *,
        session_id: str,
        turn_id: str,
        agent_run_id: str,
        role: str | None = None,
        status: str = "running",
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        return self.store.emit_event(
            session_id,
            "agent.heartbeat",
            {
                "turn_id": turn_id,
                "agent_run_id": agent_run_id,
                "role": role,
                "status": status,
                "metadata": metadata or {},
            },
        )

    def _start_agent_run(
        self,
        *,
        session_id: str,
        turn_id: str,
        role: str,
        skills: list[dict[str, Any]],
        parent_agent_run_id: str | None = None,
    ) -> str:
        agent_run_id = self._new_agent_run_id(role)
        self.store.emit_event(
            session_id,
            "agent.started",
            {
                "turn_id": turn_id,
                "agent_run_id": agent_run_id,
                "parent_agent_run_id": parent_agent_run_id,
                "role": role,
                "status": "running",
            },
        )
        self.store.emit_event(
            session_id,
            "agent.assigned",
            {
                "turn_id": turn_id,
                "agent_run_id": agent_run_id,
                "parent_agent_run_id": parent_agent_run_id,
                "role": role,
                "skills": skills,
            },
        )
        self.record_agent_heartbeat(
            session_id=session_id,
            turn_id=turn_id,
            agent_run_id=agent_run_id,
            role=role,
            metadata={"source": "agent_start"},
        )
        return agent_run_id

    def start_agent_run(
        self,
        *,
        session_id: str,
        turn_id: str,
        role: str,
        skills: list[dict[str, Any]] | None = None,
        parent_agent_run_id: str | None = None,
    ) -> str:
        return self._start_agent_run(
            session_id=session_id,
            turn_id=turn_id,
            role=role,
            skills=skills or self.skills.skills_for_role(role),
            parent_agent_run_id=parent_agent_run_id,
        )

    def _complete_agent_run(
        self,
        *,
        session_id: str,
        turn_id: str,
        agent_run_id: str,
        result: Any,
    ) -> dict[str, Any]:
        payload = {"turn_id": turn_id, "agent_run_id": agent_run_id, **result.to_dict()}
        self.store.emit_event(session_id, "agent.completed", payload)
        return payload

    def _fail_agent_run(
        self,
        *,
        session_id: str,
        turn_id: str,
        agent_run_id: str,
        role: str,
        error: Exception,
    ) -> None:
        self.store.emit_event(
            session_id,
            "agent.failed",
            {
                "turn_id": turn_id,
                "agent_run_id": agent_run_id,
                "role": role,
                "status": "failed",
                "error": str(error),
            },
        )

    def find_timed_out_agent_runs(
        self,
        *,
        session_id: str,
        turn_id: str | None = None,
        timeout_seconds: float | None = None,
        now: datetime | None = None,
    ) -> list[dict[str, Any]]:
        timeout = self.agent_timeout_seconds if timeout_seconds is None else timeout_seconds
        now = now or datetime.now(UTC)
        events = self.store.get_events(session_id)
        terminal_ids = {
            event.get("payload", {}).get("agent_run_id")
            for event in events
            if event["event_type"] in {"agent.completed", "agent.failed", "agent.timed_out"}
        }
        runs: dict[str, dict[str, Any]] = {}
        for event in events:
            if event["event_type"] not in {"agent.started", "agent.heartbeat"}:
                continue
            payload = event.get("payload", {})
            run_turn_id = payload.get("turn_id")
            if turn_id and run_turn_id != turn_id:
                continue
            agent_run_id = payload.get("agent_run_id")
            if not agent_run_id or agent_run_id in terminal_ids:
                continue
            entry = runs.setdefault(
                str(agent_run_id),
                {
                    "turn_id": run_turn_id,
                    "agent_run_id": agent_run_id,
                    "role": payload.get("role"),
                    "last_event_type": event["event_type"],
                    "last_seen_at": event["timestamp"],
                    "seconds_since_heartbeat": 0.0,
                },
            )
            entry["role"] = payload.get("role") or entry.get("role")
            entry["last_event_type"] = event["event_type"]
            entry["last_seen_at"] = event["timestamp"]
        timed_out: list[dict[str, Any]] = []
        for entry in runs.values():
            last_seen = self._event_timestamp({"timestamp": entry["last_seen_at"]})
            seconds_since = (now - last_seen).total_seconds()
            entry["seconds_since_heartbeat"] = seconds_since
            if seconds_since >= timeout:
                timed_out.append(entry)
        return timed_out

    def mark_timed_out_agent_runs(
        self,
        *,
        session_id: str,
        turn_id: str | None = None,
        timeout_seconds: float | None = None,
        now: datetime | None = None,
    ) -> list[dict[str, Any]]:
        marked: list[dict[str, Any]] = []
        for stale_run in self.find_timed_out_agent_runs(
            session_id=session_id,
            turn_id=turn_id,
            timeout_seconds=timeout_seconds,
            now=now,
        ):
            event = self.store.emit_event(
                session_id,
                "agent.timed_out",
                {
                    **stale_run,
                    "status": "timed_out",
                    "timeout_seconds": self.agent_timeout_seconds if timeout_seconds is None else timeout_seconds,
                },
            )
            marked.append(event["payload"])
        return marked

    def start_turn(self, *, user_input: str, target_paths: list[str], session_id: str | None = None) -> dict[str, Any]:
        session_id = session_id or uuid.uuid4().hex[:12]
        turn_id = uuid.uuid4().hex[:8]
        self._ensure_session(session_id)
        self.store.emit_event(session_id, "turn.started", {"turn_id": turn_id, "user_input": user_input, "target_paths": target_paths})
        requirement_analysis, required_docs, memory = self.analyzer.analyze_turn(
            session_id=session_id,
            turn_id=turn_id,
            user_input=user_input,
            target_paths=target_paths,
        )
        self.gate.emit_required(session_id, turn_id, required_docs)

        required_payload = requirement_analysis["required_documents"]
        planner_skills = self.skills.skills_for_role("planner")
        planner_run_id = self._start_agent_run(
            session_id=session_id,
            turn_id=turn_id,
            role="planner",
            skills=planner_skills,
        )
        planner_packet = build_packet(
            role="planner",
            turn_id=turn_id,
            user_input=user_input,
            target_paths=target_paths,
            required_documents=required_payload,
            requirement_memory=memory,
            agent_run_id=planner_run_id,
            assigned_skills=planner_skills,
            extra={
                "inferred_intents": requirement_analysis["inferred_intents"],
                "requirement_analysis": requirement_analysis,
            },
        )
        try:
            planner_result = self.executor.run("planner", planner_packet)
        except Exception as exc:
            self._fail_agent_run(
                session_id=session_id,
                turn_id=turn_id,
                agent_run_id=planner_run_id,
                role="planner",
                error=exc,
            )
            raise
        planner_payload = self._complete_agent_run(
            session_id=session_id,
            turn_id=turn_id,
            agent_run_id=planner_run_id,
            result=planner_result,
        )

        updated_memory = self.memory.update(
            turn_id=turn_id,
            user_input=user_input,
            target_paths=target_paths,
            inferred_intents=requirement_analysis["inferred_intents"],
            required_docs=required_payload,
            reviewer_questions=requirement_analysis["reviewer_questions"],
            open_risks=requirement_analysis["open_risks"],
            registry_suggestions=requirement_analysis["registry_suggestions"],
            workflow_signature=requirement_analysis["workflow_signature"],
            skill_suggestions=requirement_analysis["skill_suggestions"],
        )
        self.store.emit_event(
            session_id,
            "requirements.updated",
            {
                "turn_id": turn_id,
                "inferred_intents": requirement_analysis["inferred_intents"],
                "required_doc_ids": [doc["doc_id"] for doc in required_payload],
                "registry_suggestions": requirement_analysis["registry_suggestions"],
                "skill_suggestions": requirement_analysis["skill_suggestions"],
            },
        )
        return {
            "session_id": session_id,
            "turn_id": turn_id,
            "required_documents": required_payload,
            "acknowledgement_template": self.gate.build_ack_template(required_payload),
            "planner_result": planner_payload,
            "requirement_memory": updated_memory,
            "requirement_analysis": requirement_analysis,
        }

    def _require_analysis_completed(self, *, session_id: str, turn_id: str) -> dict[str, Any]:
        return ensure_requirements_analyzed(
            self.store,
            session_id=session_id,
            turn_id=turn_id,
            block_event_type="turn.blocked",
        )

    def _latest_agent_result(self, *, session_id: str, turn_id: str, role: str) -> dict[str, Any] | None:
        for event in reversed(self.store.get_events(session_id)):
            payload = event.get("payload", {})
            if event["event_type"] == "agent.completed" and payload.get("turn_id") == turn_id and payload.get("role") == role:
                return payload
        return None

    def _latest_tool_result(self, *, session_id: str, turn_id: str, tool_name: str) -> dict[str, Any] | None:
        for event in reversed(self.store.get_events(session_id)):
            payload = event.get("payload", {})
            if event["event_type"] == "tool.completed" and payload.get("turn_id") == turn_id and payload.get("tool_name") == tool_name:
                result = payload.get("result")
                return result if isinstance(result, dict) else payload
        return None

    def _latest_payload(self, *, session_id: str, turn_id: str, event_type: str) -> dict[str, Any] | None:
        event = self.store.latest_event(session_id, event_type, turn_id)
        if event is None:
            return None
        return event["payload"]

    def build_acknowledgement_template(self, *, session_id: str, turn_id: str) -> dict[str, Any]:
        required_event = self.store.latest_event(session_id, "docs.required", turn_id)
        if required_event is None:
            raise DocumentGateError("No required documents found for this turn.")
        return self.gate.build_ack_template(required_event["payload"]["documents"])

    def acknowledge_required_docs(
        self,
        *,
        session_id: str,
        turn_id: str,
        note: str | None = None,
        documents: list[dict[str, Any]] | None = None,
        auto: bool = False,
    ) -> dict[str, Any]:
        required_event = self.store.latest_event(session_id, "docs.required", turn_id)
        if required_event is None:
            raise DocumentGateError("No required documents found for this turn.")
        ack_note = note or ""
        ack_documents = documents or []
        if auto:
            payload = self.gate.build_auto_ack_payload(required_event["payload"]["documents"])
            if not ack_note:
                ack_note = payload["note"]
            if not ack_documents:
                ack_documents = payload["documents"]
        acknowledgement = self.gate.acknowledge(
            session_id=session_id,
            turn_id=turn_id,
            note=ack_note,
            documents=ack_documents,
        )
        self.memory.record_acknowledgement(
            turn_id=turn_id,
            documents=acknowledgement["documents"],
            note=acknowledgement["note"],
        )
        return acknowledgement

    def run_implementer(self, *, session_id: str, turn_id: str) -> dict[str, Any]:
        self._require_analysis_completed(session_id=session_id, turn_id=turn_id)
        self.gate.ensure_open(session_id, turn_id)
        turn = self.store.latest_event(session_id, "turn.started", turn_id)
        required = self.store.latest_event(session_id, "docs.required", turn_id)
        if turn is None or required is None:
            raise RuntimeError("Turn is incomplete.")
        skills = self.skills.skills_for_role("implementer")
        agent_run_id = self._start_agent_run(
            session_id=session_id,
            turn_id=turn_id,
            role="implementer",
            skills=skills,
        )
        packet = build_packet(
            role="implementer",
            turn_id=turn_id,
            user_input=turn["payload"]["user_input"],
            target_paths=turn["payload"]["target_paths"],
            required_documents=required["payload"]["documents"],
            requirement_memory=self.memory.load(),
            agent_run_id=agent_run_id,
            assigned_skills=skills,
        )
        try:
            result = self.executor.run("implementer", packet)
        except Exception as exc:
            self._fail_agent_run(
                session_id=session_id,
                turn_id=turn_id,
                agent_run_id=agent_run_id,
                role="implementer",
                error=exc,
            )
            raise
        return self._complete_agent_run(
            session_id=session_id,
            turn_id=turn_id,
            agent_run_id=agent_run_id,
            result=result,
        )

    def simulate_write(
        self,
        *,
        session_id: str,
        turn_id: str,
        target_paths: list[str],
        agent_run_id: str | None = None,
    ) -> dict[str, Any]:
        self._require_analysis_completed(session_id=session_id, turn_id=turn_id)
        return self.tool_gateway.execute(
            session_id=session_id,
            turn_id=turn_id,
            name="repo.write",
            payload={"target_paths": target_paths, "mode": "simulated"},
            agent_run_id=agent_run_id,
        )

    def run_reviewer(self, *, session_id: str, turn_id: str) -> dict[str, Any]:
        self._require_analysis_completed(session_id=session_id, turn_id=turn_id)
        turn = self.store.latest_event(session_id, "turn.started", turn_id)
        required = self.store.latest_event(session_id, "docs.required", turn_id)
        if turn is None or required is None:
            raise RuntimeError("Turn is incomplete.")
        questions = build_post_run_questions(required["payload"]["documents"], turn["payload"]["target_paths"])
        skills = self.skills.skills_for_role("reviewer")
        agent_run_id = self._start_agent_run(
            session_id=session_id,
            turn_id=turn_id,
            role="reviewer",
            skills=skills,
        )
        packet = build_packet(
            role="reviewer",
            turn_id=turn_id,
            user_input=turn["payload"]["user_input"],
            target_paths=turn["payload"]["target_paths"],
            required_documents=required["payload"]["documents"],
            requirement_memory=self.memory.load(),
            agent_run_id=agent_run_id,
            assigned_skills=skills,
            extra={"questions": questions},
        )
        try:
            result = self.executor.run("reviewer", packet)
            browser_result = self.browser_review.review(
                session_id=session_id,
                turn_id=turn_id,
                user_input=turn["payload"]["user_input"],
                target_paths=turn["payload"]["target_paths"],
                required_documents=required["payload"]["documents"],
                agent_run_id=agent_run_id,
            )
            result.output["browser_review"] = browser_result
        except Exception as exc:
            self._fail_agent_run(
                session_id=session_id,
                turn_id=turn_id,
                agent_run_id=agent_run_id,
                role="reviewer",
                error=exc,
            )
            raise
        payload = self._complete_agent_run(
            session_id=session_id,
            turn_id=turn_id,
            agent_run_id=agent_run_id,
            result=result,
        )
        self.store.emit_event(
            session_id,
            "reviewer.questions_ready",
            {
                "turn_id": turn_id,
                "agent_run_id": agent_run_id,
                "questions": result.output.get("questions", questions),
            },
        )
        return payload

    def run_fixer(self, *, session_id: str, turn_id: str, findings: list[str]) -> dict[str, Any]:
        self._require_analysis_completed(session_id=session_id, turn_id=turn_id)
        turn = self.store.latest_event(session_id, "turn.started", turn_id)
        required = self.store.latest_event(session_id, "docs.required", turn_id)
        if turn is None or required is None:
            raise RuntimeError("Turn is incomplete.")
        skills = self.skills.skills_for_role("fixer")
        agent_run_id = self._start_agent_run(
            session_id=session_id,
            turn_id=turn_id,
            role="fixer",
            skills=skills,
        )
        packet = build_packet(
            role="fixer",
            turn_id=turn_id,
            user_input=turn["payload"]["user_input"],
            target_paths=turn["payload"]["target_paths"],
            required_documents=required["payload"]["documents"],
            requirement_memory=self.memory.load(),
            agent_run_id=agent_run_id,
            assigned_skills=skills,
            extra={"findings": findings},
        )
        try:
            result = self.executor.run("fixer", packet)
        except Exception as exc:
            self._fail_agent_run(
                session_id=session_id,
                turn_id=turn_id,
                agent_run_id=agent_run_id,
                role="fixer",
                error=exc,
            )
            raise
        return self._complete_agent_run(
            session_id=session_id,
            turn_id=turn_id,
            agent_run_id=agent_run_id,
            result=result,
        )

    def run_quality_review(self, *, session_id: str, turn_id: str) -> dict[str, Any]:
        self._require_analysis_completed(session_id=session_id, turn_id=turn_id)
        return self.quality.review_turn(session_id=session_id, turn_id=turn_id)

    def continue_turn(self, *, session_id: str, turn_id: str) -> dict[str, Any]:
        self._require_analysis_completed(session_id=session_id, turn_id=turn_id)
        turn = self.store.latest_event(session_id, "turn.started", turn_id)
        if turn is None:
            raise RuntimeError("Turn is incomplete.")
        already_completed = self.store.latest_event(session_id, "turn.completed", turn_id)
        if already_completed is not None:
            return {
                "session_id": session_id,
                "turn_id": turn_id,
                "status": "already_completed",
                "turn_completed": already_completed,
                "quality_review": self._latest_payload(
                    session_id=session_id,
                    turn_id=turn_id,
                    event_type="quality.review_completed",
                ),
            }
        target_paths = turn["payload"]["target_paths"]
        output: dict[str, Any] = {
            "session_id": session_id,
            "turn_id": turn_id,
            "resume": {"executed_steps": [], "skipped_steps": []},
        }
        implementer_result = self._latest_agent_result(session_id=session_id, turn_id=turn_id, role="implementer")
        if implementer_result is None:
            output["implementer_result"] = self.run_implementer(session_id=session_id, turn_id=turn_id)
            output["resume"]["executed_steps"].append("implementer")
        else:
            output["implementer_result"] = implementer_result
            output["resume"]["skipped_steps"].append("implementer")

        simulated_write = self._latest_tool_result(session_id=session_id, turn_id=turn_id, tool_name="repo.write")
        if simulated_write is None:
            output["simulated_write"] = self.simulate_write(
                session_id=session_id,
                turn_id=turn_id,
                target_paths=target_paths,
                agent_run_id=output["implementer_result"].get("agent_run_id"),
            )
            output["resume"]["executed_steps"].append("simulated_write")
        else:
            output["simulated_write"] = simulated_write
            output["resume"]["skipped_steps"].append("simulated_write")

        reviewer_result = self._latest_agent_result(session_id=session_id, turn_id=turn_id, role="reviewer")
        if reviewer_result is None:
            output["reviewer_result"] = self.run_reviewer(session_id=session_id, turn_id=turn_id)
            output["resume"]["executed_steps"].append("reviewer")
        else:
            output["reviewer_result"] = reviewer_result
            output["resume"]["skipped_steps"].append("reviewer")

        quality_review = self._latest_payload(session_id=session_id, turn_id=turn_id, event_type="quality.review_completed")
        if quality_review is None:
            output["quality_review"] = self.run_quality_review(session_id=session_id, turn_id=turn_id)
            output["resume"]["executed_steps"].append("quality_review")
        else:
            output["quality_review"] = quality_review
            output["resume"]["skipped_steps"].append("quality_review")
        fallback_action = output["quality_review"]["fallback_action"]
        if fallback_action in {"recommend_immediate_fix", "recommend_specialist_fixer"}:
            findings = [finding["message"] for finding in output["quality_review"]["findings"]]
            fixer_result = self._latest_agent_result(session_id=session_id, turn_id=turn_id, role="fixer")
            if fixer_result is None:
                output["fixer_result"] = self.run_fixer(session_id=session_id, turn_id=turn_id, findings=findings)
                output["resume"]["executed_steps"].append("fixer")
            else:
                output["fixer_result"] = fixer_result
                output["resume"]["skipped_steps"].append("fixer")
            if self.store.latest_event(session_id, "turn.needs_attention", turn_id) is None:
                self.store.emit_event(
                    session_id,
                    "turn.needs_attention",
                    {
                        "turn_id": turn_id,
                        "fallback_action": fallback_action,
                        "findings": output["quality_review"]["findings"],
                    },
                )
        output["turn_completed"] = self.complete_turn(
            session_id=session_id,
            turn_id=turn_id,
            summary=f"Turn finished with quality fallback action: {fallback_action}.",
        )
        return output

    def complete_turn(self, *, session_id: str, turn_id: str, summary: str) -> dict[str, Any]:
        return self.store.emit_event(session_id, "turn.completed", {"turn_id": turn_id, "summary": summary})

    def replay_turn(self, *, session_id: str, turn_id: str) -> dict[str, Any]:
        return self.replayer.replay_turn(session_id=session_id, turn_id=turn_id)

    def compact_turn(self, *, session_id: str, turn_id: str) -> dict[str, Any]:
        return self.replayer.compact_turn(session_id=session_id, turn_id=turn_id)
