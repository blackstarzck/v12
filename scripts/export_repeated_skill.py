#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Export a repeated workflow suggestion as a reusable skill.")
    parser.add_argument("--repo-root", default=".", help="Target repository root.")
    parser.add_argument("--skill-id", default=None, help="Specific suggested skill id to export. Defaults to latest suggestion.")
    parser.add_argument("--overwrite", action="store_true", help="Overwrite an existing generated skill.")
    parser.add_argument("--json", action="store_true", help="Print machine-readable output.")
    return parser.parse_args()


def dedupe_suggestions(suggestions: list[dict[str, Any]]) -> list[dict[str, Any]]:
    deduped: dict[str, dict[str, Any]] = {}
    for suggestion in suggestions:
        key = str(suggestion.get("skill_id") or suggestion.get("workflow_signature") or "")
        if not key:
            continue
        current = deduped.get(key)
        if current is None or int(suggestion.get("repeat_count", 0)) >= int(current.get("repeat_count", 0)):
            deduped[key] = suggestion
    return list(deduped.values())


def print_result(result: dict[str, Any], *, as_json: bool) -> None:
    if as_json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return
    if result["status"] == "exported":
        print(f"Exported repeated workflow skill to {result['skill_path']}")
        print(f"Exported skill README to {result['readme_path']}")
    elif result["status"] == "already_exists":
        print(f"Repeated workflow skill already exists at {result['skill_path']}")
    print(f"Validation: {result['validation']['status']}")


def main() -> int:
    args = parse_args()
    repo_root = Path(args.repo_root).resolve()
    sys.path.insert(0, str(repo_root))

    from generated_harness.skill_registry import SkillRegistry

    memory_path = repo_root / ".harness" / "requirement_memory.json"
    if not memory_path.exists():
        raise SystemExit("No requirement memory exists yet. Run repeated turns first.")

    memory = json.loads(memory_path.read_text(encoding="utf-8"))
    suggestions = dedupe_suggestions(memory.get("skill_suggestions", []))
    if args.skill_id:
        suggestions = [suggestion for suggestion in suggestions if suggestion.get("skill_id") == args.skill_id]
    if not suggestions:
        raise SystemExit("No repeated workflow skill suggestion found.")

    registry = SkillRegistry(repo_root)
    suggestion = suggestions[-1]
    try:
        output_path = registry.export_repeated_skill(suggestion, overwrite=args.overwrite)
        status = "exported"
    except FileExistsError:
        from generated_harness.skill_registry import slugify_skill_id

        output_path = registry.skill_root() / slugify_skill_id(str(suggestion.get("skill_id"))) / "SKILL.md"
        status = "already_exists"
    validation = registry.validate_exported_skill(output_path)
    result = {
        "status": status,
        "skill_id": suggestion.get("skill_id"),
        "skill_path": str(output_path),
        "readme_path": str(output_path.with_name("README.md")),
        "validation": validation,
    }
    print_result(result, as_json=args.json)
    if validation["status"] != "passed":
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
