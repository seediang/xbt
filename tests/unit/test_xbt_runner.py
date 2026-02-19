"""Unit tests for xbt_runner.py"""

from unittest.mock import Mock

from xbt.xbt_runner import xbtRunner


class TestXbtRunnerInitialization:
    """Test xbtRunner initialization."""

    def test_init_without_callbacks(self, reset_plugin_manager, mocker, mock_cli_group):
        """Test initialization without callbacks parameter."""
        # Mock the CLI
        mocker.patch("xbt.xbt_runner.cli", mock_cli_group)

        xbtRunner()

        # Verify CLI name was changed
        assert mock_cli_group.name == "xbt"

    def test_init_with_callbacks(self, reset_plugin_manager, mocker, mock_cli_group):
        """Test initialization with callbacks parameter."""
        mocker.patch("xbt.xbt_runner.cli", mock_cli_group)

        # Mock dbtRunner.__init__
        mock_super_init = mocker.patch(
            "dbt.cli.main.dbtRunner.__init__", return_value=None
        )

        provided_callback = Mock()
        xbtRunner(callbacks=[provided_callback])

        # Verify callbacks were passed to parent
        mock_super_init.assert_called_once()
        call_kwargs = mock_super_init.call_args.kwargs
        assert "callbacks" in call_kwargs
        assert provided_callback in call_kwargs["callbacks"]

    def test_init_empty_callbacks_list_becomes_none(
        self, reset_plugin_manager, mocker, mock_cli_group
    ):
        """Test that empty callbacks list is converted to None."""
        mocker.patch("xbt.xbt_runner.cli", mock_cli_group)

        # Mock plugin manager to return no callbacks
        mock_pm = Mock()
        mock_pm.hook_register_callbacks.return_value = []
        mocker.patch(
            "xbt.plugin_manager.XbtPluginManager.get_instance", return_value=mock_pm
        )

        # Mock dbtRunner.__init__
        mock_super_init = mocker.patch(
            "dbt.cli.main.dbtRunner.__init__", return_value=None
        )

        xbtRunner()

        # Verify None was passed (not empty list)
        call_kwargs = mock_super_init.call_args.kwargs
        assert call_kwargs["callbacks"] is None

    def test_init_calls_plugin_manager_hooks(
        self, reset_plugin_manager, mocker, mock_cli_group
    ):
        """Test that plugin manager registration hooks are called."""
        mocker.patch("xbt.xbt_runner.cli", mock_cli_group)

        # Mock plugin manager
        mock_pm = Mock()
        mock_pm.hook_register_callbacks.return_value = []
        mocker.patch(
            "xbt.plugin_manager.XbtPluginManager.get_instance", return_value=mock_pm
        )

        xbtRunner()

        # Verify hooks were called
        # hook_register_commands should be called with cli_group and context
        assert mock_pm.hook_register_commands.call_count == 1
        call_args = mock_pm.hook_register_commands.call_args
        assert call_args[1]["cli_group"] == mock_cli_group
        assert call_args[1]["context"] is not None  # Should have context

        # hook_register_callbacks should be called
        assert mock_pm.hook_register_callbacks.call_count == 1


class TestCallbackMerging:
    """Test callback merging logic."""

    def test_merge_provided_and_plugin_callbacks(
        self, reset_plugin_manager, mocker, mock_cli_group
    ):
        """Test that provided callbacks and plugin callbacks are merged."""
        mocker.patch("xbt.xbt_runner.cli", mock_cli_group)

        # Mock plugin manager to return plugin callbacks
        plugin_callback1 = Mock()
        plugin_callback2 = Mock()
        mock_pm = Mock()
        mock_pm.hook_register_callbacks.return_value = [
            plugin_callback1,
            plugin_callback2,
        ]
        mocker.patch(
            "xbt.plugin_manager.XbtPluginManager.get_instance", return_value=mock_pm
        )

        # Mock dbtRunner.__init__
        mock_super_init = mocker.patch(
            "dbt.cli.main.dbtRunner.__init__", return_value=None
        )

        provided_callback = Mock()
        xbtRunner(callbacks=[provided_callback])

        # Verify all callbacks were passed
        call_kwargs = mock_super_init.call_args.kwargs
        callbacks = call_kwargs["callbacks"]
        assert provided_callback in callbacks
        assert plugin_callback1 in callbacks
        assert plugin_callback2 in callbacks
        assert len(callbacks) == 3

    def test_plugin_callbacks_only(self, reset_plugin_manager, mocker, mock_cli_group):
        """Test with only plugin callbacks (no provided callbacks)."""
        mocker.patch("xbt.xbt_runner.cli", mock_cli_group)

        # Mock plugin manager to return plugin callbacks
        plugin_callback = Mock()
        mock_pm = Mock()
        mock_pm.hook_register_callbacks.return_value = [plugin_callback]
        mocker.patch(
            "xbt.plugin_manager.XbtPluginManager.get_instance", return_value=mock_pm
        )

        # Mock dbtRunner.__init__
        mock_super_init = mocker.patch(
            "dbt.cli.main.dbtRunner.__init__", return_value=None
        )

        xbtRunner()

        # Verify plugin callbacks were passed
        call_kwargs = mock_super_init.call_args.kwargs
        callbacks = call_kwargs["callbacks"]
        assert plugin_callback in callbacks
        assert len(callbacks) == 1


