"""Candidate economies for the recalibration, measured against the owner's gates.

Nothing here changes the published ruleset. Every candidate is a set of Config
overrides applied on top of `recommended_config`, so the default game is untouched.

Thresholds are never hand-picked: for each candidate the Magnate and Syndicate
thresholds are re-derived from that candidate's own measured distribution, because a
threshold copied from a different economy measures nothing.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass, field
import json
import math
from pathlib import Path
import statistics

from .engine import ASSASSIN, ACCOMPLICE, Game, run_game
from .exploits import run_alliance_game
from .final import recommended_config
from .tune import quantile_threshold

HERE = Path(__file__).resolve().parent
OUTPUT = HERE / "output"
COUNTS = tuple(range(8, 16))

TARGET_MAGNATE = 0.35
TARGET_SYNDICATE = 0.33

# The bargaining economist's discount: nominal faction liquidity is not mobilisable.
# Coordination, free-riding, competing goals and non-binding agreements all bite.
EFFECTIVE_BRIBE_FRACTION = 0.5


@dataclass(frozen=True)
class Candidate:
    key: str
    name: str
    philosophy: str
    overrides: dict = field(default_factory=dict)
    tunes_syndicate: bool = True
    notes: str = ""


CANDIDATES: tuple[Candidate, ...] = (
    Candidate(
        key="baseline",
        name="Baseline (published today)",
        philosophy="What is in the rulebook right now.",
        overrides={},
        notes="Reference point only.",
    ),
    Candidate(
        key="A",
        name="A — Redenomination",
        philosophy="Shrink every value toward the integer floor. Change nothing structural.",
        overrides=dict(
            hit_payout=10,
            starting_influence=3,
            stipend=2,
            motive_reward=3,
            ambition_reward=5,
            guilty_vote_reward=3,
            vote_cost=2,
        ),
        notes="Smallest possible rule change: numbers only, same structure.",
    ),
    Candidate(
        key="B",
        name="B — Closed loop",
        philosophy="Stop minting. Fund the Guilty-vote reward from the executed player's estate.",
        overrides=dict(
            hit_payout=10,
            starting_influence=3,
            stipend=2,
            motive_reward=3,
            ambition_reward=5,
            guilty_vote_reward=3,
            vote_cost=2,
            guilty_reward_source="estate",
        ),
        notes="Rewards become variable rather than a fixed promise.",
    ),
    Candidate(
        key="C",
        name="C — Caps and sinks",
        philosophy="Retire the estate into the Bank instead of concentrating it on one heir.",
        overrides=dict(
            hit_payout=10,
            starting_influence=3,
            stipend=2,
            motive_reward=3,
            ambition_reward=5,
            guilty_vote_reward=3,
            vote_cost=2,
            bequest_mode="bank",
        ),
        notes="Council preferred escheat to the Bank over splitting among all living players.",
    ),
    Candidate(
        key="D",
        name="D — Decoupled Syndicate",
        philosophy="The Syndicate wins on Hits completed plus a Stash that only Hits can fill. Personal hoarding no longer counts.",
        overrides=dict(
            hit_payout=10,
            starting_influence=3,
            stipend=2,
            motive_reward=3,
            ambition_reward=5,
            guilty_vote_reward=3,
            vote_cost=2,
            bequest_mode="bank",
            syndicate_victory_mode="hits",
            syndicate_hits_required=2,
            syndicate_stash_minimum=40,
        ),
        tunes_syndicate=False,
        notes="Council rejected the naive 'all three Hits'; this is 2 of 3 plus a Stash floor.",
    ),
    Candidate(
        key="E",
        name="E — Cheap Hit, live bribe",
        philosophy="Price the Hit so a Faction can actually afford to buy it off, and accept what that costs elsewhere.",
        overrides=dict(
            hit_payout=6,
            starting_influence=3,
            stipend=2,
            motive_reward=3,
            ambition_reward=5,
            guilty_vote_reward=3,
            vote_cost=2,
            bequest_mode="bank",
        ),
        notes="Serves the stated core intent most directly; the report shows what it costs.",
    ),
)


class Probe(Game):
    """Adds the measurements the gates need but the engine does not carry."""

    def private_phase(self) -> None:
        faction = self.players[self.assassin_seat].faction
        capacity = sum(
            max(0, p.influence) for p in self.living()
            if p.faction == faction
            and p.seat not in (self.assassin_seat, self.accomplice_seat)
        )
        self.bribe_capacity = getattr(self, "bribe_capacity", [])
        self.bribe_capacity.append(capacity)
        living = [max(0, p.influence) for p in self.living()]
        self.median_wealth = getattr(self, "median_wealth", [])
        if living:
            self.median_wealth.append(statistics.median(living))
        super().private_phase()


def percentile(values: list[int], q: float) -> int:
    if not values:
        return 0
    ordered = sorted(values)
    index = min(len(ordered) - 1, int(math.ceil(q * len(ordered))) - 1)
    return ordered[index]


def config_for(candidate: Candidate, n: int, **extra) -> object:
    overrides = dict(candidate.overrides)
    overrides.update(extra)
    return recommended_config(n, **overrides)


def tune_thresholds(candidate: Candidate, games: int, seed0: int) -> dict[int, dict]:
    """Re-derive both thresholds from this candidate's own distribution."""
    out: dict[int, dict] = {}
    for n in COUNTS:
        cfg = config_for(candidate, n, magnate_threshold=1, assassin_threshold=1)
        rows = [run_game(n, seed0 + i, cfg) for i in range(games)]
        magnate = quantile_threshold([r.magnate_total for r in rows], TARGET_MAGNATE)
        if candidate.tunes_syndicate:
            syndicate = quantile_threshold(
                [r.assassin_total for r in rows], TARGET_SYNDICATE)
        else:
            syndicate = 0
        out[n] = {"magnate": max(1, magnate), "syndicate": max(1, syndicate)}
    return out


