"""Generate verified bilingual Dark Council setup packs for 8-15 players."""

from __future__ import annotations

import argparse
import csv
import random
import secrets
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

ARISTOCRAT = "ARISTOCRAT"
REFORMER = "REFORMER"
MAGNATE = "MAGNATE"
INNOCENT = "INNOCENT"
ASSASSIN = "ASSASSIN"
ACCOMPLICE = "ACCOMPLICE"

EVIDENCE = "EVIDENCE"
SECRET_INTEL = "SECRET_INTEL"

MOTIVES = ("VANITY", "WRATH", "ESPIONAGE", "COMMERCE")
AMBITIONS = ("COLLECTOR", "RADICAL", "BLACKMAILER", "DIPLOMAT")
SECRETS = ("BLACKMAIL", "TREASON", "CORRUPTION", "HERESY")
ADVANTAGES = (EVIDENCE, SECRET_INTEL)
EVIDENCE_KINDS = (
    "MOTIVE",
    "AMBITION",
    "SECRET",
    "ASSASSIN_FACTION",
    "ADVANTAGE",
)

# players -> Aristocrats, Reformers, Magnates, Magnate threshold, Syndicate threshold
SCALING = {
    8: (3, 3, 2, 16, 46),
    9: (3, 3, 3, 24, 44),
    10: (4, 4, 2, 16, 42),
    11: (4, 4, 3, 24, 42),
    12: (5, 5, 2, 16, 40),
    13: (5, 5, 3, 24, 40),
    14: (6, 6, 2, 16, 41),
    15: (6, 6, 3, 24, 39),
}

LABELS = {
    "en": {
        ARISTOCRAT: "Aristocrat",
        REFORMER: "Reformer",
        MAGNATE: "Magnate",
        INNOCENT: "Innocent",
        ASSASSIN: "Assassin",
        ACCOMPLICE: "Accomplice",
        EVIDENCE: "Evidence",
        SECRET_INTEL: "Secret Intelligence",
        "VANITY": "Vanity",
        "WRATH": "Wrath",
        "ESPIONAGE": "Espionage",
        "COMMERCE": "Commerce",
        "COLLECTOR": "Collector",
        "RADICAL": "Radical",
        "BLACKMAILER": "Extortionist",
        "DIPLOMAT": "Diplomat",
        "BLACKMAIL": "Blackmail",
        "TREASON": "Treason",
        "CORRUPTION": "Corruption",
        "HERESY": "Heresy",
    },
    "ua": {
        ARISTOCRAT: "Аристократ",
        REFORMER: "Реформіст",
        MAGNATE: "Магнат",
        INNOCENT: "Невинний",
        ASSASSIN: "Вбивця",
        ACCOMPLICE: "Спільник",
        EVIDENCE: "Доказ",
        SECRET_INTEL: "Компромат",
        "VANITY": "Марнославство",
        "WRATH": "Гнів",
        "ESPIONAGE": "Шпигунство",
        "COMMERCE": "Торгівля",
        "COLLECTOR": "Колекціонер",
        "RADICAL": "Радикал",
        "BLACKMAILER": "Вимагач",
        "DIPLOMAT": "Дипломат",
        "BLACKMAIL": "Шантаж",
        "TREASON": "Зрада",
        "CORRUPTION": "Корупція",
        "HERESY": "Єресь",
    },
}

GOAL_TEXT = {
    "en": {
        "VANITY": "Finish Round 1 or Round 2 on the Leaderboard.",
        "WRATH": "Initiate an Interrogation, regardless of its result.",
        "ESPIONAGE": (
            "Privately name to the GM both the Motive and Ambition of one other "
            "player, correctly."
        ),
        "COMMERCE": (
            "Earn at least 3 Influence in net profit from voluntary deals with at "
            "least two different players during Private Phases. You must also pay "
            "at least 1 Influence in those deals. Rule payments do not count."
        ),
        "COLLECTOR": "Win the Auction.",
        "RADICAL": (
            "Vote Guilty on two different players who are then Executed."
        ),
        "BLACKMAILER": (
            "Receive at least 2 Influence from each of two different players "
            "over the course of the game."
        ),
        "DIPLOMAT": (
            "Form a truthful Public Pact with one player from each of the other "
            "two Factions before the GM."
        ),
    },
    "ua": {
        "VANITY": (
            "Потрапити до Таблиці лідерів наприкінці Раунду 1 або Раунду 2."
        ),
        "WRATH": "Ініціювати Допит незалежно від його результату.",
        "ESPIONAGE": (
            "Приватно й безпомилково назвати Ведучому і Мотив, і Амбіцію одного "
            "іншого гравця."
        ),
        "COMMERCE": (
            "Отримати щонайменше 3 Впливу чистого прибутку від добровільних угод "
            "принаймні з двома різними гравцями під час Приватних фаз, сплативши "
            "в цих угодах хоча б 1 Вплив. Ігрові виплати та штрафи не враховуються."
        ),
        "COLLECTOR": "Виграти Аукціон.",
        "RADICAL": (
            "Проголосувати «Винен» проти двох різних гравців, яких згодом Страчено."
        ),
        "BLACKMAILER": (
            "Отримати щонайменше 2 Впливу від кожного з двох різних гравців "
            "протягом гри."
        ),
        "DIPLOMAT": (
            "Укласти перед Ведучим правдивий Публічний Пакт з одним гравцем "
            "із кожної з двох інших Фракцій."
        ),
    },
}

HITS = {
    "OLD_GUARD": {
        "en": "Break the Old Guard — an Aristocrat",
        "ua": "Зламати стару гвардію — Аристократ",
    },
    "NEW_ORDER": {
        "en": "Break the New Order — a Reformer",
        "ua": "Зламати новий порядок — Реформіст",
    },
    "PURSE_STRINGS": {
        "en": "Cut the Purse Strings — a Magnate",
        "ua": "Перекрити потік — Магнат",
    },
}


