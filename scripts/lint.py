"""Cross-platform script to run linters and static type checking."""

import subprocess
import sys


def run_command(title: str, cmd: list[str]) -> int:
    """Run command and print formatted output."""
    print("\n=======================================================")
    print(f"Running: {title}")
    print(f"Command: {' '.join(cmd)}")
    print("=======================================================\n")
    return subprocess.call(cmd)


def main() -> None:
    """Execute ruff and mypy quality checks."""
    ret_ruff_check = run_command("Ruff Linter", [sys.executable, "-m", "ruff", "check", "."])
    ret_ruff_format = run_command(
        "Ruff Format Check", [sys.executable, "-m", "ruff", "format", "--check", "."]
    )
    ret_mypy = run_command("MyPy Type Checker", [sys.executable, "-m", "mypy", "src", "tests"])

    exit_code = ret_ruff_check or ret_ruff_format or ret_mypy
    if exit_code == 0:
        print("\n[SUCCESS] All code quality checks passed cleanly.\n")
    else:
        print(f"\n[FAILURE] Code quality checks failed with exit code: {exit_code}\n")
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
