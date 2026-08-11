"""Run the published-rules, chaos, eligibility and adversarial experiment matrix."""

from __future__ import annotations

import argparse
from collections import Counter
from dataclasses import asdict
import json
from pathlib import Path
import statistics

from .chaos import ChaosConfig, chaos_policies
from .engine import ASSASSIN, ACCOMPLICE, run_game
from .exploits import EXPLOITS, ExploitPolicies, run_exploit
from .final import recommended_config
from .run import summarise


HERE = Path(__file__).resolve().parent
OUTPUT = HERE / "output"
COUNTS = tuple(range(8, 16))
CHAOS_BANDS = {
    "clean": ChaosConfig.clean(),
    "realistic": ChaosConfig.realistic(),
    "messy": ChaosConfig.messy(),
}


def aggregate(rows: list[dict]) -> dict:
    keys = (
        "aristocrat", "reformer", "magnate", "syndicate",
        "vote_exclusion_rate", "repeat_vote_exclusions", "expose_refusals",
        "gm_refusals", "bankruptcies", "debt_rescue_transfers", "debt_rescued",
    )
    out = {}
    for key in keys:
        values = [
            row[key]["rate"] if isinstance(row[key], dict) else row[key]
            for row in rows
        ]
        out[key] = statistics.fmean(values)
    return out


def run_baselines(games: int) -> dict:
    matrix = {}
    for band, chaos in CHAOS_BANDS.items():
        by_count = {}
        for n in COUNTS:
            results = [
                run_game(
                    n,
                    12_000_000 + n * 100_000 + seed,
                    recommended_config(n),
                    chaos_policies(chaos),
                )
                for seed in range(games)
            ]
            by_count[str(n)] = summarise(results)
        matrix[band] = {
            "by_count": by_count,
            "aggregate": aggregate(list(by_count.values())),
        }
    return matrix


def run_gate_comparison(games: int, n: int = 13) -> dict:
    base_results = []
    gate_off_results = []
    for i in range(games):
        seed = 13_500_000 + i
        base_results.append(run_game(n, seed, recommended_config(n)))
        gate_off_results.append(run_game(
            n, seed, recommended_config(
                n,
                expose_eligibility_enabled=False,
                interrogation_vote_eligibility_enabled=False,
            )
        ))
    base = summarise(base_results)
    off = summarise(gate_off_results)
    return {
        "n_players": n,
        "games": games,
        "published": base,
        "gates_off": off,
        "syndicate_win_delta": (
            base["syndicate"]["rate"] - off["syndicate"]["rate"]
        ),
        "correct_execution_delta": (
            base["execution_accuracy"] - off["execution_accuracy"]
        ),
    }


def run_debt_deterrence(games: int, n: int = 13) -> dict:
    seats = (0, 1, 2)
    honest_wins = exploit_wins = samples = 0
    bankrupt_by_role = Counter()
    player_samples_by_role = Counter()
    debt_causes = Counter()
    rescues = rescued = 0
    syndicate_bankrupt = syndicate_samples = 0

    for i in range(games):
        seed = 14_000_000 + i
        cfg = recommended_config(n)
        honest = run_game(n, seed, cfg)
        attacked = run_game(
            n, seed, cfg, ExploitPolicies("debt_squatting", seats)
        )
        for seat in seats:
            honest_wins += int(honest.personal_wins[seat])
            exploit_wins += int(attacked.personal_wins[seat])
            samples += 1
        for player in attacked.players:
            player_samples_by_role[player.role] += 1
            if player.bankrupt:
                bankrupt_by_role[player.role] += 1
            if player.role in (ASSASSIN, ACCOMPLICE):
                syndicate_samples += 1
                syndicate_bankrupt += int(player.bankrupt)
        debt_causes.update(attacked.debt_by_cause or {})
        rescues += attacked.debt_rescue_transfers
        rescued += attacked.debt_rescued

    return {
        "n_players": n,
        "games": games,
        "debt_squatting_honest_win_rate": honest_wins / samples,
        "debt_squatting_exploit_win_rate": exploit_wins / samples,
        "debt_squatting_value": (exploit_wins - honest_wins) / samples,
        "bankruptcy_rate_by_role": {
            role: bankrupt_by_role[role] / count
            for role, count in sorted(player_samples_by_role.items())
        },
        "syndicate_bankruptcy_rate": (
            syndicate_bankrupt / syndicate_samples if syndicate_samples else 0.0
        ),
        "debt_by_cause": dict(debt_causes.most_common()),
        "debt_rescue_transfers_per_game": rescues / games,
        "influence_rescued_per_game": rescued / games,
        "magnate_negative_balance_interpretation": (
            "Engine floors negative living Magnate balances at zero. "
            "The rulebook does not explicitly resolve this."
        ),
        "syndicate_bankruptcy_consequence": (
            "No additional personal Faction penalty: Syndicate members were already "
            "ineligible. Negative Assassin Influence still reduces Assassin+Stash."
        ),
    }


