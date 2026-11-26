"""2. Data: sources, acquisition, quality, cleaning, candidate positions and storage."""

import json

import altair as alt
import numpy as np
import pandas as pd
import streamlit as st

import data
import ui

PAGE = "data_page"
DATASETS = {
    2002: "https://www.data.gouv.fr/datasets/election-presidentielle-2002-resultats-par-bureaux-de-vote",
    2007: "https://www.data.gouv.fr/datasets/election-presidentielle-2007-resultats-par-bureaux-de-vote",
    2012: "https://www.data.gouv.fr/datasets/election-presidentielle-2012-resultats-par-bureaux-de-vote-1",
    2017: "https://www.data.gouv.fr/datasets/election-presidentielle-des-23-avril-et-7-mai-2017-resultats-definitifs-du-1er-tour-par-bureaux-de-vote",
    2022: "https://www.data.gouv.fr/datasets/election-presidentielle-des-10-et-24-avril-2022-resultats-definitifs-du-1er-tour/",
}


def render() -> None:
    ui.header(
        "Section 2 · Data",
        "From raw polling-station files to tables we trust",
        "Two sources, zero-tolerance checks, no observation altered, one storage decision.",
    )
    _sources()
    _acquisition()
    _quality()
    _cleaning()
    _positions()
    _storage()


# ---- 2.1 -------------------------------------------------------------------------------


def _sources() -> None:
    ui.section(PAGE, "s2-1")
    st.markdown(
        "We started from the question and kept only the data it needs. If either source "
        "below were removed, the question could not be answered."
    )
    ui.text_table(
        pd.DataFrame(
            {
                "Source": [
                    "<b>Official results</b><br>Ministry of the Interior, via data.gouv.fr",
                    "<b>Candidate positions</b><br>left-to-right orders published by polling institutes",
                ],
                "What we take": [
                    "Both rounds of 2002–2022, one row per polling station and candidate",
                    "22 orders of candidates, from 9 institutes, one per poll",
                ],
                "How we get it": [
                    "A script downloads the original files and checks their hash",
                    "Collected <b>by hand</b> from the institutes' reports and one published paper",
                ],
                "Used for": [
                    "Round 1 = input of every rule; round 2 = ground truth",
                    "H1, H1-soft, H2 and H3 (where is each candidate?)",
                ],
            }
        )
    )
    ui.caption("Table 2.1", "The two sources that remain after narrowing the project.")
    with st.expander("Sources we considered and dropped, and why"):
        ui.text_table(
            pd.DataFrame(
                [
                    (
                        "Consolidated election dataset (data.gouv.fr)",
                        "Same results, already harmonised",
                        "Kept only to <i>check</i> our own cleaning: we wanted every aggregation step to be ours.",
                    ),
                    (
                        "INSEE socioeconomic indicators",
                        "Explain regional differences",
                        "Dropped after the proposal feedback: the question does not need them.",
                    ),
                    (
                        "GDELT / regional press mentions of 2027 candidates",
                        "Media attention",
                        "Dropped: it explained no variable in our question.",
                    ),
                    (
                        "Chapel Hill Expert Survey (CHES)",
                        "Party left–right scores",
                        "Rates parties, not candidacies; misses most minor candidates.",
                    ),
                    (
                        "Political Compass, CEVIPOF",
                        "2D candidate positions",
                        "No 2D position exists for all 61 candidacies; dropped with 2D distances.",
                    ),
                    (
                        "Voter Autrement 2017",
                        "Individual preferences (H4, H5)",
                        "One 2017 volunteer survey cannot describe five elections (peer review 1).",
                    ),
                    (
                        "Wikipedia 2027 polls",
                        "2027 simulation",
                        "The 2027 scenario was dropped on 20 November to stay on the main question.",
                    ),
                ],
                columns=["Source", "Intended use", "Why dropped"],
            )
        )
    ui.box(
        "decision",
        "<p>Keep <b>two inputs only</b>. This follows the professor's feedback on the proposals "
        "(“determine the data from the question”) and the first peer review, which warned "
        "about scope creep across six external datasets.</p>",
    )


# ---- 2.2 -------------------------------------------------------------------------------


