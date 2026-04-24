# Harness Roadmap

This document records the remaining work for turning the current
requirement-gated Python harness into a stronger Codex runtime harness.

## Practical Conclusion

The harness already has the core safety shape: a durable main session, separate
agent runs, gated tool calls, sandbox lifecycle events, browser validation
events, and an execution-flow checker.

The main remaining work is to replace the current simulated or host-supplied
boundaries with real operational backends. In plain language: the ledger exists,
the gate exists, and the worker tracking exists; the next job is connecting
those pieces to real isolated execution, stronger replay, and CI.

## What Works Now

- Durable session log: `session_id` keeps the main work history even when an
  agent, tool, or sandbox fails.
- Requirement gate: each turn records `requirements.analyzed` before planning,
  tool use, sandbox work, or unknown execution.
- Required-document gate: mutating tools and sandbox execution are blocked until
  selected documents are acknowledged.
- Agent-run isolation: each role execution gets an `agent_run_id`, heartbeat,
  completion, failure, or timeout event.
- Tool-call audit: each mutating or external action gets a `tool_call_id` and a
  terminal `tool.completed` or `tool.failed` event.
- Codex bridge: `runtime.codex.recorded_call(...)` records real Codex-facing
  host actions through the harness event model.
- Codex host guard: `CodexHostGuard` binds one session and turn, wraps host
  tool calls, and raises `HostAuditError` when pre-final audit fails.
- Sandbox boundary: `SandboxAdapter` records provisioning, execution, failure,
  disposal, blocked stale sandboxes, and credential-looking payload blocks.
- Local sandbox backend: `LocalProcessSandboxBackend` can run real commands in
  a dedicated local workspace with a scrubbed environment.
- Browser verification boundary: reviewer browser validation is recorded as
  `validation.completed`, and the external Playwright MCP bridge can emit
  `validation.requested` before results are recorded.
- Orchestrator loop: queued work emits `work.queued`, `work.started`,
  `work.completed` or `work.failed`, and then `flow.checked`; cancellation,
  leases, and retry backoff are now event-backed.
- Session replay and compaction: one turn can be reconstructed from raw events
  and compacted into a derived summary file without replacing the raw log.
- Required-document eval: `scripts/run_doc_eval.py` measures expected versus
  actual required document matches.
- Repeated skill export: duplicate CLI exports are idempotent and generated
  skills are validated for basic reusable structure.
- Tool-log redaction: secret-looking tool payload and result keys are redacted
  before durable logging.
- Tool denylist: `credential.dump` emits `tool.blocked` and raises
  `ToolPolicyError` before handler execution.
- Host pre-final audit: `scripts/pre_final_audit.py` checks flow status, turn
  completion, open tools, quality review, and optional compaction before final
  output.
- Flow checker: `scripts/check_flow.py` detects missing requirement analysis,
  open tool calls, invalid sandbox lifecycle, unwrapped file changes, and
  missing quality-review ordering.

## What Does Not Work Yet

The harness is not yet a complete production runtime. The following pieces are
still scaffolding or local contracts:

- Strong sandbox isolation: the local-process backend is operational but is not
  a security-grade VM. Docker, Vercel Sandbox, or another stronger backend
  should remain optional adapter work for projects that truly execute untrusted
  code.
- Host enforcement: Codex tool wrapping is available, but the Python harness
  cannot force every desktop-host tool call to use it unless the host
  integration adopts the wrapper or `CodexHostGuard`.
- Host integration automation: the pre-final audit CLI and `CodexHostGuard`
  exist, but the Codex host still needs to call the guard automatically as part
  of its final-answer path.
- Distributed orchestration: local work claims are now guarded by the session
  lock, and hosted-operation requirements are documented. Actual cross-machine
  coordination remains future work.
- Release path: CI is configured locally, but there is still no repository
  remote.

## Recommended Build Order

### 1. Add One Real Sandbox Backend

Status: first slice complete with `LocalProcessSandboxBackend`.

Start here because it is the biggest safety boundary. A real sandbox is the
separate room where risky commands run. If that room crashes, the main session
ledger should still survive.

Acceptance criteria:

- A backend interface sits behind `SandboxAdapter` without changing the public
  event contract.
- Provision, execute, fail, and dispose still emit `sandbox.provisioned`,
  `sandbox.executed`, `sandbox.failed`, and `sandbox.disposed`.
- Secret-looking resource or input keys remain blocked before the backend is
  called.
- A backend crash records `sandbox.failed` and does not delete the main
  `session_id`.
- Tests cover success, timeout, crash, stale sandbox reuse, and credential
  blocking.

### 2. Formalize Session Replay And Compaction

