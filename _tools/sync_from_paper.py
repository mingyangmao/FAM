#!/usr/bin/env python3
"""Sync the project page with the paper sources in latex/.

* figures: latex/Images/*  ->  docs/static/images/*.webp
* tables:  \\label{tab:...} in latex/Sections/Results.tex  ->  <tbody> rows in
  docs/index.html, between the markers  <!-- sync:LABEL -->  <!-- /sync:LABEL -->

Run after the paper's figures or tables change (needs Pillow and poppler's
pdftocairo, e.g. `conda activate food_as_medicine`):

    python docs/_tools/sync_from_paper.py                 # figures + tables
    python docs/_tools/sync_from_paper.py --only tables

Re-encoding through pdftocairo/Pillow also drops the PDF and Illustrator
metadata (author and device names) that the original figure files carry.
GitHub Pages runs Jekyll, which skips folders starting with "_", so this
script is not published with the site.
"""
from __future__ import annotations

import argparse
import html
import re
import shutil
import subprocess
import tempfile
from pathlib import Path

from PIL import Image

DOCS = Path(__file__).resolve().parents[1]
IMAGES_OUT = DOCS / "static" / "images"
INDEX = DOCS / "index.html"

# (file in latex/Images, file in docs/static/images, width in px, lossless?)
# Charts are stored lossless so text stays crisp; figures with food photos
# are stored lossy, which is ~5x smaller at no visible cost.
FIGURES = [
    ("new_overview.png", "overview.webp", 2400, False),
    ("statics.png", "statistics.webp", 2400, True),
    ("task1_example.pdf", "task1_example.webp", 1200, False),
    ("task2.png", "task2_example.webp", 1180, False),
    ("task1_condition_radar_baseline.pdf", "radar_baseline.webp", 1000, True),
    ("task1_condition_radar_cot.pdf", "radar_cot.webp", 1000, True),
    ("task1_condition_radar_ki.pdf", "radar_ki.webp", 1000, True),
    ("task1_condition_radar_cot_ki.pdf", "radar_cot_ki.webp", 1000, True),
    ("vision_probe_1x4.pdf", "vision_probe.webp", 2400, True),
    ("human_vlm_comparison.png", "human_vlm.webp", 1600, True),
]

# Tables whose body rows are regenerated: label -> file in latex/Sections
TABLES = {
    "tab:main_results": "Results.tex",
    "tab:ctc": "Results.tex",
    "tab:input_settings": "Results.tex",
}

RULE = re.compile(r"\\(?:top|mid|bottom)rule|\\cmidrule(?:\([^)]*\))?\{[^}]*\}")
MULTICOL = re.compile(r"\\multicolumn\{(\d+)\}\{[^}]*\}\{(.*)\}", re.S)


# ---------------------------------------------------------------- figures --

def load_figure(src: Path, width: int) -> Image.Image:
    if src.suffix.lower() == ".pdf":
        with tempfile.TemporaryDirectory() as tmp:
            stem = Path(tmp) / "fig"
            subprocess.run(
                ["pdftocairo", "-png", "-singlefile", "-scale-to-x", str(width),
                 "-scale-to-y", "-1", str(src), str(stem)],
                check=True,
            )
            im = Image.open(f"{stem}.png")
            im.load()
    else:
        im = Image.open(src)
        im.load()
        if im.width > width:
            height = round(im.height * width / im.width)
            im = im.resize((width, height), Image.LANCZOS)
    if im.mode in ("RGBA", "LA", "P"):
        im = im.convert("RGBA")
        white = Image.new("RGB", im.size, "white")
        white.paste(im, mask=im.getchannel("A"))
        return white
    return im.convert("RGB")