def _acquisition() -> None:
    ui.section(PAGE, "s2-2")
    st.markdown(
        "The Ministry publishes one file per election with one line per polling station "
        "(*bureau de vote*). We use these **original station files** rather than ready-made "
        "national tables, so every aggregation step is ours and can be checked."
    )
    st.markdown(
        "- `vote-transfer acquire` asks the data.gouv.fr API for a **pinned resource "
        "identifier** per election and round.\n"
        "- It records the URL, the date, the size and the **SHA-256 hash** of each file in a "
        "versioned manifest.\n"
        "- Any later download must reproduce the hash; processing refuses any other bytes.\n"
        "- A clean re-download on 31 October 2026 reproduced every hash."
    )
    rows = []
    for year in data.YEARS:
        manifest = json.loads(
            (data.PROJECT / "data/raw/official" / str(year) / "manifest.json").read_text()
        )
        files = manifest["files"]
        q = data.quality(year)
        stations = q["diagnostics"]["stations_by_round"]["1"]["station_rows"]
        rows.append(
            {
                "Election": year,
                "Files": len({f["sha256"] for f in files}),
                "Size (MB)": round(sum({f["sha256"]: f["bytes"] for f in files}.values()) / 1e6, 1),
                "Polling stations": stations,
                "Areas": len(data.election(year).areas),
                "Dataset": DATASETS[year],
            }
        )
    st.dataframe(
        pd.DataFrame(rows),
        hide_index=True,
        width="stretch",
        column_config={
            "Dataset": st.column_config.LinkColumn(display_text="data.gouv.fr"),
            "Election": st.column_config.NumberColumn(format="%d"),
            "Polling stations": st.column_config.NumberColumn(format="localized"),
        },
    )
    ui.caption(
        "Table 2.2",
        "The five elections. 2002–2012 publish both rounds in one file. 2002 and 2007 have no "
        "voters abroad and fewer overseas areas (100 and 101 areas against 107), so for those "
        "years every total means <i>covered areas</i>, not France.",
    )
    with st.expander("What a manifest looks like (2022, round 1)"):
        manifest = json.loads((data.PROJECT / "data/raw/official/2022/manifest.json").read_text())
        st.json(manifest["files"][0])
    with st.expander("Three file layouts in twenty years"):
        st.markdown(
            "- All files are encoded in **Windows-1252**, not UTF-8.\n"
            "- In 2017 and 2022 only the **first candidate block has a header**: a naive "
            "reader would silently lose most votes. We parse every block and check that "
            "candidate votes add up to valid ballots.\n"
            "- Ballot panel numbers change between rounds, so candidates are keyed **by name** "
            "within each election.\n"
            "- Area codes such as `01`, `2A` and `ZZ` must stay **text** (a spreadsheet turns "
            "`01` into `1`).\n"
            "- Area names are missing before 2017."
        )


# ---- 2.3 -------------------------------------------------------------------------------


def _quality() -> None:
    ui.section(PAGE, "s2-3")
    st.markdown(
        "Quality is judged against our use. For each area and round we need counts that "
        "**add up exactly** to the registered electorate (candidates + blank/invalid + "
        "abstention), and the two rounds must cover the same areas."
    )
    ui.box(
        "decision",
        "<p><b>Zero tolerance.</b> These are official counts, so a violated check can only mean "
        "that <i>we</i> parsed a file wrongly. The pipeline <b>stops</b> instead of repairing "
        "anything.</p>",
    )
    ui.text_table(
        pd.DataFrame(
            [
                (
                    "Validity",
                    "Schema per layout; non-negative integers; voters ≤ registered; valid ≤ voters",
                    "0 violations",
                ),
                ("Completeness", "Required counts present", "100%"),
                ("Completeness", "Separate blank and invalid counts", "0% before 2017, 100% after"),
                ("Uniqueness", "Duplicate station or (station, candidate) keys", "0"),
                (
                    "Consistency",
                    "Candidate votes = valid ballots in every station; same areas in both rounds",
                    "0 violations",
                ),
                (
                    "Consistency",
                    "2022 sums against the Ministry's national summaries",
                    "26 / 26 fields match",
                ),
            ],
            columns=["Characteristic", "Metric", "Result (all years)"],
        )
    )
    ui.caption("Table 2.3", "Checks that can be decided from the data alone.")

    st.markdown("### Findings that need context")
    st.markdown(
        "Some values are unusual but **correct**. We flag them with Tukey's IQR fences (robust "
        "to a few extreme areas) and keep them: a flag means *look closer*, not *wrong*."
    )
    st.altair_chart(_abstention_flags(), width="stretch")
    ui.caption(
        "Figure 2.1",
        "First-round abstention of every area, by election. Points outside the IQR fences "
        "(coloured) are flagged: Corsica, overseas areas, voters abroad, sometimes "
        "Seine-Saint-Denis. These are real participation differences, so they stay in the data.",
    )
    with st.expander("Other contextual findings"):
        ui.text_table(
            pd.DataFrame(
                [
                    (
                        "2022: about 10 stations per round with 0 registered voters, 34–35 with nobody voting",
                        "They add nothing to any total, or count as abstention",
                    ),
                    (
                        "One station abroad with 123,786 registered voters (median: 753)",
                        "Consular “stations”: a feature of the frame",
                    ),
                    (
                        "3–6% of stations are turnout outliers; 50–63% of them overseas or abroad",
                        "Same pattern as at area level",
                    ),
                    (
                        "Registration changes between rounds: −0.7% to +0.3% (abroad, 2012: +3.35%)",
                        "Each round keeps its own denominator",
                    ),
                ],
                columns=["Finding", "Interpretation"],
            )
        )


