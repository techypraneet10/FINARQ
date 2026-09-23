"""Cross-platform script to run the test suite with coverage."""

import subprocess
import sys


def main() -> None:
    """Execute pytest with coverage."""
    cmd = [
        sys.executable,
        "-m",
        "pytest",
        "-v",
        "--cov=src/financial_rag",
        "--cov-report=term-missing",
        "tests/",
    ]
    sys.exit(subprocess.call(cmd))


if __name__ == "__main__":
    main()
