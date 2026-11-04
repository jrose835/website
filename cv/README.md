# Resume & CV

One content file, several looks, two published PDFs. Nothing is hand-formatted.

```bash
python3 cv/build.py --list                        # what exists
python3 cv/build.py --all                         # build everything into cv/build/
python3 cv/build.py --profile resume --theme slate
python3 cv/build.py --publish                     # rebuild + copy into assets/ for the site

python3 cv/apply.py list                          # every job application and its status
python3 cv/apply.py new acme-bio                  # start a tailored application
python3 cv/apply.py build acme                    # its resume and cover letter
```

Needs `pyyaml` and `jinja2` (`pip3 install --user pyyaml jinja2`). PDFs are rendered
by headless Chrome, which is found automatically on macOS. Without Chrome you still
get HTML you can open and print yourself.

## The three pieces

**`cv.yml`** is the only place content lives. Add a paper, a job, a bullet, a skill
here and every document picks it up. Every item has a stable `id` and some `tags`.

**`profiles/*.yml`** decide what appears, in what order, for one kind of document.
`resume.yml` is the general two-to-three page version; `cv.yml` is the full
academic record including posters, talks, teaching, and service. A profile
tailored to one job posting does not live here; it lives with that
application, under `cv/applications/`.

**`themes/*/`** decide how it looks. Each is a Jinja template plus a stylesheet.
The shared section markup lives in `themes/_shared/sections.html.j2`, so a theme
only has to style stable class names.

| theme | feel | good for |
|---|---|---|
| `berry` | warm serif, matches the website's type and colour | the default; the one linked from the site |
| `slate` | dark header band, teal rules, modern sans | industry and biotech applications |
| `classic` | Garamond, centred, hanging-indent bibliography | academic CV, fellowships, faculty applications |
| `compact` | dense, monospace metadata, section labels in a left spine | technical and computational roles, ATS-friendly |

## Applying to a job

One application, one folder. `cv/applications/<date>-<company>/` holds the
posting, the tailored resume profile and the cover letter together, so the
folder name alone tells you what the documents were for.

```bash
python3 cv/apply.py new acme-bio        # scaffold today's application
python3 cv/apply.py list                # what went where, and when
python3 cv/apply.py build acme          # resume + cover letter
python3 cv/apply.py status acme interview
```

`build` and `status` take the folder name or any unambiguous part of it, so
`acme` is enough. Built documents land in `cv/build/<folder-name>/`, which
keeps a dozen applications sorted by application rather than by filename.

Three files per folder:

| file | holds |
|---|---|
| `application.yml` | the company, role, posting URL, dates, status, output filenames, and why the documents look the way they do |
| `profile.yml` | which `cv.yml` content the resume shows, in what order |
| `letter.md` | the cover letter, salutation onward |

`application.yml` is the only place the company and role are written down.
`profile.yml` never repeats them, and `letter.md` has no letterhead, date or
subject line: those are generated from `basics` in `cv.yml` and the
application's `applied:` date. Change your email once and every future letter
has it right.

Work the posting in this order, which is where the leverage is:

1. **Write a summary for the role.** Add an entry under `summaries:` in
   `cv.yml` and point `profile.yml`'s `summary:` at it. Nothing else moves the
   needle as much. Reusing `general` wastes the one paragraph everyone reads.
2. **Reorder the sections.** The order in `profile.yml` is the order on the
   page. If the posting opens with pipeline engineering, open with Software.
3. **Cut and reorder the bullets.** `highlights:` takes ids in the order you
   want them. Four strong bullets beat eight generic ones.
4. **Trim the skills.** A skills list that mirrors the posting's vocabulary
   reads as a match; one that lists everything reads as a list.

Two traps worth knowing. An empty include list is **not** "none": `biogen: []`
falls through to every bullet, so name the one you want. And the Education
section will not split across a page break, so it jumps whole to the next
sheet; if you land on a third page holding nothing but a footer, cut three or
four lines rather than hunting for one.

Keep the folder after you apply. It is the record of what you sent, it costs
nothing, and the next similar posting starts from it instead of from scratch.

`cv/applications/` is gitignored, because this repository is public and the
folder records where you have applied. The scaffold `apply.py new` copies from
lives in `cv/templates/application/`, which is tracked, so a fresh clone can
still start one. If you want version history for applications too, a separate
private repository is the way, not making this one private.

## Publishing to the website

The site offers one document: `assets/resume.pdf`, built from the `resume` profile
in the `berry` theme and served by `cv.qmd`. `publish.yml` controls that mapping;
change the theme there and run `--publish`.

The full academic CV still builds with `--all` into `cv/build/`. It is just not
published to the site. If a fellowship or faculty application wants it, add it
back to `publish.yml` or send the built PDF directly.

## A note on rebuilds

Chrome stamps a creation time into every PDF it writes, so rebuilding produces a
byte-different file even when nothing in `cv.yml` changed. Git will show
`assets/resume.pdf` as modified after any build. If you did not change content,
`git checkout -- assets/resume.pdf` discards the churn. Only commit the PDF when
the content actually changed.

## Keeping it current

When a paper moves from under review to published, edit its entry in `cv.yml`:
change `status`, add the `venue`, `detail`, and `url`, and clear `note`. The status
drives the little tag that appears beside it. Then `--publish`.
