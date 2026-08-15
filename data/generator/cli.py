"""Command line interface for the generator."""

import argparse
from datetime import date
from pathlib import Path

from generator import writer
from generator.engine import DEFAULT_START, generate
from generator.profiles import PROFILES


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="generator",
        description="Generate a deterministic synthetic bank statement.",
    )
    parser.add_argument(
        "--seed",
        type=int,
        required=True,
        help="seed driving every random draw, same seed means same output",
    )
    parser.add_argument(
        "--profile",
        choices=(*sorted(PROFILES), "all"),
        default="employee",
        help="account holder profile to generate, or all of them",
    )
    parser.add_argument(
        "--months",
        type=int,
        default=24,
        help="length of the history in months",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=Path("out"),
        help="directory the json files are written to",
    )
    parser.add_argument(
        "--start",
        type=date.fromisoformat,
        default=DEFAULT_START,
        help="first month of the history, defaults to a fixed date",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.months < 1:
        raise SystemExit("months must be at least 1")

    selected = sorted(PROFILES) if args.profile == "all" else [args.profile]
    for name in selected:
        statement = generate(
            profile=PROFILES[name],
            seed=args.seed,
            months=args.months,
            start=args.start,
        )
        path = writer.write_transactions(
            statement.transactions, args.out, name, args.seed
        )
        labels = writer.write_labels(statement.labels, args.out, name, args.seed)
        anomalies = sum(1 for label in statement.labels if label["is_anomaly"])
        print(
            f"{name}: {len(statement.transactions)} transactions "
            f"({anomalies} anomalies) -> {path}, {labels}"
        )
    return 0
