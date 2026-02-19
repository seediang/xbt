"""Tests for hook context classes."""

from pathlib import Path

from xbt.plugins import InitContext, PostInvokeContext, PreInvokeContext


class TestInitContext:
    """Tests for the InitContext class."""

    def test_context_creation(self):
        """Test creating an InitContext with shared fields."""
        project_dir = Path("/path/to/project")
        workspace_root = Path("/path/to")

        context = InitContext(
            project_dir=project_dir,
            workspace_root=workspace_root,
            registered_dbt_commands=set(),
            registered_plugin_commands=set(),
            registered_builtin_commands=set(),
        )

        assert context.project_dir == project_dir
        assert context.workspace_root == workspace_root

    def test_has_project_true(self, tmp_path):
        """Test has_project returns True when project_dir exists."""
        context = InitContext(
            project_dir=tmp_path,
            workspace_root=tmp_path.parent,
            registered_dbt_commands=set(),
            registered_plugin_commands=set(),
            registered_builtin_commands=set(),
        )

        assert context.has_project is True

    def test_has_project_false_none(self):
        """Test has_project returns False when project_dir is None."""
        context = InitContext(
            project_dir=None,
            workspace_root=Path.cwd(),
            registered_dbt_commands=set(),
            registered_plugin_commands=set(),
            registered_builtin_commands=set(),
        )

        assert context.has_project is False

    def test_has_project_false_not_exists(self, tmp_path):
        """Test has_project returns False when project_dir doesn't exist."""
        nonexistent = tmp_path / "does" / "not" / "exist"

        context = InitContext(
            project_dir=nonexistent,
            workspace_root=tmp_path,
            registered_dbt_commands=set(),
            registered_plugin_commands=set(),
            registered_builtin_commands=set(),
        )

        assert context.has_project is False


class TestPreInvokeContext:
    """Tests for the PreInvokeContext class."""

    def test_context_creation(self):
        """Test creating a PreInvokeContext with command and args."""
        project_dir = Path("/path/to/project")
        workspace_root = Path("/path/to")

        context = PreInvokeContext(
            args=["run"],
            command="run",
            project_dir=project_dir,
            workspace_root=workspace_root,
            registered_dbt_commands=set(),
            registered_plugin_commands=set(),
            registered_builtin_commands=set(),
        )

        assert context.args == ["run"]
        assert context.command == "run"
        assert context.project_dir == project_dir
        assert context.workspace_root == workspace_root

    def test_context_args_immutability(self):
        """Test that modifying context args doesn't affect original args."""
        original_args = ["run", "model1"]

        context = PreInvokeContext(
            args=original_args.copy(),
            command="run",
            project_dir=None,
            workspace_root=Path.cwd(),
            registered_dbt_commands=set(),
            registered_plugin_commands=set(),
            registered_builtin_commands=set(),
        )

        context.args.append("model2")

        assert original_args == ["run", "model1"]

    def test_is_builtin_command_true(self):
        """Test is_builtin_command returns True for built-in commands."""
        for cmd in ["plugin", "plugins"]:
            context = PreInvokeContext(
                args=[cmd],
                command=cmd,
                project_dir=None,
                workspace_root=Path.cwd(),
                registered_dbt_commands=set(),
                registered_plugin_commands={cmd},
                registered_builtin_commands={cmd},
            )
            assert context.is_builtin_command is True

    def test_is_builtin_command_false(self):
        """Test is_builtin_command returns False for dbt commands."""
        context = PreInvokeContext(
            args=["run"],
            command="run",
            project_dir=None,
            workspace_root=Path.cwd(),
            registered_dbt_commands={"run"},
            registered_plugin_commands=set(),
            registered_builtin_commands=set(),
        )
        assert context.is_builtin_command is False

    def test_is_dbt_command_true(self):
        """Test is_dbt_command returns True for known dbt commands."""
        dbt_commands = ["run", "test", "compile", "parse", "seed", "snapshot", "build"]
        for cmd in dbt_commands:
            context = PreInvokeContext(
                args=[cmd],
                command=cmd,
                project_dir=None,
                workspace_root=Path.cwd(),
                registered_dbt_commands=set(dbt_commands),
                registered_plugin_commands=set(),
                registered_builtin_commands=set(),
            )
            assert context.is_dbt_command is True, f"Failed for command: {cmd}"

    def test_is_dbt_command_false(self):
        """Test is_dbt_command returns False for non-dbt commands."""
        context = PreInvokeContext(
            args=["custom"],
            command="custom",
            project_dir=None,
            workspace_root=Path.cwd(),
            registered_dbt_commands={"run", "test"},
            registered_plugin_commands=set(),
            registered_builtin_commands=set(),
        )
        assert context.is_dbt_command is False

    def test_is_dbt_command_none(self):
        """Test is_dbt_command returns False when command is None."""
        context = PreInvokeContext(
            args=[],
            command=None,
            project_dir=None,
            workspace_root=Path.cwd(),
            registered_dbt_commands=set(),
            registered_plugin_commands=set(),
            registered_builtin_commands=set(),
        )
        assert context.is_dbt_command is False

    def test_is_xbt_command_true(self):
        """Test is_xbt_command returns True for xbt/plugin-added commands."""
        context = PreInvokeContext(
            args=["custom"],
            command="custom",
            project_dir=None,
            workspace_root=Path.cwd(),
            registered_dbt_commands=set(),
            registered_plugin_commands={"custom"},
            registered_builtin_commands=set(),
        )
        assert context.is_xbt_command is True

    def test_is_xbt_command_false_dbt(self):
        """Test is_xbt_command returns False for dbt commands."""
        context = PreInvokeContext(
            args=["run"],
            command="run",
            project_dir=None,
            workspace_root=Path.cwd(),
            registered_dbt_commands={"run"},
            registered_plugin_commands=set(),
            registered_builtin_commands=set(),
        )
        assert context.is_xbt_command is False

    def test_is_xbt_command_true_builtin(self):
        """Test is_xbt_command returns True for built-in commands."""
        context = PreInvokeContext(
            args=["plugin"],
            command="plugin",
            project_dir=None,
            workspace_root=Path.cwd(),
            registered_dbt_commands=set(),
            registered_plugin_commands={"plugin"},
            registered_builtin_commands={"plugin"},
        )
        assert context.is_xbt_command is True

    def test_is_xbt_command_none(self):
        """Test is_xbt_command returns False when command is None."""
        context = PreInvokeContext(
            args=[],
            command=None,
            project_dir=None,
            workspace_root=Path.cwd(),
            registered_dbt_commands=set(),
            registered_plugin_commands=set(),
            registered_builtin_commands=set(),
        )
        assert context.is_xbt_command is False


