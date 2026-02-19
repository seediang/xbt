# Plugin Development Guide

This guide covers how to develop plugins for xbt using the v0.2+ plugin system.

## Quick Start

### Create a Simple Plugin

```python
from xbt.plugins import hookimpl, XbtContext

@hookimpl(run_for_commands={"run", "test", "build"})
def xbt_post_invoke(context: XbtContext) -> None:
    """React to dbt run/test/build results."""
    if context.result.success:
        print(f"✓ {context.command} succeeded!")
    else:
        print(f"✗ {context.command} failed")

@hookimpl
def xbt_pre_invoke(context: XbtContext) -> list[str] | None:
    """Inject flags for dbt runs."""
    if context.command in {"run", "test"} and context.has_project:
        if "--profile" not in context.args:
            return ["--profile", "dev"] + context.args
    return None  # Keep original args
```

Register in `pyproject.toml`:

```toml
[project.entry-points.xbt]
my_plugin = "my_xbt_plugin.plugin"
```

That's it! Your plugin is auto-discovered and ready to use.

## XbtContext Reference

The `XbtContext` object passed to hooks provides:

| Attribute | Type | Description |
|-----------|------|-------------|
| `command` | `Optional[str]` | Extracted dbt command (e.g., "run", "test") |
| `args` | `list[str]` | Original CLI arguments |
| `project_dir` | `Optional[Path]` | Resolved dbt project directory (if found) |
| `workspace_root` | `Path` | Repository/workspace root directory |
| `plugin_name` | `str` | Name of the current plugin |
| `result` | `Optional[Any]` | dbt execution result (post-invoke hooks only) |
| `is_plugin_management_command` | `bool` (property) | True if "plugin" or "plugins" command |
| `has_project` | `bool` (property) | True if valid project directory exists |

## Hook Reference

### `xbt_register_commands(cli_group, context=None)`

Called during xbtRunner initialization. Use to add custom CLI commands.

```python
from xbt.plugins import hookimpl
import click

@hookimpl
def xbt_register_commands(cli_group, context=None):
    @cli_group.command()
    def my_command():
        """Custom xbt command."""
        click.echo("Hello from xbt!")
```

### `xbt_register_callbacks(context=None)`

Returns list of callbacks to receive dbt events in real-time.

```python
from xbt.plugins import hookimpl

@hookimpl
def xbt_register_callbacks(context=None):
    def my_callback(event):
        print(f"Event: {event.info.name}")
    return [my_callback]
```

### `xbt_pre_invoke(context: XbtContext) -> Optional[List[str]]`

Modify command-line arguments before dbt execution. Use `@hookimpl` parameters for command filtering:

```python
from xbt.plugins import hookimpl, XbtContext

@hookimpl(run_for_commands={"run", "test"})
def xbt_pre_invoke(context: XbtContext) -> list[str] | None:
    """Only runs for run and test commands."""
    if not context.has_project:
        return None  # No project, keep original args
    
    # Inject custom flags based on project context
    return context.args + ["--modified"]
```

**Notes:**
- Return modified args list or `None` (to keep unchanged)
- All plugins' modifications are chained sequentially
- Use `context.command` instead of parsing args manually
- Use decorator parameters for filtering instead of manual checks

### `xbt_post_invoke(context: XbtContext) -> None`

React to dbt results after execution. Use `@hookimpl` parameters to skip certain commands:

```python
from xbt.plugins import hookimpl, XbtContext

@hookimpl(skip_for_commands={"plugin", "plugins"})
def xbt_post_invoke(context: XbtContext) -> None:
    """Skip for plugin management commands, run for all others."""
    if not context.has_project:
        return
    
    if context.result.success:
        # Upload artifacts, send notifications, etc.
        print(f"✓ {context.command} completed successfully")
    else:
        print(f"✗ {context.command} failed")
```

**Notes:**
- `context.result` has `success` (bool) and `exception` (optional)
- `context.command` is the dbt command that ran
- Use for post-processing, custom reporting, error handling

### `xbt_init() -> Optional[PluginConfig]`

Load plugin configuration during initialization.

