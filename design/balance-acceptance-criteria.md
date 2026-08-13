# Draft acceptance criteria for the next balance package

**Status: requires owner sign-off before candidate packages are designed.** These are
decision gates, not targets to tune against until one proposal passes.

## Mechanical gates

Measured against the frozen restored baseline on identical seeds at 10-15 players:

| Area | Draft acceptance criterion |
|---|---|
| Faction symmetry | Aggregate Aristocrat/Reformer win-rate gap no greater than 8 percentage points, with no persistent one-sided gap across adjacent player counts. |
| Victory viability | Aristocrat, Reformer, Magnate, and Syndicate aggregate win rates each remain between 20% and 60%. |
| Agency | No more than 10% of players record zero meaningful modelled actions; death does not remove Faction victory or Ghost participation. |
| Physical supply | 90th-percentile total physical chips in play no greater than 220; no observed game above the available 250-chip pool in the agreed stress sample. |
| Individual handling | 90th-percentile richest holding no greater than 30; worst observed no greater than 50 without requiring written-only balances. |
| Inheritance | A death leaves at least part of the remaining estate under player control; after two or three same-Faction deaths, surviving members retain a credible vote-buying budget. |
| Assassin bargaining | At least one credible game state exists in each player count where a major Faction can fund a bribe that compensates the Assassin for abandoning a Hit without transferring most of the Faction's total wealth. |
| Assassin resistance | Under a coordinated alliance stress test, abandoning Hits does not preserve the Syndicate's own win chance as well as honest Hit play. Exact acceptable loss requires sign-off. |
| Execution interest | Catching the Assassin remains economically attractive to multiple non-Syndicate players without creating a dominant "execute for money" strategy. |
| Magnate path | Magnate win rate remains viable after Final spending; Magnates are not forced to abstain from all political play. |
| Vote relevance | Purchased votes change the winning Faction in at least 15% of modelled Finals, or live testing demonstrates that the threat of purchase materially changes bargaining even when the final purchase is not decisive. |
| Circulation | Player-to-player Influence and distinct counterparties do not fall more than 20% below baseline unless live testing shows an improvement in deal quality. |
| Pacing | Meaningful activity does not collapse in Round 3; the package remains compatible with 30/45/60-minute Private Phases. |
| Complexity | At most one new player-facing concept; every changed rule is teachable in one sentence and adds no continuous arithmetic bookkeeping. |

## Human playtest gates

Simulation cannot decide these. A package is not adopted until a live playtest can
answer them.

1. Did at least one player seriously consider paying, protecting, exposing, or executing
   the Assassin for strategic reasons?
2. Could the Assassin plausibly negotiate, or was the correct choice obvious?
3. Did Influence visibly affect the Final before ballots were counted?
4. Did a bereaved Faction retain options after multiple deaths?
5. Could players physically count and transact without replacing chips with a ledger?
6. Could the GM teach every changed rule without an exception-heavy explanation?
7. Did players describe deals as social commitments rather than arithmetic exchanges?

## Required package report

Every proposed package must include:

- the completed impact map from `balance-framework.md`;
- all changed values and rules as one coherent configuration;
- baseline, candidate, and delta scorecards on shared seeds;
- results at every player count, not only the aggregate;
- normal, chaotic, and adversarial tests;
- second-order effects and the strongest known exploit;
- what the package deliberately leaves unchanged;
- which criteria pass, fail, or remain a live-playtest question.

No rulebook or playtest-aid edits occur until these criteria are approved and a complete
package is selected.

