"""Static figures for the report (PNG and SVG), drawn from the generated tables only."""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")  # no display needed; identical output from the CLI and tests

import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from matplotlib.colors import LinearSegmentedColormap  # noqa: E402

from vote_transfer.application.models import MAIN_VARIANT, NO_VARIANT  # noqa: E402
from vote_transfer.application.quality import territory_type  # noqa: E402

SURFACE, INK, MUTED, GRID = "#fcfcfb", "#0b0b0b", "#52514e", "#e6e5e0"
# Categorical slots in fixed order (validated: adjacent colour-vision separation passes).
ROLE_STYLE = {
    "finalist_a": ("Finalist A (first-round leader)", "#2a78d6"),
    "finalist_b": ("Finalist B", "#eb6834"),
    "blank_invalid": ("Blank / invalid", "#1baf7a"),
    "abstention": ("Abstention", "#eda100"),
}
TERRITORY_STYLE = {
    "metropolitan": ("Metropolitan areas", "#a3a29c", "o", 16),
    "overseas": ("Overseas areas", "#eb6834", "s", 34),
    "abroad": ("Voters abroad", "#2a78d6", "D", 44),
}
SEQUENTIAL = LinearSegmentedColormap.from_list(
    "blue", ["#eef5fe", "#cde2fb", "#86b6ef", "#3987e5", "#1c5cab"]
)
OUTLIER_COLUMN = "mean_without_2002"


def style() -> None:
    plt.rcParams.update(
        {
            "figure.facecolor": SURFACE,
            "axes.facecolor": SURFACE,
            "savefig.facecolor": SURFACE,
            "font.size": 9,
            "text.color": INK,
            "axes.labelcolor": MUTED,
            "axes.edgecolor": GRID,
            "xtick.color": MUTED,
            "ytick.color": MUTED,
            "axes.spines.top": False,
            "axes.spines.right": False,
            "axes.titlesize": 10,
            "axes.titleweight": "bold",
            "axes.titlelocation": "left",
            "svg.hashsalt": "vote-transfer",  # stable SVG ids across runs
        }
    )


def save(figure, folder: Path, name: str) -> list[str]:
    folder.mkdir(parents=True, exist_ok=True)
    figure.savefig(
        folder / f"{name}.png", dpi=200, bbox_inches="tight", metadata={"Software": None}
    )
    figure.savefig(folder / f"{name}.svg", bbox_inches="tight", metadata={"Date": None})
    plt.close(figure)
    return [f"reports/figures/{name}.png", f"reports/figures/{name}.svg"]


def comparison_figure(comparison: pd.DataFrame, numbers: dict):
    """Score per model and election as a labelled grid; lighter is closer to observed."""
    years = [c for c in comparison.columns if c.isdigit()]
    columns = [*years, "mean", OUTLIER_COLUMN]
    values = comparison[columns].to_numpy(float)
    figure, axis = plt.subplots(figsize=(7.2, 3.6))
    positions = [*range(len(years)), len(years) + 0.25, len(years) + 1.25]
    limit = np.nanmax(values)
    for j, x in enumerate(positions):
        for i in range(len(comparison)):
            value = values[i, j]
            axis.add_patch(
                plt.Rectangle(
                    (x - 0.48, i - 0.46), 0.96, 0.92, color=SEQUENTIAL(value / limit), linewidth=0
                )
            )
            axis.text(
                x,
                i,
                f"{value:.1f}",
                ha="center",
                va="center",
                color="white" if value / limit > 0.62 else INK,
                fontweight="bold" if value == np.nanmin(values[:, j]) else "normal",
            )
    axis.set_xlim(-0.5, positions[-1] + 0.5)
    axis.set_ylim(len(comparison) - 0.5, -0.5)
    axis.set_xticks(positions)
    axis.set_xticklabels([*years, "Mean", "Mean\nwithout 2002"])
    axis.xaxis.tick_top()
    axis.set_yticks(range(len(comparison)))
    axis.set_yticklabels(comparison.index)
    axis.tick_params(length=0)
    for spine in axis.spines.values():
        spine.set_visible(False)
    figure.text(
        0.01,
        -0.02,
        "Primary score: mean absolute error over four outcomes per area, weighted by round-two "
        "registered voters (pp).\nLower is closer to the observed result; bold marks the lowest "
        f"score in a column. H3 scores are held-out. {numbers['coding_status'].capitalize()}.",
        ha="left",
        va="top",
        color=MUTED,
        fontsize=7.5,
    )
    return figure


