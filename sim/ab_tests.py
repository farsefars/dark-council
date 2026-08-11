"""Paired high-N tests for the four mechanical questions removed from live A/B testing."""

from __future__ import annotations

import argparse
import os
import statistics

from .engine import run_game
from .final import recommended_config
from .run import summarise

COUNTS = [10, 11, 12, 13, 14, 15]

VARIANTS = {
    "Guilty stakes": {
        "+5/-1 (current)": {},
        "+3/-2": {"guilty_vote_reward": 3, "guilty_vote_penalty": 2},
    },
    "Election aggregation": {
        "Three-candidate plurality (current)": {},
        "Top-two runoff": {"election_mode": "runoff"},
    },
    "Ghost voting": {
        "Vote in every Interrogation and Final (current)": {},
        "One lifetime Ghost vote": {"ghost_vote_mode": "lifetime"},
    },
    "Final vote market": {
        "Flat 3 per vote (current)": {},
        "Escalating 3/6/9/...": {"vote_purchase_mode": "escalating"},
        "Flat with max 2 extra": {"vote_purchase_mode": "capped",
                                  "vote_purchase_cap": 2},
    },
}


def run_variant(overrides: dict, games: int, seed0: int) -> list:
    results = []
    for n in COUNTS:
        cfg = recommended_config(n, **overrides)
        results.extend(run_game(n, seed0 + n * 100_000 + seed, cfg)
                       for seed in range(games))
    return results


def election_shares(results: list) -> list[float]:
    shares = []
    for result in results:
        for event in result.events:
            if event[2] == "ELECTION_META":
                shares.append(event[4] / 10_000)
    return shares


def purchased_votes(results: list) -> float:
    totals = []
    for result in results:
        totals.append(sum(event[4] for event in result.events
                          if event[2] == "VOTE_PURCHASE"))
    return statistics.fmean(totals) if totals else 0.0


def ghost_votes(results: list) -> float:
    totals = []
    for result in results:
        totals.append(sum(1 for event in result.events
                          if event[2] == "GHOST_VOTE"))
    return statistics.fmean(totals) if totals else 0.0


def aggregate(results: list) -> dict:
    s = summarise(results)
    shares = election_shares(results)
    return {
        "aristocrat": s["aristocrat"]["rate"],
        "reformer": s["reformer"]["rate"],
        "magnate": s["magnate"]["rate"],
        "syndicate": s["syndicate"]["rate"],
        "deaths": s["deaths"],
        "interrogations": s["interrogations"],
        "execution_accuracy": s["execution_accuracy"],
        "bankruptcies": s["bankruptcies"],
        "low_plurality": (sum(v < 0.40 for v in shares) / len(shares)
                           if shares else 0.0),
        "winner_share": statistics.fmean(shares) if shares else 0.0,
        "purchased_votes": purchased_votes(results),
        "ghost_votes": ghost_votes(results),
    }


def render(all_stats: dict, games: int) -> str:
    total = games * len(COUNTS)
    lines = [
        "# The Dark Council — Simulator A/B Queue",
        "",
        f"**Method:** {games:,} paired seeds per player count, counts 10–15 "
        f"({total:,} games per variant).",
        "",
        "These tests answer arithmetic and modelled behavioural questions only. A null "
        "result does not prove a rule is unimportant to humans.",
        "",
    ]
    for question, variants in all_stats.items():
        lines.extend([
            f"## {question}",
            "",
            "| Variant | A | R | Magnate | Syndicate | Deaths | Interrogations | "
            "Execution accuracy | Bankruptcies | Winner <40% | Mean winner share | "
            "Extra votes bought | Lifetime Ghost votes used |",
            "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
        ])
        for name, s in variants.items():
            lines.append(
                f"| {name} | {s['aristocrat']:.1%} | {s['reformer']:.1%} | "
                f"{s['magnate']:.1%} | {s['syndicate']:.1%} | {s['deaths']:.2f} | "
                f"{s['interrogations']:.2f} | {s['execution_accuracy']:.1%} | "
                f"{s['bankruptcies']:.2f} | {s['low_plurality']:.1%} | "
                f"{s['winner_share']:.1%} | {s['purchased_votes']:.2f} | "
                f"{s['ghost_votes']:.2f} |")
        lines.extend(["", "### Interpretation", ""])
        if question == "Guilty stakes":
            lines.append(
                "Prefer neither from win rates alone. The live instrument must measure "
                "voter confidence and whether the current 16.7% break-even encourages "
                "low-confidence Guilty votes.")
        elif question == "Election aggregation":
            lines.append(
                "The simulator can measure faction outcomes and spoiler frequency; live "
                "testing must decide whether a runoff improves legitimacy or merely adds "
                "time and another negotiation pause.")
        elif question == "Ghost voting":
            lines.append(
                "The model conserves a lifetime vote for a strong Interrogation read or "
                "the Final. Live testing must decide whether this feels strategic or "
                "silences eliminated players.")
        else:
            lines.append(
                "Vote-market variants must preserve Magnate bargaining. Lower purchased "
                "vote volume is not automatically better if it removes the reason to make "
                "Influence deals.")
        lines.append("")
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--games", type=int, default=1000,
                        help="games per player count and variant")
    parser.add_argument("--output", help="optional Markdown output path")
    args = parser.parse_args()

    all_stats = {}
    for q_index, (question, variants) in enumerate(VARIANTS.items()):
        all_stats[question] = {}
        seed0 = 900_000 + q_index * 10_000
        for name, overrides in variants.items():
            results = run_variant(overrides, args.games, seed0)
            all_stats[question][name] = aggregate(results)

    report = render(all_stats, args.games)
    if args.output:
        os.makedirs(os.path.dirname(os.path.abspath(args.output)), exist_ok=True)
        with open(args.output, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(report)
    print(report)


if __name__ == "__main__":
    main()
