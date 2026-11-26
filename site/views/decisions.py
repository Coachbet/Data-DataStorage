"""6. Decisions & feedback: what we chose at each stage, how the project evolved, what reviewers changed."""

import pandas as pd
import streamlit as st

import ui

PAGE = "decisions"

STAGES = [
    (
        "Collection",
        "Original Ministry polling-station files for 2002–2022, downloaded by script and pinned "
        "by SHA-256; 22 left-to-right poll orders collected by hand.",
        "Consolidated, already harmonised results (kept only as a check); the Chapel Hill Expert "
        "Survey for positions (rates parties, misses minor candidates); six extra datasets "
        "(socioeconomic, media, surveys) dropped as unnecessary.",
        "2002 and 2007 miss voters abroad and some overseas areas; 2002 positions rest on one poll.",
        "Data 2.1–2.2, 2.5 · <code>data/raw/official/*/manifest.json</code> · <code>polling_axes.csv</code>",
    ),
    (
        "Cleaning",
        "Zero-tolerance checks that stop the pipeline; no observation removed, imputed or "
        "corrected. Shares of registered voters; blank and invalid ballots merged every year.",
        "Repairing or dropping suspicious stations and areas (they are real); shares of valid "
        "votes (would hide abstention and blank ballots, which we must predict).",
        "About a quarter of the blank/invalid outcome is invalid ballots, which no rule can "
        "explain; checked with a 5-outcome sensitivity analysis.",
        "Data 2.3–2.4 · Results 4.6 · <code>docs/data_quality_and_cleaning.md</code>",
    ),
    (
        "Storage",
        "Normalised Parquet tables (areas, outcomes, options) and one long predictions table; "
        "shares computed on read; reference tables as CSV.",
        "SQLite/PostgreSQL (declarative constraints, SQL joins, but not byte-stable and a server "
        "to install); DuckDB (a query engine over the same files, not needed at 92k rows).",
        "Constraints enforced by code, not by the engine; joins in Python; two copies of the "
        "snapshots that a check keeps aligned.",
        "Data 2.6 · <code>docs/storage_comparison.md</code> · <code>tests/test_storage.py</code>",
    ),
    (
        "Analysis",
        "Nine assumptions written as transfer matrices and scored by one rule (weighted mean "
        "absolute error per area). Parameter-free rules fixed before results; H3's single "
        "parameter validated leave-one-election-out.",
        "Learning transfers from a preference survey (H4, H5: one 2017 volunteer source for five "
        "elections) and two-dimensional distances (no 2D position exists for all 61 candidacies).",
        "Nine rules on five elections: the winner is partly a selection effect; 2002 drives "
        "the five-election ranking.",
        "Hypotheses 3.1–3.4 · Results 4.1–4.5 · <code>docs/methodology.md</code>",
    ),
    (
        "Communication",
        "One figure for the main message: each rule's error with and without 2002 (Figure 1.1), "
        "plus this site with every number recomputed live.",
        "One election at a time, as in our first app: the second peer review showed it hid the "
        "two main patterns (2002 as an outlier, abstention as the baseline's main error).",
        "A web page is less familiar than slides for some readers; the report and slides use "
        "the same generated numbers.",
        "Introduction 1.4 · <code>reports/results/numbers.json</code>",
    ),
]

