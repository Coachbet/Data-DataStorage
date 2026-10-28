"""Small command line interface for the reproducible pipeline."""

import argparse
import json
from pathlib import Path

import requests

from vote_transfer.application.datasets import bundle_year
from vote_transfer.application.processing import process_year
from vote_transfer.config import data_root
from vote_transfer.infrastructure.official import SUPPORTED_YEARS, acquire_official


def main() -> None:
    parser = argparse.ArgumentParser(description="Acquire and process original election results.")
    subparsers = parser.add_subparsers(dest="command", required=True)
    for command in ("acquire", "process", "bundle"):
        sub = subparsers.add_parser(command)
        years = sub.add_mutually_exclusive_group()
        years.add_argument("--year", type=int, nargs="+", choices=SUPPORTED_YEARS)
        years.add_argument("--all-years", action="store_true", help="all supported elections")
        sub.add_argument("--data-root", type=Path, default=data_root())
    args = parser.parse_args()
    try:
        action = {"acquire": acquire_official, "process": process_year, "bundle": bundle_year}[
            args.command
        ]
        years = SUPPORTED_YEARS if args.all_years else (args.year or [2022])
        for year in years:
            report = action(year, args.data_root)
            print(json.dumps(report, indent=2))
    except (OSError, ValueError, requests.RequestException) as error:
        parser.exit(1, f"{args.command} failed: {error}\n")


if __name__ == "__main__":
    main()
