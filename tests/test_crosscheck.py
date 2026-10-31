import json

import pandas as pd
from vote_transfer.application.crosscheck import crosscheck_national, national_totals
from vote_transfer.application.processing import process_year
from vote_transfer.infrastructure.official import sha256
from vote_transfer.infrastructure.reference import SUMMARY_FIELDS, parse_national_summary

HEADER = (
    "Code du niveau;Libellé du niveau;Etat saisie;Inscrits;Abstentions;% Abs/Ins;Votants;"
    "% Vot/Ins;Blancs;% Blancs/Ins;% Blancs/Vot;Nuls;% Nuls/Ins;% Nuls/Vot;Exprimés;"
    "% Exp/Ins;% Exp/Vot;N°Panneau;Sexe;Nom;Prénom;Voix;% Voix/Ins;% Voix/Exp"
)


def write_summary(path, totals, names, shift=0):
    """Synthetic file in the published layout; `shift` corrupts the first candidate."""
    columns = HEADER.split(";")
    values = dict.fromkeys(columns[:17], "0") | {"Code du niveau": "FE"}
    for field, name in SUMMARY_FIELDS.items():
        values[name] = str(totals[field])
    row = [values[column] for column in columns[:17]]
    for number, (cid, (surname, first)) in enumerate(names.items(), 1):
        votes = totals[f"candidate:{cid}"] + (shift if number == 1 else 0)
        row += [str(number), "X", surname, first, str(votes), "0", "0"]
    path.write_text(HEADER + "\n" + ";".join(row) + "\n", encoding="cp1252")


def test_published_totals_are_compared_field_by_field(raw_dataset):
    process_year(2022, raw_dataset)
    interim = raw_dataset / "interim" / "2022"
    turnout = pd.read_parquet(interim / "turnout.parquet")
    votes = pd.read_parquet(interim / "candidate_votes.parquet")
    ours = national_totals(turnout, votes)
    folder = raw_dataset / "raw" / "reference" / "national_2022"
    folder.mkdir(parents=True)
    files = []
    for round_number, totals in ours.items():
        names = {
            cid: tuple(reversed(name.split(" ", 1)))
            for cid, name in votes[votes["round"] == round_number]
            .drop_duplicates("candidate_id")[["candidate_id", "candidate"]]
            .itertuples(index=False)
        }
        path = folder / f"round_{round_number}.txt"
        write_summary(path, totals, names, shift=1 if round_number == 2 else 0)
        assert parse_national_summary(path)["registered"] == totals["registered"]
        files.append({"round": round_number, "file": path.name, "sha256": sha256(path)})
    (folder / "manifest.json").write_text(json.dumps({"files": files}))
    report = crosscheck_national(2022, raw_dataset)
    mismatches = [row for row in report["comparisons"] if not row["matches"]]
    assert not report["all_match"]
    assert len(mismatches) == 1 and mismatches[0]["round"] == 2  # Reported, not repaired.
    assert (raw_dataset / "processed" / "2022" / "national_crosscheck.json").exists()
