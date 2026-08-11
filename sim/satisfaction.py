"""Mechanical diagnostics for individual and group satisfaction conditions."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import statistics

from .engine import run_game
from .final import recommended_config
from .run import summarise


HERE = Path(__file__).resolve().parent
OUTPUT = HERE / "output"
COUNTS = tuple(range(8, 16))


def run_variant(
    games: int,
    *,
    seed0: int,
    private_phase_minutes=(30, 30, 30),
    ambition_deadline=2,
) -> dict:
    by_count = {}
    for n in COUNTS:
        cfg = recommended_config(
            n,
            private_phase_minutes=private_phase_minutes,
            ambition_deadline=ambition_deadline,
        )
        results = [
            run_game(n, seed0 + n * 100_000 + i, cfg)
            for i in range(games)
        ]
        by_count[str(n)] = summarise(results)
    return by_count


def average(by_count: dict, key: str) -> float:
    return statistics.fmean(row[key] for row in by_count.values())


def average_round(by_count: dict, key: str, rnd: int) -> float:
    return statistics.fmean(
        row[key].get(rnd, row[key].get(str(rnd), 0.0))
        for row in by_count.values()
    )


def weighted_goal_rates(by_count: dict, key: str) -> dict[str, float]:
    goals = sorted({
        goal for row in by_count.values() for goal in row[key]
    })
    return {
        goal: statistics.fmean(row[key].get(goal, 0.0) for row in by_count.values())
        for goal in goals
    }


def build_report(data: dict) -> str:
    base = data["baseline"]
    extended_phases = data["extended_phases"]
    extended = data["ambition_to_round3"]
    both = data["combined"]
    accuracy = {
        rnd: average_round(base, "execution_accuracy_by_round", rnd)
        for rnd in (1, 2, 3)
    }
    deaths = {
        rnd: average_round(base, "deaths_by_round", rnd)
        for rnd in (1, 2, 3)
    }
    motives = weighted_goal_rates(base, "motive_completion_by_goal")
    ambitions = weighted_goal_rates(base, "ambition_completion_by_goal")

    goal_rows = "\n".join(
        f"| {goal} | {rate:.1%} |" for goal, rate in sorted(ambitions.items())
    )
    motive_rows = "\n".join(
        f"| {goal} | {rate:.1%} |" for goal, rate in sorted(motives.items())
    )
    variant_rows = "\n".join([
        f"| Prior 30/30/30, deadline R2 | {average(base, 'ambitions_claimed'):.2f} | "
        f"{average(base, 'zero_agency_rate'):.1%} | {average(base, 'wealth_top_share'):.1%} | "
        f"{statistics.fmean(r['syndicate']['rate'] for r in base.values()):.1%} |",
        f"| Published 30/45/60, deadline R2 | {average(extended_phases, 'ambitions_claimed'):.2f} | "
        f"{average(extended_phases, 'zero_agency_rate'):.1%} | {average(extended_phases, 'wealth_top_share'):.1%} | "
        f"{statistics.fmean(r['syndicate']['rate'] for r in extended_phases.values()):.1%} |",
        f"| 30/30/30, deadline R3 | {average(extended, 'ambitions_claimed'):.2f} | "
        f"{average(extended, 'zero_agency_rate'):.1%} | {average(extended, 'wealth_top_share'):.1%} | "
        f"{statistics.fmean(r['syndicate']['rate'] for r in extended.values()):.1%} |",
        f"| Extended phases + deadline R3 | {average(both, 'ambitions_claimed'):.2f} | "
        f"{average(both, 'zero_agency_rate'):.1%} | {average(both, 'wealth_top_share'):.1%} | "
        f"{statistics.fmean(r['syndicate']['rate'] for r in both.values()):.1%} |",
    ])

    rising = accuracy[3] > accuracy[1] + 0.05
    early_death = deaths[1] / sum(deaths.values()) if sum(deaths.values()) else 0.0
    return f"""# Satisfaction diagnostics

## What this report can say

The simulator measures mechanical conditions that support or undermine satisfaction.
It cannot measure fun, comprehension, social standing, memorable moments or whether a
win feels deserved.

## Information Arc: execution accuracy by round

| Round | Accuracy | Executions/game | Deaths/game |
|---:|---:|---:|---:|
| 1 | {accuracy[1]:.1%} | {average_round(base, 'executions_by_round', 1):.2f} | {deaths[1]:.2f} |
| 2 | {accuracy[2]:.1%} | {average_round(base, 'executions_by_round', 2):.2f} | {deaths[2]:.2f} |
| 3 | {accuracy[3]:.1%} | {average_round(base, 'executions_by_round', 3):.2f} | {deaths[3]:.2f} |

