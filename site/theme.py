"""Design tokens, defined once. The stylesheet variables and the chart theme both read them."""

import base64
from pathlib import Path

SITE_DIR = Path(__file__).resolve().parent
FONT_DIR = SITE_DIR / "assets" / "fonts"

SANS = '"Source Sans 3", -apple-system, "Segoe UI", "Helvetica Neue", Arial, sans-serif'
SERIF = '"Source Serif 4", Georgia, "Times New Roman", serif'
FONT_FILES = {
    "Source Sans 3": "source-sans-3-latin-wght-normal.woff2",
    "Source Serif 4": "source-serif-4-latin-wght-normal.woff2",
}

COLOUR = {
    "paper": "#FBFAF7",
    "wash": "#F1EFE9",
    "ink": "#14171C",
    "muted": "#585E68",
    "rule": "#D9D7D0",
    "accent": "#0B5F66",
    "accent-strong": "#084A50",
    "note-ink": "#5C4300",
    "note-bg": "#FBF1D5",
    "context": "#C9CCD1",
    "context-line": "#6B717B",
}
# The four second-round outcomes: one colour each, everywhere. Fill, then outline.
OUTCOME = {
    # Softened hues (validated: lightness band, chroma floor, colour-blind separation).
    "finalist_a": ("#4F86C6", "#2E63A3"),
    "finalist_b": ("#D9825B", "#A65530"),
    "blank_invalid": ("#4BA88A", "#2E7A62"),
    "abstention": ("#D8AA45", "#8A6A1E"),
    "other": (COLOUR["context"], COLOUR["context-line"]),
}
OUTCOME_NAMES = {
    "finalist_a": "Finalist A",
    "finalist_b": "Finalist B",
    "blank_invalid": "Blank or invalid",
    "abstention": "Abstention",
    "other": "Other candidates",
}
SPACE = (4, 8, 12, 16, 24, 32, 48, 64)
TYPE_SCALE = (13, 15, 17, 21, 28, 38)


def css_variables() -> str:
    """The ``:root`` block and font faces placed before ``styles.css``."""
    faces = ""
    for family, name in FONT_FILES.items():
        encoded = base64.b64encode((FONT_DIR / name).read_bytes()).decode("ascii")
        faces += (
            f"@font-face{{font-family:'{family}';font-style:normal;font-weight:200 900;"
            f"font-display:swap;src:url(data:font/woff2;base64,{encoded}) format('woff2');}}"
        )
    variables = [f"--{name}:{value}" for name, value in COLOUR.items()]
    variables += [f"--{role.replace('_', '-')}:{fill}" for role, (fill, _) in OUTCOME.items()]
    variables += [f"--{role.replace('_', '-')}-line:{line}" for role, (_, line) in OUTCOME.items()]
    variables += [f"--s{i}:{value}px" for i, value in enumerate(SPACE, 1)]
    variables += [f"--t{i}:{value / 16:.4f}rem" for i, value in enumerate(TYPE_SCALE, 1)]
    variables += [f"--sans:{SANS}", f"--serif:{SERIF}"]
    return faces + ":root{" + ";".join(variables) + "}"


def vega_config() -> dict:
    """One Vega-Lite theme for every chart: type, grid, axes."""
    font = SANS.replace('"', "'")  # a family name with a digit must stay quoted
    return {
        "background": "transparent",
        "font": font,
        "padding": {"left": 0, "right": 8, "top": 4, "bottom": 0},
        "view": {"stroke": None},
        "axis": {
            "labelFont": font,
            "titleFont": font,
            "labelFontSize": 13,
            "titleFontSize": 13,
            "labelColor": COLOUR["muted"],
            "titleColor": COLOUR["muted"],
            "titleFontWeight": 400,
            "titlePadding": 12,
            "gridColor": COLOUR["rule"],
            "gridOpacity": 0.6,
            "domainColor": COLOUR["context-line"],
            "tickColor": COLOUR["context-line"],
            "tickSize": 4,
            "labelPadding": 6,
        },
        "axisY": {"domain": False, "ticks": False},
        "text": {"font": font, "fontSize": 13, "color": COLOUR["ink"]},
        "bar": {"strokeWidth": 1},
    }
