"""Plot the existing public aggregate; never read the private research corpus."""
from pathlib import Path
import argparse
import hashlib
import io
import json
import os
import re
import tempfile
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "docs/data/public_summary.json"
OUTPUT = ROOT / "docs/images/case-platform-counts.svg"
SOURCE_SHA256 = "6e34edc18979edc992d5609b80648df9589bec8af9e24e3c3aff9e7fbc4a1a14"


def checked_rows():
    raw = SOURCE.read_bytes()
    if hashlib.sha256(raw).hexdigest() != SOURCE_SHA256:
        raise ValueError("Public summary changed; review its provenance before plotting.")
    data = json.loads(raw)
    rows = data["per_case"]
    assert len(rows) == data["headline_metrics"]["case_count"] == 16
    assert sum(r["n"] for r in rows) == data["headline_metrics"]["canonical_case_rows"] == 130858
    for row in rows:
        assert set(row["platform_counts"]) <= {"reddit", "youtube"}
        assert all(type(n) is int and n >= 0 for n in row["platform_counts"].values())
        assert sum(row["platform_counts"].values()) == row["n"]
    return sorted(rows, key=lambda r: r["n"])


def render(png=None):
    rows = checked_rows()
    os.environ.setdefault("MPLCONFIGDIR", str(Path(tempfile.gettempdir()) / "public-summary-mpl"))
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.ticker import StrMethodFormatter
    if matplotlib.__version__ != "3.10.8":
        raise RuntimeError("Use requirements-visuals.txt for reproducible rendering.")
    with plt.rc_context({"font.family": "DejaVu Sans", "font.size": 10,
                         "svg.fonttype": "none", "svg.hashsalt": "public-case-platform-counts",
                         "axes.spines.top": False, "axes.spines.right": False}):
        fig, ax = plt.subplots(figsize=(7.4, 7.4), layout="constrained")
        y = list(range(len(rows)))
        reddit = [r["platform_counts"].get("reddit", 0) for r in rows]
        youtube = [r["platform_counts"].get("youtube", 0) for r in rows]
        ax.barh(y, reddit, label="Reddit", color="#4d6f8b", height=.65)
        ax.barh(y, youtube, left=reddit, label="YouTube", color="#bd713d", height=.65)
        ax.set(yticks=y, yticklabels=[r["case"].replace("_", " ") for r in rows],
               xlabel="Rows in the public aggregate export",
               title="Case-linked rows by platform")
        ax.xaxis.set_major_formatter(StrMethodFormatter("{x:,.0f}"))
        ax.grid(axis="x", color="#e5e5e5", linewidth=.6)
        ax.set_axisbelow(True)
        ax.legend(frameon=False, loc="lower right")
        buf = io.StringIO()
        fig.savefig(buf, format="svg", metadata={"Date": None}, facecolor="white")
        if png:
            fig.savefig(png, dpi=160, facecolor="white")
        plt.close(fig)
    svg = buf.getvalue().replace('<svg ', '<svg role="img" aria-labelledby="title desc" ', 1)
    match = re.search(r"<svg\b[^>]*>", svg)
    desc = ('<title id="title">Public aggregate case counts by platform</title>'
            '<desc id="desc">Stacked bars show Reddit and YouTube rows for sixteen canonical '
            'cases, totalling 130,858 case-linked rows. Counts describe this collected corpus, '
            'not incident frequency or representative public opinion. No raw posts or user records '
            'are included in the figure.</desc>')
    svg = svg[:match.end()] + desc + svg[match.end():]
    ET.fromstring(svg)
    return svg.encode()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--png", type=Path, help="Optional local review image")
    args = parser.parse_args()
    data = render(args.png)
    if args.check:
        assert OUTPUT.read_bytes() == data, "The SVG differs from fresh Matplotlib output."
        print("PASS: pinned public aggregate, 16 case totals, platform counts and exact SVG rerender")
    else:
        OUTPUT.parent.mkdir(parents=True, exist_ok=True)
        OUTPUT.write_bytes(data)
        print(OUTPUT.relative_to(ROOT))


if __name__ == "__main__":
    main()
