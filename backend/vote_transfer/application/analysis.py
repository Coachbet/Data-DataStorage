"""Generated analysis: every figure, table and number quoted in the deliverables.

Prose never contains a typed number. Tables go to ``reports/results/``, a flat
``numbers.json`` names every quoted value, and Markdown templates are rendered
from it. After the candidate table changes, one rerun updates every document.
"""

from __future__ import annotations

import json
import re
from datetime import date
from pathlib import Path

import pandas as pd

from vote_transfer.application.datasets import (
    available_datasets,
    load_crosscheck,
    load_dataset,
    load_predictions,
    load_tables,
    stale_predictions,
)
from vote_transfer.application.evaluation import score_predictions
from vote_transfer.application.models import (
    BASES,
    CODINGS,
    MAIN_CODING,
    MAIN_VARIANT,
    NO_VARIANT,
    SETTINGS,
    THRESHOLD,
    TOLERANCE,
    Election,
    at_least,
    build_election,
    election_scores,
    h3_name,
    variant_name,
)
from vote_transfer.application.positions import (
    REFERENCE_DIR,
    load_candidate_positions,
    load_poll_scores,
)
from vote_transfer.application.quality import territory_type
from vote_transfer.application.review import reference_quality
from vote_transfer.config import PROJECT_ROOT

MODEL_ORDER = ("H0a", "H0b", *BASES, *(h3_name(base) for base in BASES))
ROLES = ("finalist_a", "finalist_b", "blank_invalid", "abstention")
OUTLIER_YEAR = 2002
CROSSCHECK_YEAR = 2022
REPORTS_DIR = PROJECT_ROOT / "reports"
TEMPLATES_DIR = PROJECT_ROOT / "docs" / "templates"
# template name -> rendered file, relative to the project root
RENDERED = {
    "findings.md": "reports/results/findings.md",
    "report.md": "docs/report/report.md",
    "presentation_outline.md": "docs/presentation_outline.md",
    "storage_comparison.md": "docs/storage_comparison.md",
}
PLACEHOLDER = re.compile(r"\{\{\s*([^}|]+?)\s*(?:\|\s*([^}]+?)\s*)?\}\}")


# --- Tables ----------------------------------------------------------------------------


def with_roles(predictions: pd.DataFrame, report: dict) -> pd.DataFrame:
    """Name each outcome by its role, so elections with different finalists line up."""
    roles = {}
    for year, election in report["elections"].items():
        roles[(int(year), election["finalist_a"])] = "finalist_a"
        roles[(int(year), election["finalist_b"])] = "finalist_b"
    frame = predictions.copy()
    frame["role"] = [
        roles.get((year, outcome), outcome)
        for year, outcome in zip(frame.year, frame.outcome, strict=True)
    ]
    return frame


def setting_predictions(predictions: pd.DataFrame, variant: str = MAIN_VARIANT) -> pd.DataFrame:
    """The eight models under one setting; the baselines have no variant of their own."""
    return predictions[predictions.variant.isin([NO_VARIANT, variant])]


def comparison_table(predictions: pd.DataFrame, variant: str = MAIN_VARIANT) -> pd.DataFrame:
    """Primary score per model and election, with means and ranks. H3 is held-out."""
    scores = score_predictions(setting_predictions(predictions, variant))
    table = scores.pivot(index="model", columns="year", values="score_pp").reindex(MODEL_ORDER)
    years = list(table.columns)
    table["mean"] = table[years].mean(axis=1)
    table[f"mean_without_{OUTLIER_YEAR}"] = table[[y for y in years if y != OUTLIER_YEAR]].mean(
        axis=1
    )
    table["rank"] = table["mean"].rank(method="min").astype(int)
    table[f"rank_without_{OUTLIER_YEAR}"] = (
        table[f"mean_without_{OUTLIER_YEAR}"].rank(method="min").astype(int)
    )
    table.columns = [str(c) for c in table.columns]
    return table