def _abstention_flags() -> alt.Chart:
    rows = []
    for year in data.YEARS:
        e = data.election(year)
        i = e.groups.index("abstention")
        values = e.first[:, i] * 100
        q1, q3 = np.percentile(values, [25, 75])
        lo, hi = q1 - 1.5 * (q3 - q1), q3 + 1.5 * (q3 - q1)
        res = data.results(year)
        names = dict(zip(res.department_code, res.department_name, strict=False))
        for code, v in zip(e.areas, values, strict=True):
            rows.append(
                {
                    "year": str(year),
                    "area": f"{code} · {names.get(code, code)}",
                    "abstention": v,
                    "flag": "Flagged and kept" if (v < lo or v > hi) else "Within fences",
                }
            )
    frame = pd.DataFrame(rows)
    return (
        alt.Chart(frame)
        .mark_circle(size=46, opacity=0.8)
        .encode(
            y=alt.Y("year:N", title=None, sort=[str(y) for y in data.YEARS]),
            x=alt.X("abstention:Q", title="First-round abstention, % of registered voters"),
            yOffset=alt.YOffset("jitter:Q", scale=alt.Scale(domain=[-1, 1])),
            color=alt.Color(
                "flag:N",
                scale=alt.Scale(
                    domain=["Within fences", "Flagged and kept"], range=["#9AA0A8", "#C2410C"]
                ),
                title=None,
            ),
            tooltip=["area", "year", alt.Tooltip("abstention:Q", format=".1f")],
        )
        .transform_calculate(jitter="sqrt(-2*log(random()))*cos(2*PI*random())*0.3")
        .properties(height=alt.Step(52))
    )


# ---- 2.4 -------------------------------------------------------------------------------


