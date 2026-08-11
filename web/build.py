"""Build the self-contained Dark Council consumer rules page."""

from __future__ import annotations

import argparse
import html
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import time
import webbrowser

from md import Section, find_section, heading_count, render_markdown, split_sections
from presentation import (
    FACTIONS,
    FIVE_THINGS,
    GLOSSARY,
    RULE_ASSERTIONS,
    SYNDICATE_ONLY_TERMS,
    UI,
)


HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
SOURCES = {
    "ua": ROOT / "Темна Рада_latest_ua.md",
    "en": ROOT / "dark_council_latest_en.md",
}
QUICK_SOURCES = {
    "ua": ROOT / "playtest" / "player-reference-ua.md",
    "en": ROOT / "playtest" / "player-reference-en.md",
}
ASSETS = [HERE / "theme.css", HERE / "app.js", HERE / "presentation.py", HERE / "md.py"]
OUTPUT = HERE / "dist" / "index.html"
RULES_OUTPUT = HERE / "dist" / "rules"
PAGES_OUTPUT = ROOT / "docs" / "index.html"
PAGES_RULES_OUTPUT = ROOT / "docs" / "rules"


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def parse_scaling(section: Section) -> dict[str, dict[str, str]]:
    rows: dict[str, dict[str, str]] = {}
    for line in section.body.splitlines():
        if not re.match(r"^\|\s*\d+\s*\|", line):
            continue
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if len(cells) != 5:
            raise ValueError(f"Unexpected scaling row: {line}")
        players, factions, magnates, magnate_threshold, syndicate_threshold = cells
        rows[players] = {
            "factions": factions,
            "magnates": magnates,
            "magnateThreshold": magnate_threshold,
            "syndicateThreshold": syndicate_threshold,
        }
    if set(rows) != {str(number) for number in range(8, 16)}:
        raise ValueError(f"Scaling table must contain player counts 8–15, found {sorted(rows)}")
    return rows


def validate(
    markdowns: dict[str, str],
    sections: dict[str, list[Section]],
    scaling: dict[str, dict[str, dict[str, str]]],
) -> None:
    for language in ("ua", "en"):
        numbers = [section.number for section in sections[language]]
        if numbers != list(range(13)):
            raise ValueError(f"{language}: expected top-level sections 0–12, found {numbers}")

    counts = {language: heading_count(text) for language, text in markdowns.items()}
    if counts["ua"] != counts["en"]:
        raise ValueError(f"Heading parity failed: UA={counts['ua']}, EN={counts['en']}")
    for number in range(13):
        ua_count = heading_count(find_section(sections["ua"], number).body)
        en_count = heading_count(find_section(sections["en"], number).body)
        if ua_count != en_count:
            raise ValueError(
                f"Heading parity failed inside §{number}: UA={ua_count}, EN={en_count}"
            )

    if scaling["ua"] != scaling["en"]:
        raise ValueError("The Ukrainian and English player-count scaling tables differ")

    for language, assertions in RULE_ASSERTIONS.items():
        by_number = {section.number: section.body for section in sections[language]}
        for section_number, pattern in assertions:
            if not re.search(pattern, by_number[section_number], flags=re.DOTALL | re.IGNORECASE):
                raise ValueError(
                    f"{language} §{section_number}: expected rule pattern not found: {pattern}"
                )

    for language, forbidden in SYNDICATE_ONLY_TERMS.items():
        player_text = "\n".join(section.body for section in sections[language] if section.number <= 10)
        leaked = [term for term in forbidden if term.casefold() in player_text.casefold()]
        if leaked:
            raise ValueError(f"{language}: Syndicate-only terms leaked into player rules: {leaked}")


def validate_interface_data() -> None:
    if set(UI["ua"]) != set(UI["en"]):
        raise ValueError("The Ukrainian and English UI translation keys differ")
    source = read(Path(__file__))
    references = set(re.findall(r'(?:UI\[[^\]]+\]|ui)\["([^"]+)"\]', source))
    references.update(re.findall(r'i18n\("([^"]+)"', source))
    references.update(re.findall(r'data-i18n(?:-label)?="([^"]+)"', source))
    references.discard("{key}")
    unused = set(UI["ua"]) - references
    missing = references - set(UI["ua"])
    if unused or missing:
        raise ValueError(
            f"UI translation key drift: unused={sorted(unused)}, missing={sorted(missing)}"
        )

    ids = {
        language: [entry["id"] for entry in entries]
        for language, entries in GLOSSARY.items()
    }
    if ids["ua"] != ids["en"] or len(ids["ua"]) != len(set(ids["ua"])):
        raise ValueError("Glossary IDs must be unique and structurally matched")
    for language, entries in GLOSSARY.items():
        for entry in entries:
            re.compile(entry["pattern"])