class TestInvokeMethod:
    """Test the invoke method and hook execution."""

    def test_invoke_calls_pre_hook(self, reset_plugin_manager, mocker, mock_cli_group):
        """Test that invoke calls hook_pre_invoke before dbt execution."""
        mocker.patch("xbt.xbt_runner.cli", mock_cli_group)

        # Mock plugin manager
        mock_pm = Mock()
        mock_pm.hook_register_callbacks.return_value = []
        mock_pm.hook_pre_invoke.return_value = ["modified", "args"]
        mocker.patch(
            "xbt.plugin_manager.XbtPluginManager.get_instance", return_value=mock_pm
        )

        # Mock parent invoke
        mock_result = Mock()
        mock_result.success = True
        mock_super_invoke = mocker.patch(
            "dbt.cli.main.dbtRunner.invoke", return_value=mock_result
        )

        runner = xbtRunner()
        runner.invoke(["original", "args"])

        # Verify pre_invoke was called with original args and context
        call_args = mock_pm.hook_pre_invoke.call_args
        assert call_args[1]["args"] == ["original", "args"]
        assert call_args[1]["context"] is not None
        assert (
            call_args[1]["context"].command == "original"
        )  # should extract "original" as command

        # Verify parent invoke was called with modified args
        mock_super_invoke.assert_called_once_with(["modified", "args"])

    def test_invoke_calls_post_hook(self, reset_plugin_manager, mocker, mock_cli_group):
        """Test that invoke calls hook_post_invoke after dbt execution."""
        mocker.patch("xbt.xbt_runner.cli", mock_cli_group)

        # Mock plugin manager
        mock_pm = Mock()
        mock_pm.hook_register_callbacks.return_value = []
        mock_pm.hook_pre_invoke.return_value = ["test", "args"]
        mocker.patch(
            "xbt.plugin_manager.XbtPluginManager.get_instance", return_value=mock_pm
        )

        # Mock parent invoke
        mock_result = Mock()
        mock_result.success = True
        mocker.patch("dbt.cli.main.dbtRunner.invoke", return_value=mock_result)

        runner = xbtRunner()
        runner.invoke(["test", "args"])

        # Verify post_invoke was called with args, result, and context
        call_args = mock_pm.hook_post_invoke.call_args
        assert call_args[1]["args"] == ["test", "args"]
        assert call_args[1]["result"] == mock_result
        assert call_args[1]["context"] is not None
        assert (
            call_args[1]["context"].result == mock_result
        )  # context should include result

    def test_invoke_hook_execution_order(
        self, reset_plugin_manager, mocker, mock_cli_group
    ):
        """Test that hooks execute in correct order: pre -> dbt -> post."""
        mocker.patch("xbt.xbt_runner.cli", mock_cli_group)

        # Track call order
        call_order = []

        # Mock plugin manager
        mock_pm = Mock()
        mock_pm.hook_register_callbacks.return_value = []
        mock_pm.hook_pre_invoke.side_effect = lambda args, context=None: (
            call_order.append("pre"),
            args,
        )[1]
        mock_pm.hook_post_invoke.side_effect = lambda args, result, context=None: (
            call_order.append("post")
        )
        mocker.patch(
            "xbt.plugin_manager.XbtPluginManager.get_instance", return_value=mock_pm
        )

        # Mock parent invoke
        mock_result = Mock()
        mock_result.success = True
        mocker.patch(
            "dbt.cli.main.dbtRunner.invoke",
            side_effect=lambda args, **kwargs: (call_order.append("dbt"), mock_result)[
                1
            ],
        )

        runner = xbtRunner()
        runner.invoke(["test"])

        # Verify execution order
        assert call_order == ["pre", "dbt", "post"]

    def test_invoke_returns_result(self, reset_plugin_manager, mocker, mock_cli_group):
        """Test that invoke returns the dbt result."""
        mocker.patch("xbt.xbt_runner.cli", mock_cli_group)

        # Mock plugin manager
        mock_pm = Mock()
        mock_pm.hook_register_callbacks.return_value = []
        mock_pm.hook_pre_invoke.return_value = ["test"]
        mocker.patch(
            "xbt.plugin_manager.XbtPluginManager.get_instance", return_value=mock_pm
        )

        # Mock parent invoke
        mock_result = Mock()
        mock_result.success = True
        mock_result.exception = None
        mocker.patch("dbt.cli.main.dbtRunner.invoke", return_value=mock_result)

        runner = xbtRunner()
        result = runner.invoke(["test"])

        # Verify result is returned
        assert result is mock_result
        assert result.success is True

    def test_invoke_with_kwargs(self, reset_plugin_manager, mocker, mock_cli_group):
        """Test that invoke passes through kwargs to parent."""
        mocker.patch("xbt.xbt_runner.cli", mock_cli_group)

        # Mock plugin manager
        mock_pm = Mock()
        mock_pm.hook_register_callbacks.return_value = []
        mock_pm.hook_pre_invoke.return_value = ["test"]
        mocker.patch(
            "xbt.plugin_manager.XbtPluginManager.get_instance", return_value=mock_pm
        )

        # Mock parent invoke
        mock_result = Mock()
        mock_super_invoke = mocker.patch(
            "dbt.cli.main.dbtRunner.invoke", return_value=mock_result
        )

        runner = xbtRunner()
        runner.invoke(["test"], custom_kwarg="value")

        # Verify kwargs were passed through
        mock_super_invoke.assert_called_once_with(["test"], custom_kwarg="value")


