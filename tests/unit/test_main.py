"""Unit tests for main.py"""

from unittest.mock import Mock

import pytest

from xbt.main import main, match_dbt_exit_code


class TestMatchDbtExitCode:
    """Test exit code mapping logic."""

    def test_none_result_returns_1(self):
        """Test that None result returns exit code 1."""
        assert match_dbt_exit_code(None) == 1

    def test_successful_result_returns_0(self, mock_dbt_result):
        """Test that successful result returns exit code 0."""
        result = mock_dbt_result(success=True, exception=None)
        assert match_dbt_exit_code(result) == 0

    def test_failed_result_without_exception_returns_1(self, mock_dbt_result):
        """Test that failed result without exception returns exit code 1."""
        result = mock_dbt_result(success=False, exception=None)
        assert match_dbt_exit_code(result) == 1

    @pytest.mark.parametrize(
        "exception_class_name,error_message",
        [
            ("DbtUsageException", "Bad usage"),
            ("DbtProjectError", "Project error"),
            ("DbtRuntimeError", "Runtime error"),
            ("DbtDatabaseError", "Database error"),
            ("DbtCompilationError", "Compilation error"),
            ("DbtConfigError", "Config error"),
            ("DbtSchemaError", "Schema error"),
            ("DbtValidationError", "Validation error"),
        ],
    )
    def test_dbt_errors_return_exit_code_2(
        self, mock_dbt_result, exception_class_name, error_message
    ):
        """Test that dbt exceptions return exit code 2."""
        exception_class = type(exception_class_name, (Exception,), {})
        result = mock_dbt_result(
            success=False, exception=exception_class(error_message)
        )
        assert match_dbt_exit_code(result) == 2

    def test_other_exception_returns_1(self, mock_dbt_result):
        """Test that other exceptions return exit code 1."""
        result = mock_dbt_result(success=False, exception=ValueError("Some error"))
        assert match_dbt_exit_code(result) == 1

    def test_result_without_success_attribute_returns_1(self):
        """Test handling of result without success attribute."""
        result = Mock(spec=[])  # Mock with no attributes
        assert match_dbt_exit_code(result) == 1