def i18n(key: str, *, tag: str = "span", css: str = "") -> str:
    class_attr = f' class="{css}"' if css else ""
    return f'<{tag}{class_attr} data-i18n="{key}">{html.escape(UI["ua"][key])}</{tag}>'


def language_panel(language: str) -> str:
    hidden = " hidden" if language == "en" else ""
    return f'data-lang-panel data-lang="{language}"{hidden}'


class TermAnnotator(HTMLParser):
    SKIP_TAGS = {
        "a",
        "button",
        "code",
        "h1",
        "h2",
        "h3",
        "h4",
        "h5",
        "h6",
        "pre",
        "script",
        "style",
        "summary",
        "textarea",
    }

    def __init__(self, entries: list[dict[str, str]]) -> None:
        super().__init__(convert_charrefs=False)
        self.output: list[str] = []
        self.skip_depth = 0
        alternatives = [
            f"(?P<t{index}>{entry['pattern']})" for index, entry in enumerate(entries)
        ]
        self.pattern = re.compile(r"(?<!\w)(?:" + "|".join(alternatives) + r")(?!\w)")
        self.entries = entries

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self.output.append(self.get_starttag_text())
        if tag in self.SKIP_TAGS:
            self.skip_depth += 1

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self.output.append(self.get_starttag_text())

    def handle_endtag(self, tag: str) -> None:
        self.output.append(f"</{tag}>")
        if tag in self.SKIP_TAGS:
            self.skip_depth -= 1

    def handle_data(self, data: str) -> None:
        if self.skip_depth:
            self.output.append(html.escape(data, quote=False))
            return
        position = 0
        for match in self.pattern.finditer(data):
            self.output.append(html.escape(data[position : match.start()], quote=False))
            group = next(index for index, value in enumerate(match.groups()) if value is not None)
            term_id = self.entries[group]["id"]
            self.output.append(
                f'<button type="button" class="term-ref" data-term="{term_id}" '
                f'aria-expanded="false">{html.escape(match.group(0))}</button>'
            )
            position = match.end()
        self.output.append(html.escape(data[position:], quote=False))

    def handle_entityref(self, name: str) -> None:
        self.output.append(f"&{name};")

    def handle_charref(self, name: str) -> None:
        self.output.append(f"&#{name};")

    def handle_comment(self, data: str) -> None:
        self.output.append(f"<!--{data}-->")

    def result(self) -> str:
        return "".join(self.output)


def annotate_terms(markup: str, language: str) -> str:
    annotator = TermAnnotator(GLOSSARY[language])
    annotator.feed(markup)
    annotator.close()
    return annotator.result()


def toc(language: str, sections: list[Section]) -> str:
    links = []
    for section in sections:
        links.append(
            f'<li><a href="#{language}-section-{section.number}" '
            f'data-section-link="{section.number}"><span>{section.number:02d}</span> '
            f"{html.escape(section.title)}</a></li>"
        )
    links.extend(
        [
            f'<li class="toc-extra"><a href="#quick-{language}">◆ {html.escape(UI[language]["quick"])}</a></li>',
            f'<li class="toc-extra"><a href="#diagrams-{language}">◆ {html.escape(UI[language]["diagrams"])}</a></li>',
        ]
    )
    return (
        f'<nav class="toc" {language_panel(language)} aria-label="{html.escape(UI[language]["contents"])}">'
        f'<h2>{html.escape(UI[language]["contents"])}</h2><ol>{"".join(links)}</ol></nav>'
    )


