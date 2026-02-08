"""Hook specifications for xbt plugin system."""

from typing import Any, Callable, List, Optional

import pluggy

hookspec = pluggy.HookspecMarker("xbt")


@hookspec
def xbt_register_commands(cli_group: Any) -> None:
    """
    Register custom commands and options with the Click CLI group.

    This hook is called once during xbtRunner initialization, before dbt
    processes command-line arguments. Use it to add custom xbt commands or
    modify the CLI interface.

    Args:
        cli_group: The Click Group object for the xbt CLI.

    Example:
        @hookimpl
        def xbt_register_commands(cli_group):
            @cli_group.command()
            def custom_cmd():
                print("Custom command!")
    """


@hookspec
def xbt_register_callbacks() -> Optional[List[Callable[[Any], None]]]:
    """
    Register callbacks to receive dbt events.

    This hook should return a list of callback functions that will be
    invoked on every EventMsg from dbt. Callbacks are called in real-time
    as dbt executes.

    Returns:
        Optional[List[Callable[[EventMsg], None]]]: List of callback functions.
            Each callback accepts a single EventMsg argument.

    Example:
        @hookimpl
        def xbt_register_callbacks():
            def my_callback(event):
                print(f"Event: {event.info.name}")
            return [my_callback]
    """


@hookspec
def xbt_pre_invoke(args: List[str]) -> Optional[List[str]]:
    """
    Modify command-line arguments before dbt processing.

    This hook is called in invoke() before arguments are passed to dbt.
    Plugins can transform, validate, or inject arguments. All plugins'
    modifications are chained sequentially.

    Args:
        args: List of command-line arguments.

    Returns:
        Optional[List[str]]: Modified arguments. If None, args are unchanged.

    Example:
        @hookimpl
        def xbt_pre_invoke(args):
            # Inject a default profile if not specified
            if "--profile" not in args:
                args = ["--profile", "dev"] + args
            return args
    """


@hookspec
def xbt_post_invoke(args: List[str], result: Any) -> None:
    """
    React to dbt invocation results.

    This hook is called after dbt completes execution. Use it for
    post-processing, custom reporting, error handling, or cleanup.

    Args:
        args: The command-line arguments that were passed to dbt.
        result: The xbtRunnerResult object from dbt invocation.
            Has attributes: success (bool), exception (Optional[Exception])

    Example:
        @hookimpl
        def xbt_post_invoke(args, result):
            if result.success:
                print("✓ Command completed successfully")
            elif result.exception:
                print(f"✗ Error: {result.exception}")
    """
