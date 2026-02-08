import sys
from typing import Optional

from .xbt_runner import xbtRunner, xbtRunnerResult


def match_dbt_exit_code(dbt_result: Optional[xbtRunnerResult]) -> int:
    if not dbt_result:
        return 1
    if getattr(dbt_result, "success", False):
        return 0
    if getattr(dbt_result, "exception", None):
        exc_name = type(dbt_result.exception).__name__
        if exc_name in {
            "DbtUsageException",
            "DbtProjectError",
            "DbtRuntimeError",
            "DbtDatabaseError",
            "DbtCompilationError",
            "DbtConfigError",
            "DbtSchemaError",
            "DbtValidationError",
        }:
            return 2
    return 1


def main():
    dbt_args = sys.argv[1:]
    runner = xbtRunner()

    result: xbtRunnerResult = runner.invoke(dbt_args)

    if result and result.exception:
        exc_name = type(result.exception).__name__
        if exc_name == "DbtUsageException":
            print("Usage: xbt [OPTIONS] COMMAND [ARGS]...", file=sys.stderr)
            print("Try 'xbt -h' for help.", file=sys.stderr)
            print(f"\nError: {result.exception}", file=sys.stderr)

    # Exit with dbt's exit code
    sys.exit(match_dbt_exit_code(result))


if __name__ == "__main__":
    main()
