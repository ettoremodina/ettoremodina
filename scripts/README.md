# Scripts

The profile's pictures are generated; nothing here is drawn by hand.

| Script | What it makes | When to run it |
|---|---|---|
| `make_banner.py` | `assets/banner-dark.jpg` and `assets/banner-light.jpg`: the portfolio's Home with its Physarum field grown around the name. | When the name, the line under it or the portfolio's palette changes. Needs the portfolio running locally (`vite preview`) and Playwright. |
| `make_thumbnails.py` | `assets/projects/<id>.jpg`: the portfolio's project covers cut to one shape. | When a project is added to the README or its cover changes. Add its id to `PROJECTS`. |
| `contributions.py` | `contributions-dark.svg` and `contributions-light.svg`: the contribution calendar. | Never by hand: `.github/workflows/contributions.yml` runs it every day and publishes the two files on the `output` branch. |

The projects, their one-line descriptions and their order follow the portfolio
(<https://ettoremodina-webportfolio.netlify.app>): when a project changes there, change its card
in `README.md` here. A "Code" link is only given for a public repository.
