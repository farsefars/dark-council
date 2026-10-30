# The Dark Council — Research Implementation Summary

## Outcome

The approved methodology has been implemented as far as possible without a live group.

- Every major rule element received Tier 1–4 load-bearing analysis.
- **No element classified as safely Decorative.** No gameplay rule was cut.
- The correct comprehension intervention is presentation: separate references,
  six-minute layered teaching, just-in-time Auction/Final rules, and external GM logs.
- English and Ukrainian playtest materials are ready.
- The balancing engine now grades complete rule packages across **10 outcome
  scenarios**, rather than relying on aggregate win rates alone.

## Outcome-based balance engine

The engine now models:

- mixed, mob, passive, broker-heavy, and random table compositions;
- stake-sensitive Guilty voting and threshold-aware Final spending;
- Magnate vote-brokerage deals and Round 3 coalition debt rescue;
- balanced, Courier Shield, Contract Strict, Headhunter, and Martyr Launder
  Syndicate doctrines;
- the Round 2 zero-bid Auction fallback, public nomination-right tiebreak, and
  equal rounded-down Stash distribution on full Syndicate wipeout.

Final benchmark: **100 games per player count (8–15), per scenario, per package**,
with rare Early Catch outcomes oversampled fourfold.

| Package | Gates passed | Full scenarios passed |
|---|---:|---:|
| Canonical +5/-1 | 22/36 | 1/10 |
| Deliberative +3/-2 | 22/36 | 1/10 |
| **Outcome-tuned +3/-2** | **26/36** | **3/10** |

The outcome-tuned package is **+3/-2 Guilty stakes, Interrogation base 3,
Magnate thresholds reduced by 2, and Syndicate thresholds increased by 3**. It
passed all Standard House Party gates: Aristocrat 45.1%, Reformer 45.4%,
Magnate 30.0%, Syndicate 28.6%, 84.8% close finishes, and 6.1% triple
co-victories.

This is the strongest package for a separate controlled playtest. It is **not**
an automatic rulebook change.

### 12-player decision for October 31, 2026

A subsequent **2,000-game paired ablation at exactly 12 players** found:

| Package | Magnate | Syndicate | Executions | Round 1 Assassin catch |
|---|---:|---:|---:|---:|
| Canonical +5/-1, base 4, M24/S40 | 35.7% | 36.8% | 2.77 | 12.7% |
| +5/-2 only, base 4, M24/S40 | 27.9% | 34.4% | 1.98 | 4.9% |
| Outcome-tuned +3/-2, base 3, M22/S43 | 29.0% | 29.2% | 1.36 | 0.7% |

Because real players also face social hesitation that the simulator cannot model,
the October 31 live game keeps the **canonical +5/-1 package**. Voter confidence is
recorded before truth is revealed; no balance variable changes during the game.

Persistent failures under every tested package:

- Guilty voters did not gain the intended long-run personal-win advantage after
  an Early Catch.
- Contract success did not create a strong enough separation between weak and
  strong surviving-Assassin outcomes.
- Courier Shield execution accuracy stayed below 18%.
- Wrong mob voters did not underperform and Bankruptcy remained rare.
- Passive players were not mechanically punished for inactivity.
- Major-faction Candidate lockout remained about one-third of Finals.
- Early debt recovery was too easy (89–96%), although disabling Bankruptcy
  caused reckless zero-balance actions to spike.

## Critical correctness finding

The playable rulebooks say a wrong Guilty voter loses **1 Influence**. The recommended
simulator config had used **2**, so the old “Magnate 35% / Syndicate 30%” result tested
a different game.

Corrected +5/-1 baseline, 8,000 games across 8–15 players:

| Aristocrat | Reformer | Magnate | Syndicate |
|---:|---:|---:|---:|
| 48.1% | 49.1% | 40.0% | 36.2% |

The gate now asserts the canonical penalty and tests ten configurations.

## A/B conclusions

| Question | Result | Decision before live evidence |
|---|---|---|
| +5/-1 vs +3/-2 | +3/-2 produced Magnate 32.0%, Syndicate 29.1%, and raises rational Guilty confidence from 16.7% to 40% | Keep written +5/-1 for the baseline playtest; record confidence. +3/-2 is the leading next variant. |
| Plurality vs top-two runoff | Faction outcomes barely moved; winner share rose 55.2%→62.7% | Keep plurality; flag winners below 40% and ask about legitimacy. |
| Every Ghost vote vs one lifetime | Lifetime limit reduced execution accuracy and increased deaths | Keep current Ghost votes; validate engagement rather than restricting early. |
| Flat vs escalating/capped vote buying | Extra votes fell 3.87→1.03/0.52; simulator cannot measure Magnate bargaining quality | Keep flat price for the baseline playtest and observe whether wealth feels negotiated or overwhelming. |

## Controlled live-playtest rule

Use the current written rules as the frozen baseline and the prepared instruments.
Do not alter a variable mid-game.

The first baseline game must still record:

1. collect every voter's confidence after commitment and before truth reveal;
2. note whether players vote Guilty below 40% confidence;
3. interview whether -1 felt negligible or fair;
4. measure Candidate lockout, Courier Shield clues, passive-player agency, debt
   recovery, and whether every Magnate is courted.

If the baseline instrumentation is usable, test the **complete outcome-tuned
package** in a separate game. Do not test its four changes independently.

## Artifact map

### Design evidence

- `design-decisions.md`
- `dependency-map.md`
- `exploit-probe.md`
- `removal-probe-results.md`
- `load-bearing-classification.md`
- `complexity-audit.md`
- `simulation-ab-results.md`
- `scenario-balance-report.md`

### Playtest materials

- `teaching-script-en.md` / `teaching-script-ua.md`
- `player-reference-en.md` / `player-reference-ua.md`
- `syndicate-reference-en.md` / `syndicate-reference-ua.md`
- `gm-reference-en.md` / `gm-reference-ua.md`
- `playtest-kit-en.md` / `playtest-kit-ua.md`
- `generate_deal.py` / `test_generate_deal.py`
- `deal-12p-en.md` / `deal-12p-ua.md`
- `deal-12p-private/` (GM master keys and 24 individual UA/EN player cards)

## Work that requires humans

- Run the instrumented game.
- Confirm actual rules comprehension.
- Map reactions and dead time.
- Measure participation and Magnate deal access.
- Interview agency, Ghost experience, and satisfaction.
- Recalibrate simulator personas from observed behaviour.
