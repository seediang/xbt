"""Plugin execution contexts provided to hooks."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional


@dataclass
class BaseContext:
    """Shared fields for hook-specific contexts."""

    project_dir: Optional[Path]
    workspace_root: Path
    registered_dbt_commands: set[str]
    registered_plugin_commands: set[str]
    registered_builtin_commands: set[str]

    @property
    def has_project(self) -> bool:
        """Return True if a valid dbt project directory was found.

        Useful for plugins that need to operate on a dbt project.

        Returns:
            True if project_dir is not None and the directory exists.
        """
        return self.project_dir is not None and self.project_dir.exists()


@dataclass
class CommandContext(BaseContext):
    """Context for hooks that run with command and args."""

    args: list[str]
    command: Optional[str]

    @property
    def is_builtin_command(self) -> bool:
        """Return True if this is an xbt built-in command.

        Returns:
            True if command is registered by built-in plugins.
        """
        if self.command is None:
            return False
        return self.command in self.registered_builtin_commands

    @property
    def is_dbt_command(self) -> bool:
        """Return True if this is a standard dbt command.

        Checks against the dynamically registered dbt commands.

        Returns:
            True if command is a known dbt command. False for plugin or xbt
            custom commands.
        """
        if self.command is None:
            return False
        return self.command in self.registered_dbt_commands

    @property
    def is_xbt_command(self) -> bool:
        """Return True if this is an xbt or plugin-added command.

        These are commands that are not standard dbt commands and not plugin
        management commands. They include built-in xbt commands and commands
        added by plugins.

        Returns:
            True if command is in registered_plugin_commands.
        """
        if self.command is None:
            return False
        return self.command in self.registered_plugin_commands


@dataclass
class InitContext(BaseContext):
    """Context passed to register hooks during initialization."""


@dataclass
class PreInvokeContext(CommandContext):
    """Context passed to pre-invoke hooks."""


@dataclass
class PostInvokeContext(CommandContext):
    """Context passed to post-invoke hooks."""

    result: Any


__all__ = [
    "BaseContext",
    "CommandContext",
    "InitContext",
    "PreInvokeContext",
    "PostInvokeContext",
]
