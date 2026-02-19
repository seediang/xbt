"""Hook specifications for xbt plugin system."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Callable, List, Optional

import pluggy

if TYPE_CHECKING:
    from xbt.plugins import (
        InitContext,
        PluginConfig,
        PostInvokeContext,
        PreInvokeContext,
    )

hookspec = pluggy.HookspecMarker("xbt")


@hookspec
def xbt_register_commands(
    cli_group: Any, context: Optional[InitContext] = None
) -> None:
    """
    Register custom commands and options with the Click CLI group.

    This hook is called once during xbtRunner initialization, before dbt
    processes command-line arguments. Use it to add custom xbt commands or
    modify the CLI interface.

    Args:
        cli_group: The Click Group object for the xbt CLI.
        context: InitContext with execution information (new in v0.2).

    Example:
        from xbt.plugins import hookimpl

        @hookimpl
        def xbt_register_commands(cli_group, context=None):
            @cli_group.command()
            def custom_cmd():
                print("Custom command!")
    """


@hookspec
def xbt_register_callbacks(
    context: Optional[InitContext] = None,
) -> Optional[List[Callable[[Any], None]]]:
    """
    Register callbacks to receive dbt events.

    This hook should return a list of callback functions that will be
    invoked on every EventMsg from dbt. Callbacks are called in real-time
    as dbt executes.

    Args:
        context: InitContext with execution information (new in v0.2).

    Returns:
        Optional[List[Callable[[EventMsg], None]]]: List of callback functions.
            Each callback accepts a single EventMsg argument.

    Example:
        from xbt.plugins import hookimpl

        @hookimpl
        def xbt_register_callbacks(context=None):
            def my_callback(event):
                print(f"Event: {event.info.name}")
            return [my_callback]
    """


@hookspec
def xbt_pre_invoke(
    args: List[str], context: Optional[PreInvokeContext] = None
) -> Optional[List[str]]:
    """
    Modify command-line arguments before dbt processing.

    This hook is called in invoke() before arguments are passed to dbt.
    Plugins can transform, validate, or inject arguments. All plugins'
    modifications are chained sequentially.

    Args:
        args: List of command-line arguments.
        context: PreInvokeContext with execution information (new in v0.2).
            Provides extracted command, resolved project directory, etc.
            Plugins should use context for command filtering and directory info.

    Returns:
        Optional[List[str]]: Modified arguments. If None, args are unchanged.

    Example:
        from xbt.plugins import PreInvokeContext, hookimpl

        @hookimpl(run_for_commands={"run", "test", "build"})
        def xbt_pre_invoke(args, context: PreInvokeContext | None = None):
            if not context or not context.has_project:
                return None
            # Inject a custom flag for dbt runs
            return args + ["--modified"]
    """


@hookspec
def xbt_post_invoke(
    args: List[str], result: Any, context: Optional[PostInvokeContext] = None
) -> None:
    """
    React to dbt invocation results.

    This hook is called after dbt completes execution. Use it for
    post-processing, custom reporting, error handling, or cleanup.

    Args:
        args: The command-line arguments that were passed to dbt.
        result: The xbtRunnerResult object from dbt invocation.
            Has attributes: success (bool), exception (Optional[Exception])
        context: PostInvokeContext with execution information (new in v0.2).
            Provides extracted command, project directory, result status, etc.
            Plugins should prefer using context over parsing args directly.

    Example:
        from xbt.plugins import PostInvokeContext, hookimpl

        @hookimpl(run_for_commands={"run", "test"})
        def xbt_post_invoke(args, result, context: PostInvokeContext | None = None):
            if not context:
                return
            if context.result.success:
                print(f"✓ {context.command} completed successfully")
            else:
                print(f"✗ {context.command} failed")
    """


@hookspec
def xbt_init() -> Optional[PluginConfig]:
    """
    Initialize plugin configuration.

    This hook is called during plugin manager initialization. Plugins can
    return their configuration object, which xbt will load and validate.
    Configuration files are typically loaded from a plugin-specific path
    (e.g., ~/.xbt/my_plugin.yml).

    Returns:
        Optional[PluginConfig]: Plugin configuration instance, or None if
            the plugin doesn't require configuration.

    Example:
        from xbt.plugins import hookimpl, PluginConfig

        class MyPluginConfig(PluginConfig):
            config_file = "~/.xbt/my_plugin.yml"
            backend: str = "local"
            max_retries: int = 3

            def validate(self) -> None:
                if self.backend not in {"local", "s3", "gcs"}:
                    raise ValueError(f"Invalid backend: {self.backend}")

        @hookimpl
        def xbt_init():
            return MyPluginConfig.from_default()
    """
