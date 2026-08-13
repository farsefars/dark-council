# Whole-system package reassessment

**Status: analysis only. No package is implemented in the rules.** The restored
`a581b50` economy remains authoritative. Rulebooks, playtest aids, and website output
are untouched.

The corrected whole-system diagnosis has **two**, not three, mechanical failures:

1. physical-token concentration and rare pool overflow;
2. the Hit is too cheap to create the intended Assassin bargain.

Paid Final votes already change the winning Faction in **19.2%** of stable-baseline
games, above the 15% working gate. An earlier shortcut incorrectly compared a purchased
runoff with free first-round plurality and understated this as 8.5%. Every unnecessary
Final-election change was removed from the packages after that error was found.

## 1. Decision

| | Baseline | A Reward compression | B Leader tribute | C Hybrid Hits |
|---|---:|---:|---:|---:|
| Normal mechanical gates | 6/8 | **7/8 + teachability review** | **7/8 + review** | 6/8 + review |
| Realistic-chaos physical gate | Fail | **Pass** | Fail by 1 chip | Pass |
| Magnate win | 40.2% | 33.0% | 35.1% | 35.8% |
| Syndicate win | 34.9% | 37.2% | 39.0% | 39.0% |
| Physical pool p90 / worst | 177 / 257 | **142 / 182** | 147 / 195 | 141 / 193 |
| Richest holding p90 / worst | 44 / 71 | **30 / 41** | 30 / 44 | 30 / 43 |
| Hit opportunity cost / effective bribe | 0.38 | **0.63** | **0.63** | 0.48 |
| Purchased votes decisive | 20.1% | 15.0% | 17.1% | 17.8% |
| Player circulation | 70.6 | 66.1 | 66.0 | 65.9 |
| Syndicate: honest / abandon-Hits alliance | 58.3% / 45.8% | **56.0% / 37.7%** | 54.8% / 37.1% | **54.9% / 23.2%** |

**Recommendation: Package A is the only package that qualifies unchanged for a physical
playtest.** It passes every mechanical gate under normal and realistic-chaos behaviour.
Its remaining gate is human teachability and social feel.

Package B also passes clean mechanical play, but misses the realistic-chaos holding gate
at 31 versus 30 and introduces a punitive Leaderboard tax. Package C is the strongest
alliance defence but fails the ordinary Assassin-bargain gate.

This recommends a live test, not publication.

## 2. Package A - Distributed estates and compressed rewards

### Exact package

| Surface | Stable baseline | Package A |
|---|---:|---:|
| Death bequest | All remaining Influence to one chosen heir | Split as evenly as possible among up to three living players chosen by the victim |
| Motive | +5 | **+4** |
| Ambition | +10 | **+8** |
| Successful Hit | +3 Stash | **+5 Stash** |
| Correct Assassin verdict: initiator | Cost refund +5 | Cost refund **+2** |
| Correct Assassin verdict: each living Guilty voter | +5 | **+2** |

Economic thresholds are calibrated from Package A's own measured distributions:

| Players | Magnate | Assassin + Stash |
|---:|---:|---:|
| 10 | 16 | 43 |
| 11 | 23 | 42 |
| 12 | 14 | 41 |
| 13 | 23 | 41 |
| 14 | 15 | 41 |
| 15 | 20 | 41 |

### Explicitly unchanged

- starting Influence 4 and stipend 2;
- three rounds and 30/45/60-minute Private Phases;
- half of an Assassinated victim's Influence enters Stash;
- half of an Executed victim's Influence returns to Bank;
- the victim controls the whole remaining estate; none returns to Bank;
- Hit failure costs 3;
- Influence-scored Syndicate victory, Stash, Launder 2, and withdrawal 2;
- **the entire Final:** three Candidates, Reveal, vote price 3, plurality, and tie
  procedure;
- Bankruptcy, debt rescue, Ghosts, Auction, Evidence, Expose, and Interrogation cost;
- physical chips: no written-only or abstract currency.

### Impact map

**Intent:** strengthen the Hit enough that abandoning it has a meaningful but affordable
price, while removing the two measured causes of physical concentration: single-recipient
estates and oversized correct-execution injections.

**Direct beneficiaries**

- bereaved Factions retain every estate chip under the victim's control;
- the table can represent every observed package game within the physical set;
- Magnates and Syndicate retain calibrated economic victory paths;
- players can continue using the existing Final without another procedure.

**Direct payers**

- Motive and Ambition rewards fall by 1 and 2;
- a successful prosecutor and each correct living Guilty voter receive +2 instead of +5;
- estates can no longer automatically create a single super-voter;
- abandoning a Hit costs 8 relative Influence (+5 foregone and -3 failure), up from 6.

**Newly rational behaviour**

- a major Faction can fund a credible Assassin offer without transferring most of its
  available wealth;
- several heirs must coordinate how a dead ally's estate supports the Faction;
- catching the Assassin remains profitable for several actors, but is no longer the
  largest minting event in the economy.

**Behaviour made weaker**

- execution-for-money coalitions;
- single-heir snowballs;
- abandoning Hits merely because allied funding replaces the lost reward.

**After one death:** all remaining Influence stays in circulation and under the victim's
control, divided among up to three named recipients.

**After two or three deaths:** repeated estates create a coalition rather than one
40-70-chip holder. Worst observed normal holding falls from 71 to 41.

**At 10 players:** normal pool p90 110, holding p90 30, Magnate 36.0%, Syndicate 34.0%.

**At 15 players:** normal pool p90 155, holding p90 28, Magnate 31.3%, Syndicate 36.0%.

