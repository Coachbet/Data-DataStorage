"""The table of contents: one place that defines every page, section number and anchor.

The sidebar, the page headings and the cross-references all read it, so a section
can be renamed or moved without breaking a link.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Page:
    key: str  # module name in views/
    url: str  # url path ("" for the home page)
    number: int
    title: str
    icon: str
    sections: tuple[tuple[str, str], ...]  # (anchor, title)


PAGES: tuple[Page, ...] = (
    Page(
        "intro",
        "",
        1,
        "Introduction",
        ":material/home:",
        (
            ("s1-1", "The problem"),
            ("s1-2", "Why it is hard"),
            ("s1-3", "Our approach"),
            ("s1-4", "The answer in one figure"),
            ("s1-5", "Contributions"),
        ),
    ),
    Page(
        "data_page",
        "data",
        2,
        "Data",
        ":material/database:",
        (
            ("s2-1", "Sources"),
            ("s2-2", "Acquisition and provenance"),
            ("s2-3", "Quality assessment"),
            ("s2-4", "Cleaning decisions"),
            ("s2-5", "Candidate positions"),
            ("s2-6", "Storage"),
        ),
    ),
    Page(
        "hypotheses",
        "hypotheses",
        3,
        "Hypotheses",
        ":material/science:",
        (
            ("s3-1", "An assumption is a transfer table"),
            ("s3-2", "Baselines: H0a and H0b"),
            ("s3-3", "Proximity: H1, H1-soft, H2"),
            ("s3-4", "Mixture: H3"),
            ("s3-5", "Watch a rule move the voters"),
            ("s3-6", "Playground: the parameter p"),
            ("s3-7", "Playground: your own rule"),
        ),
    ),
    Page(
        "results",
        "results",
        4,
        "Results",
        ":material/insights:",
        (
            ("s4-1", "How close is each assumption?"),
            ("s4-2", "Key observations"),
            ("s4-3", "Where each assumption misses"),
            ("s4-4", "The distance threshold"),
            ("s4-5", "Robustness to candidate positions"),
            ("s4-6", "Blank ballots alone"),
            ("s4-7", "Metropolitan France and overseas"),
            ("s4-8", "Interpretation"),
        ),
    ),
    Page(
        "explore",
        "explore",
        5,
        "Explore the data",
        ":material/travel_explore:",
        (
            ("s5-1", "Round 1, candidate by candidate"),
            ("s5-2", "Both rounds side by side"),
            ("s5-3", "Predicted against observed"),
        ),
    ),
    Page(
        "decisions",
        "decisions",
        6,
        "Decisions & feedback",
        ":material/fact_check:",
        (
            ("s6-1", "Decision log"),
            ("s6-2", "How the project evolved"),
            ("s6-3", "Response to peer reviews"),
        ),
    ),
    Page(
        "method",
        "method",
        7,
        "Method & limits",
        ":material/functions:",
        (
            ("s7-1", "Notation"),
            ("s7-2", "The error score"),
            ("s7-3", "Fitting and validating H3"),
            ("s7-4", "Limits"),
            ("s7-5", "Reproduce every number"),
        ),
    ),
    Page(
        "report", "report", 8, "Report", ":material/description:", (("s8-1", "The written report"),)
    ),
)

BY_KEY = {p.key: p for p in PAGES}


def section_title(key: str, anchor: str) -> str:
    page = BY_KEY[key]
    for i, (a, title) in enumerate(page.sections, 1):
        if a == anchor:
            return f"{page.number}.{i} {title}"
    raise KeyError(anchor)


def link(key: str, anchor: str | None = None) -> str:
    """A relative link to a page, optionally to one of its sections."""
    page = BY_KEY[key]
    href = f"/{page.url}" if page.url else "/"
    return href + (f"#{anchor}" if anchor else "")
