# Copilot instructions for xbt-core

This project is a thin wrapper around dbt that exposes a plugin system. The instructions below focus on the concrete, discoverable patterns you need to be productive editing and extending this codebase.

- **Big picture**: `xbt` wraps `dbtRunner` and preserves dbt CLI behavior while allowing plugins to register commands, register event callbacks, and transform arguments before/after dbt runs. Key runtime classes live in [src/xbt/xbt_runner.py](src/xbt/xbt_runner.py) and [src/xbt/plugin_manager.py](src/xbt/plugin_manager.py).

- **Core files to read first**:
  - [src/xbt/xbt_runner.py](src/xbt/xbt_runner.py) — subclass of `dbtRunner`; overwrites `cli.name` to `xbt` and calls plugin hooks around invocation.
  - [src/xbt/plugin_manager.py](src/xbt/plugin_manager.py) — discovery, loading, and lifecycle of plugins; built-in plugins are namespaced as `builtin_<module>`.
  - [src/xbt/hookspecs.py](src/xbt/hookspecs.py) — the four hook specs: `xbt_register_commands`, `xbt_register_callbacks`, `xbt_pre_invoke`, `xbt_post_invoke`.
  - [src/xbt/_plugins/example_plugin.py](src/xbt/_plugins/example_plugin.py) — canonical reference implementation for the hooks.
  - [src/xbt/main.py](src/xbt/main.py) — CLI entrypoint and exit-code mapping.

- **Plugin discovery & naming**:
  - Built-in plugins: scanned from `src/xbt/_plugins/*.py` and registered under names `builtin_<module>`.
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
  - Run tests: `uv run pytest`
  - Type check: `uv run ty check`
  - Lint / format: `uv run ruff check .` and `uv run ruff format .`
  - Run xbt CLI locally: `uv run python -m xbt.main -- <dbt-args>` or install editable and run `xbt`.

- **Patterns and conventions**:
  - Use type hints everywhere (project enforces `ty`).
  - Keep plugin side-effects isolated and defensive: plugin manager wraps hook calls with try/except and logs warnings — follow same pattern when adding new hooks or callbacks.
  - Built-in plugin modules may set `__version__` — plugin registry expects this but tolerates `unknown`.

- **Tests & examples**:
  - See tests in `tests/unit` and `tests/integration` for realistic usage patterns. Tests exercise plugin loading (whitelist/blacklist), hooks chaining, and invocation results.

- **When modifying plugin behavior**:
  - Update `hookspecs.py` first (if adding a hook), then update `plugin_manager.py` and `xbt_runner.py` to call the hook.
  - Add a corresponding example in `src/xbt/_plugins/` and add focused unit tests under `tests/unit`.

- **Quick examples to copy-paste**:
  - Register a CLI command: see `xbt_register_commands` example in [src/xbt/_plugins/example_plugin.py](src/xbt/_plugins/example_plugin.py).
  - Pre-invoke arg injection: return a modified list from `xbt_pre_invoke` (see [src/xbt/hookspecs.py](src/xbt/hookspecs.py) docstring example).

If anything here is unclear or you'd like more detail about a specific file or workflow (for example, the entry-point loading behavior or test fixtures), tell me which area to expand and I'll iterate.
