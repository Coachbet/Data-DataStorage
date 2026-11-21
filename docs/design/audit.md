# Design audit of the site before the redesign

> **Historical record.** This describes the site as it was on 15 November 2026. On
> 20 November 2026 the screenshots were removed from the repository and the
> "2027 scenarios" page was dropped; the site now has four pages (The answer,
> Evidence, Explore the data, Method & sources). `capture.py` can recapture screenshots.

Date: 15 November 2026. State audited: `master` after the analysis merge.
Screenshots of every page were taken at 1440 px and 390 px with
[`capture.py`](capture.py); the screenshots are no longer in the repository.

## Summary

The site is honest and complete, but it does not look or read like an analysis.
Three problems run through every page:

1. **The answer is missing from the first page.** The home page asks "What
   changes?" and never says what we found. The comparison of the eight
   assumptions, which is the project's result, sits on the fourth page as a
   plain grid of numbers.
2. **The visual language is borrowed.** Pill navigation, pill buttons, a centred
   giant headline with a blue-to-purple gradient, white cards on a grey page,
   hover-lift cards and entrance animations. These are the marks of a product
   landing page. They say nothing about this project.
3. **Charts are secondary and inconsistent.** Each chart defines its own fonts
   and colours. Colour means "observed versus model" on one page, "four
   outcomes" on another and "two finalists" (blue and purple) on a third.
   Titles name the chart instead of stating what it shows.

## Page by page

### Home (`1-home-*.png`)

- **Purpose.** Introduce the project. A classmate learns the topic in ten
  seconds, but not the question's answer, and not that eight assumptions were
  compared.
- **First thing seen.** "Two rounds. One electorate. What changes?" at 70 px
  with a gradient on the last two words. It is a slogan. The most important
  thing, the finding, is not on the page.
- **Hierarchy and layout.** Everything is centred, including body text. Three
  centred section headings follow each other with 80 px gaps, so the page has
  no reading line. The "snapshot" card has a 30 px shadow and 28 px radius.
- **Chart.** The stacked bars use blue and purple for the finalists, three greys
  for the rest, and pill-shaped segments with gaps that distort small values
  (blank/invalid in round 1 is a dot). The legend is a table below.
- **Copy.** "Two snapshots of an electorate. Same categories. Different
  results." and "Observe. Explain. Check." are rhythm without content. The
  three "step" cards (01 / OBSERVE …) are the classic three-card template.
- **Template patterns.** Centred hero, primary pill plus text link, three
  identical cards with hover lift, gradient text, entrance animation.

### Explore (`2-explore-*.png`)

- **Purpose.** Clear: one election, one round, by area. This is the best page.
- **First thing seen.** A centred 64 px headline "Start with what happened.",
  then a grey pill repeating the year and area already shown in the top bar.
- **Layout.** Three metric cards, then a segmented control, then the chart.
  The controls that change the chart (year, area) are in the top bar, far from
  the chart; the round control is on the page. Two places for one job.
- **Chart.** Horizontal bars, labelled with values: good. All bars are the same
  blue, so candidates, blank ballots and abstention look like one kind of
  thing, although the project's whole point is that they are four different
  outcomes. Rounded bar ends. Axis title repeats the heading.
- **Copy.** Mostly plain. "Start with what happened." is a slogan again.

### Understand the model (`3-understand-the-model-*.png`)

- **Purpose.** Explain H0. Since H0b, H1, H2 and H3 were added, the page
  explains one of eight models and calls it "the model".
- **First thing seen.** "One simple rule. A measurable gap." Then three more
  step cards (INPUT / ASSUMPTION / COMPARISON), 320 px tall, mostly empty.
- **Chart.** Observed versus H0 as paired bars with a legend on top. Blue and
  orange here mean "observed" and "model", while on the next page blue and
  orange mean "finalist A" and "finalist B".
- **Density.** Two metric cards, a paragraph that repeats the first metric, a
  caption that defines pp again, an expander, a warning, another expander, a
  button. The key number is said three times.

### Compare models (`4-compare-models-*.png`)

- **Purpose.** The result of the project. It is page four.
- **First thing seen.** "Eight assumptions. One score.", then two full-width
  coloured banners (yellow and blue) before any content.
- **Table.** A default data grid. No best value is marked, so the reader must
  scan 56 numbers to find who wins each election. The one sentence that
  explains the table sits in a card below it, in the same weight as a caption.
- **Chart.** Three rows of grouped bars at a fixed 620 px width: it leaves the
  right third of the page empty on desktop and is cut off on mobile. The y-axis
  title is repeated three times, the model name is rotated, there is no title
  and no annotation. The largest bar (2002) is not explained.
- **Missing.** The sensitivity results, the H2 threshold mechanism and the
  predicted-versus-observed view exist in the report but not on the site.

### 2027 scenarios (`5-2027-scenarios-*.png`)

- **Purpose.** Clear, and the warning is prominent.
- **Layout.** The "not a forecast" message is one yellow banner. Below it the
  result is a heading ("Emmanuel Macron – Marine Le Pen") and a table that
  looks exactly like an observed result. Nothing in the result itself says it
  is hypothetical.
- **Chart.** None. Four numbers in a grid; with "show all models", eight
  columns of numbers.
- **Copy.** With the default model the caption reads "H0b gives Emmanuel Macron
  55.2% and H0b gives 55.2%": the comparison sentence is not adapted when the
  chosen model is the baseline.

### Sources & limits (`6-sources-limits-*.png`)

- **Purpose.** Provenance and caveats. Content is right.
- **Layout.** Two pill buttons for the source links, a numbered list, then four
  stacked expander cards. Storage and cleaning are not described at all,
  although both are graded parts of the project.

### Navigation and global chrome

- Six pills in a frosted bar, plus two pill-shaped selectors for year and area
  that apply to only three of the six pages.
- At 390 px the navigation scrolls sideways with a hidden scrollbar: "Compare
  models", "2027 scenarios" and "Sources & limits" are off-screen with no hint
  that they exist. The bar takes 148 px of a phone screen.
- The coverage note for 2002 and 2007 appears on every page except Explore,
  including pages that show all five elections at once.

## What is worth keeping

- Every honesty statement, and their wording.
- Value labels on bars, tooltips, CSV downloads, the candidate reference table.
- The offline behaviour and the empty and error states.
- The switch between "share of registered voters" and "share of valid votes".
