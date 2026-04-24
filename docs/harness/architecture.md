# requirement-gated-python-harness Architecture

## Goal

- Product or repository: requirement-gated-python-harness
- User outcome: ship a resumable coding harness with required-document gating
- Why a harness is needed: prompt text alone is too weak to enforce repeatable behavior

## Boundary Map

### Session

- Responsibility: append-only event log, replay cursor, turn state
- Durable store: choose per target stack
- Event types: turn, docs, requirements, agent run, tool call, sandbox, validation, reminders
- Resume key: `session_id`
- Isolation rule: the main session is not an agent process; failed agents are recorded as events and can be retried
- Replay and compaction: `generated_harness/session_replay.py` reconstructs a turn from raw events and writes derived compact context without replacing the raw log

### Harness Runtime

- Responsibility: shape context, analyze user requirements, select docs, route agent turns
- Main turn loop: turn.started -> requirements.analyzed -> planner -> docs.required -> docs.acknowledged -> implementer -> reviewer -> quality.review_completed
- Context shaping: summarize from session log, not from hidden process memory
- Failure recovery: replay from `session_id`

### Agent Run Boundary

- Responsibility: track one execution of one role
- Identifier: `agent_run_id`
- Event flow: `agent.started` -> `agent.assigned` -> `agent.heartbeat` -> `agent.completed`, `agent.failed`, or `agent.timed_out`
- Liveness model: `record_agent_heartbeat(...)` refreshes one run, `find_timed_out_agent_runs(...)` detects stale runs, and `mark_timed_out_agent_runs(...)` closes them as timed out
- Recovery behavior: retry creates a new `agent_run_id`; prior failed or timed-out runs remain in the session log for audit

### Agent Skills

- Responsibility: give every generated agent explicit role skills instead of relying on role names alone
- Config: `config/agent_skills.json`
- Runtime behavior: each `agent.assigned` event includes the skills for that role
- Agent packet field: `assigned_skills`

### Browser Review

- Responsibility: reviewer-owned physical browser verification for UI-impacting changes
- Adapter: `generated_harness/browser_review.py`
- External tool: Playwright MCP, supplied by the host through a browser review handler and audited as `validator.browser`
- External bridge: `generated_harness/playwright_mcp_adapter.py` writes `validation.requested` request files and records MCP results back through `validator.browser`
- Event output: `validation.completed` with `validator=playwright-mcp`; real handler runs also include `tool_call_id`
- Non-UI work: record `skipped` with `applicability=not_applicable`
- UI work without handler: record `unavailable` so quality review can route a manual or follow-up check
- Handler failure: record `tool.failed` and `validation.completed(status=failed)` without failing the reviewer agent or deleting the main session

### Requirement Analysis

- Responsibility: force analysis of user input before execution
- Output event: `requirements.analyzed`
- Captures: inferred intents, target paths, required documents, registry suggestions, reviewer questions, and open risks
- Hard rule: mutating and unknown tools are blocked if this event is missing for the current turn

### Tool Gateway

- Responsibility: tool routing, audit, policy checks
- Named tools: repo.read, repo.write, filesystem.write, shell.run, sandbox.execute, validator.run
- Policy checks: completed requirement analysis, required-doc acknowledgement, document digest freshness, write approval, audit logging
- Default behavior: allow known read-only tools; gate known mutating tools and unknown tools
- Identifier: `tool_call_id`
- Audit events: `tool.called`, `tool.blocked`, `tool.completed`, `tool.failed`, `repo.changed`
- Linkage: tool events can include `agent_run_id` and `sandbox_ref` so failures are attributed to the correct worker
- Redaction: sensitive-looking keys such as token, secret, password, credential, auth, api_key, access_key, and private_key are redacted before payloads or results are written to the durable event log

### Codex Tool Adapter

