```instructions

Use uv for Python package management and execution.

- Install dependencies with `uv sync` or `uv add <package>`.
- Run Python with `uv run python` (or `uv run python -m <module>`).
- Run tests with `uv run pytest`.
- Avoid calling `pip` directly unless explicitly requested.
## Code Quality Checks

- Run linting with `uv run ruff check .` to check code style and errors.
- Run formatting check with `uv run ruff format --check .` to verify code formatting.
- Run type checking with `uv run ty check .` for static type analysis.
- Auto-fix issues with `uv run ruff check --fix .` and `uv run ruff format .`.
- Run unit tests with `uv run pytest tests/unit/` - fast tests that should pass first.
- Run integration tests with `uv run pytest tests/integration/` - slower tests requiring dbt execution.
- Run all tests with `uv run pytest` - runs both unit and integration tests.



# Copilot instructions for xbt-core

This project is a thin wrapper around dbt that exposes a plugin system. The instructions below focus on the concrete, discoverable patterns you need to be productive editing and extending this codebase.

- **Big picture**: `xbt` wraps `dbtRunner` and preserves dbt CLI behavior while allowing plugins to register commands, register event callbacks, and transform arguments before/after dbt runs. Key runtime classes live in [src/xbt/xbt_runner.py](src/xbt/xbt_runner.py) and [src/xbt/plugin_manager.py](src/xbt/plugin_manager.py).

- **Core files to read first**:
  - [src/xbt/xbt_runner.py](src/xbt/xbt_runner.py) — subclass of `dbtRunner`; overwrites `cli.name` to `xbt` and calls plugin hooks around invocation.
  - [src/xbt/plugin_manager.py](src/xbt/plugin_manager.py) — discovery, loading, and lifecycle of plugins; built-in plugins are namespaced as `builtin_<module>`.
  - [src/xbt/hookspecs.py](src/xbt/hookspecs.py) — the four hook specs: `xbt_register_commands`, `xbt_register_callbacks`, `xbt_pre_invoke`, `xbt_post_invoke`.
  - [src/xbt/builtin_plugins/plugin_command.py](src/xbt/builtin_plugins/plugin_command.py) — example builtin plugin implementation.
  - [src/xbt/main.py](src/xbt/main.py) — CLI entrypoint and exit-code mapping.

- **Plugin discovery & naming**:
  - Built-in plugins: scanned from `src/xbt/builtin_plugins/*.py` and registered under names `builtin_<module>`.
  - External plugins: discovered via entry points group `xbt` in `pyproject.toml` / package metadata.
  - Config file: `xbt.yml` controls plugin enabling. If `enabled_plugins` is present -> whitelist mode (only those run). Otherwise uses `disabled_plugins` as a blacklist.

- **Hook behavior specifics (important for correctness)**:
  - `xbt_pre_invoke` is chained: each plugin receives the args returned by the previous. Return `None` to leave args unchanged.
  - `xbt_register_callbacks` should return a list (or single callable) of callbacks; these are merged with any provided callbacks.
  - `xbt_register_commands` receives the Click CLI group; register subcommands here.
  - `xbt_post_invoke` receives the original (or modified) args and the `xbtRunnerResult` (alias of `dbtRunnerResult`). Use `result.success` and `result.exception`.

- **Exit codes and error handling**:
  - `main()` in [src/xbt/main.py](src/xbt/main.py) maps certain dbt exceptions to specific exit codes; preserve this behavior when changing invocation paths so CLI compatibility remains the same.

- **Developer workflows and commands**:
this should commands should be executed to check the code is valid

  - Run unit tests: `uv run pytest tests/unit/` (fast, run first)
  - Run integration tests: `uv run pytest tests/integration/` (slower, run after unit tests)
  - Run all tests: `uv run pytest`
  - Type check: `uv run ty check`
  - Lint / format: `uv run ruff check .` and `uv run ruff format .`
  - Run xbt CLI locally: `uv run python -m xbt.main -- <dbt-args>` or install editable and run `xbt`.
  - Full validation workflow: `uv run ruff check . && uv run ty check && uv run pytest tests/unit/ && uv run pytest tests/integration/`

- **Patterns and conventions**:
  - Use type hints everywhere (project enforces `ty`).
  - Keep plugin side-effects isolated and defensive: plugin manager wraps hook calls with try/except and logs warnings — follow same pattern when adding new hooks or callbacks.
  - Built-in plugin modules may set `__version__` — plugin registry expects this but tolerates `unknown`.

- **Tests & examples**:
  - See tests in `tests/unit` and `tests/integration` for realistic usage patterns. Tests exercise plugin loading (whitelist/blacklist), hooks chaining, and invocation results.

- **When modifying plugin behavior**:
  - Update `hookspecs.py` first (if adding a hook), then update `plugin_manager.py` and `xbt_runner.py` to call the hook.
  - Add a corresponding example in `src/xbt/builtin_plugins/` and add focused unit tests under `tests/unit`.

- **Quick examples to copy-paste**:
  - Register a CLI command: see `xbt_register_commands` in [src/xbt/builtin_plugins/plugin_command.py](src/xbt/builtin_plugins/plugin_command.py).
  - Pre-invoke arg injection: return a modified list from `xbt_pre_invoke` (see [src/xbt/hookspecs.py](src/xbt/hookspecs.py) docstring example).

If anything here is unclear or you'd like more detail about a specific file or workflow (for example, the entry-point loading behavior or test fixtures), tell me which area to expand and I'll iterate.


```

## Changelog and release workflow (MANDATORY)

All changes to this repository must be recorded with Changie (https://changie.dev/).
Before opening a pull request, create a change fragment with `changie new` describing what the change does and why. Include the fragment in your PR so reviewers can validate release notes.

Guidelines:
- Run `changie new` to create a fragment under `changes/unreleased/` and follow prompts for `kind`/`component`.
- Use consistent `kind` values (added, changed, fixed, deprecated, removed, security) and appropriate `component` when applicable.
- When preparing releases, use `changie batch <major|minor|patch>` (or an explicit version) then `changie merge` to update `CHANGELOG.md`.
- Keep `.changie.yaml` under version control; modify it only when you need to change changie behavior.

Example commands:
```
changie new
changie batch patch
changie merge
```

Maintainers will expect changie fragments in PRs; missing fragments may be requested during review.
