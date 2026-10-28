"""Command-line entry point for understandable, selective data acquisition."""

import argparse
from pathlib import Path

from vote_transfer.application.source_catalog import SOURCES, get_source
from vote_transfer.domain.data_source import AccessMethod
from vote_transfer.infrastructure.acquisition import download_source, resolve_resources
from vote_transfer.infrastructure.official import acquire_official


def _size(value: int | None) -> str:
    if value is None:
        return "unknown size"
    return f"{value / 1_000_000:.1f} MB"


def _print_catalog() -> None:
    print("Available sources\n")
    for source in SOURCES:
        role = "primary" if source.core else "optional / validation"
        print(f"- {source.key}: {source.name} [{role}]")
        print(f"  Purpose: {source.purpose}")
        print(f"  Access: {source.access_method}")
        print(f"  Page: {source.landing_url}")
        print(f"  Note: {source.notes}\n")


def main() -> None:
    parser = argparse.ArgumentParser(description="Resolve or download documented project sources.")
    parser.add_argument("--list", action="store_true", help="show the source catalogue")
    parser.add_argument("--source", help="source key, or 'core' for primary sources")
    parser.add_argument(
        "--download",
        action="store_true",
        help="download files; otherwise no files are written",
    )
    parser.add_argument("--data-root", type=Path, default=Path("data"))
    args = parser.parse_args()

    if args.list or not args.source:
        _print_catalog()
        if not args.source:
            return

    selected = (
        [source for source in SOURCES if source.core]
        if args.source == "core"
        else [get_source(args.source)]
    )
    acquired_years = set()
    for source in selected:
        print(f"\n{source.name}")
        print(f"  Purpose: {source.purpose}")
        if args.download and source.key.startswith("official_"):
            year = int(source.key.split("_")[1])
            if year not in acquired_years:
                acquire_official(year, args.data_root)
                acquired_years.add(year)
            print(f"  Verified original files: {args.data_root / 'raw' / 'official' / str(year)}")
            continue
        if source.access_method in {AccessMethod.PARAMETERIZED_API, AccessMethod.REFERENCE_ONLY}:
            print(f"  Not downloaded automatically: {source.notes}")
            continue
        resources = resolve_resources(source)
        for resource in resources:
            details = f"{resource.format}, {_size(resource.expected_size)}"
            print(f"  Resource: {resource.title} ({details})")
            print(f"  Source URL: {resource.url}")
        if args.download:
            records = download_source(source, args.data_root)
            for record in records:
                print(f"  Saved: {record['saved_as']} ({_size(record['downloaded_bytes'])})")
                print(f"  SHA-256: {record['sha256']}")
        else:
            print("  Dry run only. Add --download to save files.")


if __name__ == "__main__":
    main()