def _cleaning() -> None:
    ui.section(PAGE, "s2-4")
    st.markdown(
        "We **removed, imputed or corrected no observation**. Every count is used as published, "
        "or derived by an exact identity. Four decisions shape the analysis."
    )

    st.markdown("### Decision 1 · Shares of registered voters, not of valid votes")
    st.markdown(
        "Abstention and blank ballots are outcomes we must predict, so they have to be in the "
        "denominator. This is why our percentages are lower than the ones reported on TV:"
    )
    st.latex(
        r"\text{share}_{a,o} = \frac{\text{count}_{a,o}}{\text{registered}_a}\qquad\text{(not }\frac{\text{count}_{a,o}}{\text{valid votes}_a}\text{)}"
    )
    st.altair_chart(_denominator_chart(), width="stretch")
    ui.caption(
        "Figure 2.2",
        "2022, round 1. The same votes as a share of registered voters (our basis) and of valid "
        "votes (the usual headline figure). Macron: 20.1% against 27.8%.",
    )

    st.markdown("### Decision 2 · Blank and invalid ballots are merged")
    c1, c2 = st.columns([3, 2])
    with c1:
        st.markdown(
            "- Before 2017 the Ministry publishes **only the total** of blank and invalid "
            "ballots.\n"
            "- We use the combined outcome in **every** election, so it means the same thing "
            "each year.\n"
            "- The separate counts of 2017 and 2022 are stored (null before, never zero) and "
            "used in a **sensitivity analysis** (Results, 4.6)."
        )
    with c2:
        st.altair_chart(_blank_invalid_chart(), width="stretch")
    ui.box(
        "limit",
        "<p>About a quarter of the second-round category is <b>invalid</b> ballots, which "
        "partly reflect mistakes rather than a choice. No behavioural rule can be expected to "
        "explain them (raised by the second peer review).</p>",
    )

    st.markdown("### Decision 3 · Unusual areas are flagged, not removed")
    st.markdown(
        "Overseas areas and voters abroad behave differently, but they are part of the "
        "electorate we study. Keeping them barely changes the baseline score: in 2022, "
        "**6.12 pp** over all areas against **5.82 pp** over metropolitan areas only."
    )

    st.markdown("### Decision 4 · One observation is one area, not one polling station")
    st.markdown(
        "We add the ~65,000–70,000 polling stations of each round into **100–107 areas** "
        "(départements, overseas territories, voters abroad): **522 area-elections** in total."
    )
    col1, col2 = st.columns(2)
    with col1:
        ui.box(
            "decision",
            "<ul><li>It is the unit fixed in our approved acquisition note.</li>"
            "<li>Polling-station codes and commune boundaries change between elections; areas "
            "are stable over 20 years.</li>"
            "<li>A station has a few hundred voters, so its shares are noisy.</li></ul>",
            label="Why areas",
        )
    with col2:
        ui.box(
            "limit",
            "<ul><li>Aggregation hides variation inside an area and cannot be reversed.</li>"
            "<li>Coarser units widen the range of behaviours compatible with the totals.</li>"
            "<li>Testing rules at station level, within each election, is the next step.</li></ul>",
            label="What it costs",
        )

    with st.expander("Every cleaning operation, with its justification"):
        ui.text_table(
            pd.DataFrame(
                [
                    (
                        "Upstream file changed",
                        "Stop (hash check)",
                        "Results must refer to the reviewed bytes",
                    ),
                    (
                        "Layout differs by year",
                        "Year-specific parser; stop on an unknown schema",
                        "A silent schema change would shift columns",
                    ),
                    (
                        "Unlabelled candidate blocks",
                        "Parse every block (wide → long)",
                        "Candidate sums prove no vote is lost",
                    ),
                    (
                        "Panel numbers change between rounds",
                        "Key candidates by name, within each year",
                        "Names are stable within an election",
                    ),
                    (
                        "Abstention, blank/invalid not published (2002–12)",
                        "Derive exactly; record as derived",
                        "Arithmetic, not an estimate",
                    ),
                    (
                        "Blank/invalid split missing (2002–12)",
                        "Keep as null; use the combined outcome",
                        "No invented data; one definition",
                    ),
                    (
                        "Comment lines, other round's rows",
                        "Filter, with counts",
                        "Out of scope; nothing else is skipped",
                    ),
                    (
                        "Unusual areas or stations",
                        "Flag and retain",
                        "Valid evidence about the electorate",
                    ),
                    (
                        "Missing areas in 2002/2007",
                        "Retain; label as “covered areas”",
                        "Cannot be recovered",
                    ),
                ],
                columns=["Issue", "Response", "Justification"],
            )
        )
    with st.expander("Ledger: every raw line accounted for (2002)"):
        ledger = pd.DataFrame(
            {
                "Line type": [
                    "Round 1 candidate rows",
                    "Round 2 candidate rows",
                    "Comment lines",
                    "Empty lines",
                ],
                "Lines": [1_026_256, 128_282, 17, 1],
            }
        )
        st.dataframe(
            ledger,
            hide_index=True,
            width="stretch",
            column_config={"Lines": st.column_config.NumberColumn(format="localized")},
        )
        st.markdown(
            "1,154,556 lines in total. Candidate totals are then joined to area totals as "
            "many-to-one, and an outer-join coverage check stops on any unmatched station."
        )