TIMELINE = [
    (
        "16 Sep 2026",
        "Project proposal",
        "Vote transfers 2002–2022 plus a 2027 simulator, socioeconomic data and press mentions.",
    ),
    (
        "Sep 2026",
        "Professor's feedback",
        "Determine the data from the question; narrow to one investigation; operationalise precisely.",
    ),
    (
        "2 Oct 2026",
        "Data acquisition note",
        "Question reframed as a comparison of assumptions H0–H5; transfer matrix defined; six sources listed.",
    ),
    (
        "6 Oct 2026",
        "Peer review 1",
        "Prune H4/H5 and the survey data; scope creep warning; praise for the baseline and held-out testing.",
    ),
    (
        "31 Oct 2026",
        "Choices fixed",
        "Hand-coded 1–7 scale; H0 confirmed to send part of eliminated voters to abstention; weighted area error agreed.",
    ),
    (
        "3 Nov 2026",
        "Quality and cleaning deliverable",
        "Zero-tolerance checks, line ledger, 26/26 national totals matched for 2022.",
    ),
    (
        "10 Nov 2026",
        "Peer review 2",
        "Candidate table unreviewed; blank vs invalid; denormalised storage; is H0 a fair baseline?",
    ),
    (
        "15 Nov 2026",
        "Response",
        "H0 renamed H0a and H0b added; H1/H2 tie and threshold rules fixed; storage normalised; one predictions table.",
    ),
    (
        "20 Nov 2026",
        "Poll-based positions",
        "Our 1–7 coding replaced by 22 institute orders; the 2027 scenario dropped.",
    ),
    ("21 Nov 2026", "H1-soft", "A distance-weighted split added in response to a review."),
    ("27 Nov 2026", "Final deliverables", "Report, decision record, code and this site."),
]

ROUND1 = [
    (
        "H4 and H5 rely on one 2017 volunteer survey: temporal and selection bias.",
        "Accepted",
        "H4 and H5 dropped.",
    ),
    (
        "Scope creep across six external datasets.",
        "Accepted",
        "Only two inputs remain: official results and candidate positions.",
    ),
    (
        "Scraping 2027 polls adds late manual work.",
        "Accepted",
        "No 2027 poll collected; the 2027 scenario was later dropped.",
    ),
    (
        "CHES is appropriate for positions.",
        "Not followed",
        "CHES rates parties, not candidacies; replaced first by our scale, then by poll orders.",
    ),
    (
        "Calibrate on 2017 and 2022 first.",
        "Partly",
        "All five elections were feasible, so H3 uses leave-one-election-out over five.",
    ),
    (
        "No raw data or running code yet.",
        "Done",
        "Tested package covering acquisition to app; hashes pinned per file.",
    ),
]

ROUND2 = [
    (
        "The hand-coded candidate table is unreviewed but drives H1 and H2.",
        "Accepted, further",
        "Replaced by 22 published poll orders; our table kept as a robustness check.",
    ),
    (
        "Two coders and a weighted kappa on the 61 rows.",
        "Not followed",
        "Agreement between us measures consistency, not correctness; institutes' disagreement is measured instead.",
    ),
    (
        "No tie rule; Cheminade has no score.",
        "Accepted",
        "Ties split 50/50 (abstention as a variant); unplaced candidates follow H0b. Fixed before results.",
    ),
    (
        "Merging blank and invalid fits H2 badly.",
        "Accepted",
        "Combined outcome kept as primary; 5-outcome sensitivity for 2017 and 2022.",
    ),
    (
        "Separate blank/invalid counts only in interim tables.",
        "Accepted",
        "Now stored in the processed and bundled areas table.",
    ),
    (
        "Does H0 include first-round abstainers? Is it deliberately weak?",
        "Accepted",
        "Kept unchanged as H0a; H0b added. The change mattered more than any other.",
    ),
    (
        "One evaluation file per election will multiply.",
        "Accepted",
        "One long predictions table with model, variant and training elections.",
    ),
    (
        "Repeated registered column; stored shares (denormalised).",
        "Accepted",
        "Split into areas and outcomes tables; shares computed on read.",
    ),
    (
        "Possible drift between processed and bundled copies.",
        "Accepted",
        "A check in make check and at app start-up.",
    ),
    (
        "Candidate CSV contradicts the argument against CSV.",
        "Accepted",
        "One paragraph explains the exception for small reference tables.",
    ),
    (
        "No chart; every view covers one election.",
        "Accepted",
        "Cross-election figures: model comparison, signed error by outcome, scatter by area.",
    ),
    (
        "Reproduction details (Makefile, bundle step, broken link, stale counts).",
        "Accepted",
        "All fixed; make archive builds a clean zip.",
    ),
]

TAG = {
    "Accepted": "fixed",
    "Accepted, further": "fixed",
    "Done": "fixed",
    "Partly": "added",
    "Not followed": "baseline",
}