class TestMainFunction:
    """Test main() function integration."""

    def test_main_successful_run(self, mocker, reset_plugin_manager, mock_dbt_result):
        """Test main() with successful dbt run."""
        # Mock sys.argv
        mocker.patch("sys.argv", ["xbt", "run"])

        # Mock xbtRunner
        mock_runner_instance = Mock()
        result = mock_dbt_result(success=True, exception=None)
        mock_runner_instance.invoke.return_value = result

        mock_runner_class = mocker.patch("xbt.main.xbtRunner")
        mock_runner_class.return_value = mock_runner_instance

        # Mock sys.exit to capture exit code
        mock_exit = mocker.patch("sys.exit")

        main()

        # Verify runner was created and invoked
        mock_runner_class.assert_called_once()
        mock_runner_instance.invoke.assert_called_once_with(["run"])

        # Verify correct exit code
        mock_exit.assert_called_once_with(0)

    def test_main_failed_run(self, mocker, reset_plugin_manager, mock_dbt_result):
        """Test main() with failed dbt run."""
        mocker.patch("sys.argv", ["xbt", "test"])

        mock_runner_instance = Mock()
        result = mock_dbt_result(success=False, exception=None)
        mock_runner_instance.invoke.return_value = result

        mock_runner_class = mocker.patch("xbt.main.xbtRunner")
        mock_runner_class.return_value = mock_runner_instance

        mock_exit = mocker.patch("sys.exit")

        main()

        # Verify exit code 1 for failure
        mock_exit.assert_called_once_with(1)

    def test_main_with_dbt_exception(
        self, mocker, reset_plugin_manager, mock_dbt_result
    ):
        """Test main() with dbt-specific exception."""
        mocker.patch("sys.argv", ["xbt", "run"])

        class DbtRuntimeError(Exception):
            pass

        mock_runner_instance = Mock()
        result = mock_dbt_result(success=False, exception=DbtRuntimeError("Error"))
        mock_runner_instance.invoke.return_value = result

        mock_runner_class = mocker.patch("xbt.main.xbtRunner")
        mock_runner_class.return_value = mock_runner_instance

        mock_exit = mocker.patch("sys.exit")

        main()

        # Verify exit code 2 for dbt exception
        mock_exit.assert_called_once_with(2)

    def test_main_usage_exception_prints_help(
        self, mocker, reset_plugin_manager, mock_dbt_result, capsys
    ):
        """Test that DbtUsageException prints usage information."""
        mocker.patch("sys.argv", ["xbt", "invalid"])

        class DbtUsageException(Exception):
            pass

        mock_runner_instance = Mock()
        result = mock_dbt_result(
            success=False, exception=DbtUsageException("Invalid command")
        )
        mock_runner_instance.invoke.return_value = result

        mock_runner_class = mocker.patch("xbt.main.xbtRunner")
        mock_runner_class.return_value = mock_runner_instance

        mock_exit = mocker.patch("sys.exit")

        main()

        # Capture stderr output
        captured = capsys.readouterr()

        # Verify usage message in stderr
        assert "Usage: xbt [OPTIONS] COMMAND [ARGS]..." in captured.err
        assert "Try 'xbt -h' for help." in captured.err
        assert "Invalid command" in captured.err

        # Verify exit code 2
        mock_exit.assert_called_once_with(2)

    def test_main_passes_all_args_to_runner(
        self, mocker, reset_plugin_manager, mock_dbt_result
    ):
        """Test that main() passes all command-line args to runner."""
        mocker.patch(
            "sys.argv", ["xbt", "run", "--models", "my_model", "--profile", "dev"]
        )

        mock_runner_instance = Mock()
        result = mock_dbt_result(success=True, exception=None)
        mock_runner_instance.invoke.return_value = result

        mock_runner_class = mocker.patch("xbt.main.xbtRunner")
        mock_runner_class.return_value = mock_runner_instance

        mocker.patch("sys.exit")

        main()

        # Verify all args (except program name) were passed
        mock_runner_instance.invoke.assert_called_once_with(
            ["run", "--models", "my_model", "--profile", "dev"]
        )

    def test_main_with_no_args(self, mocker, reset_plugin_manager, mock_dbt_result):
        """Test main() with no command-line arguments."""
        mocker.patch("sys.argv", ["xbt"])

        mock_runner_instance = Mock()
        result = mock_dbt_result(success=True, exception=None)
        mock_runner_instance.invoke.return_value = result

        mock_runner_class = mocker.patch("xbt.main.xbtRunner")
        mock_runner_class.return_value = mock_runner_instance

        mocker.patch("sys.exit")

        main()

        # Verify empty args list passed
        mock_runner_instance.invoke.assert_called_once_with([])

    def test_main_result_none(self, mocker, reset_plugin_manager):
        """Test main() when runner returns None."""
        mocker.patch("sys.argv", ["xbt", "run"])

        mock_runner_instance = Mock()
        mock_runner_instance.invoke.return_value = None

        mock_runner_class = mocker.patch("xbt.main.xbtRunner")
        mock_runner_class.return_value = mock_runner_instance

        mock_exit = mocker.patch("sys.exit")

        main()

        # Verify exit code 1 for None result
        mock_exit.assert_called_once_with(1)

    def test_main_no_exception_attribute(self, mocker, reset_plugin_manager):
        """Test handling of result without exception attribute."""
        mocker.patch("sys.argv", ["xbt", "run"])

        mock_runner_instance = Mock()
        result = Mock(spec=["success", "exception"])  # Has attributes but falsy
        result.success = False
        result.exception = None
        mock_runner_instance.invoke.return_value = result

        mock_runner_class = mocker.patch("xbt.main.xbtRunner")
        mock_runner_class.return_value = mock_runner_instance

        mock_exit = mocker.patch("sys.exit")

        main()

        # Should not crash, should return exit code 1
        mock_exit.assert_called_once_with(1)


class TestExitCodeMapping:
    """Test comprehensive exit code mapping scenarios."""

    @pytest.mark.parametrize(
        "exception_class_name,expected_code",
        [
            ("DbtUsageException", 2),
            ("DbtProjectError", 2),
            ("DbtRuntimeError", 2),
            ("DbtDatabaseError", 2),
            ("DbtCompilationError", 2),
            ("DbtConfigError", 2),
            ("DbtSchemaError", 2),
            ("DbtValidationError", 2),
            ("ValueError", 1),
            ("RuntimeError", 1),
            ("KeyError", 1),
        ],
    )
    def test_exit_code_for_exception_types(
        self, mock_dbt_result, exception_class_name, expected_code
    ):
        """Test exit codes for various exception types."""
        # Dynamically create exception class with the given name
        exception_class = type(exception_class_name, (Exception,), {})
        exception = exception_class("Test error")

        result = mock_dbt_result(success=False, exception=exception)
        assert match_dbt_exit_code(result) == expected_code
