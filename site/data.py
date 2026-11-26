"""Data access for the website.

Everything here reads the versioned snapshots (data/bundled, data/reference,
reports/results) and the existing backend. Nothing is written, and no number is
typed by hand: the site recomputes from the same functions the pipeline uses.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import streamlit as st
from vote_transfer.application.datasets import available_datasets, load_dataset
from vote_transfer.application.models import (
    MAIN_CODING,
    MAIN_VARIANT,
    THRESHOLD,
    Election,
    build_election,
    election_scores,
    mix,
    predict,
    primary_score,
    transfer_tensor,
)
from vote_transfer.application.positions import load_candidate_positions
from vote_transfer.config import data_root

PROJECT = Path(__file__).resolve().parent.parent
RESULTS = PROJECT / "reports" / "results"
FIGURES = PROJECT / "reports" / "figures"
REFERENCE = PROJECT / "data" / "reference"
DOCS = PROJECT / "docs"

YEARS = (2002, 2007, 2012, 2017, 2022)
OUTCOMES = ("finalist_a", "finalist_b", "blank_invalid", "abstention")
OUTCOME_LABEL = {
    "finalist_a": "Finalist A",
    "finalist_b": "Finalist B",
    "blank_invalid": "Blank or invalid",
    "abstention": "Abstention",
}
MODELS = (
    "H0a",
    "H0b",
    "H1",
    "H1-soft",
    "H2-abst",
    "H2-blank",
    "H3(H1)",
    "H3(H2-abst)",
    "H3(H2-blank)",
)
PARAMETER_FREE = ("H0a", "H0b", "H1", "H1-soft", "H2-abst", "H2-blank")
FAMILY = {
    "H0a": "Baseline",
    "H0b": "Baseline",
    "H1": "Proximity",
    "H1-soft": "Proximity",
    "H2-abst": "Proximity",
    "H2-blank": "Proximity",
    "H3(H1)": "Mixture",
    "H3(H2-abst)": "Mixture",
    "H3(H2-blank)": "Mixture",
}
ONE_LINE = {
    "H0a": "Eliminated voters split like the whole electorate, abstainers included.",
    "H0b": "Eliminated voters split like those who voted: nobody newly abstains.",
    "H1": "Each eliminated group goes entirely to the finalist nearest on the left-right scale.",
    "H1-soft": "Each group splits between the finalists; the nearer one gets more.",
    "H2-abst": "Like H1, but a group far from both finalists abstains.",
    "H2-blank": "Like H1, but a group far from both finalists votes blank.",
    "H3(H1)": "A share p behaves like H0b, the rest like H1. p is fitted on other elections.",
    "H3(H2-abst)": "A share p behaves like H0b, the rest like H2-abst.",
    "H3(H2-blank)": "A share p behaves like H0b, the rest like H2-blank.",
}
TEAM = ("Victor Henz", "Edgar Gusching", "Louis Bettelli", "Lucas Magret Delord", "Oscar Moulet")
COURSE = "Data, Data Storage, Data Collection · CentraleSupélec × ESSEC · 2026"
REPOSITORY = "https://github.com/Coachbet/Data-DataStorage"


# ---- Raw tables ---------------------------------------------------------------------


@st.cache_data(show_spinner=False)
def results(year: int) -> pd.DataFrame:
    """Validated wide view of one election (both rounds, every area and option)."""
    folders = available_datasets(data_root())
    return load_dataset(folders[str(year)])[0]


@st.cache_data(show_spinner=False)
def quality(year: int) -> dict:
    folders = available_datasets(data_root())
    return load_dataset(folders[str(year)])[2]


@st.cache_resource(show_spinner=False)
def election(year: int) -> Election:
    return build_election(results(year))


@st.cache_data(show_spinner=False)
def positions() -> pd.DataFrame:
    return load_candidate_positions()


@st.cache_data(show_spinner=False)
def csv(name: str) -> pd.DataFrame:
    return pd.read_csv(RESULTS / name)


@st.cache_data(show_spinner=False)
def numbers() -> dict:
    """Every number the pipeline generated for the documents (reports/results/numbers.json)."""
    import json

    return json.loads((RESULTS / "numbers.json").read_text(encoding="utf-8"))


@st.cache_data(show_spinner=False)
def polls() -> pd.DataFrame:
    return pd.read_csv(REFERENCE / "polling_axes.csv")


def scores(year: int) -> dict[str, float | None]:
    return election_scores(positions(), year, MAIN_CODING)


def name(year: int, option: str) -> str:
    """Readable label of a first-round group."""
    if option == "abstention":
        return "Abstention"
    if option == "blank_invalid":
        return "Blank or invalid"
    table = positions()
    row = table[(table.year == year) & (table.candidate_id == option.removeprefix("candidate:"))]
    return str(row.candidate_name.iloc[0]) if len(row) else option


def party(year: int, option: str) -> str:
    table = positions()
    row = table[(table.year == year) & (table.candidate_id == option.removeprefix("candidate:"))]
    return str(row.party_abbreviation.iloc[0]) if len(row) else ""


def finalists(year: int) -> tuple[str, str]:
    a, b = election(year).finalists
    return name(year, a), name(year, b)


def outcome_label(year: int, role: str) -> str:
    a, b = finalists(year)
    return {"finalist_a": a, "finalist_b": b}.get(role, OUTCOME_LABEL[role])


# ---- Models -------------------------------------------------------------------------


def fold_p(base: str, year: int) -> float:
    """H3's share p fitted with ``year`` held out (main variant)."""
    folds = csv("h3_folds.csv")
    row = folds[(folds.base == base) & (folds.variant == MAIN_VARIANT) & (folds.test_year == year)]
    return float(row.p.iloc[0])


