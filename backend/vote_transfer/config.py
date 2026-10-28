"""Shared local paths; no working-directory assumptions or implicit dotenv loading."""

import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]


def data_root() -> Path:
    """An explicit environment override supports tests and separate local datasets."""
    return Path(os.environ.get("VOTE_TRANSFER_DATA_DIR", PROJECT_ROOT / "data")).resolve()
