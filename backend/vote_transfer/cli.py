"""Small command line interface for the reproducible pipeline."""

import argparse
import json
from pathlib import Path

import requests

from vote_transfer.application.processing import process_year
from vote_transfer.config import data_root
from vote_transfer.infrastructure.official import SUPPORTED_YEARS, acquire_official


def main() -> None:
    parser = argparse.ArgumentParser(description="Acquire and process original election results.")
    subparsers = parser.add_subparsers(dest="command", required=True)
    for command in ("acquire", "process"):
        sub = subparsers.add_parser(command)
        sub.add_argument("--year", type=int, choices=SUPPORTED_YEARS, default=2022)
        sub.add_argument("--data-root", type=Path, default=data_root())
    args = parser.parse_args()
    try:
        action = acquire_official if args.command == "acquire" else process_year
        report = action(args.year, args.data_root)
    except (OSError, ValueError, requests.RequestException) as error:
        parser.exit(1, f"{args.command} failed: {error}\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