def measure(candidate: Candidate, thresholds: dict, games: int, seed0: int) -> dict:
    rows = []
    caps: list[int] = []
    medians: list[float] = []
    for n in COUNTS:
        cfg = config_for(
            candidate, n,
            magnate_threshold=thresholds[n]["magnate"],
            assassin_threshold=thresholds[n]["syndicate"],
        )
        for i in range(games):
            game = Probe(n, seed0 + i, cfg)
            result = game.run()
            rows.append((n, result))
            caps.extend(getattr(game, "bribe_capacity", []))
            medians.extend(getattr(game, "median_wealth", []))

    by_count = {}
    for n in COUNTS:
        subset = [r for c, r in rows if c == n]
        by_count[n] = {
            "player_chips_p90": percentile(
                [r.peak_player_chips for r in subset], 0.90),
            "player_chips_p99": percentile(
                [r.peak_player_chips for r in subset], 0.99),
            "stash_p90": percentile([r.peak_stash for r in subset], 0.90),
            "richest_p90": percentile(
                [r.peak_single_holding for r in subset], 0.90),
            "magnate_threshold": thresholds[n]["magnate"],
            "syndicate_threshold": thresholds[n]["syndicate"],
        }

    results = [r for _, r in rows]
    player_chips = [r.peak_player_chips for r in results]
    stash = [r.peak_stash for r in results]
    richest = [r.peak_single_holding for r in results]
    hit_value = config_for(candidate, 13).hit_payout
    capacity = statistics.fmean(caps) if caps else 0.0
    median_wealth = statistics.fmean(medians) if medians else 0.0
    effective = capacity * EFFECTIVE_BRIBE_FRACTION

    return {
        "player_chips_p50": percentile(player_chips, 0.50),
        "player_chips_p90": percentile(player_chips, 0.90),
        "player_chips_p99": percentile(player_chips, 0.99),
        "player_chips_max": max(player_chips),
        "stash_p90": percentile(stash, 0.90),
        "stash_max": max(stash),
        "richest_p90": percentile(richest, 0.90),
        "richest_p99": percentile(richest, 0.99),
        "richest_max": max(richest),
        "bank_injected": statistics.fmean(r.bank_injected for r in results),
        "player_circulated": statistics.fmean(
            r.player_circulated for r in results),
        "aristocrat": statistics.fmean(r.aristocrat_win for r in results),
        "reformer": statistics.fmean(r.reformer_win for r in results),
        "magnate": statistics.fmean(r.magnate_win for r in results),
        "syndicate": statistics.fmean(r.syndicate_win for r in results),
        "votes_decisive": statistics.fmean(r.votes_decisive for r in results),
        "hits_met": statistics.fmean(r.hits_met for r in results),
        "bribe_capacity": capacity,
        "effective_bribe_capacity": effective,
        "median_wealth": median_wealth,
        "hit_value": hit_value,
        "hit_over_capacity": hit_value / capacity if capacity else 0.0,
        "hit_over_effective": hit_value / effective if effective else 0.0,
        "reward_over_median": (
            config_for(candidate, 13).guilty_vote_reward / median_wealth
            if median_wealth else 0.0
        ),
        "concentration": (
            percentile(richest, 0.90) / median_wealth if median_wealth else 0.0
        ),
        "by_count": by_count,
    }