def national_errors(predictions: pd.DataFrame) -> pd.DataFrame:
    """Pooled shares over covered areas and the signed gap, per model, election and outcome.

    Signed error = predicted minus observed, in percentage points. Opposite local
    errors cancel here, which is why this is a diagnostic and not the primary score.
    """
    frame = predictions.copy()
    for column in ("predicted_share", "actual_share"):
        frame[column] *= frame.registered_r2
    keys = ["model", "variant", "year", "role", "outcome"]
    pooled = frame.groupby(keys, as_index=False)[
        ["predicted_share", "actual_share", "registered_r2"]
    ].sum()
    pooled["predicted_pct"] = pooled.predicted_share / pooled.registered_r2 * 100
    pooled["actual_pct"] = pooled.actual_share / pooled.registered_r2 * 100
    pooled["signed_error_pp"] = pooled.predicted_pct - pooled.actual_pct
    return pooled[[*keys, "predicted_pct", "actual_pct", "signed_error_pp"]]


def sensitivity_table(predictions: pd.DataFrame) -> pd.DataFrame:
    """The comparison table under each coding and tie setting, stacked."""
    frames = []
    for coding, tie in SETTINGS:
        table = comparison_table(predictions, variant_name(coding, tie)).reset_index()
        table.insert(0, "tie", tie)
        table.insert(0, "positions", coding)
        frames.append(table)
    return pd.concat(frames, ignore_index=True)


def tied_groups(positions: pd.DataFrame, report: dict) -> pd.DataFrame:
    """Eliminated candidates equidistant from both finalists, under each coding."""
    rows = []
    for coding in CODINGS:
        for year, election in report["elections"].items():
            scores = election_scores(positions, int(year), coding)
            a, b = scores[election["finalist_a"]], scores[election["finalist_b"]]
            for option, score in scores.items():
                if option in election.values() or score is None:
                    continue
                if abs(abs(score - a) - abs(score - b)) <= TOLERANCE:
                    rows.append(
                        {
                            "positions": coding,
                            "year": int(year),
                            "option": option,
                            "score": score,
                            "finalist_a_score": a,
                            "finalist_b_score": b,
                            "beyond_h2_threshold": at_least(abs(score - a)),
                        }
                    )
    columns = [
        "positions",
        "year",
        "option",
        "score",
        "finalist_a_score",
        "finalist_b_score",
        "beyond_h2_threshold",
    ]
    return pd.DataFrame(rows, columns=columns)


def threshold_table(elections: dict[int, Election], positions: pd.DataFrame) -> pd.DataFrame:
    """What the fixed H2 threshold does in each election, under the main (poll-based) scale.

    For every election: the finalists' scores and the pooled first-round share of
    registered voters in eliminated groups at least ``THRESHOLD`` (on the 0-1 scale) from both
    finalists (sent to a non-vote by H2), with the part that sits exactly on the
    threshold. Areas are pooled with the election's registration weights.
    """
    rows = []
    for year, election in sorted(elections.items()):
        scores = election_scores(positions, year, MAIN_CODING)
        a, b = (scores[f] for f in election.finalists)
        weights = election.registered_r2 / election.registered_r2.sum()
        pooled = dict(zip(election.groups, (weights @ election.first * 100).tolist(), strict=True))
        distance = {
            g: min(abs(scores[g] - a), abs(scores[g] - b))
            for g in election.eliminated
            if scores.get(g) is not None
        }
        far = {g for g, d in distance.items() if at_least(d)}
        on_threshold = {g for g in far if abs(distance[g] - THRESHOLD) <= TOLERANCE}
        rows.append(
            {
                "year": year,
                "finalist_a_score": a,
                "finalist_b_score": b,
                "groups_beyond_threshold": len(far),
                "beyond_threshold_pct": sum(pooled[g] for g in far),
                "exactly_on_threshold_pct": sum(pooled[g] for g in on_threshold),
                "scores_exactly_on_threshold": ",".join(
                    f"{v:.3f}" for v in sorted({round(scores[g], 9) for g in on_threshold})
                ),
                "eliminated_scored_pct": sum(pooled[g] for g in distance),
            }
        )
    return pd.DataFrame(rows)


