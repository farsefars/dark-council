from __future__ import annotations

from pathlib import Path
from collections import Counter
import tempfile
import unittest

from generate_deal import (
    ARISTOCRAT,
    EVIDENCE,
    MAGNATE,
    REFORMER,
    SECRET_INTEL,
    evidence_is_true,
    generate_deal,
    render_combined,
    validate_deal,
    write_deal,
)


class DealGeneratorTests(unittest.TestCase):
    def test_512_seeded_deals_satisfy_all_invariants(self) -> None:
        for n in range(8, 16):
            for seed in range(64):
                deal = generate_deal(n, 100_000 + n * 1_000 + seed)
                self.assertEqual([], validate_deal(deal), f"n={n}, seed={seed}")

    def test_evidence_truth_budget_is_real_not_declared(self) -> None:
        for seed in range(100):
            deal = generate_deal(12, 200_000 + seed)
            starting = [item for item in deal.evidence if not item.auction]
            auction = next(item for item in deal.evidence if item.auction)
            self.assertEqual(
                2,
                sum(evidence_is_true(item, deal.players) for item in starting),
            )
            self.assertTrue(evidence_is_true(auction, deal.players))
            for statement in deal.evidence:
                self.assertEqual(
                    statement.is_true,
                    evidence_is_true(statement, deal.players),
                )

    def test_12_player_setup_matches_published_row(self) -> None:
        deal = generate_deal(12, 20261031)
        factions = Counter(player.faction for player in deal.players)
        self.assertEqual(5, factions[ARISTOCRAT])
        self.assertEqual(5, factions[REFORMER])
        self.assertEqual(2, factions[MAGNATE])
        self.assertEqual(16, deal.magnate_threshold)
        self.assertEqual(40, deal.syndicate_threshold)

    def test_goal_deal_stays_varied_and_achievable(self) -> None:
        for n in range(8, 16):
            deal = generate_deal(n, 300_000 + n)
            motives = Counter(player.motive for player in deal.players)
            ambitions = Counter(player.ambition for player in deal.players)
            self.assertEqual(4, len(motives))
            self.assertEqual(4, len(ambitions))
            self.assertLessEqual(max(motives.values()) - min(motives.values()), 1)
            non_collector = [
                count for goal, count in ambitions.items()
                if goal != "COLLECTOR"
            ]
            self.assertLessEqual(max(non_collector) - min(non_collector), 1)

    def test_advantages_match_private_information(self) -> None:
        deal = generate_deal(12, 20261031)
        for player in deal.players:
            if player.advantage == EVIDENCE:
                self.assertIsNotNone(player.evidence_index)
                self.assertIsNone(player.intel_target)
            elif player.advantage == SECRET_INTEL:
                self.assertIsNone(player.evidence_index)
                self.assertIsNotNone(player.intel_target)
                self.assertNotEqual(player.seat, player.intel_target)

    def test_custom_names_and_bilingual_rendering(self) -> None:
        names = [f"Guest {index}" for index in range(1, 13)]
        deal = generate_deal(12, 20261031, names)
        en = render_combined(deal, "en")
        ua = render_combined(deal, "ua")
        self.assertIn("Guest 1", en)
        self.assertIn("Guest 12", ua)
        self.assertIn("GM ONLY", en)
        self.assertIn("ЛИШЕ ДЛЯ ВЕДУЧОГО", ua)
        self.assertIn("Extortionist", en)
        self.assertIn("Вимагач", ua)
        self.assertIn("Prepared Hit Set", en)
        self.assertIn("Підготовлений набір Замовлень", ua)

    def test_writes_combined_master_and_individual_cards(self) -> None:
        deal = generate_deal(12, 20261031)
        with tempfile.TemporaryDirectory() as directory:
            written = write_deal(deal, Path(directory))
            self.assertEqual(28, len(written))
            self.assertTrue(Path(directory, "deal-12p-ua.md").exists())
            self.assertTrue(Path(directory, "deal-12p-en.md").exists())
            self.assertTrue(
                Path(directory, "deal-12p-private", "gm-master-ua.md").exists()
            )
            self.assertTrue(
                Path(
                    directory,
                    "deal-12p-private",
                    "player-12-en.md",
                ).exists()
            )

    def test_bad_name_count_fails(self) -> None:
        with self.assertRaisesRegex(ValueError, "expected 12 names"):
            generate_deal(12, 1, ["Only one"])


if __name__ == "__main__":
    unittest.main()
