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

## Tailoring to a job description

```bash
cp cv/profiles/_template-tailored.yml cv/profiles/acme-scientist.yml
# edit it
python3 cv/build.py --profile acme-scientist --theme slate
```

Three levers, in the order that matters:

1. **The summary.** Add a new entry under `summaries:` in `cv.yml` written for that
   role and point the profile's `summary:` at it. This does more than anything else.
2. **Section order.** The order in the profile is the order on the page. Lead with
   whatever the posting leads with.
3. **`include:` lists.** Ids from `cv.yml`, in the order you want. Drop what is
   irrelevant. `highlights:` does the same thing per job. `tags: [selected]` pulls
   by keyword instead, and `limit: 4` caps a section.

## Publishing to the website

`publish.yml` maps a profile and theme onto `assets/resume.pdf` and `assets/cv.pdf`,
which is what `cv.qmd` serves. Change a theme there and run `--publish`.

## Keeping it current

When a paper moves from under review to published, edit its entry in `cv.yml`:
change `status`, add the `venue`, `detail`, and `url`, and clear `note`. The status
drives the little tag that appears beside it. Then `--publish`.
