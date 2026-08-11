"""Tier 4 removal probes for mechanics the simulator explicitly represents."""

from __future__ import annotations

import argparse
import os
import statistics

from .engine import run_game
from .final import recommended_config
from .run import summarise

COUNTS = [10, 11, 12, 13, 14, 15]

# These are removal or weakening probes, not recommendations.
PROBES = {
    "No stipends": {"stipend": 0},
    "No Hit system": {"hits_enabled": False},
    "No ordinary private transfers": {"private_transfers_enabled": False},
    "No Goal completion or payouts": {"goals_enabled": False},
    "No Auction": {"auction_enabled": False},
    "No Expose action": {"expose_enabled": False},
    "No Interrogation action": {"interrogation_enabled": False},
    "No Guilty-vote stakes": {"guilty_vote_reward": 0,
                              "guilty_vote_penalty": 0},
    "No forced Evidence disclosure": {"evidence_disclosure_enabled": False},
    "No Ghost question": {"ghost_mode": "off"},
    "One lifetime Ghost vote": {"ghost_vote_mode": "lifetime"},
    "No assassination payment prerequisite": {"kill_tell_required": False},
    "Same-round kill payment only": {"kill_tell_scope": "round"},
    "Assassin alone pays kill tell": {"tell_by_either": False},
    "No Laundering": {"launder_cap": 0},
    "One-way Stash": {"stash_withdraw_cap": 0},
    "No death skim": {"kill_share": 0.0, "execution_share": 0.0},
    "No Promotion": {"promotion_enabled": False},
    "No successor lead": {"promotion_reveals_evidence": False},
    "Two Candidates": {"candidate_count": 2},
    "Reveal before nominations": {"reveal_after_nomination": False},
    "No Reveal": {"reveal_enabled": False},
    "No Final vote buying": {"vote_cost": 999},
    "No Reveal vote buying": {"reveal_vote_cost": 999},
    "No Bankruptcy consequences": {"bankruptcy_enabled": False},
    "Open Factions": {"ally_hint": "open"},
    "Repeat Expose allowed": {"expose_once": False},
    "Stash not split on wipeout": {"confiscate_on_wipeout": False},
}


def run(overrides: dict, games: int, seed0: int) -> list:
    results = []
    for n in COUNTS:
        cfg = recommended_config(n, **overrides)
        results.extend(run_game(n, seed0 + n * 100_000 + seed, cfg)
                       for seed in range(games))
    return results


def outcome_key(result) -> tuple:
    return (result.winning_faction, result.magnate_win, result.syndicate_win,
            tuple(result.personal_wins.values()))


def metrics(results: list) -> dict:
    s = summarise(results)
    return {
        "a": s["aristocrat"]["rate"],
        "r": s["reformer"]["rate"],
        "m": s["magnate"]["rate"],
        "s": s["syndicate"]["rate"],
        "deaths": s["deaths"],
        "interrogations": s["interrogations"],
        "bankruptcies": s["bankruptcies"],
        "motives": s["motives_claimed"],
        "ambitions": s["ambitions_claimed"],
        "circulating": s["circulating"],
    }


def render(rows: list[tuple[str, dict, float]], games: int) -> str:
    total = games * len(COUNTS)
    lines = [
        "# The Dark Council — Tier 4 Simulator Removal Probe",
        "",
        f"**Method:** paired seeds, {games:,} games per player count for counts 10–15 "
        f"({total:,} games per probe).",
        "",
        "> A null result means the simulator may not represent the rule's human purpose. "
        "It never authorises a cut. Bankruptcy is the explicit proof case: the model "
        "does not allow proxy-paying from zero, so it cannot reproduce the live exploit.",
        "",
        "| Probe | Outcomes changed | A | R | Magnate | Syndicate | Deaths | "
        "Interrogations | Debtors | Motives | Ambitions | Circulating |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for name, m, changed in rows:
        lines.append(
            f"| {name} | {changed:.1%} | {m['a']:.1%} | {m['r']:.1%} | "
            f"{m['m']:.1%} | {m['s']:.1%} | {m['deaths']:.2f} | "
            f"{m['interrogations']:.2f} | {m['bankruptcies']:.2f} | "
            f"{m['motives']:.2f} | {m['ambitions']:.2f} | {m['circulating']:.1f} |")
    lines.extend([
        "",
        "## Coverage limits",
        "",
        "The simulator does not faithfully remove or evaluate: physical enforcement, "
        "teaching text, private-room logistics, charisma, bluff quality, memory, exact "
        "Evidence wording, whether Goals create stories, whether a Magnate feels courted, "
        "or whether death feels engaging. Those remain Tier 1/Tier 3/live-test questions.",
        "",
        "Goal removal disables completion and rewards but simulated players still carry "
        "goal-shaped behavioural tendencies. No-private-transfer keeps the separate kill "
        "tell pathway so assassination remains possible. These probes are therefore "
        "bounded perturbations, not alternate complete games.",
    ])
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--games", type=int, default=300,
                        help="games per player count and probe")
    parser.add_argument("--output", help="optional Markdown output path")
    args = parser.parse_args()

    seed0 = 1_500_000
    baseline = run({}, args.games, seed0)
    rows = [("Current rules", metrics(baseline), 0.0)]
    for name, overrides in PROBES.items():
        results = run(overrides, args.games, seed0)
        changed = statistics.fmean(
            outcome_key(a) != outcome_key(b) for a, b in zip(baseline, results))
        rows.append((name, metrics(results), changed))

    report = render(rows, args.games)
    if args.output:
        os.makedirs(os.path.dirname(os.path.abspath(args.output)), exist_ok=True)
        with open(args.output, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(report)
    print(report)


if __name__ == "__main__":
    main()
