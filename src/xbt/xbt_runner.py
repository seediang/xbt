import logging
from typing import Callable, List, Optional, TypeAlias

from dbt.cli.main import cli, dbtRunner, dbtRunnerResult
from dbt.contracts.graph.manifest import Manifest
from dbt_common.events.base_types import EventMsg

from .plugin_manager import XbtPluginManager

xbtRunnerResult: TypeAlias = dbtRunnerResult


class xbtRunner(dbtRunner):
    def __init__(
        self,
        manifest: Optional[Manifest] = None,
        callbacks: Optional[List[Callable[[EventMsg], None]]] = None,
    ):
        # add default parameters
        if callbacks is None:
            callbacks = []

        cli.name = "xbt"  # Override the CLI name for help messages

        logging.info("xbtRunner initialized.")

        # Initialize plugin manager and call registration hooks
        self.plugin_manager = XbtPluginManager.get_instance()

        # Allow plugins to register new commands and options
        self.plugin_manager.hook_register_commands(cli_group=cli)

        # Allow plugins to register callbacks, merge with provided callbacks
        callbacks.extend(self.plugin_manager.hook_register_callbacks())

        # Pass None if callbacks is empty (preserve original behavior)
        super().__init__(manifest=manifest, callbacks=callbacks if callbacks else None)

    def invoke(self, args: List[str], **kwargs) -> xbtRunnerResult:
        logging.info("Invoking xbtRunner with args: %s", args)

        # Allow plugins to modify args before invocation
        args = self.plugin_manager.hook_pre_invoke(args=args)

        result = super().invoke(args, **kwargs)

        # Allow plugins to react to invocation result
        self.plugin_manager.hook_post_invoke(args=args, result=result)

        logging.info("xbtRunner invocation completed with result: %s", result)
        return result
