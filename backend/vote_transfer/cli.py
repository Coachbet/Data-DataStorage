"""Small command line interface for the reproducible pipeline."""

import argparse
import json
from pathlib import Path

import requests

from vote_transfer.application.crosscheck import crosscheck_national
from vote_transfer.application.datasets import bundle_year, snapshot_drift
from vote_transfer.application.processing import process_year
from vote_transfer.config import data_root
from vote_transfer.infrastructure.official import SUPPORTED_YEARS, acquire_official
from vote_transfer.infrastructure.reference import NATIONAL_SUMMARIES, acquire_national_summary


def crosscheck(year: int, root: Path) -> dict:
    """Acquire pinned published totals, compare them and print a compact summary."""
    acquire_national_summary(year, root)
    report = crosscheck_national(year, root)
    mismatches = [row for row in report["comparisons"] if not row["matches"]]
    return {k: report[k] for k in ("year", "fields_compared", "all_match")} | {
        "mismatches": mismatches
    }


def check_snapshots(root: Path) -> None:
    """Fail loudly when a local build was not copied to the versioned snapshots."""
    differing = snapshot_drift(root)
    if differing:
        raise ValueError(
            "processed/ and bundled/ differ for: "
            + ", ".join(differing)
            + ". Run `vote-transfer bundle --all-years` and review the changed snapshots."
        )
    print("Processed and bundled snapshots are consistent.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Acquire and process original election results.")
    subparsers = parser.add_subparsers(dest="command", required=True)
    for command in ("acquire", "process", "bundle", "crosscheck"):
        sub = subparsers.add_parser(command)
        years = sub.add_mutually_exclusive_group()
        years.add_argument("--year", type=int, nargs="+", choices=SUPPORTED_YEARS)
        years.add_argument("--all-years", action="store_true", help="all supported elections")
        sub.add_argument("--data-root", type=Path, default=data_root())
    sub = subparsers.add_parser("check-snapshots", help="compare processed/ with bundled/")
    sub.add_argument("--data-root", type=Path, default=data_root())
    args = parser.parse_args()
    try:
        if args.command == "check-snapshots":
            return check_snapshots(args.data_root)
        action = {
            "acquire": acquire_official,
            "process": process_year,
            "bundle": bundle_year,
            "crosscheck": crosscheck,
        }[args.command]
        every = sorted(NATIONAL_SUMMARIES) if args.command == "crosscheck" else SUPPORTED_YEARS
        years = every if args.all_years else (args.year or [2022])
        for year in years:
            report = action(year, args.data_root)
            print(json.dumps(report, indent=2))
    except (OSError, ValueError, requests.RequestException) as error:
        parser.exit(1, f"{args.command} failed: {error}\n")


if __name__ == "__main__":
    main()
