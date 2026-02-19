# Plan: Enhance xbt Plugin Architecture

**Scope**: Improve xbt-core plugin system to reduce boilerplate and make plugin development easier

**Iteration**: v1 - Context & Command Filtering (Priority: High)

---

## Problem Statement

After implementing multiple plugins for xbt-loom (auto-configuration, artifact uploading, artifact management CLI, artifact uploader), we've identified repeated patterns across plugins:

1. **Repeated code for extracting dbt command** from raw CLI args
2. **Repeated code for resolving project directory** and validating existence
3. **Boilerplate checks** for plugin management commands
4. **Manual command filtering** (only run for specific dbt commands like run, test, build)
5. **Redundant utilities** duplicated across plugins (get_dbt_command, is_plugin_management_command, etc.)

This causes:
- Plugin code has 20-30% boilerplate before doing actual work
- Common utilities scattered across projects instead of in xbt core
- Inconsistent handling of edge cases
- Increased maintenance burden

---

## Proposed Solution: XbtContext & Enhanced Hooks

### Phase 1: XbtContext (High Priority)

Replace:
```python
@hookimpl
def xbt_post_invoke(args: List[str], result: Optional[object] = None) -> None:
```

With:
```python
@hookimpl
def xbt_post_invoke(context: XbtContext) -> None:
```

Where `XbtContext` provides:
```python
class XbtContext:
    """Structured context for all plugin hooks."""
    args: List[str]              # Raw CLI arguments
    command: Optional[str]       # Extracted dbt command (e.g., "run", "test")
    project_dir: Optional[Path]  # Resolved & validated project directory
    workspace_root: Path         # Workspace root directory
    plugin_name: str             # Current plugin namespace
    result: Optional[object]     # Hook result (for post-invoke)
    
    @property
    def is_plugin_management_command(self) -> bool:
        """True if xbt plugin/plugins command."""
        return self.command in {"plugin", "plugins"}
```

### Phase 2: Command Filtering (High Priority)

Add hook parameters for command filtering:
```python
@hookimpl(run_for_commands={"run", "test", "build"})
def xbt_post_invoke(context: XbtContext) -> None:
    # Only called for run, test, build
    # xbt automatically skips for other commands
    
@hookimpl(skip_for_commands={"plugin"})
def xbt_pre_invoke(context: XbtContext) -> Optional[List[str]]:
    # Called for all except plugin management
```

### Phase 3: Core Plugin Utilities (Medium Priority)

Move to `xbt.plugins.utils`:
- `get_dbt_command(args: Sequence[str]) -> Optional[str]`
- `is_command_in_set(command: Optional[str], commands: Set[str]) -> bool`
- `find_dbt_project_dir(start_dir: Optional[Path] = None) -> Optional[Path]`
- `find_workspace_root(start_dir: Path, markers: Optional[List[str]] = None) -> Path`
- `emit_status(logger: Logger, message: str, level: int = INFO) -> None`
- `format_status_message(prefix: str, message: str) -> str`

### Phase 4: Plugin Configuration (Medium Priority)

```python
from xbt.plugins import PluginConfig

class BackendConfig(PluginConfig):
    """Plugin config with schema and validation."""
    config_file = "~/.xbt/plugins.yml"  # Standard location
    
    backend: str = "local"
    skip_patterns: List[str] = field(default_factory=list)
    
    def validate(self) -> None:
        """Custom validation."""
        if self.backend not in {"local", "s3", "snowflake"}:
            raise ValueError(f"Invalid backend: {self.backend}")

@hookimpl
def xbt_init() -> BackendConfig:
    """xbt loads from ~/.xbt/plugins.yml and passes to plugins."""
    return BackendConfig()
```

---

## Implementation Steps

### Step 1: Create XbtContext Class

**File**: `src/xbt/plugins/context.py`

