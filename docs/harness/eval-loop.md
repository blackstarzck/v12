# requirement-gated-python-harness Eval Loop

## Minimal Eval Plan

1. deterministic success path
2. resume or replay path
3. boundary-mismatch check
4. baseline comparison
5. post-run reminder checklist check
6. quality fallback routing check
7. requirement-analysis hard-gate check
8. role-skill assignment check
9. repeated-workflow skill suggestion check
10. reviewer browser verification check
11. Codex tool adapter gate check
12. idempotent resume check
13. agent-run failure isolation check
14. tool-call and sandbox boundary check
15. Codex recorded-call wrapper check
16. agent heartbeat timeout check
17. orchestrator queue flow check
18. sandbox lifecycle and credential-boundary check
19. audited browser validation check
20. Playwright MCP bridge check
21. Codex host-tool audit check
22. operator CLI check
23. local-process sandbox backend check
24. session replay and compaction check
25. required-document eval CLI check
26. repeated-skill export idempotence check
27. orchestrator cancellation, lease, and retry backoff check
28. tool audit redaction check
29. pre-final audit CLI check
30. Codex host guard check
31. tool denylist check
32. repository hygiene check

## Deterministic Success Path

- task: modify a known file set with one required document
- expected: turn.started -> requirements.analyzed -> docs.required -> acknowledgement template generated -> docs.acknowledged -> agent.started -> agent.heartbeat -> agent.completed -> tool.called -> tool.completed -> repo.changed -> reviewer.questions_ready -> quality.review_completed -> turn.completed

## Resume Check

- crash after docs.required
- resume by session_id
- verify tool execution stays blocked until docs.acknowledged exists
- verify the acknowledgement template can still be reused after resume

## Boundary-Mismatch Check

- compare document registry output against tool gateway expectations
- verify mutating and unknown tools block when `requirements.analyzed` is missing
- compare validation event schema against reviewer consumer
- compare four-condition matcher output against real target files

## Baseline Comparison

Run the same task twice:

- with required-doc gating
- without required-doc gating

Compare:

- correctness
- completeness
- repeatability
- operator effort

## Reminder Checklist Check

- run a turn that touches a backend or frontend file
- confirm reviewer outputs reminder questions about risk, error handling, security, and missing scope

## Quality Fallback Routing Check

- no findings: `fallback_action=complete`
- reminder-only findings: `fallback_action=complete_with_reminders`
- one failed validator: `fallback_action=recommend_immediate_fix`
- many failed validators or findings: `fallback_action=recommend_specialist_fixer`

The reminder path should not hard-block by default. It should behave like a senior teammate asking, "Did you also check this?" before the final report.

## Requirement-Analysis Hard-Gate Check

- create a manual turn event without `requirements.analyzed`
- call a mutating tool through the gateway
- expected: `RequirementAnalysisError` and `tool.blocked`
- then start a normal turn and verify `requirements.analyzed` appears before `docs.required`

## Role-Skill Assignment Check

- start a normal turn
- verify `planner`, `implementer`, `reviewer`, and `fixer` packets include `assigned_skills`
- verify `agent.assigned` events record the role skills

## Repeated-Workflow Skill Suggestion Check

- run the same intent and target path group twice
- verify requirement memory records a `skill_suggestions` item
- export the suggestion and verify `.codex/skills/<skill-id>/SKILL.md` exists

## Reviewer Browser Verification Check

- backend-only task: reviewer records Playwright MCP validation as `skipped` with `applicability=not_applicable`
- UI task without browser handler: reviewer records `unavailable` with `applicability=required`
- UI task with browser handler: reviewer records the handler's `passed` or `failed` result as `validation.completed`
- quality review aggregates those events but does not run Playwright MCP directly

## Codex Tool Adapter Gate Check

- start a turn with one required document
- call `runtime.codex.recorded_call(..., codex_tool_name="apply_patch")` before acknowledgement
- expected: `DocumentGateError`
- acknowledge required documents
- call `recorded_call` around a successful host action
- expected: `tool.called`, `tool.completed`, and `repo.changed` record `git.apply_patch`, `tool_call_id`, and `agent_run_id`
- call `recorded_call` around a host action that raises
- expected: `tool.failed` records the same `tool_call_id` and the exception is re-raised

