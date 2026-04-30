# Harness Execution Flow

This document is the working contract for the harness. New runtime,
orchestration, tool, sandbox, or validation work should preserve this flow.
When the implementation changes, update this document and the flow checks
together.

## Practical Summary

The main `session_id` is the durable ledger. A `turn_id` is one user request
inside that ledger. Agent runs, tool calls, and sandboxes are replaceable
workers attached to the ledger.

If an agent, tool, or sandbox fails, the session should not be treated as lost.
The failure is recorded as an event, and the orchestrator can retry the pending
work with a new `agent_run_id`, `tool_call_id`, or `sandbox_ref`.

## Execution Contract

1. Start or resume the durable `session_id`.
2. Emit `turn.started` for one user request.
3. Emit `requirements.analyzed` before planning, writing, shell, sandbox, or
   unknown tool execution.
4. Emit `clarification.required` when a theme-scoped request needs explicit
   scope confirmation before planning or broad reading.
5. Emit `clarification.resolved` before `docs.required` on clarification-gated
   turns.
6. Emit `docs.required` with the policy-selected documents.
7. Block mutating tools and sandbox work until `docs.acknowledged` exists for
   the current turn.
8. For UI implementation turns, emit `antd.api_mapping.completed` before any
   implementation tool call. The mapping records visible data, states, actions,
   layout roles, selected AntD components, API/prop mappings, sources, and
   custom implementation justifications.
9. Start role work with `agent.started`, `agent.assigned`, and
   `agent.heartbeat`.
10. Complete, fail, or time out each role with one of `agent.completed`,
    `agent.failed`, or `agent.timed_out`.
11. Wrap Codex-facing host tools with `runtime.codex.recorded_call(...)` or
    `runtime.codex.tool_call(...)`.
12. Record every tool as `tool.called`, then `tool.completed` or `tool.failed`
    with the same `tool_call_id`.
    A turn must not close while a `tool.called` event is still missing its
    terminal event.
13. Denied tools record `tool.blocked` and do not emit `tool.called`.
14. Record sandbox work through `sandbox.provisioned`, `sandbox.executed`,
    `sandbox.failed`, `sandbox.disposed`, and `sandbox.blocked` using
    `sandbox_ref`.
15. Do not provision or execute a sandbox before required-document
    acknowledgement when required documents exist.
16. Do not provision or execute a sandbox before `clarification.resolved` on
    clarification-gated turns.
17. Do not pass credentials, tokens, passwords, or secret-looking payload keys
    into sandbox resources or sandbox execution input.
18. Record changed files as `repo.changed` with the responsible
    `tool_call_id`. A changed-file event without `tool_call_id` is treated as
    an unwrapped host-tool change.
19. Record reviewer validation as `validation.completed`. When validation calls
    an external browser tool, route it through `validator.browser` so
    `tool.called`, `tool.completed`, or `tool.failed` share the same
    `tool_call_id`.
    If the Playwright MCP run happens outside the Python runtime, emit
    `validation.requested` first and later record the MCP result through the
    `validator.browser` bridge.
20. Record quality review as `quality.review_completed`.
21. Route immediate repair through `fixer` when quality review requests it.
22. Finish the turn with `turn.completed`, or leave it open for retry or
    operator attention.
23. Orchestrated work should claim a queued item with `work.lease_acquired`
    before emitting `work.started`.
24. Run `flow.checked` after orchestrated execution to confirm the event stream
    still follows this contract.

## Main Flow

```mermaid
flowchart TD
    A["User request"] --> B["session.started or existing session_id"]
    B --> C["turn.started with turn_id"]
    C --> D["requirements.analyzed"]
    D --> DC{"Theme scope needs confirmation?"}
    DC -- "Yes" --> DR["clarification.required"]
    DR --> DS["clarification.resolved"]
    DC -- "No" --> E["docs.required"]
    DS --> E
    E --> F{"docs.acknowledged?"}
    F -- "No" --> G["Mutating tools and sandbox are blocked"]
    F -- "Yes" --> AM{"UI implementation turn?"}
    AM -- "Yes" --> AC["antd.api_mapping.completed"]
    AM -- "No" --> WQ["work.queued"]
    AC --> WQ
    WQ --> WL["work.lease_acquired"]
    WL --> WS["work.started"]
    WS --> H["agent.started"]
    H --> I["agent.assigned with role skills"]
    I --> J["agent.heartbeat"]
    J --> K{"Heartbeat stale?"}
    K -- "Yes" --> L["agent.timed_out"]
    L --> M["Orchestrator retries with new agent_run_id"]
    M --> H
    K -- "No" --> N{"Agent work succeeds?"}
    N -- "No" --> O["agent.failed"]
    O --> M
    N -- "Yes" --> P["agent.completed"]
    P --> Q["runtime.codex.recorded_call or tool_call context"]
    Q --> R["tool.called with tool_call_id"]
    R --> S{"Tool or sandbox succeeds?"}
    S -- "No" --> T["tool.failed or sandbox.failed"]
    T --> U["Orchestrator records retry or operator attention"]
    S -- "Yes" --> V["tool.completed"]
    V --> W["repo.changed when files changed"]
    W --> VX{"Browser validation needed?"}
    VX -- "Yes, external MCP" --> VR["validation.requested"]
    VR --> VB["tool.called: validator.browser"]
    VX -- "Yes, in-process handler" --> VB
    VB --> VC["tool.completed or tool.failed"]
    VC --> X["validation.completed"]
    VX -- "No" --> X
    X --> Y["quality.review_completed"]
    Y --> Z{"Fixer needed?"}
    Z -- "Yes" --> AA["agent.started: fixer"]
    AA --> I
    Z -- "No" --> AB["turn.completed"]
    AB --> AE["flow.checked"]
```