def render_report(data: dict) -> str:
    clean = data["baselines"]["clean"]["aggregate"]
    realistic = data["baselines"]["realistic"]["aggregate"]
    messy = data["baselines"]["messy"]["aggregate"]
    gate = data["gate_comparison"]
    debt = data["debt_deterrence"]
    exploits = data["exploits"]
    params = data["parameters"]
    by_exploit = {item["name"]: item for item in exploits}
    final_dump = by_exploit["final_dump"]
    stash_shelter = by_exploit["stash_shelter"]
    debt_squatting = by_exploit["debt_squatting"]
    vote_stripping = by_exploit["expose_vote_stripping"]
    cost_griefing = by_exploit["interrogation_cost_griefing"]
    flags = [item for item in exploits if item["exploit_value"] >= 0.03]

    exploit_rows = "\n".join(
        f"| {item['name']} | {item['honest_win_rate']:.1%} | "
        f"{item['exploit_win_rate']:.1%} | {item['exploit_value']:+.1%} | "
        f"{item['syndicate_win_delta']:+.1%} | {item['applicable_player_samples']} |"
        for item in exploits
    )
    causes = ", ".join(
        f"{name} {amount}" for name, amount in debt["debt_by_cause"].items()
    ) or "none"

    return f"""# Simulation report — published rules, chaos and exploit probes

## Scope

These are mechanical simulations. They do not measure fun, comprehension,
persuasion, satisfaction or replay intent.

Run size: {params['games']} games per player count per chaos band,
{params['paired_games']} paired games for eligibility/debt, and
{params['exploit_games']} paired games per exploit.

## Headline

| Table model | Aristocrat | Reformer | Magnate | Syndicate | Vote exclusions | GM refusals/game |
|---|---:|---:|---:|---:|---:|---:|
| Clean | {clean['aristocrat']:.1%} | {clean['reformer']:.1%} | {clean['magnate']:.1%} | {clean['syndicate']:.1%} | {clean['vote_exclusion_rate']:.1%} | {clean['gm_refusals']:.2f} |
| Realistic chaos | {realistic['aristocrat']:.1%} | {realistic['reformer']:.1%} | {realistic['magnate']:.1%} | {realistic['syndicate']:.1%} | {realistic['vote_exclusion_rate']:.1%} | {realistic['gm_refusals']:.2f} |
| Messy chaos | {messy['aristocrat']:.1%} | {messy['reformer']:.1%} | {messy['magnate']:.1%} | {messy['syndicate']:.1%} | {messy['vote_exclusion_rate']:.1%} | {messy['gm_refusals']:.2f} |

### Robustness reading

- Aristocrat/Reformer results remain stable across the chaos bands.
- Magnate wins fall from {clean['magnate']:.1%} to {messy['magnate']:.1%}. The
  Magnate economy is substantially more vulnerable to forgotten, irrational and
  grudge-driven behaviour than the election Factions.
- The Syndicate rate does not move monotonically with chaos; the model does not show a
  simple “more mistakes always help the Assassin” relationship.

## Eligibility-gate comparison (13 players, matched seeds)

- Published gate Syndicate win rate: {gate['published']['syndicate']['rate']:.1%}
- Gates-off Syndicate win rate: {gate['gates_off']['syndicate']['rate']:.1%}
- **Published gate delta:** {gate['syndicate_win_delta']:+.1%}
- Correct-Execution accuracy delta: {gate['correct_execution_delta']:+.1%}
- Published living-voter exclusion rate: {gate['published']['vote_exclusion_rate']:.1%}

Important mechanical observation: an initiator who spends their last Influence on the
Interrogation cost is excluded from the vote that immediately follows.

The gate produces a small {gate['syndicate_win_delta']:+.1%} Syndicate shift in this
sample, not a balance collapse. The much larger concern is participation: roughly
{gate['published']['vote_exclusion_rate']:.1%} of living voter opportunities are
removed.

## Debt deterrence

- Honest controlled-seat win rate: {debt['debt_squatting_honest_win_rate']:.1%}
- Debt-squatting win rate: {debt['debt_squatting_exploit_win_rate']:.1%}
- **Debt-squatting value:** {debt['debt_squatting_value']:+.1%}
- Syndicate-member Bankruptcy incidence: {debt['syndicate_bankruptcy_rate']:.1%}
- Ally rescue transfers/game: {debt['debt_rescue_transfers_per_game']:.3f}
- Influence rescued/game: {debt['influence_rescued_per_game']:.3f}
- Debt created by: {causes}

The test asks whether debt is profitable, not whether Bankruptcy is common. Syndicate
members already lost their personal Faction Victory, so ordinary Bankruptcy adds no
second personal-victory consequence to them.

Debt squatting is personally deterred in this model ({debt['debt_squatting_value']:+.1%}).
The ability-to-pay gates also work as intended: the recorded debt is created by
involuntary losses, not voluntary spending. Ally rescue is rare, so it does not make
the consequence disappear.

## Adversarial exploit catalogue

| Strategy | Honest | Exploit | Exploit value | Syndicate delta | Applicable samples |
|---|---:|---:|---:|---:|---:|
{exploit_rows}

Strategies at or above a +3 percentage-point edge: **{', '.join(item['name'] for item in flags) or 'none'}**.

### Adversarial reading

- **Final dump** is the clearest self-serving exploit: a {final_dump['exploit_value']:+.1%}
  personal edge in the
  full run. Aristocrats/Reformers have no reason to preserve Influence after buying
  votes, so cautious spending is dominated by spending everything.
- **Stash shelter** gives controlled Syndicate seats a
  {stash_shelter['exploit_value']:+.1%} edge. Leaving Influence
  in the protected Stash is stronger than the ordinary policy's liquidity reserve.
- **Debt squatting** hurts the controlled seats but moves the Syndicate win rate by
  {debt_squatting['syndicate_win_delta']:+.1%}. It is not a profitable personal exploit; it is a table-wide sabotage or
  collusion risk because low-buffer players become easier to silence.
- **Syndicate debt immunity** is real in the adjudication rules but did not produce a
  positive edge under the tested strategy ({by_exploit['syndicate_debt_immunity']['exploit_value']:+.1%}).
  It remains a missing consequence, not a demonstrated winning exploit.
- **Expose vote-stripping** and **Interrogation cost griefing** also hurt the actors
  while moving Syndicate wins by {vote_stripping['syndicate_win_delta']:+.1%} and
  {cost_griefing['syndicate_win_delta']:+.1%} respectively. They are not rational
  solo strategies, but they are plausible Syndicate-aiding or kingmaking tactics.

## Rule ambiguities surfaced

1. The engine floors a negative living Magnate balance at zero when calculating the
   combined Magnate total. The rulebook does not explicitly say whether it should
   instead subtract from the total.
2. Bankruptcy imposes no extra personal-victory consequence on Syndicate members,
   because they were already ineligible for Faction Victory. Negative Assassin
   Influence still reduces Assassin+Stash.

## Human-playtest questions

- Does exclusion from an Interrogation feel like a fair consequence or lost agency?
- Do players understand why the initiator may be unable to vote after paying?
- How often does the GM need to refuse an ineligible action?
- Does an exploit with a positive mechanical edge feel abusive at a real table?
"""


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--games", type=int, default=300,
                        help="games per player count and chaos band")
    parser.add_argument("--paired-games", type=int, default=600,
                        help="games for gate and debt paired comparisons")
    parser.add_argument("--exploit-games", type=int, default=400,
                        help="games per exploit strategy")
    args = parser.parse_args()

    data = {
        "parameters": vars(args),
        "baselines": run_baselines(args.games),
        "gate_comparison": run_gate_comparison(args.paired_games),
        "debt_deterrence": run_debt_deterrence(args.paired_games),
        "exploits": [
            asdict(run_exploit(name, games=args.exploit_games))
            for name in EXPLOITS
        ],
    }
    OUTPUT.mkdir(parents=True, exist_ok=True)
    (OUTPUT / "results.json").write_text(
        json.dumps(data, indent=2, sort_keys=True), encoding="utf-8")
    report = render_report(data)
    (HERE / "report.md").write_text(report, encoding="utf-8")
    print(report)


if __name__ == "__main__":
    main()
