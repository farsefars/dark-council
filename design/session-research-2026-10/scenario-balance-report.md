# The Dark Council — 10-Scenario Outcome Balance Report

**Method:** 100 seeded games per player count (8–15), per scenario, per package. The rare Round 1 Early Catch branch is oversampled 4x; Scenario 10 also runs a paired no-Bankruptcy control.

> **Fun is not directly simulatable.** The fun gates below are proxies for tension, agency, comeback viability, meaningful bargaining, and continued participation. They must be validated with the prepared live-playtest kit.

## 12-player readiness addendum — October 30, 2026

A later table-specific ablation ran **2,000 paired games per configuration at exactly
12 players**. It found that raising the wrong Guilty-vote penalty to `-2` reduced the
Round 1 Assassin catch rate from **12.7% to 4.9%** under `+5/-2`, and to **0.7%**
under the four-number `+3/-2` package. `+5/-2` also reduced the 12-player Magnate
win rate from **35.7% to 27.9%** unless thresholds were changed again.

For the October 31, 2026 live game, the decision is therefore to keep the written
**canonical `+5/-1`, Interrogation base 4, Magnate threshold 24, Syndicate threshold
40** package. The broader outcome-tuned package below remains a research candidate,
not tomorrow's rules.

## Package scorecard

| Package | Passed gates | Total gates | Scenario passes |
|---|---:|---:|---:|
| Canonical +5/-1 | 22 | 36 | 1/10 |
| Deliberative +3/-2 | 22 | 36 | 1/10 |
| Outcome-tuned +3/-2 | 26 | 36 | 3/10 |

**Best desk-side package:** **Outcome-tuned +3/-2** — Deliberative stakes, Interrogation base 3, Magnate threshold -2, and Syndicate threshold +3.

This is a simulator recommendation for the **next controlled playtest**, not an automatic rulebook change.

## Cross-scenario failures

- **Early Catch:** Guilty edge >=10pp.
- **Uncaught Shadow:** survivor S 50-75%, 2-3 Contracts >75%.
- **Courier Shield:** accuracy >=18%.
- **Trigger-Happy Mob:** wrong voters underperform, bankruptcies >=1.5.
- **Passive / Hoarding Table:** innocent drop >=8pp.
- **Faction Lockout & Reveal Pivot:** major-faction lockout <12%.
- **Debt Crisis & Coalition Bailout:** debt recovery 50-75%.

These are system-level weaknesses that threshold tuning alone did not solve.

## Scenario results

### Standard House Party

| Package | Sample | Gates | Metrics | Failed gates |
|---|---:|---:|---|---|
| Canonical +5/-1 | 800 | 5/6 | A=45.6%; R=43.8%; M=35.6%; S=33.8%; close=78.4%; triple=6.6%; innocent=42.0% | R 45-55% |
| Deliberative +3/-2 | 800 | 3/6 | A=47.8%; R=44.2%; M=23.5%; S=40.4%; close=84.2%; triple=7.2%; innocent=39.5% | R 45-55%, M 30-38%, S 25-35% |
| Outcome-tuned +3/-2 | 800 | 6/6 | A=45.1%; R=45.4%; M=30.0%; S=28.6%; close=84.8%; triple=6.1%; innocent=41.2% | None |

### Early Catch

| Package | Sample | Gates | Metrics | Failed gates |
|---|---:|---:|---|---|
| Canonical +5/-1 | 548 | 3/4 | promoted_win=24.3%; guilty_edge=8.7%; successor_interrogated=51.5% | Guilty edge >=10pp |
| Deliberative +3/-2 | 79 | 3/4 | promoted_win=16.5%; guilty_edge=0.3%; successor_interrogated=63.3% | Guilty edge >=10pp |
| Outcome-tuned +3/-2 | 98 | 3/4 | promoted_win=21.4%; guilty_edge=-4.0%; successor_interrogated=66.3% | Guilty edge >=10pp |

### Uncaught Shadow

| Package | Sample | Gates | Metrics | Failed gates |
|---|---:|---:|---|---|
| Canonical +5/-1 | 1032 | 3/5 | survivor_win=40.9%; zero_contract_win=6.9%; strong_contract_win=46.5%; zero_contract_sample=29; strong_contract_sample=825 | survivor S 50-75%, 2-3 Contracts >75% |
| Deliberative +3/-2 | 1328 | 3/5 | survivor_win=40.2%; zero_contract_win=6.5%; strong_contract_win=46.0%; zero_contract_sample=46; strong_contract_sample=1065 | survivor S 50-75%, 2-3 Contracts >75% |
| Outcome-tuned +3/-2 | 1312 | 3/5 | survivor_win=33.8%; zero_contract_win=4.3%; strong_contract_win=39.0%; zero_contract_sample=47; strong_contract_sample=1072 | survivor S 50-75%, 2-3 Contracts >75% |

### Courier Shield

| Package | Sample | Gates | Metrics | Failed gates |
|---|---:|---:|---|---|
| Canonical +5/-1 | 800 | 2/4 | S=41.8%; S_delta=8.0%; execution_accuracy=12.8%; courier_share=75.0% | S <=40%, accuracy >=18% |
| Deliberative +3/-2 | 800 | 2/4 | S=42.8%; S_delta=2.4%; execution_accuracy=10.2%; courier_share=90.4% | S <=40%, accuracy >=18% |
| Outcome-tuned +3/-2 | 800 | 3/4 | S=34.2%; S_delta=5.6%; execution_accuracy=10.9%; courier_share=90.0% | accuracy >=18% |

