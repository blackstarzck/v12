from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path


BLOCKED_PARTS = {
    ".harness",
    "__pycache__",
    ".pytest_cache",
    ".venv",
    "venv",
}

BLOCKED_SUFFIXES = {
    ".pyc",
    ".pyo",
}

BLOCKED_FILENAMES = {
    ".env",
    ".env.local",
}


def tracked_files(repo_root: Path) -> list[str]:
    completed = subprocess.run(
        ["git", "ls-files", "--", "."],
        cwd=repo_root,
        text=True,
        capture_output=True,
        check=False,
    )
    if completed.returncode != 0:
        raise RuntimeError(completed.stderr.strip() or "git ls-files failed")
    return [line.strip().replace("\\", "/") for line in completed.stdout.splitlines() if line.strip()]


def is_blocked(path: str) -> bool:
    parts = set(Path(path).parts)
    name = Path(path).name
    suffix = Path(path).suffix
    return bool(parts & BLOCKED_PARTS) or name in BLOCKED_FILENAMES or suffix in BLOCKED_SUFFIXES


def check_hygiene(repo_root: Path) -> dict[str, object]:
    files = tracked_files(repo_root)
    blocked = sorted(path for path in files if is_blocked(path))
    return {
        "status": "passed" if not blocked else "failed",
        "blocked_files": blocked,
        "checked_files": len(files),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Reject tracked runtime state and local environment files.")
    parser.add_argument("--repo-root", default=Path(__file__).resolve().parents[1])
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    result = check_hygiene(Path(args.repo_root).resolve())
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(f"Repository hygiene: {result['status']}")
        for path in result["blocked_files"]:
            print(f"- blocked tracked file: {path}")
    return 0 if result["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
