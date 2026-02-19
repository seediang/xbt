"""Tests for plugin utilities."""

from xbt.plugins import (
    find_dbt_project_dir,
    find_workspace_root,
    format_status_message,
    get_dbt_command,
    is_command_in_set,
)


class TestGetDbtCommand:
    """Tests for get_dbt_command utility."""

    def test_simple_command(self):
        """Test extracting a simple command."""
        assert get_dbt_command(["run"]) == "run"
        assert get_dbt_command(["test"]) == "test"
        assert get_dbt_command(["compile"]) == "compile"

    def test_command_with_options(self):
        """Test extracting command with options."""
        assert get_dbt_command(["run", "--select", "model1"]) == "run"
        assert get_dbt_command(["test", "--models", "model1"]) == "test"

    def test_flags_before_command(self):
        """Test with flags before the command."""
        assert get_dbt_command(["--debug", "run"]) == "run"
        assert get_dbt_command(["--verbose", "test"]) == "test"

    def test_project_dir_flag(self):
        """Test with --project-dir flag."""
        assert get_dbt_command(["--project-dir", ".", "run"]) == "run"
        assert get_dbt_command(["--profiles-dir", "./profiles", "test"]) == "test"

    def test_empty_args(self):
        """Test with empty args."""
        assert get_dbt_command([]) is None

    def test_only_flags(self):
        """Test with only flags, no command."""
        assert get_dbt_command(["--debug"]) is None
        assert get_dbt_command(["--verbose"]) is None
        assert get_dbt_command(["--quiet"]) is None

    def test_complex_scenario(self):
        """Test complex real-world scenario."""
        args = [
            "--project-dir",
            "./my_project",
            "-d",
            "run",
            "--select",
            "tag:daily",
            "--models",
            "+my_model",
            "--threads",
            "4",
        ]
        assert get_dbt_command(args) == "run"


class TestIsCommandInSet:
    """Tests for is_command_in_set utility."""

    def test_command_in_set(self):
        """Test command is in set."""
        assert is_command_in_set("run", {"run", "test"}) is True
        assert is_command_in_set("test", {"run", "test"}) is True

    def test_command_not_in_set(self):
        """Test command not in set."""
        assert is_command_in_set("run", {"test", "compile"}) is False
        assert is_command_in_set("compile", {"run", "test"}) is False

    def test_case_insensitive(self):
        """Test case-insensitive matching."""
        assert is_command_in_set("RUN", {"run", "test"}) is True
        assert is_command_in_set("Run", {"run", "test"}) is True
        assert is_command_in_set("run", {"RUN", "TEST"}) is True

    def test_none_command(self):
        """Test with None command."""
        assert is_command_in_set(None, {"run", "test"}) is False

    def test_empty_set(self):
        """Test with empty set."""
        assert is_command_in_set("run", set()) is False

    def test_single_item_set(self):
        """Test with single-item set."""
        assert is_command_in_set("run", {"run"}) is True
        assert is_command_in_set("test", {"run"}) is False


class TestFindDbtProjectDir:
    """Tests for find_dbt_project_dir utility."""

    def test_find_project_in_current_dir(self, tmp_path):
        """Test finding dbt_project.yml in current directory."""
        project_file = tmp_path / "dbt_project.yml"
        project_file.touch()

        result = find_dbt_project_dir(tmp_path)
        assert result == tmp_path

    def test_find_project_in_parent_dir(self, tmp_path):
        """Test finding dbt_project.yml in parent directory."""
        models_dir = tmp_path / "models"
        models_dir.mkdir()

        project_file = tmp_path / "dbt_project.yml"
        project_file.touch()

        result = find_dbt_project_dir(models_dir)
        assert result == tmp_path

    def test_find_project_multiple_levels_up(self, tmp_path):
        """Test finding dbt_project.yml multiple directories up."""
        deep_dir = tmp_path / "a" / "b" / "c" / "d"
        deep_dir.mkdir(parents=True)

        project_file = tmp_path / "dbt_project.yml"
        project_file.touch()

        result = find_dbt_project_dir(deep_dir)
        assert result == tmp_path

    def test_project_not_found(self, tmp_path):
        """Test when dbt_project.yml is not found."""
        result = find_dbt_project_dir(tmp_path)
        assert result is None

    def test_find_project_cwd(self, tmp_path, monkeypatch):
        """Test finding project from current working directory."""
        project_file = tmp_path / "dbt_project.yml"
        project_file.touch()

        monkeypatch.chdir(tmp_path)
        result = find_dbt_project_dir()
        assert result == tmp_path

    def test_find_project_prefers_closest(self, tmp_path):
        """Test that search stops at first (closest) found project."""
        parent_project = tmp_path / "dbt_project.yml"
        parent_project.touch()

        child_dir = tmp_path / "child"
        child_dir.mkdir()
        child_project = child_dir / "dbt_project.yml"
        child_project.touch()

        # Starting from child, should find child's project
        result = find_dbt_project_dir(child_dir)
        assert result == child_dir