class TestPostInvokeContext:
    """Tests for the PostInvokeContext class."""

    def test_context_with_result(self):
        """Test context holds a result object."""
        mock_result = {"success": True}

        context = PostInvokeContext(
            args=["run"],
            command="run",
            project_dir=None,
            workspace_root=Path.cwd(),
            registered_dbt_commands=set(),
            registered_plugin_commands=set(),
            registered_builtin_commands=set(),
            result=mock_result,
        )

        assert context.result == mock_result
        assert context.result["success"] is True


class TestDynamicCommandClassification:
    """Tests for dynamic command classification with registered commands."""

    def test_is_dbt_command_with_registered_dbt_commands(self):
        """Test is_dbt_command uses registered_dbt_commands when available."""
        dbt_commands = {"run", "test", "compile"}
        context = PreInvokeContext(
            args=["run"],
            command="run",
            project_dir=None,
            workspace_root=Path.cwd(),
            registered_dbt_commands=dbt_commands,
            registered_plugin_commands=set(),
            registered_builtin_commands=set(),
        )
        assert context.is_dbt_command is True

    def test_is_dbt_command_false_with_registered_commands(self):
        """Test is_dbt_command returns False for unlisted commands."""
        dbt_commands = {"run", "test"}
        context = PreInvokeContext(
            args=["custom"],
            command="custom",
            project_dir=None,
            workspace_root=Path.cwd(),
            registered_dbt_commands=dbt_commands,
            registered_plugin_commands=set(),
            registered_builtin_commands=set(),
        )
        assert context.is_dbt_command is False

    def test_is_xbt_command_with_registered_plugin_commands(self):
        """Test is_xbt_command uses registered_plugin_commands when available."""
        plugin_commands = {"notify", "slack"}
        context = PreInvokeContext(
            args=["notify"],
            command="notify",
            project_dir=None,
            workspace_root=Path.cwd(),
            registered_dbt_commands=set(),
            registered_plugin_commands=plugin_commands,
            registered_builtin_commands=set(),
        )
        assert context.is_xbt_command is True

    def test_is_xbt_command_false_when_not_in_plugin_commands(self):
        """Test is_xbt_command returns False when command not in registered_plugin_commands."""
        plugin_commands = {"notify", "slack"}
        context = PreInvokeContext(
            args=["run"],
            command="run",
            project_dir=None,
            workspace_root=Path.cwd(),
            registered_dbt_commands={"run", "test"},
            registered_plugin_commands=plugin_commands,
            registered_builtin_commands=set(),
        )
        assert context.is_xbt_command is False

    def test_dynamic_classification_priority(self):
        """Test classification priority: plugin > dbt > xbt across contexts."""
        dbt_cmds = {"run", "test"}
        plugin_cmds = {"notify", "plugin"}

        dbt_context = PreInvokeContext(
            args=["run"],
            command="run",
            project_dir=None,
            workspace_root=Path.cwd(),
            registered_dbt_commands=dbt_cmds,
            registered_plugin_commands=plugin_cmds,
            registered_builtin_commands=set(),
        )
        assert dbt_context.is_dbt_command is True
        assert dbt_context.is_xbt_command is False
        assert dbt_context.is_builtin_command is False

        plugin_context = PreInvokeContext(
            args=["notify"],
            command="notify",
            project_dir=None,
            workspace_root=Path.cwd(),
            registered_dbt_commands=dbt_cmds,
            registered_plugin_commands=plugin_cmds,
            registered_builtin_commands=set(),
        )
        assert plugin_context.is_dbt_command is False
        assert plugin_context.is_xbt_command is True
        assert plugin_context.is_builtin_command is False

        mgmt_context = PreInvokeContext(
            args=["plugin"],
            command="plugin",
            project_dir=None,
            workspace_root=Path.cwd(),
            registered_dbt_commands=dbt_cmds,
            registered_plugin_commands=plugin_cmds,
            registered_builtin_commands={"plugin"},
        )
        assert mgmt_context.is_dbt_command is False
        assert mgmt_context.is_xbt_command is True
        assert mgmt_context.is_builtin_command is True
