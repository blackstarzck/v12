#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the harness work orchestrator for one queued item.")
    parser.add_argument("--repo-root", default=".", help="Harness repository root.")
    parser.add_argument("--session-id", required=True, help="Session ID to wake.")
    parser.add_argument("--turn-id", default=None, help="Turn ID to enqueue before running.")
    parser.add_argument("--reason", default="operator_requested", help="Reason stored on newly queued work.")
    parser.add_argument("--max-attempts", type=int, default=2, help="Maximum attempts for newly queued work.")
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON.")
    return parser.parse_args()


def configure_imports(repo_root: Path) -> None:
    source_root = Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(source_root))
    if repo_root != source_root:
        sys.path.insert(0, str(repo_root))


def summarize_result(runtime: Any, session_id: str, result: dict[str, Any]) -> dict[str, Any]:
    work_item = result.get("work_item", {})
    turn_id = work_item.get("turn_id")
    flow_event = runtime.store.latest_event(session_id, "flow.checked", str(turn_id)) if turn_id else None
    quality_event = runtime.store.latest_event(session_id, "quality.review_completed", str(turn_id)) if turn_id else None
    return {
        "session_id": session_id,
        "status": result["status"],
        "work_item": work_item,
        "flow_check": flow_event["payload"] if flow_event else None,
        "quality_review": quality_event["payload"] if quality_event else None,
    }


def main() -> int:
    args = parse_args()
    repo_root = Path(args.repo_root).resolve()
    configure_imports(repo_root)

    from generated_harness import HarnessRuntime, WorkOrchestrator

    runtime = HarnessRuntime(repo_root)
    orchestrator = WorkOrchestrator(runtime)
    queued = None
    if args.turn_id:
        queued = orchestrator.enqueue_continue_turn(
            session_id=args.session_id,
            turn_id=args.turn_id,
            reason=args.reason,
            max_attempts=args.max_attempts,
        )
    result = orchestrator.run_next(session_id=args.session_id)
    output = summarize_result(runtime, args.session_id, result)
    output["queued"] = queued

    if args.json:
        print(json.dumps(output, ensure_ascii=False, indent=2))
    else:
        print(f"Session: {args.session_id}")
        if queued:
            print(f"Queued work: {queued['work_item_id']} for turn {queued['turn_id']}")
        print(f"Orchestrator status: {output['status']}")
        work_item = output.get("work_item") or {}
        if work_item:
            print(f"Work item: {work_item.get('work_item_id')} ({work_item.get('kind')})")
        flow_check = output.get("flow_check")
        if flow_check:
            print(f"Flow check: {flow_check.get('status')}")
        quality_review = output.get("quality_review")
        if quality_review:
            print(f"Quality review: {quality_review.get('status')} ({quality_review.get('fallback_action')})")
    return 0 if output["status"] in {"completed", "idle"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
