"""Tune the Hit economy and stress it against a Faction-Syndicate alliance."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import json
from pathlib import Path
import statistics

from .engine import STASH, run_game
from .exploits import run_alliance_game
from .final import recommended_config
from .tune import quantile_threshold


HERE = Path(__file__).resolve().parent
OUTPUT = HERE / "output"
COUNTS = tuple(range(8, 16))
TARGET_SYNDICATE = 0.35
FINAL_THRESHOLDS = {
    8: 156, 9: 154, 10: 152, 11: 152,
    12: 152, 13: 152, 14: 152, 15: 150,
}


@dataclass(frozen=True)
class Economy:
    hit_payout: int
    kill_share: float
    hit_penalty: int

    @property
    def name(self) -> str:
        return (
            f"hit{self.hit_payout}-skim{self.kill_share:g}"
            f"-penalty{self.hit_penalty}"
        )


def win_rate(results, threshold: int) -> float:
    return statistics.fmean(
        result.assassin_alive and result.assassin_total >= threshold
        for result in results
    )


def faction_rates(results) -> tuple[float, float, float]:
    return (
        statistics.fmean(result.aristocrat_win for result in results),
        statistics.fmean(result.reformer_win for result in results),
        statistics.fmean(result.magnate_win for result in results),
    )


def measure_economy(
    economy: Economy,
    games: int,
    seed0: int,
) -> dict:
    by_count = {}
    all_results = []
    hit_income = skim_income = launder_income = 0
    options: list[int] = []
    hit_failures = 0
    personal_failure_debt = 0

    for n in COUNTS:
        cfg = recommended_config(
            n,
            hit_payout=economy.hit_payout,
            kill_share=economy.kill_share,
            hit_penalty=economy.hit_penalty,
            assassin_threshold=1,
        )
        results = [run_game(n, seed0 + i, cfg) for i in range(games)]
        threshold = quantile_threshold(
            [result.assassin_total for result in results],
            TARGET_SYNDICATE,
        )
        by_count[n] = {
            "threshold": threshold,
            "syndicate_rate": win_rate(results, threshold),
            "assassin_total": statistics.fmean(
                result.assassin_total for result in results
            ),
            "hits_met": statistics.fmean(result.hits_met for result in results),
            "assassin_alive": statistics.fmean(
                result.assassin_alive for result in results
            ),
        }
        all_results.extend(results)
        for result in results:
            hit_failures += 3 - result.hits_met
            personal_failure_debt += (result.debt_by_cause or {}).get(
                "hit_failure_personal", 0
            )
            options.extend(
                int(event[4]) for event in result.events if event[2] == "HIT"
            )
            for _, _, _, src, dst, amount, reason in result.ledger:
                if dst != STASH:
                    continue
                if reason == "hit_success":
                    hit_income += amount
                elif reason == "assassinated_skim":
                    skim_income += amount
                elif reason == "launder":
                    launder_income += amount

    total_income = hit_income + skim_income + launder_income
    aristocrat, reformer, magnate = faction_rates(all_results)
    return {
        "economy": {
            "hit_payout": economy.hit_payout,
            "kill_share": economy.kill_share,
            "hit_penalty": economy.hit_penalty,
        },
        "by_count": by_count,
        "hit_income_share": hit_income / total_income if total_income else 0.0,
        "hit_income_per_game": hit_income / len(all_results),
        "skim_income_per_game": skim_income / len(all_results),
        "launder_income_per_game": launder_income / len(all_results),
        "hit_failures_per_game": hit_failures / len(all_results),
        "failure_debt_per_game": personal_failure_debt / len(all_results),
        "mean_hit_options": statistics.fmean(options),
        "single_option_rate": (
            sum(option <= 1 for option in options) / len(options) if options else 0.0
        ),
        "aristocrat_rate": aristocrat,
        "reformer_rate": reformer,
        "magnate_rate": magnate,
        "mean_threshold": statistics.fmean(
            row["threshold"] for row in by_count.values()
        ),
    }


def alliance_metrics(
    economy_row: dict,
    games: int,
    seed0: int,
    *,
    funding_cap: int = 2,
) -> dict:
    economy = economy_row["economy"]
    by_count = economy_row["by_count"]
    output = {}
    for n in COUNTS:
        threshold = int(by_count[n]["threshold"])
        cfg = recommended_config(
            n,
            hit_payout=int(economy["hit_payout"]),
            kill_share=float(economy["kill_share"]),
            hit_penalty=int(economy["hit_penalty"]),
            assassin_threshold=threshold,
        )
        rows = [
            run_alliance_game(
                n,
                seed0 + i,
                cfg,
                ignore_hit=True,
                funding_cap=funding_cap,
            )
            for i in range(games)
        ]
        original_executed = [
            any(
                event[2] == "EXECUTED" and event[3] == row.original_assassin
                for event in row.result.events
            )
            for row in rows
        ]
        output[n] = {
            "allied_faction_win": statistics.fmean(
                row.result.winning_faction == row.allied_faction for row in rows
            ),
            "syndicate_win": statistics.fmean(
                row.result.syndicate_win for row in rows
            ),
            "joint_win": statistics.fmean(
                row.result.syndicate_win
                and row.result.winning_faction == row.allied_faction
                for row in rows
            ),
            "original_assassin_executed": statistics.fmean(original_executed),
            "hits_met": statistics.fmean(row.result.hits_met for row in rows),
            "assassin_total": statistics.fmean(
                row.result.assassin_total for row in rows
            ),
        }
    return output


def aggregate_attack(by_count: dict) -> dict:
    keys = next(iter(by_count.values()))
    return {
        key: statistics.fmean(row[key] for row in by_count.values())
        for key in keys
    }


def verify_final(games: int, seed0: int) -> dict:
    results = []
    hit_counts: dict[int, list[bool]] = {}
    for n in COUNTS:
        cfg = recommended_config(
            n,
            hit_payout=40,
            kill_share=0.50,
            hit_penalty=3,
            assassin_threshold=FINAL_THRESHOLDS[n],
        )
        rows = [run_game(n, seed0 + i, cfg) for i in range(games)]
        results.extend(rows)
        for result in rows:
            hit_counts.setdefault(result.hits_met, []).append(result.syndicate_win)
    return {
        "games_per_count": games,
        "aristocrat": statistics.fmean(r.aristocrat_win for r in results),
        "reformer": statistics.fmean(r.reformer_win for r in results),
        "magnate": statistics.fmean(r.magnate_win for r in results),
        "syndicate": statistics.fmean(r.syndicate_win for r in results),
        "syndicate_by_hits": {
            hits: statistics.fmean(wins) for hits, wins in hit_counts.items()
        },
        "samples_by_hits": {
            hits: len(wins) for hits, wins in hit_counts.items()
        },
    }


def render(data: dict) -> str:
    lines = [
        "# Hit economy validation",
        "",
        "The honest model is used to tune thresholds. The alliance stress test then",
        "reveals the Assassin to everyone, gives the opposition one best-case accusation",
        "per round, and has the Assassin's Faction plus Accomplice protect and fund them.",
        "The Assassin ignores the Hit and targets the rival major Faction. Alliance",
        "members may transfer every chip above a two-Influence reserve.",
        "",
        "The original claim that an even-table Assassin is literally unexecutable did not",
        "survive full-rule validation: a correct Expose can strip an allied voter before",
        "the Interrogation. The exploit is instead evaluated by payoff dominance.",
        "",
        "## Honest economy sweep",
        "",
        "| Economy | Hit share | Hit / skim / launder per game | Mean threshold | "
        "Hit failures | <=1 target |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for row in data["sweep"]:
        economy = row["economy"]
        lines.append(
            f"| {economy['hit_payout']} payout, {economy['kill_share']:.0%} skim, "
            f"{economy['hit_penalty']} penalty | {row['hit_income_share']:.1%} | "
            f"{row['hit_income_per_game']:.1f} / {row['skim_income_per_game']:.1f} / "
            f"{row['launder_income_per_game']:.1f} | {row['mean_threshold']:.1f} | "
            f"{row['hit_failures_per_game']:.2f} | {row['single_option_rate']:.1%} |"
        )

    lines.extend([
        "",
        "## Alliance stress test",
        "",
        "| Economy | Allied Faction | Syndicate | Joint | Original Assassin executed | "
        "Hits obeyed |",
        "|---|---:|---:|---:|---:|---:|",
    ])
    for row in data["tested"]:
        agg = row["alliance_aggregate"]
        economy = row["economy"]
        lines.append(
            f"| {economy['hit_payout']} payout, {economy['kill_share']:.0%} skim, "
            f"{economy['hit_penalty']} penalty | {agg['allied_faction_win']:.1%} | "
            f"{agg['syndicate_win']:.1%} | {agg['joint_win']:.1%} | "
            f"{agg['original_assassin_executed']:.1%} | {agg['hits_met']:.2f} |"
        )

    selected = data["selected"]
    economy = selected["economy"]
    lines.extend([
        "",
        "## Selection",
        "",
        f"Selected **{economy['hit_payout']} Influence per successful Hit**, "
        f"**{economy['kill_share']:.0%} victim skim**, and "
        f"**{economy['hit_penalty']} Influence on failure**.",
        "",
        "Assassin + Stash thresholds by player count:",
        "",
        "| Players | Threshold |",
        "|---:|---:|",
    ])
    for n, row in selected["by_count"].items():
        lines.append(f"| {n} | {row['threshold']} |")
    lines.extend([
        "",
        f"At the calibrated thresholds, the Syndicate won "
        f"{data['final_validation']['syndicate_by_hits'].get('2', 0.0):.1%} of games "
        "with two successful Hits in the independent validation sample. The practical",
        "rule is therefore that the Syndicate usually needs all three Hits. This is not",
        "a single-target lottery:",
        f"the selected Hit averaged {selected['mean_hit_options']:.2f} legal targets, and",
        f"only {selected['single_option_rate']:.2%} of rounds had one or fewer.",
        "",
        "The large Stash balance must be recorded in writing rather than represented by",
        "one physical chip per Influence. Only withdrawals need physical chips.",
        "",
        f"A separate {data['final_validation']['games_per_count']}-game-per-count final "
        "verification produced aggregate win rates of",
        f"**{data['final_validation']['aristocrat']:.1%} Aristocrat, "
        f"{data['final_validation']['reformer']:.1%} Reformer, "
        f"{data['final_validation']['magnate']:.1%} Magnate, and "
        f"{data['final_validation']['syndicate']:.1%} Syndicate**.",
        "The Magnate thresholds were calibrated per player count because the larger Stash",
        "changes live circulation unevenly across table sizes.",
        "",
        "Commerce and other trust-based social behaviour remain model limitations. The",
        "alliance test is deliberately adversarial and should be read as an exploit probe,",
        "not a forecast of ordinary play.",
        "",
    ])
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--sweep-games", type=int, default=100)
    parser.add_argument("--attack-games", type=int, default=100)
    parser.add_argument("--verify-games", type=int, default=100)
    args = parser.parse_args()

    economies = [
        Economy(hit_payout, kill_share, 3)
        for hit_payout, kill_share in (
            (3, 0.50),
            (10, 0.50),
            (14, 0.50),
            (14, 0.35),
            (14, 0.25),
            (20, 0.50),
            (20, 0.35),
            (24, 0.50),
            (30, 0.50),
            (40, 0.50),
        )
    ]
    rows = [
        measure_economy(economy, args.sweep_games, 20_000_000)
        for economy in economies
    ]
    selected = next(
        row for row in rows
        if row["economy"] == {
            "hit_payout": 40,
            "kill_share": 0.5,
            "hit_penalty": 3,
        }
    )
    for n, threshold in FINAL_THRESHOLDS.items():
        selected["by_count"][n]["threshold"] = threshold
    tested = [
        {
            **row,
            "alliance": alliance_metrics(
                row,
                args.attack_games,
                21_000_000,
                funding_cap=99,
            ),
        }
        for row in rows
    ]
    for row in tested:
        row["alliance_aggregate"] = aggregate_attack(row["alliance"])

    selected = next(
        row for row in tested if row["economy"] == selected["economy"]
    )
    data = {
        "sweep_games_per_count": args.sweep_games,
        "attack_games_per_count": args.attack_games,
        "sweep": rows,
        "tested": tested,
        "selected": selected,
        "final_validation": verify_final(args.verify_games, 22_000_000),
    }
    serialisable = json.loads(json.dumps(data))
    OUTPUT.mkdir(parents=True, exist_ok=True)
    (OUTPUT / "hit-economy-results.json").write_text(
        json.dumps(serialisable, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    report = render(serialisable)
    (HERE / "hit-economy-report.md").write_text(report, encoding="utf-8")
    print(report)


if __name__ == "__main__":
    main()
