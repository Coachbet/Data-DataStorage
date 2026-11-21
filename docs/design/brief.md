# Design brief for the site

> **Historical record.** This describes the site as it was on 15 November 2026. On
> 20 November 2026 the screenshots were removed from the repository and the
> "2027 scenarios" page was dropped; the site now has four pages (The answer,
> Evidence, Explore the data, Method & sources). `capture.py` can recapture screenshots.

Date: 15 November 2026. Follows [`audit.md`](audit.md). The research does not
change: no model, number, data file or generated result is touched. Every value
on the site is still computed from the bundled predictions and election tables.

## Direction

An editorial data page. The reader is a professor or a classmate who wants to
follow a methodological argument and check it. So the site answers first, puts
charts before prose, keeps every caveat next to the thing it qualifies, and
uses nothing decorative.

- **Answer first.** The first page states the question, the current answer and
  shows the one chart behind it.
- **Type carries the hierarchy.** Left-aligned everywhere. A serif for
  headlines, a sans for everything else, six sizes.
- **Colour means something or is absent.** Four fixed colours for the four
  second-round outcomes, one accent for interaction, greys for context.
- **Charts share one theme** and each has a title that states the takeaway, a
  subtitle that states the measure and unit, direct labels, and a source line.
- **Quiet components.** Text navigation with an underline, hairlines instead of
  cards, rectangular buttons for real actions only.

## Tokens

Defined once in `site/theme.py`; the CSS variables and the chart theme are both
generated from it.

### Colour

| Token | Value | Use | Contrast on paper |
|---|---|---|---:|
| `paper` | `#FBFAF7` | page background | — |
| `wash` | `#F1EFE9` | table header, code, quiet bands | — |
| `ink` | `#14171C` | text, axes labels that matter | 17.2 |
| `muted` | `#585E68` | secondary text, captions, axis labels | 6.3 |
| `rule` | `#D9D7D0` | hairlines | decorative |
| `accent` | `#0B5F66` | links, focus ring, active navigation, primary button | 7.1 |
| `accent-strong` | `#084A50` | hover | 9.6 |
| `note-ink` on `note-bg` | `#5C4300` on `#FBF1D5` | status and caveat notes | 8.3 |
| `context` | `#C9CCD1`, outline `#6B717B` | "other candidates", non-highlighted series | outline 4.7 |

Outcome palette, identical in every chart, table key and scenario. It is the
four-colour palette validated for the report figures.

| Outcome | Fill | Outline | Fill on paper | Outline on paper |
|---|---|---|---:|---:|
| Finalist A (first-round leader) | `#2A78D6` | `#1F5FAE` | 4.2 | 6.1 |
| Finalist B | `#EB6834` | `#B34A1C` | 3.1 | 5.1 |
| Blank or invalid | `#1BAF7A` | `#0F7A54` | 2.7 | 5.1 |
| Abstention | `#EDA100` | `#8F6100` | 2.1 | 5.2 |

Two fills are below the 3:1 that WCAG 1.4.11 asks of graphical objects. Each
mark therefore carries a 1 px outline in the darker tone of its hue (at least
5:1), and every mark has a text label or sits in a labelled row. Colour is never
the only carrier: outcomes are always named in text beside the mark.

Text contrast targets WCAG AA (4.5:1); all text tokens exceed it. White on the
accent (primary button) is 7.4:1.

### Type

- Headlines: **Source Serif 4** (variable, OFL), weight 600.
- Text, interface, charts: **Source Sans 3** (variable, OFL).
- Both are vendored in `site/assets/fonts/` with their licences and embedded in
  the page; no request leaves the machine. System fonts are the fallback.
- Scale (px): 13 · 15 · 17 · 21 · 28 · 38. Body 17/1.55. Measure 68 characters.
- Numbers: `font-variant-numeric: tabular-nums lining-nums` on tables, metrics
  and chart labels.

### Space and shape

