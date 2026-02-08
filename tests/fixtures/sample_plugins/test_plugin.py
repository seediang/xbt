"""Sample test plugin module."""

import pluggy

__version__ = "1.0.0"

hookimpl = pluggy.HookimplMarker("xbt")


@hookimpl
def xbt_register_commands(cli_group):
    """Register test commands."""
    pass


@hookimpl
def xbt_register_callbacks():
    """Register test callbacks."""
    return []


@hookimpl
def xbt_pre_invoke(args):
    """Modify args before invocation."""
    return args


@hookimpl
def xbt_post_invoke(args, result):
    """React to invocation results."""
    pass