def _denominator_chart() -> alt.Chart:
    res = data.results(2022)
    r1 = res[(res["round"] == 1) & res.option.str.startswith("candidate:")]
    totals = r1.groupby("option")["count"].sum()
    registered = res[res["round"] == 1].drop_duplicates("department_code").registered.sum()
    frame = pd.DataFrame(
        {
            "candidate": [data.name(2022, o) for o in totals.index],
            "Share of registered voters": totals.to_numpy() / registered * 100,
            "Share of valid votes": totals.to_numpy() / totals.sum() * 100,
        }
    ).melt(id_vars="candidate", var_name="basis", value_name="share")
    order = list(
        frame[frame.basis == "Share of valid votes"].sort_values("share", ascending=False).candidate
    )
    y = alt.Y("candidate:N", sort=order, title=None, axis=alt.Axis(labelLimit=180))
    line = (
        alt.Chart(frame)
        .mark_line(color=ui.RULE, strokeWidth=3)
        .encode(y=y, x="share:Q", detail="candidate:N")
    )
    dots = (
        alt.Chart(frame)
        .mark_circle(size=90, opacity=1)
        .encode(
            y=y,
            x=alt.X("share:Q", title="% in round 1, 2022"),
            color=alt.Color(
                "basis:N",
                scale=alt.Scale(
                    domain=["Share of registered voters", "Share of valid votes"],
                    range=[ui.ACCENT, "#B9BEC5"],
                ),
                title=None,
            ),
            tooltip=["candidate", "basis", alt.Tooltip("share:Q", format=".1f")],
        )
    )
    return alt.layer(line, dots).properties(height=alt.Step(22))


def _blank_invalid_chart() -> alt.Chart:
    rows = []
    for year in (2017, 2022):
        a = pd.read_parquet(data.PROJECT / "data" / "bundled" / str(year) / "areas.parquet")
        g = a.groupby("round")[["registered", "blank", "invalid"]].sum()
        for rnd, r in g.iterrows():
            for kind in ("blank", "invalid"):
                rows.append(
                    {
                        "election": f"{year} · round {rnd}",
                        "kind": kind.capitalize(),
                        "share": r[kind] / r.registered * 100,
                    }
                )
    frame = pd.DataFrame(rows)
    return (
        alt.Chart(frame)
        .mark_bar()
        .encode(
            y=alt.Y("election:N", title=None),
            x=alt.X("share:Q", title="% of registered voters", stack="zero"),
            color=alt.Color(
                "kind:N",
                scale=alt.Scale(domain=["Blank", "Invalid"], range=["#3E9C7E", "#A9D5C6"]),
                title=None,
            ),
            tooltip=["election", "kind", alt.Tooltip("share:Q", format=".2f")],
        )
        .properties(height=alt.Step(30))
    )


# ---- 2.5 -------------------------------------------------------------------------------


