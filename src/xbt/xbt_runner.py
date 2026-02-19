import logging
from pathlib import Path
from typing import Any, Callable, List, Optional, TypeAlias

from dbt.cli.main import cli, dbtRunner, dbtRunnerResult
from dbt.contracts.graph.manifest import Manifest
from dbt_common.events.base_types import EventMsg

from xbt.plugins import InitContext, PostInvokeContext, PreInvokeContext
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

        # Initialize command tracking before any context building
        self.registered_dbt_commands: set[str] = set(cli.commands.keys())
        self.registered_plugin_commands: set[str] = set()
        self.registered_builtin_commands: set[str] = set()

        # Initialize plugin manager and call registration hooks
        self.plugin_manager = XbtPluginManager.get_instance()

        # Build context for initialization hooks
        init_context = self._build_init_context()

        # Allow plugins to register new commands and options
        self.registered_builtin_commands = (
            self.plugin_manager.hook_register_commands_with_tracking(
                cli_group=cli, context=init_context
            )
        )

        # Track which commands were added by plugins
        self.registered_plugin_commands: set[str] = (
            set(cli.commands.keys()) - self.registered_dbt_commands
        )

        # Allow plugins to register callbacks, merge with provided callbacks
        callbacks.extend(
            self.plugin_manager.hook_register_callbacks(context=init_context)
        )

        # Pass None if callbacks is empty (preserve original behavior)
        super().__init__(manifest=manifest, callbacks=callbacks if callbacks else None)

    def _base_context_kwargs(self) -> dict[str, Any]:
        """Build shared context fields used by all hook contexts.

        Args:
            command: The dbt command being executed (can be None).
            args: Raw CLI arguments.

        Returns:
            Dict of shared context fields.
        """
        project_dir = find_dbt_project_dir()
        workspace_root = find_workspace_root(project_dir or Path.cwd())
        return {
            "project_dir": project_dir,
            "workspace_root": workspace_root,
            "registered_dbt_commands": self.registered_dbt_commands,
            "registered_plugin_commands": self.registered_plugin_commands,
            "registered_builtin_commands": self.registered_builtin_commands,
        }

    def _build_init_context(self) -> InitContext:
        """Build InitContext with pre-extracted project info."""
        return InitContext(**self._base_context_kwargs())

    def _build_pre_invoke_context(
        self, command: Optional[str], args: List[str]
    ) -> PreInvokeContext:
        """Build PreInvokeContext with command and args."""
        return PreInvokeContext(
            args=args.copy() if args else [],
            command=command,
            **self._base_context_kwargs(),
        )

    def _build_post_invoke_context(
        self, command: Optional[str], args: List[str], result: Any
    ) -> PostInvokeContext:
        """Build PostInvokeContext with result information."""
        return PostInvokeContext(
            args=args.copy() if args else [],
            command=command,
            result=result,
            **self._base_context_kwargs(),
        )

    def invoke(self, args: List[str], **kwargs) -> xbtRunnerResult:
        logging.info("Invoking xbtRunner with args: %s", args)

        # Extract command from args for context
        command = get_dbt_command(args)
        context = self._build_pre_invoke_context(command=command, args=args)

        # Allow plugins to modify args before invocation
        args = self.plugin_manager.hook_pre_invoke(args=args, context=context)

        result = super().invoke(args, **kwargs)

        post_context = self._build_post_invoke_context(
            command=context.command, args=context.args, result=result
        )

        # Allow plugins to react to invocation result
        self.plugin_manager.hook_post_invoke(
            args=args, result=result, context=post_context
        )

        logging.info("xbtRunner invocation completed with result: %s", result)
        return result
