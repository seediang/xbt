"""Integration test with dbt-duckdb via xbt."""

import os
import subprocess

import pytest


class TestDbtDuckdbIntegration:
    """Test xbt with a real dbt-duckdb project."""

    def test_full_dbt_workflow(self, dbt_temp_dir, dbt_project_dir):
        """Test a complete dbt workflow (parse, seed, run, test) through xbt."""
        dbt_home, db_path, project_dir = dbt_temp_dir

        # Change to project directory
        original_cwd = os.getcwd()
        try:
            os.chdir(project_dir)

            # Test dbt parse
            result = subprocess.run(
                ["uv", "run", "xbt", "parse"],
                capture_output=True,
                text=True,
                timeout=60,
            )
            assert result.returncode == 0, f"dbt parse failed:\n{result.stderr}"
            assert (project_dir / "target" / "manifest.json").exists(), (
                "manifest.json not created"
            )

            # Test dbt seed
            result = subprocess.run(
                ["uv", "run", "xbt", "seed"],
                capture_output=True,
                text=True,
                timeout=60,
            )
            assert result.returncode == 0, f"dbt seed failed:\n{result.stderr}"

            # Test dbt run
            result = subprocess.run(
                ["uv", "run", "xbt", "run"],
                capture_output=True,
                text=True,
                timeout=60,
            )
            assert result.returncode == 0, f"dbt run failed:\n{result.stderr}"
            assert (project_dir / "target" / "run_results.json").exists(), (
                "run_results.json not created"
            )

            # Test dbt test
            result = subprocess.run(
                ["uv", "run", "xbt", "test"],
                capture_output=True,
                text=True,
                timeout=60,
            )
            assert result.returncode == 0, f"dbt test failed:\n{result.stderr}"

            # Verify DuckDB database was created
            assert db_path.exists(), "DuckDB database file not created"

        finally:
            os.chdir(original_cwd)

    def test_xbt_parse_command(self, dbt_temp_dir, dbt_project_dir):
        """Test that xbt parse command executes successfully."""
        dbt_home, db_path, project_dir = dbt_temp_dir
        original_cwd = os.getcwd()

        try:
            os.chdir(project_dir)

            result = subprocess.run(
                ["uv", "run", "xbt", "parse"],
                capture_output=True,
                text=True,
                timeout=60,
            )

            assert result.returncode == 0, (
                f"xbt parse failed with return code {result.returncode}:\nstdout: {result.stdout}\nstderr: {result.stderr}"
            )
            assert (project_dir / "target" / "manifest.json").exists()

        finally:
            os.chdir(original_cwd)

    def test_xbt_seed_and_run(self, dbt_temp_dir, dbt_project_dir):
        """Test xbt seed and run commands execute successfully."""
        dbt_home, db_path, project_dir = dbt_temp_dir
        original_cwd = os.getcwd()

        try:
            os.chdir(project_dir)

            # First parse
            subprocess.run(
                ["uv", "run", "xbt", "parse"],
                capture_output=True,
                text=True,
                timeout=60,
            )

            # Then seed
            result = subprocess.run(
                ["uv", "run", "xbt", "seed"],
                capture_output=True,
                text=True,
                timeout=60,
            )
            assert result.returncode == 0, (
                f"xbt seed failed:\nstdout: {result.stdout}\nstderr: {result.stderr}"
            )

            # Then run
            result = subprocess.run(
                ["uv", "run", "xbt", "run"],
                capture_output=True,
                text=True,
                timeout=60,
            )
            assert result.returncode == 0, (
                f"xbt run failed:\nstdout: {result.stdout}\nstderr: {result.stderr}"
            )

        finally:
            os.chdir(original_cwd)

    @pytest.mark.xfail(reason="dbt test requires more setup", strict=False)
    def test_xbt_test_command(self, dbt_temp_dir, dbt_project_dir):
        """Test xbt test command executes successfully."""
        dbt_home, db_path, project_dir = dbt_temp_dir
        original_cwd = os.getcwd()

        try:
            os.chdir(project_dir)

            # Setup: parse, seed, run first
            for cmd in ["parse", "seed", "run"]:
                subprocess.run(
                    ["uv", "run", "xbt", cmd],
                    capture_output=True,
                    text=True,
                    timeout=60,
                )

            # Then test
            result = subprocess.run(
                ["uv", "run", "xbt", "test"],
                capture_output=True,
                text=True,
                timeout=60,
            )
            assert result.returncode == 0, (
                f"xbt test failed:\nstdout: {result.stdout}\nstderr: {result.stderr}"
            )

        finally:
            os.chdir(original_cwd)
