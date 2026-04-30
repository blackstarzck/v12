from __future__ import annotations

from pathlib import Path
from typing import Any

from .session_store import FileSessionStore


class AntdApiMappingError(RuntimeError):
    pass


ANTD_MAPPING_LABELS = {"antd", "component", "frontend", "ui", "web"}
IMPLEMENTATION_TOOLS = {
    "filesystem.delete",
    "filesystem.move",
    "filesystem.write",
    "git.apply_patch",
    "repo.write",
    "sandbox.execute",
    "shell.run",
}
UI_PATH_PARTS = {
    "app",
    "components",
    "frontend",
    "pages",
    "routes",
    "ui",
    "views",
}
UI_SUFFIXES = {
    ".css",
    ".html",
    ".jsx",
    ".scss",
    ".svelte",
    ".tsx",
    ".vue",
}


def _paths_from_payload(payload: dict[str, Any]) -> list[str]:
    paths: list[str] = []
    for key in ("target_paths", "changed_paths", "paths"):
        value = payload.get(key)
        if isinstance(value, list):
            paths.extend(str(item) for item in value if str(item).strip())
        elif isinstance(value, str) and value.strip():
            paths.append(value)
    return paths


def _path_looks_ui(path: str) -> bool:
    parsed = Path(path)
    parts = {part.lower() for part in parsed.parts}
    if "theme" in parts:
        return False
    if parts & UI_PATH_PARTS:
        return True
    if parsed.suffix.lower() in UI_SUFFIXES and not {"api", "backend", "server"} & parts:
        return True
    return False


class AntdApiMappingGate:
    """Requires recorded AntD API mapping before UI implementation tools run."""

    def __init__(self, store: FileSessionStore) -> None:
        self.store = store

    def _required_documents(self, *, session_id: str, turn_id: str) -> list[dict[str, Any]]:
        required = self.store.latest_event(session_id, "docs.required", turn_id)
        if required is None:
            return []
        return required["payload"].get("documents", [])

    def _turn_target_paths(self, *, session_id: str, turn_id: str) -> list[str]:
        turn = self.store.latest_event(session_id, "turn.started", turn_id)
        if turn is None:
            return []
        return [str(path) for path in turn["payload"].get("target_paths", [])]

    def requires_mapping(
        self,
        *,
        session_id: str,
        turn_id: str,
        tool_name: str | None = None,
        payload: dict[str, Any] | None = None,
    ) -> bool:
        if tool_name is not None and tool_name not in IMPLEMENTATION_TOOLS:
            return False

        paths = self._turn_target_paths(session_id=session_id, turn_id=turn_id)
        if payload:
            paths.extend(_paths_from_payload(payload))
        if paths and all("theme" in {part.lower() for part in Path(path).parts} for path in paths):
            return False

        documents = self._required_documents(session_id=session_id, turn_id=turn_id)
        labels = {
            str(label).lower()
            for document in documents
            for label in document.get("labels", [])
            if str(label).strip()
        }
        if labels & ANTD_MAPPING_LABELS:
            return True

        return any(_path_looks_ui(path) for path in paths)

    def latest_completed(self, *, session_id: str, turn_id: str) -> dict[str, Any] | None:
        event = self.store.latest_event(session_id, "antd.api_mapping.completed", turn_id)
        return event["payload"] if event else None

    def ensure_completed(
        self,
        *,
        session_id: str,
        turn_id: str,
        tool_name: str,
        payload: dict[str, Any],
    ) -> None:
        if not self.requires_mapping(
            session_id=session_id,
            turn_id=turn_id,
            tool_name=tool_name,
            payload=payload,
        ):
            return
        if self.latest_completed(session_id=session_id, turn_id=turn_id) is not None:
            return
        self.store.emit_event(
            session_id,
            "tool.blocked",
            {
                "turn_id": turn_id,
                "tool_name": tool_name,
                "reason": "antd api mapping not completed",
            },
        )
        raise AntdApiMappingError("Blocked until AntD API mapping is recorded for this UI implementation turn.")

    def record_completed(
        self,
        *,
        session_id: str,
        turn_id: str,
        visible_data: list[str],
        states: list[str],
        actions: list[str],
        layout_roles: list[str],
        component_mappings: list[dict[str, Any]],
        sources: list[str] | None = None,
        custom_justifications: list[str] | None = None,
        agent_run_id: str | None = None,
    ) -> dict[str, Any]:
        if not component_mappings:
            raise AntdApiMappingError("AntD API mapping requires at least one component mapping.")

        normalized_mappings: list[dict[str, Any]] = []
        for mapping in component_mappings:
            component = str(mapping.get("component", "")).strip()
            prop_mappings = mapping.get("prop_mappings", [])
            if not component:
                raise AntdApiMappingError("Each AntD API mapping item requires a component.")
            if not isinstance(prop_mappings, list) or not prop_mappings:
                raise AntdApiMappingError(f"Component {component} requires at least one prop mapping.")
            normalized_mappings.append(
                {
                    "component": component,
                    "source_requirements": [
                        str(item)
                        for item in mapping.get("source_requirements", [])
                        if str(item).strip()
                    ],
                    "prop_mappings": [
                        str(item)
                        for item in prop_mappings
                        if str(item).strip()
                    ],
                    "custom_needed": bool(mapping.get("custom_needed", False)),
                    "notes": str(mapping.get("notes", "")).strip(),
                }
            )

        payload = {
            "turn_id": turn_id,
            "agent_run_id": agent_run_id,
            "visible_data": [str(item) for item in visible_data if str(item).strip()],
            "states": [str(item) for item in states if str(item).strip()],
            "actions": [str(item) for item in actions if str(item).strip()],
            "layout_roles": [str(item) for item in layout_roles if str(item).strip()],
            "component_mappings": normalized_mappings,
            "sources": [str(item) for item in sources or [] if str(item).strip()],
            "custom_justifications": [
                str(item)
                for item in custom_justifications or []
                if str(item).strip()
            ],
        }
        self.store.emit_event(session_id, "antd.api_mapping.completed", payload)
        return payload
