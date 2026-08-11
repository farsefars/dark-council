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
| Clean | 48.5% | 48.7% | 39.5% | 38.9% | 14.4% | 0.00 |
| Realistic chaos | 49.0% | 47.8% | 36.0% | 34.7% | 14.1% | 0.83 |
| Messy chaos | 47.5% | 49.2% | 33.0% | 34.6% | 13.7% | 1.90 |

### Robustness reading

- Aristocrat/Reformer results remain stable across the chaos bands.
- Magnate wins fall from 39.5% to 33.0%. The
  Magnate economy is substantially more vulnerable to forgotten, irrational and
  grudge-driven behaviour than the election Factions.
- The Syndicate rate does not move monotonically with chaos; the model does not show a
  simple “more mistakes always help the Assassin” relationship.

## Eligibility-gate comparison (13 players, matched seeds)

- Published gate Syndicate win rate: 35.3%
- Gates-off Syndicate win rate: 37.2%
- **Published gate delta:** -1.8%
- Correct-Execution accuracy delta: -0.3%
- Published living-voter exclusion rate: 14.4%

Important mechanical observation: an initiator who spends their last Influence on the
Interrogation cost is excluded from the vote that immediately follows.

The gate produces a small -1.8% Syndicate shift in this
sample, not a balance collapse. The much larger concern is participation: roughly
14.4% of living voter opportunities are
removed.

## Debt deterrence

- Honest controlled-seat win rate: 47.3%
- Debt-squatting win rate: 44.6%
- **Debt-squatting value:** -2.7%
- Syndicate-member Bankruptcy incidence: 3.2%
- Ally rescue transfers/game: 0.080
- Influence rescued/game: 0.082
- Debt created by: expose_hit 2536

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
| debt_squatting | 47.0% | 42.3% | -4.7% | +7.2% | 1200 |
| syndicate_debt_immunity | 43.0% | 38.0% | -5.0% | -2.2% | 200 |
| expose_vote_stripping | 47.0% | 46.0% | -1.0% | -4.2% | 1200 |
| interrogation_cost_griefing | 47.0% | 43.4% | -3.6% | -1.8% | 1200 |
| nomination_cartel | 47.0% | 46.4% | -0.6% | +0.0% | 1200 |
| blanket_kill_tell | 44.4% | 29.6% | -14.8% | -5.2% | 135 |
| final_dump | 50.9% | 54.4% | +3.5% | +0.0% | 739 |
| ghost_bloc | 47.0% | 42.5% | -4.5% | +0.0% | 1200 |
| stash_shelter | 43.0% | 45.0% | +2.0% | +0.0% | 200 |
| contract_abuse | 47.0% | 45.0% | -2.0% | +1.2% | 1200 |

Strategies at or above a +3 percentage-point edge: **final_dump**.

### Adversarial reading

- **Final dump** is the clearest self-serving exploit: a +3.5%
  personal edge in the
  full run. Aristocrats/Reformers have no reason to preserve Influence after buying
  votes, so cautious spending is dominated by spending everything.
- **Stash shelter** gives controlled Syndicate seats a
  +2.0% edge. Leaving Influence
  in the protected Stash is stronger than the ordinary policy's liquidity reserve.
- **Debt squatting** hurts the controlled seats but moves the Syndicate win rate by
  +7.2%. It is not a profitable personal exploit; it is a table-wide sabotage or
  collusion risk because low-buffer players become easier to silence.
- **Syndicate debt immunity** is real in the adjudication rules but did not produce a
  positive edge under the tested strategy (-5.0%).
  It remains a missing consequence, not a demonstrated winning exploit.
- **Expose vote-stripping** and **Interrogation cost griefing** also hurt the actors
  while moving Syndicate wins by -4.2% and
  -1.8% respectively. They are not rational
  solo strategies, but they are plausible Syndicate-aiding or kingmaking tactics.
- **Aggressive Contract use** produced -2.0% personal value and moved Syndicate wins +1.2%. The selected cap does not create a demonstrated credibility exploit in this model.

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
