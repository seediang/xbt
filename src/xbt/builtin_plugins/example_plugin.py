"""
Example built-in plugin for xbt.

This plugin demonstrates all four hook types and serves as a reference
for plugin developers. It adds minimal functionality but shows the structure.

To disable this example plugin in production, delete this file or
rename it to something that doesn't match *.py in the builtin_plugins/ directory.
"""

import logging

import pluggy

__version__ = "0.1.0"

logger = logging.getLogger(__name__)

hookimpl = pluggy.HookimplMarker("xbt")


@hookimpl
def xbt_register_commands(cli_group):
    """Example: Add a custom command to xbt CLI."""
    # Uncomment to add example command:
    # @cli_group.command()
    # def example():
    #     \"\"\"Example custom xbt command.\"\"\"
    #     print("This is an example command from the example_plugin")

    logger.debug("example_plugin: xbt_register_commands called")


@hookimpl
def xbt_register_callbacks():
    """Example: Register callbacks to receive dbt events."""

    def example_callback(event):
        """
        Example callback that receives all EventMsg objects from dbt.

        To use this, uncomment the return statement and this callback
        will receive every event dbt emits.
        """
        # logger.debug(f"Event from dbt: {event.info.name}")
        pass

    logger.debug("example_plugin: xbt_register_callbacks called")
    # Uncomment to register the callback:
    # return [example_callback]
    return None


@hookimpl
def xbt_pre_invoke(args):
    """Example: Modify command-line arguments before dbt processes them."""
    logger.debug(f"example_plugin: xbt_pre_invoke called with args: {args}")
    # Example: you could inject a default flag here
    # if "--verbose" not in args:
    #     args = args + ["--verbose"]
    # logger.info("example_plugin: injected --verbose flag")
    return None  # Return None to keep args unchanged


@hookimpl
def xbt_post_invoke(args, result):
    """Example: React to dbt invocation results."""
    success = getattr(result, "success", False)
    logger.info(
        f"example_plugin: xbt_post_invoke called ({args}). Result success: {success}"
    )