def sync_figures(paper: Path) -> None:
    if shutil.which("pdftocairo") is None:
        raise SystemExit("pdftocairo not found (install poppler-utils)")
    IMAGES_OUT.mkdir(parents=True, exist_ok=True)
    for name, out_name, width, lossless in FIGURES:
        im = load_figure(paper / "Images" / name, width)
        out = IMAGES_OUT / out_name
        if lossless:
            im.save(out, "WEBP", lossless=True, quality=100, method=6)
        else:
            im.save(out, "WEBP", quality=88, method=6)
        print(f"{out.relative_to(DOCS)}  {im.width}x{im.height}  "
              f"{out.stat().st_size / 1024:.0f} KB")


# ----------------------------------------------------------------- tables --

def strip_comments(tex: str) -> str:
    return re.sub(r"(?<!\\)%.*", "", tex)


def table_body(tex: str, label: str) -> str:
    """Rows between the first \\midrule and \\bottomrule of the tabular
    that belongs to \\label{label} (the label follows its tabular)."""
    at = tex.index(f"\\label{{{label}}}")
    start = tex.rindex("\\begin{tabular}", 0, at)
    end = tex.index("\\end{tabular}", start)
    tabular = tex[start:end]
    return tabular[tabular.index("\\midrule"):tabular.rindex("\\bottomrule")]


def unwrap(text: str) -> str:
    """Drop the formatting commands used inside the result cells."""
    text = re.sub(r"\\(?:textbf|underline|textit|mathbf|boldsymbol)\{", "", text)
    return text.replace("{", "").replace("}", "").replace("$", "").strip()


def cell_html(raw: str) -> str:
    span = 1
    m = MULTICOL.fullmatch(raw)
    if m:
        span, raw = int(m.group(1)), m.group(2)
    classes = []
    if "\\textbf" in raw:
        classes.append("b")
    if "\\underline" in raw:
        classes.append("top")
    value = unwrap(raw)
    if value == "--":
        value = "–"
    elif value.startswith("-"):
        value = "−" + value[1:]
    attrs = f' colspan="{span}"' if span > 1 else ""
    attrs += f' class="{" ".join(classes)}"' if classes else ""
    return f"<td{attrs}>{html.escape(value)}</td>"


def rows_html(body: str) -> list[str]:
    rows, separated = [], False
    for chunk in body.split("\\\\"):
        separated |= bool(RULE.search(chunk))
        chunk = RULE.sub("", chunk).strip()
        if not chunk:
            continue
        name, *cells = [c.strip() for c in chunk.split("&")]
        classes = []
        if separated and rows:
            classes.append("sep")
        if "\\textit" in name:
            classes.append("ref")
        tr = f' class="{" ".join(classes)}"' if classes else ""
        th = f'<th scope="row">{html.escape(unwrap(name))}</th>'
        rows.append(f"<tr{tr}>{th}{''.join(cell_html(c) for c in cells)}</tr>")
        separated = False
    return rows


def sync_tables(paper: Path) -> None:
    page = INDEX.read_text(encoding="utf-8")
    for label, section in TABLES.items():
        tex = strip_comments((paper / "Sections" / section).read_text(encoding="utf-8"))
        rows = rows_html(table_body(tex, label))
        marker = re.compile(
            rf"(?P<indent>[ \t]*)<!-- sync:{re.escape(label)} -->.*?<!-- /sync:{re.escape(label)} -->",
            re.S,
        )
        m = marker.search(page)
        if m is None:
            raise SystemExit(f"index.html has no markers for {label}")
        ind = m.group("indent")
        block = "\n".join(
            [f"{ind}<!-- sync:{label} -->"]
            + [ind + r for r in rows]
            + [f"{ind}<!-- /sync:{label} -->"]
        )
        page = page[:m.start()] + block + page[m.end():]
        print(f"{label}: {len(rows)} rows")
    INDEX.write_text(page, encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--paper-dir", type=Path, default=DOCS.parent / "latex",
                        help="paper sources with Images/ and Sections/ (default: latex/)")
    parser.add_argument("--only", choices=["figures", "tables"])
    args = parser.parse_args()
    if args.only in (None, "figures"):
        sync_figures(args.paper_dir)
    if args.only in (None, "tables"):
        sync_tables(args.paper_dir)


if __name__ == "__main__":
    main()
