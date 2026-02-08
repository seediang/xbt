"""Integration tests for plugin loading and configuration."""

from pathlib import Path


class TestPluginLoadingIntegration:
    """Integration tests for realistic plugin scenarios."""

    def test_plugin_manager_can_be_instantiated(self, reset_plugin_manager, mocker):
        """Test that plugin manager can be instantiated without errors."""
        mocker.patch("pathlib.Path.cwd", return_value=Path("/tmp"))
        mocker.patch("importlib.metadata.entry_points", return_value=[])

        from xbt.plugin_manager import XbtPluginManager

        # Should not raise exception
        pm = XbtPluginManager.get_instance()

        assert pm is not None
        assert hasattr(pm, "pm")
        assert hasattr(pm, "hook_register_commands")
        assert hasattr(pm, "hook_register_callbacks")
        assert hasattr(pm, "hook_pre_invoke")
        assert hasattr(pm, "hook_post_invoke")

    def test_plugin_manager_config_loading(
        self, reset_plugin_manager, tmp_path, mocker
    ):
        """Test that plugin manager loads configuration correctly."""
        # Create config file
        config_file = tmp_path / "xbt.yml"
        config_file.write_text("enabled_plugins:\n  - test_plugin\n")

        mocker.patch("pathlib.Path.cwd", return_value=tmp_path)

        from xbt.plugin_manager import XbtPluginManager

        mocker.patch.object(
            XbtPluginManager, "_find_config_file", return_value=config_file
        )
        mocker.patch("importlib.metadata.entry_points", return_value=[])

        pm = XbtPluginManager()

        # Verify config was loaded
        assert pm._enabled_plugins == {"test_plugin"}

    def test_plugin_filtering_active(self, reset_plugin_manager, tmp_path, mocker):
        """Test that plugin filtering based on config actually works."""
        # Create config that disables a plugin
        config_file = tmp_path / "xbt.yml"
        config_file.write_text("disabled_plugins:\n  - bad_plugin\n")

        mocker.patch("pathlib.Path.cwd", return_value=tmp_path)

        from xbt.plugin_manager import XbtPluginManager

        mocker.patch.object(
            XbtPluginManager, "_find_config_file", return_value=config_file
        )
        mocker.patch("importlib.metadata.entry_points", return_value=[])

        pm = XbtPluginManager()

        # bad_plugin should not be allowed
        assert not pm._is_plugin_allowed("bad_plugin")
        # other plugins should be allowed
        assert pm._is_plugin_allowed("good_plugin")