@dataclass
class Player:
    seat: int
    faction: str
    role: str
    motive: str
    ambition: str
    secret: str
    outsider: int
    advantage: str
    experienced: bool | None = None
    evidence_index: int | None = None
    intel_target: int | None = None


@dataclass
class EvidenceStatement:
    kind: str
    value: str
    is_true: bool
    owner: int | None = None
    auction: bool = False


@dataclass
class Deal:
    seed: int
    names: list[str] | None
    players: list[Player]
    evidence: list[EvidenceStatement]
    hits: list[str]
    magnate_threshold: int
    syndicate_threshold: int

    @property
    def n(self) -> int:
        return len(self.players)

    @property
    def assassin(self) -> Player:
        return next(player for player in self.players if player.role == ASSASSIN)

    @property
    def accomplice(self) -> Player:
        return next(player for player in self.players if player.role == ACCOMPLICE)

    def name(self, seat: int, language: str) -> str:
        if self.names:
            return self.names[seat]
        prefix = "Player" if language == "en" else "Гравець"
        return f"{prefix} {seat + 1}"

    def secret_subject(self, seat: int, language: str) -> str:
        if self.names:
            return self.names[seat]
        if language == "ua":
            return f"гравця {seat + 1}"
        return f"Player {seat + 1}"


def _deal_goals(
    rng: random.Random,
    options: tuple[str, ...],
    n: int,
    caps: dict[str, int],
) -> list[str]:
    result = list(options)
    counts = Counter(result)
    while len(result) < n:
        available = [
            option
            for option in options
            if counts[option] < caps.get(option, n)
        ]
        least_dealt = min(counts[option] for option in available)
        choice = rng.choice(
            [option for option in available if counts[option] == least_dealt]
        )
        result.append(choice)
        counts[choice] += 1
    rng.shuffle(result)
    return result[:n]


def _move_hard_goals_off_new_players(
    rng: random.Random,
    goals: list[str],
    experienced: list[bool] | None,
    hard_goal: str,
) -> None:
    """Give first-time players a lower-overhead private objective when possible."""
    if experienced is None:
        return
    new_seats = [
        seat for seat, is_experienced in enumerate(experienced)
        if not is_experienced and goals[seat] == hard_goal
    ]
    experienced_seats = [
        seat for seat, is_experienced in enumerate(experienced)
        if is_experienced and goals[seat] != hard_goal
    ]
    rng.shuffle(experienced_seats)
    for new_seat, experienced_seat in zip(new_seats, experienced_seats):
        goals[new_seat], goals[experienced_seat] = (
            goals[experienced_seat],
            goals[new_seat],
        )


def _diversify_new_player_goals(
    rng: random.Random,
    goals: list[str],
    experienced: list[bool] | None,
    allowed: tuple[str, ...],
) -> None:
    """Spread accessible objectives across new players as evenly as possible."""
    if experienced is None:
        return
    new_seats = [seat for seat, value in enumerate(experienced) if not value]
    novice_counts = Counter(goals[seat] for seat in new_seats)
    missing = [goal for goal in allowed if novice_counts[goal] == 0]
    rng.shuffle(missing)
    for goal in missing:
        duplicate_seat = next(
            (
                seat for seat in new_seats
                if novice_counts[goals[seat]] > 1
            ),
            None,
        )
        donor_seat = next(
            (
                seat for seat, value in enumerate(experienced)
                if value and goals[seat] == goal
            ),
            None,
        )
        if duplicate_seat is None or donor_seat is None:
            continue
        old_goal = goals[duplicate_seat]
        goals[duplicate_seat], goals[donor_seat] = (
            goals[donor_seat],
            goals[duplicate_seat],
        )
        novice_counts[old_goal] -= 1
        novice_counts[goal] += 1


def _deal_factions_and_roles(
    rng: random.Random,
    n: int,
    aristocrats: int,
    reformers: int,
    magnates: int,
    experienced: list[bool] | None,
) -> tuple[list[str], list[str]]:
    if experienced is None:
        factions = (
            [ARISTOCRAT] * aristocrats
            + [REFORMER] * reformers
            + [MAGNATE] * magnates
        )
        rng.shuffle(factions)
        roles = [INNOCENT] * n
        aristocrat_seat = rng.choice([
            seat for seat, faction in enumerate(factions)
            if faction == ARISTOCRAT
        ])
        reformer_seat = rng.choice([
            seat for seat, faction in enumerate(factions)
            if faction == REFORMER
        ])
    else:
        experience_counts = Counter(experienced)
        supported = {
            11: Counter({True: 8, False: 3}),
            12: Counter({True: 8, False: 4}),
        }
        if n not in supported or experience_counts != supported[n]:
            raise ValueError(
                "experience-balanced dealing currently requires exactly "
                "11 players (8 experienced / 3 new) or "
                "12 players (8 experienced / 4 new)"
            )
        new_seats = [seat for seat, value in enumerate(experienced) if not value]
        experienced_seats = [seat for seat, value in enumerate(experienced) if value]
        rng.shuffle(new_seats)
        rng.shuffle(experienced_seats)

        factions = [""] * n
        if n == 11:
            novice_factions = [ARISTOCRAT, REFORMER, MAGNATE]
        else:
            novice_factions = [ARISTOCRAT, ARISTOCRAT, REFORMER, REFORMER]
        rng.shuffle(novice_factions)
        for seat, faction in zip(new_seats, novice_factions):
            factions[seat] = faction

        novice_counts = Counter(novice_factions)
        remaining = {
            ARISTOCRAT: aristocrats - novice_counts[ARISTOCRAT],
            REFORMER: reformers - novice_counts[REFORMER],
            MAGNATE: magnates - novice_counts[MAGNATE],
        }
        experienced_factions = [
            faction
            for faction, count in remaining.items()
            for _ in range(count)
        ]
        rng.shuffle(experienced_factions)
        for seat, faction in zip(experienced_seats, experienced_factions):
            factions[seat] = faction

        aristocrat_seat = rng.choice([
            seat for seat in experienced_seats
            if factions[seat] == ARISTOCRAT
        ])
        reformer_seat = rng.choice([
            seat for seat in experienced_seats
            if factions[seat] == REFORMER
        ])

        roles = [INNOCENT] * n

    syndicate_seats = [aristocrat_seat, reformer_seat]
    rng.shuffle(syndicate_seats)
    roles[syndicate_seats[0]] = ASSASSIN
    roles[syndicate_seats[1]] = ACCOMPLICE
    return factions, roles