```python
"""Plugin execution context."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, List, Optional, Sequence


@dataclass
class XbtContext:
    """Execution context passed to all plugin hooks.
    
    This provides pre-extracted and validated information to reduce
    boilerplate in plugin implementations.
    """
    
    args: List[str]              # Raw CLI arguments passed to xbt/dbt
    command: Optional[str]       # Extracted dbt command (e.g., "run", "test", "compile")
    project_dir: Optional[Path]  # Resolved project directory (may be None if not found)
    workspace_root: Path         # Workspace root directory  
    plugin_name: str             # Plugin namespace/identifier
    result: Optional[Any] = None # Hook result (for post-invoke hooks)
    
    @property
    def is_plugin_management_command(self) -> bool:
        """Return True if this is xbt plugin/plugins command."""
        return self.command in {"plugin", "plugins"}
    
    @property
    def has_project(self) -> bool:
        """Return True if a valid project directory was found."""
        return self.project_dir is not None and self.project_dir.exists()


__all__ = ["XbtContext"]
```

---

### Step 2: Create Plugin Utilities Module

**File**: `src/xbt/plugins/utils.py`

```python
"""Utilities for plugin development."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional, Sequence, Set


def get_dbt_command(args: Sequence[str]) -> Optional[str]:
    """Extract dbt command from CLI arguments.
    
    Returns the first positional argument (non-flag), which is typically
    the dbt command like 'run', 'test', 'compile', etc.
    
    Args:
        args: CLI arguments
        
    Returns:
        Command name or None if not found
        
    Examples:
        ['run'] -> 'run'
        ['test', '--select', 'model1'] -> 'test'
        ['-d', 'run'] -> 'run'
        ['--project-dir', '.', 'run'] -> 'run'
        [] -> None
    """
    if not args:
        return None
    
    for arg in args:
        if not arg.startswith("-"):
            return arg
    
    return None


def is_command_in_set(command: Optional[str], commands: Set[str]) -> bool:
    """Check if command is in the given set.
    
    Case-insensitive comparison.
    
    Args:
        command: Command name to check
        commands: Set of valid commands
        
    Returns:
        True if command is in set
    """
    if not command:
        return False
    return command.lower() in {c.lower() for c in commands}


def find_dbt_project_dir(start_dir: Optional[Path] = None) -> Optional[Path]:
    """Find dbt project directory by looking for dbt_project.yml.
    
    Searches up from start_dir (or cwd) until dbt_project.yml is found.
    
    Args:
        start_dir: Directory to start search from (defaults to cwd)
        
    Returns:
        Path to project directory or None if not found
    """
    current = (start_dir or Path.cwd()).resolve()
    
    # Check current and parent directories up to filesystem root
    while True:
        if (current / "dbt_project.yml").exists():
            return current
        
        parent = current.parent
        if parent == current:  # Reached filesystem root
            break
        
        current = parent
    
    return None


def find_workspace_root(
    start_dir: Path,
    markers: Optional[list[str]] = None,
    max_depth: int = 10,
) -> Path:
    """Find workspace root by looking for marker files/directories.
    
    Searches up from start_dir for marker files. Default markers:
    .git, pyproject.toml, dbt_project.yml
    
    Args:
        start_dir: Directory to start search from
        markers: List of marker files/dirs to look for
        max_depth: Maximum directories to traverse
        
    Returns:
        Path to workspace root or start_dir if not found
    """
    if markers is None:
        markers = [".git", "pyproject.toml", "dbt_project.yml"]
    
    current = start_dir.resolve()
    
    for _ in range(max_depth):
        if any((current / marker).exists() for marker in markers):
            return current
        
        parent = current.parent
        if parent == current:  # Reached filesystem root
            break
        
        current = parent
    
    return start_dir


def emit_status(
    logger: logging.Logger,
    message: str,
    level: int = logging.INFO,
) -> None:
    """Log and print a status message to both logger and stdout.
    
    Args:
        logger: Logger instance
        message: Message to emit
        level: Logging level
    """
    logger.log(level, message)
    print(message)


def format_status_message(prefix: str, message: str) -> str:
    """Format a status message with timestamp and prefix.
    
    Args:
        prefix: Plugin name or prefix for the message
        message: Message content
        
    Returns:
        Formatted message like "HH:MM:SS  prefix: message"
    """
    import time
    timestamp = time.strftime("%H:%M:%S")
    return f"{timestamp}  {prefix}: {message}"


__all__ = [
    "get_dbt_command",
    "is_command_in_set",
    "find_dbt_project_dir",
    "find_workspace_root",
    "emit_status",
    "format_status_message",
]
```