def hero(language: str) -> str:
    meta = (
        ("8–15", "гравців" if language == "ua" else "players"),
        ("3", "раунди" if language == "ua" else "rounds"),
        ("30/20/15", "хв приватної фази" if language == "ua" else "min private phases"),
    )
    return (
        f'<section class="hero" {language_panel(language)}><div class="hero-inner">'
        f'<p class="eyebrow">{html.escape(UI[language]["start_here"])}</p>'
        f'<h1>{html.escape(UI[language]["title"])}</h1>'
        f'<p class="hero-subtitle">{html.escape(UI[language]["subtitle"])}</p>'
        f'<div class="hero-meta">{"".join(f"<span><strong>{n}</strong> {html.escape(label)}</span>" for n, label in meta)}</div>'
        "</div></section>"
    )


def five_things(language: str) -> str:
    cards = "".join(
        f'<article class="memory-card"><span class="memory-number">{index}</span>'
        f"<strong>{html.escape(title)}</strong><small>{html.escape(copy)}</small></article>"
        for index, (title, copy) in enumerate(FIVE_THINGS[language], 1)
    )
    return (
        f'<section class="experience-block"><p class="chapter-kicker">{"Головне" if language == "ua" else "Essentials"}</p>'
        f'<h2>{html.escape(UI[language]["five_things"])}</h2><div class="five-things">{cards}</div></section>'
    )


def game_flow(language: str) -> str:
    ui = UI[language]
    private_times = {
        1: f'{ui["private"]} · {"30 хв" if language == "ua" else "30 min"}',
        2: f'{ui["private"]} · {"20 хв" if language == "ua" else "20 min"}',
        3: f'{ui["private"]} · {"15 хв" if language == "ua" else "15 min"}',
    }
    arc = [
        (ui["prep"], "", "картки" if language == "ua" else "cards"),
        (f'{ui["round"]} 1', "", f'{ui["hit"]} · {ui["private"]} · {ui["council"]} · {ui["leaders"]}'),
        (f'{ui["round"]} 2', ui["payout"], f'{ui["hit"]} · {ui["auction"]} · {ui["private"]} · {ui["council"]} · {ui["leaders"]}'),
        (f'{ui["round"]} 3', ui["payout"], f'{ui["hit"]} · {ui["private"]} · {ui["council"]}'),
        (ui["final"], "", f'{ui["nominate"]} · {ui["reveal"]} · {ui["ballot"]}'),
    ]
    arc_html = "".join(
        f'<div class="arc-step">{f"<span class=payout-badge>{html.escape(badge)}</span>" if badge else ""}'
        f"<strong>{html.escape(title)}</strong><span>{html.escape(copy)}</span></div>"
        for title, badge, copy in arc
    )
    rounds = [
        (f'{ui["round"]} 1', [ui["hit"], private_times[1], ui["council"], ui["leaders"]]),
        (
            f'{ui["round"]} 2',
            [ui["payout"], ui["hit"], ui["auction"], private_times[2], ui["council"], ui["leaders"]],
        ),
        (f'{ui["round"]} 3', [ui["payout"], ui["hit"], private_times[3], ui["council"], ui["final"]]),
    ]
    round_html = []
    for label, steps in rounds:
        sequence = '<span class="arrow">→</span>'.join(
            f"<span>{html.escape(step)}</span>" for step in steps
        )
        round_html.append(
            f'<div class="round-strip"><div class="round-label">{html.escape(label)}</div>'
            f'<div class="round-steps">{sequence}</div></div>'
        )
    return (
        f'<section class="experience-block"><p class="chapter-kicker">{"Послідовність" if language == "ua" else "Sequence"}</p>'
        f'<h2>{html.escape(ui["flow"])}</h2><div class="game-arc">{arc_html}</div>'
        f'<div class="rounds">{"".join(round_html)}</div></section>'
    )