def _choose_evidence_holders(
    rng: random.Random,
    factions: list[str],
    roles: list[str],
    experienced: list[bool] | None,
) -> list[int]:
    """Spread Evidence across all Factions; prefer experienced readers."""
    holders = []
    for faction in (ARISTOCRAT, REFORMER, MAGNATE):
        pool = [
            seat for seat, player_faction in enumerate(factions)
            if player_faction == faction
            and roles[seat] == INNOCENT
            and (experienced is None or experienced[seat])
        ]
        if not pool:
            pool = [
                seat for seat, player_faction in enumerate(factions)
                if player_faction == faction and roles[seat] == INNOCENT
            ]
        if not pool:
            pool = [
                seat for seat, player_faction in enumerate(factions)
                if player_faction == faction
            ]
        holders.append(rng.choice(pool))

    fourth_pool = [
        seat for seat in range(len(factions))
        if seat not in holders and (experienced is None or experienced[seat])
    ]
    if not fourth_pool:
        fourth_pool = [seat for seat in range(len(factions)) if seat not in holders]
    holders.append(rng.choice(fourth_pool))
    return holders


def _false_options(kind: str, actual: set[str]) -> list[str]:
    domain = {
        "MOTIVE": MOTIVES,
        "AMBITION": AMBITIONS,
        "SECRET": SECRETS,
        "ASSASSIN_FACTION": (ARISTOCRAT, REFORMER),
        "ADVANTAGE": ADVANTAGES,
    }[kind]
    return [value for value in domain if value not in actual]


def _evidence_actuals(players: list[Player]) -> dict[str, set[str]]:
    assassin = next(player for player in players if player.role == ASSASSIN)
    accomplice = next(player for player in players if player.role == ACCOMPLICE)
    return {
        "MOTIVE": {assassin.motive, accomplice.motive},
        "AMBITION": {assassin.ambition, accomplice.ambition},
        "SECRET": {assassin.secret, accomplice.secret},
        "ASSASSIN_FACTION": {assassin.faction},
        "ADVANTAGE": {assassin.advantage, accomplice.advantage},
    }


def evidence_is_true(statement: EvidenceStatement, players: list[Player]) -> bool:
    return statement.value in _evidence_actuals(players)[statement.kind]


def _build_evidence(
    rng: random.Random,
    players: list[Player],
    holders: list[int],
) -> list[EvidenceStatement]:
    actuals = _evidence_actuals(players)
    unfalsifiable = [
        kind for kind in EVIDENCE_KINDS
        if not _false_options(kind, actuals[kind])
    ]
    auction_kind = (
        rng.choice(unfalsifiable)
        if unfalsifiable
        else rng.choice(list(EVIDENCE_KINDS))
    )
    remaining = [kind for kind in EVIDENCE_KINDS if kind != auction_kind]
    falsifiable = [
        kind for kind in remaining
        if _false_options(kind, actuals[kind])
    ]
    false_kinds = set(rng.sample(falsifiable, 2))

    statements = []
    for kind in remaining:
        if kind in false_kinds:
            value = rng.choice(_false_options(kind, actuals[kind]))
            statement = EvidenceStatement(kind, value, False)
        else:
            value = rng.choice(sorted(actuals[kind]))
            statement = EvidenceStatement(kind, value, True)
        statements.append(statement)
    rng.shuffle(statements)
    rng.shuffle(holders)
    for index, (statement, owner) in enumerate(zip(statements, holders)):
        statement.owner = owner
        players[owner].evidence_index = index

    auction = EvidenceStatement(
        auction_kind,
        rng.choice(sorted(actuals[auction_kind])),
        True,
        auction=True,
    )
    return statements + [auction]


def generate_deal(
    n: int,
    seed: int,
    names: list[str] | None = None,
    experienced: list[bool] | None = None,
) -> Deal:
    if n not in SCALING:
        raise ValueError("player count must be between 8 and 15")
    if names is not None and len(names) != n:
        raise ValueError(f"expected {n} names, received {len(names)}")
    if experienced is not None and len(experienced) != n:
        raise ValueError(f"expected {n} experience flags, received {len(experienced)}")
    rng = random.Random(seed)
    aristocrats, reformers, magnates, magnate_threshold, syndicate_threshold = (
        SCALING[n]
    )
    factions, roles = _deal_factions_and_roles(
        rng,
        n,
        aristocrats,
        reformers,
        magnates,
        experienced,
    )
    motives = _deal_goals(rng, MOTIVES, n, {"VANITY": 3})
    ambitions = _deal_goals(rng, AMBITIONS, n, {"COLLECTOR": 1})
    _move_hard_goals_off_new_players(rng, motives, experienced, "ESPIONAGE")
    _move_hard_goals_off_new_players(rng, ambitions, experienced, "DIPLOMAT")
    _diversify_new_player_goals(
        rng,
        motives,
        experienced,
        ("VANITY", "WRATH", "COMMERCE"),
    )
    _diversify_new_player_goals(
        rng,
        ambitions,
        experienced,
        ("COLLECTOR", "RADICAL", "BLACKMAILER"),
    )
    secrets_dealt = [rng.choice(SECRETS) for _ in range(n)]
    evidence_holders = _choose_evidence_holders(
        rng,
        factions,
        roles,
        experienced,
    )
    players = []
    for seat in range(n):
        outsider = rng.choice(
            [
                other
                for other in range(n)
                if factions[other] != factions[seat]
            ]
        )
        players.append(
            Player(
                seat=seat,
                faction=factions[seat],
                role=roles[seat],
                motive=motives[seat],
                ambition=ambitions[seat],
                secret=secrets_dealt[seat],
                outsider=outsider,
                advantage=(
                    EVIDENCE if seat in evidence_holders else SECRET_INTEL
                ),
                experienced=(
                    experienced[seat] if experienced is not None else None
                ),
            )
        )

    evidence = _build_evidence(rng, players, evidence_holders)
    for player in players:
        if player.advantage == SECRET_INTEL:
            player.intel_target = rng.choice(
                [seat for seat in range(n) if seat != player.seat]
            )

    deal = Deal(
        seed=seed,
        names=names,
        players=players,
        evidence=evidence,
        hits=["OLD_GUARD", "NEW_ORDER", "PURSE_STRINGS"],
        magnate_threshold=magnate_threshold,
        syndicate_threshold=syndicate_threshold,
    )
    errors = validate_deal(deal)
    if errors:
        raise AssertionError("; ".join(errors))
    return deal