## Idempotent Resume Check

- finish a turn through `continue_turn`
- call `continue_turn` again with the same `session_id` and `turn_id`
- expected: return `status=already_completed` and do not emit duplicate agent/tool/review events

## Agent-Run Failure Isolation Check

- run an implementer with an executor that fails once
- expected: `agent.started` and `agent.failed` are recorded with the failed `agent_run_id`
- expected: the main `session_id` remains readable and no `turn.completed` event is emitted
- retry implementer
- expected: retry succeeds with a new `agent_run_id`

## Agent Heartbeat Timeout Check

- start a role execution and verify `agent.heartbeat` is recorded
- move the timeout clock past the allowed window
- expected: `find_timed_out_agent_runs(...)` returns the stale `agent_run_id`
- call `mark_timed_out_agent_runs(...)`
- expected: `agent.timed_out` is recorded and a retry can use a new `agent_run_id`
- complete a role normally and verify it is not later marked timed out

## Orchestrator Queue Flow Check

- enqueue a resumable turn through `WorkOrchestrator.enqueue_continue_turn(...)`
- run it with `WorkOrchestrator.run_next(...)`
- expected: `work.queued`, `work.started`, `work.completed`, and `flow.checked`
- expected: `flow.checked.status=passed`
- create a malformed event stream with a gated tool before `docs.acknowledged`
- expected: `ExecutionFlowVerifier.verify_turn(...)` returns `status=failed`
- enqueue a turn that cannot continue because docs were not acknowledged
- expected: `work.failed` and `work.retry_scheduled`

## Tool-Call And Sandbox Boundary Check

- call a mutating tool through `ToolGateway.begin_tool_call`
- expected: authorization returns a `tool_call_id`
- complete the tool call
- expected: `tool.completed` and `repo.changed` preserve the same `tool_call_id`
- provision and execute a sandbox through `SandboxAdapter`
- expected: `sandbox.provisioned`, `tool.called`, `tool.completed`, and `sandbox.executed` share the same `sandbox_ref`
- try to execute an unknown, disposed, or failed `sandbox_ref`
- expected: `sandbox.blocked` and `tool.failed`; the main session remains resumable
- try to provision or execute with a credential-looking key such as `api_token`
- expected: `sandbox.blocked`, no secret value appears in the session log, and no sandbox execution occurs

## Local-Process Sandbox Backend Check

- configure `LocalProcessSandboxBackend`
- provision with `copy_paths`
- execute a Python command inside the copied workspace
- expected: stdout is captured, return code is recorded, and the sandbox remains separate from the main repo
- set a token-like host environment variable
- expected: the variable is not visible inside the sandbox command and is not written to the event log
- run a timeout command
- expected: `tool.failed` and `sandbox.failed` are recorded, then later reuse of the same sandbox is blocked

## Session Replay And Compaction Check

- replay a turn after `docs.required`
- expected: `next_recommended_action=acknowledge_required_docs`
- replay a turn with an open `tool.called`
- expected: `next_recommended_action=close_open_tool_calls`
- compact a completed turn
- expected: `.harness/compact/<session>-<turn>.json` exists, `session.compacted` is emitted, and raw events remain available

## Required-Document Eval CLI Check

- run `py scripts/run_doc_eval.py --json`
- expected: all fixture cases pass, including current TALKPIK UI, theme,
  component-customization, Korean-language, and non-UI doc cases
- create one intentionally wrong expected doc id
- expected: CLI exits 1 and reports missing and unexpected doc ids

## Repeated-Skill Export Idempotence Check

- run repeated turns until a skill suggestion appears
- run `py scripts/export_repeated_skill.py --json`
- expected: the first run exports `SKILL.md` and `README.md`
- run the export command again without `--overwrite`
- expected: status is `already_exists`, validation still passes, and no duplicate skill folder is created

