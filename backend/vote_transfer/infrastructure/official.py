"""Acquire and parse original Ministry files, keeping the published bytes intact."""

from __future__ import annotations

import csv
import hashlib
import json
import re
import unicodedata
from datetime import UTC, datetime
from pathlib import Path

import pandas as pd
import requests

DATASETS = {
    (2022, 1): "election-presidentielle-des-10-et-24-avril-2022-resultats-definitifs-du-1er-tour",
    (2022, 2): "election-presidentielle-des-10-et-24-avril-2022-resultats-definitifs-du-2nd-tour",
}
SUPPORTED_YEARS = tuple(sorted({year for year, _ in DATASETS}))
STATION_KEY = ["year", "round", "department_code", "commune_code", "station_code"]
COUNTS = ["registered", "abstentions", "voters", "blank", "invalid", "valid"]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def acquire_official(year: int, root: Path) -> dict:
    """Download both rounds with API-resolved URLs and verified, resumable manifests."""
    if year not in SUPPORTED_YEARS:
        raise ValueError(f"Supported original-file adapters: {SUPPORTED_YEARS}")
    folder = root / "raw" / "official" / str(year)
    folder.mkdir(parents=True, exist_ok=True)
    manifest_path = folder / "manifest.json"
    manifest = json.loads(manifest_path.read_text()) if manifest_path.exists() else {"files": []}
    records = {item["round"]: item for item in manifest["files"]}
    with requests.Session() as session:
        session.headers["User-Agent"] = "vote-transfer/0.1 academic research"
        for round_number in (1, 2):
            target = folder / f"round_{round_number}.txt"
            if target.exists():
                record = records.get(round_number)
                if not record or sha256(target) != record["sha256"]:
                    raise ValueError(
                        f"Unverified raw file: {target}. Move it aside before retrying."
                    )
                continue
            slug = DATASETS[year, round_number]
            api = f"https://www.data.gouv.fr/api/1/datasets/{slug}/"
            response = session.get(api, timeout=(10, 60))
            response.raise_for_status()
            dataset = response.json()
            matches = [
                resource
                for resource in dataset["resources"]
                if resource.get("format", "").lower() == "txt"
                and f"burvot-t{round_number}-france-entiere" in resource["title"].lower()
            ]
            if len(matches) != 1:
                raise ValueError(f"Expected exactly one polling-station text resource at {api}")
            resource = matches[0]
            temporary = target.with_suffix(".txt.part")
            with session.get(resource["url"], stream=True, timeout=(10, 120)) as download:
                download.raise_for_status()
                with temporary.open("wb") as output:
                    for chunk in download.iter_content(1024 * 1024):
                        output.write(chunk)
                resolved_url = download.url
            expected = resource.get("filesize")
            if expected and temporary.stat().st_size != expected:
                raise ValueError(f"Incomplete download: {temporary}")
            # Verify the source layout before accepting it as an immutable raw input.
            with temporary.open(encoding="cp1252") as stream:
                if "Code du département" not in stream.readline():
                    raise ValueError(f"Unexpected original-file header: {temporary}")
            temporary.replace(target)
            records[round_number] = {
                "round": round_number,
                "file": target.name,
                "source_api": api,
                "resource_id": resource["id"],
                "url": resource["url"],
                "resolved_url": resolved_url,
                "licence": dataset.get("license"),
                "retrieved_at_utc": datetime.now(UTC).isoformat(),
                "bytes": target.stat().st_size,
                "sha256": sha256(target),
            }
            manifest = {
                "year": year,
                "source": "Ministry original files",
                "files": list(records.values()),
            }
            temporary_manifest = manifest_path.with_suffix(".json.part")
            temporary_manifest.write_text(json.dumps(manifest, indent=2) + "\n")
            temporary_manifest.replace(manifest_path)
    return manifest


def parse_official(path: Path, year: int, round_number: int) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Parse the 2022 cp1252/semicolon layout, including repeated candidate blocks.

    The publisher only supplies the first candidate's header. Each subsequent
    candidate occupies another seven fields; silently truncating them loses votes.
    Ministry geography codes are preserved, including overseas reporting areas.
    """
    if year != 2022 or round_number not in (1, 2):
        raise ValueError("This original-file parser supports the two 2022 rounds only.")
    turnout_rows, candidate_rows = [], []
    with path.open(encoding="cp1252", newline="") as stream:
        reader = csv.reader(stream, delimiter=";")
        header = next(reader, [])
        expected = {
            0: "Code du département",
            1: "Libellé du département",
            4: "Code de la commune",
            6: "Code du b.vote",
            7: "Inscrits",
            8: "Abstentions",
            10: "Votants",
            12: "Blancs",
            15: "Nuls",
            18: "Exprimés",
            21: "N°Panneau",
            23: "Nom",
            24: "Prénom",
            25: "Voix",
        }
        if any(len(header) <= i or header[i] != name for i, name in expected.items()):
            raise ValueError(f"Unsupported original-file schema: {path}")
        width = None
        for line, row in enumerate(reader, start=2):
            if width is None:
                width = len(row)
            if len(row) != width or len(row) < 28 or (len(row) - 21) % 7:
                raise ValueError(f"Malformed candidate blocks at {path}:{line}")
            key = (year, round_number, row[0], row[4], row[6])
            try:
                turnout_rows.append((*key, row[1], *(int(row[i]) for i in (7, 8, 10, 12, 15, 18))))
                for start in range(21, len(row), 7):
                    candidate = f"{row[start + 3]} {row[start + 2]}".strip()
                    if not row[start] or not candidate:
                        raise ValueError("Missing candidate identifier or name")
                    normalized = (
                        unicodedata.normalize("NFKD", candidate)
                        .encode("ascii", "ignore")
                        .decode()
                        .lower()
                    )
                    candidate_id = re.sub(r"[^a-z0-9]+", "-", normalized).strip("-")
                    candidate_rows.append(
                        (*key, candidate_id, candidate, int(row[start + 4]), row[start])
                    )
            except ValueError as error:
                raise ValueError(f"Invalid count or candidate at {path}:{line}: {error}") from error
    turnout = pd.DataFrame(turnout_rows, columns=[*STATION_KEY, "department_name", *COUNTS])
    votes = pd.DataFrame(
        candidate_rows,
        columns=[*STATION_KEY, "candidate_id", "candidate", "votes", "source_panel_number"],
    )
    return turnout, votes