def validate_deal(deal: Deal) -> list[str]:
    errors = []
    expected_a, expected_r, expected_m, expected_mag, expected_syn = SCALING[deal.n]
    faction_counts = Counter(player.faction for player in deal.players)
    if sorted((faction_counts[ARISTOCRAT], faction_counts[REFORMER])) != sorted(
        (expected_a, expected_r)
    ):
        errors.append("major-Faction counts are wrong")
    if faction_counts[MAGNATE] != expected_m:
        errors.append("Magnate count is wrong")
    if deal.magnate_threshold != expected_mag:
        errors.append("Magnate threshold is wrong")
    if deal.syndicate_threshold != expected_syn:
        errors.append("Syndicate threshold is wrong")

    syndicate = [
        player for player in deal.players
        if player.role in (ASSASSIN, ACCOMPLICE)
    ]
    if len(syndicate) != 2:
        errors.append("Syndicate must contain exactly two players")
    elif {player.faction for player in syndicate} != {ARISTOCRAT, REFORMER}:
        errors.append("Syndicate must be one Aristocrat and one Reformer")
    if any(player.faction == MAGNATE for player in syndicate):
        errors.append("Magnate cannot be in the Syndicate")
    if any(player.experienced is False for player in syndicate):
        errors.append("new players cannot receive Syndicate roles")

    if any(player.experienced is not None for player in deal.players):
        expected_experience = (
            {
                ARISTOCRAT: Counter({True: 2, False: 1}),
                REFORMER: Counter({True: 2, False: 1}),
                MAGNATE: Counter({True: 2, False: 1}),
            }
            if deal.n == 11
            else {
                ARISTOCRAT: Counter({True: 2, False: 2}),
                REFORMER: Counter({True: 2, False: 2}),
                MAGNATE: Counter({True: 2}),
            }
        )
        for faction, expected in expected_experience.items():
            innocent_team = [
                player for player in deal.players
                if player.faction == faction and player.role == INNOCENT
            ]
            experience = Counter(player.experienced for player in innocent_team)
            if experience != expected:
                errors.append(
                    f"{faction} Innocent experience split is {experience}; "
                    f"expected {expected}"
                )

    if sum(player.ambition == "COLLECTOR" for player in deal.players) > 1:
        errors.append("Collector cap exceeded")
    if sum(player.motive == "VANITY" for player in deal.players) > 3:
        errors.append("Vanity cap exceeded")

    for player in deal.players:
        if deal.players[player.outsider].faction == player.faction:
            errors.append(f"seat {player.seat + 1} has an invalid outsider clue")
        if player.advantage == SECRET_INTEL:
            if player.intel_target is None or player.intel_target == player.seat:
                errors.append(f"seat {player.seat + 1} has invalid Secret Intelligence")
        elif player.evidence_index is None:
            errors.append(f"seat {player.seat + 1} is missing Evidence")

    starting = [statement for statement in deal.evidence if not statement.auction]
    auction = [statement for statement in deal.evidence if statement.auction]
    if len(starting) != 4 or len(auction) != 1:
        errors.append("Evidence must be four starting plus one Auction statement")
    if len({statement.kind for statement in deal.evidence}) != 5:
        errors.append("Evidence must use each template exactly once")
    actual_false = [
        statement for statement in starting
        if not evidence_is_true(statement, deal.players)
    ]
    actual_true = [
        statement for statement in starting
        if evidence_is_true(statement, deal.players)
    ]
    if len(actual_false) != 2 or len(actual_true) != 2:
        errors.append("starting Evidence must contain exactly two true and two false")
    if auction and not evidence_is_true(auction[0], deal.players):
        errors.append("Auction Evidence must be truthful")
    owners = [statement.owner for statement in starting]
    if len(set(owners)) != 4 or None in owners:
        errors.append("starting Evidence must have four different owners")
    evidence_factions = Counter(
        deal.players[owner].faction for owner in owners if owner is not None
    )
    if set(evidence_factions) != {ARISTOCRAT, REFORMER, MAGNATE}:
        errors.append("starting Evidence must reach every Faction")
    if max(evidence_factions.values(), default=0) > 2:
        errors.append("no Faction may hold more than two starting Evidence pieces")
    syndicate_evidence = sum(
        deal.players[owner].role in (ASSASSIN, ACCOMPLICE)
        for owner in owners if owner is not None
    )
    if syndicate_evidence > 1:
        errors.append("at most one Syndicate member may hold starting Evidence")
    if not any(
        statement.is_true
        and statement.owner is not None
        and deal.players[statement.owner].role == INNOCENT
        for statement in starting
    ):
        errors.append("at least one truthful starting Evidence must be held by an Innocent")

    valid_hits = {
        "OLD_GUARD": sum(
            player.faction == ARISTOCRAT
            and player.role not in (ASSASSIN, ACCOMPLICE)
            for player in deal.players
        ),
        "NEW_ORDER": sum(
            player.faction == REFORMER
            and player.role not in (ASSASSIN, ACCOMPLICE)
            for player in deal.players
        ),
        "PURSE_STRINGS": faction_counts[MAGNATE],
    }
    if any(valid_hits[hit] < 2 for hit in deal.hits):
        errors.append("recommended Hit has fewer than two opening targets")
    return errors


