#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Check a harness turn against the documented execution flow.")
    parser.add_argument("--repo-root", default=".", help="Harness repository root.")
    parser.add_argument("--session-id", required=True, help="Session ID to inspect.")
    parser.add_argument("--turn-id", default=None, help="Turn ID to inspect. If omitted, the session must contain one turn.")
    parser.add_argument("--emit", action="store_true", help="Also append a flow.checked event.")
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON.")
    return parser.parse_args()


def configure_imports(repo_root: Path) -> None:
    source_root = Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(source_root))
    if repo_root != source_root:
        sys.path.insert(0, str(repo_root))


def resolve_turn_id(store: Any, session_id: str, requested_turn_id: str | None) -> str:
    if requested_turn_id:
        return requested_turn_id
    turn_ids = [
        str(event["payload"]["turn_id"])
        for event in store.get_events(session_id)
        if event["event_type"] == "turn.started" and event.get("payload", {}).get("turn_id")
    ]
    unique_turn_ids = sorted(set(turn_ids))
    if len(unique_turn_ids) == 1:
        return unique_turn_ids[0]
    if not unique_turn_ids:
        raise SystemExit(f"No turns found in session {session_id}.")
    raise SystemExit("Pass --turn-id because this session contains multiple turns.")


def main() -> int:
    args = parse_args()
    repo_root = Path(args.repo_root).resolve()
    configure_imports(repo_root)

    from generated_harness import ExecutionFlowVerifier, HarnessRuntime

    runtime = HarnessRuntime(repo_root)
    turn_id = resolve_turn_id(runtime.store, args.session_id, args.turn_id)
    verifier = ExecutionFlowVerifier(runtime.store)
    result = verifier.verify_turn(session_id=args.session_id, turn_id=turn_id)
    emitted = None
    if args.emit:
        emitted = verifier.emit_check(session_id=args.session_id, turn_id=turn_id)

    output = {
        "session_id": args.session_id,
        "turn_id": turn_id,
        "status": result.status,
        "findings": result.findings,
        "emitted": emitted,
    }
    if args.json:
        print(json.dumps(output, ensure_ascii=False, indent=2))
    else:
        print(f"Session: {args.session_id}")
        print(f"Turn: {turn_id}")
        print(f"Flow check: {result.status}")
        if result.findings:
            print("Findings:")
            for finding in result.findings:
                location = f" at event #{finding.get('sequence')}" if finding.get("sequence") else ""
                print(f"  - {finding['code']}{location}: {finding['message']}")
        if emitted:
            print(f"Recorded flow.checked event #{emitted['sequence']}.")
    return 0 if result.status == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
