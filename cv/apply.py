#!/usr/bin/env python3
"""One job application, one folder.

    python3 cv/apply.py new bioage-labs          # scaffold today's application
    python3 cv/apply.py list                     # what went where, and when
    python3 cv/apply.py build bioage             # resume + cover letter
    python3 cv/apply.py status bioage interview  # move it along

Each application lives in cv/applications/<YYYY-MM-DD>-<slug>/ and holds three
files:

    application.yml   the posting, the dates, the status, your notes
    profile.yml       which cv.yml content the resume shows, in what order
    letter.md         the cover letter, subject line onward

The folder name tells you what the documents were for. application.yml is the
only place the company, role, posting URL and output filenames are written
down, so profile.yml and letter.md never repeat them.

Built documents go to cv/build/<folder-name>/, which keeps the PDFs for twelve
applications sorted by application instead of by filename.

cv/applications/ is gitignored. The folder records where you have applied, and
this repository is public.
"""
from __future__ import annotations

import argparse
import datetime as dt
import re
import shutil
import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).parent))
import build as B  # noqa: E402
from letter import render_letter  # noqa: E402

ROOT = Path(__file__).resolve().parent
APPS = ROOT / "applications"
TEMPLATE = ROOT / "templates" / "application"

STATUSES = ["drafting", "applied", "screen", "interview",
            "offer", "rejected", "withdrawn"]


# --------------------------------------------------------------------------
def app_dirs() -> list[Path]:
    if not APPS.exists():
        return []
    return sorted((d for d in APPS.iterdir()
                   if d.is_dir() and (d / "application.yml").exists()),
                  reverse=True)


def meta_of(d: Path) -> dict:
    return yaml.safe_load((d / "application.yml").read_text()) or {}


def resolve(token: str) -> Path:
    """Accept a full folder name or any unambiguous fragment of one."""
    dirs = app_dirs()
    if not dirs:
        sys.exit("No applications yet. Start one: python3 cv/apply.py new <slug>")
    exact = [d for d in dirs if d.name == token]
    if exact:
        return exact[0]
    hits = [d for d in dirs if token.lower() in d.name.lower()]
    if not hits:
        sys.exit(f"No application matching {token!r}. "
                 f"Try: python3 cv/apply.py list")
    if len(hits) > 1:
        names = "\n  ".join(d.name for d in hits)
        sys.exit(f"{token!r} matches several applications:\n  {names}")
    return hits[0]