class TestFindWorkspaceRoot:
    """Tests for find_workspace_root utility."""

    def test_find_workspace_with_git(self, tmp_path):
        """Test finding workspace root with .git."""
        git_dir = tmp_path / ".git"
        git_dir.mkdir()

        result = find_workspace_root(tmp_path)
        assert result == tmp_path

    def test_find_workspace_with_pyproject(self, tmp_path):
        """Test finding workspace root with pyproject.toml."""
        pyproject = tmp_path / "pyproject.toml"
        pyproject.touch()

        result = find_workspace_root(tmp_path)
        assert result == tmp_path

    def test_find_workspace_with_dbt_project(self, tmp_path):
        """Test finding workspace root with dbt_project.yml."""
        dbt_project = tmp_path / "dbt_project.yml"
        dbt_project.touch()

        result = find_workspace_root(tmp_path)
        assert result == tmp_path

    def test_find_workspace_in_subdirs(self, tmp_path):
        """Test finding workspace root from subdirectory."""
        git_dir = tmp_path / ".git"
        git_dir.mkdir()

        subdir = tmp_path / "src" / "xbt"
        subdir.mkdir(parents=True)

        result = find_workspace_root(subdir)
        assert result == tmp_path

    def test_workspace_not_found(self, tmp_path):
        """Test when no markers are found."""
        result = find_workspace_root(tmp_path)
        assert result == tmp_path  # Returns start_dir if not found

    def test_workspace_with_custom_markers(self, tmp_path):
        """Test workspace root with custom markers."""
        custom_marker = tmp_path / "WORKSPACE"
        custom_marker.touch()

        subdir = tmp_path / "src"
        subdir.mkdir()

        result = find_workspace_root(subdir, markers=["WORKSPACE"])
        assert result == tmp_path

    def test_workspace_respects_max_depth(self, tmp_path):
        """Test that max_depth limits search."""
        # Create deep nested directory
        deep_dir = tmp_path / "a" / "b" / "c" / "d" / "e"
        deep_dir.mkdir(parents=True)

        # Create marker at top level
        git_dir = tmp_path / ".git"
        git_dir.mkdir()

        # Search with max_depth=2 should not find the marker
        result = find_workspace_root(deep_dir, max_depth=2)
        assert (
            result == deep_dir
        )  # Returns start_dir because max_depth prevents reaching marker


class TestFormatStatusMessage:
    """Tests for format_status_message utility."""

    def test_format_message(self):
        """Test basic message formatting."""
        result = format_status_message("my-plugin", "processing started")

        # Check that it contains the prefix and message
        assert "my-plugin" in result
        assert "processing started" in result
        # Check format has HH:MM:SS pattern
        parts = result.split("  ")
        assert len(parts) == 2
        assert ":" in parts[0]  # Time format

    def test_format_message_with_special_chars(self):
        """Test formatting with special characters."""
        result = format_status_message("plugin-v2", "error: something failed")

        assert "plugin-v2" in result
        assert "error: something failed" in result

    def test_format_message_order(self):
        """Test that timestamp comes before prefix."""
        result = format_status_message("test", "msg")

        timestamp_idx = result.find(":")
        prefix_idx = result.find("test")
        assert timestamp_idx < prefix_idx