@st.cache_resource(show_spinner=False)
def tensor(year: int, model: str) -> np.ndarray:
    """(areas, groups, 4) transfer matrices of a parameter-free model."""
    return transfer_tensor(election(year), model, scores(year))


def model_tensor(year: int, model: str, p: float | None = None) -> np.ndarray:
    if model.startswith("H3("):
        base = model[3:-1]
        share = fold_p(base, year) if p is None else p
        return mix(tensor(year, base), tensor(year, "H0b"), share)
    return tensor(year, model)


def prediction(year: int, model: str, p: float | None = None) -> np.ndarray:
    """(areas, 4) predicted second-round shares of registered voters."""
    return predict(election(year), model_tensor(year, model, p))


def score(year: int, predicted: np.ndarray) -> float:
    """The primary score: weighted mean over areas of the 4-outcome MAE, in pp."""
    return primary_score(predicted, election(year))


def weights(year: int) -> np.ndarray:
    e = election(year)
    return e.registered_r2 / e.registered_r2.sum()


def pooled_first(year: int) -> pd.Series:
    """First-round shares of registered voters, pooled over covered areas (weighted r2)."""
    e = election(year)
    return pd.Series(weights(year) @ e.first, index=e.groups)


def pooled(year: int, values: np.ndarray) -> np.ndarray:
    return weights(year) @ values


def flows(year: int, model: str, p: float | None = None) -> pd.DataFrame:
    """Pooled flows from each first-round group to each outcome, in % of registered voters."""
    e = election(year)
    t = model_tensor(year, model, p)
    mass = np.einsum("a,ag,agk->gk", weights(year), e.first, t) * 100
    frame = pd.DataFrame(mass, index=e.groups, columns=OUTCOMES)
    return frame


def custom_tensor(year: int, mixture: dict[str, float]) -> np.ndarray:
    """A user-made rule: a weighted mix of 'nearest finalist', 'proportional',
    'abstain' and 'blank' rows for eliminated groups. Weights sum to one."""
    e = election(year)
    h1, h0b = tensor(year, "H1"), tensor(year, "H0b")
    abstain, blank = h0b.copy(), h0b.copy()
    index = {g: i for i, g in enumerate(e.groups)}
    for group in e.eliminated:
        abstain[:, index[group], :] = (0, 0, 0, 1)
        blank[:, index[group], :] = (0, 0, 1, 0)
    return (
        mixture["nearest"] * h1
        + mixture["proportional"] * h0b
        + mixture["abstain"] * abstain
        + mixture["blank"] * blank
    )


def predict_custom(year: int, mixture: dict[str, float]) -> np.ndarray:
    return predict(election(year), custom_tensor(year, mixture))


@st.cache_data(show_spinner=False)
def live_scores() -> pd.DataFrame:
    """Every model's primary score per election, recomputed live from the backend.

    Used to check that the site agrees with reports/results/model_comparison.csv.
    """
    rows = []
    for year in YEARS:
        for model in MODELS:
            rows.append((model, year, score(year, prediction(year, model))))
    return pd.DataFrame(rows, columns=["model", "year", "score"])


def comparison() -> pd.DataFrame:
    return csv("model_comparison.csv").set_index("model").loc[list(MODELS)]


def candidate_table(year: int) -> pd.DataFrame:
    """Every first-round candidate: name, party, scale position and first-round share."""
    first = pooled_first(year) * 100
    e = election(year)
    s = scores(year)
    rows = []
    for option in e.groups:
        if not option.startswith("candidate:"):
            continue
        rows.append(
            {
                "option": option,
                "candidate": name(year, option),
                "party": party(year, option),
                "score": s.get(option),
                "share": float(first[option]),
                "role": "finalist_a"
                if option == e.finalists[0]
                else "finalist_b"
                if option == e.finalists[1]
                else "eliminated",
            }
        )
    return pd.DataFrame(rows).sort_values("score", na_position="last").reset_index(drop=True)


def threshold() -> float:
    return THRESHOLD