**Likely second-order adaptation:** three heirs may voluntarily reconsolidate an estate.
That remains legal, but it is visible, requires cooperation, consumes negotiation time,
and can be interrupted by competing needs.

**Strongest tested exploits**

- `stash_shelter`: +7.8-point personal edge at 13 players, versus +7.0 baseline;
- `final_dump`: +3.9, versus +4.8 baseline;
- no tested exploit gains a new double-digit personal edge;
- debt-squatting can raise Syndicate outcomes indirectly, but does not improve the
  controlled players' own win rate.

**Teaching/bookkeeping cost**

- five numeric substitutions;
- one changed death sentence: name up to three heirs and split the remainder evenly;
- no new phase, currency, tax, victory gate, or Final procedure.

### Normal and realistic-chaos evidence

| Metric | Normal baseline | Normal A | Realistic baseline | Realistic A |
|---|---:|---:|---:|---:|
| A/R gap | 2.7% | **0.4%** | 1.2% | 2.2% |
| Magnate | 40.2% | **33.0%** | 39.4% | 32.3% |
| Syndicate | 34.9% | **37.2%** | 35.9% | 33.6% |
| Zero-agency players | 1.1% | **1.0%** | 1.1% | **1.0%** |
| Pool p90 / worst | 177 / 257 | **142 / 182** | 169 / 261 | **140 / 189** |
| Holding p90 / worst | 44 / 71 | **30 / 41** | 41 / 66 | **30 / 48** |
| Paid votes decisive | 20.1% | 15.0% | 17.4% | 16.0% |
| Hit cost / effective bribe | 0.38 | **0.63** | 0.39 | **0.63** |
| Correct-execution injection | 25.7 | **11.8** | 24.0 | **12.6** |
| Social transfers | 42.3 | 42.0 | 40.9 | 40.5 |

The package reduces paid-vote decisiveness because it reduces available Influence, but
it remains at or above the agreed gate without changing the Final.

### Alliance attack

The pessimistic coalition gives the Assassin's cover Faction perfect knowledge,
coordinated funding, bloc voting, and deliberate rival-Faction targets.

- Baseline Syndicate: 58.3% following Hits, 45.8% abandoning them (**-12.6**).
- Package A Syndicate: 56.0% following Hits, 37.7% abandoning them (**-18.3**).

A makes betrayal materially worse for the Syndicate without making it impossible.
The allied Faction still wins 86.7% of abandonment games. That remaining problem is
political bloc strength, not an economy failure, and should not be hidden by inflating
the Hit again.

## 3. Package B - Distributed estates and leader tribute

### Package

- three chosen heirs;
- successful Hit +5;
- correct prosecutor +3 and correct Guilty voters +2;
- after the Round 1 and Round 2 Leaderboards, each Top-3 player pays 2 to Bank;
- Goal rewards remain +5/+10;
- the Final remains unchanged.

### Result

B passes all clean mechanical gates:

- Magnate 35.1%, Syndicate 39.0%;
- pool 147 p90 / 195 worst;
- holding 30 p90 / 44 worst;
- paid votes decisive 17.1%;
- Hit/bribe ratio 0.63.

It is rejected as the primary live candidate because:

- realistic-chaos holding p90 is 31, missing the agreed gate;
- it introduces a mandatory tax and makes visible Leaderboard success partly punitive;
- it is more exploitable through debt effects: the debt-squatting attack raises
  Syndicate outcomes by 17.2 points, versus 10.0 under A;
- direct reward compression targets the measured source of excess chips more clearly.

B remains the fallback if the owner strongly prefers preserving +5/+10 Goal rewards.

## 4. Package C - Hybrid two-Hit Syndicate

### Package

B's estate, tribute, and execution changes, but Hit reward stays +3 and Syndicate
victory additionally requires two successful Hits.

### Result

- Magnate 35.8%, Syndicate 39.0%;
- pool 141 p90 / 193 worst;
- holding 30 p90 / 43 worst;
- paid votes decisive 17.8%;
- abandoning Hits cuts alliance Syndicate victory to 23.2%.

C is rejected because ordinary Hit opportunity cost / effective bribe is **0.48**, below
the accepted live bargaining band, and it adds a second Syndicate victory gate. It is a
structural fallback only if live play shows A still makes alliance betrayal too safe.

## 5. Findings that changed the recommendation

1. **Voting was not broken.** A full paired replay with purchases suppressed but all
   policy decisions preserved measured baseline decisiveness at 19.2%. The previous
   8.5% result compared unlike election procedures.
2. **Inheritance was not the main concentration source.** Correct-execution rewards were
   the dominant inflow in 99 of 128 oversized-stack games; inheritance dominated one.
3. **The Hit metric initially omitted failure.** Correct opportunity cost is success
   payout plus failure penalty: baseline 6, A/B 8.
4. **Returning estates to Bank remains rejected.** It efficiently removes chips but
   violates the inheritance and bereaved-Faction agency invariant.
5. **The hybrid requirement best resists the alliance but worsens normal bargaining.**
6. **No package edits the Final.** Once the counterfactual was corrected, those changes
   had no justified role in the package.

## 6. Required live-playtest questions

Package A must be tested as one indivisible configuration.

1. Can a Faction make a serious offer to the Assassin, and is the decision difficult?
2. Do several players still care about executing the Assassin at +2/+2?
3. Does naming up to three heirs feel like meaningful legacy or administration?
4. Does lowering Goals to +4/+8 reduce their motivational pull?
5. Are 30-40-chip extremes physically comfortable?
6. Does the alliance's political win rate remain too high even after its Syndicate
   payoff falls?

Until those questions are answered, the restored stable rules remain authoritative.
