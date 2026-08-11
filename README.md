# The Dark Council

Bilingual rules and a generated consumer-facing website for **The Dark Council /
Темна Рада**.

**Live site:** <https://vibadarl_microsoft.github.io/personalproject_darkcouncil/>

**Rules backend:**
<https://vibadarl_microsoft.github.io/personalproject_darkcouncil/rules/manifest.json>

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
├── web/
│   ├── build.py
│   ├── presentation.py
│   ├── theme.css
│   ├── app.js
│   ├── test_build.py
│   └── dist/index.html
└── docs/                         # GitHub Pages output (generated)
```
