# requirement-gated-python-harness Session Model

## Session Purpose

- What the session represents: durable history of one harnessed task stream
- What it does not represent: sandbox filesystem or prompt context alone

## Event Stream

| Event | Producer | Stored Fields | Notes |
| --- | --- | --- | --- |
| session.started | runtime | session_id, metadata | first durable event |
| turn.started | runtime | turn_id, user_input, target_paths | begins a new turn |
| requirements.analyzed | requirement analyzer | turn_id, intents, required_docs, risks, suggestions | hard pre-execution analysis receipt |
| requirements.analysis_blocked | requirement analyzer | turn_id, reason | emitted when a request cannot be analyzed |
| docs.required | pre-turn selector | turn_id, doc_ids, digests | hard gate input |
| docs.acknowledged | runtime or agent bridge | turn_id, doc_ids, digests, constraints | required before execution |
| requirements.updated | runtime | turn_id, intents, matched_docs, suggestions | persistent requirement analysis |
| agent.started | runtime | turn_id, agent_run_id, role, status | begins one replaceable role execution |
| agent.assigned | runtime | turn_id, agent_run_id, role, skills | explicit handoff with role skills |
| agent.heartbeat | runtime or host bridge | turn_id, agent_run_id, role, status, metadata | durable still-alive signal for long-running work |
| agent.completed | runtime | turn_id, agent_run_id, role, status, output | successful role execution |
| agent.failed | runtime | turn_id, agent_run_id, role, error | failed role execution; main session remains resumable |
| agent.timed_out | runtime or orchestrator | turn_id, agent_run_id, role, last_seen_at, timeout_seconds | stale role execution; retry can start a new agent_run_id |
| tool.called | tool gateway | turn_id, agent_run_id, tool_call_id, tool_name, input | audited |
| tool.blocked | tool gateway | turn_id, reason | used for missing docs or policy failures |
| tool.completed | tool gateway | turn_id, agent_run_id, tool_call_id, tool_name, result | successful tool call |
| tool.failed | tool gateway | turn_id, agent_run_id, tool_call_id, tool_name, error | failed tool call |
| repo.changed | tool gateway | turn_id, agent_run_id, tool_call_id, tool_name, changed_paths | changed-file audit trail |
| sandbox.provisioned | sandbox adapter | turn_id, agent_run_id, sandbox_ref, resources | replaceable isolated environment allocated |
| sandbox.executed | sandbox adapter | turn_id, agent_run_id, sandbox_ref, tool_call_id, status | isolated work |
| sandbox.failed | sandbox adapter | turn_id, agent_run_id, sandbox_ref, tool_call_id, error | sandbox failure isolated from main session |
| sandbox.disposed | sandbox adapter | turn_id, agent_run_id, sandbox_ref, status | sandbox released |
| sandbox.blocked | sandbox adapter | turn_id, agent_run_id, sandbox_ref, tool_call_id, reason, details | lifecycle or credential-boundary block |
| validation.requested | Playwright MCP bridge | turn_id, agent_run_id, request_id, validator, request_path, app_url, target_paths | external browser-review request written for MCP runner |
| validation.completed | reviewer or validator | turn_id, agent_run_id, validator, status, findings, artifacts, tool_call_id | deterministic check point, including Playwright MCP browser review |
| reviewer.questions_ready | reviewer | turn_id, agent_run_id, questions | post-run reminder hook |
| quality.review_completed | quality reviewer | turn_id, status, findings, reminders, fallback_action | post-run diagnostic and fallback routing |
| session.compacted | session replayer | turn_id, cursor, compact_path, summary, next_recommended_action | derived compact context; raw events remain authoritative |
| work.queued | orchestrator | turn_id, work_item_id, kind, attempt, max_attempts | durable queue item |
| work.lease_acquired | orchestrator | turn_id, work_item_id, worker_id, lease_expires_at | temporary worker claim that prevents duplicate execution |
| work.started | orchestrator | turn_id, work_item_id, kind, status | queue item is running |
| work.completed | orchestrator | turn_id, work_item_id, flow_check, timed_out_agent_runs | queue item finished |
| work.failed | orchestrator | turn_id, work_item_id, error, timed_out_agent_runs | queue item failed but session remains resumable |
| work.retry_scheduled | orchestrator | turn_id, work_item_id, retry_of, attempt | retry queued after work failure |
| work.cancelled | orchestrator | work_item_id, status, reason | queued work was intentionally removed from pending execution |
| flow.checked | flow verifier | turn_id, status, findings | event stream was checked against execution-flow.md |
| turn.needs_attention | runtime | turn_id, fallback_action, findings | emitted when immediate fix or specialist review is recommended |
| turn.completed | runtime | turn_id, summary | successful close |
| turn.failed | runtime | turn_id, reason | resumable failure |

## Cursor and Replay

- Session identifier: `session_id`
- Cursor model: monotonically increasing event offset
- Replay path: rebuild turn state from ordered events
- Resume path: restart runtime from `session_id` and last durable offset
- Compaction path: `compact_turn` writes `.harness/compact/<session>-<turn>.json` and emits `session.compacted`; this is a derived summary for prompt shaping, not the source of truth
- File safety: session IDs are restricted to safe path characters, and event appends use a process-level session lock
- Idempotence rule: a completed turn returns the existing `turn.completed` event instead of rerunning implementer, tool, reviewer, or quality steps
- Agent isolation rule: failed role execution is recorded as `agent.failed` by `agent_run_id`; the main `session_id` is not treated as failed
- Agent liveness rule: running agents should emit `agent.heartbeat`; stale runs are closed by `agent.timed_out` and retried with a new `agent_run_id`
- Tool isolation rule: failed tools are recorded by `tool_call_id`; callers can retry with a new tool call without rewriting prior events; a turn cannot close with an unterminated `tool.called`
- Validation isolation rule: browser handler failures are recorded as `tool.failed` plus `validation.completed(status=failed)`; external MCP runs can be represented by `validation.requested` and later closed by `validation.completed`; the reviewer agent and main session remain recoverable
- Sandbox isolation rule: a dead sandbox is replaced by provisioning a new `sandbox_ref`; unknown, disposed, failed, or credential-bearing sandbox work emits `sandbox.blocked`; session recovery comes from events, not sandbox files
- Orchestration rule: queued work is represented by `work_item_id`, and successful orchestrated work should emit `flow.checked`
- Lease rule: pending work with an active `work.lease_acquired` or `work.started` lease is hidden from other workers until `lease_expires_at`; acquisition uses `emit_event_if` so the claim check and lease append happen under the same session lock
- Retry rule: failed work can be re-queued with `available_at`; pending work ignores retry items until their delay has passed

## Retention and Compaction

- Retention rule: keep raw events and compact views separately
- Compaction rule: summaries are derived, not authoritative
- Prompt shaping rule: build prompts from session state and selected docs

## Failure Cases

- Harness crash: recover from event log
- Agent crash: emit `agent.failed`, keep the turn open, and retry with a new `agent_run_id`
- Silent agent stall: emit `agent.timed_out` after the heartbeat window expires, then retry with a new `agent_run_id`
- Sandbox crash: emit `sandbox.failed`, replace sandbox, and replay pending turn state
- Sandbox policy block: emit `sandbox.blocked`, keep the main session alive, and provision a clean replacement sandbox when needed
- Tool timeout: emit `tool.failed` with `tool_call_id` and retry by policy
- Work failure: emit `work.failed` and optionally `work.retry_scheduled`
- Partial completion: require reviewer or operator decision before close
