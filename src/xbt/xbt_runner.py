import logging
from pathlib import Path
from typing import Callable, List, Optional, TypeAlias

from dbt.cli.main import cli, dbtRunner, dbtRunnerResult
from dbt.contracts.graph.manifest import Manifest
from dbt_common.events.base_types import EventMsg

from xbt.plugins import XbtContext
from xbt.plugins.utils import find_dbt_project_dir, find_workspace_root, get_dbt_command

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

        # Build context for initialization hooks (args will be empty at this stage)
        init_context = self._build_context(command=None, args=[])

        # Allow plugins to register new commands and options
        self.plugin_manager.hook_register_commands(cli_group=cli, context=init_context)

        # Allow plugins to register callbacks, merge with provided callbacks
        callbacks.extend(
            self.plugin_manager.hook_register_callbacks(context=init_context)
        )

        # Pass None if callbacks is empty (preserve original behavior)
        super().__init__(manifest=manifest, callbacks=callbacks if callbacks else None)

    def _build_context(self, command: Optional[str], args: List[str]) -> XbtContext:
        """Build XbtContext with pre-extracted command and project info.

        Args:
            command: The dbt command being executed (can be None).
            args: Raw CLI arguments.

        Returns:
            XbtContext with all plugins' commonly needed information.
        """
        project_dir = find_dbt_project_dir()
        workspace_root = find_workspace_root(project_dir or Path.cwd())

        return XbtContext(
            args=args.copy() if args else [],
            command=command,
            project_dir=project_dir,
            workspace_root=workspace_root,
            plugin_name="xbt_runner",  # Internal runner context
            result=None,
        )

    def invoke(self, args: List[str], **kwargs) -> xbtRunnerResult:
        logging.info("Invoking xbtRunner with args: %s", args)

        # Extract command from args for context
        command = get_dbt_command(args)
        context = self._build_context(command=command, args=args)

        # Allow plugins to modify args before invocation
        args = self.plugin_manager.hook_pre_invoke(args=args, context=context)

        result = super().invoke(args, **kwargs)

        # Update context with result for post-invoke hooks
        context.result = result

        # Allow plugins to react to invocation result
        self.plugin_manager.hook_post_invoke(args=args, result=result, context=context)

        logging.info("xbtRunner invocation completed with result: %s", result)
        return result
