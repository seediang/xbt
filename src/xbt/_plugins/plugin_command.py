"""
Plugin command for xbt.

Provides commands to manage and list loaded plugins.
"""

import logging
from typing import Any, Callable, List, Optional

import pluggy

from xbt.plugin_manager import XbtPluginManager

__version__ = "0.1.0"

logger = logging.getLogger(__name__)

hookimpl = pluggy.HookimplMarker("xbt")


@hookimpl
def xbt_register_commands(cli_group: Any) -> None:
    """Add plugin management commands to xbt."""

    @cli_group.group(name="plugin")
    def plugin_group():
        """Manage xbt plugins."""
        pass

    @plugin_group.command(name="list")
    def list_plugins():
        """List all loaded plugins."""

        pm = XbtPluginManager.get_instance()
        plugins = pm.get_plugins()

        if not plugins:
            print("No plugins loaded")
            return

        # Build a map from name -> metadata for fast lookup
        plugin_map = {p["name"]: p for p in plugins}

        print("Loaded plugins:\n")
        # Respect the manager's loaded order
        for name in pm._plugins_loaded:
            plugin = plugin_map.get(name)
            if not plugin:
                continue
            source_icon = "📦" if plugin["source"] == "external" else "🔧"
            print(f"  {source_icon} {plugin['name']}")
            print(f"     Version: {plugin['version']}")
            print(f"     Source:  {plugin['source']}")
            print(f"     Module:  {plugin['module']}")
            print()


@hookimpl
def xbt_register_callbacks() -> Optional[List[Callable[[Any], None]]]:
    """Example implementation."""
    return None


@hookimpl
def xbt_pre_invoke(args: List[str]) -> Optional[List[str]]:
    """Example implementation."""
    return None


@hookimpl
def xbt_post_invoke(args: List[str], result: Any) -> None:
    """Example implementation."""
    pass