def blank_only_table(
    predictions: pd.DataFrame, areas_by_year: dict[int, pd.DataFrame]
) -> pd.DataFrame:
    """Score 2017 and 2022 with blank and invalid ballots as separate outcomes.

    Convention, the same for every model: first-round invalid ballots stay invalid
    (an identity row), and everything a model sends to ``blank_invalid`` is a blank
    ballot. Invalid ballots partly reflect mistakes, so no behavioural rule here
    tries to explain their change.
    """
    rows = []
    main = setting_predictions(predictions)
    for year, areas in sorted(areas_by_year.items()):
        if areas[["blank", "invalid"]].isna().any().any():
            continue  # the split is not published for this election
        wide = areas.pivot(index="area_code", columns="round")
        invalid_r1 = wide[("invalid", 1)] / wide[("registered", 1)]
        actual_blank = wide[("blank", 2)] / wide[("registered", 2)]
        actual_invalid = wide[("invalid", 2)] / wide[("registered", 2)]
        for model, frame in main[main.year == year].groupby("model"):
            predicted = frame.pivot(index="area_code", columns="role", values="predicted_share")
            actual = frame.pivot(index="area_code", columns="role", values="actual_share")
            weight = frame.drop_duplicates("area_code").set_index("area_code").registered_r2
            weight = weight / weight.sum()
            errors = pd.DataFrame(
                {
                    "finalist_a": predicted.finalist_a - actual.finalist_a,
                    "finalist_b": predicted.finalist_b - actual.finalist_b,
                    "blank": predicted.blank_invalid - invalid_r1.astype(float) - actual_blank,
                    "invalid": invalid_r1.astype(float) - actual_invalid.astype(float),
                    "abstention": predicted.abstention - actual.abstention,
                }
            ).astype(float)
            combined = predicted.blank_invalid - actual.blank_invalid
            four = pd.concat(
                [errors[["finalist_a", "finalist_b", "abstention"]], combined.rename("bi")], axis=1
            )
            rows.append(
                {
                    "year": year,
                    "model": model,
                    "score_4_outcomes_pp": float((four.abs().mean(axis=1) * weight).sum() * 100),
                    "score_5_outcomes_pp": float((errors.abs().mean(axis=1) * weight).sum() * 100),
                    "signed_blank_invalid_pp": float((combined * weight).sum() * 100),
                    "signed_blank_pp": float((errors.blank * weight).sum() * 100),
                    "signed_invalid_pp": float((errors.invalid * weight).sum() * 100),
                    "observed_blank_r2_pct": float(
                        (actual_blank.astype(float) * weight).sum() * 100
                    ),
                    "observed_invalid_r2_pct": float(
                        (actual_invalid.astype(float) * weight).sum() * 100
                    ),
                }
            )
    table = pd.DataFrame(rows)
    for outcomes in (4, 5):
        table[f"rank_{outcomes}_outcomes"] = (
            table.groupby("year")[f"score_{outcomes}_outcomes_pp"].rank(method="min").astype(int)
        )
    order = {model: i for i, model in enumerate(MODEL_ORDER)}
    return table.sort_values(["year", "model"], key=lambda c: c.map(order).fillna(c)).reset_index(
        drop=True
    )


def territory_scores(predictions: pd.DataFrame) -> pd.DataFrame:
    """Primary score within metropolitan, overseas and abroad areas (main setting)."""
    main = setting_predictions(predictions).copy()
    main["territory"] = main.area_code.map(territory_type)
    frames = [
        score_predictions(frame).assign(territory=territory)
        for territory, frame in main.groupby("territory")
    ]
    return pd.concat(frames, ignore_index=True)[
        ["territory", "model", "year", "score_pp", "territorial_units"]
    ]


