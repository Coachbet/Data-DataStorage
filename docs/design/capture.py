"""Capture full-page screenshots of every page of the running app.

Development aid only: Playwright is not a project dependency. Start the app
(`make app`), then run, for example:

    uv run --with playwright python docs/design/capture.py docs/design/after

It drives the locally installed Chrome, clicks each item of the main navigation
and saves one PNG per page at desktop (1440 px) and mobile (390 px) widths.
"""

import re
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

URL = "http://localhost:8501"
WIDTHS = {"desktop": 1440, "mobile": 390}
NAVIGATION = '.st-key-page [data-testid="stRadioOption"]'
CONTENT_HEIGHT = """() => {
  const main = document.querySelector('[data-testid="stMain"]');
  return Math.max(main ? main.scrollHeight : 0, document.documentElement.scrollHeight);
}"""


def settle(page):
    page.wait_for_function(
        "() => !document.querySelector('[data-testid=\"stStatusWidget\"]')", timeout=30_000
    )
    page.wait_for_timeout(1200)  # Vega charts draw after the script finishes


def capture(target: Path) -> None:
    target.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(channel="chrome")
        for name, width in WIDTHS.items():
            page = browser.new_page(viewport={"width": width, "height": 900})
            page.goto(URL, wait_until="networkidle")
            settle(page)
            labels = [
                text.strip()
                for text in page.locator(NAVIGATION).all_inner_texts()
                if text.strip()
            ]
            labels = list(dict.fromkeys(labels))
            for index, label in enumerate(labels, 1):
                # A scripted click also reaches items scrolled out of a narrow navigation.
                page.locator(NAVIGATION).filter(has_text=label).first.evaluate(
                    "item => (item.querySelector('input') || item).click()"
                )
                settle(page)
                page.set_viewport_size({"width": width, "height": 900})
                height = min(int(page.evaluate(CONTENT_HEIGHT)) + 40, 12_000)
                page.set_viewport_size({"width": width, "height": height})
                page.wait_for_timeout(600)
                slug = re.sub(r"[^a-z0-9]+", "-", label.lower()).strip("-")
                page.screenshot(path=str(target / f"{index}-{slug}-{name}.png"))
                print(f"{name}: {label}")
            page.close()
        browser.close()


if __name__ == "__main__":
    capture(Path(sys.argv[1] if len(sys.argv) > 1 else "docs/design/after"))
