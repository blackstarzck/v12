---
name: requirement-gated-harness
description: Use when working on the requirement-gated Python harness, running its session flow, checking required-document acknowledgement, auditing tool or sandbox events, replaying sessions, or exporting repeated workflow skills.
---

# Requirement-Gated Harness

Use this skill when a task should be handled through the local requirement-gated
Python harness instead of ad hoc shell or file edits.

## Locate The Harness

In this repository, the harness runtime lives at the repository root.

On this machine, the current local project root is:

```text
C:\Users\admin\Desktop\workspace\topik-project\v12
```

If this plugin wrapper is moved, locate the harness by finding both:

- `generated_harness/runtime.py`
- `docs/harness/execution-flow.md`

Treat `docs/harness/execution-flow.md` as the source of truth for runtime,
tool, sandbox, orchestration, and validation behavior.

## Operating Rules

Think of the harness as a work ledger with a front gate:

- The durable ledger is `session_id`; it must survive agent, tool, or sandbox
  failures.
- The front gate is the required-document acknowledgement step; mutating tools
  and sandbox execution must wait until selected documents are acknowledged.
- Each worker attempt has its own `agent_run_id`.
- Each real tool action has its own `tool_call_id`.
- Each sandbox has its own `sandbox_ref`, and failed or disposed sandboxes must
  not be reused.
- Credentials stay outside sandbox resources and sandbox execution input.

Before changing runtime behavior, identify the event it produces or consumes in
`docs/harness/execution-flow.md`. If a new event is needed, update the document,
flow checker, and tests together.

## Common Commands

Run these commands from the repository root.

Run tests:

```powershell
$env:PYTHONPATH=(Get-Location).Path
py tests\test_harness_runtime.py
```

Run the required-document evaluator:

```powershell
py scripts\run_doc_eval.py --json
```

Check repository hygiene:

```powershell
py scripts\check_repo_hygiene.py --json
```

Check one session and turn:

```powershell
py scripts\check_flow.py --session-id <session_id> --turn-id <turn_id>
```

Check and record the flow result:

```powershell
py scripts\check_flow.py --session-id <session_id> --turn-id <turn_id> --emit
```

Run the pre-final audit:

```powershell
py scripts\pre_final_audit.py --session-id <session_id> --turn-id <turn_id> --compact --json
```

Export a repeated workflow suggestion as a reusable skill:

```powershell
py scripts\export_repeated_skill.py --repo-root . --json
```

## Validation Checklist

Before final output for harness work, confirm:

- `requirements.analyzed` appears before required documents, tools, or sandbox
  events.
- Required documents are acknowledged before mutating work.
- Every `tool.called` has a matching `tool.completed` or `tool.failed`.
- Every `repo.changed` event includes the responsible `tool_call_id`.
- Browser validation, when used, is recorded as `validator.browser` and
  `validation.completed`.
- The pre-final audit passes or reports exactly what still blocks completion.