# --- Numbers quoted in prose ---------------------------------------------------------


def surname(full_name: str) -> str:
    """Drop the first given-name token: 'Jean-Marie Le Pen' -> 'Le Pen'."""
    return full_name.split(" ", 1)[1]


def ranking(series: pd.Series) -> str:
    return " < ".join(series.sort_values(kind="stable").index)


def build_numbers(
    predictions: pd.DataFrame,
    report: dict,
    positions: pd.DataFrame,
    tables: dict[str, pd.DataFrame],
    quality: dict,
) -> dict:
    """Flat name -> value map. Names are what templates cite; values are never typed."""
    comparison, errors, sensitivity = tables["comparison"], tables["errors"], tables["sensitivity"]
    without = f"mean_without_{OUTLIER_YEAR}"
    years = [int(y) for y in report["elections"]]
    n: dict[str, object] = {
        "coding_status": report["coding_status"],
        "comparison_coding_status": report["comparison_coding_status"],
        "n.elections": len(years),
    }
    n["n.models"] = len(MODEL_ORDER)
    n["n.candidacies"] = len(positions)
    n.update(scale_numbers())
    names = positions.set_index(["year", "candidate_id"]).candidate_name
    weights = predictions.drop_duplicates(["year", "area_code"]).groupby("year").registered_r2
    for year in years:
        election = report["elections"][str(year)]
        n[f"areas.{year}"] = election["areas"]
        n[f"registered_r2.{year}"] = int(weights.sum()[year])
        for role in ROLES[:2]:
            candidate = election[role].removeprefix("candidate:")
            n[f"{role}.{year}"] = surname(names[(year, candidate)])
    n["areas.total"] = sum(n[f"areas.{year}"] for year in years)

    for model, row in comparison.iterrows():
        for year in years:
            n[f"score.{model}.{year}"] = row[str(year)]
        n[f"score.{model}.mean"] = row["mean"]
        n[f"score.{model}.{without}"] = row[without]
        n[f"rank.{model}"] = int(row["rank"])
        n[f"rank_without_{OUTLIER_YEAR}.{model}"] = int(row[f"rank_without_{OUTLIER_YEAR}"])
        for baseline in ("H0a", "H0b"):
            wins = sum(row[str(y)] < comparison.loc[baseline, str(y)] for y in years)
            n[f"wins.{model}.vs_{baseline}"] = int(wins)
            n[f"delta.{model}.vs_{baseline}.mean"] = row["mean"] - comparison.loc[baseline, "mean"]
            n[f"delta.{model}.vs_{baseline}.{without}"] = (
                row[without] - comparison.loc[baseline, without]
            )
    best, best_without = comparison["mean"].idxmin(), comparison[without].idxmin()
    n["best.model"], n["best.mean"] = best, comparison.loc[best, "mean"]
    n[f"best.{without}"] = comparison.loc[best, without]
    n[f"best.rank_without_{OUTLIER_YEAR}"] = int(
        comparison.loc[best, f"rank_without_{OUTLIER_YEAR}"]
    )
    n[f"best_without_{OUTLIER_YEAR}.model"] = best_without
    n[f"best_without_{OUTLIER_YEAR}.{without}"] = comparison.loc[best_without, without]
    n[f"best_without_{OUTLIER_YEAR}.mean"] = comparison.loc[best_without, "mean"]
    n["ranking.all"] = ranking(comparison["mean"])
    n[f"ranking.without_{OUTLIER_YEAR}"] = ranking(comparison[without])
    n[f"text.best_without_{OUTLIER_YEAR}"] = (
        "stays first" if best == best_without else "is no longer first"
    )
    parameter_free = comparison.loc[["H0a", "H0b", *BASES]]
    n["best_parameter_free.model"] = parameter_free["mean"].idxmin()
    n[f"best_parameter_free_without_{OUTLIER_YEAR}.model"] = parameter_free[without].idxmin()

    main_errors = errors[errors.variant.isin([NO_VARIANT, MAIN_VARIANT])]
    for row in main_errors.itertuples():
        n[f"signed.{row.model}.{row.year}.{row.role}"] = row.signed_error_pp
        n[f"predicted.{row.model}.{row.year}.{row.role}"] = row.predicted_pct
        n[f"actual.{row.year}.{row.role}"] = row.actual_pct
    gaps = main_errors.assign(gap=main_errors.signed_error_pp.abs()).groupby(["model", "year"]).gap
    for (model, year), gap in gaps.mean().items():
        n[f"national_gap.{model}.{year}"] = gap
    for model, gap in gaps.mean().groupby("model").mean().items():
        n[f"national_gap.{model}.mean"] = gap
    for model in MODEL_ORDER:
        for role in ROLES:
            signed = main_errors[(main_errors.model == model) & (main_errors.role == role)]
            n[f"signed_min.{model}.{role}"] = signed.signed_error_pp.min()
            n[f"signed_max.{model}.{role}"] = signed.signed_error_pp.max()
            n[f"signed_positive_elections.{model}.{role}"] = int((signed.signed_error_pp > 0).sum())

    folds = pd.DataFrame(report["h3_folds"])
    folds = folds[folds.variant == MAIN_VARIANT]
    for base in BASES:
        of_base = folds[folds.base == base]
        held_out = of_base[of_base.test_year.notna()]
        for fold in held_out.itertuples():
            n[f"p.{base}.{int(fold.test_year)}"] = fold.p
        n[f"p.{base}.min"], n[f"p.{base}.max"] = held_out.p.min(), held_out.p.max()
        n[f"p.{base}.all"] = of_base[of_base.test_year.isna()].p.iloc[0]

    for coding, tie in SETTINGS[1:]:
        key = f"sens.{coding}.{tie}"
        table = sensitivity[(sensitivity.positions == coding) & (sensitivity.tie == tie)]
        table = table.set_index("model")
        for model, row in table.iterrows():
            n[f"{key}.score.{model}.mean"] = row["mean"]
            n[f"{key}.score.{model}.{without}"] = row[without]
            n[f"{key}.rank.{model}"] = int(row["rank"])
            n[f"{key}.change.{model}.mean"] = row["mean"] - comparison.loc[model, "mean"]
        n[f"{key}.best.model"] = table["mean"].idxmin()
        n[f"{key}.best_without_{OUTLIER_YEAR}.model"] = table[without].idxmin()
        n[f"{key}.ranking"] = ranking(table["mean"])
        n[f"{key}.text.same_ranking"] = (
            "is unchanged" if ranking(table["mean"]) == n["ranking.all"] else "changes"
        )
        n[f"{key}.text.same_best"] = (
            "the same model" if table["mean"].idxmin() == best else "a different model"
        )
        changes = (table["mean"] - comparison["mean"]).abs()
        n[f"{key}.max_abs_change"] = changes.max()
    ties = tables["ties"]
    for coding in CODINGS:
        of_coding = ties[ties.positions == coding]
        n[f"ties.{coding}.count"] = len(of_coding)
        n[f"ties.{coding}.elections"] = (
            ", ".join(str(y) for y in sorted(of_coding.year.unique())) or "none"
        )

    blank = tables["blank_only"]
    for row in blank.itertuples():
        key = f"blank.{row.model}.{row.year}"
        n[f"{key}.score4"], n[f"{key}.score5"] = row.score_4_outcomes_pp, row.score_5_outcomes_pp
        n[f"{key}.signed_blank_invalid"] = row.signed_blank_invalid_pp
        n[f"{key}.signed_blank"] = row.signed_blank_pp
        n[f"{key}.rank4"], n[f"{key}.rank5"] = row.rank_4_outcomes, row.rank_5_outcomes
        n[f"blank.{row.year}.signed_invalid"] = row.signed_invalid_pp  # same for every model
        n[f"blank.{row.year}.observed_blank"] = row.observed_blank_r2_pct
        n[f"blank.{row.year}.observed_invalid"] = row.observed_invalid_r2_pct
        n[f"blank.{row.year}.invalid_share_of_combined"] = (
            100
            * row.observed_invalid_r2_pct
            / (row.observed_blank_r2_pct + row.observed_invalid_r2_pct)
        )
    for year, of_year in blank.groupby("year"):
        four = ranking(of_year.set_index("model").score_4_outcomes_pp)
        five = ranking(of_year.set_index("model").score_5_outcomes_pp)
        n[f"blank.{year}.text.same_ranking"] = "is unchanged" if four == five else "changes"
        n[f"blank.{year}.ranking5"] = five
    n["blank.years"] = " and ".join(str(y) for y in sorted(blank.year.unique()))

    for row in tables["threshold"].itertuples():
        key = f"h2.{row.year}"
        n[f"{key}.finalist_a_score"], n[f"{key}.finalist_b_score"] = (
            round(float(row.finalist_a_score), 3),
            round(float(row.finalist_b_score), 3),
        )
        n[f"{key}.beyond_pct"] = row.beyond_threshold_pct
        n[f"{key}.on_threshold_pct"] = row.exactly_on_threshold_pct
        n[f"{key}.on_threshold_scores"] = row.scores_exactly_on_threshold or "none"
        n[f"{key}.eliminated_scored_pct"] = row.eliminated_scored_pct
    n["h2.threshold"] = THRESHOLD

    for row in tables["territory"].itertuples():
        n[f"territory.{row.territory}.{row.model}.{row.year}"] = row.score_pp
        n[f"territory.{row.territory}.areas.{row.year}"] = int(row.territorial_units)

    n["quality.rows"] = quality["rows"]
    n["quality.without_score"] = quality["completeness"]["rows_without_score"]
    n["quality.with_alternative"] = quality["rows_with_alternative"]
    n["quality.draft_rows"] = quality["review_status"].get("draft", 0)
    n["quality.reviewed_rows"] = quality["review_status"].get("reviewed", 0)
    n["quality.inconsistent_parties"] = ", ".join(
        item["party"] for item in quality["consistency"]["parties_coded_differently"]
    )
    n["quality.parties_checked"] = quality["consistency"]["parties_checked"]
    n["quality.accuracy_status"] = quality["accuracy"]["status"]
    n["fallback.count"] = len(report["h0b_fallbacks"])
    n["fallback.years"] = " and ".join(str(f["year"]) for f in report["h0b_fallbacks"])
    return n


