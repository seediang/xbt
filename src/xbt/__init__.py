"""xbt - dbt wrapper with plugin system."""

__version__ = "0.2.0"

# Export public plugin API
from xbt.plugins import (
    InitContext,
    PluginConfig,
    PostInvokeContext,
    PreInvokeContext,
    emit_status,
    find_dbt_project_dir,
    find_workspace_root,
    format_status_message,
    get_dbt_command,
    hookimpl,
    is_command_in_set,
)

__all__ = [
    "InitContext",
    "PreInvokeContext",
    "PostInvokeContext",
    "PluginConfig",
    "hookimpl",
    "get_dbt_command",
    "is_command_in_set",
    "find_dbt_project_dir",
    "find_workspace_root",
    "emit_status",
    "format_status_message",
]
