#!/usr/bin/env python3
"""
Build Jim Rose's resume/CV from cv.yml.

    python3 cv/build.py --all                        # every profile x its themes
    python3 cv/build.py --profile resume --theme berry
    python3 cv/build.py --profile cv --theme classic --no-pdf
    python3 cv/build.py --list                       # show profiles and themes

Content lives in cv.yml. Which content appears, in what order, lives in
cv/profiles/*.yml. How it looks lives in cv/themes/*/.

To tailor to a job description, copy a profile, reorder/trim the `include`
lists, point `summary` at a new entry in cv.yml's `summaries:`, and build it.
"""

from __future__ import annotations

import argparse
import html
import re
import shutil
import subprocess
import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    sys.exit("Missing dependency: pip3 install --user pyyaml jinja2")
try:
    from jinja2 import Environment, FileSystemLoader, select_autoescape
except ImportError:
    sys.exit("Missing dependency: pip3 install --user pyyaml jinja2")

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "cv.yml"
THEMES = ROOT / "themes"
PROFILES = ROOT / "profiles"
OUT = ROOT / "build"

CHROME_CANDIDATES = [
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "/Applications/Chromium.app/Contents/MacOS/Chromium",
    "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
    shutil.which("google-chrome") or "",
    shutil.which("chromium") or "",
]

MONTHS = {
    "01": "Jan", "02": "Feb", "03": "Mar", "04": "Apr",
    "05": "May", "06": "Jun", "07": "Jul", "08": "Aug",
    "09": "Sep", "10": "Oct", "11": "Nov", "12": "Dec",
}


# --------------------------------------------------------------------------
# Tiny inline-markdown renderer: **bold**, *italic*, `code`, [text](url)
# --------------------------------------------------------------------------
def md(text) -> str:
    if text is None:
        return ""
    s = html.escape(str(text).strip())
    s = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r'<a href="\2">\1</a>', s)
    s = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", s)
    s = re.sub(r"(?<!\*)\*([^*]+?)\*(?!\*)", r"<em>\1</em>", s)
    s = re.sub(r"`([^`]+?)`", r"<code>\1</code>", s)
    s = s.replace("&amp;mdash;", "&mdash;")
    return s


def daterange(start: str, end: str) -> str:
    """'2024-09' + '' -> 'Sep 2024 – Present'; '2019' + '2024' -> '2019 – 2024'."""
    def fmt(v):
        v = str(v or "").strip()
        if not v:
            return ""
        if "-" in v:
            y, m = v.split("-")[:2]
            return f"{MONTHS.get(m, m)} {y}"
        return v
    a, b = fmt(start), fmt(end) or "Present"
    return f"{a} &ndash; {b}" if a else b


# --------------------------------------------------------------------------
# Section resolution
# --------------------------------------------------------------------------
def pick(items, include=None, tags=None, limit=None):
    """Select and order items by explicit id list, else by tag, else all."""
    items = items or []
    if include:
        by_id = {it.get("id"): it for it in items if isinstance(it, dict)}
        missing = [i for i in include if i not in by_id]
        if missing:
            print(f"    ! unknown ids ignored: {', '.join(missing)}", file=sys.stderr)
        chosen = [by_id[i] for i in include if i in by_id]
    elif tags:
        want = set(tags)
        chosen = [it for it in items if want & set(it.get("tags") or [])]
    else:
        chosen = list(items)
    return chosen[:limit] if limit else chosen


def resolve(data: dict, profile: dict) -> list[dict]:
    """Turn a profile's section specs into concrete render-ready sections."""
    out = []
    for spec in profile.get("sections", []):
        key = spec["key"]
        raw = data.get(key, [])
        chosen = pick(raw, spec.get("include"), spec.get("tags"), spec.get("limit"))
        if not chosen:
            continue

        # Per-entry highlight filtering for experience-shaped sections.
        hl_map = spec.get("highlights") or {}
        max_hl = spec.get("max_highlights")
        rendered = []
        for it in chosen:
            it = dict(it)
            if "highlights" in it and isinstance(it["highlights"], list):
                hls = it["highlights"]
                if it.get("id") in hl_map:
                    hls = pick(hls, include=hl_map[it["id"]])
                elif spec.get("highlight_tags"):
                    hls = pick(hls, tags=spec["highlight_tags"])
                if max_hl:
                    hls = hls[:max_hl]
                it["highlights"] = hls
            rendered.append(it)

        out.append({
            "key": key,
            "title": spec.get("title", key.title()),
            "note": spec.get("note", ""),
            "style": spec.get("style", ""),
            "items": rendered,
        })
    return out


def group_publications(items):
    """Split pubs into 'In press / under review' and 'Published' for CV themes."""
    pending_status = {"inpress", "review", "prep"}
    pending = [p for p in items if p.get("status") in pending_status]
    out = [p for p in items if p.get("status") not in pending_status]
    return pending, out