def storage_numbers(
    root: Path, manifests: Path = PROJECT_ROOT / "data" / "raw" / "official"
) -> dict:
    """Measured sizes for the storage comparison: raw text, Parquet, and the same tables as CSV."""
    folders = available_datasets(root)
    raw_bytes, parquet_bytes, csv_bytes, rows = 0, 0, 0, {"areas": 0, "outcomes": 0, "options": 0}
    stations = candidates = 0
    for year, folder in folders.items():
        manifest = json.loads((manifests / year / "manifest.json").read_text())
        raw_bytes += sum({item["file"]: item["bytes"] for item in manifest["files"]}.values())
        *tables, quality = load_tables(folder)
        stations += quality["polling_station_round_rows"]
        candidates += quality["candidate_rows"]
        for name, table in zip(rows, tables, strict=True):
            rows[name] += len(table)
            parquet_bytes += (folder / f"{name}.parquet").stat().st_size
            csv_bytes += len(table.to_csv(index=False).encode())
    predictions, _ = load_predictions(root)
    layer = "processed" if (root / "processed" / "predictions.parquet").is_file() else "bundled"
    predictions_bytes = (root / layer / "predictions.parquet").stat().st_size
    predictions_csv = len(predictions.to_csv(index=False).encode())
    return {
        "storage.raw_mb": raw_bytes / 1e6,
        "storage.station_rows": stations,
        "storage.candidate_rows": candidates,
        "storage.area_rows": rows["areas"],
        "storage.outcome_rows": rows["outcomes"],
        "storage.option_rows": rows["options"],
        "storage.prediction_rows": len(predictions),
        "storage.election_tables": 3 * len(folders),
        "storage.elections_parquet_kb": parquet_bytes / 1e3,
        "storage.elections_csv_kb": csv_bytes / 1e3,
        "storage.predictions_parquet_kb": predictions_bytes / 1e3,
        "storage.predictions_csv_kb": predictions_csv / 1e3,
        "storage.total_parquet_kb": (parquet_bytes + predictions_bytes) / 1e3,
        "storage.total_csv_kb": (csv_bytes + predictions_csv) / 1e3,
        "storage.csv_to_parquet_ratio": (csv_bytes + predictions_csv)
        / (parquet_bytes + predictions_bytes),
    }


