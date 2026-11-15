"""Read verified outputs and package compact, offline-ready teaching snapshots."""

import json
import shutil
import tempfile
from pathlib import Path

import pandas as pd

from vote_transfer.application.baseline import evaluate_h0
from vote_transfer.application.processing import results_view, validate_tables
from vote_transfer.infrastructure.official import sha256

DATA_FILES = ("areas.parquet", "outcomes.parquet", "options.parquet")
BUNDLE_FILES = (*DATA_FILES, "quality_report.json")
MAX_BUNDLE_BYTES = 2_000_000  # Deliberately small enough for ordinary Git tracking.


def available_datasets(root: Path) -> dict[str, Path]:
    """Prefer complete local builds; otherwise use the versioned aggregate snapshots."""
    available = {}
    for layer in ("bundled", "processed"):
        for folder in (root / layer).glob("[0-9][0-9][0-9][0-9]"):
            if all((folder / name).is_file() for name in BUNDLE_FILES):
                available[folder.name] = folder
    return dict(sorted(available.items(), reverse=True))


def load_tables(folder: Path) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, dict]:
    """Check published hashes and table constraints before exposing any observation."""
    quality = json.loads((folder / "quality_report.json").read_text())
    for name in DATA_FILES:
        if quality.get("outputs", {}).get(name) != sha256(folder / name):
            raise ValueError(
                "Processed outputs do not match their build report. Re-run processing."
            )
    areas, outcomes, options = (pd.read_parquet(folder / name) for name in DATA_FILES)
    validate_tables(areas, outcomes, options)
    if set(areas.year) != {quality["year"]} or set(outcomes.year) != {quality["year"]}:
        raise ValueError("Dataset years do not match their build report.")
    return areas, outcomes, options, quality


def load_dataset(folder: Path) -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    """The app's wide results view and its H0a comparison, both derived on load."""
    areas, outcomes, options, quality = load_tables(folder)
    results = results_view(areas, outcomes, options)
    return results, evaluate_h0(results), quality


def bundle_year(year: int, root: Path) -> dict:
    """Copy only validated small aggregates and provenance, never raw or station data."""
    source = root / "processed" / str(year)
    load_tables(source)
    size = sum((source / name).stat().st_size for name in BUNDLE_FILES)
    if size > MAX_BUNDLE_BYTES:
        raise ValueError(f"Bundle exceeds the {MAX_BUNDLE_BYTES:,}-byte per-year limit.")
    parent = root / "bundled"
    parent.mkdir(parents=True, exist_ok=True)
    target = parent / str(year)
    with tempfile.TemporaryDirectory(dir=parent, prefix=".bundle-") as temporary:
        staging = Path(temporary)
        for name in BUNDLE_FILES:
            shutil.copyfile(source / name, staging / name)
        load_tables(staging)
        target.mkdir(exist_ok=True)
        for name in BUNDLE_FILES:
            (staging / name).replace(target / name)
    return {"year": year, "bytes": size, "directory": str(target), "files": list(BUNDLE_FILES)}


def snapshot_drift(root: Path) -> list[str]:
    """Name each data file whose local build and versioned snapshot hold different bytes.

    A stale snapshot means a fresh clone and this machine would show different results.
    Files present in only one layer are not drift: there is nothing to disagree with.
    """
    differing = []
    for bundled in sorted((root / "bundled").glob("[0-9][0-9][0-9][0-9]")):
        for name in DATA_FILES:
            ours, theirs = root / "processed" / bundled.name / name, bundled / name
            if ours.is_file() and theirs.is_file() and sha256(ours) != sha256(theirs):
                differing.append(f"{bundled.name}/{name}")
    return differing
