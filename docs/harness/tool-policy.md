# requirement-gated-python-harness Tool Policy

## Defaults

- default mode: deny
- all tool calls must be audited
- every tool call receives a `tool_call_id`
- every `tool.called` must end with `tool.completed` or `tool.failed` before the turn closes
- tool events should include `agent_run_id` when a role execution caused the call
- sandbox tool events should also include `sandbox_ref`
- mutating and unknown tool calls require `requirements.analyzed` for the current turn
- required-doc acknowledgement is checked before write, shell, sandbox, and unknown tools
- sandbox provisioning is also blocked until required-doc acknowledgement when the turn has required documents
- sandbox execution requires a known, active `sandbox_ref`
- disposed or failed sandboxes cannot be reused; the orchestrator must provision a replacement sandbox
- sandbox resources and execution input must not include credential-looking keys such as token, secret, password, credential, auth, api_key, access_key, or private_key
- browser validation uses `validator.browser` and should be audited with `tool_call_id` when a real browser handler runs
- external Playwright MCP validation can be requested with `validation.requested` and must be recorded back as `validator.browser`
- Codex host integrations should prefer `runtime.codex.recorded_call(...)` so begin, completion, and failure recording stay paired by `tool_call_id`
- Codex host integrations that cannot use the callable wrapper should use `runtime.codex.tool_call(...)` as a context manager
- Host integrations can use `CodexHostGuard` to bind one `session_id` and `turn_id`, wrap tool calls, and require pre-final audit before final output
- read-only tools must be explicitly listed; unknown tools are treated as risky until classified
- denied tools emit `tool.blocked` and raise `ToolPolicyError` before handler execution
- acknowledgement must include extracted constraints for every required document
- acknowledgement is tied to document digests, so changed documents require a new acknowledgement
- changed files are recorded as `repo.changed`
- `repo.changed` must include the `tool_call_id` that caused the change; missing IDs indicate an unwrapped host-tool change
- tool audit payloads and results redact sensitive-looking keys before they are written to the durable event log
- post-run reviewer reminders are emitted after implementation even when validation passes
- post-run quality review routes work to fallback actions instead of hard-blocking reminder-only issues

## Read-Only Without Acknowledgement

- `repo.read`: read repository state
- `repo.search`: search repository state
- `filesystem.read`: read a file
- `git.diff`: inspect local changes

## Requires Requirement Analysis And Required-Doc Acknowledgement

- `shell.run`: runs commands and can mutate files or external systems
- `sandbox.execute`: runs isolated commands
- `repo.write`: mutates repository state
- `filesystem.write`: mutates repository state
- `git.apply_patch`: maps to Codex `apply_patch`
- `validator.browser`: runs reviewer-owned browser validation and records pass, failure, or unavailable status as `validation.completed`
- unknown tool names: blocked until they are classified as read-only or acknowledged as risky

## Require Extra Approval

- `external.publish`: affects remote systems
- `git.commit`: records repository history

## Deny

- `credential.dump`: secrets must stay outside the sandbox and host tool layer
- sandbox payloads containing credential-looking keys: blocked before execution and recorded as `sandbox.blocked`

## Codex Tool Aliases

- `apply_patch` -> `git.apply_patch`
- `functions.apply_patch` -> `git.apply_patch`
- `shell_command` -> `shell.run`
- `functions.shell_command` -> `shell.run`
- `browser_review` -> `validator.browser`
- `playwright` -> `validator.browser`

## Codex Wrapper Modes

- `runtime.codex.recorded_call(...)`: preferred path for host integrations that can run the real tool as a callable; automatically emits `tool.completed` or `tool.failed`
- `runtime.codex.tool_call(...)`: context-manager path for host integrations that need manual completion; emits `tool.failed` if the context exits without `complete(...)`
- `runtime.codex.begin(...)`, `complete(...)`, `fail(...)`: low-level API for advanced hosts that need direct event control
- `CodexHostGuard.recorded_call(...)`: host-facing convenience wrapper for one bound `session_id` and `turn_id`
- `CodexHostGuard.require_final_audit(...)`: host-facing final gate that raises `HostAuditError` unless the turn is complete, quality-reviewed, and flow-valid

## Audit Fields

Capture at least:

- session_id
- turn_id
- agent_run_id
- tool_call_id
- sandbox_ref when the tool uses a sandbox
- validation tool_call_id when browser validation calls a real browser handler
- tool name
- normalized input
- result or error
- policy decision
- requirement analysis status
- changed paths for mutating tools
- quality fallback action after review