# --- Templates -------------------------------------------------------------------------


def crosscheck_numbers(record: dict | None) -> dict:
    """One sentence on the comparison with published national totals, from its dated record."""
    if record is None or not record["all_match"]:
        return {
            "text.crosscheck": f"Our {CROSSCHECK_YEAR} sums were compared with the Ministry's "
            "published national summaries (see `docs/validation.md`)."
        }
    checked = date.fromisoformat(record["checked_on"])
    return {
        "crosscheck.fields": record["fields_compared"],
        "crosscheck.date": f"{checked.day} {checked:%B %Y}",
        "text.crosscheck": f"Our {record['year']} sums match the Ministry's published national "
        f"summaries on all {record['fields_compared']} fields compared "
        f"(`vote-transfer crosscheck`, rerun on {checked.day} {checked:%B %Y}).",
    }


def format_value(value: object, spec: str | None) -> str:
    if spec:
        return format(value, spec)
    if isinstance(value, float):
        return f"{value:.1f}"
    return str(value)


def render_template(text: str, numbers: dict) -> str:
    """Replace ``{{ name }}`` or ``{{ name | format }}``; an unknown name is an error."""
    missing = sorted({m.group(1) for m in PLACEHOLDER.finditer(text) if m.group(1) not in numbers})
    if missing:
        raise ValueError(f"Template cites numbers that were not generated: {missing}")
    return PLACEHOLDER.sub(lambda m: format_value(numbers[m.group(1)], m.group(2)), text)


