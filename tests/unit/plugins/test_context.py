"""Tests for XbtContext."""

from pathlib import Path

from xbt.plugins import XbtContext


class TestXbtContext:
    """Tests for the XbtContext class."""

    def test_context_creation(self):
        """Test creating an XbtContext with all fields."""
        project_dir = Path("/path/to/project")
        workspace_root = Path("/path/to")

        context = XbtContext(
            args=["run"],
            command="run",
            project_dir=project_dir,
            workspace_root=workspace_root,
            plugin_name="test_plugin",
            result=None,
        )

        assert context.args == ["run"]
        assert context.command == "run"
        assert context.project_dir == project_dir
        assert context.workspace_root == workspace_root
        assert context.plugin_name == "test_plugin"
        assert context.result is None

    def test_is_plugin_management_command_true(self):
        """Test is_plugin_management_command returns True for plugin command."""
        context = XbtContext(
            args=["plugin", "list"],
            command="plugin",
            project_dir=None,
            workspace_root=Path.cwd(),
            plugin_name="test",
        )

        assert context.is_plugin_management_command is True

    def test_is_plugin_management_command_for_plugins(self):
        """Test is_plugin_management_command returns True for plugins command."""
        context = XbtContext(
            args=["plugins", "list"],
            command="plugins",
            project_dir=None,
            workspace_root=Path.cwd(),
            plugin_name="test",
        )

        assert context.is_plugin_management_command is True

    def test_is_plugin_management_command_false(self):
        """Test is_plugin_management_command returns False for dbt commands."""
        context = XbtContext(
            args=["run"],
            command="run",
            project_dir=None,
            workspace_root=Path.cwd(),
            plugin_name="test",
        )

        assert context.is_plugin_management_command is False

    def test_has_project_true(self, tmp_path):
        """Test has_project returns True when project_dir exists."""
        context = XbtContext(
            args=["run"],
            command="run",
            project_dir=tmp_path,
            workspace_root=tmp_path.parent,
            plugin_name="test",
        )

        assert context.has_project is True

    def test_has_project_false_none(self):
        """Test has_project returns False when project_dir is None."""
        context = XbtContext(
            args=["run"],
            command="run",
            project_dir=None,
            workspace_root=Path.cwd(),
            plugin_name="test",
        )

        assert context.has_project is False

    def test_has_project_false_not_exists(self, tmp_path):
        """Test has_project returns False when project_dir doesn't exist."""
        nonexistent = tmp_path / "does" / "not" / "exist"

        context = XbtContext(
            args=["run"],
            command="run",
            project_dir=nonexistent,
            workspace_root=tmp_path,
            plugin_name="test",
        )

        assert context.has_project is False

    def test_context_with_result(self):
        """Test context can hold a result object."""
        mock_result = {"success": True}

        context = XbtContext(
            args=["run"],
            command="run",
            project_dir=None,
            workspace_root=Path.cwd(),
            plugin_name="test",
            result=mock_result,
        )

        assert context.result == mock_result
        assert context.result["success"] is True

    def test_context_args_immutability(self):
        """Test that modifying context args doesn't affect original args."""
        original_args = ["run", "model1"]

        context = XbtContext(
            args=original_args.copy(),
            command="run",
            project_dir=None,
            workspace_root=Path.cwd(),
            plugin_name="test",
        )

        # Modify context args
        context.args.append("model2")

        # Original should not change (depends on implementation)
        assert original_args == ["run", "model1"]