def _positions() -> None:
    ui.section(PAGE, "s2-5")
    st.markdown(
        "Four of our rules need to know **where each candidate stands** on the left–right axis. "
        "This is the only input they add to the baseline, so it decides which finalist each "
        "eliminated group is sent to."
    )
    ui.box(
        "decision",
        "<p>Use the <b>left-to-right orders that polling institutes publish</b> in their "
        "reports, averaged over institutes. They cover every candidate, minor ones included, "
        "and come from outside the team. This followed the advice of Magdaléna Tydrichová "
        "(voting theory) after the second peer review questioned our own coding.</p>",
    )
    st.markdown(
        "**From orders to a score.** In a poll listing $n$ candidates, the candidate in place $i$ (counting from 0) gets"
    )
    st.latex(
        r"\text{position}_{c,\text{poll}} = \frac{i}{n-1}\in[0,1],\qquad \text{score}_c = \frac{1}{|P|}\sum_{\text{poll}\in P}\text{position}_{c,\text{poll}}"
    )
    st.markdown(
        "where $P$ is the set of polls of that election. 0 is the leftmost candidate, 1 the rightmost."
    )

    p = data.polls()
    counts = p.groupby("year").agg(
        polls=("institute", "size"), institutes=("institute", lambda s: ", ".join(s))
    )
    ui.html(
        '<table class="paper"><thead><tr><th>Election</th><th>Polls</th>'
        '<th style="text-align:left">Institutes</th></tr></thead><tbody>'
        + "".join(
            f"<tr><td>{y}</td><td>{r.polls}</td><td style='text-align:left'>{r.institutes}</td></tr>"
            for y, r in counts.iterrows()
        )
        + "</tbody></table>"
    )
    ui.caption(
        "Table 2.4",
        "Polls collected per election. 2017 and 2022 orders come from the compilation by Delemazure, Dong, Peters and Tydrichová (2024).",
    )
    ui.box(
        "limit",
        "<p><b>2002 rests on a single poll</b> (Ipsos, the only original report we found). This "
        "matters, because 2002 is the election that decides the overall ranking (Results, 4.2).</p>",
    )
    year = st.segmented_control("Election", data.YEARS, default=2022, key="data_year") or 2022
    st.altair_chart(ui.position_strip(year), width="stretch")
    ui.caption(
        f"Figure 2.3 ({year})",
        "Each circle is a candidate, sized by first-round share of registered voters. Shaded "
        "zones are at least one third of the scale from <i>both</i> finalists: there, rule H2 "
        "sends voters to a non-vote. The score is an order, not a measured distance.",
    )

    st.markdown("### Do institutes agree?")
    st.altair_chart(_agreement_chart(), width="stretch")
    ui.caption(
        "Figure 2.4",
        "Range between the lowest and highest position given to each candidate by different "
        "institutes (2007–2022; 2002 has one poll). Above 0.4 (dashed line), a candidate is "
        "<b>unplaced</b>: Lassalle 2017. Cheminade (2012, 2017) is also unplaced because "
        "institutes list him last by default. Unplaced voters follow the H0b rule.",
    )
    with st.expander("How we got here: from CHES to our own scale to the polls"):
        st.markdown(
            "1. **Acquisition note (2 Oct.)**: planned to map each candidate to a party in the "
            "*Chapel Hill Expert Survey*. It rates parties, not candidacies, and misses most "
            "minor candidates.\n"
            "2. **31 October**: we coded seven political families by hand (far left = 1 … far "
            "right = 7).\n"
            "3. **Second peer review (10 Nov.)**: all 61 rows were drafts, two thirds had a "
            "plausible alternative, ties were frequent and nobody had checked the table.\n"
            "4. **20 November**: we replaced our coding with the institutes' published orders. "
            "Our 1–7 scale is kept only as a **robustness check** (Results, 4.5)."
        )
        st.markdown(
            "We did not run the two-coder agreement study the reviewers proposed: agreement "
            "between two of us measures our consistency, not whether the positions are right."
        )


def _agreement_chart() -> alt.Chart:
    s = pd.read_csv(data.REFERENCE / "candidate_scores.csv")
    s = s[(s.n_institutes > 1)].copy()
    names = data.positions().set_index(["year", "candidate_id"]).candidate_name
    s["candidate"] = [
        f"{names.get((y, c), c)} ({y})" for y, c in zip(s.year, s.candidate_id, strict=True)
    ]
    s["status"] = s.status.str.capitalize()
    s = s.sort_values("range", ascending=False).head(18)
    bars = (
        alt.Chart(s)
        .mark_bar(height={"band": 0.7})
        .encode(
            y=alt.Y("candidate:N", sort="-x", title=None, axis=alt.Axis(labelLimit=220)),
            x=alt.X(
                "range:Q",
                title="Disagreement between institutes (highest − lowest position)",
                scale=alt.Scale(domain=[0, 0.7]),
            ),
            color=alt.Color(
                "status:N",
                scale=alt.Scale(domain=["Placed", "Unplaced"], range=[ui.ACCENT, "#C2410C"]),
                title=None,
            ),
            tooltip=["candidate", alt.Tooltip("range:Q", format=".2f"), "n_institutes"],
        )
    )
    rule = (
        alt.Chart(pd.DataFrame({"x": [0.4]}))
        .mark_rule(strokeDash=[4, 3], color=ui.INK)
        .encode(x="x:Q")
    )
    return (bars + rule).properties(height=alt.Step(20))


# ---- 2.6 -------------------------------------------------------------------------------


