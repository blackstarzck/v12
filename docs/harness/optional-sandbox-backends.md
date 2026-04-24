# Optional Sandbox Backends

## Practical Conclusion

The core harness should stay small. `LocalProcessSandboxBackend` is the default
operational backend for local smoke tests, while Docker, Vercel Sandbox, or any
stronger isolation layer should be added only as an adapter.

In plain language: the harness owns the ledger and the rules. The sandbox
backend is the replaceable room where risky commands run.

## Backend Contract

Any stronger sandbox backend must preserve this contract:

- `provision(...)` creates a fresh workspace and returns a backend reference.
- `execute(...)` runs one command against that workspace.
- `dispose(...)` removes or releases the workspace.
- Credentials do not enter the sandbox input or environment by default.
- Backend failure records `sandbox.failed`; it must not delete the main
  `session_id` event log.

## Local Backend

Use this when the code is trusted enough for local execution and the goal is
repeatable smoke testing.

- Module: `generated_harness/local_sandbox_backend.py`
- Isolation level: local process workspace, not a security-grade VM
- Good for: harness tests, simple command execution, local development
- Not good for: untrusted code, hostile dependencies, network isolation

## Docker Recipe

Use Docker only when a project already accepts container setup as part of its
developer workflow.

Adapter shape:

1. Build or pull a project-specific image outside the harness turn.
2. Mount a per-`sandbox_ref` workspace, not the main repo root.
3. Pass only scrubbed environment variables.
4. Run commands with CPU, memory, network, and timeout limits.
5. Copy allowed artifacts back through an explicit result path.
6. Emit the normal harness events through `SandboxAdapter`.

The Docker adapter should not be required by the core harness package. Keep it
behind the same `SandboxBackend` protocol used by the local backend.

## Vercel Sandbox Recipe

Use Vercel Sandbox only when a hosted Firecracker-style microVM is worth the
extra platform dependency.

Adapter shape:

1. Provision one sandbox per `sandbox_ref`.
2. Upload the minimal file set needed for the task.
3. Run commands through the provider SDK or API.
4. Stream or collect command output into the `sandbox.execute` result.
5. Dispose the remote sandbox when the turn or work item ends.
6. Keep provider tokens in the host runtime, never in sandbox-visible payloads.

This stays optional because many harness experiments only need local trusted
execution. Requiring a hosted sandbox would make the harness larger than the
problem it is solving.

## Acceptance Check

For any optional backend, run the same tests expected of the local backend:

- successful command execution
- timeout or crash records `sandbox.failed`
- disposed or failed sandbox reuse is blocked
- credential-looking keys are blocked before backend execution
- the main session can still replay after backend failure