```python
from xbt.plugins import hookimpl, PluginConfig

class MyPluginConfig(PluginConfig):
    config_file = "~/.xbt/my_plugin.yml"
    backend: str = "local"
    max_retries: int = 3

    def validate(self) -> None:
        if self.backend not in {"local", "s3", "gcs"}:
            raise ValueError(f"Invalid backend: {self.backend}")

@hookimpl
def xbt_init() -> MyPluginConfig | None:
    return MyPluginConfig.from_default()
```

## Shared Plugin Utilities

Import from `xbt.plugins`:

```python
from xbt.plugins import (
    get_dbt_command,
    is_command_in_set,
    find_dbt_project_dir,
    find_workspace_root,
    emit_status,
    format_status_message,
)
```

### `get_dbt_command(args: Sequence[str]) -> Optional[str]`
- Extracts dbt command from CLI arguments
- Handles flags and flag-value pairs correctly
- Example: `get_dbt_command(["--project-dir", ".", "run"])` → `"run"`

### `is_command_in_set(command: Optional[str], commands: Set[str]) -> bool`
- Case-insensitive command matching
- Example: `is_command_in_set("RUN", {"run", "test"})` → `True`

### `find_dbt_project_dir(start_dir: Optional[Path] = None) -> Optional[Path]`
- Search for `dbt_project.yml` up the directory tree
- Starts from `start_dir` or current working directory
- Returns path containing `dbt_project.yml` or `None`

### `find_workspace_root(start_dir: Path, markers: Optional[list[str]] = None) -> Path`
- Find repository root by looking for marker files
- Default markers: `.git`, `pyproject.toml`, `dbt_project.yml`
- Returns workspace root or `start_dir` if not found

### `emit_status(logger: logging.Logger, message: str, level: int = logging.INFO) -> None`
- Log and print a message (unified output)
- Useful for user-facing status updates

### `format_status_message(prefix: str, message: str) -> str`
- Format message with timestamp and prefix
- Example output: `"14:23:45  my-plugin: processing started"`

## Command Filtering with Decorators

No manual branching needed! Use decorator parameters:

```python
from xbt.plugins import hookimpl, XbtContext

# Only run for specific commands
@hookimpl(run_for_commands={"run", "test", "build"})
def xbt_post_invoke(context: XbtContext) -> None:
    # This hook only executes for run, test, build
    # xbt automatically skips for other commands
    pass

# Skip for specific commands
@hookimpl(skip_for_commands={"plugin", "plugins"})
def xbt_pre_invoke(context: XbtContext) -> list[str] | None:
    # This hook runs for all commands except plugin management
    pass

# No filters (runs for all commands)
@hookimpl
def xbt_register_callbacks(context=None):
    # This always runs
    pass
```

## Best Practices

### Keep Hooks Focused

Each hook should have a single responsibility:
- `xbt_register_commands` – Add CLI commands
- `xbt_register_callbacks` – Monitor dbt events
- `xbt_pre_invoke` – Prepare or modify arguments
- `xbt_post_invoke` – React to results
- `xbt_init` – Load plugin configuration

### Use Command Filtering

Always use `@hookimpl` parameters to filter by command rather than manual checks:

```python
# Good: Declarative filtering
@hookimpl(run_for_commands={"run", "test"})
def xbt_pre_invoke(context):
    # Only runs for run and test
    pass

# Avoid: Manual filtering
@hookimpl
def xbt_pre_invoke(context):
    if context.command not in {"run", "test"}:
        return
    # Logic here
```

### Leverage XbtContext

Use the pre-extracted context instead of manual parsing:

```python
# Good: Use context properties
if context.has_project and context.project_dir:
    # Work with project
    pass

# Avoid: Manual directory searches
from pathlib import Path
project_dir = None
current = Path.cwd()
while current != current.parent:
    if (current / "dbt_project.yml").exists():
        project_dir = current
        break
```

## Real-World Examples

See [src/xbt/_plugins/](src/xbt/_plugins/) for built-in plugins:

- [example_plugin.py](src/xbt/_plugins/example_plugin.py) – Reference implementation with all hooks
- [plugin_command.py](src/xbt/_plugins/plugin_command.py) – Real-world plugin that adds the `xbt plugin list` command