---

### Step 3: Update Hook Signatures in Hookspecs

**File**: `src/xbt/hookspecs.py` (update existing)

Replace:
```python
@hookspec
def xbt_pre_invoke(args: List[str]) -> List[str] | None:
    """Before dbt processes arguments."""

@hookspec
def xbt_post_invoke(args: List[str], result: Optional[object] = None) -> None:
    """After dbt invocation completes."""
```

With (backwards compatible):
```python
@hookspec(firstresult=False)
def xbt_pre_invoke(
    args: List[str] | None = None,
    context: Optional[XbtContext] = None,
) -> List[str] | None:
    """Before dbt processes arguments.
    
    New implementations should use context parameter.
    The args parameter is deprecated but maintained for backwards compatibility.
    
    Args:
        args: (Deprecated) Raw CLI arguments
        context: XbtContext with pre-extracted data
        
    Returns:
        Modified arguments or None to keep original
    """

@hookspec(firstresult=False)
def xbt_post_invoke(
    args: List[str] | None = None,
    result: Optional[object] = None,
    context: Optional[XbtContext] = None,
) -> None:
    """After dbt invocation completes.
    
    New implementations should use context parameter.
    
    Args:
        args: (Deprecated) Raw CLI arguments
        result: dbt execution result
        context: XbtContext with pre-extracted data
    """
```

---

### Step 4: Implement Hook Filtering

**File**: `src/xbt/plugins/filter.py` (new)

```python
"""Hook filtering and execution control."""

from __future__ import annotations

from typing import Any, Callable, Optional, Set


class HookFilter:
    """Decorator and handler for filtering hook execution by command."""
    
    def __init__(
        self,
        run_for_commands: Optional[Set[str]] = None,
        skip_for_commands: Optional[Set[str]] = None,
    ):
        """Initialize hook filter.
        
        Args:
            run_for_commands: Only execute for these commands
            skip_for_commands: Skip execution for these commands
        """
        self.run_for_commands = run_for_commands
        self.skip_for_commands = skip_for_commands
    
    def should_execute(self, command: Optional[str]) -> bool:
        """Determine if hook should execute for this command.
        
        Args:
            command: The dbt command being executed
            
        Returns:
            True if hook should execute
        """
        if not command:
            command = None
        else:
            command = command.lower()
        
        # Skip if in skip list
        if self.skip_for_commands:
            skip_set = {c.lower() for c in self.skip_for_commands}
            if command in skip_set:
                return False
        
        # Only run if in run list (if specified)
        if self.run_for_commands:
            run_set = {c.lower() for c in self.run_for_commands}
            return command in run_set
        
        # No filters, always run
        return True


def hookimpl(
    tryfirst: bool = False,
    trylast: bool = False,
    optionalhook: bool = False,
    run_for_commands: Optional[Set[str]] = None,
    skip_for_commands: Optional[Set[str]] = None,
) -> Callable:
    """Enhanced hookimpl with command filtering.
    
    Args:
        tryfirst: Hook runs before others of this name
        trylast: Hook runs after others of this name
        optionalhook: Hook is optional
        run_for_commands: Only execute for these dbt commands
        skip_for_commands: Skip execution for these dbt commands
        
    Usage:
        @hookimpl(run_for_commands={"run", "test", "build"})
        def xbt_post_invoke(context: XbtContext) -> None:
            # Only runs for run, test, build commands
    """
    import pluggy
    
    base_impl = pluggy.HookimplMarker("xbt")(
        tryfirst=tryfirst,
        trylast=trylast,
        optionalhook=optionalhook,
    )
    
    def decorator(func: Callable) -> Callable:
        # Apply pluggy marker
        func = base_impl(func)
        
        # Attach filter metadata if any
        if run_for_commands or skip_for_commands:
            hook_filter = HookFilter(
                run_for_commands=run_for_commands,
                skip_for_commands=skip_for_commands,
            )
            func._xbt_hook_filter = hook_filter
        
        return func
    
    return decorator
```

