"""Data: collection, cleaning and storage, each with its choice, alternative and limit."""

import json

import pandas as pd
import streamlit as st

import data
import ui

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
        "Two sources, seven quality checks, one storage decision.",
    )

    st.markdown("## 2.1 Collection")
    st.markdown(
        "**Source 1: official results.** The Ministry of the Interior publishes one file per "
        "election with one line per polling station (*bureau de vote*) and per candidate. We "
        "use the original station files rather than ready-made national tables, so every "
        "aggregation step is ours and can be checked. A script downloads them through the "
        "data.gouv.fr API and records the address, date, size and SHA-256 hash of each file; "
        "processing refuses any file whose bytes differ."
    )
    rows = []
    for year in data.YEARS:
        manifest = json.loads(
            (data.PROJECT / "data/raw/official" / str(year) / "manifest.json").read_text()
        )
        files = manifest["files"]
        q = data.quality(year)
        rows.append(
            {
                "Election": year,
                "Files": len({f["sha256"] for f in files}),
                "Size (MB)": round(sum({f["sha256"]: f["bytes"] for f in files}.values()) / 1e6, 1),
                "Station-round records": q.get("polling_station_round_rows"),
                "Areas": len(data.election(year).areas),
                "Dataset": DATASETS[year],
            }
        )
    table = pd.DataFrame(rows)
    st.dataframe(
        table,
        hide_index=True,
        width="stretch",
        column_config={
            "Dataset": st.column_config.LinkColumn(display_text="data.gouv.fr"),
            "Election": st.column_config.NumberColumn(format="%d"),
            "Station-round records": st.column_config.NumberColumn(format="localized"),
        },
    )
    ui.caption(
        "Table 1",
        "The five elections. 2002–2012 publish both rounds in one file. The 2002 and 2007 "
        "files have no voters abroad and fewer overseas areas (100 and 101 areas against 107), "
        "so for those years every total means <i>covered areas</i>, not France.",
    )

    st.markdown(
        "**Source 2: candidate positions, collected by us.** Four of our assumptions need to "
        "know where each candidate stands on the left-right axis. No existing dataset covers "
        "all 61 candidacies (the Chapel Hill Expert Survey, for instance, rates parties and "
        "misses most minor candidates). Polling institutes, however, list candidates from "
        "left to right in every published poll. We collected **22 such orders** from 9 "
        "institutes, each with its source link, and turned them into a score from 0 (leftmost) "
        "to 1 (rightmost): candidates are evenly spaced within each poll, then averaged over "
        "institutes."
    )
    p = data.polls()
    counts = p.groupby("year").agg(
        polls=("institute", "size"), institutes=("institute", lambda s: ", ".join(s))
    )
    ui.html(
        '<table class="paper"><thead><tr><th>Election</th><th>Polls</th><th style="text-align:left">Institutes</th></tr></thead><tbody>'
        + "".join(
            f"<tr><td>{y}</td><td>{r.polls}</td><td style='text-align:left'>{r.institutes}</td></tr>"
            for y, r in counts.iterrows()
        )
        + "</tbody></table>"
    )
    ui.callout(
        "<b>Weak point: 2002 rests on a single poll</b> (Ipsos, the only original report we "
        "found). This matters, because 2002 is the election that decides the overall ranking "
        "(see Results). Treat every 2002 position as less certain than the others.",
        warn=True,
    )
    year = st.segmented_control("Election", data.YEARS, default=2022, key="data_year") or 2022
    st.altair_chart(ui.position_strip(year), width="stretch")
    ui.caption(
        f"Figure 2 ({year})",
        "Each circle is a candidate, sized by first-round share of registered voters. The "
        "shaded zones are at least one third of the scale from <i>both</i> finalists: this is "
        "where assumption H2 sends voters to a non-vote. The score is an order, not a "
        "measured ideological distance.",
    )

    st.markdown("## 2.2 Cleaning")
    st.markdown(
        "Official counts leave little to *repair* and much to *verify*. Our rule: **every "
        "check has a threshold of zero violations, and a violation stops the pipeline** "
        "instead of being fixed, because in an official file it can only mean that we parsed "
        "it wrongly. We removed, imputed or corrected no observation."
    )
    checks = pd.DataFrame(
        [
            ("Integrity", "File bytes equal the pinned SHA-256 hash", "Stop"),
            ("Schema", "Three file layouts over 20 years; unknown layout", "Stop"),
            ("Uniqueness", "Duplicate station or (station, candidate) keys", "Stop"),
            ("Bounds", "voters ≤ registered, valid ≤ voters, no negative count", "Stop"),
            ("Consistency", "Candidate votes add up to valid ballots in every station", "Stop"),
            ("Coverage", "Both rounds cover exactly the same areas", "Stop"),
            (
                "External",
                "2022 sums vs the Ministry's published national totals (26 fields)",
                "All match",
            ),
        ],
        columns=["Check", "What is tested", "If it fails"],
    )
    st.dataframe(checks, hide_index=True, width="stretch")
    ui.caption(
        "Table 2",
        "Quality checks, run on every build. The list of every raw line read, kept or skipped is in <code>docs/data_quality_and_cleaning.md</code>.",
    )
    st.markdown(
        "Three cleaning decisions shape the analysis:\n\n"
        "1. **Shares of registered voters, not of valid votes.** Abstention and blank ballots "
        "are outcomes we want to predict, so they must be in the denominator. This is why our "
        "percentages differ from the ones on TV.\n"
        "2. **Blank and invalid ballots are merged.** Before 2017 the Ministry publishes them "
        "together; we use the combined outcome every year so that it means the same thing. The "
        "separate counts of 2017 and 2022 are kept for a sensitivity check.\n"
        "3. **Unusual areas are flagged, not removed.** Overseas areas and voters abroad have "
        "very different turnout, but they are part of the electorate we study."
    )

    st.markdown("### Why one observation is one area, not one polling station")
    st.markdown(
        "We add the ~65,000–70,000 polling stations of each round into 100–107 areas "
        "(départements, overseas territories, voters abroad), giving **522 area-elections**. "
        "We chose this level for three reasons: it was the unit fixed in our approved "
        "acquisition note; areas are stable over the twenty years, while stations are "
        "renumbered and redrawn between elections, so station-level results cannot be "
        "compared across years without a boundary harmonisation we could not do; and a "
        "station has a few hundred voters, so its shares are noisy. **The cost:** "
        "aggregation hides variation inside an area, and coarser units make the "
        "ecological-inference problem worse, because more different individual behaviours "
        "fit the same totals. Testing the assumptions at station level, within each election, "
        "is the obvious next step."
    )

    st.markdown("## 2.3 Storage")
    st.markdown(
        "Raw files are kept unchanged. Cleaned data is stored as **Parquet files in a "
        "normalised layout**: per election, an `areas` table (registered voters, stations), an "
        "`outcomes` table (one count per area, round and option) and an `options` table "
        "(labels); and one long `predictions` table for every model, variant, election, area "
        "and outcome. Shares are never stored: they are computed when the data is read."
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
    comparison = pd.DataFrame(
        {
            "Need": [
                "Written once by one process",
                "Read whole columns",
                "Join models × elections",
                "Reproduced by a classmate",
                "Keys and constraints",
            ],
            "Parquet files (chosen)": [
                "Natural: one file per table",
                "Columnar: reads only what is asked",
                "In pandas after loading",
                "Byte-identical rebuild, hash per file, small enough for Git",
                "Enforced by our code on every write and load",
            ],
            "SQLite / PostgreSQL": [
                "Works, but transactions and a server solve a problem we do not have",
                "Row-oriented, no advantage at this size",
                "SQL joins and views: its strongest argument",
                "Binary file not byte-stable; PostgreSQL needs a server and an account",
                "Declarative: the engine refuses bad rows",
            ],
            "DuckDB over Parquet": [
                "Not a storage change",
                "Columnar",
                "SQL directly on our files",
                "One extra package",
                "None of its own",
            ],
        }
    )
    head = "".join(f"<th style='text-align:left'>{c}</th>" for c in comparison.columns)
    body = "".join(
        "<tr>"
        + "".join(f"<td style='text-align:left;vertical-align:top'>{v}</td>" for v in row)
        + "</tr>"
        for row in comparison.itertuples(index=False)
    )
    ui.html(f'<table class="paper"><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table>')
    ui.caption(
        "Table 3",
        "Storage options against what our data needs. We checked the relational option "
        "concretely: a test loads our 2022 tables into SQLite with primary keys, foreign keys "
        "and CHECK constraints, and gets the same shares. Full comparison in "
        "<code>docs/storage_comparison.md</code>.",
    )
    st.markdown(
        "**Decision.** Parquet, because our data is written once, read by column, small, and "
        "must be rebuilt *exactly* by a reader with no setup. **What we give up:** constraints "
        "are checked by our code, not declared in a schema, so a file written by other code "
        "is only caught when it is loaded; joins live in Python. DuckDB would add SQL without "
        "changing the files if the predictions grew by orders of magnitude, and a real "
        "database would be the right answer if several people wrote results at once. The "
        "small hand-made reference tables (poll orders, candidate scores) stay as CSV so they "
        "can be reviewed line by line in Git."
    )
