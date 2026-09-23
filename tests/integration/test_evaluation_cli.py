"""Integration tests for Evaluation CLI sub-commands and report output."""

import sys
from unittest.mock import patch

import pytest

from financial_rag.evaluation.cli import async_main


@pytest.mark.asyncio
async def test_cli_run_markdown_format(capsys) -> None:
    test_args = [
        "cli.py",
        "run",
        "--dataset",
        "financial_rag_eval_v1",
        "--suite",
        "retrieval",
        "--format",
        "markdown",
    ]
    with patch.object(sys, "argv", test_args):
        code = await async_main()
        assert code == 0

        captured = capsys.readouterr()
        assert "# Financial RAG Evaluation Scorecard" in captured.out
        assert "Retrieval" in captured.out


@pytest.mark.asyncio
async def test_cli_run_json_format(capsys) -> None:
    test_args = ["cli.py", "run", "--dataset", "financial_rag_eval_v1", "--format", "json"]
    with patch.object(sys, "argv", test_args):
        code = await async_main()
        assert code == 0

        captured = capsys.readouterr()
        assert '"dataset_version": "financial_rag_eval_v1"' in captured.out


@pytest.mark.asyncio
async def test_cli_ablation_command(capsys) -> None:
    test_args = ["cli.py", "ablation", "--dataset", "financial_rag_eval_v1"]
    with patch.object(sys, "argv", test_args):
        code = await async_main()
        assert code == 0

        captured = capsys.readouterr()
        assert "hybrid_rerank" in captured.out
