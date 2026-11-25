"""Read verified outputs and package compact, offline-ready teaching snapshots."""

import json
import shutil
import tempfile
from pathlib import Path

import pandas as pd

from vote_transfer.application.baseline import evaluate_h0
from vote_transfer.application.models import evaluate_models
from vote_transfer.application.positions import REFERENCE_DIR, load_candidate_positions
from vote_transfer.application.processing import results_view, validate_tables
from vote_transfer.infrastructure.official import SUPPORTED_YEARS, sha256

DATA_FILES = ("areas.parquet", "outcomes.parquet", "options.parquet")
BUNDLE_FILES = (*DATA_FILES, "quality_report.json")
PREDICTION_FILES = ("predictions.parquet", "evaluation_report.json")
CROSSCHECK_RECORD = "crosscheck_{year}.json"  # dated summary written by `vote-transfer crosscheck`
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
    quality = json.loads((folder / "quality_report.json").read_text(encoding="utf-8"))
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


def prediction_inputs(root: Path, reference: Path = REFERENCE_DIR) -> dict:
    """Hashes of everything the predictions depend on: five elections and the candidate table."""
    folders = available_datasets(root)
    missing = [year for year in SUPPORTED_YEARS if str(year) not in folders]
    if missing:
        raise ValueError(f"Cross-election evaluation needs every election; missing: {missing}.")
    return {
        "elections": {
            str(year): json.loads(
                (folders[str(year)] / "quality_report.json").read_text(encoding="utf-8")
            )["outputs"]
            for year in SUPPORTED_YEARS
        },
        "candidate_positions_sha256": sha256(reference / "candidate_positions.csv"),
        "candidate_scores_sha256": sha256(reference / "candidate_scores.csv"),
    }


def build_predictions(root: Path, reference: Path = REFERENCE_DIR) -> dict:
    """Evaluate every model on every election and publish one long predictions table."""
    inputs = prediction_inputs(root, reference)
    folders = available_datasets(root)
    results = {year: load_dataset(folders[str(year)])[0] for year in SUPPORTED_YEARS}
    predictions, report = evaluate_models(results, load_candidate_positions(reference))
    report |= {"rows": len(predictions), "inputs": inputs}
    parent = root / "processed"
    parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=parent, prefix=".build-") as temporary:
        staging = Path(temporary)
        predictions.to_parquet(staging / "predictions.parquet", index=False)
        report["outputs"] = {"predictions.parquet": sha256(staging / "predictions.parquet")}
        (staging / "evaluation_report.json").write_text(
            json.dumps(report, indent=2) + "\n", encoding="utf-8", newline="\n"
        )
        for name in PREDICTION_FILES:
            (staging / name).replace(parent / name)
    return {k: report[k] for k in ("coding_status", "comparison_coding_status", "rows", "outputs")}


def load_predictions(root: Path) -> tuple[pd.DataFrame, dict] | None:
    """Prefer a local evaluation; otherwise the bundled one. None when neither exists."""
    for layer in ("processed", "bundled"):
        folder = root / layer
        if all((folder / name).is_file() for name in PREDICTION_FILES):
            report = json.loads((folder / "evaluation_report.json").read_text(encoding="utf-8"))
            if report["outputs"]["predictions.parquet"] != sha256(folder / "predictions.parquet"):
                raise ValueError("Predictions do not match their evaluation report. Re-evaluate.")
            return pd.read_parquet(folder / "predictions.parquet"), report
    return None


def stale_predictions(root: Path, reference: Path = REFERENCE_DIR) -> bool:
    """True when the elections or the candidate table changed after the last evaluation."""
    loaded = load_predictions(root)
    return loaded is not None and loaded[1]["inputs"] != prediction_inputs(root, reference)


def bundle_predictions(root: Path) -> dict:
    """Copy a verified local evaluation next to the per-year snapshots."""
    source = root / "processed"
    if not all((source / name).is_file() for name in PREDICTION_FILES):
        raise ValueError("No local evaluation to bundle. Run `vote-transfer evaluate` first.")
    report = json.loads((source / "evaluation_report.json").read_text(encoding="utf-8"))
    if report["outputs"]["predictions.parquet"] != sha256(source / "predictions.parquet"):
        raise ValueError("Predictions do not match their evaluation report. Re-evaluate.")
    size = sum((source / name).stat().st_size for name in PREDICTION_FILES)
    if size > MAX_BUNDLE_BYTES:
        raise ValueError(f"Predictions exceed the {MAX_BUNDLE_BYTES:,}-byte bundle limit.")
    target = root / "bundled"
    target.mkdir(parents=True, exist_ok=True)
    for name in PREDICTION_FILES:
        temporary = target / f".{name}.staged"
        shutil.copyfile(source / name, temporary)
        temporary.replace(target / name)
    return {"bytes": size, "directory": str(target), "files": list(PREDICTION_FILES)}


def snapshot_drift(root: Path) -> list[str]:
    """Name each data file whose local build and versioned snapshot hold different bytes.

    A stale snapshot means a fresh clone and this machine would show different results.
    Files present in only one layer are not drift: there is nothing to disagree with.
    """
    pairs = [
        (f"{bundled.name}/{name}", root / "processed" / bundled.name / name, bundled / name)
        for bundled in sorted((root / "bundled").glob("[0-9][0-9][0-9][0-9]"))
        for name in DATA_FILES
    ]
    pairs += [
        (name, root / "processed" / name, root / "bundled" / name) for name in PREDICTION_FILES
    ]
    return [
        label
        for label, ours, theirs in pairs
        if ours.is_file() and theirs.is_file() and sha256(ours) != sha256(theirs)
    ]


def load_crosscheck(root: Path, year: int) -> dict | None:
    """The last recorded comparison with published national totals, if one was made."""
    record = root / "bundled" / CROSSCHECK_RECORD.format(year=year)
    return json.loads(record.read_text(encoding="utf-8")) if record.is_file() else None