def attack(candidate: Candidate, thresholds: dict, games: int, seed0: int) -> dict:
    allied = []
    syndicate = []
    executed = []
    for n in COUNTS:
        cfg = config_for(
            candidate, n,
            magnate_threshold=thresholds[n]["magnate"],
            assassin_threshold=thresholds[n]["syndicate"],
        )
        for i in range(games):
            row = run_alliance_game(n, seed0 + i, cfg, ignore_hit=True,
                                    funding_cap=99)
            allied.append(row.result.winning_faction == row.allied_faction)
            syndicate.append(row.result.syndicate_win)
            executed.append(any(
                event[2] == "EXECUTED" and event[3] == row.original_assassin
                for event in row.result.events))
    return {
        "allied_faction_win": statistics.fmean(allied),
        "syndicate_win": statistics.fmean(syndicate),
        "assassin_executed": statistics.fmean(executed),
    }


def gate_status(row: dict, attack_row: dict) -> dict[str, bool]:
    return {
        "player_pool_180": row["player_chips_p90"] <= 180,
        "stash_pool_60": row["stash_p90"] <= 60,
        "holding_25": row["richest_p90"] <= 25,
        "median_5_12": 5 <= row["median_wealth"] <= 12,
        # The Council split on whether a Faction's nominal liquidity is mobilisable,
        # so both readings are reported rather than one being quietly chosen.
        "bribe_live_nominal": 0.6 <= row["hit_over_capacity"] <= 1.0,
        "bribe_live_effective": 0.6 <= row["hit_over_effective"] <= 1.0,
        "reward_appetite": row["reward_over_median"] >= 0.40,
        "votes_matter": row["votes_decisive"] >= 0.20,
        "faction_balance": all(
            0.42 <= row[key] <= 0.55 for key in ("aristocrat", "reformer")),
        "magnate_band": 0.30 <= row["magnate"] <= 0.40,
        "syndicate_band": 0.28 <= row["syndicate"] <= 0.38,
        # Serving an ally instead of the Hit must not pay better than playing straight.
        "alliance_unprofitable": (
            attack_row["syndicate_win"] <= row["syndicate"] + 0.05),
    }


def run(games: int, tune_games: int, attack_games: int, seed0: int) -> dict:
    data = {}
    for candidate in CANDIDATES:
        if candidate.key == "baseline":
            thresholds = {
                n: {
                    "magnate": recommended_config(n).magnate_threshold,
                    "syndicate": recommended_config(n).assassin_threshold,
                }
                for n in COUNTS
            }
        else:
            thresholds = tune_thresholds(candidate, tune_games, seed0)
        row = measure(candidate, thresholds, games, seed0 + 500_000)
        attack_row = attack(candidate, thresholds, attack_games, seed0 + 900_000)
        data[candidate.key] = {
            "name": candidate.name,
            "philosophy": candidate.philosophy,
            "notes": candidate.notes,
            "overrides": candidate.overrides,
            "thresholds": {str(k): v for k, v in thresholds.items()},
            "measurements": row,
            "alliance": attack_row,
            "gates": gate_status(row, attack_row),
        }
    return data


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--games", type=int, default=120)
    parser.add_argument("--tune-games", type=int, default=200)
    parser.add_argument("--attack-games", type=int, default=60)
    parser.add_argument("--seed", type=int, default=61_000_000)
    args = parser.parse_args()

    data = run(args.games, args.tune_games, args.attack_games, args.seed)
    OUTPUT.mkdir(parents=True, exist_ok=True)
    (OUTPUT / "economy-candidates.json").write_text(
        json.dumps(data, indent=2, sort_keys=True), encoding="utf-8")

    for key, row in data.items():
        m = row["measurements"]
        passed = sum(1 for v in row["gates"].values() if v)
        total = len(row["gates"])
        print(f"\n=== {row['name']}  ({passed}/{total} gates) ===")
        print(f"  chips: player p90 {m['player_chips_p90']:>4} "
              f"p99 {m['player_chips_p99']:>4} | stash p90 {m['stash_p90']:>4} "
              f"| richest p90 {m['richest_p90']:>3} (median {m['median_wealth']:.1f})")
        print(f"  money: injected {m['bank_injected']:>5.0f}  "
              f"circulated {m['player_circulated']:>5.0f}")
        print(f"  bribe: hit {m['hit_value']} / nominal {m['bribe_capacity']:.1f} "
              f"= {m['hit_over_capacity']:.2f} | effective "
              f"{m['effective_bribe_capacity']:.1f} = {m['hit_over_effective']:.2f}")
        print(f"  wins:  A {m['aristocrat']:.0%}  R {m['reformer']:.0%}  "
              f"M {m['magnate']:.0%}  S {m['syndicate']:.0%}  "
              f"votes decisive {m['votes_decisive']:.0%}")
        print(f"  attack: allied {row['alliance']['allied_faction_win']:.0%}  "
              f"syndicate {row['alliance']['syndicate_win']:.0%}")
        failed = [k for k, v in row["gates"].items() if not v]
        if failed:
            print(f"  FAILS: {', '.join(failed)}")


if __name__ == "__main__":
    main()
