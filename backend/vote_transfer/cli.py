"""Small command line interface for the reproducible pipeline."""

import argparse
import json
from pathlib import Path

import requests

from vote_transfer.application.crosscheck import crosscheck_national
from vote_transfer.application.datasets import (
    PREDICTION_FILES,
    build_predictions,
    bundle_predictions,
    bundle_year,
    snapshot_drift,
    stale_predictions,
)
from vote_transfer.application.positions import REFERENCE_DIR, load_candidate_positions
from vote_transfer.application.processing import process_year
from vote_transfer.application.review import coding_agreement, coding_sheet, load_coding_sheet
from vote_transfer.config import PROJECT_ROOT, data_root
from vote_transfer.infrastructure.official import SUPPORTED_YEARS, acquire_official
from vote_transfer.infrastructure.reference import NATIONAL_SUMMARIES, acquire_national_summary

RESULTS_DIR = PROJECT_ROOT / "reports" / "results"


def crosscheck(year: int, root: Path) -> dict:
    """Acquire pinned published totals, compare them and print a compact summary."""
    acquire_national_summary(year, root)
    report = crosscheck_national(year, root)
    mismatches = [row for row in report["comparisons"] if not row["matches"]]
    return {k: report[k] for k in ("year", "fields_compared", "all_match")} | {
        "mismatches": mismatches
    }


YEARLY = {
    "acquire": acquire_official,
    "process": process_year,
    "bundle": bundle_year,
    "crosscheck": crosscheck,
}


def run_yearly(args: argparse.Namespace) -> None:
    every = sorted(NATIONAL_SUMMARIES) if args.command == "crosscheck" else SUPPORTED_YEARS
    for year in every if args.all_years else (args.year or [2022]):
        print(json.dumps(YEARLY[args.command](year, args.data_root), indent=2))
    local = [args.data_root / "processed" / name for name in PREDICTION_FILES]
    if args.command == "bundle" and args.all_years and all(p.is_file() for p in local):
        print(json.dumps(bundle_predictions(args.data_root), indent=2))


def check_snapshots(args: argparse.Namespace) -> None:
    """Fail loudly when a local build was not copied to the versioned snapshots."""
    differing = snapshot_drift(args.data_root)
    if differing:
        raise ValueError(
            "processed/ and bundled/ differ for: "
            + ", ".join(differing)
            + ". Run `vote-transfer bundle --all-years` and review the changed snapshots."
        )
    if stale_predictions(args.data_root):
        raise ValueError(
            "The elections or the candidate table changed after the last evaluation. "
            "Run `vote-transfer evaluate --all-models --all-years`, then `bundle --all-years`."
        )
    print("Processed and bundled snapshots are consistent.")


def evaluate(args: argparse.Namespace) -> None:
    print(json.dumps(build_predictions(args.data_root), indent=2))


def analyse(args: argparse.Namespace) -> None:
    from vote_transfer.application.analysis import run_analysis  # imports Matplotlib

    print(json.dumps(run_analysis(args.data_root), indent=2))


def review_kit(args: argparse.Namespace) -> None:
    """Write the blind sheet two coders fill independently. It contains no codes."""
    target = REFERENCE_DIR / "review" / "coding_sheet_template.csv"
    target.parent.mkdir(parents=True, exist_ok=True)
    coding_sheet(load_candidate_positions()).to_csv(target, index=False)
    print(f"Wrote {target}")


def review_agreement(args: argparse.Namespace) -> None:
    """Compare two filled sheets. The inputs are the coders' files; nothing is simulated."""
    positions = load_candidate_positions()
    sheets = [load_coding_sheet(path, positions) for path in (args.coder_a, args.coder_b)]
    report = {
        "coder_a_file": args.coder_a.name,
        "coder_b_file": args.coder_b.name,
        **coding_agreement(*sheets),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n")
    kappa = report["quadratic_weighted_kappa"]
    print(
        f"{report['rows']} rows; agreement {report['agreement_pct']:.1f}%; "
        f"quadratic-weighted kappa {'undefined' if kappa is None else f'{kappa:.3f}'}; "
        f"{len(report['disagreements'])} disagreement(s). Wrote {args.output}"
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Acquire, process and analyse election results.")
    subparsers = parser.add_subparsers(dest="command", required=True)
    for command in YEARLY:
        sub = subparsers.add_parser(command)
        years = sub.add_mutually_exclusive_group()
        years.add_argument("--year", type=int, nargs="+", choices=SUPPORTED_YEARS)
        years.add_argument("--all-years", action="store_true", help="all supported elections")
        sub.set_defaults(run=run_yearly)
    sub = subparsers.add_parser("check-snapshots", help="compare processed/ with bundled/")
    sub.set_defaults(run=check_snapshots)
    sub = subparsers.add_parser("evaluate", help="run every model on every election")
    # Evaluation is cross-election by design (H3 trains on four elections and tests on
    # the fifth), so there is no partial mode. The flags make command lines explicit.
    sub.add_argument("--all-models", action="store_true", help="always on")
    sub.add_argument("--all-years", action="store_true", help="always on")
    sub.set_defaults(run=evaluate)
    sub = subparsers.add_parser("analyse", help="regenerate figures, results and documents")
    sub.set_defaults(run=analyse)
    sub = subparsers.add_parser("review-kit", help="write the blind coding sheet template")
    sub.set_defaults(run=review_kit)
    sub = subparsers.add_parser("review-agreement", help="agreement between two coders' sheets")
    sub.add_argument("--coder-a", type=Path, required=True)
    sub.add_argument("--coder-b", type=Path, required=True)
    sub.add_argument("--output", type=Path, default=RESULTS_DIR / "coding_agreement.json")
    sub.set_defaults(run=review_agreement)
    for sub in subparsers.choices.values():
        sub.add_argument("--data-root", type=Path, default=data_root())
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    try:
        args.run(args)
    except (OSError, ValueError, requests.RequestException) as error:
        parser.exit(1, f"{args.command} failed: {error}\n")


if __name__ == "__main__":
    main()