def _storage() -> None:
    ui.section(PAGE, "s2-6")
    st.markdown(
        "Raw files are kept **unchanged**. Cleaned data is stored as **Parquet files in a "
        "normalised layout**; shares are never stored, they are computed when data is read."
    )
    ui.text_table(
        pd.DataFrame(
            [
                (
                    "<code>areas</code>",
                    "year, round, area",
                    "registered voters, polling stations, blank, invalid",
                    "1,044",
                ),
                ("<code>outcomes</code>", "year, round, area, option", "count", "9,475"),
                ("<code>options</code>", "year, option", "label", "71"),
                (
                    "<code>predictions</code>",
                    "model, variant, year, area, outcome",
                    "predicted and actual share, weight",
                    "91,872",
                ),
            ],
            columns=["Table", "Key", "Columns", "Rows"],
        )
    )
    ui.caption(
        "Table 2.5",
        "The data model. The wide table used by the site is a view built on load, not a stored copy.",
    )
    n = data.numbers()
    ui.stats(
        [
            (
                f"{n['storage.total_parquet_kb']:.0f} kB",
                "all processed tables and predictions, as Parquet",
            ),
            (
                f"{n['storage.total_csv_kb'] / 1000:.1f} MB",
                f"the same tables as CSV ({n['storage.csv_to_parquet_ratio']:.0f}× larger)",
            ),
            (f"{n['storage.prediction_rows']:,}", "rows in the predictions table"),
            ("0", "servers or accounts needed to reproduce"),
        ]
    )
    st.markdown("### Three options against what our data needs")
    ui.text_table(
        pd.DataFrame(
            {
                "Need": [
                    "Written once by one process",
                    "Read whole columns",
                    "Join models × elections",
                    "Reproduced by a classmate",
                    "Keys and constraints",
                ],
                "Parquet files (chosen)": [
                    "✅ One file per table",
                    "✅ Columnar",
                    "➖ In pandas after loading",
                    "✅ Byte-identical rebuild, hash per file, fits in Git",
                    "➖ Enforced by our code on every write and load",
                ],
                "SQLite / PostgreSQL": [
                    "➖ Transactions solve a problem we do not have",
                    "➖ Row-oriented",
                    "✅ SQL joins and views",
                    "❌ Binary file not byte-stable; PostgreSQL needs a server",
                    "✅ Declarative: the engine refuses bad rows",
                ],
                "DuckDB over Parquet": [
                    "Not a storage change",
                    "✅ Columnar",
                    "✅ SQL directly on our files",
                    "✅ One extra package",
                    "❌ None of its own",
                ],
            }
        )
    )
    ui.caption(
        "Table 2.6",
        "We tested the relational option concretely: a test loads our 2022 tables into SQLite "
        "with primary keys, foreign keys and CHECK constraints, and gets the same shares.",
    )
    col1, col2 = st.columns(2)
    with col1:
        ui.box(
            "decision",
            "<p><b>Parquet.</b> Our data is written once, read by column, small, and must be "
            "rebuilt <i>exactly</i> by a reader with no setup.</p>",
        )
    with col2:
        ui.box(
            "limit",
            "<ul><li>Constraints are checked by code, not declared.</li><li>Joins live in Python.</li>"
            "<li>Two copies (processed, bundled) can diverge: a check detects it.</li></ul>",
            label="What we give up",
        )
    with st.expander("Why the small reference tables stay as CSV"):
        st.markdown(
            "The poll orders, the candidate scores and the hand-coded comparison table are "
            "small, typed or regenerated by hand, and reviewed **line by line in Git**. Their "
            "types and rules are enforced when they are read. Scores keep every decimal: rounded "
            "to three decimals, a candidate exactly halfway between the finalists (Boutin, 2002) "
            "would no longer count as a tie."
        )
    with st.expander("How the storage changed after the second peer review"):
        st.markdown(
            "- One `h0_evaluation.parquet` per election became **one long predictions table** "
            "with `model`, `variant` and `train_elections` columns.\n"
            "- The wide table with a repeated `registered` column was split into **areas** and "
            "**outcomes** tables (no more risk of summing the denominator).\n"
            "- Separate blank and invalid counts are now stored for 2017 and 2022.\n"
            "- A check compares the processed and bundled copies on every `make check` and at "
            "app start-up."
        )
