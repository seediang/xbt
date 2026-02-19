"""Utilities for plugin development.

Common functionality extracted from repeated patterns across plugins:
- Extracting dbt commands from arguments
- Finding dbt project and workspace directories
- Status message formatting
- Logging/printing integration
"""

from __future__ import annotations

import logging
import time
from pathlib import Path
from typing import Optional, Sequence, Set


def get_dbt_command(args: Sequence[str]) -> Optional[str]:
    """Extract dbt command from CLI arguments.

    Returns the first positional argument (non-flag), which is typically
    the dbt command like 'run', 'test', 'compile', etc. This handles:
    - Simple commands: ['run'] -> 'run'
    - Commands with options: ['test', '--select', 'model1'] -> 'test'
    - Flags before command: ['-d', 'run'] -> 'run'
    - Project dir specified: ['--project-dir', '.', 'run'] -> 'run'

    Args:
        args: CLI arguments to parse.

    Returns:
        Command name or None if no command found.

    Examples:
        >>> get_dbt_command(['run'])
        'run'
        >>> get_dbt_command(['test', '--select', 'model1'])
        'test'
        >>> get_dbt_command(['-d', 'run'])
        'run'
        >>> get_dbt_command([])
        None
        >>> get_dbt_command(['--project-dir', '.'])
        None
    """
    if not args:
        return None

    # Flags that take a value (the next argument is their value, not a command)
    # These are long-form dbt flags that require arguments
    flags_with_values = {
        "--project-dir",
        "--profiles-dir",
        "--profile",
        "--select",
        "--exclude",
        "--models",
        "--selector",
        "--threads",
        "--target",
        "--vars",
        "--state",
        "--artifact-state",
        "--partial-parse-state",
    }

    i = 0
    while i < len(args):
        arg = args[i]

        # Skip flags and their arguments
        if arg.startswith("-"):
            # Check if this flag takes a value
            if arg in flags_with_values and i + 1 < len(args):
                # Skip both the flag and its value
                i += 2
            else:
                # Skip just the flag
                i += 1
        else:
            # Found a non-flag argument, this should be the command
            return arg

    return None


def is_command_in_set(command: Optional[str], commands: Set[str]) -> bool:
    """Check if command is in the given set (case-insensitive).

    Args:
        command: Command name to check (can be None).
        commands: Set of valid command names.

    Returns:
        True if command is in set (case-insensitive), False otherwise.

    Examples:
        >>> is_command_in_set('run', {'run', 'test'})
        True
        >>> is_command_in_set('RUN', {'run', 'test'})
        True
        >>> is_command_in_set('build', {'run', 'test'})
        False
        >>> is_command_in_set(None, {'run', 'test'})
        False
    """
    if not command:
        return False
    return command.lower() in {c.lower() for c in commands}


def find_dbt_project_dir(start_dir: Optional[Path] = None) -> Optional[Path]:
    """Find dbt project directory by searching for dbt_project.yml.

    Searches up from start_dir (or current working directory) until
    dbt_project.yml is found. Stops at filesystem root.

    Args:
        start_dir: Directory to start search from. Defaults to cwd.

    Returns:
        Path to directory containing dbt_project.yml, or None if not found.

    Examples:
        >>> # If /path/to/project/dbt_project.yml exists:
        >>> find_dbt_project_dir(Path('/path/to/project/models'))
        Path('/path/to/project')
        >>> # If no dbt_project.yml found:
        >>> find_dbt_project_dir(Path('/tmp/nonexistent'))
        None
    """
    current = (start_dir or Path.cwd()).resolve()

    # Check current and parent directories up to filesystem root
    while True:
        if (current / "dbt_project.yml").exists():
            return current

        parent = current.parent
        if parent == current:  # Reached filesystem root
            break

        current = parent

    return None


def find_workspace_root(
    start_dir: Path,
    markers: Optional[list[str]] = None,
    max_depth: int = 10,
) -> Path:
    """Find workspace/repository root by searching for marker files.

    Searches up from start_dir for marker files/directories. Default markers
    are .git, pyproject.toml, and dbt_project.yml. Stops at filesystem root
    or after max_depth levels.

    Args:
        start_dir: Directory to start search from.
        markers: List of marker file/directory names. Defaults to
            [".git", "pyproject.toml", "dbt_project.yml"].
        max_depth: Maximum parent directories to traverse.

    Returns:
        Path to workspace root, or start_dir if not found.

    Examples:
        >>> # If /workspace/.git exists:
        >>> find_workspace_root(Path('/workspace/src/xbt'))
        Path('/workspace')
        >>> # If no markers found:
        >>> find_workspace_root(Path('/tmp/nonexistent'))
        Path('/tmp/nonexistent')
    """
    if markers is None:
        markers = [".git", "pyproject.toml", "dbt_project.yml"]

    current = start_dir.resolve()

    for _ in range(max_depth):
        if any((current / marker).exists() for marker in markers):
            return current

        parent = current.parent
        if parent == current:  # Reached filesystem root
            break

        current = parent

    return start_dir


def emit_status(
    logger: logging.Logger,
    message: str,
    level: int = logging.INFO,
) -> None:
    """Log and print a status message.

    Emits a message to both the logger and stdout. Useful for user-facing
    status updates that should appear in both logs and console output.

    Args:
        logger: Logger instance to emit to.
        message: Message text.
        level: Logging level (default: INFO).
    """
    logger.log(level, message)
    print(message)


def format_status_message(prefix: str, message: str) -> str:
    """Format a status message with timestamp and prefix.

    Creates a formatted message suitable for status updates.
    Format: "HH:MM:SS  prefix: message"

    Args:
        prefix: Plugin name or prefix for the message.
        message: Message content.

    Returns:
        Formatted message string.

    Examples:
        >>> msg = format_status_message("my-plugin", "processing started")
        >>> # Might return: "14:23:45  my-plugin: processing started"
    """
    timestamp = time.strftime("%H:%M:%S")
    return f"{timestamp}  {prefix}: {message}"


__all__ = [
    "get_dbt_command",
    "is_command_in_set",
    "find_dbt_project_dir",
    "find_workspace_root",
    "emit_status",
    "format_status_message",
]
