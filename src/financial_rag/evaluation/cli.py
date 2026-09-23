"""Developer Evaluation and Benchmark CLI tool."""

import argparse
import asyncio
import contextlib
import sys
from pathlib import Path

# Ensure UTF-8 output encoding for cross-platform and Windows terminal support
if hasattr(sys.stdout, "reconfigure"):
    with contextlib.suppress(Exception):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    with contextlib.suppress(Exception):
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")

from financial_rag.application.evaluation.service import EvaluationService
from financial_rag.infrastructure.evaluation.report_formatter import ReportFormatter


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments for evaluation runner."""
    parser = argparse.ArgumentParser(
        prog="python -m financial_rag.evaluation.cli",
        description="Production Financial RAG Platform Evaluation & Regression CLI",
    )
    subparsers = parser.add_subparsers(dest="command", help="Evaluation sub-commands")

    # Command: run
    run_parser = subparsers.add_parser("run", help="Execute an evaluation benchmark suite")
    run_parser.add_argument(
        "--dataset",
        "-d",
        default="financial_rag_eval_v1",
        help="Dataset version (default: financial_rag_eval_v1)",
    )
    run_parser.add_argument(
        "--suite", "-s", default="end_to_end", help="Evaluation suite (default: end_to_end)"
    )
    run_parser.add_argument(
        "--format",
        "-f",
        default="markdown",
        choices=["markdown", "json", "csv"],
        help="Report output format",
    )
    run_parser.add_argument(
        "--save-baseline", action="store_true", help="Persist results as new baseline"
    )
    run_parser.add_argument(
        "--output-dir", "-o", type=Path, default=None, help="Directory to save report file"
    )

    # Command: compare
    compare_parser = subparsers.add_parser(
        "compare", help="Compare current evaluation run against baseline"
    )
    compare_parser.add_argument(
        "--dataset", "-d", default="financial_rag_eval_v1", help="Dataset version"
    )

    # Command: ablation
    ablation_parser = subparsers.add_parser(
        "ablation", help="Execute retrieval strategy ablation study"
    )
    ablation_parser.add_argument(
        "--dataset", "-d", default="financial_rag_eval_v1", help="Dataset version"
    )

    # Command: check-gates
    gate_parser = subparsers.add_parser(
        "check-gates", help="Evaluate CI quality gates against benchmark"
    )
    gate_parser.add_argument(
        "--dataset", "-d", default="financial_rag_eval_v1", help="Dataset version"
    )

    return parser.parse_args()


async def async_main() -> int:
    """Main asynchronous execution flow for evaluation CLI."""
    args = parse_args()
    if not args.command:
        print(
            "Error: No sub-command specified. Use 'run', 'compare', 'ablation', or 'check-gates'.",
            file=sys.stderr,
        )
        return 1

    eval_service = EvaluationService()
    formatter = ReportFormatter()

    if args.command == "run":
        scorecard, regression, gate_result = await eval_service.execute_evaluation(
            dataset_version=args.dataset,
            suite=args.suite,
            compare_baseline=True,
            enforce_gates=True,
        )

        if args.save_baseline:
            eval_service.save_as_baseline(scorecard)
            print(
                f"✅ Saved scorecard {scorecard.evaluation_run_id} as gold baseline for {args.dataset}."
            )

        # Render Output
        if args.format == "json":
            output = formatter.format_json(scorecard, regression)
        elif args.format == "csv":
            output = formatter.format_csv(scorecard)
        else:
            output = formatter.format_markdown(scorecard, regression)

        print(output)

        if args.output_dir:
            args.output_dir.mkdir(parents=True, exist_ok=True)
            ext = "json" if args.format == "json" else ("csv" if args.format == "csv" else "md")
            out_file = args.output_dir / f"evaluation_report_{scorecard.evaluation_run_id}.{ext}"
            with open(out_file, "w", encoding="utf-8") as f_out:
                f_out.write(output)
            print(f"\n📁 Report saved to {out_file}")

        return 0 if gate_result.passed else 1

    elif args.command == "ablation":
        print(f"Running retrieval strategy ablation on dataset '{args.dataset}'...\n")
        ablation = await eval_service.run_retrieval_ablation(args.dataset)
        print("| Strategy | Recall@10 | Precision@10 | MRR | NDCG@10 | Latency (ms) |")
        print("|---|:---:|:---:|:---:|:---:|:---:|")
        for strat, met in ablation.items():
            print(
                f"| **{strat}** | `{met.recall_at_10:.4f}` | `{met.precision_at_10:.4f}` | `{met.mrr:.4f}` | `{met.ndcg_at_10:.4f}` | `{met.mean_latency_ms:.2f}` |"
            )
        return 0

    elif args.command == "check-gates":
        scorecard, regression, gate_result = await eval_service.execute_evaluation(
            dataset_version=args.dataset,
            suite="end_to_end",
        )
        if gate_result.passed:
            print("🎉 ALL CI QUALITY GATES PASSED.")
            return 0
        else:
            print("❌ CI QUALITY GATES FAILED:")
            for f in gate_result.failures:
                print(f"  - {f}")
            return 1

    return 0


def main() -> None:
    """CLI synchronous entrypoint."""
    exit_code = asyncio.run(async_main())
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