def render_documents(numbers: dict, templates: Path, project: Path) -> list[str]:
    written = []
    for name, target in RENDERED.items():
        source = templates / name
        if not source.is_file():
            continue
        note = (
            f"<!-- Generated from docs/templates/{name} by `vote-transfer analyse`. "
            "Edit the template, not this file. -->\n\n"
        )
        path = project / target
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(note + render_template(source.read_text(encoding="utf-8"), numbers))
        written.append(target)
    return written


# --- Orchestration ---------------------------------------------------------------------


def analysis_tables(root: Path, positions: pd.DataFrame) -> tuple[dict, pd.DataFrame, dict]:
    loaded = load_predictions(root)
    if loaded is None:
        raise ValueError("No predictions found. Run `vote-transfer evaluate` first.")
    if stale_predictions(root):
        raise ValueError(
            "Predictions are older than the elections or the candidate table. "
            "Run `vote-transfer evaluate --all-models --all-years` first."
        )
    predictions, report = loaded
    predictions = with_roles(predictions, report)
    folders = available_datasets(root)
    areas = {int(year): load_tables(folder)[0] for year, folder in folders.items()}
    tables = {
        "comparison": comparison_table(predictions),
        "errors": national_errors(predictions),
        "sensitivity": sensitivity_table(predictions),
        "ties": tied_groups(positions, report),
        "blank_only": blank_only_table(predictions, areas),
        "territory": territory_scores(predictions),
        "threshold": threshold_table(
            {int(y): build_election(load_dataset(f)[0]) for y, f in folders.items()}, positions
        ),
        "h3_folds": pd.DataFrame(report["h3_folds"]).assign(
            train_elections=lambda f: f.train_elections.map(lambda y: ",".join(map(str, y)))
        ),
    }
    return tables, predictions, report