def evidence_text(statement: EvidenceStatement, language: str) -> str:
    label = LABELS[language]
    value = label[statement.value]
    if language == "en":
        return {
            "MOTIVE": f"One Syndicate member's Motive is **{value}**.",
            "AMBITION": f"One Syndicate member's Ambition is **{value}**.",
            "SECRET": f"One Syndicate member's Secret is **{value}**.",
            "ASSASSIN_FACTION": (
                f"The Assassin, not the Accomplice, is the **{value}**."
            ),
            "ADVANTAGE": (
                f"One Syndicate member's Starting Advantage was **{value}**."
            ),
        }[statement.kind]
    return {
        "MOTIVE": f"Мотив одного з членів Синдикату — **{value}**.",
        "AMBITION": f"Амбіція одного з членів Синдикату — **{value}**.",
        "SECRET": f"Секрет одного з членів Синдикату — **{value}**.",
        "ASSASSIN_FACTION": (
            f"Вбивця — це **{value}**, а не Спільник."
        ),
        "ADVANTAGE": (
            f"Стартовою Перевагою одного з членів Синдикату був **{value}**."
        ),
    }[statement.kind]


def _victory_text(player: Player, deal: Deal, language: str) -> str:
    if player.role in (ASSASSIN, ACCOMPLICE):
        if language == "en":
            return (
                f"The current Assassin must survive with at least "
                f"{deal.syndicate_threshold} personal Influence + Stash. "
                "You win together."
            )
        return (
            f"Чинний Вбивця має вижити й мати щонайменше "
            f"{deal.syndicate_threshold} особистого Впливу + Криївку. "
            "Ви перемагаєте разом."
        )
    if player.faction == MAGNATE:
        if language == "en":
            return (
                f"The remaining combined Magnate Influence must reach "
                f"{deal.magnate_threshold} after Final spending."
            )
        return (
            f"Сумарний Вплив Магнатів після витрат у Фіналі має досягти "
            f"{deal.magnate_threshold}."
        )
    faction = LABELS[language][player.faction]
    if language == "en":
        return f"A {faction} Candidate must win the Final Election."
    return (
        f"На Фінальних Виборах має перемогти Кандидат, який належить "
        f"до Фракції «{faction}»."
    )


def _faction_victory_text(player: Player, deal: Deal, language: str) -> str:
    """Public Faction condition only; never reveal a player's secret Role."""
    if player.faction == MAGNATE:
        if language == "en":
            return (
                f"The remaining combined Magnate Influence must reach "
                f"{deal.magnate_threshold} after Final spending."
            )
        return (
            f"Після витрат у Фіналі сумарний Вплив Магнатів має досягти "
            f"{deal.magnate_threshold}."
        )
    faction = LABELS[language][player.faction]
    if language == "en":
        return f"A {faction} Candidate must win the Final Election."
    return f"На Фінальних Виборах має перемогти Кандидат-{faction}."


def render_player_card(deal: Deal, player: Player, language: str) -> str:
    label = LABELS[language]
    name = deal.name(player.seat, language)
    outsider = deal.name(player.outsider, language)
    partner = (
        deal.accomplice if player.role == ASSASSIN else deal.assassin
    )
    if language == "en":
        lines = [
            f"# PRIVATE — {name}",
            "",
            f"- **Seat:** {player.seat + 1}",
            f"- **Starting Influence:** 4",
            f"- **Faction:** {label[player.faction]}",
            f"- **Role:** {label[player.role]}",
            f"- **Victory:** {_victory_text(player, deal, language)}",
        ]
        if player.role in (ASSASSIN, ACCOMPLICE):
            lines.extend([
                f"- **Syndicate partner:** {deal.name(partner.seat, language)} "
                f"({label[partner.role]})",
                "- Read the separate Syndicate Reference before Round 1.",
            ])
        lines.extend([
            "",
            f"## Motive (+5): {label[player.motive]}",
            GOAL_TEXT[language][player.motive],
            "",
            f"## Ambition (+10): {label[player.ambition]}",
            GOAL_TEXT[language][player.ambition],
            "",
            f"- **Secret:** {label[player.secret]}",
            f"- **Outside-Faction clue:** {outsider} is **not** in your Faction.",
            "",
            f"## Starting Advantage: {label[player.advantage]}",
        ])
        if player.advantage == EVIDENCE:
            statement = deal.evidence[player.evidence_index or 0]
            lines.extend([
                evidence_text(statement, language),
                "This statement may be false. Keep its exact wording.",
            ])
        else:
            target = deal.players[player.intel_target or 0]
            lines.append(
                f"{deal.name(target.seat, language)}'s Secret is "
                f"**{label[target.secret]}**. This information is truthful."
            )
        lines.extend([
            "",
            "> Keep this card private. Report completed Goals to the GM by the end "
            "of Round 2.",
        ])
        return "\n".join(lines) + "\n"

    lines = [
        f"# ПРИВАТНО — {name}",
        "",
        f"- **Місце:** {player.seat + 1}",
        f"- **Стартовий Вплив:** 4",
        f"- **Фракція:** {label[player.faction]}",
        f"- **Роль:** {label[player.role]}",
        f"- **Перемога:** {_victory_text(player, deal, language)}",
    ]
    if player.role in (ASSASSIN, ACCOMPLICE):
        lines.extend([
            f"- **Напарник у Синдикаті:** {deal.name(partner.seat, language)} "
            f"({label[partner.role]})",
            "- До Раунду 1 прочитайте окрему Пам'ятку Синдикату.",
        ])
    lines.extend([
        "",
        f"## Мотив (+5): {label[player.motive]}",
        GOAL_TEXT[language][player.motive],
        "",
        f"## Амбіція (+10): {label[player.ambition]}",
        GOAL_TEXT[language][player.ambition],
        "",
        f"- **Секрет:** {label[player.secret]}",
        f"- **Зачіпка про чужу Фракцію:** {outsider} **не належить** до Вашої Фракції.",
        "",
        f"## Стартова Перевага: {label[player.advantage]}",
    ])
    if player.advantage == EVIDENCE:
        statement = deal.evidence[player.evidence_index or 0]
        lines.extend([
            evidence_text(statement, language),
            "Це твердження може бути хибним. Збережіть його точне формулювання.",
        ])
    else:
        target = deal.players[player.intel_target or 0]
        lines.append(
            f"Секрет {deal.secret_subject(target.seat, language)} — "
            f"**{label[target.secret]}**. Ця інформація правдива."
        )
    lines.extend([
        "",
        "> Тримайте цю картку в таємниці. Повідомте Ведучому про виконані Цілі "
        "до кінця Раунду 2.",
    ])
    return "\n".join(lines) + "\n"


