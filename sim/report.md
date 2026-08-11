# Simulation report — published rules, chaos and exploit probes

## Scope

These are mechanical simulations. They do not measure fun, comprehension,
persuasion, satisfaction or replay intent.

Run size: 300 games per player count per chaos band,
600 paired games for eligibility/debt, and
400 paired games per exploit.

## Headline

| Table model | Aristocrat | Reformer | Magnate | Syndicate | Vote exclusions | GM refusals/game |
|---|---:|---:|---:|---:|---:|---:|
| Clean | 47.2% | 49.6% | 41.9% | 35.8% | 14.2% | 0.00 |
| Realistic chaos | 47.0% | 49.5% | 38.6% | 33.5% | 13.8% | 0.78 |
| Messy chaos | 48.3% | 47.7% | 34.0% | 34.6% | 13.5% | 1.84 |

### Robustness reading

- Aristocrat/Reformer results remain stable across the chaos bands.
- Magnate wins fall from 41.9% to 34.0%. The
  Magnate economy is substantially more vulnerable to forgotten, irrational and
  grudge-driven behaviour than the election Factions.
- The Syndicate rate does not move monotonically with chaos; the model does not show a
  simple “more mistakes always help the Assassin” relationship.

## Eligibility-gate comparison (13 players, matched seeds)

- Published gate Syndicate win rate: 35.0%
- Gates-off Syndicate win rate: 32.8%
- **Published gate delta:** +2.2%
- Correct-Execution accuracy delta: +0.5%
- Published living-voter exclusion rate: 14.1%

Important mechanical observation: an initiator who spends their last Influence on the
Interrogation cost is excluded from the vote that immediately follows.

The gate produces a small +2.2% Syndicate shift in this
sample, not a balance collapse. The much larger concern is participation: roughly
14.1% of living voter opportunities are
removed.

## Debt deterrence

- Honest controlled-seat win rate: 46.9%
- Debt-squatting win rate: 44.2%
- **Debt-squatting value:** -2.7%
- Syndicate-member Bankruptcy incidence: 3.0%
- Ally rescue transfers/game: 0.068
- Influence rescued/game: 0.070
- Debt created by: expose_hit 2056

The test asks whether debt is profitable, not whether Bankruptcy is common. Syndicate
members already lost their personal Faction Victory, so ordinary Bankruptcy adds no
second personal-victory consequence to them.

Debt squatting is personally deterred in this model (-2.7%).
The ability-to-pay gates also work as intended: the recorded debt is created by
involuntary losses, not voluntary spending. Ally rescue is rare, so it does not make
the consequence disappear.

## Adversarial exploit catalogue

| Strategy | Honest | Exploit | Exploit value | Syndicate delta | Applicable samples |
|---|---:|---:|---:|---:|---:|
| debt_squatting | 42.7% | 42.7% | +0.0% | +14.0% | 1200 |
| syndicate_debt_immunity | 30.0% | 32.5% | +2.5% | +1.0% | 200 |
| expose_vote_stripping | 42.7% | 43.2% | +0.6% | +6.0% | 1200 |
| interrogation_cost_griefing | 42.7% | 39.9% | -2.8% | +2.5% | 1200 |
| nomination_cartel | 42.7% | 43.7% | +1.0% | +0.0% | 1200 |
| blanket_kill_tell | 31.6% | 27.9% | -3.7% | -1.2% | 136 |
| final_dump | 47.2% | 52.8% | +5.5% | +0.0% | 739 |
| ghost_bloc | 42.7% | 37.2% | -5.4% | +0.0% | 1200 |
| stash_shelter | 30.0% | 38.0% | +8.0% | +3.5% | 200 |

Strategies at or above a +3 percentage-point edge: **final_dump, stash_shelter**.

### Adversarial reading

- **Final dump** is the clearest self-serving exploit: a +5.5%
  personal edge in the
  full run. Aristocrats/Reformers have no reason to preserve Influence after buying
  votes, so cautious spending is dominated by spending everything.
- **Stash shelter** gives controlled Syndicate seats a
  +8.0% edge. Leaving Influence
  in the protected Stash is stronger than the ordinary policy's liquidity reserve.
- **Debt squatting** hurts the controlled seats but moves the Syndicate win rate by
  +14.0%. It is not a profitable personal exploit; it is a table-wide sabotage or
  collusion risk because low-buffer players become easier to silence.
- **Syndicate debt immunity** is real in the adjudication rules but did not produce a
  positive edge under the tested strategy (+2.5%).
  It remains a missing consequence, not a demonstrated winning exploit.
- **Expose vote-stripping** and **Interrogation cost griefing** also hurt the actors
  while moving Syndicate wins by +6.0% and
  +2.5% respectively. They are not rational
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