- Responsibility: bridge real Codex tool calls into the harness gateway
- Preferred host contract: call `runtime.codex.recorded_call(...)` around one real Codex-facing action so `tool.called`, `tool.completed`, and `tool.failed` stay paired by `tool_call_id`
- Manual host contract: use `runtime.codex.tool_call(...)` when the host must run the real tool outside the callable shape
- Tool aliases: `apply_patch` maps to `git.apply_patch`; `shell_command` maps to `shell.run`
- Boundary: the adapter records and gates Codex actions with `tool_call_id`, but it does not directly execute Codex desktop tools from Python
- Host-side audit: `scripts/pre_final_audit.py` lets a Codex host check flow status, turn completion, open tool calls, quality review, and optional compaction before final output

### Codex Host Guard

- Responsibility: give host integrations one small object that binds `session_id` and `turn_id`
- Module: `generated_harness/host_integration.py`
- Preferred tool path: `CodexHostGuard.recorded_call(...)` delegates to `runtime.codex.recorded_call(...)`
- Manual tool path: `CodexHostGuard.tool_call(...)` delegates to the context-manager wrapper
- Final-answer gate: `CodexHostGuard.require_final_audit(...)` raises `HostAuditError` unless pre-final audit passes
- Examples: `CODEX_HOST_TOOL_EXAMPLES` documents `apply_patch`, `functions.shell_command`, and browser validation wrapping

### Requirement Memory

- Responsibility: persist user intent, inferred labels, matched docs, open risks, registry suggestions, workflow signatures, and repeated-workflow skill suggestions across turns
- Stored in: `.harness/requirement_memory.json`
- Used by: document matcher, acknowledgement history, and reviewer

### Repeated Workflow Skill Export

- Responsibility: convert repeated work patterns into reusable skills
- Detection signal: same workflow signature across multiple turns
- Default threshold: 2 matching turns
- Export path: `.codex/skills/<skill-id>/SKILL.md`
- README path: `.codex/skills/<skill-id>/README.md`
- Script: `scripts/export_repeated_skill.py`

### Quality Review

- Responsibility: review finished work before final output, using changed files, validator results, missing-scope reminders, and reviewer questions
- Browser role split: reviewer performs Playwright MCP checks, quality review only aggregates the recorded result
- Post-run behavior: remind and route instead of only blocking
- Fallback actions: complete, complete_with_reminders, recommend_immediate_fix, recommend_specialist_fixer
- Events: `validation.completed`, `reviewer.questions_ready`, `quality.review_completed`, `turn.needs_attention`

### Acknowledgement Templates

- Responsibility: capture extracted constraints per required document before execution
- Stored in: `.harness/acks/<session>-<turn>.json`
- Generated by: `scripts/ack_required_docs.py --template`
- Freshness rule: if a required document changes after acknowledgement, the next mutating tool call is blocked until the document is acknowledged again

### Sandbox Adapter

- Responsibility: isolated execution and file mutation
- Identifier: `sandbox_ref`
- Provisioning model: `sandbox.provisioned` records resources and keeps credentials outside the sandbox by default
- Execution model: `SandboxAdapter.execute(...)` routes through `ToolGateway` as `sandbox.execute`
- Teardown model: `sandbox.disposed`; a failed sandbox records `sandbox.failed` and can be replaced without losing session state
- Policy block model: `sandbox.blocked` records unknown, disposed, failed, or credential-bearing sandbox attempts without treating the main session as failed
- Lifecycle rule: only known active sandboxes can execute; disposed or failed `sandbox_ref` values must be replaced
- Credential rule: resource and input keys that look like tokens, secrets, passwords, credentials, auth keys, API keys, access keys, or private keys are blocked before execution
- Local backend: `generated_harness/local_sandbox_backend.py` provides a first operational backend by creating `.harness/sandboxes/<sandbox_ref>`, copying requested paths, running a command with a scrubbed environment, and removing the workspace on dispose
- Boundary note: the local-process backend is useful for smoke tests and local development. Stronger isolation such as Docker or Vercel Sandbox should stay optional adapter work, not core harness work.
- Optional backend recipes: `docs/harness/optional-sandbox-backends.md` documents Docker and Vercel Sandbox as replaceable adapters behind the same `SandboxBackend` protocol.