---

### Step 5: Update xbtRunner to Build XbtContext

**File**: `src/xbt/runner.py` (modify)

In `xbtRunner._invoke_hooks()` or similar hook execution method:

```python
def _build_context(self, command: Optional[str]) -> XbtContext:
    """Build XbtContext for this execution."""
    from xbt.plugins.utils import find_dbt_project_dir, find_workspace_root
    
    project_dir = find_dbt_project_dir()
    workspace_root = find_workspace_root(
        project_dir or Path.cwd()
    )
    
    return XbtContext(
        args=self.args.copy(),
        command=command,
        project_dir=project_dir,
        workspace_root=workspace_root,
        plugin_name=self.plugin_name,
        result=None,  # Set for post-invoke hooks
    )

def _call_hook(self, hook_name: str, context: XbtContext) -> Any:
    """Call hook with filtering support."""
    hook_filter = getattr(self.hook_func, "_xbt_hook_filter", None)
    
    if hook_filter and not hook_filter.should_execute(context.command):
        return None
    
    # Call with context
    return self.hook_func(context)
```

---

## Migration Guide for Plugin Developers

### Old Style (Deprecated)

```python
from xbt_loom_plugin.utils import get_dbt_command, is_plugin_management_command

@hookimpl
def xbt_post_invoke(args: List[str], result: Optional[object] = None) -> None:
    # Lots of boilerplate
    if is_plugin_management_command(args):
        return
    
    command = get_dbt_command(args)
    if command not in {"run", "test", "build"}:
        return
    
    project_dir = resolve_project_dir(args)
    if not project_dir:
        return
```

### New Style (Recommended)

```python
from xbt.plugins import XbtContext

@hookimpl(run_for_commands={"run", "test", "build"})
def xbt_post_invoke(context: XbtContext) -> None:
    # Context provides everything pre-extracted
    if not context.has_project:
        return
    
    # Do actual work
```

---

## Testing Strategy

1. **Unit Tests**: Test XbtContext creation and validation
2. **Hook Filter Tests**: Test command filtering logic
3. **Integration Tests**: Test with real plugins using new context
4. **Backwards Compatibility**: Ensure old-style plugins still work

---

## Backwards Compatibility

- Keep old hook signatures working (with deprecation warnings)
- Plugins can use either old or new style
- Migration period: 2-3 releases

---

## Success Criteria

- ✓ Plugin boilerplate reduced by 50%+
- ✓ Common utilities in xbt-core, not duplicated
- ✓ New plugins easier to write
- ✓ Existing plugins continue to work
- ✓ Command filtering works declaratively
- ✓ XbtContext provides all commonly needed information

---

## Files to Create

1. `src/xbt/plugins/__init__.py` - Package init, export public API
2. `src/xbt/plugins/context.py` - XbtContext class
3. `src/xbt/plugins/utils.py` - Utility functions
4. `src/xbt/plugins/filter.py` - Hook filtering logic
5. `tests/test_plugin_context.py` - Context tests
6. `tests/test_plugin_filter.py` - Filter tests
7. `tests/test_plugin_utils.py` - Utils tests

---

## Files to Modify

1. `src/xbt/hookspecs.py` - Update hook signatures (backwards compatible)
2. `src/xbt/runner.py` - Build context, handle filtering
3. `src/xbt/__init__.py` - Export new classes
4. Documentation - Update plugin development guide
