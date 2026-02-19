# xbt-core – dbt-core Extended

**xbt** is a wrapper around [dbt](https://docs.getdbt.com/) that extends `dbtRunner` with a simple yet flexible plugin system. It enables you to inject custom logic before and after dbt commands while maintaining full compatibility with dbt's CLI and exit codes.

## Features

- 🔌 **Plugin System** – Register custom logic with minimal boilerplate (v0.2+: ~70% less code!)
- 🎯 **Structured Context** – Pre-extracted command, project directory, and execution info
- 🔑 **Command Filtering** – Declarative `@hookimpl(run_for_commands={...})` instead of manual branching
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

xbt features a plugin system that minimizes boilerplate by providing:

- **Hook Contexts** – Pre-extracted command, project directory, and execution info per hook
- **Command Filtering** – Declarative `@hookimpl(run_for_commands={...})` decorators instead of manual branching
- **Shared Utilities** – Common functions in `xbt.plugins` module for CLI parsing, directory discovery, and formatting
- **Plugin Configuration** – YAML-based `PluginConfig` for structured plugin settings

### Automatic Plugin Discovery

xbt discovers plugins from:
- Built-in plugins in `src/xbt/_plugins/`
- External packages via entry points (group: `xbt`)

Plugins are auto-loaded and immediately available—no registration code needed.

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

See [PLUGIN_DEVELOPMENT.md](PLUGIN_DEVELOPMENT.md) for comprehensive plugin development documentation, including:

- Quick start guide with example plugins
- Complete hook context reference
- All hook specifications with detailed examples
- Shared utilities for common tasks
- Command filtering with decorators
- Real-world plugin examples from the built-in plugins

## Development

### Prerequisites

- Python 3.12 or later
- [uv](https://docs.astral.sh/uv/) for package management

### Setup

Clone the repository and install dependencies:

```bash
git clone <repository-url>
cd xbt-core
uv sync
```

### Running Tests

```bash
uv run pytest
```

### Type Checking

```bash
uv run ty check
```

### Linting and Formatting

```bash
# Check formatting and linting
uv run ruff check .
uv run ruff format --check .

# Auto-fix issues
uv run ruff format .
uv run ruff check --fix .
```

### Full Validation

Run all checks that are required for a PR:

```bash
uv run pytest && uv run ruff check . && uv run ruff format --check . && uv run ty check
```

### Project Structure

```
xbt-core/
├── src/xbt/
│   ├── __init__.py              # Public API exports
│   ├── main.py                  # CLI entry point
│   ├── xbt_runner.py            # Core xbtRunner class
│   ├── hookspecs.py             # Hook specifications for plugins
│   ├── plugin_manager.py        # Plugin discovery and management
│   ├── plugins/                 # Public plugin development API (v0.2+)
│   │   ├── __init__.py          # Exports: hook contexts, hookimpl, utilities
│   │   ├── context.py           # Hook context dataclasses
│   │   ├── filter.py            # HookFilter for command filtering
│   │   ├── utils.py             # Shared plugin utilities
│   │   └── config.py            # PluginConfig base class
│   ├── _plugins/                # Built-in plugins
│   │   ├── __init__.py
│   │   ├── example_plugin.py    # Reference implementation
│   │   └── plugin_command.py    # CLI commands plugin
├── tests/
│   ├── unit/
│   │   ├── plugins/             # Plugin system tests (v0.2+)
│   │   │   ├── test_context.py
│   │   │   ├── test_filter.py
│   │   │   └── test_utils.py
│   │   ├── test_hookspecs.py
│   │   ├── test_plugin_manager.py
│   │   ├── test_xbt_runner.py
│   │   └── test_main.py
│   ├── integration/
│   │   ├── test_dbt_duckdb.py
│   │   └── test_plugin_loading.py
│   └── fixtures/
├── pyproject.toml               # Project configuration
├── README.md                    # This file
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

Before opening a PR, please run all validations:

```bash
uv run pytest && uv run ruff check . && uv run ruff format --check . && uv run ty check
```