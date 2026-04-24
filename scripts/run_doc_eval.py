from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


def load_harness(repo_root: Path) -> None:
    sys.path.insert(0, str(repo_root))


def load_cases(case_file: Path) -> list[dict[str, Any]]:
    payload = json.loads(case_file.read_text(encoding="utf-8"))
    cases = payload.get("cases", [])
    if not isinstance(cases, list):
        raise ValueError("Eval case file must contain a 'cases' list.")
    return cases


def run_eval(repo_root: Path, case_file: Path) -> dict[str, Any]:
    load_harness(repo_root)
    from generated_harness.document_registry import DocumentRegistry

    registry = DocumentRegistry(repo_root)
    results: list[dict[str, Any]] = []
    for index, case in enumerate(load_cases(case_file), start=1):
        name = str(case.get("name") or f"case_{index}")
        user_input = str(case.get("user_input") or "")
        target_paths = [str(path) for path in case.get("target_paths", [])]
        expected = [str(doc_id) for doc_id in case.get("expected_doc_ids", [])]
        matched, inferred_intents, suggestions = registry.match(
            user_input=user_input,
            target_paths=target_paths,
            memory={},
        )
        actual = [doc.doc_id for doc in matched]
        missing = [doc_id for doc_id in expected if doc_id not in actual]
        unexpected = [doc_id for doc_id in actual if doc_id not in expected]
        results.append(
            {
                "name": name,
                "status": "passed" if not missing and not unexpected else "failed",
                "user_input": user_input,
                "target_paths": target_paths,
                "expected_doc_ids": expected,
                "actual_doc_ids": actual,
                "missing_doc_ids": missing,
                "unexpected_doc_ids": unexpected,
                "inferred_intents": inferred_intents,
                "registry_suggestions": suggestions,
            }
        )
    failed = [result for result in results if result["status"] == "failed"]
    return {
        "status": "passed" if not failed else "failed",
        "case_file": str(case_file),
        "total": len(results),
        "passed": len(results) - len(failed),
        "failed": len(failed),
        "results": results,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Evaluate required-document matching.")
    parser.add_argument("--repo-root", default=Path(__file__).resolve().parents[1])
    parser.add_argument("--case-file", default=None)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    repo_root = Path(args.repo_root).resolve()
    case_file = Path(args.case_file).resolve() if args.case_file else repo_root / "config" / "required_doc_eval.json"
    result = run_eval(repo_root, case_file)
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(f"Required-document eval: {result['status']} ({result['passed']}/{result['total']} passed)")
        for case in result["results"]:
            detail = ", ".join(case["actual_doc_ids"]) or "none"
            print(f"- {case['name']}: {case['status']} -> {detail}")
    return 0 if result["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
