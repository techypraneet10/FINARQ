"""Cross-platform script to run the local FastAPI development server."""

import subprocess
import sys


def main() -> None:
    """Execute uvicorn with live reload."""
    cmd = [
        sys.executable,
        "-m",
        "uvicorn",
        "financial_rag.main:app",
        "--reload",
        "--port",
        "8000",
        "--host",
        "0.0.0.0",
    ]
    sys.exit(subprocess.call(cmd))


if __name__ == "__main__":
    main()
