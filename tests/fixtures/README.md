"""README for test fixtures."""

# Test Fixtures

This directory contains sample configuration files and plugins used in integration tests.

## sample_configs/

- `whitelist.yml` - Configuration with enabled_plugins (whitelist mode)
- `blacklist.yml` - Configuration with disabled_plugins (blacklist mode)
- `empty.yml` - Empty configuration (all plugins enabled)
- `invalid.yml` - Invalid YAML for error handling tests

## sample_plugins/

- `test_plugin.py` - Sample plugin module for testing plugin loading