def render_gm_master(deal: Deal, language: str) -> str:
    label = LABELS[language]
    faction_counts = Counter(player.faction for player in deal.players)
    title = (
        f"The Dark Council — GM Master Key ({deal.n} Players)"
        if language == "en"
        else f"Темна Рада — Ключ Ведучого ({deal.n} гравців)"
    )
    warning = (
        "**GM ONLY — do not share this section or the combined pack with players.**"
        if language == "en"
        else "**ЛИШЕ ДЛЯ ВЕДУЧОГО — не надсилайте цей розділ або весь пакет гравцям.**"
    )
    lines = [f"# {title}", "", warning, ""]
    if language == "en":
        lines.extend([
            f"- **Seed:** `{deal.seed}`",
            f"- **Faction counts:** {label[ARISTOCRAT]} "
            f"{faction_counts[ARISTOCRAT]} · {label[REFORMER]} "
            f"{faction_counts[REFORMER]} · {label[MAGNATE]} "
            f"{faction_counts[MAGNATE]}",
            f"- **Magnate threshold:** {deal.magnate_threshold}",
            f"- **Assassin + Stash threshold:** {deal.syndicate_threshold}",
            f"- **Assassin:** {deal.name(deal.assassin.seat, language)} "
            f"({label[deal.assassin.faction]})",
            f"- **Accomplice:** {deal.name(deal.accomplice.seat, language)} "
            f"({label[deal.accomplice.faction]})",
            "",
            "## Evidence Key",
            "",
            "| # | Location | Statement | Truth |",
        ])
    else:
        lines.extend([
            f"- **Код роздачі:** `{deal.seed}`",
            f"- **Склад Фракцій:** {label[ARISTOCRAT]} "
            f"{faction_counts[ARISTOCRAT]} · {label[REFORMER]} "
            f"{faction_counts[REFORMER]} · {label[MAGNATE]} "
            f"{faction_counts[MAGNATE]}",
            f"- **Поріг Магнатів:** {deal.magnate_threshold}",
            f"- **Поріг Вбивці + Криївки:** {deal.syndicate_threshold}",
            f"- **Вбивця:** {deal.name(deal.assassin.seat, language)} "
            f"({label[deal.assassin.faction]})",
            f"- **Спільник:** {deal.name(deal.accomplice.seat, language)} "
            f"({label[deal.accomplice.faction]})",
            "",
            "## Ключ Доказів",
            "",
            "| # | Де знаходиться | Твердження | Істинність |",
        ])
    lines.append("|---:|---|---|---|")
    for index, statement in enumerate(deal.evidence, 1):
        location = (
            "Round 2 Auction"
            if statement.auction and language == "en"
            else "Аукціон Раунду 2"
            if statement.auction
            else deal.name(statement.owner or 0, language)
        )
        truth = (
            "TRUE" if statement.is_true and language == "en"
            else "FALSE" if language == "en"
            else "ПРАВДА" if statement.is_true
            else "ХИБА"
        )
        lines.append(
            f"| {index} | {location} | {evidence_text(statement, language)} | "
            f"**{truth}** |"
        )

    lines.extend([
        "",
        "## Player Setup Table" if language == "en" else "## Таблиця гравців",
        "",
        "| Seat / Player | Exp. | Faction | Role | Motive | Ambition | Secret | "
        "Outsider clue | Advantage |"
        if language == "en"
        else "| Місце / Гравець | Досвід | Фракція | Роль | Мотив | Амбіція | "
        "Секрет | Гравець з іншої Фракції | Перевага |",
        "|---|---|---|---|---|---|---|---|---|",
    ])
    for player in deal.players:
        advantage = label[player.advantage]
        if player.advantage == EVIDENCE:
            advantage += f" #{(player.evidence_index or 0) + 1}"
        else:
            target = deal.players[player.intel_target or 0]
            advantage += (
                f": {deal.name(target.seat, language)} = {label[target.secret]}"
            )
        experience_label = (
            "Досвідчений"
            if player.experienced and language == "ua"
            else "Новачок"
            if player.experienced is False and language == "ua"
            else "Y"
            if player.experienced
            else "N"
            if player.experienced is False
            else "—"
        )
        lines.append(
            f"| {player.seat + 1} / {deal.name(player.seat, language)} | "
            f"{experience_label} | "
            f"{label[player.faction]} | {label[player.role]} | "
            f"{label[player.motive]} | {label[player.ambition]} | "
            f"{label[player.secret]} | {deal.name(player.outsider, language)} | "
            f"{advantage} |"
        )

    lines.extend([
        "",
        "## Prepared Hit Set" if language == "en" else "## Підготовлений набір Замовлень",
        "",
    ])
    for round_number, hit in enumerate(deal.hits, 1):
        lines.append(
            f"{round_number}. **{HITS[hit][language]}**"
        )
    lines.append(
        "\nRe-check at least two living players match the printed trait at the start "
        "of each round; replace a Hit if deaths have made it invalid."
        if language == "en"
        else "\nНа початку кожного раунду повторно перевірте наявність щонайменше "
        "двох живих гравців за надрукованою ознакою; замініть Замовлення, якщо "
        "після смертей воно стало недійсним."
    )
    return "\n".join(lines) + "\n"


