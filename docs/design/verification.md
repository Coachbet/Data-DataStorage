# Verification of the redesign

Checked against the screenshots in [`after/`](after/) (1440 px and 390 px, taken
with `capture.py` on the bundled data) and against the test suite. The criteria
are those of [`brief.md`](brief.md). "Pass" with a note means the criterion
holds and the note records its limit.

## Checklist, every page

| # | Item | Result | Why |
|---|---|---|---|
| 1 | No centred hero with a giant headline and two pill buttons | Pass | Every page starts with a left-aligned headline and a purpose line; there is no call-to-action row. |
| 2 | No grid of identical icon cards | Pass | No cards. Findings are a numbered list; assumptions are a definition list. |
| 3 | No gradients, glows, blobs, emoji or decorative icons | Pass | Flat fills only. The old logo (gradient) was replaced by a flat mark. The remaining icons are functional: expander chevrons and the help marks beside metric labels. |
| 4 | One accent colour; colours carry meaning or nothing | Pass | Teal marks links, the active page and selected controls. Blue, orange, green and amber mean the four outcomes and nothing else. Amber notes mark status and caveats. |
| 5 | Every headline says something specific and true | Pass | Chart titles and the home headline are computed from the results and tested against `numbers.json`. Section labels on Method & sources ("Sources", "Limits") are plain labels by design. |
| 6 | Spacing on one scale | Pass | The stylesheet uses the `--s1`…`--s8` tokens for margins and padding; other pixel values are sizes (hairlines, nav height, minimum button height). |
| 7 | No default Streamlit look beside custom styling | Pass, with one exception | Navigation, buttons, alerts, expanders, metrics and tables are restyled. The interactive grids inside expanders (`st.dataframe`) keep Streamlit's own look: they are drawn on a canvas and cannot be styled from CSS. They only appear on demand. |
| 8 | Numbers formatted consistently | Pass | Shares are `12.3%`, differences `4.3 pp` or `+4.3 pp` with a true minus, counts use thousands separators; all through `fmt_pct`, `fmt_pp`, `fmt_int`. Table cells show the bare number with the unit in the column header. The fitted share p keeps two decimals because it is a proportion, not a percentage. |

## Acceptance criteria, per page

| Page | Criterion | Result | Why |
|---|---|---|---|
| All | Holds at 390 px without horizontal page scroll | Pass | Checked on the five mobile captures. Wide tables scroll inside their own box. |
| All | One `h1` and a purpose line | Pass | `components.page_header` is called once per page. |
| All | States that results are aggregate patterns, not individual transfers | Pass | Tested for every page (`test_every_page_says_results_are_aggregate_not_individual`). |
| The answer | Answer sentences and chart visible without scrolling at 1440 × 900 | Pass | The chart's axis title ends at about 880 px in the desktop capture. On a shorter window the bottom rows of the chart need a scroll. |
| The answer | Chart title is a true statement computed from the results | Pass | `presentation.answer` builds it from the comparison table; tested. |
| The answer | Each finding names where its evidence is | Pass | Each of the three ends with a link to a numbered Evidence section. |
| Evidence | The closest assumption per election is readable in one row | Pass | Comparison table: one row per election, lowest value bold, underlined and shaded (not colour alone). |
| Evidence | The 2002 outlier and the H2 threshold are annotated | Pass | 2002 is annotated on the home chart and outlined and named in the signed-error panels; the threshold section has its own chart and a "Why this happens" note. |
| Evidence | Takeaway title, measure subtitle and source line on every chart | Pass | All seven charts; see the desktop capture. |
| Explore the data | Controls sit directly above what they change | Pass | Election and area above both sections; round and basis above the detail chart. |
| Explore the data | Outcome colours for the four outcomes, grey for other candidates | Pass | Same `role_colour` scale as every other chart. |
| 2027 scenarios | No result on screen without "hypothetical" and "not a forecast" | Pass | The banner, the frame label, the chart subtitle, the table caption and the reading note each carry the words; the banner is tested in every state, including the error state. |
| 2027 scenarios | H0b is the default; an all-models view exists | Pass | Tested. |
| Method & sources | Provenance, cleaning, storage, limits and reproduction reachable in one click | Pass | Five anchored sections listed at the top of the page. |
| Method & sources | AI disclosure sentence unchanged | Pass | Compared word for word in a test. |

## Accessibility

- Text colours against the page and wash backgrounds are at least 4.5:1, and
  mark outlines at least 3:1; the ratios are in `brief.md` and asserted in
  `tests/test_site.py`. Streamlit fades captions to 60% opacity by default; the
  stylesheet resets that, since the faded text fell below AA.
- Value labels of stacked bars are placed under the bars, in ink on the page
  colour, because neither white nor ink reaches 4.5:1 on all four fills.
  Segments too narrow for a label have their value in the table or tooltip.
- Outcomes are named in text beside every chart; observed and predicted bars
  differ by fill (solid against outlined), area types by shape.
- Navigation is a native radio group: arrow keys move, focus is visible.
- Motion: the stylesheet adds none and removes transitions under
  `prefers-reduced-motion`.

## Not verified

- No screen reader was run. Vega-Lite charts are drawn on a canvas, so their
  content is not exposed to assistive technology; titles, subtitles, reading
  notes and the tables under "Exact figures" carry the same facts in text.
- Only Chrome was used for the captures.