def scale_numbers(folder: Path = REFERENCE_DIR) -> dict[str, object]:
    """What the report says about the poll-based scale, read from the shipped files."""
    polls = pd.read_csv(folder / "polling_axes.csv")
    scores = load_poll_scores(folder)
    placed, unplaced = scores[scores.status == "placed"], scores[scores.status == "unplaced"]
    names = {
        "jacques-cheminade": "Cheminade",
        "jean-lassalle": "Lassalle",
    }
    n: dict[str, object] = {
        "scale.polls": len(polls),
        "scale.institutes": polls.institute.nunique(),
        "scale.unplaced": len(unplaced),
        "scale.unplaced_list": ", ".join(
            f"{names.get(row.candidate_id, row.candidate_id)} {row.year}"
            for row in unplaced.sort_values(["year", "candidate_id"]).itertuples()
        ),
        "scale.max_range_placed": float(placed["range"].max()),
        "scale.from_reports": int(polls.source_type.ne("compiled table").sum()),
        "scale.from_paper": int(polls.source_type.eq("compiled table").sum()),
    }
    for year, of_year in polls.groupby("year"):
        n[f"scale.polls.{year}"] = len(of_year)
    return n


def run_analysis(
    root: Path,
    project: Path = PROJECT_ROOT,
    templates: Path = TEMPLATES_DIR,
    figures: bool = True,
) -> dict:
    """Regenerate every table, figure, number and rendered document."""
    positions = load_candidate_positions()
    tables, predictions, report = analysis_tables(root, positions)
    results = project / "reports" / "results"
    results.mkdir(parents=True, exist_ok=True)
    agreement_file = results / "coding_agreement.json"
    agreement = json.loads(agreement_file.read_text()) if agreement_file.is_file() else None
    quality = reference_quality(positions, agreement)
    numbers = build_numbers(predictions, report, positions, tables, quality)
    numbers |= storage_numbers(root)
    numbers |= crosscheck_numbers(load_crosscheck(root, CROSSCHECK_YEAR))
    files = {
        "model_comparison.csv": tables["comparison"].reset_index(),
        "signed_errors.csv": tables["errors"],
        "sensitivity.csv": tables["sensitivity"],
        "tied_groups.csv": tables["ties"],
        "blank_only.csv": tables["blank_only"],
        "territory_scores.csv": tables["territory"],
        "h2_threshold.csv": tables["threshold"],
        "h3_folds.csv": tables["h3_folds"],
    }
    for name, table in files.items():
        table.round(6).to_csv(results / name, index=False)
    (results / "candidate_table_quality.json").write_text(
        json.dumps(quality, indent=2, ensure_ascii=False) + "\n"
    )
    rounded = {k: round(v, 6) if isinstance(v, float) else v for k, v in numbers.items()}
    (results / "numbers.json").write_text(
        json.dumps(rounded, indent=2, ensure_ascii=False, default=float) + "\n"
    )
    written = [f"reports/results/{name}" for name in [*files, "candidate_table_quality.json"]]
    written.append("reports/results/numbers.json")
    if figures:
        from vote_transfer.application.figures import write_figures

        written += write_figures(tables, predictions, numbers, project / "reports" / "figures")
    written += render_documents(numbers, templates, project)
    return {
        "coding_status": report["coding_status"],
        "best_model": numbers["best.model"],
        "written": written,
    }
