#!/usr/bin/env python3
"""Render a cover letter to HTML and PDF.

This is the renderer, not a command. `apply.py` calls it with the body of an
application's letter.md; nothing else needs to.

The letterhead and the date are built here from `basics` in cv.yml and the
application's `applied:` date, so a letter.md holds only the letter: the
subject line, the salutation, the body, and the sign-off. Changing your email
address once in cv.yml changes it on every letter you ever send.

Typography deliberately matches the resume themes, so a letter and a resume
arriving together look like one document.
"""
from __future__ import annotations

import datetime as _dt
import re
import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).parent))
from build import md, to_pdf, OUT, ROOT  # noqa: E402

CSS = """
@page { size: letter; margin: 0.8in 0.9in; }
* { box-sizing: border-box; }
body {
  font-family: "Charter", "Iowan Old Style", Georgia, serif;
  font-size: 10.3pt; line-height: 1.46; color: #1a1a1a;
  margin: 0; padding: 0.8in 0.9in; max-width: 8.5in;
}
@media print { body { padding: 0; } }
.from { font-size: 9.4pt; line-height: 1.42; color: #444; margin-bottom: 1.6em; }
.from .who { font-size: 12.5pt; font-weight: 600; color: #111;
              letter-spacing: -0.01em; display: block; margin-bottom: 0.18em; }
.date { margin: 0 0 1.3em; color: #444; font-size: 9.9pt; }
.subject { font-weight: 600; margin: 0 0 1.35em; }
p { margin: 0 0 0.78em; }
p.salutation { margin-bottom: 0.95em; }
p.signoff { margin-top: 1.3em; margin-bottom: 0.2em; }
p.name { font-weight: 600; }
a { color: inherit; text-decoration: none; }
strong { font-weight: 600; }
"""

SIGNOFFS = ("Sincerely,", "Best regards,", "Regards,", "Yours sincerely,")


def letterhead(basics: dict) -> str:
    """Name line plus a contact line, both from cv.yml."""
    who = basics["name"]
    if basics.get("credentials"):
        who = f"{who}, {basics['credentials']}"
    bits = [basics.get("location"), basics.get("email"),
            basics.get("website"), basics.get("github")]
    contact = " · ".join(b for b in bits if b)
    return ('<p class="from"><span class="who">' + md(who) + "</span>"
            + md(contact) + "</p>")


def long_date(value) -> str:
    if isinstance(value, _dt.date):
        d = value
    else:
        try:
            d = _dt.date.fromisoformat(str(value))
        except ValueError:
            return str(value)
    return f"{d.strftime('%B')} {d.day}, {d.year}"


def render_letter(body: str, basics: dict, stem: str, outdir: Path = OUT,
                  make_pdf: bool = True, date=None, subject: str = "",
                  title: str = "Cover letter") -> Path:
    """Render `body` (Markdown paragraphs) into <outdir>/<stem>.html and .pdf."""
    parts = [letterhead(basics)]
    parts.append('<p class="date">' + md(long_date(date or _dt.date.today()))
                 + "</p>")

    paras = [b for b in re.split(r"\n\s*\n", body) if b.strip()]
    if subject and not (paras and paras[0].lstrip().startswith("**Re:")):
        paras.insert(0, f"**Re: {subject}**")

    for raw in paras:
        para = " ".join(line.strip() for line in raw.strip().splitlines())
        if not para:
            continue
        cls = ""
        if para.startswith("**Re:"):
            cls = ' class="subject"'
        elif para.startswith("Dear "):
            cls = ' class="salutation"'
        elif para in SIGNOFFS:
            cls = ' class="signoff"'
        elif para.startswith(basics["name"]) and len(parts) > 2:
            cls = ' class="name"'
        parts.append(f"<p{cls}>{md(para)}</p>")

    doc = (f'<!doctype html><html lang="en"><head><meta charset="utf-8">'
           f'<title>{basics["name"]} — {title}</title>'
           f"<style>{CSS}</style></head><body>{''.join(parts)}</body></html>")

    outdir.mkdir(parents=True, exist_ok=True)
    html_path = outdir / f"{stem}.html"
    html_path.write_text(doc)
    print(f"  html  {html_path.relative_to(ROOT.parent)}")
    pdf_path = outdir / f"{stem}.pdf"
    if make_pdf and to_pdf(html_path, pdf_path):
        print(f"  pdf   {pdf_path.relative_to(ROOT.parent)}")
    return html_path


if __name__ == "__main__":
    sys.exit("letter.py is a renderer. Use: python3 cv/apply.py build <id>")
