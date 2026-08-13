"""Faction-Syndicate alliance stress test for whole-system packages."""

from __future__ import annotations

import argparse
from pathlib import Path
import statistics

from .exploits import run_alliance_game
from .final import recommended_config
from .packages import PACKAGES, get_package


def measure(config_for, games: int, seed: int) -> dict:
    rows = []
    for player_count in range(10, 16):
        honest = []
        abandoned = []
        for index in range(games):
            game_seed = seed + player_count * 100_000 + index
            config = config_for(player_count)
            honest.append(run_alliance_game(
                player_count, game_seed, config, ignore_hit=False
            ))
            abandoned.append(run_alliance_game(
                player_count, game_seed, config, ignore_hit=True
            ))

        def summarise(results):
            count = len(results)
            return {
                "syndicate": sum(row.result.syndicate_win for row in results) / count,
                "allied_faction": sum(
                    row.result.winning_faction == row.allied_faction for row in results
                ) / count,
                "joint": sum(
                    row.result.syndicate_win
                    and row.result.winning_faction == row.allied_faction
                    for row in results
                ) / count,
                "hits": statistics.fmean(row.result.hits_met for row in results),
                "assassin_total": statistics.fmean(
                    row.result.assassin_total for row in results
                ),
            }

        rows.append({
            "players": player_count,
            "honest": summarise(honest),
            "abandoned": summarise(abandoned),
        })
    return {"rows": rows}


def render(measured: dict[str, dict], games: int, seed: int) -> str:
    lines = [
        "# Faction-Syndicate alliance stress test",
        "",
        f"**Sample:** {games} paired games per player count and strategy; "
        f"10-15 players; first seed {seed}.",
        "",
        "The coalition has perfect knowledge, protects and funds the Assassin, and votes "
        "as a bloc. `Honest Hits` follows ordinary target selection; `Abandon Hits` "
        "deliberately attacks the rival Faction. This is a pessimistic rejection test, "
        "not a prediction of ordinary play.",
        "",
        "| Package | Syndicate honest | Syndicate abandon | Delta | "
        "Allied Faction abandon | Joint abandon | Hits honest/abandon |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for name, data in measured.items():
        rows = data["rows"]
        honest_syn = statistics.fmean(row["honest"]["syndicate"] for row in rows)
        abandon_syn = statistics.fmean(row["abandoned"]["syndicate"] for row in rows)
        allied = statistics.fmean(
            row["abandoned"]["allied_faction"] for row in rows
        )
        joint = statistics.fmean(row["abandoned"]["joint"] for row in rows)
        honest_hits = statistics.fmean(row["honest"]["hits"] for row in rows)
        abandon_hits = statistics.fmean(row["abandoned"]["hits"] for row in rows)
        lines.append(
            f"| {name} | {honest_syn:.1%} | {abandon_syn:.1%} | "
            f"{abandon_syn - honest_syn:+.1%} | {allied:.1%} | {joint:.1%} | "
            f"{honest_hits:.2f}/{abandon_hits:.2f} |"
        )

    lines.extend([
        "",
        "## By player count",
        "",
    ])
    for name, data in measured.items():
        lines.extend([
            f"### {name}",
            "",
            "| Players | Syndicate honest | Syndicate abandon | Allied Faction abandon | "
            "Joint abandon |",
            "|---:|---:|---:|---:|---:|",
        ])
        for row in data["rows"]:
            lines.append(
                f"| {row['players']} | {row['honest']['syndicate']:.1%} | "
                f"{row['abandoned']['syndicate']:.1%} | "
                f"{row['abandoned']['allied_faction']:.1%} | "
                f"{row['abandoned']['joint']:.1%} |"
            )
        lines.append("")
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--games", type=int, default=100)
    parser.add_argument("--seed", type=int, default=4_200_000)
    parser.add_argument("--output", type=Path)
    parser.add_argument(
        "--package",
        action="append",
        choices=sorted(PACKAGES),
        dest="packages",
    )
    args = parser.parse_args()

    selected = args.packages or list(PACKAGES)
    measured = {
        "Baseline": measure(recommended_config, args.games, args.seed),
    }
    for key in selected:
        package = get_package(key)
        measured[package.name] = measure(package.config_for, args.games, args.seed)

    report = render(measured, args.games, args.seed)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(report, encoding="utf-8")
        print(args.output)
    else:
        print(report)


if __name__ == "__main__":
    main()
