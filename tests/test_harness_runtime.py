from __future__ import annotations

import base64
import json
import os
import subprocess
import sys
import tempfile
import unittest
from datetime import UTC, datetime, timedelta
from pathlib import Path

from generated_harness import (
    CODEX_HOST_TOOL_EXAMPLES,
    ClarificationRequiredError,
    CodexHostGuard,
    ExecutionFlowVerifier,
    HarnessRuntime,
    HostAuditError,
    LocalProcessSandboxBackend,
    PlaywrightMcpBridge,
    SandboxBackendError,
    SandboxPolicyError,
    ToolPolicyError,
    WorkOrchestrator,
)
from generated_harness.agents import DefaultAgentExecutor
from generated_harness.document_gate import DocumentGateError
from generated_harness.requirement_analysis import RequirementAnalysisError
from generated_harness.session_store import FileSessionStore
from scripts.rebuild_doc_library import build_library


PROJECT_ROOT = Path(__file__).resolve().parents[1]


class HarnessRuntimeTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.repo_root = Path(self.temp_dir.name)
        (self.repo_root / "config").mkdir()
        (self.repo_root / "docs" / "guides").mkdir(parents=True)
        (self.repo_root / "docs" / "harness").mkdir(parents=True)
        (self.repo_root / "src" / "backend").mkdir(parents=True)
        (self.repo_root / "src" / "frontend").mkdir(parents=True)
        (self.repo_root / "src" / "theme" / "components").mkdir(parents=True)

        registry = {
            "documents": [
                {
                    "doc_id": "backend-rules",
                    "path": "docs/guides/backend.md",
                    "summary": "Backend rules",
                    "priority": 10,
                    "keywords": ["api", "backend"],
                    "intent_patterns": ["fix", "add"],
                    "path_globs": ["src/backend/**"],
                    "content_patterns": ["router\\."],
                    "labels": ["backend"],
                    "section_hints": ["security"],
                    "toc": {"max_chunk_lines": 50, "max_heading_depth": 3},
                },
                {
                    "doc_id": "frontend-rules",
                    "path": "docs/guides/frontend.md",
                    "summary": "Frontend rules",
                    "priority": 8,
                    "keywords": ["ui", "frontend"],
                    "intent_patterns": ["fix", "add"],
                    "path_globs": ["src/frontend/**"],
                    "content_patterns": ["useState\\("],
                    "labels": ["frontend"],
                    "section_hints": ["a11y"],
                    "toc": {"max_chunk_lines": 50, "max_heading_depth": 3},
                },
                {
                    "doc_id": "theme-fast-start",
                    "path": "docs/harness/theme-fast-start.md",
                    "summary": "Theme fast-start rules",
                    "priority": 99,
                    "keywords": ["theme", "token", "card"],
                    "intent_patterns": ["change", "update", "refactor"],
                    "path_globs": ["src/theme/**"],
                    "content_patterns": ["sharedComponentTokens", "ConfigProvider"],
                    "labels": ["theme", "theme-clarification", "workflow"],
                    "section_hints": ["Mandatory Clarification"],
                    "toc": {"max_chunk_lines": 50, "max_heading_depth": 3},
                },
            ]
        }
        (self.repo_root / "config" / "document_registry.json").write_text(json.dumps(registry), encoding="utf-8")
        (self.repo_root / "docs" / "guides" / "backend.md").write_text(
            "# Backend\n\n## Security\n\nCheck auth.\n\n## Error Handling\n\nReturn explicit errors.\n",
            encoding="utf-8",
        )
        (self.repo_root / "docs" / "guides" / "frontend.md").write_text(
            "# Frontend\n\n## Accessibility\n\nLabel controls.\n",
            encoding="utf-8",
        )
        (self.repo_root / "docs" / "harness" / "theme-fast-start.md").write_text(
            "# Theme Fast Start\n\n## Mandatory Clarification\n\nConfirm exact scope first.\n",
            encoding="utf-8",
        )
        (self.repo_root / "src" / "backend" / "api.py").write_text("router = object()\n", encoding="utf-8")
        (self.repo_root / "src" / "frontend" / "screen.tsx").write_text("useState()\n", encoding="utf-8")
        (self.repo_root / "src" / "theme" / "components" / "shared.ts").write_text(
            "export const sharedComponentTokens = {};\n",
            encoding="utf-8",
        )
        self.runtime = HarnessRuntime(self.repo_root)

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def python_command(self, code: str) -> str:
        encoded = base64.b64encode(code.encode("utf-8")).decode("ascii")
        return f'"{sys.executable}" -c "import base64; exec(base64.b64decode(\'{encoded}\').decode())"'

    def test_required_docs_match_and_block_write_until_ack(self) -> None:
        start = self.runtime.start_turn(
            user_input="Fix the API route and add better error handling",
            target_paths=["src/backend/api.py"],
        )
        analysis = self.runtime.store.latest_event(start["session_id"], "requirements.analyzed", start["turn_id"])
        self.assertIsNotNone(analysis)
        self.assertEqual(analysis["payload"]["status"], "completed")
        self.assertEqual([doc["doc_id"] for doc in start["required_documents"]], ["backend-rules"])
        with self.assertRaises(DocumentGateError):
            self.runtime.simulate_write(
                session_id=start["session_id"],
                turn_id=start["turn_id"],
                target_paths=["src/backend/api.py"],
            )
        self.runtime.acknowledge_required_docs(
            session_id=start["session_id"],
            turn_id=start["turn_id"],
            note="Reviewed backend constraints before execution.",
            documents=[
                {
                    "doc_id": "backend-rules",
                    "constraints": ["Use explicit API errors.", "Re-check auth and validation."],
                }
            ],
        )
        result = self.runtime.simulate_write(
            session_id=start["session_id"],
            turn_id=start["turn_id"],
            target_paths=["src/backend/api.py"],
        )
        self.assertEqual(result["status"], "noop")

    def test_theme_turn_requires_clarification_before_docs(self) -> None:
        start = self.runtime.start_turn(
            user_input="Card component theme color only. Do not touch button styles.",
            target_paths=["src/theme/components/shared.ts"],
        )
        self.assertEqual(start["status"], "awaiting_clarification")
        self.assertEqual(start["required_documents"], [])
        self.assertIsNone(start["planner_result"])
        self.assertIsNotNone(
            self.runtime.store.latest_event(start["session_id"], "clarification.required", start["turn_id"])
        )
        self.assertIsNone(
            self.runtime.store.latest_event(start["session_id"], "docs.required", start["turn_id"])
        )

    def test_theme_turn_blocks_until_clarification_then_requires_doc_ack(self) -> None:
        start = self.runtime.start_turn(
            user_input="Adjust Card theme token spacing only.",
            target_paths=["src/theme/components/shared.ts"],
        )
        with self.assertRaises(ClarificationRequiredError):
            self.runtime.simulate_write(
                session_id=start["session_id"],
                turn_id=start["turn_id"],
                target_paths=["src/theme/components/shared.ts"],
            )

        resolved = self.runtime.resolve_clarification(
            session_id=start["session_id"],
            turn_id=start["turn_id"],
            clarification_response="Change only Card component tokens in light and dark mode. Keep other components unchanged.",
        )
        self.assertEqual(resolved["status"], "clarification_resolved")
        self.assertEqual([doc["doc_id"] for doc in resolved["required_documents"]], ["theme-fast-start"])
        self.assertIn("Confirmed theme clarification:", resolved["clarification"]["merged_user_input"])

        with self.assertRaises(DocumentGateError):
            self.runtime.simulate_write(
                session_id=start["session_id"],
                turn_id=start["turn_id"],
                target_paths=["src/theme/components/shared.ts"],
            )

        self.runtime.acknowledge_required_docs(
            session_id=start["session_id"],
            turn_id=start["turn_id"],
            auto=True,
        )
        result = self.runtime.simulate_write(
            session_id=start["session_id"],
            turn_id=start["turn_id"],
            target_paths=["src/theme/components/shared.ts"],
        )
        self.assertEqual(result["status"], "noop")

    def test_flow_verifier_detects_docs_required_before_clarification_resolution(self) -> None:
        start = self.runtime.start_turn(
            user_input="Adjust Card theme token spacing only.",
            target_paths=["src/theme/components/shared.ts"],
        )
        self.runtime.store.emit_event(
            start["session_id"],
            "docs.required",
            {
                "turn_id": start["turn_id"],
                "documents": [{"doc_id": "theme-fast-start", "path": "docs/harness/theme-fast-start.md"}],
            },
        )
        result = ExecutionFlowVerifier(self.runtime.store).verify_turn(
            session_id=start["session_id"],
            turn_id=start["turn_id"],
        )
        self.assertEqual(result.status, "failed")
        self.assertTrue(
            any(finding["code"] == "docs_required_before_clarification_resolved" for finding in result.findings)
        )

    def test_agents_receive_role_skills(self) -> None:
        start = self.runtime.start_turn(
            user_input="Fix the API route and add better error handling",
            target_paths=["src/backend/api.py"],
        )
        self.assertTrue(start["planner_result"]["output"]["skills"])
        planner_assigned = self.runtime.store.latest_event(start["session_id"], "agent.assigned", start["turn_id"])
        self.assertTrue(planner_assigned["payload"]["skills"])

        self.runtime.acknowledge_required_docs(
            session_id=start["session_id"],
            turn_id=start["turn_id"],
            auto=True,
        )
        implementer = self.runtime.run_implementer(session_id=start["session_id"], turn_id=start["turn_id"])
        reviewer = self.runtime.run_reviewer(session_id=start["session_id"], turn_id=start["turn_id"])
        self.assertTrue(implementer["output"]["skills"])
        self.assertTrue(reviewer["output"]["skills"])

    def test_implementer_blocks_until_required_docs_are_acknowledged(self) -> None:
        start = self.runtime.start_turn(
            user_input="Fix the API route and add better error handling",
            target_paths=["src/backend/api.py"],
        )
        with self.assertRaises(DocumentGateError):
            self.runtime.run_implementer(session_id=start["session_id"], turn_id=start["turn_id"])

    def test_codex_adapter_records_apply_patch_through_gateway(self) -> None:
        start = self.runtime.start_turn(
            user_input="Fix the API route and add better error handling",
            target_paths=["src/backend/api.py"],
        )
        with self.assertRaises(DocumentGateError):
            self.runtime.codex.begin(
                session_id=start["session_id"],
                turn_id=start["turn_id"],
                codex_tool_name="apply_patch",
                payload={"changed_paths": ["src/backend/api.py"]},
            )

        self.runtime.acknowledge_required_docs(
            session_id=start["session_id"],
            turn_id=start["turn_id"],
            auto=True,
        )
        authorization = self.runtime.codex.begin(
            session_id=start["session_id"],
            turn_id=start["turn_id"],
            codex_tool_name="apply_patch",
            payload={"changed_paths": ["src/backend/api.py"]},
            agent_run_id="implementer_test",
        )
        self.assertEqual(authorization["tool_name"], "git.apply_patch")
        self.assertTrue(authorization["tool_call_id"].startswith("tool_"))
        self.assertEqual(authorization["agent_run_id"], "implementer_test")
        self.assertTrue(authorization["requires_gate"])
        self.runtime.codex.complete(
            session_id=start["session_id"],
            turn_id=start["turn_id"],
            codex_tool_name="apply_patch",
            payload={"changed_paths": ["src/backend/api.py"]},
            result={"status": "applied", "changed_paths": ["src/backend/api.py"]},
            tool_call_id=authorization["tool_call_id"],
            agent_run_id="implementer_test",
        )
        changed = self.runtime.store.latest_event(start["session_id"], "repo.changed", start["turn_id"])
        self.assertEqual(changed["payload"]["tool_name"], "git.apply_patch")
        self.assertEqual(changed["payload"]["tool_call_id"], authorization["tool_call_id"])
        self.assertEqual(changed["payload"]["agent_run_id"], "implementer_test")

    def test_codex_recorded_call_auto_completes_with_tool_call_id(self) -> None:
        start = self.runtime.start_turn(
            user_input="Fix the API route and add better error handling",
            target_paths=["src/backend/api.py"],
        )
        self.runtime.acknowledge_required_docs(
            session_id=start["session_id"],
            turn_id=start["turn_id"],
            auto=True,
        )

        result = self.runtime.codex.recorded_call(
            session_id=start["session_id"],
            turn_id=start["turn_id"],
            codex_tool_name="apply_patch",
            payload={"changed_paths": ["src/backend/api.py"]},
            agent_run_id="implementer_test",
            action=lambda authorization: {
                "status": "applied",
                "changed_paths": ["src/backend/api.py"],
                "used_tool_call_id": authorization["tool_call_id"],
            },
        )

        completed = self.runtime.store.latest_event(start["session_id"], "tool.completed", start["turn_id"])
        changed = self.runtime.store.latest_event(start["session_id"], "repo.changed", start["turn_id"])
        self.assertEqual(result["status"], "applied")
        self.assertEqual(completed["payload"]["tool_call_id"], result["used_tool_call_id"])
        self.assertEqual(changed["payload"]["tool_call_id"], result["used_tool_call_id"])
        self.assertEqual(changed["payload"]["agent_run_id"], "implementer_test")

    def test_codex_recorded_call_auto_fails_when_action_raises(self) -> None:
        start = self.runtime.start_turn(
            user_input="Fix the API route and add better error handling",
            target_paths=["src/backend/api.py"],
        )
        self.runtime.acknowledge_required_docs(
            session_id=start["session_id"],
            turn_id=start["turn_id"],
            auto=True,
        )

        def broken_action(authorization):
            raise RuntimeError(f"host tool died after {authorization['tool_call_id']}")

        with self.assertRaises(RuntimeError):
            self.runtime.codex.recorded_call(
                session_id=start["session_id"],
                turn_id=start["turn_id"],
                codex_tool_name="apply_patch",
                payload={"changed_paths": ["src/backend/api.py"]},
                agent_run_id="implementer_test",
                action=broken_action,
            )

        called = self.runtime.store.latest_event(start["session_id"], "tool.called", start["turn_id"])
        failed = self.runtime.store.latest_event(start["session_id"], "tool.failed", start["turn_id"])
        self.assertEqual(failed["payload"]["tool_call_id"], called["payload"]["tool_call_id"])
        self.assertEqual(failed["payload"]["agent_run_id"], "implementer_test")
        self.assertIn("host tool died", failed["payload"]["error"])

    def test_codex_tool_call_context_fails_if_not_completed(self) -> None:
        start = self.runtime.start_turn(
            user_input="Fix the API route and add better error handling",
            target_paths=["src/backend/api.py"],
        )
        self.runtime.acknowledge_required_docs(
            session_id=start["session_id"],
            turn_id=start["turn_id"],
            auto=True,
        )

        with self.runtime.codex.tool_call(
            session_id=start["session_id"],
            turn_id=start["turn_id"],
            codex_tool_name="apply_patch",
            payload={"changed_paths": ["src/backend/api.py"]},
            agent_run_id="implementer_test",
        ) as tool_call:
            tool_call_id = tool_call.tool_call_id

        failed = self.runtime.store.latest_event(start["session_id"], "tool.failed", start["turn_id"])
        self.assertEqual(failed["payload"]["tool_call_id"], tool_call_id)
        self.assertIn("without complete", failed["payload"]["error"])

    def test_codex_host_guard_wraps_tool_and_requires_final_audit(self) -> None:
        start = self.runtime.start_turn(
            user_input="Fix the API route and add better error handling",
            target_paths=["src/backend/api.py"],
        )
        self.runtime.acknowledge_required_docs(
            session_id=start["session_id"],
            turn_id=start["turn_id"],
            auto=True,
        )
        guard = CodexHostGuard(
            self.runtime,
            session_id=start["session_id"],
            turn_id=start["turn_id"],
        )
        result = guard.recorded_call(
            codex_tool_name="apply_patch",
            payload={"changed_paths": ["src/backend/api.py"]},
            agent_run_id="implementer_test",
            action=lambda authorization: {
                "status": "applied",
                "changed_paths": ["src/backend/api.py"],
                "used_tool_call_id": authorization["tool_call_id"],
            },
        )
        self.assertEqual(result["status"], "applied")
        with self.assertRaises(HostAuditError) as raised:
            guard.require_final_audit()
        self.assertTrue(any(finding["code"] == "turn_not_completed" for finding in raised.exception.audit["findings"]))

    def test_codex_host_guard_final_audit_passes_completed_turn(self) -> None:
        start = self.runtime.start_turn(
            user_input="Fix the API route and add better error handling",
            target_paths=["src/backend/api.py"],
        )
        self.runtime.acknowledge_required_docs(
            session_id=start["session_id"],
            turn_id=start["turn_id"],
            auto=True,
        )
        WorkOrchestrator(self.runtime).enqueue_continue_turn(
            session_id=start["session_id"],
            turn_id=start["turn_id"],
        )
        WorkOrchestrator(self.runtime).run_next(session_id=start["session_id"])
        guard = CodexHostGuard(
            self.runtime,
            session_id=start["session_id"],
            turn_id=start["turn_id"],
        )
        audit = guard.require_final_audit(compact=True)
        self.assertEqual(audit["status"], "passed")
        self.assertTrue(Path(audit["compact"]["compact_path"]).exists())

    def test_codex_host_tool_examples_cover_required_host_actions(self) -> None:
        examples = {example.codex_tool_name: example for example in CODEX_HOST_TOOL_EXAMPLES}
        self.assertEqual(examples["apply_patch"].canonical_tool_name, "git.apply_patch")
        self.assertEqual(examples["functions.shell_command"].canonical_tool_name, "shell.run")
        self.assertEqual(examples["browser_review"].canonical_tool_name, "validator.browser")
        self.assertTrue(all(example.preferred_wrapper == "recorded_call" for example in examples.values()))

    def test_agent_run_failure_is_recorded_and_can_retry_without_losing_main_session(self) -> None:
        class FlakyExecutor(DefaultAgentExecutor):
            def __init__(self) -> None:
                self.failed_once = False

            def run(self, role, packet):
                if role == "implementer" and not self.failed_once:
                    self.failed_once = True
                    raise RuntimeError("agent worker died")
                return super().run(role, packet)

        runtime = HarnessRuntime(self.repo_root, executor=FlakyExecutor())
        start = runtime.start_turn(
            user_input="Fix the API route and add better error handling",
            target_paths=["src/backend/api.py"],
        )
        runtime.acknowledge_required_docs(
            session_id=start["session_id"],
            turn_id=start["turn_id"],
            auto=True,
        )
        with self.assertRaises(RuntimeError):
            runtime.run_implementer(session_id=start["session_id"], turn_id=start["turn_id"])

        failed = runtime.store.latest_event(start["session_id"], "agent.failed", start["turn_id"])
        self.assertEqual(failed["payload"]["role"], "implementer")
        self.assertTrue(failed["payload"]["agent_run_id"].startswith("implementer_"))
        self.assertIsNone(runtime.store.latest_event(start["session_id"], "turn.completed", start["turn_id"]))

        retry = runtime.run_implementer(session_id=start["session_id"], turn_id=start["turn_id"])
        self.assertEqual(retry["role"], "implementer")
        self.assertTrue(retry["agent_run_id"].startswith("implementer_"))
        self.assertNotEqual(retry["agent_run_id"], failed["payload"]["agent_run_id"])
        self.assertIsNotNone(runtime.store.latest_event(start["session_id"], "session.started"))

    def test_agent_run_start_records_heartbeat(self) -> None:
        start = self.runtime.start_turn(
            user_input="Fix the API route and add better error handling",
            target_paths=["src/backend/api.py"],
        )
        heartbeat = self.runtime.store.latest_event(start["session_id"], "agent.heartbeat", start["turn_id"])
        self.assertEqual(heartbeat["payload"]["role"], "planner")
        self.assertEqual(heartbeat["payload"]["agent_run_id"], start["planner_result"]["agent_run_id"])
        self.assertEqual(heartbeat["payload"]["status"], "running")

    def test_timed_out_agent_run_is_marked_and_can_retry_with_new_run_id(self) -> None:
        start = self.runtime.start_turn(
            user_input="Fix the API route and add better error handling",
            target_paths=["src/backend/api.py"],
        )
        self.runtime.acknowledge_required_docs(
            session_id=start["session_id"],
            turn_id=start["turn_id"],
            auto=True,
        )
        stale_run_id = self.runtime.start_agent_run(
            session_id=start["session_id"],
            turn_id=start["turn_id"],
            role="implementer",
        )
        heartbeat = self.runtime.store.latest_event(start["session_id"], "agent.heartbeat", start["turn_id"])
        future = datetime.fromisoformat(heartbeat["timestamp"]) + timedelta(seconds=10)

        stale = self.runtime.find_timed_out_agent_runs(
            session_id=start["session_id"],
            turn_id=start["turn_id"],
            timeout_seconds=5,
            now=future,
        )
        self.assertEqual([run["agent_run_id"] for run in stale], [stale_run_id])

        marked = self.runtime.mark_timed_out_agent_runs(
            session_id=start["session_id"],
            turn_id=start["turn_id"],
            timeout_seconds=5,
            now=future,
        )
        self.assertEqual(marked[0]["agent_run_id"], stale_run_id)
        self.assertEqual(marked[0]["status"], "timed_out")

        retry = self.runtime.run_implementer(session_id=start["session_id"], turn_id=start["turn_id"])
        self.assertNotEqual(retry["agent_run_id"], stale_run_id)
        self.assertTrue(retry["agent_run_id"].startswith("implementer_"))

    def test_completed_agent_run_is_not_marked_timed_out(self) -> None:
        start = self.runtime.start_turn(
            user_input="Fix the API route and add better error handling",
            target_paths=["src/backend/api.py"],
        )
        planner_heartbeat = self.runtime.store.latest_event(start["session_id"], "agent.heartbeat", start["turn_id"])
        future = datetime.fromisoformat(planner_heartbeat["timestamp"]) + timedelta(seconds=10)
        stale = self.runtime.find_timed_out_agent_runs(
            session_id=start["session_id"],
            turn_id=start["turn_id"],
            timeout_seconds=5,
            now=future,
        )
        self.assertEqual(stale, [])

    def test_manual_heartbeat_refreshes_timeout_window(self) -> None:
        start = self.runtime.start_turn(
            user_input="Fix the API route and add better error handling",
            target_paths=["src/backend/api.py"],
        )
        run_id = self.runtime.start_agent_run(
            session_id=start["session_id"],
            turn_id=start["turn_id"],
            role="reviewer",
        )
        first_heartbeat = self.runtime.store.latest_event(start["session_id"], "agent.heartbeat", start["turn_id"])
        self.runtime.record_agent_heartbeat(
            session_id=start["session_id"],
            turn_id=start["turn_id"],
            agent_run_id=run_id,
            role="reviewer",
            metadata={"source": "manual_test"},
        )
        latest_heartbeat = self.runtime.store.latest_event(start["session_id"], "agent.heartbeat", start["turn_id"])
        refreshed_now = datetime.fromisoformat(latest_heartbeat["timestamp"]) + timedelta(seconds=3)
        stale = self.runtime.find_timed_out_agent_runs(
            session_id=start["session_id"],
            turn_id=start["turn_id"],
            timeout_seconds=5,
            now=refreshed_now,
        )
        self.assertNotIn(run_id, [run["agent_run_id"] for run in stale])

    def test_tool_call_ids_link_gateway_events_to_agent_runs(self) -> None:
        start = self.runtime.start_turn(
            user_input="Fix the API route and add better error handling",
            target_paths=["src/backend/api.py"],
        )
        self.runtime.acknowledge_required_docs(
            session_id=start["session_id"],
            turn_id=start["turn_id"],
            auto=True,
        )
        authorization = self.runtime.tool_gateway.begin_tool_call(
            session_id=start["session_id"],
            turn_id=start["turn_id"],
            name="repo.write",
            payload={"changed_paths": ["src/backend/api.py"]},
            agent_run_id="implementer_test",
        )
        result = self.runtime.tool_gateway.complete_tool_call(
            session_id=start["session_id"],
            turn_id=start["turn_id"],
            name="repo.write",
            payload={"changed_paths": ["src/backend/api.py"]},
            result={"status": "written", "changed_paths": ["src/backend/api.py"]},
            tool_call_id=authorization["tool_call_id"],
            agent_run_id="implementer_test",
        )
        self.assertEqual(result["status"], "written")
        completed = self.runtime.store.latest_event(start["session_id"], "tool.completed", start["turn_id"])
        self.assertEqual(completed["payload"]["tool_call_id"], authorization["tool_call_id"])
        self.assertEqual(completed["payload"]["agent_run_id"], "implementer_test")

    def test_tool_gateway_redacts_sensitive_payload_values_from_event_log(self) -> None:
        start = self.runtime.start_turn(
            user_input="Fix the API route and add better error handling",
            target_paths=["src/backend/api.py"],
        )
        self.runtime.acknowledge_required_docs(
            session_id=start["session_id"],
            turn_id=start["turn_id"],
            auto=True,
        )
        result = self.runtime.tool_gateway.execute(
            session_id=start["session_id"],
            turn_id=start["turn_id"],
            name="repo.write",
            payload={
                "changed_paths": ["src/backend/api.py"],
                "api_token": "secret-token-value",
                "nested": {"password": "secret-password-value"},
            },
            agent_run_id="implementer_test",
        )
        self.assertEqual(result["payload"]["api_token"], "secret-token-value")
        event_text = json.dumps(self.runtime.store.get_events(start["session_id"]), ensure_ascii=False)
        self.assertNotIn("secret-token-value", event_text)
        self.assertNotIn("secret-password-value", event_text)
        self.assertIn("[redacted]", event_text)

    def test_tool_gateway_denies_credential_dump_tool(self) -> None:
        start = self.runtime.start_turn(
            user_input="Fix the API route and add better error handling",
            target_paths=["src/backend/api.py"],
        )
        self.runtime.acknowledge_required_docs(
            session_id=start["session_id"],
            turn_id=start["turn_id"],
            auto=True,
        )
        with self.assertRaises(ToolPolicyError):
            self.runtime.tool_gateway.begin_tool_call(
                session_id=start["session_id"],
                turn_id=start["turn_id"],
                name="credential.dump",
                payload={"api_token": "secret-token-value"},
                agent_run_id="implementer_test",
            )
        blocked = self.runtime.store.latest_event(start["session_id"], "tool.blocked", start["turn_id"])
        self.assertEqual(blocked["payload"]["tool_name"], "credential.dump")
        self.assertEqual(blocked["payload"]["reason"], "tool_denied")
        event_text = json.dumps(self.runtime.store.get_events(start["session_id"]), ensure_ascii=False)
        self.assertNotIn("secret-token-value", event_text)
        self.assertIn("[redacted]", event_text)

    def test_sandbox_adapter_records_replaceable_sandbox_boundary(self) -> None:
        start = self.runtime.start_turn(
            user_input="Fix the API route and add better error handling",
            target_paths=["src/backend/api.py"],
        )
        self.runtime.acknowledge_required_docs(
            session_id=start["session_id"],
            turn_id=start["turn_id"],
            auto=True,
        )
        sandbox = self.runtime.sandbox.provision(
            session_id=start["session_id"],
            turn_id=start["turn_id"],
            resources={"repo": "checkout"},
            agent_run_id="implementer_test",
        )
        self.assertTrue(sandbox["sandbox_ref"].startswith("sandbox_"))
        self.assertFalse(sandbox["credentials_visible"])

        executed = self.runtime.sandbox.execute(
            session_id=start["session_id"],
            turn_id=start["turn_id"],
            sandbox_ref=sandbox["sandbox_ref"],
            command="python -m pytest",
            agent_run_id="implementer_test",
        )
        self.assertEqual(executed["status"], "noop")
        self.assertEqual(executed["sandbox_ref"], sandbox["sandbox_ref"])
        self.assertTrue(executed["tool_call_id"].startswith("tool_"))

        sandbox_event = self.runtime.store.latest_event(start["session_id"], "sandbox.executed", start["turn_id"])
        self.assertEqual(sandbox_event["payload"]["sandbox_ref"], sandbox["sandbox_ref"])
        self.assertEqual(sandbox_event["payload"]["agent_run_id"], "implementer_test")
        self.assertEqual(sandbox_event["payload"]["tool_call_id"], executed["tool_call_id"])

    def test_sandbox_blocks_sensitive_resources_without_logging_secret_value(self) -> None:
        start = self.runtime.start_turn(
            user_input="Fix the API route and add better error handling",
            target_paths=["src/backend/api.py"],
        )
        self.runtime.acknowledge_required_docs(
            session_id=start["session_id"],
            turn_id=start["turn_id"],
            auto=True,
        )
        with self.assertRaises(SandboxPolicyError):
            self.runtime.sandbox.provision(
                session_id=start["session_id"],
                turn_id=start["turn_id"],
                resources={"api_token": "super-secret-token"},
                agent_run_id="implementer_test",
            )

        blocked = self.runtime.store.latest_event(start["session_id"], "sandbox.blocked", start["turn_id"])
        self.assertEqual(blocked["payload"]["reason"], "credentials_not_allowed")
        self.assertEqual(blocked["payload"]["details"]["sensitive_paths"], ["resources.api_token"])
        event_text = json.dumps(self.runtime.store.get_events(start["session_id"]), ensure_ascii=False)
        self.assertNotIn("super-secret-token", event_text)
        self.assertIsNone(self.runtime.store.latest_event(start["session_id"], "sandbox.provisioned", start["turn_id"]))

    def test_sandbox_provision_blocks_until_required_docs_are_acknowledged(self) -> None:
        start = self.runtime.start_turn(
            user_input="Fix the API route and add better error handling",
            target_paths=["src/backend/api.py"],
        )
        with self.assertRaises(DocumentGateError):
            self.runtime.sandbox.provision(
                session_id=start["session_id"],
                turn_id=start["turn_id"],
                resources={"repo": "checkout"},
            )
        blocked = self.runtime.store.latest_event(start["session_id"], "tool.blocked", start["turn_id"])
        self.assertEqual(blocked["payload"]["reason"], "required documents not acknowledged")

    def test_sandbox_execute_requires_known_active_sandbox(self) -> None:
        start = self.runtime.start_turn(
            user_input="Fix the API route and add better error handling",
            target_paths=["src/backend/api.py"],
        )
        self.runtime.acknowledge_required_docs(
            session_id=start["session_id"],
            turn_id=start["turn_id"],
            auto=True,
        )

        with self.assertRaises(SandboxPolicyError):
            self.runtime.sandbox.execute(
                session_id=start["session_id"],
                turn_id=start["turn_id"],
                sandbox_ref="sandbox_missing",
                command="python -m pytest",
                agent_run_id="implementer_test",
            )

        blocked = self.runtime.store.latest_event(start["session_id"], "sandbox.blocked", start["turn_id"])
        failed = self.runtime.store.latest_event(start["session_id"], "tool.failed", start["turn_id"])
        self.assertEqual(blocked["payload"]["reason"], "unknown_sandbox")
        self.assertEqual(blocked["payload"]["tool_call_id"], failed["payload"]["tool_call_id"])

    def test_sandbox_dispose_blocks_later_execution(self) -> None:
        start = self.runtime.start_turn(
            user_input="Fix the API route and add better error handling",
            target_paths=["src/backend/api.py"],
        )
        self.runtime.acknowledge_required_docs(
            session_id=start["session_id"],
            turn_id=start["turn_id"],
            auto=True,
        )
        sandbox = self.runtime.sandbox.provision(
            session_id=start["session_id"],
            turn_id=start["turn_id"],
            resources={"repo": "checkout"},
        )
        disposed = self.runtime.sandbox.dispose(
            session_id=start["session_id"],
            turn_id=start["turn_id"],
            sandbox_ref=sandbox["sandbox_ref"],
        )
        self.assertEqual(disposed["status"], "disposed")

        with self.assertRaises(SandboxPolicyError):
            self.runtime.sandbox.execute(
                session_id=start["session_id"],
                turn_id=start["turn_id"],
                sandbox_ref=sandbox["sandbox_ref"],
                command="python -m pytest",
            )

        blocked = self.runtime.store.latest_event(start["session_id"], "sandbox.blocked", start["turn_id"])
        self.assertEqual(blocked["payload"]["reason"], "sandbox_not_active")
        self.assertEqual(blocked["payload"]["details"]["status"], "disposed")

    def test_sandbox_handler_failure_marks_sandbox_failed_and_blocks_reuse(self) -> None:
        runtime = HarnessRuntime(
            self.repo_root,
            sandbox_handler=lambda payload: (_ for _ in ()).throw(RuntimeError("sandbox process crashed")),
        )
        start = runtime.start_turn(
            user_input="Fix the API route and add better error handling",
            target_paths=["src/backend/api.py"],
        )
        runtime.acknowledge_required_docs(
            session_id=start["session_id"],
            turn_id=start["turn_id"],
            auto=True,
        )
        sandbox = runtime.sandbox.provision(
            session_id=start["session_id"],
            turn_id=start["turn_id"],
            resources={"repo": "checkout"},
        )

        with self.assertRaises(RuntimeError):
            runtime.sandbox.execute(
                session_id=start["session_id"],
                turn_id=start["turn_id"],
                sandbox_ref=sandbox["sandbox_ref"],
                command="python -m pytest",
            )
        failed = runtime.store.latest_event(start["session_id"], "sandbox.failed", start["turn_id"])
        self.assertEqual(failed["payload"]["sandbox_ref"], sandbox["sandbox_ref"])

        with self.assertRaises(SandboxPolicyError):
            runtime.sandbox.execute(
                session_id=start["session_id"],
                turn_id=start["turn_id"],
                sandbox_ref=sandbox["sandbox_ref"],
                command="python -m pytest",
            )
        blocked = runtime.store.latest_event(start["session_id"], "sandbox.blocked", start["turn_id"])
        self.assertEqual(blocked["payload"]["details"]["status"], "failed")

    def test_local_process_sandbox_backend_executes_in_workspace_with_scrubbed_env(self) -> None:
        runtime = HarnessRuntime(
            self.repo_root,
            sandbox_backend=LocalProcessSandboxBackend(self.repo_root, default_timeout_seconds=5),
        )
        start = runtime.start_turn(
            user_input="Fix the API route and add better error handling",
            target_paths=["src/backend/api.py"],
        )
        runtime.acknowledge_required_docs(
            session_id=start["session_id"],
            turn_id=start["turn_id"],
            auto=True,
        )
        sandbox = runtime.sandbox.provision(
            session_id=start["session_id"],
            turn_id=start["turn_id"],
            resources={"copy_paths": ["src/backend/api.py"]},
            agent_run_id="implementer_test",
        )
        self.assertEqual(sandbox["backend"]["backend"], "local-process")
        self.assertEqual(sandbox["backend"]["copied_paths"], ["src/backend/api.py"])

        previous_value = os.environ.get("SHOULD_NOT_LEAK_TOKEN")
        os.environ["SHOULD_NOT_LEAK_TOKEN"] = "visible-secret"
        try:
            executed = runtime.sandbox.execute(
                session_id=start["session_id"],
                turn_id=start["turn_id"],
                sandbox_ref=sandbox["sandbox_ref"],
                command=self.python_command(
                    "import os\n"
                    "from pathlib import Path\n"
                    "print(Path('src/backend/api.py').read_text().strip())\n"
                    "print(os.environ.get('SHOULD_NOT_LEAK_TOKEN', 'missing'))\n"
                ),
                agent_run_id="implementer_test",
            )
        finally:
            if previous_value is None:
                os.environ.pop("SHOULD_NOT_LEAK_TOKEN", None)
            else:
                os.environ["SHOULD_NOT_LEAK_TOKEN"] = previous_value

        self.assertEqual(executed["status"], "completed")
        self.assertEqual(executed["returncode"], 0)
        self.assertIn("router = object()", executed["stdout"])
        self.assertIn("missing", executed["stdout"])
        event_text = json.dumps(runtime.store.get_events(start["session_id"]), ensure_ascii=False)
        self.assertNotIn("visible-secret", event_text)

        workspace_path = Path(executed["workspace_path"])
        self.assertTrue(workspace_path.exists())
        disposed = runtime.sandbox.dispose(
            session_id=start["session_id"],
            turn_id=start["turn_id"],
            sandbox_ref=sandbox["sandbox_ref"],
        )
        self.assertEqual(disposed["backend"]["backend"], "local-process")
        self.assertTrue(disposed["backend"]["workspace_removed"])
        self.assertFalse(workspace_path.exists())

    def test_local_process_sandbox_nonzero_command_does_not_kill_sandbox(self) -> None:
        runtime = HarnessRuntime(
            self.repo_root,
            sandbox_backend=LocalProcessSandboxBackend(self.repo_root, default_timeout_seconds=5),
        )
        start = runtime.start_turn(
            user_input="Fix the API route and add better error handling",
            target_paths=["src/backend/api.py"],
        )
        runtime.acknowledge_required_docs(
            session_id=start["session_id"],
            turn_id=start["turn_id"],
            auto=True,
        )
        sandbox = runtime.sandbox.provision(
            session_id=start["session_id"],
            turn_id=start["turn_id"],
            resources={},
        )

        failed_command = runtime.sandbox.execute(
            session_id=start["session_id"],
            turn_id=start["turn_id"],
            sandbox_ref=sandbox["sandbox_ref"],
            command=self.python_command("import sys\nprint('command failed')\nsys.exit(7)\n"),
        )
        self.assertEqual(failed_command["status"], "failed")
        self.assertEqual(failed_command["returncode"], 7)
        self.assertIsNone(runtime.store.latest_event(start["session_id"], "sandbox.failed", start["turn_id"]))

        successful_command = runtime.sandbox.execute(
            session_id=start["session_id"],
            turn_id=start["turn_id"],
            sandbox_ref=sandbox["sandbox_ref"],
            command=self.python_command("print('still active')\n"),
        )
        self.assertEqual(successful_command["status"], "completed")
        self.assertIn("still active", successful_command["stdout"])

    def test_local_process_sandbox_timeout_marks_sandbox_failed_and_blocks_reuse(self) -> None:
        runtime = HarnessRuntime(
            self.repo_root,
            sandbox_backend=LocalProcessSandboxBackend(self.repo_root, default_timeout_seconds=0.1),
        )
        start = runtime.start_turn(
            user_input="Fix the API route and add better error handling",
            target_paths=["src/backend/api.py"],
        )
        runtime.acknowledge_required_docs(
            session_id=start["session_id"],
            turn_id=start["turn_id"],
            auto=True,
        )
        sandbox = runtime.sandbox.provision(
            session_id=start["session_id"],
            turn_id=start["turn_id"],
            resources={},
        )

        with self.assertRaises(SandboxBackendError):
            runtime.sandbox.execute(
                session_id=start["session_id"],
                turn_id=start["turn_id"],
                sandbox_ref=sandbox["sandbox_ref"],
                command=self.python_command("import time\ntime.sleep(1)\n"),
            )
        failed = runtime.store.latest_event(start["session_id"], "sandbox.failed", start["turn_id"])
        self.assertIn("timed out", failed["payload"]["error"])

        with self.assertRaises(SandboxPolicyError):
            runtime.sandbox.execute(
                session_id=start["session_id"],
                turn_id=start["turn_id"],
                sandbox_ref=sandbox["sandbox_ref"],
                command=self.python_command("print('blocked')\n"),
            )
        blocked = runtime.store.latest_event(start["session_id"], "sandbox.blocked", start["turn_id"])
        self.assertEqual(blocked["payload"]["details"]["status"], "failed")

    def test_repeated_workflow_suggests_and_exports_skill(self) -> None:
        self.runtime.start_turn(
            user_input="Fix the API route and add better error handling",
            target_paths=["src/backend/api.py"],
        )
        repeated = self.runtime.start_turn(
            user_input="Fix the API route and add better error handling",
            target_paths=["src/backend/api.py"],
        )
        suggestions = repeated["requirement_analysis"]["skill_suggestions"]
        self.assertEqual(len(suggestions), 1)
        self.assertEqual(suggestions[0]["kind"], "repeated_workflow")

        memory = json.loads((self.repo_root / ".harness" / "requirement_memory.json").read_text(encoding="utf-8"))
        self.assertTrue(memory["skill_suggestions"])
        exported = self.runtime.skills.export_repeated_skill(suggestions[0])
        readme = exported.with_name("README.md")
        self.assertTrue(exported.exists())
        self.assertTrue(readme.exists())
        self.assertIn("workflow signature", exported.read_text(encoding="utf-8"))
        self.assertIn("## Validation", exported.read_text(encoding="utf-8"))
        self.assertIn("What this skill is", readme.read_text(encoding="utf-8"))
        self.assertEqual(self.runtime.skills.validate_exported_skill(exported)["status"], "passed")

    def test_export_repeated_skill_cli_is_idempotent_and_validates_output(self) -> None:
        self.runtime.start_turn(
            user_input="Fix the API route and add better error handling",
            target_paths=["src/backend/api.py"],
        )
        self.runtime.start_turn(
            user_input="Fix the API route and add better error handling",
            target_paths=["src/backend/api.py"],
        )

        first = subprocess.run(
            [
                sys.executable,
                str(PROJECT_ROOT / "scripts" / "export_repeated_skill.py"),
                "--repo-root",
                str(self.repo_root),
                "--json",
            ],
            cwd=PROJECT_ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(first.returncode, 0, first.stderr)
        first_output = json.loads(first.stdout)
        self.assertEqual(first_output["status"], "exported")
        self.assertEqual(first_output["validation"]["status"], "passed")

        second = subprocess.run(
            [
                sys.executable,
                str(PROJECT_ROOT / "scripts" / "export_repeated_skill.py"),
                "--repo-root",
                str(self.repo_root),
                "--json",
            ],
            cwd=PROJECT_ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(second.returncode, 0, second.stderr)
        second_output = json.loads(second.stdout)
        self.assertEqual(second_output["status"], "already_exists")
        self.assertEqual(second_output["validation"]["status"], "passed")

    def test_mutating_tool_blocks_without_requirement_analysis(self) -> None:
        session_id = "manual-session"
        turn_id = "manual-turn"
        self.runtime.store.emit_event(session_id, "session.started", {"session_id": session_id})
        self.runtime.store.emit_event(
            session_id,
            "turn.started",
            {
                "turn_id": turn_id,
                "user_input": "Fix the API route",
                "target_paths": ["src/backend/api.py"],
            },
        )
        with self.assertRaises(RequirementAnalysisError):
            self.runtime.tool_gateway.execute(
                session_id=session_id,
                turn_id=turn_id,
                name="repo.write",
                payload={"target_paths": ["src/backend/api.py"]},
            )
        blocked = self.runtime.store.latest_event(session_id, "tool.blocked", turn_id)
        self.assertEqual(blocked["payload"]["reason"], "requirements analysis not completed")

    def test_empty_user_input_blocks_requirement_analysis(self) -> None:
        with self.assertRaises(RequirementAnalysisError):
            self.runtime.start_turn(user_input="   ", target_paths=["src/backend/api.py"])

    def test_unknown_and_mutating_tools_block_until_ack(self) -> None:
        start = self.runtime.start_turn(
            user_input="Fix the API route and add better error handling",
            target_paths=["src/backend/api.py"],
        )
        read_result = self.runtime.tool_gateway.execute(
            session_id=start["session_id"],
            turn_id=start["turn_id"],
            name="repo.read",
            payload={"target_paths": ["src/backend/api.py"]},
        )
        self.assertEqual(read_result["status"], "noop")

        for tool_name in ["repo.write", "sandbox.execute", "shell.run", "filesystem.write", "custom.tool"]:
            with self.subTest(tool_name=tool_name):
                with self.assertRaises(DocumentGateError):
                    self.runtime.tool_gateway.execute(
                        session_id=start["session_id"],
                        turn_id=start["turn_id"],
                        name=tool_name,
                        payload={"target_paths": ["src/backend/api.py"]},
                    )

    def test_ack_expires_when_required_document_changes(self) -> None:
        start = self.runtime.start_turn(
            user_input="Fix the API route and add better error handling",
            target_paths=["src/backend/api.py"],
        )
        self.runtime.acknowledge_required_docs(
            session_id=start["session_id"],
            turn_id=start["turn_id"],
            auto=True,
        )
        (self.repo_root / "docs" / "guides" / "backend.md").write_text(
            "# Backend\n\n## Security\n\nUpdated constraints.\n",
            encoding="utf-8",
        )
        with self.assertRaises(DocumentGateError):
            self.runtime.simulate_write(
                session_id=start["session_id"],
                turn_id=start["turn_id"],
                target_paths=["src/backend/api.py"],
            )

    def test_intent_only_match_does_not_pull_unrelated_doc(self) -> None:
        start = self.runtime.start_turn(
            user_input="Fix the backend API error handling",
            target_paths=["src/backend/api.py"],
        )
        self.assertEqual([doc["doc_id"] for doc in start["required_documents"]], ["backend-rules"])

    def test_ack_requires_constraints_per_document(self) -> None:
        start = self.runtime.start_turn(
            user_input="Add API validation",
            target_paths=["src/backend/api.py"],
        )
        with self.assertRaises(DocumentGateError):
            self.runtime.acknowledge_required_docs(
                session_id=start["session_id"],
                turn_id=start["turn_id"],
                note="Read the docs.",
                documents=[{"doc_id": "backend-rules", "constraints": []}],
            )

    def test_previous_memory_does_not_force_unrelated_doc_by_itself(self) -> None:
        self.runtime.start_turn(
            user_input="Fix the frontend screen states",
            target_paths=["src/frontend/screen.tsx"],
        )
        start = self.runtime.start_turn(
            user_input="Fix the API route",
            target_paths=["src/backend/api.py"],
        )
        self.assertEqual([doc["doc_id"] for doc in start["required_documents"]], ["backend-rules"])

    def test_reviewer_emits_questions_and_memory_updates(self) -> None:
        start = self.runtime.start_turn(
            user_input="Add API validation",
            target_paths=["src/backend/api.py"],
        )
        self.runtime.acknowledge_required_docs(
            session_id=start["session_id"],
            turn_id=start["turn_id"],
            auto=True,
        )
        review = self.runtime.run_reviewer(session_id=start["session_id"], turn_id=start["turn_id"])
        self.assertTrue(any("error handling" in question.lower() for question in review["output"]["questions"]))
        memory = json.loads((self.repo_root / ".harness" / "requirement_memory.json").read_text(encoding="utf-8"))
        self.assertIn("backend", memory["active_labels"])
        self.assertTrue(memory["acknowledged_constraints"])

    def test_reviewer_skips_browser_review_for_non_ui_scope(self) -> None:
        start = self.runtime.start_turn(
            user_input="Add API validation",
            target_paths=["src/backend/api.py"],
        )
        self.runtime.acknowledge_required_docs(
            session_id=start["session_id"],
            turn_id=start["turn_id"],
            auto=True,
        )
        review = self.runtime.run_reviewer(session_id=start["session_id"], turn_id=start["turn_id"])
        browser_review = review["output"]["browser_review"]
        self.assertEqual(browser_review["validator"], "playwright-mcp")
        self.assertEqual(browser_review["status"], "skipped")
        self.assertEqual(browser_review["applicability"], "not_applicable")

        validation = self.runtime.store.latest_event(start["session_id"], "validation.completed", start["turn_id"])
        self.assertEqual(validation["payload"]["status"], "skipped")

    def test_reviewer_marks_browser_review_unavailable_for_ui_scope_without_handler(self) -> None:
        start = self.runtime.start_turn(
            user_input="Fix the frontend screen state",
            target_paths=["src/frontend/screen.tsx"],
        )
        self.runtime.acknowledge_required_docs(
            session_id=start["session_id"],
            turn_id=start["turn_id"],
            auto=True,
        )
        review = self.runtime.run_reviewer(session_id=start["session_id"], turn_id=start["turn_id"])
        browser_review = review["output"]["browser_review"]
        self.assertEqual(browser_review["validator"], "playwright-mcp")
        self.assertEqual(browser_review["status"], "unavailable")
        self.assertEqual(browser_review["applicability"], "required")

    def test_reviewer_records_playwright_handler_result_for_ui_scope(self) -> None:
        runtime = HarnessRuntime(
            self.repo_root,
            browser_review_handler=lambda request: {
                "status": "passed",
                "summary": "Playwright MCP loaded the screen without console errors.",
                "artifacts": {"screenshot": "screenshots/screen.png"},
            },
        )
        start = runtime.start_turn(
            user_input="Fix the frontend screen state",
            target_paths=["src/frontend/screen.tsx"],
        )
        runtime.acknowledge_required_docs(
            session_id=start["session_id"],
            turn_id=start["turn_id"],
            auto=True,
        )
        review = runtime.run_reviewer(session_id=start["session_id"], turn_id=start["turn_id"])
        browser_review = review["output"]["browser_review"]
        self.assertEqual(browser_review["status"], "passed")
        self.assertEqual(browser_review["artifacts"]["screenshot"], "screenshots/screen.png")

        validation = runtime.store.latest_event(start["session_id"], "validation.completed", start["turn_id"])
        self.assertEqual(validation["payload"]["validator"], "playwright-mcp")
        self.assertEqual(validation["payload"]["status"], "passed")
        self.assertTrue(validation["payload"]["tool_call_id"].startswith("tool_"))

        called = runtime.store.latest_event(start["session_id"], "tool.called", start["turn_id"])
        completed = runtime.store.latest_event(start["session_id"], "tool.completed", start["turn_id"])
        self.assertEqual(called["payload"]["tool_name"], "validator.browser")
        self.assertEqual(completed["payload"]["tool_name"], "validator.browser")
        self.assertEqual(completed["payload"]["tool_call_id"], validation["payload"]["tool_call_id"])
        self.assertEqual(called["payload"]["agent_run_id"], review["agent_run_id"])

    def test_reviewer_records_failed_browser_handler_without_failing_agent_session(self) -> None:
        def failing_browser_handler(request):
            raise RuntimeError("browser could not connect")

        runtime = HarnessRuntime(self.repo_root, browser_review_handler=failing_browser_handler)
        start = runtime.start_turn(
            user_input="Fix the frontend screen state",
            target_paths=["src/frontend/screen.tsx"],
        )
        runtime.acknowledge_required_docs(
            session_id=start["session_id"],
            turn_id=start["turn_id"],
            auto=True,
        )

        review = runtime.run_reviewer(session_id=start["session_id"], turn_id=start["turn_id"])
        browser_review = review["output"]["browser_review"]
        self.assertEqual(browser_review["status"], "failed")
        self.assertIn("browser could not connect", browser_review["summary"])

        failed_tool = runtime.store.latest_event(start["session_id"], "tool.failed", start["turn_id"])
        validation = runtime.store.latest_event(start["session_id"], "validation.completed", start["turn_id"])
        agent_failed = runtime.store.latest_event(start["session_id"], "agent.failed", start["turn_id"])
        self.assertEqual(failed_tool["payload"]["tool_name"], "validator.browser")
        self.assertEqual(failed_tool["payload"]["tool_call_id"], validation["payload"]["tool_call_id"])
        self.assertIsNone(agent_failed)

        quality = runtime.run_quality_review(session_id=start["session_id"], turn_id=start["turn_id"])
        self.assertEqual(quality["fallback_action"], "recommend_immediate_fix")
        self.assertTrue(any(finding["category"] == "validator_failed" for finding in quality["findings"]))

    def test_playwright_mcp_bridge_writes_request_and_records_passed_result(self) -> None:
        start = self.runtime.start_turn(
            user_input="Fix the frontend screen state",
            target_paths=["src/frontend/screen.tsx"],
        )
        self.runtime.acknowledge_required_docs(
            session_id=start["session_id"],
            turn_id=start["turn_id"],
            auto=True,
        )
        bridge = PlaywrightMcpBridge(self.repo_root, self.runtime.store, self.runtime.tool_gateway)
        request = bridge.request_review(
            session_id=start["session_id"],
            turn_id=start["turn_id"],
            app_url="http://localhost:3000",
            agent_run_id="reviewer_test",
        )
        request_path = self.repo_root / request["request_path"]
        self.assertTrue(request_path.exists())
        request_json = json.loads(request_path.read_text(encoding="utf-8"))
        self.assertEqual(request_json["tool_name"], "validator.browser")
        self.assertEqual(request_json["target_paths"], ["src/frontend/screen.tsx"])

        result = bridge.record_review_result(
            session_id=start["session_id"],
            turn_id=start["turn_id"],
            request_id=request["request_id"],
            status="passed",
            summary="Playwright MCP rendered the screen.",
            artifacts={"screenshot": "artifacts/screen.png"},
        )
        self.assertEqual(result["status"], "passed")
        self.assertTrue(result["tool_call_id"].startswith("tool_"))
        completed = self.runtime.store.latest_event(start["session_id"], "tool.completed", start["turn_id"])
        validation = self.runtime.store.latest_event(start["session_id"], "validation.completed", start["turn_id"])
        self.assertEqual(completed["payload"]["tool_name"], "validator.browser")
        self.assertEqual(validation["payload"]["tool_call_id"], result["tool_call_id"])

    def test_playwright_mcp_bridge_records_failed_result_as_tool_failed(self) -> None:
        start = self.runtime.start_turn(
            user_input="Fix the frontend screen state",
            target_paths=["src/frontend/screen.tsx"],
        )
        self.runtime.acknowledge_required_docs(
            session_id=start["session_id"],
            turn_id=start["turn_id"],
            auto=True,
        )
        bridge = PlaywrightMcpBridge(self.repo_root, self.runtime.store, self.runtime.tool_gateway)
        request = bridge.request_review(
            session_id=start["session_id"],
            turn_id=start["turn_id"],
        )
        result = bridge.record_review_result(
            session_id=start["session_id"],
            turn_id=start["turn_id"],
            request_id=request["request_id"],
            status="failed",
            summary="Console error found.",
        )
        self.assertEqual(result["status"], "failed")
        failed = self.runtime.store.latest_event(start["session_id"], "tool.failed", start["turn_id"])
        validation = self.runtime.store.latest_event(start["session_id"], "validation.completed", start["turn_id"])
        self.assertEqual(failed["payload"]["tool_name"], "validator.browser")
        self.assertEqual(failed["payload"]["tool_call_id"], validation["payload"]["tool_call_id"])

    def test_playwright_mcp_review_cli_request_and_record(self) -> None:
        start = self.runtime.start_turn(
            user_input="Fix the frontend screen state",
            target_paths=["src/frontend/screen.tsx"],
        )
        self.runtime.acknowledge_required_docs(
            session_id=start["session_id"],
            turn_id=start["turn_id"],
            auto=True,
        )
        requested = subprocess.run(
            [
                sys.executable,
                str(PROJECT_ROOT / "scripts" / "playwright_mcp_review.py"),
                "--repo-root",
                str(self.repo_root),
                "--json",
                "request",
                "--session-id",
                start["session_id"],
                "--turn-id",
                start["turn_id"],
                "--app-url",
                "http://localhost:3000",
            ],
            cwd=PROJECT_ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(requested.returncode, 0, requested.stderr)
        request_output = json.loads(requested.stdout)
        self.assertEqual(request_output["status"], "requested")

        recorded = subprocess.run(
            [
                sys.executable,
                str(PROJECT_ROOT / "scripts" / "playwright_mcp_review.py"),
                "--repo-root",
                str(self.repo_root),
                "--json",
                "record",
                "--session-id",
                start["session_id"],
                "--turn-id",
                start["turn_id"],
                "--request-id",
                request_output["request_id"],
                "--status",
                "passed",
                "--summary",
                "Playwright MCP passed through CLI.",
                "--artifact",
                "screenshot=artifacts/screen.png",
            ],
            cwd=PROJECT_ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(recorded.returncode, 0, recorded.stderr)
        record_output = json.loads(recorded.stdout)
        self.assertEqual(record_output["status"], "passed")
        self.assertEqual(record_output["artifacts"]["screenshot"], "artifacts/screen.png")

    def test_continue_turn_runs_after_acknowledgement(self) -> None:
        start = self.runtime.start_turn(
            user_input="Fix the API route and add better error handling",
            target_paths=["src/backend/api.py"],
        )
        self.runtime.acknowledge_required_docs(
            session_id=start["session_id"],
            turn_id=start["turn_id"],
            auto=True,
        )
        continued = self.runtime.continue_turn(
            session_id=start["session_id"],
            turn_id=start["turn_id"],
        )
        self.assertEqual(continued["simulated_write"]["status"], "noop")
        self.assertIn("reviewer_result", continued)
        self.assertEqual(continued["quality_review"]["status"], "passed")
        self.assertEqual(continued["quality_review"]["fallback_action"], "complete")
        changed = self.runtime.store.latest_event(start["session_id"], "repo.changed", start["turn_id"])
        self.assertIsNotNone(changed)
        self.assertEqual(changed["payload"]["changed_paths"], ["src/backend/api.py"])

    def test_continue_turn_is_idempotent_after_completion(self) -> None:
        start = self.runtime.start_turn(
            user_input="Fix the API route and add better error handling",
            target_paths=["src/backend/api.py"],
        )
        self.runtime.acknowledge_required_docs(
            session_id=start["session_id"],
            turn_id=start["turn_id"],
            auto=True,
        )
        first = self.runtime.continue_turn(session_id=start["session_id"], turn_id=start["turn_id"])
        last_sequence = first["turn_completed"]["sequence"]
        second = self.runtime.continue_turn(session_id=start["session_id"], turn_id=start["turn_id"])
        self.assertEqual(second["status"], "already_completed")
        self.assertEqual(second["turn_completed"]["sequence"], last_sequence)

    def test_replay_turn_reconstructs_acknowledgement_next_action(self) -> None:
        start = self.runtime.start_turn(
            user_input="Fix the API route and add better error handling",
            target_paths=["src/backend/api.py"],
        )

        replayed = self.runtime.replay_turn(session_id=start["session_id"], turn_id=start["turn_id"])
        self.assertEqual(replayed["next_recommended_action"], "acknowledge_required_docs")
        self.assertEqual([doc["doc_id"] for doc in replayed["required_documents"]], ["backend-rules"])
        self.assertIsNone(replayed["docs_acknowledged"])
        self.assertEqual(replayed["open_tool_calls"], [])

    def test_replay_turn_detects_open_tool_call(self) -> None:
        start = self.runtime.start_turn(
            user_input="Fix the API route and add better error handling",
            target_paths=["src/backend/api.py"],
        )
        self.runtime.acknowledge_required_docs(
            session_id=start["session_id"],
            turn_id=start["turn_id"],
            auto=True,
        )
        authorization = self.runtime.tool_gateway.begin_tool_call(
            session_id=start["session_id"],
            turn_id=start["turn_id"],
            name="repo.write",
            payload={"changed_paths": ["src/backend/api.py"]},
            agent_run_id="implementer_test",
        )

        replayed = self.runtime.replay_turn(session_id=start["session_id"], turn_id=start["turn_id"])
        self.assertEqual(replayed["next_recommended_action"], "close_open_tool_calls")
        self.assertEqual([tool["tool_call_id"] for tool in replayed["open_tool_calls"]], [authorization["tool_call_id"]])

    def test_compact_turn_writes_summary_without_replacing_raw_events(self) -> None:
        start = self.runtime.start_turn(
            user_input="Fix the API route and add better error handling",
            target_paths=["src/backend/api.py"],
        )
        self.runtime.acknowledge_required_docs(
            session_id=start["session_id"],
            turn_id=start["turn_id"],
            auto=True,
        )
        self.runtime.continue_turn(session_id=start["session_id"], turn_id=start["turn_id"])
        raw_event_count = len(self.runtime.store.get_events(start["session_id"]))

        compacted = self.runtime.compact_turn(session_id=start["session_id"], turn_id=start["turn_id"])
        compact_path = Path(compacted["compact_path"])
        self.assertTrue(compact_path.exists())
        stored_compact = json.loads(compact_path.read_text(encoding="utf-8"))
        self.assertEqual(stored_compact["next_recommended_action"], "already_completed")
        self.assertIn("backend-rules", stored_compact["summary"])
        self.assertEqual(stored_compact["changed_paths"], ["src/backend/api.py"])
        compact_event = self.runtime.store.latest_event(start["session_id"], "session.compacted", start["turn_id"])
        self.assertEqual(compact_event["payload"]["cursor"], raw_event_count)
        self.assertGreater(len(self.runtime.store.get_events(start["session_id"])), raw_event_count)

    def test_session_store_rejects_unsafe_session_id(self) -> None:
        store = FileSessionStore(self.repo_root)
        with self.assertRaises(ValueError):
            store.emit_event("../escape", "session.started", {"session_id": "../escape"})

    def test_quality_review_warns_without_recorded_changes(self) -> None:
        start = self.runtime.start_turn(
            user_input="Fix the API route and add better error handling",
            target_paths=["src/backend/api.py"],
        )
        self.runtime.acknowledge_required_docs(
            session_id=start["session_id"],
            turn_id=start["turn_id"],
            auto=True,
        )
        self.runtime.run_reviewer(session_id=start["session_id"], turn_id=start["turn_id"])
        review = self.runtime.run_quality_review(session_id=start["session_id"], turn_id=start["turn_id"])
        self.assertEqual(review["status"], "needs_attention")
        self.assertEqual(review["fallback_action"], "complete_with_reminders")
        self.assertTrue(any(finding["category"] == "no_changes_recorded" for finding in review["findings"]))

    def test_quality_review_routes_failed_validation_to_fixer(self) -> None:
        start = self.runtime.start_turn(
            user_input="Fix the API route and add better error handling",
            target_paths=["src/backend/api.py"],
        )
        self.runtime.acknowledge_required_docs(
            session_id=start["session_id"],
            turn_id=start["turn_id"],
            auto=True,
        )
        self.runtime.simulate_write(
            session_id=start["session_id"],
            turn_id=start["turn_id"],
            target_paths=["src/backend/api.py"],
        )
        self.runtime.store.emit_event(
            start["session_id"],
            "validation.completed",
            {
                "turn_id": start["turn_id"],
                "status": "failed",
                "summary": "Type check failed in the touched backend file.",
                "target_paths": ["src/backend/api.py"],
            },
        )
        self.runtime.run_reviewer(session_id=start["session_id"], turn_id=start["turn_id"])
        review = self.runtime.run_quality_review(session_id=start["session_id"], turn_id=start["turn_id"])
        self.assertEqual(review["status"], "needs_attention")
        self.assertEqual(review["fallback_action"], "recommend_immediate_fix")
        fixer = self.runtime.run_fixer(
            session_id=start["session_id"],
            turn_id=start["turn_id"],
            findings=[finding["message"] for finding in review["findings"]],
        )
        self.assertEqual(fixer["status"], "recommended")

    def test_document_library_index_lists_section_files(self) -> None:
        (self.repo_root / "docs" / "guides" / "backend.md").write_text(
            "\n".join(
                [
                    "# Backend",
                    "Overview line.",
                    *[f"Overview detail {index}." for index in range(1, 45)],
                    "## Security",
                    "Check auth.",
                    "## Error Handling",
                    "Return explicit errors.",
                    "## Migrations",
                    "Keep rollback notes.",
                ]
            )
            + "\n",
            encoding="utf-8",
        )
        built = build_library(self.repo_root, self.repo_root / "config" / "document_registry.json")
        self.assertEqual(built, 3)
        index_text = (
            self.repo_root / ".harness" / "document_library" / "backend-rules" / "INDEX.md"
        ).read_text(encoding="utf-8")
        self.assertIn("- files:", index_text)
        self.assertIn("01-backend.md: Backend", index_text)
        self.assertIn("02-security.md: Security", index_text)

    def test_required_doc_eval_cli_passes_fixture_cases(self) -> None:
        case_file = self.repo_root / "config" / "required_doc_eval.json"
        case_file.write_text(
            json.dumps(
                {
                    "cases": [
                        {
                            "name": "backend",
                            "user_input": "Fix backend API behavior.",
                            "target_paths": ["src/backend/api.py"],
                            "expected_doc_ids": ["backend-rules"],
                        },
                        {
                            "name": "frontend",
                            "user_input": "Fix frontend UI state.",
                            "target_paths": ["src/frontend/screen.tsx"],
                            "expected_doc_ids": ["frontend-rules"],
                        },
                    ]
                }
            ),
            encoding="utf-8",
        )
        completed = subprocess.run(
            [
                sys.executable,
                str(PROJECT_ROOT / "scripts" / "run_doc_eval.py"),
                "--repo-root",
                str(self.repo_root),
                "--case-file",
                str(case_file),
                "--json",
            ],
            cwd=PROJECT_ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        output = json.loads(completed.stdout)
        self.assertEqual(output["status"], "passed")
        self.assertEqual(output["passed"], 2)

    def test_required_doc_eval_cli_reports_mismatch(self) -> None:
        case_file = self.repo_root / "config" / "required_doc_eval_bad.json"
        case_file.write_text(
            json.dumps(
                {
                    "cases": [
                        {
                            "name": "wrong_expectation",
                            "user_input": "Fix backend API behavior.",
                            "target_paths": ["src/backend/api.py"],
                            "expected_doc_ids": ["frontend-rules"],
                        }
                    ]
                }
            ),
            encoding="utf-8",
        )
        completed = subprocess.run(
            [
                sys.executable,
                str(PROJECT_ROOT / "scripts" / "run_doc_eval.py"),
                "--repo-root",
                str(self.repo_root),
                "--case-file",
                str(case_file),
                "--json",
            ],
            cwd=PROJECT_ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(completed.returncode, 1)
        output = json.loads(completed.stdout)
        self.assertEqual(output["status"], "failed")
        self.assertEqual(output["results"][0]["missing_doc_ids"], ["frontend-rules"])
        self.assertEqual(output["results"][0]["unexpected_doc_ids"], ["backend-rules"])

    def test_repo_hygiene_cli_passes_tracked_project_files(self) -> None:
        completed = subprocess.run(
            [
                sys.executable,
                str(PROJECT_ROOT / "scripts" / "check_repo_hygiene.py"),
                "--repo-root",
                str(PROJECT_ROOT),
                "--json",
            ],
            cwd=PROJECT_ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        output = json.loads(completed.stdout)
        self.assertEqual(output["status"], "passed")
        self.assertEqual(output["blocked_files"], [])

    def test_flow_verifier_passes_after_orchestrated_turn(self) -> None:
        start = self.runtime.start_turn(
            user_input="Fix the API route and add better error handling",
            target_paths=["src/backend/api.py"],
        )
        self.runtime.acknowledge_required_docs(
            session_id=start["session_id"],
            turn_id=start["turn_id"],
            auto=True,
        )
        orchestrator = WorkOrchestrator(self.runtime)
        queued = orchestrator.enqueue_continue_turn(
            session_id=start["session_id"],
            turn_id=start["turn_id"],
        )
        result = orchestrator.run_next(session_id=start["session_id"])
        self.assertEqual(result["status"], "completed")
        self.assertEqual(result["work_item"]["work_item_id"], queued["work_item_id"])

        flow_checked = self.runtime.store.latest_event(start["session_id"], "flow.checked", start["turn_id"])
        self.assertEqual(flow_checked["payload"]["status"], "passed")
        work_completed = self.runtime.store.latest_event(start["session_id"], "work.completed", start["turn_id"])
        self.assertEqual(work_completed["payload"]["flow_check"]["status"], "passed")

    def test_flow_verifier_detects_gated_tool_without_ack(self) -> None:
        start = self.runtime.start_turn(
            user_input="Fix the API route and add better error handling",
            target_paths=["src/backend/api.py"],
        )
        self.runtime.store.emit_event(
            start["session_id"],
            "tool.called",
            {
                "turn_id": start["turn_id"],
                "tool_call_id": "tool_bad",
                "agent_run_id": "agent_bad",
                "tool_name": "repo.write",
                "input": {"target_paths": ["src/backend/api.py"]},
                "requires_gate": True,
            },
        )
        result = ExecutionFlowVerifier(self.runtime.store).verify_turn(
            session_id=start["session_id"],
            turn_id=start["turn_id"],
        )
        self.assertEqual(result.status, "failed")
        self.assertTrue(any(finding["code"] == "gated_tool_without_ack" for finding in result.findings))

    def test_flow_verifier_detects_invalid_sandbox_lifecycle(self) -> None:
        start = self.runtime.start_turn(
            user_input="Fix the API route and add better error handling",
            target_paths=["src/backend/api.py"],
        )
        self.runtime.store.emit_event(
            start["session_id"],
            "sandbox.executed",
            {
                "turn_id": start["turn_id"],
                "sandbox_ref": "sandbox_missing",
                "tool_call_id": "tool_missing",
                "status": "completed",
            },
        )
        result = ExecutionFlowVerifier(self.runtime.store).verify_turn(
            session_id=start["session_id"],
            turn_id=start["turn_id"],
        )
        self.assertEqual(result.status, "failed")
        self.assertTrue(any(finding["code"] == "sandbox_event_without_provision" for finding in result.findings))

    def test_flow_verifier_detects_validation_tool_id_without_call(self) -> None:
        start = self.runtime.start_turn(
            user_input="Fix the frontend screen state",
            target_paths=["src/frontend/screen.tsx"],
        )
        self.runtime.store.emit_event(
            start["session_id"],
            "validation.completed",
            {
                "turn_id": start["turn_id"],
                "validator": "playwright-mcp",
                "status": "passed",
                "tool_call_id": "tool_missing",
            },
        )
        result = ExecutionFlowVerifier(self.runtime.store).verify_turn(
            session_id=start["session_id"],
            turn_id=start["turn_id"],
        )
        self.assertEqual(result.status, "failed")
        self.assertTrue(any(finding["code"] == "validation_without_tool_call" for finding in result.findings))

    def test_flow_verifier_detects_open_tool_call_at_turn_completion(self) -> None:
        start = self.runtime.start_turn(
            user_input="Fix the API route and add better error handling",
            target_paths=["src/backend/api.py"],
        )
        self.runtime.acknowledge_required_docs(
            session_id=start["session_id"],
            turn_id=start["turn_id"],
            auto=True,
        )
        self.runtime.tool_gateway.begin_tool_call(
            session_id=start["session_id"],
            turn_id=start["turn_id"],
            name="repo.write",
            payload={"changed_paths": ["src/backend/api.py"]},
            agent_run_id="implementer_test",
        )
        self.runtime.store.emit_event(
            start["session_id"],
            "quality.review_completed",
            {
                "turn_id": start["turn_id"],
                "status": "passed",
                "findings": [],
                "reminders": [],
                "fallback_action": "complete",
            },
        )
        self.runtime.complete_turn(
            session_id=start["session_id"],
            turn_id=start["turn_id"],
            summary="Forced completion for audit test.",
        )

        result = ExecutionFlowVerifier(self.runtime.store).verify_turn(
            session_id=start["session_id"],
            turn_id=start["turn_id"],
        )
        self.assertEqual(result.status, "failed")
        self.assertTrue(any(finding["code"] == "tool_call_without_terminal" for finding in result.findings))

    def test_flow_verifier_detects_repo_changed_without_tool_call_id(self) -> None:
        start = self.runtime.start_turn(
            user_input="Fix the API route and add better error handling",
            target_paths=["src/backend/api.py"],
        )
        self.runtime.store.emit_event(
            start["session_id"],
            "repo.changed",
            {
                "turn_id": start["turn_id"],
                "changed_paths": ["src/backend/api.py"],
                "source": "manual_unwrapped_change",
            },
        )
        result = ExecutionFlowVerifier(self.runtime.store).verify_turn(
            session_id=start["session_id"],
            turn_id=start["turn_id"],
        )
        self.assertEqual(result.status, "failed")
        self.assertTrue(any(finding["code"] == "repo_changed_missing_tool_call_id" for finding in result.findings))

    def test_flow_verifier_detects_work_started_without_lease(self) -> None:
        start = self.runtime.start_turn(
            user_input="Fix the API route and add better error handling",
            target_paths=["src/backend/api.py"],
        )
        self.runtime.store.emit_event(
            start["session_id"],
            "work.queued",
            {
                "turn_id": start["turn_id"],
                "work_item_id": "work_without_lease",
                "kind": "continue_turn",
                "status": "queued",
            },
        )
        self.runtime.store.emit_event(
            start["session_id"],
            "work.started",
            {
                "turn_id": start["turn_id"],
                "work_item_id": "work_without_lease",
                "kind": "continue_turn",
                "status": "running",
            },
        )
        result = ExecutionFlowVerifier(self.runtime.store).verify_turn(
            session_id=start["session_id"],
            turn_id=start["turn_id"],
        )
        self.assertEqual(result.status, "failed")
        self.assertTrue(any(finding["code"] == "work_started_without_lease" for finding in result.findings))

    def test_orchestrator_schedules_retry_when_work_fails(self) -> None:
        start = self.runtime.start_turn(
            user_input="Fix the API route and add better error handling",
            target_paths=["src/backend/api.py"],
        )
        orchestrator = WorkOrchestrator(self.runtime)
        queued = orchestrator.enqueue_continue_turn(
            session_id=start["session_id"],
            turn_id=start["turn_id"],
            max_attempts=2,
        )
        now = datetime(2026, 1, 1, tzinfo=UTC)
        result = orchestrator.run_next(session_id=start["session_id"], now=now)
        self.assertEqual(result["status"], "failed")
        failed = self.runtime.store.latest_event(start["session_id"], "work.failed", start["turn_id"])
        self.assertEqual(failed["payload"]["work_item_id"], queued["work_item_id"])
        retry = self.runtime.store.latest_event(start["session_id"], "work.retry_scheduled", start["turn_id"])
        self.assertEqual(retry["payload"]["retry_of"], queued["work_item_id"])
        self.assertEqual(retry["payload"]["attempt"], 2)
        self.assertEqual(retry["payload"]["retry_delay_seconds"], 2)
        self.assertEqual(orchestrator.pending_work(session_id=start["session_id"], now=now), [])
        self.assertEqual(
            [item["work_item_id"] for item in orchestrator.pending_work(session_id=start["session_id"], now=now + timedelta(seconds=3))],
            [retry["payload"]["work_item_id"]],
        )

    def test_orchestrator_cancelled_work_is_not_run(self) -> None:
        start = self.runtime.start_turn(
            user_input="Fix the API route and add better error handling",
            target_paths=["src/backend/api.py"],
        )
        orchestrator = WorkOrchestrator(self.runtime)
        queued = orchestrator.enqueue_continue_turn(
            session_id=start["session_id"],
            turn_id=start["turn_id"],
        )
        cancelled = orchestrator.cancel_work(
            session_id=start["session_id"],
            work_item_id=queued["work_item_id"],
            reason="test_cancel",
        )
        self.assertEqual(cancelled["status"], "cancelled")
        self.assertEqual(orchestrator.pending_work(session_id=start["session_id"]), [])
        self.assertEqual(orchestrator.run_next(session_id=start["session_id"])["status"], "idle")

    def test_orchestrator_lease_hides_work_until_expiry(self) -> None:
        start = self.runtime.start_turn(
            user_input="Fix the API route and add better error handling",
            target_paths=["src/backend/api.py"],
        )
        orchestrator = WorkOrchestrator(self.runtime)
        queued = orchestrator.enqueue_continue_turn(
            session_id=start["session_id"],
            turn_id=start["turn_id"],
        )
        now = datetime(2026, 1, 1, tzinfo=UTC)
        lease = orchestrator.acquire_lease(
            session_id=start["session_id"],
            work_item=queued,
            worker_id="worker-test",
            lease_seconds=5,
            now=now,
        )
        self.assertEqual(lease["worker_id"], "worker-test")
        self.assertEqual(orchestrator.pending_work(session_id=start["session_id"], now=now + timedelta(seconds=4)), [])
        self.assertEqual(
            [item["work_item_id"] for item in orchestrator.pending_work(session_id=start["session_id"], now=now + timedelta(seconds=6))],
            [queued["work_item_id"]],
        )

    def test_orchestrator_atomic_lease_denies_second_active_claim(self) -> None:
        start = self.runtime.start_turn(
            user_input="Fix the API route and add better error handling",
            target_paths=["src/backend/api.py"],
        )
        orchestrator = WorkOrchestrator(self.runtime)
        queued = orchestrator.enqueue_continue_turn(
            session_id=start["session_id"],
            turn_id=start["turn_id"],
        )
        now = datetime(2026, 1, 1, tzinfo=UTC)
        first = orchestrator.acquire_lease(
            session_id=start["session_id"],
            work_item=queued,
            worker_id="worker-one",
            lease_seconds=30,
            now=now,
        )
        second = orchestrator.acquire_lease(
            session_id=start["session_id"],
            work_item=queued,
            worker_id="worker-two",
            lease_seconds=30,
            now=now + timedelta(seconds=1),
        )
        self.assertEqual(first["status"], "leased")
        self.assertEqual(second["status"], "lease_denied")
        self.assertEqual(second["reason"], "work_item_not_claimable")
        lease_events = [
            event
            for event in self.runtime.store.get_events(start["session_id"])
            if event["event_type"] == "work.lease_acquired"
        ]
        self.assertEqual(len(lease_events), 1)
        self.assertEqual(lease_events[0]["payload"]["worker_id"], "worker-one")

    def test_session_store_emit_event_if_is_atomic_under_lock(self) -> None:
        session_id = "atomic-store"
        self.runtime.store.emit_event(session_id, "session.started", {"session_id": session_id})
        skipped = self.runtime.store.emit_event_if(
            session_id,
            "work.lease_acquired",
            {"work_item_id": "work_missing", "status": "leased"},
            lambda events: any(event["event_type"] == "work.queued" for event in events),
        )
        self.assertIsNone(skipped)
        self.assertIsNone(self.runtime.store.latest_event(session_id, "work.lease_acquired"))

    def test_orchestrator_marks_timed_out_agent_before_retrying_turn(self) -> None:
        runtime = HarnessRuntime(self.repo_root, agent_timeout_seconds=0)
        start = runtime.start_turn(
            user_input="Fix the API route and add better error handling",
            target_paths=["src/backend/api.py"],
        )
        runtime.acknowledge_required_docs(
            session_id=start["session_id"],
            turn_id=start["turn_id"],
            auto=True,
        )
        stale_run_id = runtime.start_agent_run(
            session_id=start["session_id"],
            turn_id=start["turn_id"],
            role="implementer",
        )
        orchestrator = WorkOrchestrator(runtime)
        orchestrator.enqueue_continue_turn(session_id=start["session_id"], turn_id=start["turn_id"])
        result = orchestrator.run_next(session_id=start["session_id"])
        self.assertEqual(result["status"], "completed")
        timed_out = runtime.store.latest_event(start["session_id"], "agent.timed_out", start["turn_id"])
        self.assertEqual(timed_out["payload"]["agent_run_id"], stale_run_id)
        completed = runtime.store.latest_event(start["session_id"], "work.completed", start["turn_id"])
        self.assertEqual(completed["payload"]["timed_out_agent_runs"][0]["agent_run_id"], stale_run_id)

    def test_check_flow_cli_reports_unclosed_tool_call(self) -> None:
        session_id = "cli-flow-bad"
        turn_id = "turn-bad"
        self.runtime.store.emit_event(session_id, "session.started", {"session_id": session_id})
        self.runtime.store.emit_event(
            session_id,
            "turn.started",
            {"turn_id": turn_id, "user_input": "Fix API", "target_paths": ["src/backend/api.py"]},
        )
        self.runtime.store.emit_event(session_id, "requirements.analyzed", {"turn_id": turn_id, "status": "completed"})
        self.runtime.store.emit_event(
            session_id,
            "tool.called",
            {
                "turn_id": turn_id,
                "tool_call_id": "tool_open",
                "tool_name": "repo.read",
                "input": {},
                "requires_gate": False,
            },
        )
        self.runtime.store.emit_event(
            session_id,
            "quality.review_completed",
            {"turn_id": turn_id, "status": "passed", "findings": [], "reminders": [], "fallback_action": "complete"},
        )
        self.runtime.store.emit_event(session_id, "turn.completed", {"turn_id": turn_id, "summary": "closed"})

        completed = subprocess.run(
            [
                sys.executable,
                str(PROJECT_ROOT / "scripts" / "check_flow.py"),
                "--repo-root",
                str(self.repo_root),
                "--session-id",
                session_id,
                "--turn-id",
                turn_id,
                "--json",
            ],
            cwd=PROJECT_ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(completed.returncode, 1)
        output = json.loads(completed.stdout)
        self.assertEqual(output["status"], "failed")
        self.assertTrue(any(finding["code"] == "tool_call_without_terminal" for finding in output["findings"]))

    def test_run_orchestrator_cli_enqueues_and_emits_flow_check(self) -> None:
        start = self.runtime.start_turn(
            user_input="Fix the API route and add better error handling",
            target_paths=["src/backend/api.py"],
        )
        self.runtime.acknowledge_required_docs(
            session_id=start["session_id"],
            turn_id=start["turn_id"],
            auto=True,
        )
        completed = subprocess.run(
            [
                sys.executable,
                str(PROJECT_ROOT / "scripts" / "run_orchestrator.py"),
                "--repo-root",
                str(self.repo_root),
                "--session-id",
                start["session_id"],
                "--turn-id",
                start["turn_id"],
                "--json",
            ],
            cwd=PROJECT_ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        output = json.loads(completed.stdout)
        self.assertEqual(output["status"], "completed")
        self.assertEqual(output["flow_check"]["status"], "passed")
        flow = self.runtime.store.latest_event(start["session_id"], "flow.checked", start["turn_id"])
        self.assertEqual(flow["payload"]["status"], "passed")

    def test_pre_final_audit_cli_passes_completed_turn_and_writes_compaction(self) -> None:
        start = self.runtime.start_turn(
            user_input="Fix the API route and add better error handling",
            target_paths=["src/backend/api.py"],
        )
        self.runtime.acknowledge_required_docs(
            session_id=start["session_id"],
            turn_id=start["turn_id"],
            auto=True,
        )
        orchestrator = WorkOrchestrator(self.runtime)
        orchestrator.enqueue_continue_turn(session_id=start["session_id"], turn_id=start["turn_id"])
        orchestrator.run_next(session_id=start["session_id"])

        completed = subprocess.run(
            [
                sys.executable,
                str(PROJECT_ROOT / "scripts" / "pre_final_audit.py"),
                "--repo-root",
                str(self.repo_root),
                "--session-id",
                start["session_id"],
                "--turn-id",
                start["turn_id"],
                "--compact",
                "--json",
            ],
            cwd=PROJECT_ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        output = json.loads(completed.stdout)
        self.assertEqual(output["status"], "passed")
        self.assertEqual(output["flow_status"], "passed")
        self.assertTrue(Path(output["compact"]["compact_path"]).exists())

    def test_pre_final_audit_cli_fails_incomplete_turn(self) -> None:
        start = self.runtime.start_turn(
            user_input="Fix the API route and add better error handling",
            target_paths=["src/backend/api.py"],
        )
        completed = subprocess.run(
            [
                sys.executable,
                str(PROJECT_ROOT / "scripts" / "pre_final_audit.py"),
                "--repo-root",
                str(self.repo_root),
                "--session-id",
                start["session_id"],
                "--turn-id",
                start["turn_id"],
                "--json",
            ],
            cwd=PROJECT_ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(completed.returncode, 1)
        output = json.loads(completed.stdout)
        self.assertEqual(output["status"], "failed")
        self.assertTrue(any(finding["code"] == "turn_not_completed" for finding in output["findings"]))


if __name__ == "__main__":
    unittest.main()