def council_visual(language: str) -> str:
    ui = UI[language]
    outcomes = [
        ("", ui["vote_fails"], "+3", "to the accused" if language == "en" else "отримує звинувачений"),
        ("danger", ui["innocent_dies"], "−1", "to each living Guilty voter" if language == "en" else "кожному, хто голосував «Винен»"),
        ("success", ui["assassin_dies"], "+5", "to each living Guilty voter" if language == "en" else "кожному, хто голосував «Винен»"),
    ]
    cards = "".join(
        f'<article class="outcome {css}"><strong>{html.escape(title)}</strong>'
        f"<b>{amount}</b><span> {html.escape(copy)}</span></article>"
        for css, title, amount, copy in outcomes
    )
    order = (
        ["Вбивство + Замовлення", "Питання Привидів", "Обговорення / Викриття / Допит", "Кінець Ради"]
        if language == "ua"
        else ["Assassination + Hit", "Ghost question", "Discussion / Expose / Interrogation", "Council closes"]
    )
    sequence = '<span class="arrow">→</span>'.join(
        f"<span>{html.escape(step)}</span>" for step in order
    )
    return (
        f'<section class="experience-block"><p class="chapter-kicker">{"Спільне рішення" if language == "ua" else "Collective decision"}</p>'
        f'<h2>{html.escape(ui["council"])}</h2><div class="round-strip council-order">'
        f'<div class="round-label">{html.escape(ui["council"])}</div><div class="round-steps">{sequence}</div></div>'
        f'<h3>{html.escape(ui["interrogation"])}</h3><div class="outcome-grid">{cards}</div></section>'
    )


def economy_visual(language: str) -> str:
    if language == "ua":
        title = "Економіка Впливу: доходи та витрати"
        income = "Дохід"
        spend = "Витрати"
        rows = [
            ("+4", "Стартовий Вплив", income),
            ("+2", "Виплата на початку Раундів 2 і 3", income),
            ("+5 / +10", "Виконаний Мотив / Амбіція", income),
            ("+1", "Правильне Викриття", income),
            ("+3", "Якщо Допит не пройшов — звинуваченому", income),
            ("+5", "Якщо Страчено Вбивцю — кожному, хто голосував «Винен»", income),
            ("−2", "Неправильне Викриття", spend),
            ("−1", "Якщо Страчено Невинного — кожному, хто голосував «Винен»", spend),
            ("4, далі +1", "Почати Допит", spend),
            ("1 / 3", "Додатковий голос за Розкриття / на Фінальних Виборах", spend),
        ]
        warning = (
            "Добровільна дія дозволена лише за наявності Впливу на найбільший "
            "можливий штраф: 2 для Викриття, 1 для голосування на Допиті. "
            "Передавати Вплив можна лише під час Приватної фази."
        )
    else:
        title = "Influence: what comes in and goes out"
        income = "Gain"
        spend = "Lose / pay"
        rows = [
            ("+4", "Starting Influence", income),
            ("+2", "Stipend at the start of Rounds 2 and 3", income),
            ("+5 / +10", "Completed Motive / Ambition", income),
            ("+1", "Correct Expose", income),
            ("+3", "Interrogation fails: to the accused", income),
            ("+5", "Assassin executed: each living Guilty vote", income),
            ("−2", "Incorrect Expose", spend),
            ("−1", "Innocent executed: each living Guilty vote", spend),
            ("4, then +1", "Initiate an Interrogation", spend),
            ("1 / 3", "Extra Reveal vote / Final vote", spend),
        ]
        warning = (
            "A voluntary action requires enough Influence for its largest possible "
            "penalty: 2 to Expose, 1 to vote in an Interrogation. Influence may be "
            "transferred only during the Private Phase."
        )
    entries = "".join(
        f'<div class="economy-entry {"gain" if group == income else "cost"}">'
        f'<span class="economy-value">{html.escape(value)}</span><span class="economy-copy">'
        f"<small>{html.escape(group)}</small>{html.escape(copy)}</span></div>"
        for value, copy, group in rows
    )
    return (
        f'<section class="experience-block"><p class="chapter-kicker">{"Вплив" if language == "ua" else "Influence"}</p>'
        f"<h2>{html.escape(title)}</h2><div class=\"economy-board\">{entries}</div>"
        f'<p class="economy-warning">{html.escape(warning)}</p></section>'
    )


def evidence_visual(language: str) -> str:
    ui = UI[language]
    cards = "".join(
        f'<span class="evidence-card {"false" if index in (2, 4) else ""} {"auction" if index == 5 else ""}">?</span>'
        for index in range(1, 6)
    )
    return (
        f'<section class="experience-block"><p class="chapter-kicker">{"Інформація" if language == "ua" else "Information"}</p>'
        f'<h2>{html.escape(ui["evidence"])}</h2><div class="evidence-board">'
        f'<div class="evidence-cards">{cards}</div><div class="arrow">→</div>'
        f'<div class="evidence-copy"><strong>{html.escape(ui["true"])} · {html.escape(ui["false"])}</strong>'
        f'<span>{html.escape(ui["auction_truth"])}</span></div></div></section>'
    )


