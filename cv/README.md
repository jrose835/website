# Resume & CV

One content file, several looks, two published PDFs. Nothing is hand-formatted.

```bash
python3 cv/build.py --list                        # what exists
python3 cv/build.py --all                         # build everything into cv/build/
python3 cv/build.py --profile resume --theme slate
python3 cv/build.py --publish                     # rebuild + copy into assets/ for the site
```

Needs `pyyaml` and `jinja2` (`pip3 install --user pyyaml jinja2`). PDFs are rendered
by headless Chrome, which is found automatically on macOS. Without Chrome you still
get HTML you can open and print yourself.

## The three pieces

**`cv.yml`** is the only place content lives. Add a paper, a job, a bullet, a skill
here and every document picks it up. Every item has a stable `id` and some `tags`.

**`profiles/*.yml`** decide what appears, in what order, for one kind of document.
`resume.yml` is the general two-to-three page version; `cv.yml` is the full
academic record including posters, talks, teaching, and service.

**`themes/*/`** decide how it looks. Each is a Jinja template plus a stylesheet.
The shared section markup lives in `themes/_shared/sections.html.j2`, so a theme
only has to style stable class names.

| theme | feel | good for |
|---|---|---|
| `berry` | warm serif, matches the website's type and colour | the default; the one linked from the site |
| `slate` | dark header band, teal rules, modern sans | industry and biotech applications |
| `classic` | Garamond, centred, hanging-indent bibliography | academic CV, fellowships, faculty applications |
| `compact` | dense, monospace metadata, section labels in a left spine | technical and computational roles, ATS-friendly |

## Tailoring to a job posting

Tailored resumes never touch the website. `--publish` is the only command that
writes into `assets/`, and `publish.yml` names only the general resume, so a
tailored build can land in `cv/build/` and nowhere else.

```bash
cp cv/profiles/_template-tailored.yml cv/profiles/acme-bio.yml
# edit it, then:
python3 cv/build.py --profile acme-bio --theme berry
```

Three keys at the top of the profile control what comes out:

| key | what it does |
|---|---|
| `name` | the PDF's document title, visible in the reader's viewer. Keep it "Resume"; never put the company here |
| `label` | a private note shown by `--list`, so you can tell your profiles apart later |
| `filename` | the file on disk, e.g. `JamesRose_Resume_AcmeBio` — this is what you attach |

Then work the posting itself, in the order that matters:

1. **Write a summary for the role.** Add a new entry under `summaries:` in
   `cv.yml` and point the profile's `summary:` at it. Nothing else moves the
   needle as much. Reusing `general` wastes the one paragraph everyone reads.
2. **Reorder the sections.** The order in the profile is the order on the page.
   If the posting opens with pipeline engineering, open with Software.
3. **Cut and reorder the bullets.** `highlights:` under an experience entry takes
   ids in the order you want them. Put the bullet that answers the posting first
   and delete the ones that don't. Four strong bullets beat eight generic ones.
4. **Trim the skills.** `include:` on the skills section. A skills list that
   mirrors the posting's vocabulary reads as a match; one that lists everything
   reads as a list.

`tags: [selected]` pulls items by keyword instead of by id, and `limit: 4` caps a
section. Omitting `include:` takes everything.

Keep the profile after you apply. It is a record of what you sent, it costs
nothing, and the next similar posting starts from it instead of from scratch.
The built PDF lives in `cv/build/`, which is gitignored, so re-run the build if
you need the file again.

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
