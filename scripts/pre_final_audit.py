from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


def load_harness(repo_root: Path) -> None:
    sys.path.insert(0, str(repo_root))


def audit_turn(
    *,
    repo_root: Path,
    session_id: str,
    turn_id: str,
    compact: bool = False,
) -> dict[str, Any]:
    load_harness(repo_root)
    from generated_harness import HarnessRuntime, audit_runtime_turn

    runtime = HarnessRuntime(repo_root)
    return audit_runtime_turn(
        runtime=runtime,
        session_id=session_id,
        turn_id=turn_id,
        compact=compact,
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run host-side pre-final harness audit.")
    parser.add_argument("--repo-root", default=Path(__file__).resolve().parents[1])
    parser.add_argument("--session-id", required=True)
    parser.add_argument("--turn-id", required=True)
    parser.add_argument("--compact", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    result = audit_turn(
        repo_root=Path(args.repo_root).resolve(),
        session_id=args.session_id,
        turn_id=args.turn_id,
        compact=args.compact,
    )
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(f"Pre-final audit: {result['status']}")
        for finding in result["findings"]:
            print(f"- {finding['code']}: {finding['message']}")
    return 0 if result["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
