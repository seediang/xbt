"""xbt plugin development utilities and interfaces.

This package provides the public API for developing xbt plugins:

- XbtContext: Structured context passed to all hooks (extracted dbt command,
  project directory, etc.)
- hookimpl: Enhanced hook implementation marker with command filtering support
- PluginConfig: Base class for plugin configuration with YAML loading
- Various utilities: get_dbt_command, find_workspace_root, format_status_message, etc.

Example usage:

    from xbt.plugins import XbtContext, hookimpl, PluginConfig

    @hookimpl(run_for_commands={"run", "test", "build"})
    def xbt_post_invoke(context: XbtContext) -> None:
        if not context.has_project:
            return
        # Do work with context.command, context.project_dir, etc.

    class MyPluginConfig(PluginConfig):
        config_file = "~/.xbt/my_plugin.yml"
        backend: str = "local"

        def validate(self) -> None:
            if self.backend not in {"local", "s3"}:
                raise ValueError(f"Invalid backend: {self.backend}")
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Callable, Optional, Set

import pluggy

from xbt.plugins.config import PluginConfig
from xbt.plugins.context import XbtContext
from xbt.plugins.filter import HookFilter
from xbt.plugins.utils import (
    emit_status,
    find_dbt_project_dir,
    find_workspace_root,
    format_status_message,
    get_dbt_command,
    is_command_in_set,
)

if TYPE_CHECKING:
    pass


def hookimpl(
    tryfirst: bool = False,
    trylast: bool = False,
    optionalhook: bool = False,
    run_for_commands: Optional[Set[str]] = None,
    skip_for_commands: Optional[Set[str]] = None,
) -> Callable:
    """Enhanced hook implementation marker with command filtering.

    Wraps pluggy.HookimplMarker to add declarative command filtering. Plugins
    can specify which dbt commands should trigger their hooks without manual
    branching in the hook implementation.

    Args:
        tryfirst: Hook runs before others of this name.
        trylast: Hook runs after others of this name.
        optionalhook: Hook is optional (doesn't error if hookspec missing).
        run_for_commands: Only execute for these dbt commands.
            If specified, hook only runs for matching commands.
            If None, runs for all commands (unless skip_for_commands filters).
        skip_for_commands: Skip execution for these dbt commands.
            Takes precedence over run_for_commands if both specified.

    Returns:
        Decorator function for hook implementations.

    Examples:
        >>> @hookimpl(run_for_commands={"run", "test", "build"})
        ... def xbt_post_invoke(context: XbtContext) -> None:
        ...     # Only called for run, test, build
        ...     pass

        >>> @hookimpl(skip_for_commands={"plugin", "plugins"})
        ... def xbt_pre_invoke(context: XbtContext) -> Optional[list]:
        ...     # Called for all except plugin/plugins commands
        ...     return None

        >>> @hookimpl(tryfirst=True)
        ... def xbt_register_commands(context: XbtContext) -> None:
        ...     # Regular behavior, runs first
        ...     pass
    """
    # Create the base pluggy hook implementation marker
    base_impl = pluggy.HookimplMarker("xbt")(
        tryfirst=tryfirst,
        trylast=trylast,
        optionalhook=optionalhook,
    )

    def decorator(func: Callable) -> Callable:
        # Apply pluggy marker
        func = base_impl(func)

        # Attach filter metadata if any command filtering specified
        if run_for_commands or skip_for_commands:
            hook_filter = HookFilter(
                run_for_commands=run_for_commands,
                skip_for_commands=skip_for_commands,
            )
            func._xbt_hook_filter = hook_filter  # type: ignore

        return func

    return decorator


__all__ = [
    # Main classes
    "XbtContext",
    "PluginConfig",
    "hookimpl",
    # Utilities
    "get_dbt_command",
    "is_command_in_set",
    "find_dbt_project_dir",
    "find_workspace_root",
    "emit_status",
    "format_status_message",
]