def render() -> None:
    ui.header(
        "Section 6 · Decisions & feedback",
        "What we chose, what we rejected, and why",
        "The project is graded on the justification of its choices. This page lists them stage "
        "by stage, shows how the project changed, and what each round of feedback changed.",
    )

    ui.section(PAGE, "s6-1")
    st.markdown(
        "For each stage of the workflow: our main choice, the alternative we rejected, the cost of our choice, and where to check it."
    )
    overview = pd.DataFrame([(s, c) for s, c, *_ in STAGES], columns=["Stage", "Main choice"])
    ui.text_table(overview.assign(Stage=lambda d: "<b>" + d.Stage + "</b>"))
    for stage, choice, alternative, limit, evidence in STAGES:
        with st.expander(f"{stage} · details"):
            ui.box("decision", f"<p>{choice}</p>", label="Choice")
            ui.box("note", f"<p>{alternative}</p>", label="Alternative considered and rejected")
            ui.box("limit", f"<p>{limit}</p>", label="Consequence or limitation")
            ui.html(f"<p class='caption'><b>Evidence.</b> {evidence}</p>")

    ui.section(PAGE, "s6-2")
    st.markdown(
        "The question stayed the same from the acquisition note onwards. The scope narrowed and the methods became stricter."
    )
    ui.html(
        '<div class="timeline">'
        + "".join(
            f'<div class="ev"><div class="date">{d}</div><div class="what">{w}</div><p>{t}</p></div>'
            for d, w, t in TIMELINE
        )
        + "</div>"
    )
    c1, c2 = st.columns(2)
    with c1:
        ui.box(
            "note",
            "<ul><li>2027 simulator</li><li>Socioeconomic indicators</li><li>Press mentions (GDELT)</li>"
            "<li>H4, H5 and the 2017 survey</li><li>2D positions</li><li>Shrinkage for small départements</li></ul>",
            label="Dropped along the way",
        )
    with c2:
        ui.box(
            "decision",
            "<ul><li>A second baseline (H0b)</li><li>Poll-based candidate positions</li>"
            "<li>Fixed tie and threshold rules</li><li>Held-out validation for H3</li>"
            "<li>Normalised storage</li><li>Sensitivity analyses</li></ul>",
            label="Added along the way",
        )

    ui.section(PAGE, "s6-3")
    st.markdown(
        "Every comment, what we did, and the status. Full list in `docs/response_to_reviews.md`."
    )
    for title, rows in (
        ("Peer review 1 · acquisition (6 October)", ROUND1),
        ("Peer review 2 · quality, cleaning, storage (10 November)", ROUND2),
    ):
        with st.expander(title):
            body = "".join(
                f"<tr><td>{c}</td><td><span class='tag {TAG[s]}'>{s}</span></td><td>{a}</td></tr>"
                for c, s, a in rows
            )
            ui.html(
                '<table class="paper text"><thead><tr><th>Comment</th><th>Status</th><th>What we did</th></tr></thead>'
                f"<tbody>{body}</tbody></table>"
            )
    with st.expander("Professor's feedback on the proposals"):
        st.markdown(
            "- **Determine the data from the question.** Two inputs remain; removing either makes the question unanswerable.\n"
            "- **Narrow to one investigation.** One question; every rule is a transfer matrix scored the same way.\n"
            "- **Operationalise precisely.** Shares, outcomes, the score and every rule are formulas (Section 7); the one "
            "variable two members could have coded differently, candidate position, is computed from published polls.\n"
            "- **More data is not better.** Six planned sources dropped.\n"
            "- **No sophisticated analysis before understanding the data.** Eight of nine rules have no parameter; the "
            "ninth has one, validated on elections it was not fitted on."
        )
    ui.box(
        "result",
        "<p>The single most important change came from a reviewer's question: <i>does the "
        "baseline send eliminated voters to abstention?</i> Answering it (H0b) removed more "
        "error than any political rule added.</p>",
        label="Lesson learned",
    )
