"""Tests for HookFilter."""

from xbt.plugins.filter import HookFilter


class TestHookFilter:
    """Tests for the HookFilter class."""

    def test_filter_with_run_for_commands(self):
        """Test filter with run_for_commands set."""
        filter_obj = HookFilter(run_for_commands={"run", "test"})

        assert filter_obj.should_execute("run") is True
        assert filter_obj.should_execute("test") is True
        assert filter_obj.should_execute("compile") is False
        assert filter_obj.should_execute("plugin") is False

    def test_filter_with_skip_for_commands(self):
        """Test filter with skip_for_commands set."""
        filter_obj = HookFilter(skip_for_commands={"plugin", "plugins"})

        assert filter_obj.should_execute("run") is True
        assert filter_obj.should_execute("test") is True
        assert filter_obj.should_execute("plugin") is False
        assert filter_obj.should_execute("plugins") is False

    def test_filter_with_both_sets(self):
        """Test filter with both sets (skip takes precedence)."""
        filter_obj = HookFilter(
            run_for_commands={"run", "test", "build"},
            skip_for_commands={"test"},
        )

        # test is in run_for but also in skip_for, skip should win
        assert filter_obj.should_execute("test") is False
        assert filter_obj.should_execute("run") is True
        assert filter_obj.should_execute("build") is True
        assert filter_obj.should_execute("compile") is False

    def test_filter_with_no_sets(self):
        """Test filter with no sets always returns True."""
        filter_obj = HookFilter()

        assert filter_obj.should_execute("run") is True
        assert filter_obj.should_execute("test") is True
        assert filter_obj.should_execute("anything") is True
        assert filter_obj.should_execute(None) is True

    def test_filter_with_none_command(self):
        """Test filter with None command."""
        # With run_for_commands
        filter_obj = HookFilter(run_for_commands={"run", "test"})
        assert filter_obj.should_execute(None) is False

        # With skip_for_commands
        filter_obj2 = HookFilter(skip_for_commands={"plugin"})
        assert filter_obj2.should_execute(None) is True

        # With no sets
        filter_obj3 = HookFilter()
        assert filter_obj3.should_execute(None) is True

    def test_filter_case_insensitive(self):
        """Test that filter comparison is case-insensitive."""
        filter_obj = HookFilter(run_for_commands={"run", "test"})

        assert filter_obj.should_execute("RUN") is True
        assert filter_obj.should_execute("Run") is True
        assert filter_obj.should_execute("TEST") is True
        assert filter_obj.should_execute("Test") is True

    def test_filter_skip_case_insensitive(self):
        """Test skip_for_commands is case-insensitive."""
        filter_obj = HookFilter(skip_for_commands={"plugin"})

        assert filter_obj.should_execute("PLUGIN") is False
        assert filter_obj.should_execute("Plugin") is False
        assert filter_obj.should_execute("plugin") is False

    def test_filter_empty_sets(self):
        """Test filter with empty sets."""
        # Empty run_for_commands means don't run for anything
        filter_obj = HookFilter(run_for_commands=set())
        assert filter_obj.should_execute("run") is False
        assert filter_obj.should_execute("test") is False

        # Empty skip_for_commands means don't skip anything
        filter_obj2 = HookFilter(skip_for_commands=set())
        assert filter_obj2.should_execute("run") is True
        assert filter_obj2.should_execute("test") is True

    def test_filter_single_command(self):
        """Test filter with single-item sets."""
        filter_obj = HookFilter(run_for_commands={"run"})

        assert filter_obj.should_execute("run") is True
        assert filter_obj.should_execute("test") is False
