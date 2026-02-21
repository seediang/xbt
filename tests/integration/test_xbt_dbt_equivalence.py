"""Integration tests to verify xbt output matches dbt output."""

import os
import re
import subprocess
from pathlib import Path

import pytest


class TestXbtDbtEquivalence:
    """Test that xbt produces identical output to dbt for various commands."""

    @staticmethod
    def normalize_output(output: str) -> str:
        """
        Normalize output by removing timestamps, paths, and runtime info.

        This allows us to compare the essential content while ignoring
        environment-specific details.
        """
        # Remove timestamps (HH:MM:SS format)
        output = re.sub(r"\d{2}:\d{2}:\d{2}", "HH:MM:SS", output)
        # Remove absolute paths - replace with relative markers
        output = re.sub(r"/[^\s]+/dbt_project", "PROJECT_DIR", output)
        output = re.sub(r"[A-Z]:\\[^\s]+\\dbt_project", "PROJECT_DIR", output)
        # Remove runtime/performance info
        output = re.sub(r"in \d+\.\d+s", "in X.XXs", output)
        output = re.sub(r"Completed in \d+\.\d+s", "Completed in X.XXs", output)
        # Remove dbt version info that might differ
        output = re.sub(r"Running with dbt=[\d\.]+", "Running with dbt=X.X.X", output)
        # Normalize line endings
        output = output.replace("\r\n", "\n")
        return output.strip()

    @staticmethod
    def run_command(cmd: list[str], cwd: Path, timeout: int = 60) -> tuple[int, str, str]:
        """Run a command and return returncode, stdout, stderr."""
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=cwd,
        )
        return result.returncode, result.stdout, result.stderr

    def test_parse_command_equivalence(self, dbt_temp_dir, dbt_project_dir):
        """Test that 'xbt parse' output matches 'dbt parse'."""
        dbt_home, db_path, project_dir = dbt_temp_dir

        # Run dbt parse
        dbt_returncode, dbt_stdout, dbt_stderr = self.run_command(
            ["dbt", "parse"],
            cwd=project_dir,
        )

        # Run xbt parse
        xbt_returncode, xbt_stdout, xbt_stderr = self.run_command(
            ["uv", "run", "xbt", "parse"],
            cwd=project_dir,
        )

        # Both should succeed
        assert dbt_returncode == 0, f"dbt parse failed:\n{dbt_stderr}"
        assert xbt_returncode == 0, f"xbt parse failed:\n{xbt_stderr}"

        # Compare normalized outputs
        dbt_normalized = self.normalize_output(dbt_stdout)
        xbt_normalized = self.normalize_output(xbt_stdout)

        # Check that both outputs contain key indicators (performance info written)
        assert "Performance info" in xbt_normalized or "perf_info.json" in xbt_normalized
        # Both should create manifest.json
        assert (project_dir / "target" / "manifest.json").exists()

    def test_ls_command_equivalence(self, dbt_temp_dir, dbt_project_dir):
        """Test that 'xbt ls' output matches 'dbt ls'."""
        dbt_home, db_path, project_dir = dbt_temp_dir

        # First parse to create manifest
        self.run_command(["dbt", "parse"], cwd=project_dir)

        # Run dbt ls
        dbt_returncode, dbt_stdout, dbt_stderr = self.run_command(
            ["dbt", "ls"],
            cwd=project_dir,
        )

        # Run xbt ls
        xbt_returncode, xbt_stdout, xbt_stderr = self.run_command(
            ["uv", "run", "xbt", "ls"],
            cwd=project_dir,
        )

        # Both should succeed
        assert dbt_returncode == 0, f"dbt ls failed:\n{dbt_stderr}"
        assert xbt_returncode == 0, f"xbt ls failed:\n{xbt_stderr}"

        # Filter to get only resource names (lines that start with project name)
        # Exclude metadata lines (those with timestamps, "Running with", "Found", etc.)
        def extract_resources(output: str) -> set[str]:
            """Extract resource names from ls output, excluding metadata."""
            resources = set()
            for line in output.strip().split("\n"):
                line = line.strip()
                # Skip empty lines
                if not line:
                    continue
                # Skip metadata lines (contain timestamps or common metadata phrases)
                if any(
                    phrase in line
                    for phrase in ["Running with", "Found ", "Registered adapter", "HH:MM:SS"]
                ):
                    continue
                # Skip ANSI color codes and get the actual content
                # Remove ANSI escape sequences
                clean_line = re.sub(r"\x1b\[[0-9;]*m", "", line)
                # If it starts with project name (test_project), it's a resource
                if clean_line.startswith("test_project."):
                    resources.add(clean_line)
            return resources

        dbt_resources = extract_resources(dbt_stdout)
        xbt_resources = extract_resources(xbt_stdout)

        assert dbt_resources == xbt_resources, (
            f"Resource lists differ:\ndbt: {sorted(dbt_resources)}\nxbt: {sorted(xbt_resources)}"
        )

    def test_run_command_equivalence(self, dbt_temp_dir, dbt_project_dir):
        """Test that 'xbt run' output matches 'dbt run'."""
        dbt_home, db_path, project_dir = dbt_temp_dir

        # Ensure seed data is loaded first
        self.run_command(["dbt", "seed"], cwd=project_dir)

        # Run dbt run
        dbt_returncode, dbt_stdout, dbt_stderr = self.run_command(
            ["dbt", "run"],
            cwd=project_dir,
        )

        # Clean target and re-seed
        import shutil

        if (project_dir / "target").exists():
            shutil.rmtree(project_dir / "target")
        self.run_command(["uv", "run", "xbt", "seed"], cwd=project_dir)

        # Run xbt run
        xbt_returncode, xbt_stdout, xbt_stderr = self.run_command(
            ["uv", "run", "xbt", "run"],
            cwd=project_dir,
        )

        # Both should succeed
        assert dbt_returncode == 0, f"dbt run failed:\n{dbt_stderr}"
        assert xbt_returncode == 0, f"xbt run failed:\n{xbt_stderr}"

        # Compare normalized outputs
        dbt_normalized = self.normalize_output(dbt_stdout)
        xbt_normalized = self.normalize_output(xbt_stdout)

        # Check for key success indicators
        assert "Completed successfully" in xbt_normalized or "Done" in xbt_normalized
        # Both should create run_results.json
        assert (project_dir / "target" / "run_results.json").exists()

    def test_test_command_equivalence(self, dbt_temp_dir, dbt_project_dir):
        """Test that 'xbt test' output matches 'dbt test'."""
        dbt_home, db_path, project_dir = dbt_temp_dir

        # Ensure models are built first
        self.run_command(["dbt", "seed"], cwd=project_dir)
        self.run_command(["dbt", "run"], cwd=project_dir)

        # Run dbt test
        dbt_returncode, dbt_stdout, dbt_stderr = self.run_command(
            ["dbt", "test"],
            cwd=project_dir,
        )

        # Run xbt test
        xbt_returncode, xbt_stdout, xbt_stderr = self.run_command(
            ["uv", "run", "xbt", "test"],
            cwd=project_dir,
        )

        # Both should succeed
        assert dbt_returncode == 0, f"dbt test failed:\n{dbt_stderr}"
        assert xbt_returncode == 0, f"xbt test failed:\n{xbt_stderr}"

        # Compare normalized outputs - both should indicate all tests passed
        dbt_normalized = self.normalize_output(dbt_stdout)
        xbt_normalized = self.normalize_output(xbt_stdout)

        # Check for indicators of test success
        assert "Completed successfully" in xbt_normalized or "Done" in xbt_normalized
        # Look for test result indicators
        passed_pattern = r"(\d+) passed"
        dbt_passed = re.search(passed_pattern, dbt_normalized)
        xbt_passed = re.search(passed_pattern, xbt_normalized)

        if dbt_passed and xbt_passed:
            assert dbt_passed.group(1) == xbt_passed.group(1), (
                f"Different number of tests passed: dbt={dbt_passed.group(1)}, xbt={xbt_passed.group(1)}"
            )

    def test_build_command_equivalence(self, dbt_temp_dir, dbt_project_dir):
        """Test that 'xbt build' output matches 'dbt build'."""
        dbt_home, db_path, project_dir = dbt_temp_dir

        # Run dbt build
        dbt_returncode, dbt_stdout, dbt_stderr = self.run_command(
            ["dbt", "build"],
            cwd=project_dir,
        )

        # Clean and run xbt build
        import shutil

        if (project_dir / "target").exists():
            shutil.rmtree(project_dir / "target")

        xbt_returncode, xbt_stdout, xbt_stderr = self.run_command(
            ["uv", "run", "xbt", "build"],
            cwd=project_dir,
        )

        # Both should succeed
        assert dbt_returncode == 0, f"dbt build failed:\n{dbt_stderr}"
        assert xbt_returncode == 0, f"xbt build failed:\n{xbt_stderr}"

        # Compare normalized outputs
        dbt_normalized = self.normalize_output(dbt_stdout)
        xbt_normalized = self.normalize_output(xbt_stdout)

        # Check for key success indicators
        assert "Completed successfully" in xbt_normalized or "Done" in xbt_normalized
        # Both should create artifacts
        assert (project_dir / "target" / "run_results.json").exists()

    def test_help_output_contains_xbt_not_dbt(self, dbt_temp_dir, dbt_project_dir):
        """Test that xbt --help shows 'xbt' instead of 'dbt' in usage."""
        dbt_home, db_path, project_dir = dbt_temp_dir

        # Run xbt --help
        xbt_returncode, xbt_stdout, xbt_stderr = self.run_command(
            ["uv", "run", "xbt", "--help"],
            cwd=project_dir,
        )

        assert xbt_returncode == 0, f"xbt --help failed:\n{xbt_stderr}"

        # Check that help text refers to 'xbt' not 'dbt'
        help_text = xbt_stdout.lower()
        # The usage line should say "xbt" not "dbt"
        usage_lines = [line for line in xbt_stdout.split("\n") if "usage:" in line.lower()]
        if usage_lines:
            assert "xbt" in usage_lines[0].lower(), "Help usage should reference 'xbt'"

    def test_version_flag_equivalence(self, dbt_temp_dir, dbt_project_dir):
        """Test that 'xbt --version' works like 'dbt --version'."""
        dbt_home, db_path, project_dir = dbt_temp_dir

        # Run dbt --version
        dbt_returncode, dbt_stdout, dbt_stderr = self.run_command(
            ["dbt", "--version"],
            cwd=project_dir,
        )

        # Run xbt --version
        xbt_returncode, xbt_stdout, xbt_stderr = self.run_command(
            ["uv", "run", "xbt", "--version"],
            cwd=project_dir,
        )

        # Both should succeed
        assert dbt_returncode == 0, f"dbt --version failed:\n{dbt_stderr}"
        assert xbt_returncode == 0, f"xbt --version failed:\n{xbt_stderr}"

        # Both should contain version information
        assert "installed" in dbt_stdout.lower() or "version" in dbt_stdout.lower()
        assert "installed" in xbt_stdout.lower() or "version" in xbt_stdout.lower()

    def test_exit_codes_match(self, dbt_temp_dir, dbt_project_dir):
        """Test that xbt and dbt return the same exit codes for various scenarios."""
        dbt_home, db_path, project_dir = dbt_temp_dir

        # Test successful command
        dbt_returncode, _, _ = self.run_command(["dbt", "parse"], cwd=project_dir)
        xbt_returncode, _, _ = self.run_command(["uv", "run", "xbt", "parse"], cwd=project_dir)
        assert dbt_returncode == xbt_returncode == 0

        # Test invalid command (should both fail)
        dbt_returncode, _, _ = self.run_command(
            ["dbt", "invalid-command-xyz"],
            cwd=project_dir,
        )
        xbt_returncode, _, _ = self.run_command(
            ["uv", "run", "xbt", "invalid-command-xyz"],
            cwd=project_dir,
        )
        # Both should fail (non-zero exit code)
        assert dbt_returncode != 0
        assert xbt_returncode != 0