## Sequence Flow

```mermaid
sequenceDiagram
    participant User
    participant Orchestrator
    participant Runtime
    participant SessionStore
    participant Agent
    participant ToolGateway
    participant Sandbox
    participant Quality

    User->>Runtime: start_turn(user_input, target_paths)
    Runtime->>SessionStore: session.started
    Runtime->>SessionStore: turn.started
    Runtime->>SessionStore: requirements.analyzed
    alt Theme clarification required
        Runtime->>SessionStore: clarification.required
        Runtime-->>User: clarification questions + fast-start paths
        User->>Runtime: resolve_clarification(response)
        Runtime->>SessionStore: clarification.resolved
    end
    Runtime->>SessionStore: docs.required
    Runtime-->>User: acknowledgement template
    User->>Runtime: acknowledge_required_docs
    Runtime->>SessionStore: docs.acknowledged
    opt UI implementation turn
        User->>Runtime: record_antd_api_mapping
        Runtime->>SessionStore: antd.api_mapping.completed
    end
    Orchestrator->>SessionStore: work.queued
    Orchestrator->>SessionStore: work.lease_acquired
    Orchestrator->>SessionStore: work.started
    Orchestrator->>Runtime: continue_turn(session_id, turn_id)
    Runtime->>SessionStore: agent.started
    Runtime->>SessionStore: agent.assigned
    Runtime->>SessionStore: agent.heartbeat
    Runtime->>Agent: run role packet
    alt Agent completes
        Agent-->>Runtime: AgentResult
        Runtime->>SessionStore: agent.completed
    else Agent fails
        Runtime->>SessionStore: agent.failed
        Orchestrator->>Runtime: retry with new agent_run_id
    else Agent stalls
        Orchestrator->>Runtime: mark_timed_out_agent_runs
        Runtime->>SessionStore: agent.timed_out
        Orchestrator->>Runtime: retry with new agent_run_id
    end
    Runtime->>ToolGateway: execute or Codex recorded_call
    alt Tool denied
        ToolGateway->>SessionStore: tool.blocked
    else Tool allowed and succeeds
        ToolGateway->>SessionStore: tool.called
        ToolGateway->>SessionStore: tool.completed
        ToolGateway->>SessionStore: repo.changed
    else Tool allowed and fails
        ToolGateway->>SessionStore: tool.called
        ToolGateway->>SessionStore: tool.failed
    end
    Runtime->>Sandbox: optional sandbox execution
    alt Sandbox active and credential-clean
        Sandbox->>SessionStore: sandbox.provisioned / sandbox.executed / sandbox.failed / sandbox.disposed
    else Unknown, disposed, failed, or secret-bearing sandbox payload
        Sandbox->>SessionStore: sandbox.blocked
    end
    alt Browser validation required
        Runtime->>SessionStore: validation.requested
        Runtime->>ToolGateway: validator.browser
        ToolGateway->>SessionStore: tool.called
        ToolGateway->>SessionStore: tool.completed or tool.failed
    end
    Runtime->>SessionStore: validation.completed
    Runtime->>Quality: review_turn
    Quality->>SessionStore: quality.review_completed
    Runtime->>SessionStore: turn.completed
    Orchestrator->>SessionStore: flow.checked
```

## Flow Check Rules

The harness should continuously check these rules while new features are
developed:

- `requirements.analyzed` must exist before `docs.required`.
- `clarification.required` must appear after `requirements.analyzed`.
- `clarification.resolved` must not exist without an earlier `clarification.required`.
- On clarification-gated turns, `docs.required` must appear after `clarification.resolved`.
- Gated `tool.called` events must have both `requirements.analyzed` and
  `docs.acknowledged` earlier in the same turn.
- On clarification-gated turns, gated `tool.called` events must also have an
  earlier `clarification.resolved`.
- UI implementation tool calls must have an earlier
  `antd.api_mapping.completed` event.
- `antd.api_mapping.completed` must appear after `docs.acknowledged` when the
  turn has required documents.
- Every `agent.completed`, `agent.failed`, or `agent.timed_out` must match an
  earlier `agent.started`.
- Every `tool.completed` or `tool.failed` must match an earlier `tool.called`
  by `tool_call_id`.
- Every `tool.called` before `turn.completed` must have `tool.completed` or
  `tool.failed` before `turn.completed`.
- Every `repo.changed` with a `tool_call_id` must match an earlier
  `tool.called`.
- Every `repo.changed` must include the responsible `tool_call_id`.
- Every `validation.completed` with a `tool_call_id` must match an earlier
  `tool.called`.
- Every `sandbox.executed`, `sandbox.failed`, or `sandbox.disposed` must match
  an earlier `sandbox.provisioned` by `sandbox_ref`.
- `sandbox.executed` must not appear after the same `sandbox_ref` was already
  `sandbox.disposed` or `sandbox.failed`.
- `sandbox.provisioned` must appear after `requirements.analyzed`, and after
  `docs.acknowledged` when the turn has required documents.
- On clarification-gated turns, `sandbox.provisioned` must also appear after
  `clarification.resolved`.
- `turn.completed` must not appear before `quality.review_completed`.
- Every `work.lease_acquired` must match an earlier `work.queued` by
  `work_item_id`.
- Every `work.started` must match both an earlier `work.queued` and an earlier
  `work.lease_acquired` by `work_item_id`.
- Every `work.retry_scheduled` must reference an earlier queued item through
  `retry_of`.
- Orchestrated runs should emit `flow.checked` after execution.

## Development Rule

Before adding new runtime behavior, identify which event in this document it
produces or consumes. If the behavior needs a new event, add it here, update
the flow checker, and add a test that proves the event stream still follows
the contract.
