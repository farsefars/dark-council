# Whole-system balance scorecard

**Frozen baseline:** restored stable economy (`a581b50`).  
**Sample:** 100 games x 6 player counts (10, 11, 12, 13, 14, 15); first seed 1900000.  
**Method:** baseline and candidate use identical seeds. Simulation is a rejection test, not proof of fun or clarity.

## Headline scorecard

| Metric | Baseline |
|---|---:|
| Aristocrat win | 50.2% [46.2%, 54.2%] |
| Reformer win | 47.5% [43.5%, 51.5%] |
| Magnate win | 40.3% [36.5%, 44.3%] |
| Syndicate win | 36.7% [32.9%, 40.6%] |
| A/R gap | 2.7% |
| Zero-agency players | 1.1% |
| Bank to players | 184.85 |
| Players to Bank | 94.44 |
| Player circulation | 70.13 |
| Peak physical pool p90 | 179.00 |
| Peak physical pool worst | 257.00 |
| Richest holding p90 | 42.00 |
| Richest holding worst | 64.00 |
| Vote buyers/game | 1.52 |
| Purchased votes/game | 3.34 |
| Purchased votes decisive | 8.5% |
| Hit success | 95.1% |
| Hit reward | 3.00 |
| Effective Faction liquidity | 15.64 |
| Hit/effective bribe | 0.19 |
| Correct-execution injection/game | 25.20 |
| Deaths/game | 5.72 |
| Inheritance/game | 28.02 |
| Social transfer/game | 42.11 |
| Social pairs/game | 24.73 |
| Games with social transfer | 100.0% |
| Evidence disclosures/game | 2.87 |
| Verified Factions/player | 4.05 |

## Invariant gates

| Invariant | Result | Evidence |
|---|---|---|
| I1 Agency | **PASS** | 1.1% of players recorded no modelled agency |
| I2 Inheritance | **PASS** | 28.0 Influence inherited per game |
| I3 Physical playability | **FAIL** | p90 pool 179/250; p90 holding 42/30 |
| I4 Assassin triangle | **FAIL** | Hit/effective bribe 0.19; execution reward 25.2; Assassin alive 73.5% |
| I5 Influence matters | **FAIL** | Magnate 40.3%; purchased votes decisive 8.5%/20% |
| I6 Social over arithmetic | **PASS** | social transfers in 100.0% of games; 24.7 distinct directed pairs |
| I7 Teachability | **PASS** | baseline adds no concepts |
| I8 Symmetry and viability | **PASS** | A/R gap 2.7%; range 36.7%-50.2% |

## Player-count view

| Players | Aristocrat | Reformer | Magnate | Syndicate | Pool p90 | Holding p90 | Zero agency |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 10 | 53.0% | 42.0% | 44.0% | 32.0% | 130 | 40 | 1.1% |
| 11 | 55.0% | 42.0% | 41.0% | 26.0% | 139 | 43 | 0.8% |
| 12 | 41.0% | 58.0% | 43.0% | 39.0% | 162 | 42 | 1.2% |
| 13 | 47.0% | 50.0% | 47.0% | 42.0% | 164 | 42 | 1.1% |
| 14 | 53.0% | 47.0% | 35.0% | 31.0% | 202 | 41 | 1.0% |
| 15 | 52.0% | 46.0% | 32.0% | 50.0% | 198 | 43 | 1.2% |

## Pacing

| Round | Meaningful modelled actions/game | Deaths/game | Goals claimed/game |
|---:|---:|---:|---:|
| 1 | 18.48 | 2.01 | 3.88 |
| 2 | 13.86 | 2.03 | 4.30 |
| 3 | 10.64 | 1.68 | 0.00 |

## Interpretation limits

- The scorecard measures modelled behaviour, not persuasion quality, enjoyment, clarity, or desire to replay.
- `Hit/effective bribe` uses end-of-Council major-Faction liquidity averaged across all rounds, then discounts it by 50%. The timing and discount are explicit bargaining assumptions, not discovered facts.
- `Purchased votes decisive` is conservative: it asks whether stripping paid weight from the same first-round choices changes the winning Faction.
- Complexity and teachability require manual rules review for every candidate.
- Acceptance thresholds are guardrails. They must be revised from live-playtest evidence rather than tuned until a preferred package passes.
