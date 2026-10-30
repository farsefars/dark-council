# The Dark Council — Simulator A/B Queue

**Method:** 1,000 paired seeds per player count, counts 10–15 (6,000 games per variant).

These tests answer arithmetic and modelled behavioural questions only. A null result does not prove a rule is unimportant to humans.

## Guilty stakes

| Variant | A | R | Magnate | Syndicate | Deaths | Interrogations | Execution accuracy | Bankruptcies | Winner <40% | Mean winner share | Extra votes bought | Lifetime Ghost votes used |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| +5/-1 (current) | 50.3% | 46.9% | 42.0% | 37.3% | 5.85 | 5.14 | 22.5% | 0.32 | 1.3% | 55.1% | 3.81 | 0.00 |
| +3/-2 | 48.9% | 47.6% | 33.2% | 29.5% | 5.65 | 4.62 | 22.5% | 0.60 | 1.7% | 54.2% | 2.67 | 0.00 |

### Interpretation

Prefer neither from win rates alone. The live instrument must measure voter confidence and whether the current 16.7% break-even encourages low-confidence Guilty votes.

## Election aggregation

| Variant | A | R | Magnate | Syndicate | Deaths | Interrogations | Execution accuracy | Bankruptcies | Winner <40% | Mean winner share | Extra votes bought | Lifetime Ghost votes used |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Three-candidate plurality (current) | 50.0% | 47.6% | 41.5% | 37.2% | 5.82 | 5.13 | 22.5% | 0.33 | 1.4% | 55.2% | 3.88 | 0.00 |
| Top-two runoff | 49.8% | 47.0% | 41.5% | 37.2% | 5.82 | 5.13 | 22.5% | 0.33 | 0.0% | 62.7% | 3.88 | 0.00 |

### Interpretation

The simulator can measure faction outcomes and spoiler frequency; live testing must decide whether a runoff improves legitimacy or merely adds time and another negotiation pause.

## Ghost voting

| Variant | A | R | Magnate | Syndicate | Deaths | Interrogations | Execution accuracy | Bankruptcies | Winner <40% | Mean winner share | Extra votes bought | Lifetime Ghost votes used |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Vote in every Interrogation and Final (current) | 48.5% | 48.6% | 43.9% | 37.7% | 5.83 | 5.12 | 22.9% | 0.32 | 1.1% | 55.3% | 3.83 | 0.00 |
| One lifetime Ghost vote | 47.9% | 48.2% | 41.7% | 38.0% | 6.10 | 4.95 | 20.7% | 0.34 | 0.9% | 58.9% | 3.69 | 6.10 |

### Interpretation

The model conserves a lifetime vote for a strong Interrogation read or the Final. Live testing must decide whether this feels strategic or silences eliminated players.

## Final vote market

| Variant | A | R | Magnate | Syndicate | Deaths | Interrogations | Execution accuracy | Bankruptcies | Winner <40% | Mean winner share | Extra votes bought | Lifetime Ghost votes used |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Flat 3 per vote (current) | 49.5% | 47.8% | 43.1% | 36.3% | 5.85 | 5.17 | 22.7% | 0.32 | 1.6% | 55.3% | 3.87 | 0.00 |
| Escalating 3/6/9/... | 48.4% | 47.1% | 43.1% | 36.3% | 5.85 | 5.17 | 22.7% | 0.32 | 1.4% | 52.7% | 1.03 | 0.00 |
| Flat with max 2 extra | 48.1% | 47.0% | 43.1% | 36.3% | 5.85 | 5.17 | 22.7% | 0.32 | 1.6% | 52.2% | 0.52 | 0.00 |

### Interpretation

Vote-market variants must preserve Magnate bargaining. Lower purchased vote volume is not automatically better if it removes the reason to make Influence deals.

