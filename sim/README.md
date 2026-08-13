# Dark Council simulator — plain-language guide

## What it is

This is a robot version of a game night. It:

1. deals Factions, Roles, Goals, Secrets and information;
2. gives everyone Influence;
3. plays three rounds and the Final;
4. records every transfer, vote, death and victory;
5. repeats the game thousands of times.

The purpose is not to predict one real game. It is to find mechanical patterns that
are almost impossible to see from one playtest.

## Why its results are useful

- **Each robot sees only its own information.** It cannot ask the engine who the
  Assassin is.
- **Influence must balance.** After every round:
  `players + Bank + Stash == 0`. A broken ledger stops the run.
- **Games are seeded.** The same seed reproduces the same deal and behaviour. Rule
  variants therefore play the same starting games rather than relying on different
  luck.

## What it can and cannot answer

| It can test | It cannot test |
|---|---|
| Faction and Syndicate win rates | Whether the game is fun |
| Whether thresholds are reachable | Whether the rules are easy to understand |
| Whether a rule creates an arithmetic exploit | Whether negotiations feel satisfying |
| How often a modelled situation occurs | Whether players want to play again |

Real people answer the right-hand column. If the simulator finds no effect, that means
only that the model may not cover the human behaviour.

## Three kinds of robot

### Sensible

Follows the rules and uses one of five recognisable play styles: Politician,
Detective, Merchant, Wallflower or Firebrand.

### Chaotic

Models ordinary human unpredictability through four separate channels:

- **misremembers** — attempts an illegal action, which the GM refuses;
- **plays badly** — makes a legal but self-defeating choice;
- **forgets** — omits a useful action;
- **tilts** — prioritises a grudge over winning.

The standard bands are 0% (clean table), 12% (realistic table) and 30% (messy table).
The chaos random stream is separate from the deal, so adding chaos does not reshuffle
the roles.

### Exploiter

Actively looks for a legal loophole. Exploiters never fabricate a payment, alter
history or cheat; they simply use the written rules ruthlessly.

Each exploit is run against an honest control on the same seeds. The report shows:

`exploit value = exploiter win rate - honest win rate in the same seat`

A consistent positive edge is evidence that the rule is easy to abuse.

## Debt is tested as deterrence

The desired outcome is not “somebody must become Bankrupt.” Bankruptcy exists to stop
players treating debt as free money.

The test therefore asks:

- Does deliberately remaining in debt improve a player's chance of winning?
- Which Factions or Roles are immune to the consequence?
- What actions still create debt now that voluntary overspending is forbidden?
- Does an ally rescue preserve a strategically important vote without meaningful cost?

## Run it

From the repository root:

```powershell
python -m sim.validate
python -m sim.run
python -m sim.exploits
python -m sim.scorecard --games 100 --output design\baseline-scorecard.md
```

Generated reports and ledgers are intentionally ignored by Git.

`sim.scorecard` is the whole-system comparison gate. With no `--set` arguments it
measures the frozen stable baseline. Candidate values are applied as one package and
run on the same seeds:

```powershell
python -m sim.scorecard --games 100 --name "Candidate A" `
  --set hit_payout=4 --set vote_cost=2
```

The output reports baseline, candidate, and delta across win viability, Influence flow,
physical-token load, vote decisiveness, Assassin incentives, inheritance, information,
negotiation, pacing, and complexity. Passing it qualifies a package for human testing;
it does not prove the package is fun or clear.

Named whole-system packages are simulator-only configurations in `sim/packages.py`:
they are calibrated only for the current 10-15-player reassessment range.

```powershell
python -m sim.scorecard --games 150 --package reward-compression
python -m sim.scorecard --games 150 --package reward-compression --mode realistic
python -m sim.exploits --package reward-compression --games 250 --players 13
python -m sim.alliance --games 150 --package reward-compression
```

The alliance runner is deliberately pessimistic: a perfectly informed cover Faction
funds and protects the Assassin while the Assassin abandons Hits to attack its rival.
Use it to reject packages that make betrayal too safe, not to predict ordinary play.

## Satisfaction diagnostics

```powershell
python -m sim.satisfaction
```

This produces `sim/satisfaction-report.md`, covering execution accuracy by round,
death timing, per-Goal completion, zero-agency players, wealth concentration, the
30/45/60 social-phase schedule, and the tested Round 3 Ambition deadline.
