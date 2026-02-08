# Summary
xbt is an extension to dbt. It acts as a wrapper around the dbt dbtRunner object with a simple plugin system to add custom logic before and after dbt commands. The output from xbt should be identical for any dbt command with the exception dbt is replaced with xbt.

xbt has a plugin systems that exposes the following:
- ability to register dbt callbacks via dbtRunner
- ability to add new commands to the CLI context
- pre commands hook that allows arguments to be adjusted
- post command hook that returns the results of the dbt command

## Development
- uv used for package management
- tests implemented using pytest
- ty used for type checking
- ruff used for linting and formatting
- support python 3.12 and higher
- use type hints, code must successfully pass ty check
- when done run the following commands to ensure the python code is valid
    - uv run ruff check .
    - uv run ty check
    - uv run pytest

# command line
- use the following to run python ```uv run python```
- You have access to a powershell console