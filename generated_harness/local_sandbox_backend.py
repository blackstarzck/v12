from __future__ import annotations

import os
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any


SAFE_ENV_KEYS = {
    "COMSPEC",
    "HOME",
    "PATH",
    "PATHEXT",
    "SYSTEMDRIVE",
    "SYSTEMROOT",
    "TEMP",
    "TMP",
    "USERPROFILE",
    "WINDIR",
}


class SandboxBackendError(RuntimeError):
    """Raised when the sandbox backend cannot provision or execute work."""


@dataclass
class LocalSandboxState:
    sandbox_ref: str
    workspace_path: Path
    timeout_seconds: float


class LocalProcessSandboxBackend:
    """Run sandbox commands in a dedicated local workspace with a scrubbed env.

    This backend is an operational bridge, not a security-grade VM. It gives the
    harness a real process boundary for smoke tests and local development while
    keeping the stronger sandbox contract behind SandboxAdapter.
    """

    def __init__(
        self,
        repo_root: str | Path,
        *,
        sandbox_root: str | Path | None = None,
        default_timeout_seconds: float = 30,
        max_output_chars: int = 12000,
        keep_workspaces: bool = False,
    ) -> None:
        self.repo_root = Path(repo_root).resolve()
        self.sandbox_root = Path(sandbox_root).resolve() if sandbox_root else self.repo_root / ".harness" / "sandboxes"
        self.default_timeout_seconds = default_timeout_seconds
        self.max_output_chars = max_output_chars
        self.keep_workspaces = keep_workspaces
        self._states: dict[str, LocalSandboxState] = {}

    def _workspace_path(self, sandbox_ref: str) -> Path:
        if not sandbox_ref.startswith("sandbox_") or not sandbox_ref.replace("_", "").isalnum():
            raise SandboxBackendError(f"Unsafe sandbox_ref: {sandbox_ref}")
        return (self.sandbox_root / sandbox_ref).resolve()

    def _safe_repo_path(self, path: str) -> Path:
        candidate = (self.repo_root / path).resolve()
        if candidate != self.repo_root and self.repo_root not in candidate.parents:
            raise SandboxBackendError(f"Path escapes repo root: {path}")
        return candidate

    def _safe_workspace_path(self, state: LocalSandboxState, path: str | None) -> Path:
        if not path:
            return state.workspace_path
        candidate = (state.workspace_path / path).resolve()
        if candidate != state.workspace_path and state.workspace_path not in candidate.parents:
            raise SandboxBackendError(f"Path escapes sandbox workspace: {path}")
        return candidate

    def _timeout(self, value: Any | None) -> float:
        if value is None:
            return self.default_timeout_seconds
        try:
            timeout = float(value)
        except (TypeError, ValueError) as exc:
            raise SandboxBackendError(f"Invalid timeout_seconds: {value!r}") from exc
        if timeout <= 0:
            raise SandboxBackendError("timeout_seconds must be greater than zero.")
        return timeout

    def _copy_path(self, source: Path, destination: Path) -> None:
        if not source.exists():
            raise SandboxBackendError(f"Sandbox copy path does not exist: {source}")
        if source.is_dir():
            if destination.exists():
                shutil.rmtree(destination)
            shutil.copytree(
                source,
                destination,
                ignore=shutil.ignore_patterns(".git", ".harness", "__pycache__", "*.pyc"),
            )
            return
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)

    def _copy_requested_paths(self, workspace_path: Path, resources: dict[str, Any]) -> list[str]:
        copy_paths = resources.get("copy_paths", [])
        if isinstance(copy_paths, str):
            copy_paths = [copy_paths]
        if not isinstance(copy_paths, list):
            raise SandboxBackendError("resources.copy_paths must be a string or list of strings.")
        copied: list[str] = []
        for raw_path in copy_paths:
            relative_path = str(raw_path).replace("\\", "/").strip()
            if not relative_path:
                continue
            source = self._safe_repo_path(relative_path)
            destination = (workspace_path / relative_path).resolve()
            if destination != workspace_path and workspace_path not in destination.parents:
                raise SandboxBackendError(f"Copy path escapes sandbox workspace: {relative_path}")
            self._copy_path(source, destination)
            copied.append(relative_path)
        return copied

    def _state_for_execute(self, sandbox_ref: str) -> LocalSandboxState:
        state = self._states.get(sandbox_ref)
        if state:
            return state
        workspace_path = self._workspace_path(sandbox_ref)
        if not workspace_path.exists():
            raise SandboxBackendError(f"Local sandbox workspace is missing: {sandbox_ref}")
        state = LocalSandboxState(
            sandbox_ref=sandbox_ref,
            workspace_path=workspace_path,
            timeout_seconds=self.default_timeout_seconds,
        )
        self._states[sandbox_ref] = state
        return state

    def _clean_env(self, extra_env: Any | None) -> dict[str, str]:
        env = {key: value for key, value in os.environ.items() if key.upper() in SAFE_ENV_KEYS}
        if extra_env is None:
            return env
        if not isinstance(extra_env, dict):
            raise SandboxBackendError("input.env must be a dictionary when provided.")
        for key, value in extra_env.items():
            env[str(key)] = str(value)
        return env

    def _truncate(self, value: Any) -> str:
        text = "" if value is None else str(value)
        if len(text) <= self.max_output_chars:
            return text
        return text[: self.max_output_chars] + "\n[truncated]"

    def provision(self, *, sandbox_ref: str, resources: dict[str, Any] | None = None) -> dict[str, Any]:
        resources = resources or {}
        workspace_path = self._workspace_path(sandbox_ref)
        if workspace_path.exists():
            shutil.rmtree(workspace_path)
        workspace_path.mkdir(parents=True, exist_ok=True)
        copied_paths = self._copy_requested_paths(workspace_path, resources)
        timeout_seconds = self._timeout(resources.get("timeout_seconds"))
        self._states[sandbox_ref] = LocalSandboxState(
            sandbox_ref=sandbox_ref,
            workspace_path=workspace_path,
            timeout_seconds=timeout_seconds,
        )
        return {
            "backend": "local-process",
            "status": "provisioned",
            "workspace_path": str(workspace_path),
            "copied_paths": copied_paths,
            "timeout_seconds": timeout_seconds,
            "credentials_visible": False,
        }

    def execute(
        self,
        *,
        sandbox_ref: str,
        command: str,
        input_payload: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        if not command.strip():
            raise SandboxBackendError("Sandbox command must not be empty.")
        input_payload = input_payload or {}
        state = self._state_for_execute(sandbox_ref)
        cwd = self._safe_workspace_path(state, input_payload.get("cwd"))
        timeout_seconds = self._timeout(input_payload.get("timeout_seconds", state.timeout_seconds))
        try:
            completed = subprocess.run(
                command,
                cwd=cwd,
                env=self._clean_env(input_payload.get("env")),
                shell=True,
                text=True,
                capture_output=True,
                timeout=timeout_seconds,
                check=False,
            )
        except subprocess.TimeoutExpired as exc:
            raise SandboxBackendError(f"Sandbox command timed out after {timeout_seconds:g} seconds.") from exc
        return {
            "backend": "local-process",
            "status": "completed" if completed.returncode == 0 else "failed",
            "sandbox_ref": sandbox_ref,
            "command": command,
            "cwd": str(cwd),
            "workspace_path": str(state.workspace_path),
            "returncode": completed.returncode,
            "stdout": self._truncate(completed.stdout),
            "stderr": self._truncate(completed.stderr),
            "timed_out": False,
        }

    def dispose(self, *, sandbox_ref: str) -> dict[str, Any]:
        state = self._states.pop(sandbox_ref, None)
        workspace_path = state.workspace_path if state else self._workspace_path(sandbox_ref)
        removed = False
        if workspace_path.exists() and not self.keep_workspaces:
            shutil.rmtree(workspace_path)
            removed = True
        return {
            "backend": "local-process",
            "status": "disposed",
            "sandbox_ref": sandbox_ref,
            "workspace_path": str(workspace_path),
            "workspace_removed": removed,
        }
