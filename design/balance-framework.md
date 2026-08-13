# Whole-system balance framework

Dark Council is balanced as a connected social system, not as a collection of
independent numbers. A proposal is therefore a complete rules package. It is compared
with a frozen baseline on identical game setups and random seeds before any rulebook
text changes.

## 1. Invariants

Every candidate must preserve these properties.

| ID | Invariant |
|---|---|
| I1 | Every living role retains meaningful agency through the Final. |
| I2 | Death hurts, but does not remove a Faction from play. Inheritance remains part of the game. |
| I3 | Influence remains physically playable: the available chip pool covers normal play and individual holdings stay practical to count. |
| I4 | Bribing, executing, and protecting the Assassin can each be rational in some game states. |
| I5 | Influence is a credible direct victory path for Magnates and an indirect victory path for Factions through votes. |
| I6 | Social negotiation matters more than arithmetic optimisation. |
| I7 | A new rule must be teachable in one sentence or justify its additional complexity. |
| I8 | Aristocrat and Reformer outcomes remain symmetric, and no Role loses a credible route to victory. |

An invariant is a guardrail, not a tuning target. A package that improves one headline
metric by materially breaking another invariant is rejected.

## 2. Whole-game scorecard

Every baseline and candidate report covers all ten axes.

| Axis | Required evidence |
|---|---|
| Role and Faction viability | Win rates and confidence intervals by player count, Faction, Role, and survival state. |
| Influence flow | Influence created, destroyed, transferred, and retained by round and source. |
| Wealth concentration | Peak chips in play, peak Stash, richest holding, and concentration after deaths. |
| Voting power | Vote purchases, buyers, purchased-vote share, and elections whose winner changes because of purchased votes. |
| Assassin incentive triangle | Relative value and affordability of completing a Hit, accepting a bribe, protecting the Assassin, and executing the Assassin. |
| Death and inheritance | Effects on bereaved Faction liquidity, agency, concentration, and kingmaking. |
| Information and Evidence | Whether players have enough credible information to make paid votes, accusations, and alliances rational. |
| Negotiation density | Player-to-player transfers, distinct counterparties, and meaningful offers by round. |
| Pacing | Decisions, deaths, goals, and economic activity across the 30/45/60-minute rounds and Final. |
| Complexity and exploits | New concepts, teaching burden, bookkeeping, dominant strategies, denial play, and coalition abuse. |

Simulation can measure mechanical consequences and reject unsafe packages. It cannot
establish fun, clarity, persuasion quality, or whether players want to repeat the game.
Those claims require live playtest evidence.

## 3. Impact map

Complete this before proposing values.

```text
Package:
Design intent:
Rules changed:
Rules explicitly unchanged:

Direct beneficiaries:
Direct payers:
Newly rational behaviour:
Behaviour made weaker or irrational:

After one death:
After two or three deaths:
At 10 players:
At 15 players:

Likely second-order adaptation:
Worst legal exploit:
Teaching and bookkeeping cost:

Expected scorecard gains:
Expected scorecard losses:
Acceptance criteria:
Live-playtest questions:
```

The impact map must describe who pays for an improvement. "No downside" is not an
acceptable answer.

## 4. Decision protocol

1. **Freeze the baseline.** The restored stable rules are the reference until a complete
   package is approved. Candidate B is always compared with the baseline, never with
   candidate A.
2. **Use shared scenarios.** Baseline and candidates use identical player counts, seeds,
   deals, and behaviour settings. Report deltas as well as absolute results.
3. **Test packages, not knobs.** A Hit reward is assessed together with starting
   Influence, goals, inheritance, execution incentives, vote costs, thresholds, and
   Influence sinks.
4. **Use evidence in tiers.**
   - deterministic rules and ledger validation;
   - high-volume mechanical simulations;
   - lower-volume adversarial and player-agent scenarios;
   - live playtests for social incentives, clarity, and fun.
5. **Use simulations as rejection tests.** A failed invariant rejects a package. Passing
   the model only qualifies it for human testing.
6. **State uncertainty.** Sensitive thresholds, unmodelled behaviour, and conflicting
   interpretations are reported rather than averaged away.
7. **Approve the package before editing rules.** Reports and simulator flags may be
   developed first. Rulebooks and playtest aids change only after explicit approval.
8. **Record the decision.** Each adopted package gets one entry containing its intent,
   evidence, accepted trade-offs, acceptance criteria, and unchanged surfaces.

## 5. Minimum comparison matrix

All economy packages are tested at 10, 11, 12, 13, 14, and 15 players. Cheap mechanical
runs use enough seeds to expose distributions and rare extremes. Rich player-agent runs
use fewer seeds but preserve isolated player knowledge and produce transaction ledgers.
At minimum, reports separate:

- baseline, candidate, and candidate-minus-baseline;
- each player count and the combined result;
- normal, chaotic, and adversarial behaviour;
- rounds 1, 2, 3, and the Final;
- average, 90th percentile, and worst observed physical-token load.

