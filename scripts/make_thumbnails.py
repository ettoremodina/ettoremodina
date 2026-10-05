"""Cut the project thumbnails of the profile from the portfolio's own cover images.

Each project shown in the README has a `cover.webp` in the portfolio repository
(`src/assets/projects/<id>/`). This crops every one to the same shape and saves it under
`assets/projects/<id>.jpg`, so the cards line up and the profile never depends on the hashed
file names of the deployed site.

    python scripts/make_thumbnails.py                       # portfolio next to this repo
    PORTFOLIO=/path/to/portfolio-website python scripts/make_thumbnails.py

Add an id to `PROJECTS` when a project is added to the README.
"""

import os
from pathlib import Path

from PIL import Image, ImageOps

ROOT = Path(__file__).resolve().parent.parent
PORTFOLIO = Path(os.environ.get("PORTFOLIO", ROOT.parent / "portfolio-website"))
COVERS = PORTFOLIO / "src" / "assets" / "projects"
OUTPUT = ROOT / "assets" / "projects"

# Portfolio project ids, the same that end the write-up links (`/projects/<id>`).
PROJECTS = (
    "agent-workflow",
    "jobhunter",
    "knowledge",
    "voice-expense-tracker",
    "digital-twin-satellite",
    "physics-informed-ml",
    "regicide-ai",
    "rl-scotland-yard",
    "bomb-buster",
    "neural-organic-growth",
)

# Every thumbnail is cut to this shape; the README scales it down to the column.
SIZE = (800, 500)


def main() -> None:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    for project in PROJECTS:
        cover = Image.open(COVERS / project / "cover.webp").convert("RGB")
        # Centre crop to the common shape; a cover narrower than the target is scaled up.
        thumbnail = ImageOps.fit(cover, SIZE, Image.LANCZOS, centering=(0.5, 0.5))
        path = OUTPUT / f"{project}.jpg"
        thumbnail.save(path, quality=84, optimize=True)
        print(f"{path.name}: {cover.size} -> {SIZE}, {path.stat().st_size // 1024} kB")


if __name__ == "__main__":
    main()
