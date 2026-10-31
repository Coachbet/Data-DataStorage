"""Independent published totals used only to cross-check our own aggregation."""

from __future__ import annotations

import csv
import json
from datetime import UTC, datetime
from pathlib import Path

import requests

from vote_transfer.infrastructure.official import candidate_identifier, sha256

# Ministry national summary files ("resultats-par-niveau-fe"), same releases as the
# polling-station files. Only 2022 has been located and reviewed so far.
NATIONAL_SUMMARIES = {
    2022: {
        1: "https://www.data.gouv.fr/api/1/datasets/r/1421c8db-b10f-4ed1-abb3-52b010e74e79",
        2: "https://www.data.gouv.fr/api/1/datasets/r/debe2f26-48e5-4c45-abab-4926145c9936",
    }
}
SUMMARY_FIELDS = {
    "registered": "Inscrits",
    "abstentions": "Abstentions",
    "voters": "Votants",
    "blank": "Blancs",
    "invalid": "Nuls",
    "valid": "Exprimés",
}
FIRST_CANDIDATE_FIELD = 17  # N°Panneau; each candidate then occupies seven fields.


def acquire_national_summary(year: int, root: Path) -> dict:
    """Download both national summaries; reproduce pinned checksums when present."""
    if year not in NATIONAL_SUMMARIES:
        raise ValueError(f"National summaries are reviewed for: {sorted(NATIONAL_SUMMARIES)}")
    folder = root / "raw" / "reference" / f"national_{year}"
    folder.mkdir(parents=True, exist_ok=True)
    manifest_path = folder / "manifest.json"
    manifest = (
        json.loads(manifest_path.read_text())
        if manifest_path.exists()
        else {
            "source": "Ministry published national summaries; independent aggregation check",
            "files": [],
        }
    )
    records = {item["round"]: item for item in manifest["files"]}
    with requests.Session() as session:
        session.headers["User-Agent"] = "vote-transfer/0.1 academic research"
        for round_number, url in NATIONAL_SUMMARIES[year].items():
            target = folder / f"round_{round_number}.txt"
            pinned = records.get(round_number)
            if target.exists():
                if not pinned or sha256(target) != pinned["sha256"]:
                    raise ValueError(f"Unverified reference file: {target}.")
                continue
            temporary = target.with_suffix(".txt.part")
            with session.get(url, timeout=(10, 60)) as response:
                response.raise_for_status()
                temporary.write_bytes(response.content)
                resolved_url = response.url
            digest = sha256(temporary)
            if pinned and digest != pinned["sha256"]:
                raise ValueError(f"Reference bytes differ from the pinned checksum: {temporary}")
            temporary.replace(target)
            if not pinned:
                records[round_number] = {
                    "round": round_number,
                    "file": target.name,
                    "url": url,
                    "resolved_url": resolved_url,
                    "sha256": digest,
                    "retrieved_at_utc": datetime.now(UTC).isoformat(),
                    "bytes": target.stat().st_size,
                }
    manifest["files"] = [records[n] for n in sorted(records)]
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n")
    return manifest


def parse_national_summary(path: Path) -> dict[str, int]:
    """Return published national totals keyed like our outputs (counts and candidates)."""
    with path.open(encoding="cp1252", newline="") as stream:
        header, row = list(csv.reader(stream, delimiter=";"))[:2]
    if header[FIRST_CANDIDATE_FIELD] != "N°Panneau" or row[0] != "FE":
        raise ValueError(f"Unsupported national summary layout: {path}")
    totals = {name: int(row[header.index(field)]) for name, field in SUMMARY_FIELDS.items()}
    for start in range(FIRST_CANDIDATE_FIELD, len(row), 7):
        surname, first_name, votes = row[start + 2], row[start + 3], row[start + 4]
        totals[f"candidate:{candidate_identifier(f'{first_name} {surname}')}"] = int(votes)
    return totals