def final_visual(language: str, scaling: dict[str, dict[str, str]]) -> str:
    ui = UI[language]
    steps = [ui["nominate"], ui["reveal"], ui["buy"], ui["ballot"], ui["victory"]]
    step_html = "".join(f'<div class="final-step">{html.escape(step)}</div>' for step in steps)
    default = scaling["13"]
    thresholds = [
        (ui["factions"], "factions", default["factions"]),
        (ui["magnates"], "magnates", default["magnates"]),
        (ui["magnates_need"], "magnateThreshold", default["magnateThreshold"]),
        (ui["syndicate_needs"], "syndicateThreshold", default["syndicateThreshold"]),
    ]
    threshold_html = "".join(
        f'<article class="threshold-card"><span>{html.escape(label)}</span>'
        f'<strong data-threshold="{key}">{html.escape(value)}</strong></article>'
        for label, key, value in thresholds
    )
    faction_html = "".join(
        f'<article class="faction-card {css}"><h3>{html.escape(name)}</h3>'
        f"<p>{html.escape(copy)}</p></article>"
        for css, name, copy in FACTIONS[language]
    )
    return (
        f'<section class="experience-block"><p class="chapter-kicker">{"Розв'язка" if language == "ua" else "Endgame"}</p>'
        f'<h2>{html.escape(ui["final_flow"])}</h2><div class="final-flow">{step_html}</div>'
        f'<h3>{html.escape(ui["thresholds"])}</h3><div class="threshold-grid">{threshold_html}</div>'
        f'<div class="faction-grid">{faction_html}</div></section>'
    )


def glossary(language: str) -> str:
    terms = "".join(
        f'<button class="term-ref glossary-term" type="button" aria-expanded="false" '
        f'data-term="{entry["id"]}">{html.escape(entry["term"])}</button>'
        for entry in GLOSSARY[language]
    )
    return (
        f'<section class="experience-block"><p class="chapter-kicker">{"Швидкий пошук" if language == "ua" else "Quick lookup"}</p>'
        f'<h2>{html.escape(UI[language]["glossary"])}</h2><div class="glossary-list">{terms}</div></section>'
    )


def goals_matrix(language: str, section: Section) -> str:
    lines = section.body.splitlines()
    table_lines = [line for line in lines if line.strip().startswith("|")]
    if len(table_lines) < 4:
        raise ValueError(f"{language}: could not extract Goals matrix")
    rows = [[cell.strip("* ") for cell in line.strip().strip("|").split("|")] for line in table_lines]
    categories = rows[0][1:]
    motive_names = rows[2][1:]
    ambition_names = rows[3][1:]

    definitions: dict[str, str] = {}
    current_name: str | None = None
    current_copy: list[str] = []
    for line in lines:
        match = re.match(r"^- \*\*(.+?):\*\*\s*(.*)$", line)
        if match:
            if current_name:
                definitions[current_name] = " ".join(current_copy).strip()
            current_name = match.group(1)
            current_copy = [match.group(2)]
        elif current_name and line.startswith("  "):
            current_copy.append(line.strip())
        elif current_name and line.strip() and not line.startswith(" "):
            definitions[current_name] = " ".join(current_copy).strip()
            current_name = None
            current_copy = []
    if current_name:
        definitions[current_name] = " ".join(current_copy).strip()

    cells = []
    for index, category in enumerate(categories):
        motive = motive_names[index]
        ambition = ambition_names[index]
        cells.append(
            f'<div class="goal-column"><h4>{html.escape(category)}</h4>'
            f'<article class="goal-card motive"><span>+5</span><strong>{html.escape(motive)}</strong>'
            f"<p>{html.escape(definitions.get(motive, ''))}</p></article>"
            f'<article class="goal-card ambition"><span>+10</span><strong>{html.escape(ambition)}</strong>'
            f"<p>{html.escape(definitions.get(ambition, ''))}</p></article></div>"
        )
    heading = "Особисті Цілі: мала й велика" if language == "ua" else "Personal Goals: small and large"
    deadline = (
        "Заявіть виконання до кінця Раунду 2"
        if language == "ua"
        else "Claim completion by the end of Round 2"
    )
    return (
        f'<section class="experience-block goals-visual"><p class="chapter-kicker">{html.escape(deadline)}</p>'
        f"<h2>{html.escape(heading)}</h2><div class=\"goals-grid\">{''.join(cells)}</div></section>"
    )


