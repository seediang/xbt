"""Hook filtering and execution control.

Provides declarative command filtering for hooks so plugins can specify
which dbt commands should trigger their hooks without manual branching.
"""

from __future__ import annotations

from typing import Optional, Set


class HookFilter:
    """Determines if a hook should execute based on dbt command.

    Supports both positive filtering (run only for specific commands) and
    negative filtering (skip specific commands). If skip_for_commands takes
    precedence if both are specified.

    Attributes:
        run_for_commands: Only execute hook for these commands (or None for all).
        skip_for_commands: Skip execution for these commands (or None for none).
    """

    def __init__(
        self,
        run_for_commands: Optional[Set[str]] = None,
        skip_for_commands: Optional[Set[str]] = None,
    ):
        """Initialize hook filter.

        Args:
            run_for_commands: Set of commands to run for. If None, runs for all
                commands (unless skip_for_commands filters them out).
            skip_for_commands: Set of commands to skip. Takes precedence over
                run_for_commands.
        """
        self.run_for_commands = run_for_commands
        self.skip_for_commands = skip_for_commands

    def should_execute(self, command: Optional[str]) -> bool:
        """Determine if hook should execute for this command.

        Decision logic:
        1. If command is in skip_for_commands, return False
        2. If run_for_commands is specified (even if empty), return whether command is in it
        3. Otherwise, return True (no filters, always run)

        Args:
            command: The dbt command being executed. Can be None if no command found.

        Returns:
            True if hook should execute, False otherwise.

        Examples:
            >>> # Only run for specific commands
            >>> f = HookFilter(run_for_commands={'run', 'test'})
            >>> f.should_execute('run')
            True
            >>> f.should_execute('compile')
            False
            >>> # Skip specific commands
            >>> f = HookFilter(skip_for_commands={'plugin'})
            >>> f.should_execute('run')
            True
            >>> f.should_execute('plugin')
            False
            >>> # Combined (skip takes precedence)
            >>> f = HookFilter(run_for_commands={'run', 'test'}, skip_for_commands={'test'})
            >>> f.should_execute('test')
            False
            >>> f.should_execute('run')
            True
        """
        # Normalize command to lowercase for comparison
        normalized_command = command.lower() if command else None

        # Skip if in skip list (takes precedence)
        if self.skip_for_commands:
            skip_set = {c.lower() for c in self.skip_for_commands}
            if normalized_command in skip_set:
                return False

        # Only run if in run list (if run_for_commands is not None)
        # None means no run filter (use other filters instead)
        # Empty set means don't run anything
        if self.run_for_commands is not None:
            run_set = {c.lower() for c in self.run_for_commands}
            return normalized_command in run_set

        # No run_for filter, check if skip filter exists
        # If no filters at all, always run
        if not self.skip_for_commands:
            return True
        # Skip filter exists and already returned False if matched, so True
        return True


__all__ = ["HookFilter"]