class TestArgsModification:
    """Test argument modification through pre_invoke hook."""

    def test_args_modification_passed_to_dbt(
        self, reset_plugin_manager, mocker, mock_cli_group
    ):
        """Test that modified args from pre_invoke are passed to dbt."""
        mocker.patch("xbt.xbt_runner.cli", mock_cli_group)

        # Mock plugin manager to modify args
        mock_pm = Mock()
        mock_pm.hook_register_callbacks.return_value = []
        mock_pm.hook_pre_invoke.return_value = ["run", "--profile", "dev"]
        mocker.patch(
            "xbt.plugin_manager.XbtPluginManager.get_instance", return_value=mock_pm
        )

        # Mock parent invoke
        mock_result = Mock()
        mock_super_invoke = mocker.patch(
            "dbt.cli.main.dbtRunner.invoke", return_value=mock_result
        )

        runner = xbtRunner()
        runner.invoke(["run"])

        # Verify modified args were passed to parent
        mock_super_invoke.assert_called_once_with(["run", "--profile", "dev"])

    def test_unmodified_args_when_pre_hook_returns_same(
        self, reset_plugin_manager, mocker, mock_cli_group
    ):
        """Test that args remain unchanged if pre_invoke returns them unchanged."""
        mocker.patch("xbt.xbt_runner.cli", mock_cli_group)

        # Mock plugin manager to return same args
        mock_pm = Mock()
        mock_pm.hook_register_callbacks.return_value = []
        mock_pm.hook_pre_invoke.return_value = ["test", "cmd"]
        mocker.patch(
            "xbt.plugin_manager.XbtPluginManager.get_instance", return_value=mock_pm
        )

        # Mock parent invoke
        mock_result = Mock()
        mock_super_invoke = mocker.patch(
            "dbt.cli.main.dbtRunner.invoke", return_value=mock_result
        )

        runner = xbtRunner()
        runner.invoke(["test", "cmd"])

        # Verify same args passed through
        mock_super_invoke.assert_called_once_with(["test", "cmd"])


class TestManifestParameter:
    """Test manifest parameter handling."""

    def test_init_with_manifest(self, reset_plugin_manager, mocker, mock_cli_group):
        """Test initialization with manifest parameter."""
        mocker.patch("xbt.xbt_runner.cli", mock_cli_group)

        # Mock dbtRunner.__init__
        mock_super_init = mocker.patch(
            "dbt.cli.main.dbtRunner.__init__", return_value=None
        )

        mock_manifest = Mock()
        xbtRunner(manifest=mock_manifest)

        # Verify manifest was passed to parent
        call_kwargs = mock_super_init.call_args.kwargs
        assert call_kwargs["manifest"] is mock_manifest
