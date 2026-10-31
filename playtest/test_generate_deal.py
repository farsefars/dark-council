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
    render_discord_dm_ua,
    render_discord_pack_ua,
    validate_deal,
    write_deal,
    write_discord_ua,
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

    def test_11_player_experience_balance(self) -> None:
        names = [
            "Vladka", "Marta", "Pavlushka", "Taya", "Violetta", "Vlada",
            "Anton", "Max", "Stefa", "Sofiyka", "Darynka",
        ]
        experienced = [
            True, False, True, True, True, True,
            False, True, False, True, True,
        ]
        for seed in range(64):
            deal = generate_deal(11, 500_000 + seed, names, experienced)
            syndicate = [
                player for player in deal.players
                if player.role != "INNOCENT"
            ]
            self.assertTrue(all(player.experienced for player in syndicate))
            for faction in (ARISTOCRAT, REFORMER, MAGNATE):
                innocent_team = [
                    player for player in deal.players
                    if player.faction == faction and player.role == "INNOCENT"
                ]
                self.assertEqual(
                    Counter({True: 2, False: 1}),
                    Counter(player.experienced for player in innocent_team),
                )
            new_players = [
                player for player in deal.players if player.experienced is False
            ]
            self.assertTrue(all(player.motive != "ESPIONAGE" for player in new_players))
            self.assertTrue(all(player.ambition != "DIPLOMAT" for player in new_players))
            self.assertEqual(3, len({player.motive for player in new_players}))
            self.assertEqual(3, len({player.ambition for player in new_players}))
            evidence_factions = Counter(
                deal.players[item.owner].faction
                for item in deal.evidence
                if not item.auction and item.owner is not None
            )
            self.assertEqual(
                {ARISTOCRAT, REFORMER, MAGNATE},
                set(evidence_factions),
            )
            self.assertLessEqual(max(evidence_factions.values()), 2)
            evidence_owners = [
                item.owner for item in deal.evidence
                if not item.auction and item.owner is not None
            ]
            self.assertLessEqual(
                sum(
                    deal.players[seat].role != "INNOCENT"
                    for seat in evidence_owners
                ),
                1,
            )
            self.assertTrue(any(
                item.is_true
                and item.owner is not None
                and deal.players[item.owner].role == "INNOCENT"
                for item in deal.evidence
                if not item.auction
            ))

    def test_discord_output_is_copyable_and_under_message_limit(self) -> None:
        names = [
            "Vladka", "Marta", "Pavlushka", "Taya", "Violetta", "Vlada",
            "Anton", "Max", "Stefa", "Sofiyka", "Darynka",
        ]
        experienced = [
            True, False, True, True, True, True,
            False, True, False, True, True,
        ]
        deal = generate_deal(11, 20261031, names, experienced)
        pack = render_discord_pack_ua(deal)
        self.assertIn("# Публічне повідомлення", pack)
        self.assertEqual(12, pack.count("```md"))
        for player in deal.players:
            message = render_discord_dm_ua(deal, player)
            self.assertIn(deal.name(player.seat, "ua"), message)
            self.assertIn("**Фракція:**", message)
            self.assertIn("**Роль:**", message)
            self.assertLessEqual(len(message), 2_000)
        with tempfile.TemporaryDirectory() as directory:
            written = write_discord_ua(deal, Path(directory))
            self.assertEqual(13, len(written))
            self.assertTrue(Path(directory, "deal-11p-discord-ua.md").exists())
            self.assertTrue(
                Path(
                    directory,
                    "deal-11p-private",
                    "discord-01-Vladka-ua.txt",
                ).exists()
            )


if __name__ == "__main__":
    unittest.main()
