#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def parse_artifact(value: str) -> tuple[str, str]:
    if "=" not in value:
        raise argparse.ArgumentTypeError("Artifacts must use key=value format.")
    key, artifact_value = value.split("=", 1)
    key = key.strip()
    if not key:
        raise argparse.ArgumentTypeError("Artifact key cannot be empty.")
    return key, artifact_value


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Bridge Playwright MCP browser review requests and results.")
    parser.add_argument("--repo-root", default=".", help="Harness repository root.")
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON.")

    subparsers = parser.add_subparsers(dest="command", required=True)
    request = subparsers.add_parser("request", help="Write a Playwright MCP review request file.")
    request.add_argument("--session-id", required=True, help="Session ID to inspect.")
    request.add_argument("--turn-id", required=True, help="Turn ID to inspect.")
    request.add_argument("--app-url", default=None, help="Application URL for the browser run.")
    request.add_argument("--agent-run-id", default=None, help="Reviewer agent run ID when known.")

    record = subparsers.add_parser("record", help="Record a completed Playwright MCP review result.")
    record.add_argument("--session-id", required=True, help="Session ID to update.")
    record.add_argument("--turn-id", required=True, help="Turn ID to update.")
    record.add_argument("--request-id", default=None, help="Request ID created by the request command.")
    record.add_argument("--status", required=True, choices=["passed", "failed", "error", "unavailable"])
    record.add_argument("--summary", required=True, help="Short result summary.")
    record.add_argument("--agent-run-id", default=None, help="Reviewer agent run ID when known.")
    record.add_argument("--artifact", action="append", type=parse_artifact, default=[], help="Artifact as key=value.")
    return parser.parse_args()


def configure_imports(repo_root: Path) -> None:
    source_root = Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(source_root))
    if repo_root != source_root:
        sys.path.insert(0, str(repo_root))


def print_request(result: dict[str, object]) -> None:
    print(f"Browser review request: {result['request_id']}")
    print(f"Request file: {result['request_path']}")
    print("Run Playwright MCP with the checks in that request file, then record the result:")
    print(
        "py scripts/playwright_mcp_review.py record "
        f"--session-id {result['request']['session_id']} "
        f"--turn-id {result['turn_id']} "
        f"--request-id {result['request_id']} "
        "--status passed --summary \"Browser review passed\""
    )


def print_record(result: dict[str, object]) -> None:
    print(f"Browser validation: {result['status']}")
    print(f"Tool call: {result['tool_call_id']}")
    print(f"Summary: {result['summary']}")


def main() -> int:
    args = parse_args()
    repo_root = Path(args.repo_root).resolve()
    configure_imports(repo_root)

    from generated_harness import HarnessRuntime, PlaywrightMcpBridge

    runtime = HarnessRuntime(repo_root)
    bridge = PlaywrightMcpBridge(repo_root, runtime.store, runtime.tool_gateway)
    if args.command == "request":
        result = bridge.request_review(
            session_id=args.session_id,
            turn_id=args.turn_id,
            app_url=args.app_url,
            agent_run_id=args.agent_run_id,
        )
        if args.json:
            print(json.dumps(result, ensure_ascii=False, indent=2))
        else:
            print_request(result)
        return 0

    artifacts = {key: value for key, value in args.artifact}
    result = bridge.record_review_result(
        session_id=args.session_id,
        turn_id=args.turn_id,
        request_id=args.request_id,
        status=args.status,
        summary=args.summary,
        artifacts=artifacts,
        agent_run_id=args.agent_run_id,
    )
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print_record(result)
    return 0 if result["status"] in {"passed", "unavailable"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
