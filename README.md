# xbt-core – dbt-core Extended

**xbt** is a wrapper around [dbt](https://docs.getdbt.com/) that extends `dbtRunner` with a simple yet flexible plugin system. It enables you to inject custom logic before and after dbt commands while maintaining full compatibility with dbt's CLI and exit codes.

## Features

- 🔌 **Plugin System** – Register custom logic to run before/after any dbt command
- 📋 **Custom Commands** – Add new commands to the CLI context
- 🎯 **Transparent Wrapper** – Output and exit codes match dbt exactly
- 🔗 **dbtRunner Integration** – Direct access to dbt's event system via callbacks
- 🐍 **Python 3.12+** – Built with modern Python

## Installation

```bash
pip install xbt
```

Or, if you're using [uv](https://docs.astral.sh/uv/) for package management:

```bash
uv sync
```

## Quick Start

Use `xbt` as a drop-in replacement for `dbt-core`:

```bash
xbt run
xbt test
xbt compile
xbt -h
```

All standard dbt commands work exactly as they would with `dbt`, including argument parsing and exit codes.

## Plugin System

xbt uses [pluggy](https://pluggy.readthedocs.io/) to provide a simple yet powerful plugin architecture. Plugins can extend xbt by implementing four hooks:

1. **`xbt_register_commands`** – Add custom commands to the CLI
2. **`xbt_register_callbacks`** – Receive real-time dbt events  
3. **`xbt_pre_invoke`** – Transform command-line arguments
4. **`xbt_post_invoke`** – React to dbt results after execution

Plugins are discovered automatically from:
- Built-in plugins in `src/xbt/_plugins/`
- External packages via entry points (group: `xbt`)

### Plugin Configuration

xbt supports a configuration file (`xbt.yml`) to control which plugins are loaded. This file uses two modes:

**Blacklist mode** (default):
- All plugins are loaded except those listed in `disabled_plugins`
- Used when `enabled_plugins` is not specified

**Whitelist mode**:
- Only plugins listed in `enabled_plugins` are loaded
- When `enabled_plugins` is empty, NO plugins are loaded

#### Configuration File Format

Create an `xbt.yml` file in your project root:

```yaml
# Blacklist mode: disable specific plugins
disabled_plugins:
  - builtin_example_plugin

# OR use whitelist mode: only enable specific plugins
enabled_plugins:
  - builtin_plugin_manager_plugin
  - my_external_plugin
```

#### Explicit Plugin Order

You can control the order in which plugins are called by adding a
`plugin_order` list to `xbt.yml`. The plugin manager registers and
invokes hooks in registration order, so specifying `plugin_order`
ensures `xbt_pre_invoke` chaining and other hooks run in the order you
expect.

Rules:
- Plugins listed in `plugin_order` are registered in the given order.
- Any discovered but unlisted plugins are appended afterwards in
  discovery order.
- Plugins listed in `plugin_order` that are disabled or not found are
  ignored and will emit a warning.

Example `xbt.yml`:

```yaml
plugin_order:
  - builtin_example_plugin
  - my_external_plugin

# You can still use the blacklist/whitelist controls
disabled_plugins:
  - builtin_some_other_plugin
```

#### Plugin Management Commands

Use the built-in `plugin` command to manage and inspect plugins:

```bash
xbt plugin list    # Show all loaded plugins with versions
```

### Plugin Development

#### Create a Simple Plugin

1. Create a Python file implementing one or more hooks:

```python
# my_xbt_plugin/plugin.py
from xbt.hookspecs import hookimpl

@hookimpl
def xbt_post_invoke(args, result):
    """React to dbt command results."""
    if result.success:
        print("✓ Command succeeded!")
    elif result.exception:
        print(f"✗ Error: {result.exception}")

@hookimpl
def xbt_pre_invoke(args):
    """Modify arguments before dbt processes them."""
    if "--profile" not in args and "--select" in args:
        args = ["--profile", "dev"] + args
    return args
```

2. Register your plugin in your package's `pyproject.toml`:

```toml
[project.entry-points.xbt]
my_plugin = "my_xbt_plugin.plugin"
```

3. Install your package:

```bash
pip install my_xbt_plugin
```

Your plugin will be auto-discovered and loaded when xbt runs!

#### Hook Reference

**`xbt_register_commands(cli_group)`**
- Called during xbtRunner initialization
- Access the Click CLI group to add custom commands/options
- Use for extending xbt with new subcommands

**`xbt_register_callbacks()`**
- Should return `List[Callable[[EventMsg], None]]` or None
- Each callback receives EventMsg objects in real-time as dbt executes
- Use for monitoring, logging, or event-driven behavior

**`xbt_pre_invoke(args)`**
- Receives list of command-line arguments
- Should return modified list or None (to keep unchanged)
- All plugins' args modifications are chained sequentially
- Use for argument validation, injection, or transformation

**`xbt_post_invoke(args, result)`**
- Called after dbt command completes
- `result` has attributes: `success` (bool), `exception` (Optional[Exception])
- Use for post-processing, custom reporting, error handling

#### Example: Built-in Plugin

See [src/xbt/_plugins/example_plugin.py](src/xbt/_plugins/example_plugin.py) for a reference implementation showing all four hooks.

## Development

### Prerequisites

- Python 3.12 or later
- [uv](https://docs.astral.sh/uv/) for package management

### Setup

Clone the repository and install dependencies:

```bash
git clone <repository-url>
cd xbt2
uv sync
```

### Running Tests

```bash
uv run pytest
```

### Type Checking

```bash
uv run ty
```

### Linting and Formatting

```bash
# Check formatting and linting
uv run ruff check src/xbt

# Auto-fix issues
uv run ruff format src/xbt
uv run ruff check --fix src/xbt
```

### Project Structure

```
xbt2/
├── src/xbt/
│   ├── main.py              # CLI entry point
│   ├── xbt_runner.py        # Core xbtRunner class
│   ├── hookspecs.py         # Hook specifications for plugins
│   ├── plugin_manager.py    # Plugin discovery and management
│   ├── _plugins/
│   │   ├── __init__.py
│   │   └── example_plugin.py    # Reference plugin implementation
├── pyproject.toml           # Project configuration
└── README.md
```

## Acknowledgements

dbt® is a registered trademark of dbt Labs, Inc. This project is an independent wrapper around dbt and is not endorsed by or affiliated with dbt Labs.

## License

[Add your license here]

## Contributing

We track changes using Changie (https://changie.dev/) and require a small change fragment for non-trivial PRs.

- Add a changie fragment for code or behavior changes: run `changie new` and include the generated file under `changes/unreleased/`.
- PRs that only change documentation, tests, fixtures, or Markdown do not need a fragment and are accepted without one.
- If you have an exceptional reason to skip adding a fragment (for example an emergency hotfix or infra-only change), add the `no-changie` label to the PR and explain the rationale in the PR description; the CI will skip the fragment check when that label is present.

Quick commands:

```bash
# Create a changie fragment interactively
changie new

# Batch a patch (maintainer only)
changie batch patch
changie merge
```

Please also run tests and linters before opening a PR:

```bash
uv run ruff check .
uv run ty check
uv run pytest
```