def signed_error_figure(errors: pd.DataFrame, numbers: dict, models: list[str]):
    """Signed national error by outcome and election: where each model fails."""
    main = errors[errors.variant.isin([NO_VARIANT, MAIN_VARIANT])]
    years = sorted(main.year.unique())
    figure, axes = plt.subplots(
        len(models), 1, figsize=(7.2, 2.25 * len(models)), sharex=True, sharey=True
    )
    width = 0.19
    for axis, model in zip(np.atleast_1d(axes), models, strict=True):
        of_model = main[main.model == model].set_index(["year", "role"]).signed_error_pp
        for k, (role, (label, colour)) in enumerate(ROLE_STYLE.items()):
            heights = [of_model[(year, role)] for year in years]
            x = np.arange(len(years)) + (k - 1.5) * (width + 0.02)
            axis.bar(x, heights, width, color=colour, label=label, linewidth=0)
            for xi, height in zip(x, heights, strict=True):
                if abs(height) >= 5:  # label only the errors that matter
                    axis.text(
                        xi,
                        height + (0.8 if height > 0 else -0.8),
                        f"{height:+.0f}",
                        ha="center",
                        va="bottom" if height > 0 else "top",
                        fontsize=7,
                        color=INK,
                    )
        axis.axhline(0, color=MUTED, linewidth=0.8)
        axis.set_title(model)
        axis.set_ylabel("Predicted − observed (pp)")
        axis.grid(axis="y", color=GRID, linewidth=0.6)
        axis.set_axisbelow(True)
    last = np.atleast_1d(axes)[-1]
    last.set_xticks(range(len(years)))
    last.set_xticklabels(
        [f"{y}\n{numbers[f'finalist_a.{y}']} (A)\n{numbers[f'finalist_b.{y}']} (B)" for y in years]
    )
    last.tick_params(axis="x", length=0)
    np.atleast_1d(axes)[0].legend(
        ncols=4, frameon=False, loc="lower left", bbox_to_anchor=(0, 1.16), fontsize=8, borderpad=0
    )
    figure.text(
        0.01,
        0.0,
        "Shares of registered voters pooled over covered areas. Positive: the model predicts too "
        f"much of that outcome.\nAggregate patterns, not individual transfers. "
        f"{numbers['coding_status'].capitalize()} for models that read candidate scores.",
        ha="left",
        va="top",
        color=MUTED,
        fontsize=7.5,
    )
    figure.subplots_adjust(hspace=0.32)
    return figure


def scatter_figure(predictions: pd.DataFrame, numbers: dict, model: str, year: int):
    """Predicted against observed shares by area for one election and one model."""
    frame = predictions[
        (predictions.model == model)
        & (predictions.year == year)
        & predictions.variant.isin([NO_VARIANT, MAIN_VARIANT])
    ].copy()
    frame["territory"] = frame.area_code.map(territory_type)
    titles = {
        "finalist_a": f"{numbers[f'finalist_a.{year}']} (finalist A)",
        "finalist_b": f"{numbers[f'finalist_b.{year}']} (finalist B)",
        "blank_invalid": "Blank / invalid",
        "abstention": "Abstention",
    }
    figure, axes = plt.subplots(2, 2, figsize=(7.2, 7.0))
    for axis, (role, title) in zip(axes.ravel(), titles.items(), strict=True):
        of_role = frame[frame.role == role]
        low = 0
        high = max(of_role.predicted_share.max(), of_role.actual_share.max()) * 105
        axis.plot([low, high], [low, high], color=MUTED, linewidth=0.8, linestyle="--", zorder=1)
        for territory, (label, colour, marker, size) in TERRITORY_STYLE.items():
            points = of_role[of_role.territory == territory]
            axis.scatter(
                points.actual_share * 100,
                points.predicted_share * 100,
                s=size,
                c=colour,
                marker=marker,
                label=label,
                edgecolors=SURFACE,
                linewidths=0.6,
                zorder=3 if territory != "metropolitan" else 2,
            )
            if territory != "metropolitan":
                for point in points.itertuples():
                    axis.annotate(
                        point.area_code,
                        (point.actual_share * 100, point.predicted_share * 100),
                        xytext=(4, 3),
                        textcoords="offset points",
                        fontsize=6.5,
                        color=MUTED,
                    )
        axis.set_xlim(low, high)
        axis.set_ylim(low, high)
        axis.set_aspect("equal")
        axis.set_title(title)
        axis.set_xlabel("Observed (% of registered)")
        axis.set_ylabel(f"{model} (% of registered)")
        axis.grid(color=GRID, linewidth=0.6)
        axis.set_axisbelow(True)
    axes[0, 0].legend(frameon=False, loc="lower left", bbox_to_anchor=(0, 1.1), ncols=3, fontsize=8)
    figure.text(
        0.01,
        0.02,
        f"{year} second round, one point per reporting area. On the dashed line the model equals "
        "the observed share; above it the model predicts too much.\nZ-codes are overseas areas; "
        f"ZZ is voters abroad. {numbers['coding_status'].capitalize()}.",
        ha="left",
        va="top",
        color=MUTED,
        fontsize=7.5,
    )
    figure.subplots_adjust(hspace=0.38, wspace=0.3)
    return figure


def write_figures(
    tables: dict, predictions: pd.DataFrame, numbers: dict, folder: Path
) -> list[str]:
    style()
    best = numbers["best.model"]
    panel_models = list(dict.fromkeys(["H0a", "H0b", best]))
    written = save(comparison_figure(tables["comparison"], numbers), folder, "model_comparison")
    written += save(
        signed_error_figure(tables["errors"], numbers, panel_models),
        folder,
        "signed_error_by_outcome",
    )
    written += save(
        scatter_figure(predictions, numbers, best, 2022), folder, "predicted_vs_observed_2022"
    )
    return written
