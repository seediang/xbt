"""Plugin execution context provided to all hooks."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional


@dataclass
class XbtContext:
    """Structured execution context passed to all plugin hooks.

    This provides pre-extracted and validated information to reduce boilerplate
    in plugin implementations. Instead of parsing args or searching for project
    directories, plugins receive all commonly needed information in a single
    context object.

    Attributes:
        args: Raw CLI arguments passed to xbt/dbt.
        command: Extracted dbt command (e.g., "run", "test", "compile", "plugin").
            None if no command was found.
        project_dir: Resolved and validated dbt project directory.
            Will be None if dbt_project.yml was not found.
        workspace_root: Workspace/repository root directory.
            Detected by searching for .git, pyproject.toml, or dbt_project.yml.
        plugin_name: Plugin namespace/identifier (e.g., "builtin_plugin_command").
        result: Hook result object (only populated for post-invoke hooks).
            For post-invoke, contains the dbt execution result.
    """

    args: list[str]
    command: Optional[str]
    project_dir: Optional[Path]
    workspace_root: Path
    plugin_name: str
    result: Any = None

    @property
    def is_plugin_management_command(self) -> bool:
        """Return True if this is an xbt plugin/plugins command.

        Plugin management commands are handled specially and most plugins
        should not perform their normal operations for these commands.

        Returns:
            True if command is "plugin" or "plugins".
        """
        return self.command in {"plugin", "plugins"}

    @property
    def has_project(self) -> bool:
        """Return True if a valid dbt project directory was found.

        Useful for plugins that need to operate on a dbt project.

        Returns:
            True if project_dir is not None and the directory exists.
        """
        return self.project_dir is not None and self.project_dir.exists()


__all__ = ["XbtContext"]