## Orchestrator Cancellation, Lease, And Retry Backoff Check

- cancel queued work
- expected: pending work becomes empty and `run_next` returns idle
- acquire a work lease
- expected: pending work is hidden until the lease expires
- try to acquire the same active work item from a second worker
- expected: the second claim returns `lease_denied` and no duplicate `work.lease_acquired` event is written
- trigger a failed work item with retries available
- expected: `work.retry_scheduled` includes `retry_delay_seconds` and `available_at`, and pending work waits until that time

## Tool Audit Redaction Check

- call a tool with keys such as `api_token` and nested `password`
- expected: the caller receives its normal result, but the durable session log stores `[redacted]` instead of secret values

## Tool Denylist Check

- call `credential.dump` through `ToolGateway.begin_tool_call(...)`
- expected: `ToolPolicyError` is raised
- expected: `tool.blocked(reason=tool_denied)` is recorded
- expected: credential-looking payload values are redacted in the session log

## Pre-Final Audit CLI Check

- complete a turn through the orchestrator
- run `py scripts/pre_final_audit.py --session-id <session> --turn-id <turn> --compact --json`
- expected: status is `passed`, flow status is `passed`, and a compact summary file exists
- run the same audit on an incomplete turn
- expected: CLI exits 1 and reports `turn_not_completed`

## Audited Browser Validation Check

- run UI-impacting work with a configured browser review handler
- expected: `tool.called`, `tool.completed`, and `validation.completed` share the same `tool_call_id`
- make the browser review handler raise an exception
- expected: `tool.failed` and `validation.completed(status=failed)` share the same `tool_call_id`
- expected: the reviewer agent is not marked failed only because the browser handler failed

## Playwright MCP Bridge Check

- run `py scripts/playwright_mcp_review.py request --session-id <session> --turn-id <turn> --json`
- expected: a `.harness/browser_reviews/<request-id>.request.json` file exists and `validation.requested` is emitted
- after the external MCP run, run `py scripts/playwright_mcp_review.py record --session-id <session> --turn-id <turn> --request-id <request-id> --status passed --summary "..."`
- expected: `tool.completed` and `validation.completed` share one `tool_call_id`
- repeat with `--status failed`
- expected: `tool.failed` and `validation.completed(status=failed)` share one `tool_call_id`

## Codex Host-Tool Audit Check

- create a turn with `tool.called` but no matching `tool.completed` or `tool.failed`, then try to close the turn
- expected: `ExecutionFlowVerifier` reports `tool_call_without_terminal`
- create a `repo.changed` event without `tool_call_id`
- expected: `ExecutionFlowVerifier` reports `repo_changed_missing_tool_call_id`

## Operator CLI Check

- run `py scripts/check_flow.py --session-id <session> --turn-id <turn> --json`
- expected: exit code 0 for passed flows and 1 for failed flows
- run `py scripts/run_orchestrator.py --session-id <session> --turn-id <turn> --json`
- expected: queued work runs through `WorkOrchestrator` and emits `flow.checked`
- run `py scripts/check_repo_hygiene.py --json`
- expected: tracked runtime state, bytecode, and local environment files are rejected

## Codex Recorded-Call Wrapper Check

- run a successful `runtime.codex.recorded_call(...)`
- expected: the action receives authorization with `tool_call_id`
- expected: completion and changed-file events preserve that same `tool_call_id`
- open a `runtime.codex.tool_call(...)` context and exit without `complete(...)`
- expected: `tool.failed` is emitted so an incomplete host wrapper cannot silently look successful

## Codex Host Guard Check

- create a `CodexHostGuard` for one `session_id` and `turn_id`
- run a successful `guard.recorded_call(...)`
- expected: the same event sequence as `runtime.codex.recorded_call(...)`
- call `guard.require_final_audit(...)` before the turn completes
- expected: `HostAuditError` with `turn_not_completed`
- finish a turn through the orchestrator and call `guard.require_final_audit(compact=True)`
- expected: status is `passed` and a compact summary exists
