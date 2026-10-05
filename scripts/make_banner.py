"""Render the profile banner from the portfolio's live Physarum field.

The banner is not drawn: it is the Home page of the portfolio, with its own content hidden and
one plate — name and role — put in its place. The Physarum solver treats that plate like any
other block of text on the site: it walls the interior off and grows its network around it.
After the culture has formed, the window is photographed once per theme.

Needs the portfolio running locally (production build, `vite preview`) and Playwright:

    python scripts/make_banner.py                      # http://localhost:4173
    BASE_URL=http://localhost:5173 python scripts/make_banner.py
"""

import os
from pathlib import Path

from PIL import Image
from playwright.sync_api import sync_playwright

BASE_URL = os.environ.get("BASE_URL", "http://localhost:4173")
ASSETS = Path(__file__).resolve().parent.parent / "assets"

# The banner's size in CSS pixels; it is captured at twice that for sharp text.
WIDTH, HEIGHT, SCALE = 1280, 380, 2
# How long the culture is left to grow before the photograph, in milliseconds.
SETTLE_MS = int(os.environ.get("SETTLE_MS", "45000"))
# How strongly the field is shown per theme, 0 to 1. The site keeps it quieter, behind a page
# of text; on the light ground the same strength reads as mud, so it is held lower there.
FIELD_OPACITY = {"dark": 0.8, "light": 0.5}

KICKER = "Mathematical engineer · Milan"
NAME = "Ettore Modina"
LINE = "Machine learning, mathematical modelling and the automation of everyday work."

# Replaces the Home's content with the banner's plate. Runs inside the portfolio page, so the
# fonts and the palette tokens (`--text-strong`, `--signal`, …) are the site's own.
INJECT = """
([kicker, name, line, opacity]) => {
  document.querySelectorAll('[data-field-plate]').forEach((el) => el.removeAttribute('data-field-plate'))
  document.querySelectorAll('[data-field-origin]').forEach((el) => el.removeAttribute('data-field-origin'))

  const style = document.createElement('style')
  style.textContent = `
    .site-content { visibility: hidden; }
    html, body { overflow: hidden; }
    .home-field { visibility: visible; opacity: ${opacity} !important; }
    .banner { position: fixed; inset: 0; display: grid; place-items: center start; padding-left: 84px; }
    .banner__plate { padding: 30px 40px 34px; max-width: 640px; }
    .banner__kicker { margin: 0; color: var(--signal-narrative, var(--signal)); font: 600 15px/1 var(--font-body);
      letter-spacing: 0.16em; text-transform: uppercase; }
    .banner__name { margin: 16px 0 0; color: var(--text-strong); font: 500 84px/0.95 var(--font-display);
      letter-spacing: -0.025em; }
    .banner__line { margin: 18px 0 0; color: var(--text-subtle); font: 400 21px/1.4 var(--font-body); }
  `
  document.head.append(style)

  const banner = document.createElement('div')
  banner.className = 'banner'
  banner.innerHTML = `
    <div class="banner__plate" data-field-plate>
      <p class="banner__kicker"></p>
      <h1 class="banner__name" data-field-origin></h1>
      <p class="banner__line"></p>
    </div>`
  banner.querySelector('.banner__kicker').textContent = kicker
  banner.querySelector('.banner__name').textContent = name
  banner.querySelector('.banner__line').textContent = line
  document.body.append(banner)
  // The field re-reads its plates when the window changes.
  window.dispatchEvent(new Event('resize'))
}
"""


def capture(playwright, theme: str) -> Path:
    """Grow the field around the banner's plate in one theme and save the photograph."""
    browser = playwright.chromium.launch()
    context = browser.new_context(viewport={"width": WIDTH, "height": HEIGHT}, device_scale_factor=SCALE)
    context.add_init_script(
        f"localStorage.setItem('portfolio-theme', '{theme}');"
        "localStorage.setItem('portfolio-simple', 'off');"
    )
    page = context.new_page()
    page.goto(BASE_URL, wait_until="domcontentloaded")
    page.wait_for_selector("canvas.home-field", state="attached")
    page.evaluate(INJECT, [KICKER, NAME, LINE, FIELD_OPACITY[theme]])
    page.wait_for_timeout(SETTLE_MS)

    png = ASSETS / f"banner-{theme}.png"
    page.screenshot(path=png)
    browser.close()

    # A photograph of a glowing field is far smaller as a JPEG, and loses nothing visible.
    jpg = png.with_suffix(".jpg")
    Image.open(png).convert("RGB").save(jpg, quality=88, optimize=True)
    png.unlink()
    return jpg


def main() -> None:
    ASSETS.mkdir(exist_ok=True)
    with sync_playwright() as playwright:
        for theme in ("dark", "light"):
            path = capture(playwright, theme)
            print(f"{path.name}: {path.stat().st_size // 1024} kB")


if __name__ == "__main__":
    main()
