"""Plugin configuration management.

Provides a base class for plugins to define their configuration schema
with automatic loading from YAML files and validation.
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional


class PluginConfig:
    """Base class for plugin configuration.

    Subclasses define a config_file path where configuration is loaded from.
    Subclasses should override validate() to add custom validation logic.

    Attributes:
        config_file: Path to the configuration file (typically YAML).
            Can include ~ for home directory expansion.
    """

    config_file: Optional[str] = None

    @classmethod
    def from_path(cls, config_path: Path | str) -> "PluginConfig":
        """Load configuration from a file.

        Args:
            config_path: Path to configuration file.

        Returns:
            Loaded and validated configuration instance.

        Raises:
            FileNotFoundError: If config file doesn't exist.
            ValueError: If configuration is invalid.
        """
        config_path = Path(config_path).expanduser()

        if not config_path.exists():
            raise FileNotFoundError(f"Config file not found: {config_path}")

        # Import yaml here to avoid hard dependency
        try:
            import yaml
        except ImportError as e:
            raise ImportError(
                "PyYAML is required for plugin configuration support. "
                "Install with: pip install pyyaml"
            ) from e

        with open(config_path) as f:
            data = yaml.safe_load(f) or {}

        instance = cls(**data)
        instance.validate()
        return instance

    @classmethod
    def from_default(cls) -> Optional["PluginConfig"]:
        """Load configuration from default config_file location.

        Returns:
            Loaded configuration if config_file exists, None otherwise.

        Raises:
            ValueError: If configuration is invalid.
        """
        if not cls.config_file:
            return None

        config_path = Path(cls.config_file).expanduser()

        if not config_path.exists():
            return None

        return cls.from_path(config_path)

    def validate(self) -> None:
        """Validate configuration.

        Override in subclasses to add validation logic. Should raise ValueError
        if configuration is invalid.

        Raises:
            ValueError: If configuration is invalid.
        """
        pass


__all__ = ["PluginConfig"]
