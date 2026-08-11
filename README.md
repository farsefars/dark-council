# The Dark Council

Bilingual rules and a generated consumer-facing website for **The Dark Council /
Темна Рада**.

**Live site:** <https://farsefars.github.io/dark-council/>

**Rules endpoint:**
<https://farsefars.github.io/dark-council/rules/manifest.json>

## Source of truth

- `Темна Рада_latest_ua.md` — canonical Ukrainian rules.
- `dark_council_latest_en.md` — matching English rules.
- `playtest/` — teaching scripts, quick references, GM/Syndicate references, and
  playtest instruments.

The HTML is generated from these Markdown files. Do not edit
`web/dist/index.html` directly.

The same build publishes static, cache-friendly rule endpoints:

- `/rules/manifest.json`
- `/rules/uk.md`
- `/rules/en.md`
- `/rules/player-reference-uk.md`
- `/rules/player-reference-en.md`

## Update the rules

1. Edit both latest rulebooks, preserving EN/UA structure and values.
2. Rebuild and test:

   ```powershell
   Set-Location web
   python build.py
   python -m unittest -v
   python build.py --check
   ```

3. Commit the Markdown changes and regenerated `web/dist/` and `docs/` outputs.
4. Push to `main`. GitHub Pages serves the updated `docs/` directory.

The generator has no Python package dependencies. It validates section parity,
player-count thresholds, numeric rules, translation keys, Ukrainian copy guards, and
glossary annotation.

## Mechanical and exploit testing

The version-controlled simulator plays the published rules with sensible, chaotic and
strictly legal exploit-seeking policies:

```powershell
python -m sim.validate
python -m sim.experiments
```

Read `sim/README.md` for the plain-language explanation, `sim/METHODOLOGY.md` for the
testing contract, `sim/report.md` for the latest exploit findings, and
`sim/satisfaction-report.md` for the individual/group satisfaction diagnostics.
`sim/contract-report.md` records the fee, stake, per-player-cap and table-cap tests
behind the published Contract configuration.

## Browser QA

Optional browser tests reuse an installed Microsoft Edge:

```powershell
Set-Location web\qa
npm ci
npm test
```

They check both languages at desktop, tablet, mobile and print sizes; click every
table-of-contents link; and exercise glossary hover, keyboard and touch behaviour.

## Repository structure

```text
.
├── dark_council_latest_en.md
├── Темна Рада_latest_ua.md
├── playtest/
├── sim/                          # mechanical, chaos, and exploit testing
├── web/
│   ├── build.py
│   ├── presentation.py
│   ├── theme.css
│   ├── app.js
│   ├── test_build.py
│   └── dist/index.html
└── docs/                         # GitHub Pages output (generated)
```