def experience(language: str, sections: list[Section], scaling: dict[str, dict[str, str]]) -> str:
    markup = (
        f'<section class="experience diagrams" id="diagrams-{language}" {language_panel(language)}>'
        f'<header class="diagrams-heading"><p class="chapter-kicker">{"Наочна пам’ятка" if language == "ua" else "Visual reference"}</p>'
        f'<h2>{html.escape(UI[language]["diagrams"])}</h2></header>'
        f"{five_things(language)}{game_flow(language)}{economy_visual(language)}"
        f"{goals_matrix(language, find_section(sections, 5))}"
        f"{council_visual(language)}{evidence_visual(language)}{final_visual(language, scaling)}"
        f"{glossary(language)}</section>"
    )
    return annotate_terms(markup, language)


def render_rule_section(language: str, section: Section) -> str:
    ident = f"{language}-section-{section.number}"
    body = render_markdown(section.body, id_prefix=f"{ident}-")
    heading = (
        f'<header class="section-heading"><span class="section-number">{section.number:02d}</span>'
        f"<h2>{html.escape(section.title)}</h2></header>"
    )
    if section.number in {8, 9}:
        label = "Показати деталі" if language == "ua" else "Show details"
        body = f'<details class="progressive"><summary>{label}</summary>{body}</details>'
    if section.number >= 11:
        summary_label = (
            f"Розділ {section.number} · {section.title}"
            if language == "ua"
            else f"Section {section.number} · {section.title}"
        )
        return (
            f'<details class="section-collapse rule-section" id="{ident}" '
            f'data-section="{section.number}"><summary>{html.escape(summary_label)}</summary>'
            f'<div class="collapsed-rule-body">{heading}{body}</div></details>'
        )
    return (
        f'<section class="rule-section" id="{ident}" data-section="{section.number}">'
        f"{heading}{body}</section>"
    )


def rulebook(language: str, sections: list[Section]) -> str:
    content = "".join(render_rule_section(language, section) for section in sections)
    return (
        f'<div class="rulebook" {language_panel(language)}>'
        f"{annotate_terms(content, language)}</div>"
    )


def quick_reference(language: str, markdown: str) -> str:
    lines = markdown.splitlines()
    title = re.sub(r"^#\s+", "", lines[0]).strip()
    body = annotate_terms(
        render_markdown("\n".join(lines[1:]), id_prefix=f"quick-{language}-"),
        language,
    )
    return (
        f'<section class="quick-reference" {language_panel(language)} id="quick-{language}">'
        f'<button class="print-button" type="button" data-print="quick">{html.escape(UI[language]["print"])}</button>'
        f"<h2>{html.escape(title)}</h2>{body}</section>"
    )


