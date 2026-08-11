from __future__ import annotations

from collections import Counter
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import unittest

import build
from md import find_section, split_sections


class HtmlAudit(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.ids: list[str] = []
        self.scripts: list[list[str]] = []
        self.current_script: list[str] | None = None

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = dict(attrs)
        if values.get("id"):
            self.ids.append(values["id"] or "")
        if tag == "script":
            self.current_script = [values.get("type") or "script", ""]
            self.scripts.append(self.current_script)

    def handle_endtag(self, tag: str) -> None:
        if tag == "script":
            self.current_script = None

    def handle_data(self, data: str) -> None:
        if self.current_script is not None:
            self.current_script[1] += data


class BuildTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.markdowns = {language: build.read(path) for language, path in build.SOURCES.items()}
        cls.sections = {
            language: split_sections(text)[1] for language, text in cls.markdowns.items()
        }
        cls.scaling = {
            language: build.parse_scaling(find_section(sections, 12))
            for language, sections in cls.sections.items()
        }
        cls.page = build.build_html()
        cls.audit = HtmlAudit()
        cls.audit.feed(cls.page)

    def test_rule_validation_passes(self) -> None:
        build.validate(self.markdowns, self.sections, self.scaling)
        build.validate_interface_data()

    def test_numeric_drift_fails(self) -> None:
        changed = dict(self.markdowns)
        changed["ua"] = changed["ua"].replace("+2 Впливу", "+7 Впливу")
        sections = dict(self.sections)
        sections["ua"] = split_sections(changed["ua"])[1]
        with self.assertRaisesRegex(ValueError, "expected rule pattern"):
            build.validate(changed, sections, self.scaling)

    def test_player_count_drift_fails(self) -> None:
        changed = json.loads(json.dumps(self.scaling))
        changed["en"]["13"]["magnateThreshold"] = "999"
        with self.assertRaisesRegex(ValueError, "scaling tables differ"):
            build.validate(self.markdowns, self.sections, changed)

    def test_output_has_unique_ids(self) -> None:
        duplicates = [ident for ident, count in Counter(self.audit.ids).items() if count > 1]
        self.assertEqual([], duplicates)

    def test_public_sections_are_readable_and_collapsible(self) -> None:
        self.assertIn("Відмивання", self.page)
        self.assertIn("Promotion", self.page)
        self.assertNotIn("application/octet-stream", self.page)
        self.assertNotIn("sealed-section", self.page)
        self.assertEqual(4, self.page.count('class="section-collapse rule-section"'))
        self.assertEqual(2, self.page.count('data-section-link="11"'))
        self.assertEqual(2, self.page.count('data-section-link="12"'))

    def test_threshold_json_covers_all_setups(self) -> None:
        payload = next(
            body
            for kind, body in self.audit.scripts
            if kind == "application/json" and '"magnateThreshold"' in body
        )
        data = json.loads(payload)
        self.assertEqual({str(value) for value in range(8, 16)}, set(data))

    def test_visual_components_are_bilingual(self) -> None:
        self.assertEqual(16, self.page.count('class="goal-card '))
        self.assertEqual(20, self.page.count('class="economy-entry '))
        self.assertEqual(22, self.page.count('<section class="rule-section"'))
        self.assertEqual(4, self.page.count('class="section-collapse rule-section"'))
        self.assertEqual(2, self.page.count('class="game-arc"'))

    def test_page_is_offline(self) -> None:
        lowered = self.page.lower()
        self.assertNotIn("http://", lowered)
        self.assertNotIn("https://", lowered)

    def test_rules_backend_manifest_and_files(self) -> None:
        artifacts = build.build_artifacts()
        manifest_path = build.RULES_OUTPUT / "manifest.json"
        self.assertIn(manifest_path, artifacts)
        manifest = json.loads(artifacts[manifest_path])
        self.assertEqual("uk", manifest["defaultLanguage"])
        for language in ("uk", "en"):
            entry = manifest["languages"][language]
            self.assertIn(build.RULES_OUTPUT / entry["rules"], artifacts)
            self.assertIn(build.RULES_OUTPUT / entry["playerReference"], artifacts)
            self.assertIn(build.PAGES_RULES_OUTPUT / entry["rules"], artifacts)
            self.assertIn(build.PAGES_RULES_OUTPUT / entry["playerReference"], artifacts)
        self.assertEqual(artifacts[build.OUTPUT], artifacts[build.PAGES_OUTPUT])

    def test_comprehension_answers_are_in_player_path(self) -> None:
        player = "\n".join(
            section.body for section in self.sections["ua"] if section.number <= 10
        )
        expected = [
            r"лише під час Приватної фази",
            r"негайно погашає борг",
            r"найбільший негайний штраф",
            r"для спроби Викриття потрібно мати щонайменше 2 Впливу",
            r"для участі в голосуванні на Допиті потрібно мати щонайменше 1 Впливу",
            r"перед висуванням Кандидатів",
            r"стає \*\*Банкрутом\*\* на весь",
            r"особисто не отримує Перемогу Фракції",
            r"Ви втрачаєте 2 Впливу",
            r"отримує \+3 Впливу",
            r"втрачає \*\*1 Вплив\*\*",
            r"рівно \*\*п'ять\*\*",
            r"Рівно \*\*два з п'яти є хибними\*\*",
            r"має один голос у кожному Допиті та на Фінальних Виборах",
            r"не може мати, отримувати, витрачати або передавати Вплив",
        ]
        for pattern in expected:
            self.assertRegex(player, re.compile(pattern, re.IGNORECASE))
        final = find_section(self.sections["ua"], 9).body
        self.assertLess(final.index("### 9.1 Кандидати"), final.index("### 9.2 Розкриття"))
        wins = find_section(self.sections["ua"], 10).body
        for faction in ("Аристократи", "Реформісти", "Магнати", "Синдикат"):
            self.assertIn(faction, wins)

    def test_eligibility_wording_is_deterministic(self) -> None:
        ua = self.markdowns["ua"]
        en = self.markdowns["en"]
        self.assertNotIn("можуть позбавити", ua)
        self.assertNotIn("can make a player personally ineligible", en)
        self.assertIn("позбавляють\nгравця особистого права", ua)
        self.assertIn("make a player\npersonally ineligible", en)
        self.assertIn("Наслідок, описаний без слова «може», застосовується завжди", ua)
        self.assertIn('A consequence stated without "may" always applies', en)
        self.assertIn("Живий гравець із меншим балансом не подає голосу", ua)
        self.assertIn("A living player with less does not cast a vote", en)

    def test_contract_tooltip_matches_public_rule(self) -> None:
        ua_contract = next(
            entry["definition"] for entry in build.GLOSSARY["ua"] if entry["id"] == "contract"
        )
        self.assertIn("замовлення на вбивство для Синдикату", ua_contract)
        self.assertIn("ніколи не вказує на конкретного гравця", ua_contract)

    def test_responsive_print_and_motion_modes_exist(self) -> None:
        css = (Path(build.HERE) / "theme.css").read_text(encoding="utf-8")
        self.assertIn("@media print", css)
        self.assertIn("@media (min-width: 42rem)", css)
        self.assertIn("@media (min-width: 55rem)", css)
        self.assertIn("@media (prefers-reduced-motion: reduce)", css)
        self.assertIn(':root[data-print="quick"]', css)
        self.assertIn("[hidden][hidden]", css)
        self.assertNotIn(".lang-panel {", css)

    def test_balance_status_is_not_published(self) -> None:
        self.assertNotIn("Balance status", self.markdowns["en"])
        self.assertNotIn("Стан балансу", self.markdowns["ua"])
        self.assertNotIn("Balance status", self.page)
        self.assertNotIn("Стан балансу", self.page)

    def test_player_count_summary_is_rendered(self) -> None:
        self.assertIn('class="setup-summary"', self.page)
        self.assertEqual(1, self.page.count("<strong data-selected-player-count>"))
        self.assertGreaterEqual(self.page.count('data-threshold="factions"'), 3)
        self.assertIn('<option value="13" selected>', self.page)

    def test_language_panels_ship_isolated(self) -> None:
        self.assertEqual(5, len(re.findall(r'data-lang-panel data-lang="ua"(?! hidden)', self.page)))
        self.assertEqual(5, self.page.count('data-lang-panel data-lang="en" hidden'))
        self.assertNotIn('class="lang-panel', self.page)

    def test_ui_chrome_uses_single_node_i18n(self) -> None:
        self.assertEqual(2, self.page.count('data-i18n="title"'))
        for key in ("choose_count", "current_path", "player", "syndicate", "gm", "skip"):
            self.assertEqual(1, self.page.count(f'data-i18n="{key}"'))

    def test_every_fragment_target_exists(self) -> None:
        targets = set(re.findall(r'\sid="([^"]+)"', self.page))
        fragments = re.findall(r'href="#([^"]+)"', self.page)
        self.assertTrue(fragments)
        self.assertEqual([], sorted({fragment for fragment in fragments if fragment not in targets}))

    def test_rules_lead_and_diagrams_are_last(self) -> None:
        for language in ("ua", "en"):
            section_zero = self.page.index(f'id="{language}-section-0"')
            quick = self.page.index(f'id="quick-{language}"')
            diagrams = self.page.index(f'id="diagrams-{language}"')
            self.assertLess(section_zero, quick)
            self.assertLess(quick, diagrams)

    def test_retired_ukrainian_calques_are_absent(self) -> None:
        for phrase in (
            "що входить і виходить",
            "Стежте лише за п'ятьма речами",
            "Пороги цього столу",
            "живий голос",
            "Одна кімната брехні",
            "Режим читання",
        ):
            self.assertNotIn(phrase, self.page)

    def test_every_glossary_id_is_annotated(self) -> None:
        for entry in build.GLOSSARY["ua"]:
            self.assertGreaterEqual(self.page.count(f'data-term="{entry["id"]}"'), 2)
        self.assertGreater(self.page.count('class="term-ref"'), 150)

    def test_term_buttons_do_not_annotate_headings_or_summaries(self) -> None:
        for tag in ("h1", "h2", "h3", "h4", "h5", "h6", "summary"):
            blocks = re.findall(fr"<{tag}\b[^>]*>(.*?)</{tag}>", self.page, re.DOTALL)
            self.assertTrue(all('class="term-ref"' not in block for block in blocks))

    def test_shared_tooltip_data_matches_annotations(self) -> None:
        glossary_payload = next(
            body
            for kind, body in self.audit.scripts
            if kind == "application/json" and '"definition"' in body
        )
        glossary = json.loads(glossary_payload)
        annotated = set(re.findall(r'data-term="([^"]+)"', self.page))
        self.assertEqual(set(glossary["ua"]), set(glossary["en"]))
        self.assertEqual(set(glossary["ua"]), annotated)
        self.assertEqual(1, self.page.count('id="term-tip"'))

    def test_ukrainian_inflections_are_annotated_safely(self) -> None:
        sample = (
            "<p>Впливу в Криївці, Розкритті та Викритті.</p>"
            "<h2>Вплив</h2><a href=\"#\">Допит</a><code>Синдикат</code>"
        )
        annotated = build.annotate_terms(sample, "ua")
        self.assertEqual(4, annotated.count('class="term-ref"'))
        self.assertIn("<h2>Вплив</h2>", annotated)
        self.assertIn('<a href="#">Допит</a>', annotated)
        self.assertIn("<code>Синдикат</code>", annotated)


if __name__ == "__main__":
    unittest.main()
