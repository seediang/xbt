"""Unit tests for hookspecs.py"""

import pluggy
import pytest

from xbt import hookspecs


class TestHookSpecifications:
    """Test hook specification definitions."""

    def test_hookspec_marker_exists(self):
        """Test that hookspec marker is defined."""
        assert hasattr(hookspecs, "hookspec")
        assert isinstance(hookspecs.hookspec, pluggy.HookspecMarker)

    @pytest.mark.parametrize(
        "hook_name",
        [
            "xbt_register_commands",
            "xbt_register_callbacks",
            "xbt_pre_invoke",
            "xbt_post_invoke",
        ],
    )
    def test_hook_exists(self, hook_name):
        """Test that hook is defined and callable."""
        assert hasattr(hookspecs, hook_name)
        assert callable(getattr(hookspecs, hook_name))


class TestHookSpecRegistration:
    """Test that hooks can be registered with pluggy."""

    def test_register_hookspecs_with_pluggy(self):
        """Test that hookspecs can be registered with PluginManager."""
        pm = pluggy.PluginManager("xbt")

        # Should not raise exception
        pm.add_hookspecs(hookspecs)

        # Verify hooks are registered
        assert pm.hook.xbt_register_commands
        assert pm.hook.xbt_register_callbacks
        assert pm.hook.xbt_pre_invoke
        assert pm.hook.xbt_post_invoke

    def test_hook_names_in_plugin_manager(self):
        """Test that all expected hooks are available in plugin manager."""
        pm = pluggy.PluginManager("xbt")
        pm.add_hookspecs(hookspecs)

        # Get all hook names
        hook_names = [name for name in dir(pm.hook) if not name.startswith("_")]

        assert "xbt_register_commands" in hook_names
        assert "xbt_register_callbacks" in hook_names
        assert "xbt_pre_invoke" in hook_names
        assert "xbt_post_invoke" in hook_names


class TestHookImplRegistration:
    """Test that hook implementations can be registered."""

    def test_register_command_hook_implementation(self):
        """Test registering xbt_register_commands implementation."""
        pm = pluggy.PluginManager("xbt")
        pm.add_hookspecs(hookspecs)

        hookimpl = pluggy.HookimplMarker("xbt")

        class Plugin:
            @hookimpl
            def xbt_register_commands(self, cli_group):
                cli_group.test = True

        plugin = Plugin()
        pm.register(plugin)

        # Should be able to call hook
        from unittest.mock import Mock

        mock_cli = Mock()
        pm.hook.xbt_register_commands(cli_group=mock_cli)

        # Verify hook was called
        assert hasattr(mock_cli, "test")
        assert mock_cli.test is True

    def test_register_callbacks_hook_implementation(self):
        """Test registering xbt_register_callbacks implementation."""
        pm = pluggy.PluginManager("xbt")
        pm.add_hookspecs(hookspecs)

        hookimpl = pluggy.HookimplMarker("xbt")

        class Plugin:
            @hookimpl
            def xbt_register_callbacks(self):
                return [lambda event: None]

        plugin = Plugin()
        pm.register(plugin)

        # Should be able to call hook
        results = pm.hook.xbt_register_callbacks()

        # Verify hook was called and returned callback
        assert len(results) == 1
        assert callable(results[0][0])

    def test_register_pre_invoke_hook_implementation(self):
        """Test registering xbt_pre_invoke implementation."""
        pm = pluggy.PluginManager("xbt")
        pm.add_hookspecs(hookspecs)

        hookimpl = pluggy.HookimplMarker("xbt")

        class Plugin:
            @hookimpl
            def xbt_pre_invoke(self, args):
                return args + ["--added"]

        plugin = Plugin()
        pm.register(plugin)

        # Should be able to call hook
        results = pm.hook.xbt_pre_invoke(args=["test"])

        # Verify hook was called and modified args
        assert len(results) == 1
        assert results[0] == ["test", "--added"]

    def test_register_post_invoke_hook_implementation(self):
        """Test registering xbt_post_invoke implementation."""
        pm = pluggy.PluginManager("xbt")
        pm.add_hookspecs(hookspecs)

        hookimpl = pluggy.HookimplMarker("xbt")

        class Plugin:
            @hookimpl
            def xbt_post_invoke(self, args, result):
                result.processed = True

        plugin = Plugin()
        pm.register(plugin)

        # Should be able to call hook
        from unittest.mock import Mock

        mock_result = Mock()
        pm.hook.xbt_post_invoke(args=["test"], result=mock_result)

        # Verify hook was called and modified result
        assert hasattr(mock_result, "processed")
        assert mock_result.processed is True


class TestMultiplePlugins:
    """Test that multiple plugins can implement hooks."""

    def test_multiple_plugins_register_commands(self):
        """Test that multiple plugins can register commands."""
        pm = pluggy.PluginManager("xbt")
        pm.add_hookspecs(hookspecs)

        hookimpl = pluggy.HookimplMarker("xbt")

        class Plugin1:
            @hookimpl
            def xbt_register_commands(self, cli_group):
                cli_group.plugin1 = True

        class Plugin2:
            @hookimpl
            def xbt_register_commands(self, cli_group):
                cli_group.plugin2 = True

        pm.register(Plugin1())
        pm.register(Plugin2())

        # Both plugins should be called
        from unittest.mock import Mock

        mock_cli = Mock()
        pm.hook.xbt_register_commands(cli_group=mock_cli)

        assert mock_cli.plugin1 is True
        assert mock_cli.plugin2 is True

    def test_multiple_plugins_register_callbacks(self):
        """Test that callbacks from multiple plugins are collected."""
        pm = pluggy.PluginManager("xbt")
        pm.add_hookspecs(hookspecs)

        hookimpl = pluggy.HookimplMarker("xbt")

        class Plugin1:
            @hookimpl
            def xbt_register_callbacks(self):
                return [lambda: "callback1"]

        class Plugin2:
            @hookimpl
            def xbt_register_callbacks(self):
                return [lambda: "callback2"]

        pm.register(Plugin1())
        pm.register(Plugin2())

        results = pm.hook.xbt_register_callbacks()

        # Both plugins' callbacks should be in results (order may vary)
        assert len(results) == 2
        callback_values = [results[0][0](), results[1][0]()]
        assert "callback1" in callback_values
        assert "callback2" in callback_values

    def test_multiple_plugins_pre_invoke(self):
        """Test that multiple plugins can modify args in sequence."""
        pm = pluggy.PluginManager("xbt")
        pm.add_hookspecs(hookspecs)

        hookimpl = pluggy.HookimplMarker("xbt")

        class Plugin1:
            @hookimpl
            def xbt_pre_invoke(self, args):
                return args + ["plugin1"]

        class Plugin2:
            @hookimpl
            def xbt_pre_invoke(self, args):
                return args + ["plugin2"]

        pm.register(Plugin1())
        pm.register(Plugin2())

        results = pm.hook.xbt_pre_invoke(args=["test"])

        # Both modifications should be returned (order may vary)
        assert len(results) == 2
        # Check that plugins modified the args
        assert any("plugin1" in r for r in results)
        assert any("plugin2" in r for r in results)