def build_html() -> str:
    markdowns = {language: read(path) for language, path in SOURCES.items()}
    parsed = {language: split_sections(text) for language, text in markdowns.items()}
    sections = {language: result[1] for language, result in parsed.items()}
    scaling = {
        language: parse_scaling(find_section(language_sections, 12))
        for language, language_sections in sections.items()
    }
    validate(markdowns, sections, scaling)
    validate_interface_data()

    css = read(HERE / "theme.css")
    js = read(HERE / "app.js")
    quick = {language: read(path) for language, path in QUICK_SOURCES.items()}
    glossary_data = {
        language: {
            entry["id"]: {"term": entry["term"], "definition": entry["definition"]}
            for entry in entries
        }
        for language, entries in GLOSSARY.items()
    }
    count_options = "".join(
        f'<option value="{count}"{" selected" if count == 13 else ""}>{count}</option>'
        for count in range(8, 16)
    )
    topbar = f"""
    <header class="topbar">
      <a class="brand-mark" href="#top" aria-label="The Dark Council">
        <span class="brand-sigil" aria-hidden="true">DC</span>
        {i18n("title", tag="span", css="brand-name")}
      </a>
      <div class="top-controls">
        <div class="segmented" aria-label="Language">
          <button type="button" data-set-lang="ua" aria-pressed="true">UA</button>
          <button type="button" data-set-lang="en" aria-pressed="false">EN</button>
        </div>
        <div class="count-control">
          <label for="player-count" data-i18n="choose_count">{html.escape(UI["ua"]["choose_count"])}</label>
          <select id="player-count">{count_options}</select>
        </div>
        <button class="icon-button" id="theme-toggle" type="button"
          data-i18n-label="theme_toggle" title="{html.escape(UI["ua"]["theme_toggle"])}"
          aria-label="{html.escape(UI["ua"]["theme_toggle"])}">◐</button>
      </div>
    </header>"""
    paths = f"""
    <nav class="path-switcher" aria-label="Reading path">
      {i18n("current_path")}
      <div class="path-buttons">
        <button class="path-button" type="button" data-reading-path="player" data-i18n="player">{html.escape(UI["ua"]["player"])}</button>
        <button class="path-button" type="button" data-reading-path="syndicate" data-i18n="syndicate">{html.escape(UI["ua"]["syndicate"])}</button>
        <button class="path-button" type="button" data-reading-path="gm" data-i18n="gm">{html.escape(UI["ua"]["gm"])}</button>
      </div>
    </nav>"""
    setup_summary = f"""
    <section class="setup-summary" aria-live="polite" aria-atomic="true">
      <span class="setup-summary-title" data-i18n="setup_summary">{html.escape(UI["ua"]["setup_summary"])}</span>
      <div class="setup-stat setup-player-count">
        <small data-i18n="player_count">{html.escape(UI["ua"]["player_count"])}</small>
        <strong data-selected-player-count>13</strong>
      </div>
      <div class="setup-stat">
        <small data-i18n="factions">{html.escape(UI["ua"]["factions"])}</small>
        <strong data-threshold="factions">{html.escape(scaling["ua"]["13"]["factions"])}</strong>
      </div>
      <div class="setup-stat">
        <small data-i18n="magnate_count">{html.escape(UI["ua"]["magnate_count"])}</small>
        <strong data-threshold="magnates">{html.escape(scaling["ua"]["13"]["magnates"])}</strong>
      </div>
      <div class="setup-stat">
        <small data-i18n="magnates_need">{html.escape(UI["ua"]["magnates_need"])}</small>
        <strong data-threshold="magnateThreshold">{html.escape(scaling["ua"]["13"]["magnateThreshold"])}</strong>
      </div>
      <div class="setup-stat">
        <small data-i18n="syndicate_needs">{html.escape(UI["ua"]["syndicate_needs"])}</small>
        <strong data-threshold="syndicateThreshold">{html.escape(scaling["ua"]["13"]["syndicateThreshold"])}</strong>
      </div>
    </section>"""
    page = f"""<!doctype html>
<html lang="uk" data-lang="ua" data-theme="dark" data-path="player">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="description" content="The Dark Council — bilingual consumer rules">
  <title>Темна Рада — правила</title>
  <style>{css}</style>
</head>
<body id="top">
  <a class="skip-link" href="#rules" data-i18n="skip">{html.escape(UI["ua"]["skip"])}</a>
  {topbar}
  {hero("ua")}{hero("en")}
  {paths}
  {setup_summary}
  <div class="page-shell">
    {toc("ua", sections["ua"])}{toc("en", sections["en"])}
    <main class="main-column" id="rules">
      {rulebook("ua", sections["ua"])}
      {rulebook("en", sections["en"])}
      {quick_reference("ua", quick["ua"])}
      {quick_reference("en", quick["en"])}
      {experience("ua", sections["ua"], scaling["ua"])}
      {experience("en", sections["en"], scaling["en"])}
    </main>
  </div>
  <footer data-i18n="title">{html.escape(UI["ua"]["title"])}</footer>
  <script id="threshold-data" type="application/json">{json.dumps(scaling["ua"], ensure_ascii=False)}</script>
  <script id="ui-data" type="application/json">{json.dumps(UI, ensure_ascii=False)}</script>
  <script id="glossary-data" type="application/json">{json.dumps(glossary_data, ensure_ascii=False)}</script>
  <div id="term-tip" class="term-tooltip" role="tooltip" hidden></div>
  <script>{js}</script>
</body>
</html>
"""
    page = "\n".join(line.rstrip() for line in page.splitlines()) + "\n"
    if re.search(r"https?://", page, flags=re.IGNORECASE):
        raise ValueError("Generated output contains an external HTTP(S) reference")
    retired_calques = (
        "що входить і виходить",
        "Стежте лише за п'ятьма речами",
        "Пороги цього столу",
        "живий голос",
        "Одна кімната брехні",
        "Режим читання",
    )
    found = [phrase for phrase in retired_calques if phrase in page]
    if found:
        raise ValueError(f"Retired Ukrainian calques found in generated page: {found}")
    return page


