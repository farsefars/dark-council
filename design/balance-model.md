# Influence, voting, death, and the Assassin: causal balance model

This model describes the restored stable economy before proposing changes. Its purpose
is to show which levers are coupled, where value enters and leaves, and which apparent
economy problems are actually information or incentive problems.

## 1. The system

Influence has four simultaneous jobs:

1. **survival and action access** - players need non-negative holdings and minimum
   balances for Expose and Interrogation votes;
2. **social currency** - gifts, bargains, kill tells, extortion, Commerce, and debt
   rescue;
3. **political power** - Reveal votes cost 1 and Final votes cost 3;
4. **victory score** - remaining Influence directly decides Magnate and Syndicate
   victories.

The same chip can perform only one of these jobs at the Final: spending it for political
power reduces the totals used for economic victories. This trade-off is load-bearing.

## 2. Sources, transfers, and sinks

| Flow | Stable rule | System effect |
|---|---|---|
| Starting Influence | Bank gives 4 to every player | Establishes initial liquidity; scales directly with table size. |
| Round stipend | Bank gives 2 to each living player in each round | Replenishes agency but rewards survival and large tables. |
| Motive / Ambition | Bank gives 5 / 10 | Large personal injections before Round 3; strongly affect rankings and thresholds. |
| Correct Expose | Bank gives 1 to the exposer; target loses 4 | A small reward plus a strong targeted sink. |
| Failed Interrogation | Bank gives survivor 3 | Makes false accusations costly and creates comeback liquidity. |
| Correct Interrogation | Refund +5 to initiator and +5 to living Guilty voters | A large distributed Bank injection tied to catching the Assassin. |
| Hit | Bank adds 3 to Stash on success; 3 leaves Stash/personal balance on failure | Small marginal incentive compared with victim wealth. |
| Assassination | Half the victim's positive Influence enters Stash | The Assassin's main economic reward rises with victim wealth. |
| Execution | Half the victim's positive Influence returns to Bank | A strong sink. |
| Inheritance | All remaining victim Influence goes to one chosen living player | Preserves Faction/social agency but concentrates wealth. |
| Player deals | Player to player | Circulates existing chips and creates social obligations; does not change total supply. |
| Auction, actions, Reveal, votes | Player to Bank | Retires Influence in exchange for information, pressure, or political power. |

Measured over 600 restored-baseline games:

- Bank to players: **184.9** Influence/game;
- players to Bank: **94.4**;
- player-to-player circulation: **70.1**;
- inheritance: **28.0**;
- peak physical pool: **179 p90**, **257 worst observed**;
- richest single holding: **42 p90**, **64 worst observed**.

The main physical problem is therefore not simply total supply. Single-heir inheritance
preserves money while repeatedly consolidating it.

## 3. The Assassin incentive triangle

Let:

- `H` = Hit success reward;
- `V` = victim's positive Influence when killed;
- `K(V) = floor(V / 2)` = Stash income from the victim;
- `B` = credible bribe offered for choosing or sparing a target;
- `F` = Hit failure penalty;
- `T` = remaining gap to the Syndicate threshold;
- `E` = expected personal/economic value to players of executing the Assassin;
- `P` = political value of keeping the Assassin alive as a covert Faction ally.

### Complete the Hit

The immediate Stash gain is:

`complete value = K(V_hit) + H`

### Abandon the Hit for an allied target or bargain

Killing a non-matching victim produces:

`abandon value = K(V_other) + B - F + P`

The Hit is economically preferred only when:

`K(V_hit) + H > K(V_other) + B - F + P`

This exposes two facts hidden by the payout number:

1. victim wealth can matter more than the Hit reward; and
2. a Faction alliance adds political value `P`, not just chips.

The 40-Influence experiment tried to dominate every possible `B + P` with `H`. It made
abandonment unattractive, but also made a credible bribe physically impossible and
inflated the entire Stash/threshold system.

### The bribe/Hit identity under Influence-scored victory

When Syndicate victory is based on accumulated Influence, skipping a successful Hit
costs approximately `H + F` relative to completing it. A rational bribe must therefore
cover:

`credible bribe >= H + F + victim-value difference + lost political option value`

Raising `H` simultaneously:

- makes Hits harder to abandon;
- raises the minimum credible bribe by the same amount;
- raises reachable Syndicate wealth and therefore the required threshold;
- increases physical-token load if Stash chips are real.

That is why the same knob cannot independently create both a strong Hit incentive and
an affordable alliance bargain. This is a structural coupling, not a calibration error.

## 4. Why execution incentives are not only an Assassin rule

On a correct execution, the initiator receives their cost back plus 5, and every living
Guilty voter receives 5. The scorecard measures the complete Bank injection from these
three reward lines rather than treating the voter reward as an isolated amount.

This creates three simultaneous consequences:

- it gives non-Syndicate actors a reason to expose and execute the Assassin;
- it injects enough Influence to move Leaderboards, Magnate totals, and Final vote
  budgets;
- because rewards are per voter, its economic effect grows with coalition size.

Reducing or redirecting this reward is therefore not a local disinflation change. It
also changes deduction risk, public coalition formation, Magnate viability, and the
price of protecting the Assassin.

## 5. Why inheritance cannot be treated as a generic sink

Returning every estate to the Bank would reduce concentration and supply, but it would
also remove the dead player's final social choice and strip liquidity from their allies.
With several deaths, a bereaved Faction could lose both people and voting power.

Inheritance performs three valuable jobs:

- preserves some agency after a death;
- lets a victim reward trust or protect a Faction;
- keeps Influence circulating between players.

Its failure is **concentration**, not existence. Any future package must preserve those
jobs while testing concentration and repeated-death effects explicitly.

## 6. Voting is already mechanically relevant

A corrected paired counterfactual replays the complete election with the same seeds and
policy decisions but suppresses purchased vote weight. The stable baseline produces:

- **1.52** Final vote buyers/game;
- **3.34** purchased votes/game;
- **19.2%** of winners changed at the Faction level because of purchased votes;
- **4.05** verified Faction identities known per player at the end of the modelled game.

This passes the 15% working gate. The earlier 8.5% result was invalid because it compared
the purchased election's final result with free first-round plurality rather than
replaying the same tie/runoff procedure without paid weight.

Voting therefore remains an important coupling—economic changes can remove liquidity
and weaken it—but it is not a baseline problem requiring a new information or Final
rule. Future packages must preserve its decisiveness rather than redesign it.

## 7. Restored baseline diagnosis

| Invariant | Result | Causal reading |
|---|---|---|
| Agency | Pass | Stipends, inheritance, Ghost votes, and social transfers keep most players active. |
| Inheritance | Pass | It preserves circulation and bereaved-Faction agency. |
| Physical playability | Fail | Total pool usually fits, but one-heir estates create impractical holdings; rare pool extremes exceed 250. |
| Assassin triangle | Fail | Hit opportunity cost is cheap relative to available Faction wealth; protection also carries unpriced political value. |
| Influence matters | Pass | Magnates are viable and bought votes change the winning Faction often enough to clear the working gate. |
| Social negotiation | Pass in the model | Player-to-player transfer volume is high; live play must confirm whether those transfers are meaningful bargains. |
| Teachability | Pass | The restored rules add no experimental concepts. |
| Symmetry and viability | Pass in aggregate | A/R gap is small and all four victory routes remain reachable, though player-count samples need higher-N confirmation. |

The next unit of work is not "pick a better Hit number." It is to define acceptance
criteria for the entire package, then compare coherent alternatives that preserve
inheritance, physical tokens, social bargaining, and vote relevance together.