### Orchestrator

- Responsibility: retries, wakeups, optional fan-out
- Module: `generated_harness/orchestrator.py`
- Queue model: `work.queued` -> `work.started` -> `work.completed` or `work.failed`
- Retry policy: bounded by `max_attempts`; failures can emit `work.retry_scheduled`
- Lease model: `work.lease_acquired` prevents another worker from picking the same item until the lease expires; lease acquisition is checked and appended under the session-store lock
- Cancellation model: `work.cancelled` removes a queued item from pending work
- Backoff model: retries include `retry_delay_seconds` and `available_at`
- Flow guard: successful orchestrated work emits `flow.checked` from `generated_harness/flow_contract.py`
- Cancellation or wake: explicit work item state
- Hosted operation note: `docs/harness/hosted-operations.md` defines the external store and scheduler contract needed before using this across multiple machines.

### Execution Flow Contract

- Source of truth: `docs/harness/execution-flow.md`
- Runtime checker: `ExecutionFlowVerifier.verify_turn(...)`
- Orchestrator behavior: `WorkOrchestrator.run_next(...)` emits `flow.checked` after `continue_turn`
- Development rule: new events must update the execution-flow document, verifier, and tests together

### Credential Boundary

- Secret source: external vault, proxy, or scoped environment outside sandbox
- Access pattern: fetched by runtime or proxied service
- What never enters the sandbox: raw long-lived credentials

## First Implementation Slice

- Smallest working path: planner + implementer + reviewer with required-doc gating
- Includes: forced requirement analysis, four-condition document matching, requirement memory, agent run IDs, agent heartbeat and timeout events, tool call IDs, active-only sandbox lifecycle enforcement, credential-bearing sandbox payload blocks, changed-file audit, Codex recorded-call wrapping, audited browser validation, Playwright MCP request/result bridge, orchestrator queue events, flow contract checks, post-run reminders, and quality fallback routing
- Added operational slice: local-process sandbox backend, session replay and compaction, expanded required-document eval CLI fixtures, idempotent repeated-skill export validation, orchestrator lease/cancel/backoff, tool-log redaction, host-side pre-final audit, Codex host guard, optional sandbox backend recipes, hosted-operation notes, and GitHub Actions CI
- Deferred components: actual distributed scheduler implementation and remote repository publishing
- Main risks: stale document registry, weak validation coverage, Codex host calls that are not wrapped by `runtime.codex`

## Validation

- Deterministic evaluator: run one stable task against required docs and validators
- Replay or resume check: crash between docs.required and docs.acknowledged
- Idempotent resume check: calling `continue_turn` after completion must not rerun completed steps
- Agent failure check: failed implementer records `agent.failed` and can retry with a new `agent_run_id`
- Agent timeout check: stale heartbeat records `agent.timed_out` and retry uses a new `agent_run_id`
- Tool and sandbox boundary check: `tool_call_id` links call, completion or failure, and changed-file audit; sandbox lifecycle events must reference an earlier `sandbox.provisioned`
- Codex host-tool audit check: a turn cannot close with open `tool.called` events, and every `repo.changed` must carry the responsible `tool_call_id`
- Browser validation check: real Playwright handler runs emit `tool.called`, `tool.completed` or `tool.failed`, and `validation.completed` with the same `tool_call_id`
- Playwright MCP bridge check: `validation.requested` writes a request file, and the later recorded MCP result emits `tool.completed` or `tool.failed` plus `validation.completed`
- Flow contract check: orchestrated runs emit `flow.checked=passed`; malformed event streams fail the verifier
- Credential safety check: verify secrets never enter sandbox env by default
