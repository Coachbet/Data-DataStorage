import subprocess
import sys

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
    stale = raw_dataset / "bundled/2022/department_results.parquet"
    stale.write_bytes(stale.read_bytes() + b"x")
    result = run_cli("check-snapshots", "--data-root", str(raw_dataset))
    assert result.returncode == 1
    assert "2022/department_results.parquet" in result.stderr
    assert "bundle" in result.stderr