- Spacing scale (px): 4 · 8 · 12 · 16 · 24 · 32 · 48 · 64. Nothing else.
- Content column 1040 px; text measure 680 px.
- Radius 3 px on controls and notes. No shadows. No gradients.
- Motion: none beyond the browser's own; `prefers-reduced-motion` still honoured.

### Number formats

One decimal everywhere, through shared helpers: `fmt_pp` (`4.3 pp`, signed
`+4.3 pp` for errors), `fmt_pct` (`38.5%`), `fmt_int` (`48,752,339`). The fitted
share `p` keeps two decimals because its grid step is 0.01.

## Information architecture

Six pages become five. Navigation is a row of text links, fixed at the top; the
active page is bold with an accent underline. At 390 px it wraps onto two lines,
so every page stays visible.

| New page | Contains | Was |
|---|---|---|
| **The answer** | question; answer in two sentences; the comparison chart; three findings, each naming its evidence; status note | Home (new content) |
| **Evidence** | the five assumptions with what each does to one real group; comparison table; signed errors; H2 threshold; predicted against observed; sensitivity; H3 folds; H0a in one election, with its formulas and example | Understand the model + Compare models |
| **Explore the data** | election, area and round pickers on the page; both rounds side by side; one round in detail; exact figures and download | Explore + the home "snapshot" |
| **Method & sources** | provenance, checks, storage, limits, reproduction, candidate reference, glossary, AI disclosure | Sources & limits |

The election and area pickers leave the global bar. They appear only where a
single election is shown: on Explore, in the "one election" section of Evidence
and in the source section of Method. The choice is remembered across pages.

### Removed, and why

- The hero slogan, its two buttons and the gradient: replaced by the answer.
- The two sets of three "step" cards: their content is now the one-line
  definition of each assumption (Evidence) and the method summary.
- The "Next: …" buttons at the bottom of pages: the navigation is always visible.
- The grey "2022 · All covered areas" pill: the pickers now sit beside the chart.
- The global coverage note on pages that show all elections at once: it now
  appears where a 2002 or 2007 figure is shown, and in the status note.
- The second definition of "pp" in a caption on the model page: defined once at
  first use and in the glossary.

New on the site, from results that already existed in `reports/`: the model
comparison chart, the H2 threshold view, predicted against observed by area,
the sensitivity table. Nothing else was added.

## Honesty elements and where they live

| Statement | Place |
|---|---|
| Aggregate patterns, not individual transfers | status note on The answer; banner on Evidence; note under the H0a comparison; scenario frame; footer on every page |
| Coverage of 2002 and 2007 | status note; Evidence note; warning on Explore when such a year is selected; Method limits |
| Draft coding, pending items | status note; Evidence banner; scenario banner; candidate reference |
| Hypothetical scenario on the 2022 electorate — not a forecast | scenario banner, frame label, result heading, chart subtitle, "how to read" |
| AI-assistance disclosure | Method & sources, unchanged sentence |

## Acceptance criteria

Every page: passes the checklist below; holds at 390 px without horizontal page
scroll; one `h1`; a one-line purpose statement under it.

- **The answer.** The answer sentences and the chart are visible without
  scrolling at 1440 × 900. The chart title is a true statement computed from the
  results. Each of the three findings names where its evidence is.
- **Evidence.** A reader can find which assumption is closest in each election
  without reading more than one row. The 2002 outlier and the H2 threshold are
  annotated. Every chart has takeaway title, measure subtitle, source line.
- **Explore the data.** The controls that change a chart sit directly above it.
  The four outcomes use the outcome colours; other candidates are grey.
- **Method & sources.** Provenance, cleaning, storage, limits and reproduction
  are each reachable in one click. The AI disclosure sentence is unchanged.

### Checklist (every page)

1. No centred hero with a giant headline and two pill buttons.
2. No grid of identical icon cards.
3. No gradients, glows, blobs, emoji or decorative icons.
4. One accent colour; colours carry meaning or nothing.
5. Every headline says something specific and true about this project.
6. Spacing on one scale.
7. No default Streamlit look beside custom styling.
8. Numbers formatted consistently.

Results of the verification are recorded in [`verification.md`](verification.md).
