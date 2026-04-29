from __future__ import annotations

from typing import Any

from .session_store import FileSessionStore


THEME_INTENT_TERMS = (
    "theme",
    "theming",
    "token",
    "tokens",
    "appearance",
    "preset",
    "dark mode",
    "light mode",
    "palette",
    "brand color",
    "design token",
    "component token",
    "global token",
    "configprovider",
    "getapptheme",
    "\ud14c\ub9c8",
    "\ud1a0\ud070",
    "\ub2e4\ud06c \ubaa8\ub4dc",
    "\ub77c\uc774\ud2b8 \ubaa8\ub4dc",
    "\ud504\ub9ac\uc14b",
)

VISUAL_SCOPE_TERMS = (
    "color",
    "background",
    "bg",
    "radius",
    "rounded",
    "border",
    "shadow",
    "font",
    "spacing",
    "surface",
    "padding",
    "header bg",
    "\uc0c9\uc0c1",
    "\ubc30\uacbd",
    "\ub77c\uc6b4\ub4dc",
    "\ubaa8\uc11c\ub9ac",
    "\ub450\uaed8",
    "\uadf8\ub9bc\uc790",
    "\uac04\uaca9",
    "\ud3f0\ud2b8",
)

COMPONENT_SCOPE_TERMS = (
    "card",
    "button",
    "input",
    "menu",
    "layout",
    "table",
    "form",
    "drawer",
    "modal",
    "tabs",
    "steps",
    "component",
    "antd",
    "\uce74\ub4dc",
    "\ubc84\ud2bc",
    "\uc785\ub825",
    "\ub808\uc774\uc544\uc6c3",
    "\ud14c\uc774\ube14",
    "\ud3fc",
    "\ub4dc\ub85c\uc5b4",
    "\ubaa8\ub2ec",
    "\ud0ed",
    "\ucef4\ud3ec\ub10c\ud2b8",
)

THEME_SCOPE_PATHS = (
    "src/theme/",
    "src/styles/",
    "src/main.tsx",
)

THEME_FAST_START_PATHS = [
    "docs/harness/theme-fast-start.md",
    "docs/ant-design/08-theme-architecture.md",
    "src/theme/index.ts",
    "src/theme/registry.ts",
    "src/theme/create-theme.ts",
    "src/theme/global/shared-seed.ts",
    "src/theme/components/shared.ts",
    "src/theme/presets/default.ts",
    "src/main.tsx",
]

THEME_CLARIFICATION_QUESTIONS = [
    "Scope: should this change affect the whole app, one component family, one page, or one local section?",
    "Target surface: which component, page, or visual state should change?",
    "Appearance: should the change apply to light mode, dark mode, or both?",
    "Implementation layer: do you want a global token, a component token, a named preset, or a local scoped override?",
    "Guardrails: which current values or areas must stay unchanged?",
]


class ClarificationRequiredError(RuntimeError):
    pass


def _normalized_paths(target_paths: list[str]) -> list[str]:
    return [path.replace("\\", "/").strip() for path in target_paths if str(path).strip()]


def _theme_paths_requested(target_paths: list[str]) -> bool:
    normalized = _normalized_paths(target_paths)
    return any(
        candidate == scope_path or candidate.startswith(scope_path)
        for candidate in normalized
        for scope_path in THEME_SCOPE_PATHS
    )


def _theme_language_requested(user_input: str) -> bool:
    lowered = user_input.lower()
    if any(term in lowered for term in THEME_INTENT_TERMS):
        return True
    return any(term in lowered for term in VISUAL_SCOPE_TERMS) and any(
        term in lowered for term in COMPONENT_SCOPE_TERMS
    )


def theme_clarification_needed(
    *,
    user_input: str,
    target_paths: list[str],
    required_documents: list[dict[str, Any]],
) -> bool:
    if _theme_paths_requested(target_paths):
        return True
    if _theme_language_requested(user_input):
        return True
    return any("theme-clarification" in doc.get("labels", []) for doc in required_documents)


def build_theme_clarification_payload(
    *,
    turn_id: str,
    user_input: str,
    target_paths: list[str],
    required_documents: list[dict[str, Any]],
) -> dict[str, Any]:
    return {
        "turn_id": turn_id,
        "category": "theme_scope_confirmation",
        "reason": "Theme-related work must confirm exact scope before planning, doc gating, or execution.",
        "summary": "Confirm the exact theme scope before reading broadly or changing tokens.",
        "questions": list(THEME_CLARIFICATION_QUESTIONS),
        "fast_start_paths": list(THEME_FAST_START_PATHS),
        "target_paths": target_paths,
        "related_doc_ids": [doc.get("doc_id") for doc in required_documents],
        "user_input": user_input,
    }


def merged_user_input(original_user_input: str, clarification_response: str) -> str:
    return (
        f"{original_user_input.strip()}\n\n"
        "Confirmed theme clarification:\n"
        f"{clarification_response.strip()}"
    )


def latest_clarification_required(
    store: FileSessionStore,
    *,
    session_id: str,
    turn_id: str,
) -> dict[str, Any] | None:
    event = store.latest_event(session_id, "clarification.required", turn_id)
    return None if event is None else event["payload"]


def latest_clarification_resolved(
    store: FileSessionStore,
    *,
    session_id: str,
    turn_id: str,
) -> dict[str, Any] | None:
    event = store.latest_event(session_id, "clarification.resolved", turn_id)
    return None if event is None else event["payload"]


def ensure_clarification_resolved(
    store: FileSessionStore,
    *,
    session_id: str,
    turn_id: str,
    block_event_type: str | None = "tool.blocked",
) -> dict[str, Any] | None:
    required_event = store.latest_event(session_id, "clarification.required", turn_id)
    if required_event is None:
        return None
    resolved_event = store.latest_event(session_id, "clarification.resolved", turn_id)
    if resolved_event is not None and int(resolved_event["sequence"]) > int(required_event["sequence"]):
        return resolved_event["payload"]

    payload = {
        "turn_id": turn_id,
        "reason": "required theme clarification not resolved",
        "category": required_event["payload"].get("category"),
        "questions": required_event["payload"].get("questions", []),
        "fast_start_paths": required_event["payload"].get("fast_start_paths", []),
    }
    if block_event_type:
        store.emit_event(session_id, block_event_type, payload)
    raise ClarificationRequiredError("Blocked until required theme clarification is resolved.")