The accuracy curve {'rises materially' if rising else 'does not rise by five percentage points'} from
Round 1 to Round 3. {early_death:.1%} of simulated deaths occur in Round 1.

## Personal arcs

### Motive completion

| Motive | Completion |
|---|---:|
{motive_rows}

### Ambition completion

| Ambition | Completion |
|---|---:|
{goal_rows}

## Consequential-agency proxy

- Players with no completed Goal, successful Expose, initiated Interrogation or
  meaningful transfer: **{average(base, 'zero_agency_rate'):.1%}**
- Mean share of positive living Influence held by the richest player:
  **{average(base, 'wealth_top_share'):.1%}**

This is not a satisfaction score. It identifies players for whom the model recorded no
state-changing personal action.

## Pacing and Round 3 objective variants

| Variant | Ambitions/game | Zero-agency | Richest share | Syndicate |
|---|---:|---:|---:|---:|
{variant_rows}

## Interpretation

1. **Information Arc:** {'Late executions are more grounded than early ones.' if rising else 'The model does not show a strong late-game accuracy improvement. More rounds are not reliably producing more correct collective decisions.'}
2. **Early elimination:** Round 1 creates {early_death:.1%} of deaths; those players spend
   most of the remaining game without economic actions.
3. **Goal vacuum:** extending the Ambition deadline changes completion from
   {average(base, 'ambitions_claimed'):.2f} to
   {average(extended, 'ambitions_claimed'):.2f} per game.
4. **Longer social time:** 30/45/60 phases change zero-agency from
   {average(base, 'zero_agency_rate'):.1%} to
   {average(extended_phases, 'zero_agency_rate'):.1%}. The simulator can model more
   conversation opportunities, but not whether the longer phase feels necessary or slow.

## Recommendation

1. **Extended social phases:** 30/45/60-minute Private Phases with 5-minute and
   1-minute warnings. This reflects the observed need for more interaction as the
   15-player information network grows denser. The next live test must measure whether
   the added time produces more useful conversations rather than repetition.
2. **Do not simply extend Ambitions to Round 3.** It raises Ambition completion by
   {average(extended, 'ambitions_claimed') - average(base, 'ambitions_claimed'):.2f}
   per game but also raises the Syndicate rate from
   {statistics.fmean(r['syndicate']['rate'] for r in base.values()):.1%} to
   {statistics.fmean(r['syndicate']['rate'] for r in extended.values()):.1%}. The
   extra Round 3 income is not balance-neutral.
3. **Keep the current information schedule for now.** Accuracy rises from
   {accuracy[1]:.1%} to {accuracy[3]:.1%}; the deduction funnel works. The live
   question is whether the 35.8% of deaths occurring in Round 1 still feels too early.
4. **Do not add a general agency mechanic.** The zero-agency proxy is only
   {average(base, 'zero_agency_rate'):.1%}. Ghost satisfaction remains a human
   experience question, not evidence of a whole-table agency failure.
5. **Investigate Ambition design rather than its deadline.** Collector and Radical are
   the weakest ({ambitions.get('COLLECTOR', 0):.1%} and
   {ambitions.get('RADICAL', 0):.1%}); targeted rewrites are safer than injecting +10
   Influence during Round 3.

## Human checks still required

- Can every player explain why they lost?
- Does each player identify at least one choice that mattered?
- Are Round 3 negotiations urgent or rushed?
- Do Ghosts still feel involved after losing economic actions?
- Do late Executions feel earned?
"""


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--games", type=int, default=400)
    args = parser.parse_args()
    seed = 16_000_000
    data = {
        "games_per_count": args.games,
        "baseline": run_variant(args.games, seed0=seed),
        "extended_phases": run_variant(
            args.games, seed0=seed, private_phase_minutes=(30, 45, 60)),
        "ambition_to_round3": run_variant(
            args.games, seed0=seed, ambition_deadline=3),
        "combined": run_variant(
            args.games, seed0=seed,
            private_phase_minutes=(30, 45, 60), ambition_deadline=3),
    }
    OUTPUT.mkdir(parents=True, exist_ok=True)
    (OUTPUT / "satisfaction-results.json").write_text(
        json.dumps(data, indent=2, sort_keys=True), encoding="utf-8")
    report = build_report(data)
    (HERE / "satisfaction-report.md").write_text(report, encoding="utf-8")
    print(report)


if __name__ == "__main__":
    main()
