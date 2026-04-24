# Harness Quickstart

This file explains the practical day-to-day flow for using the local
requirement-gated harness in this repository.

Use it like a check-in desk before risky work:

1. start the turn
2. read the required documents the harness selects
3. acknowledge the constraints you extracted
4. do the implementation work
5. run the pre-final audit before calling the work complete

## When To Use This

Use the harness first when:

- changing UI, theme, or layout behavior
- touching reusable components
- making broad refactors
- changing files that should be governed by project rules
- you want an auditable record of required docs, review steps, and final risks

## Step 1: Start A Turn

Run this from the repository root.

Example for a UI task:

```powershell
py scripts\run_turn.py `
  --user-input "Update the Home page UI and verify loading, empty, and error states." `
  --target-path src/pages/HomePage.tsx
```

Example for a theme task:

```powershell
py scripts\run_turn.py `
  --user-input "Refactor the theme token flow and keep the default preset close to stock Ant Design." `
  --target-path src/theme/presets/default.ts
```

Example for a component task:

```powershell
py scripts\run_turn.py `
  --user-input "Fix the app shell menu layout and avoid custom inline styling if AntD already solves it." `
  --target-path src/components/app/AppShell.tsx
```

What this does:

- creates a durable `session_id`, which is the permanent work ledger
- creates a `turn_id`, which is one request inside that ledger
- analyzes the request before execution
- selects the local project documents that must be read first

## Step 2: Generate The Acknowledgement Template

After step 1, the harness prints the `session_id` and `turn_id`.

Create the acknowledgement template:

```powershell
py scripts\ack_required_docs.py `
  --session-id <session_id> `
  --turn-id <turn_id> `
  --template
```

This writes a JSON file under:

```text
.harness/acks/<session>-<turn>.json
```

Think of this as a reading confirmation sheet. It is not enough to say
"I read it." You need to fill in the actual constraints you extracted.

## Step 3: Fill In The Constraints And Submit The Acknowledgement

Open the generated JSON file and write short constraints for each required
document.

Example:

```json
{
  "note": "Summarized the rules before implementation.",
  "documents": [
    {
      "doc_id": "project-agent-rules",
      "digest": "...",
      "read_paths": ["AGENTS.md"],
      "constraints": [
        "Use Ant Design components before custom UI.",
        "Report what works, what does not work yet, and risk remains."
      ]
    }
  ]
}
```

Then submit it:

```powershell
py scripts\ack_required_docs.py `
  --session-id <session_id> `
  --turn-id <turn_id> `
  --input .harness/acks/<session_id>-<turn_id>.json
```

## Step 4: Continue The Turn

Once the acknowledgement is accepted, continue the turn:

```powershell
py scripts\run_turn.py `
  --session-id <session_id> `
  --resume-turn <turn_id>
```

The harness will continue through its implementer, simulated write, reviewer,
and quality-review flow.

## Step 5: Do The Real Implementation Work

The harness gives you the required docs and the execution ledger.
You still do the real coding work in the repository as usual.

Recommended practical pattern:

1. start the turn
2. acknowledge the required docs
3. perform the real edits and checks
4. run the pre-final audit
5. summarize the outcome

## Step 6: Run The Pre-Final Audit

Before you say the work is complete, run:

```powershell
py scripts\pre_final_audit.py `
  --session-id <session_id> `
  --turn-id <turn_id> `
  --compact `
  --json
```

This is the last checkpoint. It checks whether:

- required docs were acknowledged
- the turn has a valid event flow
- quality review exists
- anything still blocks completion

## Useful Support Commands

Run the document-matching evaluator:

```powershell
py scripts\run_doc_eval.py --json
```

Run repository hygiene checks:

```powershell
py scripts\check_repo_hygiene.py --json
```

Run harness runtime tests:

```powershell
$env:PYTHONPATH=(Get-Location).Path
py tests\test_harness_runtime.py
```

## Recommended Standard For This Repository

For UI or theme work, use this minimum flow:

1. `run_turn.py`
2. `ack_required_docs.py --template`
3. fill in constraints
4. `ack_required_docs.py --input ...`
5. do the implementation work
6. `pre_final_audit.py`

If the task is small and read-only, you do not need to force the full flow.
If the task changes UI, theme, shared components, or project rules, treat this
flow as the default start procedure.
