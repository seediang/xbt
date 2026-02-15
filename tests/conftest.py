"""Shared fixtures for pytest tests."""

from pathlib import Path
from typing import Any, Dict, List
from unittest.mock import MagicMock, Mock

import pytest


@pytest.fixture
def reset_plugin_manager():
    """Reset the XbtPluginManager singleton before each test."""
    from xbt.plugin_manager import XbtPluginManager

    # Reset singleton instance
    XbtPluginManager._instance = None
    yield
    # Clean up after test
    XbtPluginManager._instance = None


@pytest.fixture
def mock_dbt_runner(mocker):
    """Mock dbtRunner.invoke() to avoid actual dbt execution."""
    mock_result = Mock()
    mock_result.success = True
    mock_result.exception = None

    mock_invoke = mocker.patch(
        "dbt.cli.main.dbtRunner.invoke", return_value=mock_result
    )
    return mock_invoke


@pytest.fixture
def mock_dbt_result():
    """Factory fixture for creating mock dbtRunnerResult objects."""

    def _create_result(success: bool = True, exception: Exception | None = None):
        result = Mock()
        result.success = success
        result.exception = exception
        return result

    return _create_result


@pytest.fixture
def temp_config_file(tmp_path):
    """Create a temporary xbt.yml config file with specified content."""

    def _create_config(
        content: Dict[str, Any] | None = None, location: Path | None = None
    ):
        import yaml

        target_dir = location if location else tmp_path
        config_path = target_dir / "xbt.yml"

        if content is not None:
            with open(config_path, "w") as f:
                yaml.dump(content, f)
        else:
            # Create empty file
            config_path.touch()

        return config_path

    return _create_config


@pytest.fixture
def mock_entry_points(mocker):
    """Mock importlib.metadata.entry_points() for plugin discovery."""

    def _create_entry_points(plugins: List[Dict[str, str]]):
        """
        Create mock entry points.

        Args:
            plugins: List of dicts with 'name', 'value', and optional 'module' keys
        """
        mock_eps = []
        for plugin_info in plugins:
            ep = Mock()
            ep.name = plugin_info["name"]
            ep.value = plugin_info["value"]
            ep.group = "xbt"

            # Mock the load() method to return a module
            if "module" in plugin_info:
                ep.load.return_value = plugin_info["module"]
            else:
                mock_module = Mock()
                ep.load.return_value = mock_module

            mock_eps.append(ep)

        # Mock for Python 3.10+ (with group parameter)
        mocker.patch("importlib.metadata.entry_points", return_value=mock_eps)

        return mock_eps

    return _create_entry_points


@pytest.fixture
def mock_cli_group():
    """Mock Click CLI group for command registration tests."""
    cli_group = MagicMock()
    cli_group.name = "xbt"
    return cli_group


@pytest.fixture
def mock_cli_with_command_tracking():
    """Mock CLI with command registration tracking for plugin_command tests."""
    mock_cli = MagicMock()
    registered_commands = {}

    def mock_command(name):
        def decorator(func):
            registered_commands[name] = func
            return func

        return decorator

    mock_plugin_group = MagicMock()
    mock_plugin_group.command = mock_command

    def mock_group(name):
        def decorator(func):
            func()  # Execute to register subcommands
            return mock_plugin_group

        return decorator

    mock_cli.group = mock_group
    return mock_cli, registered_commands


@pytest.fixture(autouse=True)
def _setup_xbt_runner_mocks(mocker, request):
    """Auto-setup common mocks for xbt_runner tests."""
    # Only apply to xbt_runner tests
    if "test_xbt_runner" in request.node.nodeid:
        mocker.patch("pathlib.Path.cwd", return_value=Path("/tmp"))
        mocker.patch("pathlib.Path.glob", return_value=[])
        mocker.patch("importlib.metadata.entry_points", return_value=[])
        mocker.patch("dbt.cli.main.dbtRunner.__init__", return_value=None)


@pytest.fixture
def dbt_project_dir():
    """Return the path to the fixture dbt project."""
    fixture_path = Path(__file__).parent / "fixtures" / "dbt_project"
    return fixture_path


@pytest.fixture
def dbt_temp_dir(tmp_path, dbt_project_dir):
    """Set up temporary directory for dbt and create profiles.yml with correct path."""
    import os

    # Create a temporary dbt home directory
    dbt_home = tmp_path / "dbt_home"
    dbt_home.mkdir(parents=True, exist_ok=True)

    # Path for DuckDB database
    db_path = tmp_path / "test.duckdb"

    # Read profiles template and replace placeholder
    profiles_template = dbt_project_dir / "profiles.yml"
    profiles_content = profiles_template.read_text()
    profiles_content = profiles_content.replace(
        "[dbt_db_path]", str(db_path).replace("\\", "/")
    )

    # Write to temp dbt home
    profiles_dir = dbt_home / "dbt" / "profiles.yml"
    profiles_dir.parent.mkdir(parents=True, exist_ok=True)
    profiles_dir.write_text(profiles_content)

    # Set environment variable to use temp profiles
    os.environ["DBT_PROFILES_DIR"] = str(dbt_home / "dbt")

    yield dbt_home, db_path, dbt_project_dir

    # Cleanup
    if "DBT_PROFILES_DIR" in os.environ:
        del os.environ["DBT_PROFILES_DIR"]