def render_combined(deal: Deal, language: str) -> str:
    parts = [render_gm_master(deal, language)]
    heading = (
        "# PRIVATE PLAYER CARDS — PRINT/CUT OR SEND INDIVIDUALLY"
        if language == "en"
        else "# ПРИВАТНІ КАРТКИ ГРАВЦІВ — РОЗДРУКУЙТЕ/РОЗРІЖТЕ АБО НАДІШЛІТЬ ОКРЕМО"
    )
    parts.extend([heading + "\n"])
    for player in deal.players:
        parts.append("---\n\n" + render_player_card(deal, player, language))
    return "\n".join(parts)


def render_public_discord_ua(deal: Deal) -> str:
    faction_counts = Counter(player.faction for player in deal.players)
    return "\n".join([
        "**Темна Рада — стартова інформація**",
        "",
        f"Нас **{deal.n} гравців**:",
        f"- Аристократи: **{faction_counts[ARISTOCRAT]}**",
        f"- Реформісти: **{faction_counts[REFORMER]}**",
        f"- Магнати: **{faction_counts[MAGNATE]}** "
        f"(поріг перемоги: **{deal.magnate_threshold} Впливу**)",
        "- Синдикат: **1 Вбивця + 1 Спільник** "
        "(один Аристократ і один Реформіст; Магнати не входять до Синдикату)",
        f"- Поріг Синдикату: **{deal.syndicate_threshold}** "
        "(особистий Вплив чинного Вбивці + Криївка)",
        "- У грі **5 Доказів**, рівно **2 з них хибні**. "
        "Доказ з Аукціону завжди правдивий.",
        "",
        "Правила: https://farsefars.github.io/dark-council/",
        "",
        "Я надішлю кожному приватне повідомлення. Не пересилайте свою картку іншим.",
    ])


def render_discord_dm_ua(deal: Deal, player: Player) -> str:
    label = LABELS["ua"]
    name = deal.name(player.seat, "ua")
    outsider = deal.name(player.outsider, "ua")
    lines = [
        f"**Темна Рада — приватна картка для {name}**",
        "",
        "Не пересилайте це повідомлення іншим гравцям.",
        "",
        f"**Фракція:** {label[player.faction]}",
        f"**Як перемагає Ваша Фракція:** "
        f"{_faction_victory_text(player, deal, 'ua')}",
    ]
    lines.extend([
        "",
        f"## Мотив (+5): {label[player.motive]}",
        GOAL_TEXT["ua"][player.motive],
        "",
        f"## Амбіція (+10): {label[player.ambition]}",
        GOAL_TEXT["ua"][player.ambition],
        "",
        "**Дедлайн Цілей:** заявити Ведучому до початку Раунду 3.",
        "",
        f"## Секрет: {label[player.secret]}",
        "Якщо інший гравець правильно Викриє Ваш Секрет, Ви втрачаєте 4 Впливу, "
        "а цей гравець отримує +1.",
        "",
        "## Зачіпка про Фракцію",
        f"**{outsider} не належить до Вашої Фракції.**",
        "",
        "Стартові 4 фішки Впливу Ви отримаєте особисто перед Раундом 1.",
        "Повна пам'ятка: https://farsefars.github.io/dark-council/",
    ])
    return "\n".join(lines)


def render_discord_pack_ua(deal: Deal) -> str:
    parts = [
        render_gm_discord_reference_ua(deal),
        "",
        "---",
        "",
        "# Публічне повідомлення",
        "",
        "```md",
        render_public_discord_ua(deal),
        "```",
    ]
    for player in deal.players:
        parts.extend([
            "",
            "---",
            "",
            f"# DM — {deal.name(player.seat, 'ua')}",
            "",
            "```md",
            render_discord_dm_ua(deal, player),
            "```",
        ])
    return "\n".join(parts) + "\n"


def render_gm_discord_reference_ua(deal: Deal) -> str:
    label = LABELS["ua"]
    faction_counts = Counter(player.faction for player in deal.players)
    lines = [
        "# ЛИШЕ ДЛЯ ВЕДУЧОГО — коротка довідка",
        "",
        "## Пороги й таймінг",
        "",
        "| Параметр | Значення |",
        "|---|---|",
        f"| Склад Фракцій | {faction_counts[ARISTOCRAT]} Аристократів · "
        f"{faction_counts[REFORMER]} Реформістів · {faction_counts[MAGNATE]} Магнати |",
        f"| Поріг Магнатів | {deal.magnate_threshold} |",
        f"| Поріг Вбивці + Криївки | {deal.syndicate_threshold} |",
        "| Вартість Допиту | 4, 5, 6… |",
        "| Приватні фази | 30 / 45 / 60 хв |",
        "| Докази | 5 усього; рівно 2 хибні; Аукціонний Доказ правдивий |",
        "",
        "## Що повідомити кожному особисто",
        "",
        "| № | Гравець | Фракція | Таємна Роль | Стартова Перевага |",
        "|---:|---|---|---|---|",
    ]
    for player in deal.players:
        if player.advantage == EVIDENCE:
            statement = deal.evidence[player.evidence_index or 0]
            truth = "ПРАВДА" if statement.is_true else "ХИБА"
            advantage = (
                f"**Доказ [{truth}]:** {evidence_text(statement, 'ua')}"
            )
        else:
            target = deal.players[player.intel_target or 0]
            advantage = (
                f"**Компромат:** Секрет {deal.secret_subject(target.seat, 'ua')} — "
                f"**{label[target.secret]}**"
            )
        lines.append(
            f"| {player.seat + 1} | {deal.name(player.seat, 'ua')} | "
            f"{label[player.faction]} | **{label[player.role]}** | {advantage} |"
        )

    auction = next(statement for statement in deal.evidence if statement.auction)
    lines.extend([
        "",
        f"**Аукціонний Доказ (Раунд 2, ПРАВДА):** "
        f"{evidence_text(auction, 'ua')}",
        "",
        "## Повна зведена таблиця",
        "",
        "| № | Гравець | Досвід | Фракція | Роль | Мотив (+5) | Амбіція (+10) | "
        "Секрет | Гравець з іншої Фракції | Перевага |",
        "|---:|---|---|---|---|---|---|---|---|---|",
    ])
    for player in deal.players:
        advantage = label[player.advantage]
        if player.advantage == EVIDENCE:
            statement = deal.evidence[player.evidence_index or 0]
            advantage += f" ({'ПРАВДА' if statement.is_true else 'ХИБА'})"
        else:
            target = deal.players[player.intel_target or 0]
            advantage += (
                f": {deal.name(target.seat, 'ua')} = {label[target.secret]}"
            )
        lines.append(
            f"| {player.seat + 1} | {deal.name(player.seat, 'ua')} | "
            f"{'Досвідчений' if player.experienced else 'Новачок'} | "
            f"{label[player.faction]} | "
            f"{label[player.role]} | {label[player.motive]} | "
            f"{label[player.ambition]} | {label[player.secret]} | "
            f"{deal.name(player.outsider, 'ua')} | {advantage} |"
        )
    lines.extend([
        "",
        "## Замовлення на старті",
        "",
    ])
    for round_number, hit in enumerate(deal.hits, 1):
        lines.append(f"{round_number}. **{HITS[hit]['ua']}**")
    return "\n".join(lines)