def build_artifacts() -> dict[Path, str]:
    manifest = {
        "schemaVersion": 1,
        "defaultLanguage": "uk",
        "languages": {
            "uk": {
                "label": "Українська",
                "rules": "uk.md",
                "playerReference": "player-reference-uk.md",
            },
            "en": {
                "label": "English",
                "rules": "en.md",
                "playerReference": "player-reference-en.md",
            },
        },
    }
    local = {
        OUTPUT: build_html(),
        RULES_OUTPUT / "uk.md": read(SOURCES["ua"]),
        RULES_OUTPUT / "en.md": read(SOURCES["en"]),
        RULES_OUTPUT / "player-reference-uk.md": read(QUICK_SOURCES["ua"]),
        RULES_OUTPUT / "player-reference-en.md": read(QUICK_SOURCES["en"]),
        RULES_OUTPUT / "manifest.json": json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
    }
    hosted = {
        PAGES_OUTPUT: local[OUTPUT],
        PAGES_RULES_OUTPUT / "uk.md": local[RULES_OUTPUT / "uk.md"],
        PAGES_RULES_OUTPUT / "en.md": local[RULES_OUTPUT / "en.md"],
        PAGES_RULES_OUTPUT / "player-reference-uk.md": local[
            RULES_OUTPUT / "player-reference-uk.md"
        ],
        PAGES_RULES_OUTPUT / "player-reference-en.md": local[
            RULES_OUTPUT / "player-reference-en.md"
        ],
        PAGES_RULES_OUTPUT / "manifest.json": local[RULES_OUTPUT / "manifest.json"],
    }
    return local | hosted


def write_or_check(*, check: bool) -> None:
    artifacts = build_artifacts()
    if check:
        stale = [path for path, content in artifacts.items() if not path.exists() or read(path) != content]
        if stale:
            paths = ", ".join(str(path.relative_to(HERE)) for path in stale)
            raise SystemExit(f"Generated output is stale or missing ({paths}); run python build.py")
        print(f"OK: {len(artifacts)} generated artifacts are current and all validation gates passed")
        return
    for path, content in artifacts.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
    print(
        f"Built {OUTPUT} ({OUTPUT.stat().st_size:,} bytes) and "
        f"{len(artifacts) - 2} generated rules/site artifacts, including docs/"
    )


def watch() -> None:
    watched = [*SOURCES.values(), *QUICK_SOURCES.values(), *ASSETS, Path(__file__)]
    modified = {path: path.stat().st_mtime_ns for path in watched}
    write_or_check(check=False)
    print("Watching for changes. Press Ctrl+C to stop.")
    while True:
        time.sleep(0.8)
        changed = False
        for path in watched:
            current = path.stat().st_mtime_ns
            if current != modified[path]:
                modified[path] = current
                changed = True
        if changed:
            try:
                write_or_check(check=False)
            except Exception as error:
                print(f"Build failed: {error}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="validate and check generated output")
    parser.add_argument("--watch", action="store_true", help="rebuild when a source file changes")
    parser.add_argument("--open", action="store_true", help="open the generated page")
    args = parser.parse_args()
    if args.watch:
        watch()
        return
    write_or_check(check=args.check)
    if args.open and not args.check:
        webbrowser.open(OUTPUT.as_uri())


if __name__ == "__main__":
    main()
