# The Dark Council rules website

The Markdown rulebooks remain the source of truth. Never edit `dist/index.html`
directly.

## Rebuild

From this directory:

```powershell
python build.py
```

Useful options:

```powershell
python build.py --check
python -m unittest -v
python build.py --open
python build.py --watch
```

- `--check` validates all source files and confirms the generated file is current.
- `python -m unittest -v` mutation-tests drift detection and audits language isolation,
  public collapsibles, IDs, thresholds, bilingual visuals, and offline output.
- `--open` builds and opens the page in the default browser.
- `--watch` rebuilds whenever a source file changes.

The result is written to both `dist/index.html` (local artifact) and
`../docs/index.html` (GitHub Pages output). It needs no web server, external font,
package install, or network connection.

## Browser layout QA

The browser test reuses the installed Microsoft Edge:

```powershell
Set-Location qa
npm ci
npm test
```

It checks both languages at desktop, tablet and mobile widths, clicks every table of
contents link, verifies the public Syndicate/GM collapsibles, checks print isolation,
and writes screenshots to `qa\screenshots`.

## Updating rules

1. Edit `..\Темна Рада_latest_ua.md` and `..\dark_council_latest_en.md`.
2. Keep both languages structurally matched.
3. Run `python build.py`.
4. If the build reports drift, update only the relevant visual label or assertion in
   `presentation.py`; do not weaken the check.

Sections 0–10 form the normal player path. Section 11 (Syndicate) and section 12
(GM) are public, searchable, printable collapsible sections.

The generated page leads with Section 0 ("The Game in 60 Seconds"). The visual
reference appears after the full rules and quick reference. Capitalised game terms are
annotated during the build with inflection-aware glossary triggers; hover, focus or tap
one to open the shared tooltip.
