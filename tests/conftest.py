"""Small, explicitly synthetic original-file fixtures; no real voter data."""

import csv
import json
from pathlib import Path

import pytest
from vote_transfer.infrastructure.official import sha256

HEADER = [
    "Code du département",
    "Libellé du département",
    "Code de la circonscription",
    "Libellé de la circonscription",
    "Code de la commune",
    "Libellé de la commune",
    "Code du b.vote",
    "Inscrits",
    "Abstentions",
    "% Abs/Ins",
    "Votants",
    "% Vot/Ins",
    "Blancs",
    "% Blancs/Ins",
    "% Blancs/Vot",
    "Nuls",
    "% Nuls/Ins",
    "% Nuls/Vot",
    "Exprimés",
    "% Exp/Ins",
    "% Exp/Vot",
    "N°Panneau",
    "Sexe",
    "Nom",
    "Prénom",
    "Voix",
    "% Voix/Ins",
    "% Voix/Exp",
]


@pytest.fixture
def raw_dataset(tmp_path: Path) -> Path:
    folder = tmp_path / "raw" / "official" / "2022"
    folder.mkdir(parents=True)
    files = []
    for round_number in (1, 2):
        path = folder / f"round_{round_number}.txt"
        with path.open("w", encoding="cp1252", newline="") as stream:
            writer = csv.writer(stream, delimiter=";")
            writer.writerow(HEADER)
            for code, scale in (("01", 1), ("2A", 2)):
                row = [
                    code,
                    f"Synthetic unit {code}",
                    "01",
                    "Example",
                    "001",
                    "Example",
                    "0001",
                    100 * scale,
                    20 * scale,
                    "20",
                    80 * scale,
                    "80",
                    2 * scale,
                    "2",
                    "2.5",
                    3 * scale,
                    "3",
                    "3.75",
                    75 * scale,
                    "75",
                    "93.75",
                ]
                candidates = (
                    [("ALPHA", 30), ("BETA", 20), ("GAMMA", 25)]
                    if round_number == 1
                    else [("GAMMA", 35), ("ALPHA", 40)]
                )
                for number, (name, count) in enumerate(candidates, 1):
                    row.extend([str(number), "F", name, "Test", count * scale, "0", "0"])
                writer.writerow(row)
        files.append({"round": round_number, "file": path.name, "sha256": sha256(path)})
    (folder / "manifest.json").write_text(json.dumps({"year": 2022, "files": files}))
    return tmp_path
