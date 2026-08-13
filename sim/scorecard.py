"""Whole-system balance scorecard against a frozen stable baseline.

The baseline and candidate use identical seeds. Config overrides are applied only to
the candidate; the published/recommended configuration remains the engine default.
"""

from __future__ import annotations

import argparse
import ast
from collections import defaultdict
from dataclasses import fields
import math
from pathlib import Path
import statistics
from typing import Any

from .engine import (
    ACCOMPLICE,
    ARISTOCRAT,
    ASSASSIN,
    MAGNATE,
    REFORMER,
    Config,
    run_game,
)
from .final import recommended_config
from .run import wilson


DEFAULT_COUNTS = (10, 11, 12, 13, 14, 15)
DEFAULT_GAMES = 100
DEFAULT_SEED = 1_900_000
PHYSICAL_TOKEN_BUDGET = 250
PRACTICAL_HOLDING_P90 = 30
TARGET_VOTE_DECISIVENESS = 0.20
EFFECTIVE_BRIBE_FRACTION = 0.5


def mean(values: list[float]) -> float:
    return statistics.fmean(values) if values else 0.0


def quantile(values: list[float], q: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    index = max(0, min(len(ordered) - 1, math.ceil(q * len(ordered)) - 1))
    return ordered[index]


def rate(results: list, attr: str) -> float:
    return sum(bool(getattr(result, attr)) for result in results) / len(results)


def event_count(result, kind: str) -> int:
    return sum(1 for event in result.events if event[2] == kind)


def ledger_amount(result, reason: str) -> int:
    return sum(row[5] for row in result.ledger if row[6] == reason)


def is_player(holder: str) -> bool:
    return holder.isdigit()


def collect(results: list, configs: dict[int, Config], override_count: int) -> dict[str, Any]:
    games = len(results)
    players = sum(result.n_players for result in results)
    purchases = [
        event
        for result in results
        for event in result.events
        if event[2] == "VOTE_PURCHASE"
    ]
    evidence = sum(event_count(result, "EVIDENCE_DISCLOSURE") for result in results)
    reveals = sum(event_count(result, "REVEAL") for result in results)
    pacts = sum(event_count(result, "PUBLIC_PACT") for result in results)
    hits = sum(event_count(result, "HIT") for result in results)

    social_amounts: list[int] = []
    social_pairs: list[int] = []
    social_games = 0
    inheritance_amounts: list[int] = []
    faction_liquidity: list[float] = []
    verified_factions: list[int] = []
    activity_by_round: dict[int, list[int]] = defaultdict(list)
    deaths_by_round: dict[int, list[int]] = defaultdict(list)
    goals_by_round: dict[int, list[int]] = defaultdict(list)

    for result in results:
        social_rows = [
            row for row in result.ledger
            if is_player(row[3])
            and is_player(row[4])
            and not row[6].endswith("_bequest")
        ]
        social_amounts.append(sum(row[5] for row in social_rows))
        social_pairs.append(len({(row[3], row[4]) for row in social_rows}))
        social_games += bool(social_rows)
        inheritance_amounts.append(sum(
            row[5] for row in result.ledger if row[6].endswith("_bequest")
        ))

        for round_number in (1, 2, 3):
            round_snapshots = [
                row for row in result.snapshots if row[1] == round_number
            ]
            for faction in (ARISTOCRAT, REFORMER):
                faction_liquidity.append(sum(
                    max(0, row[3])
                    for row in round_snapshots
                    if row[4] and result.players[row[2]].faction == faction
                ))
        verified_factions.extend(
            len(player.knowledge.verified_faction) for player in result.players
        )

        for round_number in (1, 2, 3):
            social = sum(1 for row in social_rows if row[1] == round_number)
            public = sum(
                1 for event in result.events
                if event[1] == round_number
                and event[2] in {"EXPOSE", "INTERROGATION", "PUBLIC_PACT"}
            )
            goals = sum(
                1 for row in result.ledger
                if row[1] == round_number
                and row[6] in {"motive_claim", "ambition_claim"}
            )
            activity_by_round[round_number].append(social + public)
            deaths_by_round[round_number].append(
                (result.deaths_by_round or {}).get(round_number, 0)
            )
            goals_by_round[round_number].append(goals)

    win_rates = {
        "Aristocrat": rate(results, "aristocrat_win"),
        "Reformer": rate(results, "reformer_win"),
        "Magnate": rate(results, "magnate_win"),
        "Syndicate": rate(results, "syndicate_win"),
    }
    win_intervals = {}
    for label, attribute in (
        ("Aristocrat", "aristocrat_win"),
        ("Reformer", "reformer_win"),
        ("Magnate", "magnate_win"),
        ("Syndicate", "syndicate_win"),
    ):
        successes = sum(bool(getattr(result, attribute)) for result in results)
        win_intervals[label] = wilson(successes, games)
    faction_gap = abs(win_rates["Aristocrat"] - win_rates["Reformer"])
    hit_reward = mean([configs[result.n_players].hit_payout for result in results])
    nominal_bribe = mean(faction_liquidity)
    effective_bribe = nominal_bribe * EFFECTIVE_BRIBE_FRACTION
    hit_bribe_ratio = hit_reward / effective_bribe if effective_bribe else math.inf

    per_count: dict[int, dict[str, float]] = {}
    for count in sorted({result.n_players for result in results}):
        subset = [result for result in results if result.n_players == count]
        per_count[count] = {
            "aristocrat": rate(subset, "aristocrat_win"),
            "reformer": rate(subset, "reformer_win"),
            "magnate": rate(subset, "magnate_win"),
            "syndicate": rate(subset, "syndicate_win"),
            "peak_p90": quantile([r.peak_total_chips for r in subset], 0.9),
            "richest_p90": quantile([r.peak_single_holding for r in subset], 0.9),
            "zero_agency": sum(r.zero_agency_players for r in subset)
            / sum(r.n_players for r in subset),
        }

    metrics = {
        "games": games,
        "players": players,
        "win_rates": win_rates,
        "win_intervals": win_intervals,
        "faction_gap": faction_gap,
        "assassin_alive": rate(results, "assassin_alive"),
        "zero_agency_share": sum(r.zero_agency_players for r in results) / players,
        "bank_injected": mean([r.bank_injected for r in results]),
        "bank_retired": mean([r.bank_retired for r in results]),
        "player_circulated": mean([r.player_circulated for r in results]),
        "peak_total_p90": quantile([r.peak_total_chips for r in results], 0.9),
        "peak_total_worst": max(r.peak_total_chips for r in results),
        "peak_players_p90": quantile([r.peak_player_chips for r in results], 0.9),
        "peak_stash_p90": quantile([r.peak_stash for r in results], 0.9),
        "richest_p90": quantile([r.peak_single_holding for r in results], 0.9),
        "richest_worst": max(r.peak_single_holding for r in results),
        "wealth_top_share": mean([r.wealth_top_share for r in results]),
        "vote_buyers": len({(event[0], event[3]) for event in purchases}) / games,
        "purchased_votes": sum(int(event[4]) for event in purchases) / games,
        "vote_decisiveness": sum(r.votes_decisive for r in results) / games,
        "hit_success": sum(r.hits_met for r in results) / hits if hits else 0.0,
        "hit_reward": hit_reward,
        "nominal_faction_liquidity": nominal_bribe,
        "effective_faction_liquidity": effective_bribe,
        "hit_bribe_ratio": hit_bribe_ratio,
        "execution_reward": mean([
            ledger_amount(r, "guilty_vote_reward")
            + ledger_amount(r, "prosecutor_refund")
            + ledger_amount(r, "prosecutor_reward")
            for r in results
        ]),
        "deaths": mean([r.deaths for r in results]),
        "inheritance": mean(inheritance_amounts),
        "social_amount": mean(social_amounts),
        "social_pairs": mean(social_pairs),
        "social_game_rate": social_games / games,
        "evidence_disclosures": evidence / games,
        "reveals": reveals / games,
        "public_pacts": pacts / games,
        "verified_factions": mean(verified_factions),
        "activity_by_round": {
            round_number: mean(values)
            for round_number, values in activity_by_round.items()
        },
        "deaths_by_round": {
            round_number: mean(values)
            for round_number, values in deaths_by_round.items()
        },
        "goals_by_round": {
            round_number: mean(values)
            for round_number, values in goals_by_round.items()
        },
        "override_count": override_count,
        "per_count": per_count,
    }
    metrics["invariants"] = assess_invariants(metrics)
    return metrics


def assess_invariants(metrics: dict[str, Any]) -> list[tuple[str, str, str]]:
    win_rates = metrics["win_rates"]
    return [
        (
            "I1 Agency",
            "PASS" if metrics["zero_agency_share"] <= 0.10 else "FAIL",
            f"{metrics['zero_agency_share']:.1%} of players recorded no modelled agency",
        ),
        (
            "I2 Inheritance",
            "PASS" if metrics["inheritance"] > 0 or metrics["deaths"] == 0 else "FAIL",
            f"{metrics['inheritance']:.1f} Influence inherited per game",
        ),
        (
            "I3 Physical playability",
            "PASS"
            if metrics["peak_total_p90"] <= PHYSICAL_TOKEN_BUDGET
            and metrics["richest_p90"] <= PRACTICAL_HOLDING_P90
            else "FAIL",
            f"p90 pool {metrics['peak_total_p90']:.0f}/{PHYSICAL_TOKEN_BUDGET}; "
            f"p90 holding {metrics['richest_p90']:.0f}/{PRACTICAL_HOLDING_P90}",
        ),
        (
            "I4 Assassin triangle",
            "PASS"
            if 0.5 <= metrics["hit_bribe_ratio"] <= 1.5
            and metrics["execution_reward"] > 0
            and 0.15 <= metrics["assassin_alive"] <= 0.85
            else "FAIL",
            f"Hit/effective bribe {metrics['hit_bribe_ratio']:.2f}; "
            f"execution reward {metrics['execution_reward']:.1f}; "
            f"Assassin alive {metrics['assassin_alive']:.1%}",
        ),
        (
            "I5 Influence matters",
            "PASS"
            if 0.15 <= win_rates["Magnate"] <= 0.55
            and metrics["vote_decisiveness"] >= TARGET_VOTE_DECISIVENESS
            else "FAIL",
            f"Magnate {win_rates['Magnate']:.1%}; purchased votes decisive "
            f"{metrics['vote_decisiveness']:.1%}/{TARGET_VOTE_DECISIVENESS:.0%}",
        ),
        (
            "I6 Social over arithmetic",
            "PASS"
            if metrics["social_game_rate"] >= 0.70 and metrics["social_pairs"] >= 2
            else "FAIL",
            f"social transfers in {metrics['social_game_rate']:.1%} of games; "
            f"{metrics['social_pairs']:.1f} distinct directed pairs",
        ),
        (
            "I7 Teachability",
            "PASS" if metrics["override_count"] == 0 else "REVIEW",
            "baseline adds no concepts"
            if metrics["override_count"] == 0
            else f"{metrics['override_count']} Config values changed; manual rules review required",
        ),
        (
            "I8 Symmetry and viability",
            "PASS"
            if metrics["faction_gap"] <= 0.08
            and all(0.15 <= value <= 0.65 for value in win_rates.values())
            else "FAIL",
            f"A/R gap {metrics['faction_gap']:.1%}; range "
            f"{min(win_rates.values()):.1%}-{max(win_rates.values()):.1%}",
        ),
    ]


def run_suite(
    counts: tuple[int, ...],
    games_per_count: int,
    seed: int,
    overrides: dict[str, Any] | None = None,
) -> tuple[list, dict[int, Config]]:
    overrides = overrides or {}
    results = []
    configs = {}
    for count in counts:
        config = recommended_config(count, **overrides)
        configs[count] = config
        for index in range(games_per_count):
            game_seed = seed + count * 100_000 + index
            results.append(run_game(count, game_seed, config))
    return results, configs


def fmt(value: float, percent: bool = False) -> str:
    return f"{value:.1%}" if percent else f"{value:.2f}"


def delta(candidate: float, baseline: float, percent: bool = False) -> str:
    difference = candidate - baseline
    return f"{difference:+.1%}" if percent else f"{difference:+.2f}"


def render_metrics(
    baseline: dict[str, Any],
    candidate: dict[str, Any] | None,
    name: str,
    counts: tuple[int, ...],
    games_per_count: int,
    seed: int,
    overrides: dict[str, Any],
) -> str:
    lines = [
        "# Whole-system balance scorecard",
        "",
        f"**Frozen baseline:** restored stable economy (`a581b50`).  ",
        f"**Sample:** {games_per_count} games x {len(counts)} player counts "
        f"({', '.join(map(str, counts))}); first seed {seed}.  ",
        "**Method:** baseline and candidate use identical seeds. Simulation is a rejection "
        "test, not proof of fun or clarity.",
        "",
    ]
    if candidate:
        rendered = ", ".join(f"`{key}={value!r}`" for key, value in overrides.items())
        lines.extend([
            f"**Candidate:** {name}.  ",
            f"**Overrides:** {rendered or 'none'}.",
            "",
        ])

    rows = [
        ("Aristocrat win", ("win_rates", "Aristocrat"), True),
        ("Reformer win", ("win_rates", "Reformer"), True),
        ("Magnate win", ("win_rates", "Magnate"), True),
        ("Syndicate win", ("win_rates", "Syndicate"), True),
        ("A/R gap", ("faction_gap",), True),
        ("Zero-agency players", ("zero_agency_share",), True),
        ("Bank to players", ("bank_injected",), False),
        ("Players to Bank", ("bank_retired",), False),
        ("Player circulation", ("player_circulated",), False),
        ("Peak physical pool p90", ("peak_total_p90",), False),
        ("Peak physical pool worst", ("peak_total_worst",), False),
        ("Richest holding p90", ("richest_p90",), False),
        ("Richest holding worst", ("richest_worst",), False),
        ("Vote buyers/game", ("vote_buyers",), False),
        ("Purchased votes/game", ("purchased_votes",), False),
        ("Purchased votes decisive", ("vote_decisiveness",), True),
        ("Hit success", ("hit_success",), True),
        ("Hit reward", ("hit_reward",), False),
        ("Effective Faction liquidity", ("effective_faction_liquidity",), False),
        ("Hit/effective bribe", ("hit_bribe_ratio",), False),
        ("Correct-execution injection/game", ("execution_reward",), False),
        ("Deaths/game", ("deaths",), False),
        ("Inheritance/game", ("inheritance",), False),
        ("Social transfer/game", ("social_amount",), False),
        ("Social pairs/game", ("social_pairs",), False),
        ("Games with social transfer", ("social_game_rate",), True),
        ("Evidence disclosures/game", ("evidence_disclosures",), False),
        ("Verified Factions/player", ("verified_factions",), False),
    ]

    def get(metrics: dict[str, Any], path: tuple[str, ...]) -> float:
        value: Any = metrics
        for key in path:
            value = value[key]
        return float(value)

    lines.extend([
        "## Headline scorecard",
        "",
        "| Metric | Baseline |" + (" Candidate | Delta |" if candidate else ""),
        "|---|---:|" + ("---:|---:|" if candidate else ""),
    ])
    for label, path, percent in rows:
        base_value = get(baseline, path)
        base_text = fmt(base_value, percent)
        if path[0] == "win_rates":
            lo, hi = baseline["win_intervals"][path[1]]
            base_text = f"{base_value:.1%} [{lo:.1%}, {hi:.1%}]"
        if candidate:
            candidate_value = get(candidate, path)
            candidate_text = fmt(candidate_value, percent)
            if path[0] == "win_rates":
                lo, hi = candidate["win_intervals"][path[1]]
                candidate_text = f"{candidate_value:.1%} [{lo:.1%}, {hi:.1%}]"
            lines.append(
                f"| {label} | {base_text} | "
                f"{candidate_text} | "
                f"{delta(candidate_value, base_value, percent)} |"
            )
        else:
            lines.append(f"| {label} | {base_text} |")

    focus = candidate or baseline
    lines.extend([
        "",
        "## Invariant gates",
        "",
        "| Invariant | Result | Evidence |",
        "|---|---|---|",
    ])
    for invariant, status, evidence_text in focus["invariants"]:
        lines.append(f"| {invariant} | **{status}** | {evidence_text} |")

    lines.extend([
        "",
        "## Player-count view",
        "",
        "| Players | Aristocrat | Reformer | Magnate | Syndicate | "
        "Pool p90 | Holding p90 | Zero agency |",
        "|---:|---:|---:|---:|---:|---:|---:|---:|",
    ])
    for count, values in focus["per_count"].items():
        lines.append(
            f"| {count} | {values['aristocrat']:.1%} | {values['reformer']:.1%} | "
            f"{values['magnate']:.1%} | {values['syndicate']:.1%} | "
            f"{values['peak_p90']:.0f} | {values['richest_p90']:.0f} | "
            f"{values['zero_agency']:.1%} |"
        )

    lines.extend([
        "",
        "## Pacing",
        "",
        "| Round | Meaningful modelled actions/game | Deaths/game | Goals claimed/game |",
        "|---:|---:|---:|---:|",
    ])
    for round_number in (1, 2, 3):
        lines.append(
            f"| {round_number} | {focus['activity_by_round'][round_number]:.2f} | "
            f"{focus['deaths_by_round'][round_number]:.2f} | "
            f"{focus['goals_by_round'][round_number]:.2f} |"
        )

    lines.extend([
        "",
        "## Interpretation limits",
        "",
        "- The scorecard measures modelled behaviour, not persuasion quality, enjoyment, "
        "clarity, or desire to replay.",
        "- `Hit/effective bribe` uses end-of-Council major-Faction liquidity averaged "
        "across all rounds, then discounts it by 50%. The timing and discount are "
        "explicit bargaining assumptions, not discovered facts.",
        "- `Purchased votes decisive` is conservative: it asks whether stripping paid "
        "weight from the same first-round choices changes the winning Faction.",
        "- Complexity and teachability require manual rules review for every candidate.",
        "- Acceptance thresholds are guardrails. They must be revised from live-playtest "
        "evidence rather than tuned until a preferred package passes.",
        "",
    ])
    return "\n".join(lines)


def parse_override(raw: str) -> tuple[str, Any]:
    key, separator, raw_value = raw.partition("=")
    valid = {field.name for field in fields(Config)}
    if not separator or key not in valid:
        raise argparse.ArgumentTypeError(
            f"expected CONFIG_FIELD=value; valid fields include {', '.join(sorted(valid))}"
        )
    try:
        value = ast.literal_eval(raw_value)
    except (SyntaxError, ValueError):
        value = raw_value
    return key, value


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--counts", nargs="+", type=int, default=list(DEFAULT_COUNTS))
    parser.add_argument("--games", type=int, default=DEFAULT_GAMES)
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
    parser.add_argument("--name", default="Candidate")
    parser.add_argument(
        "--set",
        dest="overrides",
        action="append",
        default=[],
        type=parse_override,
        metavar="FIELD=VALUE",
    )
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    counts = tuple(args.counts)
    override_dict = dict(args.overrides)
    baseline_results, baseline_configs = run_suite(counts, args.games, args.seed)
    baseline = collect(baseline_results, baseline_configs, 0)

    candidate = None
    if override_dict:
        candidate_results, candidate_configs = run_suite(
            counts, args.games, args.seed, override_dict
        )
        candidate = collect(
            candidate_results, candidate_configs, len(override_dict)
        )

    report = render_metrics(
        baseline,
        candidate,
        args.name,
        counts,
        args.games,
        args.seed,
        override_dict,
    )
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(report, encoding="utf-8")
        print(args.output)
    else:
        print(report)


if __name__ == "__main__":
    main()
