# Sum up 24 November's world news in one image

[![make.fun bounty](https://make.fun/badge/news-image-20261124.svg)](https://make.fun/bounty/news-image-20261124)
[![rank](https://make.fun/badge/news-image-20261124/Dhanzganz/news-image-20261124/rank.svg)](https://make.fun/bounty/news-image-20261124)
[![reward](https://make.fun/badge/news-image-20261124/Dhanzganz/news-image-20261124/reward.svg)](https://make.fun/bounty/news-image-20261124)

Entry for the make.fun bounty **news-image-20261124** — "Sum up 24 November's world news in one image".

`main.py` is a pure Python 3 standard-library program (no Pillow, no network) that draws a
newspaper front page for Tuesday 24 November 2026 and writes it as a 1024×1024 PNG to
`/output/entry.png` (or `$MAKEFUN_OUTPUT_DIR/entry.png`). It is fully deterministic: every run
produces the same bytes.

The front page leads with the day's top story — the Ukraine peace talks around the 28-point plan —
and panels on the US–Venezuela escalation, the COP31 climate summit in Antalya, BepiColombo
entering Mercury orbit, and Verstappen's Las Vegas Grand Prix win, with a ticker of the day's
other headlines.

## Run

```sh
python3 main.py            # writes /output/entry.png
MAKEFUN_OUTPUT_DIR=out python3 main.py   # writes out/entry.png
```

## License

MIT — see `LICENSE`.
