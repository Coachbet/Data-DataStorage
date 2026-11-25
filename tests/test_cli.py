import subprocess
import sys

import pandas as pd
from vote_transfer.application.datasets import bundle_year
from vote_transfer.application.processing import process_year


def run_cli(*arguments):
    return subprocess.run(
        [sys.executable, "-m", "vote_transfer.cli", *arguments], capture_output=True, text=True
    )


def test_check_snapshots_fails_only_when_copies_differ(raw_dataset):
    process_year(2022, raw_dataset)
    bundle_year(2022, raw_dataset)
    assert run_cli("check-snapshots", "--data-root", str(raw_dataset)).returncode == 0
    stale = raw_dataset / "bundled/2022/outcomes.parquet"
    stale.write_bytes(stale.read_bytes() + b"x")
    result = run_cli("check-snapshots", "--data-root", str(raw_dataset))
    assert result.returncode == 1
    assert "2022/outcomes.parquet" in result.stderr
    assert "bundle" in result.stderr


def test_evaluate_and_bundle_work_on_a_clone_without_raw_data(tmp_path):
    """Fresh clone: only bundled snapshots exist, yet predictions can be rebuilt and bundled."""
    import shutil
    from pathlib import Path

    from vote_transfer.application.datasets import snapshot_drift

    bundled = Path(__file__).resolve().parents[1] / "data" / "bundled"
    shutil.copytree(bundled, tmp_path / "bundled")
    (tmp_path / "bundled" / "predictions.parquet").unlink()
    assert (
        run_cli("evaluate", "--all-models", "--all-years", "--data-root", str(tmp_path)).returncode
        == 0
    )
    result = run_cli("bundle", "--all-years", "--data-root", str(tmp_path))
    assert result.returncode == 0, result.stderr
    assert "no local processed build" in result.stdout
    # Same content, not same bytes: the last floating-point digit of a prediction can differ
    # between platforms (BLAS, CPU), so the file hash is only comparable on one machine.
    pd.testing.assert_frame_equal(
        pd.read_parquet(tmp_path / "bundled" / "predictions.parquet"),
        pd.read_parquet(bundled / "predictions.parquet"),
        rtol=1e-9,
        atol=1e-12,
    )
    assert snapshot_drift(tmp_path) == []
