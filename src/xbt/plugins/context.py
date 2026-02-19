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
    def is_plugin_command(self) -> bool:
        """Return True if this is a plugin management command ("plugin"/"plugins").

        Returns:
            True if command is "plugin" or "plugins".
        """
        return self.command in {"plugin", "plugins"}

    @property
    def is_dbt_command(self) -> bool:
        """Return True if this is a standard dbt command.

        Standard dbt commands include: run, test, compile, parse, snapshot,
        seed, freshness, deps, docs, debug, build, list, retry, source,
        exposure, metric, and other core dbt functionality.

        Returns:
            True if command is a known dbt command. False for plugin or xbt
            custom commands.
        """
        if self.command is None:
            return False

        dbt_commands = {
            "build",
            "compile",
            "debug",
            "deps",
            "docs",
            "exposure",
            "freshness",
            "list",
            "metric",
            "parse",
            "retry",
            "run",
            "seed",
            "snapshot",
            "source",
            "test",
        }
        return self.command in dbt_commands

    @property
    def is_xbt_command(self) -> bool:
        """Return True if this is an xbt or plugin-added command.

        These are commands that are not standard dbt commands and not plugin
        management commands. They are either built-in xbt commands or commands
        added by plugins.

        Returns:
            True if command is not a dbt command and not a plugin command.
        """
        return (
            self.command is not None
            and not self.is_dbt_command
            and not self.is_plugin_command
        )

    @property
    def has_project(self) -> bool:
        """Return True if a valid dbt project directory was found.

        Useful for plugins that need to operate on a dbt project.

        Returns:
            True if project_dir is not None and the directory exists.
        """
        return self.project_dir is not None and self.project_dir.exists()


__all__ = ["XbtContext"]