### Trigger-Happy Mob

| Package | Sample | Gates | Metrics | Failed gates |
|---|---:|---:|---|---|
| Canonical +5/-1 | 800 | 0/3 | wrong_voter_win=41.8%; other_innocent_win=37.9%; bankruptcies=0.38; deaths_13_15=7.25 | wrong voters underperform, bankruptcies >=1.5, deaths <=7 |
| Deliberative +3/-2 | 800 | 1/3 | wrong_voter_win=39.4%; other_innocent_win=38.0%; bankruptcies=0.32; deaths_13_15=5.19 | wrong voters underperform, bankruptcies >=1.5 |
| Outcome-tuned +3/-2 | 800 | 1/3 | wrong_voter_win=41.2%; other_innocent_win=39.0%; bankruptcies=0.29; deaths_13_15=5.24 | wrong voters underperform, bankruptcies >=1.5 |

### Passive / Hoarding Table

| Package | Sample | Gates | Metrics | Failed gates |
|---|---:|---:|---|---|
| Canonical +5/-1 | 800 | 2/3 | innocent=43.7%; innocent_drop=-1.7%; S=47.2%; passive_contract_kills=74.0% | innocent drop >=8pp |
| Deliberative +3/-2 | 800 | 2/3 | innocent=42.9%; innocent_drop=-3.4%; S=48.2%; passive_contract_kills=75.4% | innocent drop >=8pp |
| Outcome-tuned +3/-2 | 800 | 1/3 | innocent=44.3%; innocent_drop=-3.1%; S=42.5%; passive_contract_kills=75.6% | innocent drop >=8pp, S >=45% |

### Magnate Kingmaker Market

| Package | Sample | Gates | Metrics | Failed gates |
|---|---:|---:|---|---|
| Canonical +5/-1 | 800 | 1/3 | approached=83.8%; pivotal=23.4%; M=34.5% | Magnates approached >=85%, broker votes pivotal >=25% |
| Deliberative +3/-2 | 800 | 2/3 | approached=86.0%; pivotal=22.6%; M=32.1% | broker votes pivotal >=25% |
| Outcome-tuned +3/-2 | 800 | 3/3 | approached=86.4%; pivotal=26.2%; M=38.0% | None |

### Faction Lockout & Reveal Pivot

| Package | Sample | Gates | Metrics | Failed gates |
|---|---:|---:|---|---|
| Canonical +5/-1 | 800 | 2/3 | lockout=33.6%; candidate_reveal=97.4% | major-faction lockout <12% |
| Deliberative +3/-2 | 800 | 2/3 | lockout=34.2%; candidate_reveal=96.6% | major-faction lockout <12% |
| Outcome-tuned +3/-2 | 800 | 2/3 | lockout=33.6%; candidate_reveal=96.8% | major-faction lockout <12% |

### Early Victim & Ghost Agency

| Package | Sample | Gates | Metrics | Failed gates |
|---|---:|---:|---|---|
| Canonical +5/-1 | 1188 | 3/3 | early_ghost_win=31.4%; catch_with_ghosts=75.9%; ghost_pivotal=76.9% | None |
| Deliberative +3/-2 | 848 | 3/3 | early_ghost_win=30.3%; catch_with_ghosts=49.5%; ghost_pivotal=72.5% | None |
| Outcome-tuned +3/-2 | 848 | 3/3 | early_ghost_win=34.1%; catch_with_ghosts=50.5%; ghost_pivotal=74.1% | None |

### Debt Crisis & Coalition Bailout

| Package | Sample | Gates | Metrics | Failed gates |
|---|---:|---:|---|---|
| Canonical +5/-1 | 2150 | 1/2 | recovery=89.1%; reckless_with_bankruptcy=0.00; reckless_without_bankruptcy=5.86; reckless_spike=100.0% | debt recovery 50-75% |
| Deliberative +3/-2 | 1923 | 1/2 | recovery=95.8%; reckless_with_bankruptcy=0.00; reckless_without_bankruptcy=11.35; reckless_spike=100.0% | debt recovery 50-75% |
| Outcome-tuned +3/-2 | 1846 | 1/2 | recovery=96.1%; reckless_with_bankruptcy=0.00; reckless_without_bankruptcy=10.57; reckless_spike=100.0% | debt recovery 50-75% |

## Interpretation rule

A package is not recommended merely because its average win rates look good. It must avoid catastrophic conditional branches: automatic Syndicate wins after survival, hopeless games after an early catch, unrewarded Magnate brokerage, inert Ghosts, and debt that is either meaningless or permanent.

Any failed proxy gate becomes a live-playtest observation target. Simulator results can reject arithmetic failures; they cannot certify that a moment felt fun, fair, or socially satisfying.

## Recommended next controlled test

Keep **Canonical +5/-1** as the frozen canonical baseline. Test **Outcome-tuned +3/-2** as one complete package in the next separate playtest; do not mix individual knobs. Compare the comprehension, reaction, participation, Interrogation-confidence, and exit-interview instruments against the frozen baseline.
