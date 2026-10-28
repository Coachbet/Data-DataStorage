"""Read verified outputs and package compact, offline-ready teaching snapshots."""

import json
import shutil
import tempfile
from pathlib import Path

import pandas as pd

from vote_transfer.infrastructure.official import sha256

DATA_FILES = ("department_results.parquet", "h0_evaluation.parquet")
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


def load_dataset(folder: Path) -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    """Check published hashes before exposing either observations or model outputs."""
    quality = json.loads((folder / "quality_report.json").read_text())
    for name in DATA_FILES:
        if quality.get("outputs", {}).get(name) != sha256(folder / name):
            raise ValueError(
                "Processed outputs do not match their build report. Re-run processing."
            )
    results, evaluation = (pd.read_parquet(folder / name) for name in DATA_FILES)
    if set(results.year) != {quality["year"]} or set(evaluation.year) != {quality["year"]}:
        raise ValueError("Dataset years do not match their build report.")
    return results, evaluation, quality


def bundle_year(year: int, root: Path) -> dict:
    """Copy only validated small aggregates and provenance, never raw or station data."""
    source = root / "processed" / str(year)
    load_dataset(source)
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
        load_dataset(staging)
        target.mkdir(exist_ok=True)
        for name in BUNDLE_FILES:
            (staging / name).replace(target / name)
    return {"year": year, "bytes": size, "directory": str(target), "files": list(BUNDLE_FILES)}