def write_discord_ua(deal: Deal, output_dir: Path) -> list[Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    prefix = f"deal-{deal.n}p"
    private_dir = output_dir / f"{prefix}-private"
    private_dir.mkdir(parents=True, exist_ok=True)
    combined = output_dir / f"{prefix}-discord-ua.md"
    combined.write_text(render_discord_pack_ua(deal), encoding="utf-8")
    written = [combined]
    public = private_dir / "discord-public-ua.txt"
    public.write_text(render_public_discord_ua(deal), encoding="utf-8")
    written.append(public)
    for player in deal.players:
        safe_name = "".join(
            char if char.isalnum() or char in ("-", "_") else "-"
            for char in deal.name(player.seat, "ua")
        ).strip("-")
        path = private_dir / f"discord-{player.seat + 1:02d}-{safe_name}-ua.txt"
        path.write_text(render_discord_dm_ua(deal, player), encoding="utf-8")
        written.append(path)
    return written


def write_deal(deal: Deal, output_dir: Path) -> list[Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    prefix = f"deal-{deal.n}p"
    written = []
    private_dir = output_dir / f"{prefix}-private"
    private_dir.mkdir(parents=True, exist_ok=True)
    for language in ("ua", "en"):
        combined = output_dir / f"{prefix}-{language}.md"
        combined.write_text(render_combined(deal, language), encoding="utf-8")
        written.append(combined)
        gm = private_dir / f"gm-master-{language}.md"
        gm.write_text(render_gm_master(deal, language), encoding="utf-8")
        written.append(gm)
        for player in deal.players:
            card = private_dir / (
                f"player-{player.seat + 1:02d}-{language}.md"
            )
            card.write_text(
                render_player_card(deal, player, language),
                encoding="utf-8",
            )
            written.append(card)
    return written


def _parse_names(args) -> list[str] | None:
    if args.names and args.names_file:
        raise ValueError("use either --names or --names-file, not both")
    if args.names:
        return [name.strip() for name in args.names.split(",") if name.strip()]
    if args.names_file:
        return [
            line.strip()
            for line in Path(args.names_file).read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
    return None


def _parse_roster(path: str | None) -> tuple[list[str] | None, list[bool] | None]:
    if not path:
        return None, None
    with Path(path).open(encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    if not rows or not {"Name", "Experienced"} <= set(rows[0]):
        raise ValueError("roster CSV must have Name and Experienced columns")
    names = [row["Name"].strip() for row in rows]
    experienced = []
    for row in rows:
        value = row["Experienced"].strip().casefold()
        if value in {"y", "yes", "true", "1"}:
            experienced.append(True)
        elif value in {"n", "no", "false", "0"}:
            experienced.append(False)
        else:
            raise ValueError(
                f"invalid Experienced value for {row['Name']!r}: "
                f"{row['Experienced']!r}"
            )
    return names, experienced


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--players", type=int, default=12)
    parser.add_argument("--seed", type=int)
    parser.add_argument("--names", help="comma-separated player names")
    parser.add_argument("--names-file", help="UTF-8 file with one player name per line")
    parser.add_argument(
        "--roster-file",
        help="UTF-8 CSV with Name and Experienced (Y/N) columns",
    )
    parser.add_argument(
        "--discord-ua",
        action="store_true",
        help="write Ukrainian Discord copy blocks and individual text files",
    )
    parser.add_argument(
        "--output-dir",
        default=str(Path(__file__).resolve().parent),
    )
    args = parser.parse_args()
    roster_names, experienced = _parse_roster(args.roster_file)
    if roster_names is not None and (args.names or args.names_file):
        raise ValueError("use --roster-file or --names/--names-file, not both")
    names = roster_names or _parse_names(args)
    n = len(names) if names else args.players
    seed = args.seed if args.seed is not None else secrets.randbits(32)
    deal = generate_deal(n, seed, names, experienced)
    written = write_deal(deal, Path(args.output_dir))
    if args.discord_ua:
        written.extend(write_discord_ua(deal, Path(args.output_dir)))
    print(
        f"Generated verified {n}-player deal with seed {seed}: "
        f"{len(written)} files"
    )
    for path in written[:4]:
        print(f"  {path}")
    if len(written) > 4:
        print(f"  ... and {len(written) - 4} individual files")


if __name__ == "__main__":
    main()