def slugify(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", str(text).lower()).strip("-")


# --------------------------------------------------------------------------
def cmd_new(args) -> None:
    if not TEMPLATE.exists():
        sys.exit(f"Missing template: {TEMPLATE}")
    day = args.date or dt.date.today().isoformat()
    dest = APPS / f"{day}-{slugify(args.slug)}"
    if dest.exists():
        sys.exit(f"Already exists: {dest.relative_to(ROOT.parent)}")
    shutil.copytree(TEMPLATE, dest)

    # Stamp today's date so the first edit is about the job, not the YAML.
    meta_path = dest / "application.yml"
    meta_path.write_text(
        meta_path.read_text().replace("created:  2000-01-01", f"created:  {day}"))

    print(f"Created {dest.relative_to(ROOT.parent)}")
    for f in sorted(p.name for p in dest.iterdir()):
        print(f"  {f}")
    print("\nFill in application.yml first; profile.yml and letter.md read "
          "the company and role from it.")


def cmd_list(args) -> None:
    dirs = app_dirs()
    if not dirs:
        print("No applications yet. Start one: python3 cv/apply.py new <slug>")
        return
    rows = []
    for d in dirs:
        m = meta_of(d)
        built = B.OUT / d.name
        docs = []
        if built.exists():
            if any(built.glob("*Resume*.pdf")):
                docs.append("resume")
            if any(built.glob("*CoverLetter*.pdf")):
                docs.append("letter")
        rows.append((
            str(m.get("applied") or m.get("created") or ""),
            str(m.get("company") or "?"),
            str(m.get("role") or "?"),
            str(m.get("status") or "drafting"),
            ", ".join(docs) or "not built",
            d.name,
        ))
    w = [max(len(r[i]) for r in rows + [("DATE", "COMPANY", "ROLE",
                                         "STATUS", "DOCUMENTS", "")])
         for i in range(5)]
    w[2] = min(w[2], 38)
    head = ("DATE", "COMPANY", "ROLE", "STATUS", "DOCUMENTS")
    print("  ".join(h.ljust(w[i]) for i, h in enumerate(head)))
    for r in rows:
        role = r[2] if len(r[2]) <= w[2] else r[2][:w[2] - 1] + "…"
        print("  ".join([r[0].ljust(w[0]), r[1].ljust(w[1]), role.ljust(w[2]),
                         r[3].ljust(w[3]), r[4]]))
    if args.verbose:
        print()
        for d in dirs:
            m = meta_of(d)
            print(f"{d.name}")
            if m.get("posting"):
                print(f"  posting  {m['posting']}")
            if m.get("notes"):
                print(f"  notes    {' '.join(str(m['notes']).split())}")


def cmd_status(args) -> None:
    d = resolve(args.id)
    if args.value not in STATUSES:
        sys.exit(f"Unknown status {args.value!r}. One of: {', '.join(STATUSES)}")
    path = d / "application.yml"
    text = path.read_text()
    if re.search(r"^status:.*$", text, re.M):
        text = re.sub(r"^status:.*$", f"status:   {args.value}", text, count=1,
                      flags=re.M)
    else:
        text += f"\nstatus:   {args.value}\n"
    path.write_text(text)
    m = meta_of(d)
    print(f"{m.get('company', d.name)}: {args.value}")


def cmd_build(args) -> None:
    d = resolve(args.id)
    m = meta_of(d)
    data = yaml.safe_load(B.DATA.read_text())
    outdir = B.OUT / d.name
    docs = m.get("documents") or {}
    # A blank `company:` in a fresh scaffold must not become "None" on disk;
    # fall back to the slug in the folder name.
    fallback = re.sub(r"^\d{4}-\d{2}-\d{2}-", "", d.name)
    company_tag = slugify(m.get("company") or fallback).replace("-", "").title()

    made = False

    prof_path = d / "profile.yml"
    if prof_path.exists():
        spec = docs.get("resume") or {}
        profile = yaml.safe_load(prof_path.read_text()) or {}
        profile.setdefault("name", "Resume")
        profile["filename"] = (spec.get("filename")
                               or f"JamesRose_Resume_{company_tag}")
        profile["label"] = (f"{m.get('role', '?')} at {m.get('company', '?')}"
                            f" ({m.get('status', 'drafting')})")
        theme = spec.get("theme") or profile.get("themes", ["berry"])[0]
        print(f"{d.name} / resume / {theme}")
        B.build_one(data, d.name, theme, not args.no_pdf, outdir,
                    profile=profile)
        made = True

    letter_path = d / "letter.md"
    if letter_path.exists() and letter_path.read_text().strip():
        spec = docs.get("letter") or {}
        stem = spec.get("filename") or f"JamesRose_CoverLetter_{company_tag}"
        subject = ", ".join(x for x in (m.get("role"), m.get("company")) if x)
        print(f"{d.name} / letter")
        render_letter(
            body=letter_path.read_text(),
            basics=data["basics"],
            stem=stem,
            outdir=outdir,
            make_pdf=not args.no_pdf,
            date=m.get("applied") or m.get("created"),
            subject=subject,
            title=f"Cover letter — {m.get('company', '')}".strip(" —"),
        )
        made = True

    if not made:
        sys.exit(f"Nothing to build in {d.relative_to(ROOT.parent)}")


# --------------------------------------------------------------------------
def main() -> None:
    ap = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd")

    p = sub.add_parser("new", help="scaffold a new application folder")
    p.add_argument("slug", help="short company name, e.g. bioage-labs")
    p.add_argument("--date", help="YYYY-MM-DD (default: today)")
    p.set_defaults(func=cmd_new)

    p = sub.add_parser("list", help="show every application and its status")
    p.add_argument("-v", "--verbose", action="store_true",
                   help="also show posting URLs and notes")
    p.set_defaults(func=cmd_list)

    p = sub.add_parser("build", help="build the resume and letter")
    p.add_argument("id", help="folder name or any unambiguous part of it")
    p.add_argument("--no-pdf", action="store_true")
    p.set_defaults(func=cmd_build)

    p = sub.add_parser("status", help="set where the application stands")
    p.add_argument("id")
    p.add_argument("value", help=" | ".join(STATUSES))
    p.set_defaults(func=cmd_status)

    args = ap.parse_args()
    if not getattr(args, "func", None):
        ap.print_help()
        return
    args.func(args)


if __name__ == "__main__":
    main()