Status: first slice complete with `SessionReplayer`, `replay_turn`, and
`compact_turn`.

The session log is the durable ledger. Replay and compaction decide how much of
that ledger is shown to the next agent without losing the original record.

Acceptance criteria:

- A replay API can reconstruct a turn state from `session_id` and `turn_id`.
- A compaction step writes a summarized context packet while raw events remain
  available.
- A resumed turn can continue after `docs.required`, after a failed agent, and
  after a failed tool call.
- Tests cover long sessions and prove completed turns are not rerun.

### 3. Build A Required-Document Eval Set

Status: first slice complete with `scripts/run_doc_eval.py` and
`config/required_doc_eval.json`.

The document gate is only useful if it chooses the right documents. Treat this
like checking whether the harness picked the right manual before doing work.

Acceptance criteria:

- Add fixture tasks with expected required documents.
- Measure missed required documents and unnecessary document matches.
- Record open risks and reviewer questions in the eval output.
- Keep the eval deterministic so it can run in CI.

### 4. Harden Repeated-Workflow Skill Export

Status: first slice complete with idempotent CLI export and generated skill
validation.

The harness already suggests reusable skills when the same workflow repeats.
The next step is making those exports clean enough for real reuse.

Acceptance criteria:

- Duplicate suggestions are merged instead of creating noisy skill folders.
- Exported `SKILL.md` files explain when to use the skill, required inputs, and
  validation steps.
- Exported `README.md` files describe the workflow in non-developer language.
- Tests verify that one repeated workflow exports one reusable skill.

### 5. Expand The Orchestrator For Real Operations

Status: first slice complete with cancellation, leases, and retry backoff.

The current orchestrator proves the queue and retry model. Production use needs
stronger controls for multiple workers and interrupted runs.

Acceptance criteria:

- Work items support cancellation and operator attention states.
- Retry scheduling uses bounded backoff.
- A worker lease or lock prevents two workers from running the same item.
- Multiple pending turns can be resumed without corrupting one another.

### 6. Strengthen Codex Host Integration

Status: first slice complete with `scripts/pre_final_audit.py`,
`CodexHostGuard`, and host-tool examples; full Codex host adoption remains.

The harness has a wrapper for Codex-facing tools, but the host needs a strict
habit: every mutating action should enter through the wrapper.

Acceptance criteria:

- Add host-integration examples for `apply_patch`, shell execution, and browser
  validation.
- Add a pre-final audit command that fails when a turn contains unwrapped
  `repo.changed` events or open `tool.called` events.
- Document which host tools are read-only, mutating, or unknown.

### 7. Add CI And Release Packaging

Status: CI file added with tests, required-document eval, and repository
hygiene checks; remote publishing still needs a remote repository.

Once a remote Git repository exists, add a small CI path. CI is the automatic
checklist that runs before changes are trusted.

Acceptance criteria:

- CI runs `py tests\test_harness_runtime.py`.
- CI runs at least one `scripts/check_flow.py` smoke check.
- CI rejects committed `.harness` runtime state, Python bytecode, and local
  environment files.
- The package layout is documented for future harness variants inside the
  wider harness library.

### 8. Security Hardening

Status: first slice complete with sandbox credential blocks, tool-log
redaction, and a denied-tool path for `credential.dump`.

The harness blocks obvious credential keys today. Production use should also
control where secrets come from and how external tools are allowed.

Acceptance criteria:

- Add a vault or proxy pattern for credentials that never enter sandbox input.
- Add denylist and allowlist tests for external tool names.
- Add log redaction checks for secret-looking payloads.
- Document the difference between runtime credentials and sandbox-visible data.

## Work To Defer

- Multi-agent fan-out beyond the current role sequence.
- Distributed control plane or hosted scheduler implementation.
- Multiple sandbox backends enabled at the same time.
- Public release packaging and remote publishing.

These are useful later, but they should not come before one real sandbox
backend, replay policy, and CI.

## Immediate Next Steps

1. Keep Docker or Vercel Sandbox as optional backend recipes, not core harness
   requirements. Status: documented in `docs/harness/optional-sandbox-backends.md`.
2. Wire the Codex host to call `scripts/pre_final_audit.py` automatically
   before final output. Status: host-facing guard exists; desktop-host adoption
   is the remaining external integration.
3. Add hosted scheduling only if multiple machines need to resume the same
   harness library. Status: documented in `docs/harness/hosted-operations.md`.

## Git Handoff

This folder did not start as a Git repository. The local repository can record
the current harness state, but pushing to a remote requires a remote URL or an
explicit instruction to create a new GitHub repository.

When a remote exists, use this shape:

```powershell
git remote add origin <remote-url>
git push -u origin main
```
