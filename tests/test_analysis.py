"""Generated analysis outputs: tables, numbers, figures and rendered documents."""

import json
from pathlib import Path

import pandas as pd
import pytest
from vote_transfer.application.analysis import (
    MODEL_ORDER,
    RENDERED,
    TEMPLATES_DIR,
    analysis_tables,
    render_template,
    run_analysis,
)
from vote_transfer.application.positions import load_candidate_positions

PROJECT = Path(__file__).resolve().parents[1]
DATA = PROJECT / "data"
YEARS = ["2002", "2007", "2012", "2017", "2022"]


@pytest.fixture(scope="module")
def bundled_root(tmp_path_factory):
    """Only the versioned snapshots: what a fresh clone has."""
    import shutil

    root = tmp_path_factory.mktemp("data")
    shutil.copytree(DATA / "bundled", root / "bundled")
    return root


@pytest.fixture(scope="module")
def generated(bundled_root, tmp_path_factory):
    project = tmp_path_factory.mktemp("project")
    summary = run_analysis(bundled_root, project=project)
    return project, summary


@pytest.fixture(scope="module")
def tables(bundled_root):
    return analysis_tables(bundled_root, load_candidate_positions())[0]


def test_templates_take_numbers_only_from_the_generated_map():
    numbers = {"score.H1.mean": 4.348, "best.model": "H1", "n": 5}
    text = "{{best.model}} scores {{score.H1.mean}} ({{ score.H1.mean | .2f }}) on {{n}}."
    assert render_template(text, numbers) == "H1 scores 4.3 (4.35) on 5."
    with pytest.raises(ValueError, match="not generated"):
        render_template("{{score.H9.mean}}", numbers)


def test_one_command_writes_every_result_figure_and_document(generated):
    project, summary = generated
    assert summary["coding_status"] == "draft coding"
    for name in (
        "model_comparison.csv",
        "signed_errors.csv",
        "sensitivity.csv",
        "tied_groups.csv",
        "blank_only.csv",
        "territory_scores.csv",
        "h3_folds.csv",
        "candidate_table_quality.json",
        "numbers.json",
        "findings.md",
    ):
        assert (project / "reports/results" / name).stat().st_size > 0
    for figure in ("model_comparison", "signed_error_by_outcome", "predicted_vs_observed_2022"):
        assert (project / f"reports/figures/{figure}.png").read_bytes().startswith(b"\x89PNG")
        assert "<svg" in (project / f"reports/figures/{figure}.svg").read_text()
    for name, target in RENDERED.items():
        if (TEMPLATES_DIR / name).is_file():
            rendered = (project / target).read_text()
            assert "{{" not in rendered
            assert rendered.startswith("<!-- Generated from")


def test_committed_results_and_documents_match_a_fresh_run(generated):
    """No number in the repository may differ from what the code produces today."""
    project, _ = generated
    committed = json.loads((PROJECT / "reports/results/numbers.json").read_text())
    fresh = json.loads((project / "reports/results/numbers.json").read_text())
    assert committed == fresh
    for name in ("model_comparison.csv", "sensitivity.csv", "blank_only.csv", "h3_folds.csv"):
        pd.testing.assert_frame_equal(
            pd.read_csv(PROJECT / "reports/results" / name),
            pd.read_csv(project / "reports/results" / name),
        )
    for name, target in RENDERED.items():
        if (TEMPLATES_DIR / name).is_file():
            assert (PROJECT / target).read_text() == (project / target).read_text(), target


def test_comparison_table_means_and_ranks(tables):
    comparison = tables["comparison"]
    assert list(comparison.index) == list(MODEL_ORDER)
    assert comparison["mean"].tolist() == pytest.approx(comparison[YEARS].mean(axis=1).tolist())
    assert comparison["mean_without_2002"].tolist() == pytest.approx(
        comparison[YEARS[1:]].mean(axis=1).tolist()
    )
    assert comparison["rank"].min() == 1
    assert comparison.loc[comparison["mean"].idxmin(), "rank"] == 1


def test_h3_scores_in_the_comparison_are_the_held_out_scores(tables):
    folds = tables["h3_folds"]
    main = folds[(folds.variant == "positions=primary;tie=split") & folds.test_year.notna()]
    for fold in main.itertuples():
        score = tables["comparison"].loc[f"H3({fold.base})", str(int(fold.test_year))]
        assert score == pytest.approx(fold.heldout_score_pp, abs=1e-9)
        assert str(int(fold.test_year)) not in fold.train_elections.split(",")


def test_signed_errors_cancel_across_the_four_outcomes(tables):
    errors = tables["errors"]
    sums = errors.groupby(["model", "variant", "year"]).signed_error_pp.sum()
    assert sums.abs().max() < 1e-8
    assert set(errors.role) == {"finalist_a", "finalist_b", "blank_invalid", "abstention"}


def test_blank_only_table_decomposes_the_combined_error(tables):
    blank = tables["blank_only"]
    assert set(blank.year) == {2017, 2022}  # the split is not published before 2017
    assert (blank.signed_blank_pp + blank.signed_invalid_pp).tolist() == pytest.approx(
        blank.signed_blank_invalid_pp.tolist()
    )
    assert blank.groupby("year").signed_invalid_pp.nunique().eq(1).all()  # model-independent
    for row in blank.itertuples():
        expected = tables["comparison"].loc[row.model, str(row.year)]
        assert row.score_4_outcomes_pp == pytest.approx(expected, abs=1e-9)


def test_sensitivity_covers_every_setting_and_keeps_baselines_fixed(tables):
    sensitivity = tables["sensitivity"]
    assert len(sensitivity) == 4 * len(MODEL_ORDER)
    for model in ("H0a", "H0b"):
        assert sensitivity[sensitivity.model == model]["mean"].nunique() == 1
    assert sensitivity[sensitivity.model == "H1"]["mean"].nunique() > 1


def test_analysis_refuses_stale_or_missing_predictions(tmp_path):
    with pytest.raises(ValueError, match="No predictions"):
        run_analysis(tmp_path, project=tmp_path, figures=False)