# --------------------------------------------------------------------------
# Rendering
# --------------------------------------------------------------------------
def env_for(theme_dir: Path) -> Environment:
    env = Environment(
        loader=FileSystemLoader([str(theme_dir), str(THEMES / "_shared")]),
        autoescape=select_autoescape(enabled_extensions=(), default=False),
        trim_blocks=True,
        lstrip_blocks=True,
    )
    env.filters["md"] = md
    env.filters["daterange"] = daterange
    env.globals["group_publications"] = group_publications
    return env


def build_one(data, profile_name, theme_name, make_pdf=True, outdir=OUT):
    profile_path = PROFILES / f"{profile_name}.yml"
    if not profile_path.exists():
        sys.exit(f"No such profile: {profile_path}")
    theme_dir = THEMES / theme_name
    if not (theme_dir / "template.html.j2").exists():
        sys.exit(f"No such theme: {theme_dir}")

    tcfg = {}
    tcfg_path = theme_dir / "theme.yml"
    if tcfg_path.exists():
        tcfg = yaml.safe_load(tcfg_path.read_text()) or {}
    if tcfg.get("pdf") is False:
        make_pdf = False

    profile = yaml.safe_load(profile_path.read_text())
    sections = resolve(data, profile)

    css = (theme_dir / "style.css").read_text()
    env = env_for(theme_dir)
    tmpl = env.get_template("template.html.j2")
    html_out = tmpl.render(
        basics=data["basics"],
        summary=data["summaries"].get(profile.get("summary", "general"), ""),
        sections=sections,
        profile=profile,
        css=css,
        theme=theme_name,
    )

    outdir.mkdir(parents=True, exist_ok=True)
    stem = f"JamesRose_{profile_name}_{theme_name}"
    html_path = outdir / f"{stem}.html"
    html_path.write_text(html_out)
    print(f"  html  {html_path.relative_to(ROOT.parent)}")

    if make_pdf:
        pdf_path = outdir / f"{stem}.pdf"
        if to_pdf(html_path, pdf_path):
            print(f"  pdf   {pdf_path.relative_to(ROOT.parent)}")
    return html_path


def to_pdf(html_path: Path, pdf_path: Path) -> bool:
    chrome = next((c for c in CHROME_CANDIDATES if c and Path(c).exists()), None)
    if not chrome:
        print("  ! no Chrome/Chromium found — HTML only "
              "(open it and print to PDF manually)", file=sys.stderr)
        return False
    cmd = [
        chrome, "--headless=new", "--disable-gpu", "--no-sandbox",
        "--no-pdf-header-footer", "--run-all-compositor-stages-before-draw",
        "--virtual-time-budget=10000",
        f"--print-to-pdf={pdf_path}", html_path.as_uri(),
    ]
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    if r.returncode != 0 or not pdf_path.exists():
        print(f"  ! PDF failed: {r.stderr.strip()[:400]}", file=sys.stderr)
        return False
    return True


# --------------------------------------------------------------------------
def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--profile", help="profile name (see cv/profiles/)")
    ap.add_argument("--theme", help="theme name (see cv/themes/)")
    ap.add_argument("--all", action="store_true",
                    help="build every profile against every theme it lists")
    ap.add_argument("--list", action="store_true", help="list profiles and themes")
    ap.add_argument("--publish", action="store_true",
                    help="build the documents named in cv/publish.yml and copy "
                         "them into assets/ for the website")
    ap.add_argument("--no-pdf", action="store_true", help="skip PDF rendering")
    ap.add_argument("--out", default=str(OUT), help="output directory")
    args = ap.parse_args()

    themes = sorted(p.name for p in THEMES.iterdir()
                    if p.is_dir() and not p.name.startswith("_"))
    profiles = sorted(p.stem for p in PROFILES.glob("*.yml")
                      if not p.name.startswith("_"))

    if args.list:
        print("themes:  " + ", ".join(themes))
        print("profiles:")
        for p in profiles:
            meta = yaml.safe_load((PROFILES / f"{p}.yml").read_text())
            print(f"  {p:<10} {meta.get('name', '')}")
        return

    data = yaml.safe_load(DATA.read_text())
    outdir = Path(args.out)

    if args.publish:
        spec = yaml.safe_load((ROOT / "publish.yml").read_text())
        for item in spec["publish"]:
            print(f"{item['profile']} / {item['theme']}")
            build_one(data, item["profile"], item["theme"], True, outdir)
            src = outdir / f"JamesRose_{item['profile']}_{item['theme']}.pdf"
            dst = (ROOT / item["as"]).resolve()
            if not src.exists():
                print(f"  ! {src.name} was not produced; nothing published",
                      file=sys.stderr)
                continue
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)
            print(f"  ->    {dst.relative_to(ROOT.parent)}")
        return

    if args.all:
        for p in profiles:
            meta = yaml.safe_load((PROFILES / f"{p}.yml").read_text())
            for t in meta.get("themes", themes):
                print(f"{p} / {t}")
                build_one(data, p, t, not args.no_pdf, outdir)
        return

    if not (args.profile and args.theme):
        ap.error("need --profile and --theme (or --all / --list)")
    print(f"{args.profile} / {args.theme}")
    build_one(data, args.profile, args.theme, not args.no_pdf, outdir)


if __name__ == "__main__":
    main()
