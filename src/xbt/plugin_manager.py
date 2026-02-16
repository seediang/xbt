"""Plugin manager for xbt using pluggy."""

import importlib.metadata
import importlib.util
import logging
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

import pluggy
import yaml

from . import hookspecs

logger = logging.getLogger(__name__)

hookimpl = pluggy.HookimplMarker("xbt")


class XbtPluginManager:
    """
    Manages xbt plugins using pluggy.

    Discovers plugins from:
    1. Built-in plugins in src/xbt/_plugins/
    2. External packages via entry points (group: xbt)

    Plugins can extend xbt by implementing hooks defined in hookspecs.py.

    Implemented as a singleton to ensure only one instance exists.
    """

    _instance = None

    def __init__(self):
        """Initialize plugin manager and discover all available plugins."""
        # Prevent re-initialization if already initialized
        if XbtPluginManager._instance is not None:
            return

        self.pm = pluggy.PluginManager("xbt")
        self.pm.add_hookspecs(hookspecs)
        self._plugins_loaded = []
        self._plugin_registry: List[Dict[str, Any]] = []
        # Raw discovered plugins (including metadata) in discovery order
        self._discovered_plugins_raw: List[Dict[str, Any]] = []
        # Optional explicit ordering from config
        self._plugin_order: Optional[List[str]] = None
        self._enabled_plugins: Optional[Set[str]] = None
        self._disabled_plugins: Set[str] = set()

        # Load configuration from xbt.yml if it exists
        self._load_config()

        self._discover_and_load_plugins()
        logger.info(
            f"Loaded {len(self._plugins_loaded)} plugins: {self._plugins_loaded}"
        )

    def _load_config(self):
        """Load plugin configuration from xbt.yml file."""
        if yaml is None:
            logger.debug("PyYAML not installed, skipping config file loading")
            return

        # Look for xbt.yml in current directory and parent directories
        config_path = self._find_config_file()
        if config_path is None:
            logger.debug("No xbt.yml config file found")
            return

        try:
            with open(config_path, "r") as f:
                config = yaml.safe_load(f) or {}

            # Parse enabled_plugins
            enabled = config.get("enabled_plugins")
            if enabled is not None:
                self._enabled_plugins = set(enabled) if enabled else set()
                logger.info(f"Enabled plugins from config: {self._enabled_plugins}")

            # Parse plugin_order
            plugin_order = config.get("plugin_order")
            if plugin_order is not None:
                # keep the order as provided by the user
                self._plugin_order = list(plugin_order) if plugin_order else []
                logger.info(f"Plugin order from config: {self._plugin_order}")

            # Parse disabled_plugins
            disabled = config.get("disabled_plugins") or []
            self._disabled_plugins = set(disabled) if disabled else set()
            if self._disabled_plugins:
                logger.info(f"Disabled plugins from config: {self._disabled_plugins}")
        except Exception as e:
            logger.warning(f"Error loading xbt.yml config: {e}")

    def _find_config_file(self) -> Optional[Path]:
        """Find xbt.yml in current directory or project root."""
        # Check current directory and up to project root
        current = Path.cwd()
        for _ in range(10):  # Limit to 10 levels up
            config_file = current / "xbt.yml"
            if config_file.exists():
                return config_file
            parent = current.parent
            if parent == current:  # Reached filesystem root
                break
            current = parent
        return None

    def _is_plugin_allowed(self, plugin_name: str) -> bool:
        """Check if a plugin is allowed based on configuration."""
        # Check if explicitly disabled
        if plugin_name in self._disabled_plugins:
            return False

        # If enabled_plugins is defined, only allow those
        if self._enabled_plugins is not None:
            return plugin_name in self._enabled_plugins

        # Otherwise, allow all plugins except disabled ones
        return True

    @classmethod
    def get_instance(cls) -> "XbtPluginManager":
        """
        Get or create the singleton instance of XbtPluginManager.

        Returns:
            The singleton XbtPluginManager instance.
        """
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def _discover_and_load_plugins(self):
        """Discover and load plugins from all sources."""
        # Load built-in plugins from src/xbt/_plugins/
        # Discover built-in and external plugins; registration happens
        # after ordering is computed to allow `plugin_order` to take effect.
        self._load_builtin_plugins()
        self._load_entry_point_plugins()

        # Register discovered plugins in the final order determined by
        # configuration (if provided) while respecting disabled/whitelist.
        self._register_plugins_in_order()

    def _load_builtin_plugins(self):
        """Load built-in plugins from the _plugins package."""
        plugins_dir = Path(__file__).parent / "_plugins"

        if not plugins_dir.exists():
            logger.debug("No built-in plugins directory found")
            return

        try:
            # Add _plugins directory to sys.path temporarily for imports
            plugins_path = str(plugins_dir.parent)
            if plugins_path not in sys.path:
                sys.path.insert(0, plugins_path)

            # Discover and import all .py modules in _plugins/ (except __init__)
            for plugin_file in plugins_dir.glob("*.py"):
                if plugin_file.name.startswith("__"):
                    continue

                module_name = plugin_file.stem
                try:
                    spec = importlib.util.spec_from_file_location(
                        f"xbt._plugins.{module_name}", plugin_file
                    )
                    if spec and spec.loader:
                        module = importlib.util.module_from_spec(spec)
                        sys.modules[f"xbt._plugins.{module_name}"] = module
                        spec.loader.exec_module(module)

                        # Check if plugin is allowed
                        plugin_name = f"builtin_{module_name}"
                        if not self._is_plugin_allowed(plugin_name):
                            logger.debug(f"Skipping disabled plugin: {plugin_name}")
                            continue

                        # Record discovery; actual registration delayed until
                        # ordering is computed.
                        version = getattr(module, "__version__", "unknown")
                        self._discovered_plugins_raw.append(
                            {
                                "name": plugin_name,
                                "obj": module,
                                "version": version,
                                "source": "builtin",
                                "module": f"xbt._plugins.{module_name}",
                            }
                        )
                        logger.debug(f"Discovered built-in plugin: {module_name}")
                except Exception as e:
                    logger.warning(f"Failed to load built-in plugin {module_name}: {e}")
        except Exception as e:
            logger.warning(f"Error discovering built-in plugins: {e}")

    def _load_entry_point_plugins(self):
        """Load external plugins registered via entry points."""
        try:
            # Python 3.10+ API - use select() with group parameter
            entry_points = importlib.metadata.entry_points(group="xbt")
        except TypeError:
            # Fallback for Python < 3.10
            all_eps = importlib.metadata.entry_points()
            if isinstance(all_eps, dict):
                entry_points = all_eps.get("xbt", [])
            else:
                entry_points = [ep for ep in all_eps if ep.group == "xbt"]

        for entry_point in entry_points:
            try:
                # Check if plugin is allowed
                if not self._is_plugin_allowed(entry_point.name):
                    logger.debug(f"Skipping disabled plugin: {entry_point.name}")
                    continue

                plugin = entry_point.load()
                # Attempt to determine version from distribution metadata
                version = "unknown"
                try:
                    package_name = entry_point.value.split(":")[0].split(".")[0]
                    dist = importlib.metadata.distribution(package_name)
                    version = dist.version
                except Exception:
                    pass

                # Record discovery; registration delayed until ordering step
                self._discovered_plugins_raw.append(
                    {
                        "name": entry_point.name,
                        "obj": plugin,
                        "version": version,
                        "source": "external",
                        "module": entry_point.value,
                    }
                )
                logger.debug(f"Discovered entry point plugin: {entry_point.name}")
            except Exception as e:
                logger.warning(
                    f"Failed to load entry point plugin {entry_point.name}: {e}"
                )

        # Note: _register_plugins_in_order will apply config-based filtering
        # (enabled/disabled) when doing the final registrations.

    def _register_plugins_in_order(self):
        """Register discovered plugins with pluggy in configured order.

        This respects `self._plugin_order` when provided. Any names in
        `plugin_order` that are not present (either unknown or disabled)
        will be logged and ignored. Remaining discovered plugins are
        appended in discovery order.
        """
        # Build a map for quick lookup
        discovered_map = {p["name"]: p for p in self._discovered_plugins_raw}

        # Determine allowed candidates (respecting enabled/disabled)
        candidates = [p for p in self._discovered_plugins_raw if self._is_plugin_allowed(p["name"])]
        candidate_names = [p["name"] for p in candidates]

        final_order: List[str] = []
        used: Set[str] = set()

        if self._plugin_order is not None:
            # Add in user-specified order when available
            for name in self._plugin_order:
                if name in candidate_names:
                    final_order.append(name)
                    used.add(name)
                else:
                    logger.warning(f"Plugin specified in plugin_order not found or disabled: {name}")

        # Append remaining candidates in discovery order
        for name in candidate_names:
            if name not in used:
                final_order.append(name)

        # Perform actual registration in final_order
        for name in final_order:
            entry = discovered_map.get(name)
            if not entry:
                logger.debug(f"Skipping unknown plugin during registration: {name}")
                continue
            try:
                self.pm.register(entry["obj"], name=name)
                self._plugins_loaded.append(name)
                self._plugin_registry.append(
                    {
                        "name": name,
                        "version": entry.get("version", "unknown"),
                        "source": entry.get("source", "unknown"),
                        "module": entry.get("module", "unknown"),
                    }
                )
                logger.debug(f"Registered plugin: {name}")
            except Exception as e:
                logger.warning(f"Failed to register plugin {name}: {e}")
    def hook_register_commands(self, cli_group: Any) -> None:
        """
        Call xbt_register_commands hook for all plugins.

        Args:
            cli_group: The Click Group object to register commands with.
        """
        try:
            self.pm.hook.xbt_register_commands(cli_group=cli_group)
        except Exception as e:
            logger.warning(f"Error in xbt_register_commands hooks: {e}")

    def hook_register_callbacks(self) -> List:
        """
        Call xbt_register_callbacks hook for all plugins.

        Returns:
            Flattened list of all callbacks from all plugins.
        """
        callbacks = []
        try:
            results = self.pm.hook.xbt_register_callbacks()
            for result in results:
                if result:
                    if isinstance(result, list):
                        callbacks.extend(result)
                    else:
                        callbacks.append(result)
        except Exception as e:
            logger.warning(f"Error in xbt_register_callbacks hooks: {e}")
        return callbacks

    def hook_pre_invoke(self, args: List[str]) -> List[str]:
        """
        Call xbt_pre_invoke hook for all plugins, chaining modifications.

        Each plugin receives the args from the previous plugin, allowing
        sequential modification of arguments.

        Args:
            args: Original command-line arguments.

        Returns:
            Modified arguments after all plugins have processed them.
        """
        try:
            results = self.pm.hook.xbt_pre_invoke(args=args)
            # Chain modifications: each result becomes input for next plugin
            for result in results:
                if result is not None:
                    args = result
        except Exception as e:
            logger.warning(f"Error in xbt_pre_invoke hooks: {e}")
        return args

    def hook_post_invoke(self, args: List[str], result: Any) -> None:
        """
        Call xbt_post_invoke hook for all plugins.

        Args:
            args: The arguments that were passed to dbt.
            result: The xbtRunnerResult from dbt invocation.
        """
        try:
            self.pm.hook.xbt_post_invoke(args=args, result=result)
        except Exception as e:
            logger.warning(f"Error in xbt_post_invoke hooks: {e}")

    def get_plugins(self) -> List[Dict[str, Any]]:
        """
        Get information about all loaded plugins including their versions.

        Returns:
            List of dicts with plugin information:
                - name: str - Plugin name
                - version: str - Plugin version (or "unknown" if unavailable)
                - source: str - "builtin" or "external"
                - module: str - Module name or entry point value
        """
        return self._plugin_registry
