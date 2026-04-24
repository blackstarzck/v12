# Hosted Operations

## Practical Conclusion

The current harness is safe for one local workspace and local workers. For
multiple machines, the design needs an external coordinator before it should be
treated as production scheduling.

Think of the current file session store as a notebook on one desk. It has a
lock so two hands on the same desk do not write the same line at once. If the
work moves to several desks, the notebook must move to a shared service.

## What Works Locally

- `FileSessionStore` keeps an append-only JSONL event log.
- Session writes are protected by a local filesystem lock.
- `WorkOrchestrator` records `work.queued`, `work.lease_acquired`,
  `work.started`, `work.completed`, `work.failed`, and retry events.
- Lease acquisition is checked and appended under the session-store lock.

## What Must Change For Multiple Machines

Use an external store when more than one host can run the same harness library.
The external store must provide:

- atomic append for session events
- compare-and-set or transaction support for work leases
- monotonic event ordering per `session_id`
- durable read-after-write behavior
- retention policy for raw session logs and compact summaries

Good implementation targets include SQLite on one host, Postgres, durable queue
services, or a workflow engine. The exact service is less important than the
contract: one work item must not be claimed by two workers at the same time.

## Hosted Scheduler Contract

A hosted scheduler should only own wakeups and leases. It must not own prompt
content, tool execution, or sandbox internals.

Required behavior:

1. Read pending `work.queued` items.
2. Atomically acquire one lease.
3. Start work by calling the runtime or orchestrator.
4. Mark completion or failure in the session log.
5. Schedule retry with bounded backoff when allowed.
6. Mark stale agent runs as `agent.timed_out` before retrying a turn.

## Deferred Until Needed

Do not add a distributed scheduler by default. Add it only when one of these is
true:

- multiple machines need to resume the same sessions
- work must survive host restarts without operator action
- the harness is serving several users or repositories at once
- sandbox work can run longer than one local desktop session

Until then, the local orchestrator is the smaller and easier-to-debug path.
