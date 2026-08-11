# Staged Contract — fee and limit test

## Mechanic modelled

- Bilateral Contract registered with the GM.
- Both parties pay the tested fee to the Bank and escrow 1 Influence.
- Rounds 1–2: mutual defence if either party is accused at that Council.
- Round 3: nominate the partner where possible and vote for them if they are a
  Candidate.
- Stake returns when the trigger resolves.
- The engine enforces the action; ordinary promises remain non-binding.

This is a mechanical proxy for the proposed fixed-trigger Contract, not evidence that
it improves pacing.

## Clean-table matrix (13 players, paired seeds)

| Fee each | Limit/player | Contracts/game | Syndicate Δ | Magnate Δ | Richest-share Δ | Abuse value |
|---:|---:|---:|---:|---:|---:|---:|
| 0 | 1 | 4.98 | +0.0% | +7.8% | -1.2% | -2.9% |
| 0 | 2 | 7.91 | -7.8% | +0.0% | -1.7% | +1.1% |
| 0 | 3 | 9.01 | -5.8% | +5.0% | -1.4% | +1.9% |
| 0 | ∞ | 9.54 | -7.0% | -1.0% | -1.6% | -0.8% |
| 1 | 1 | 4.95 | -11.0% | -5.8% | -0.1% | +3.3% |
| 1 | 2 | 7.71 | -11.5% | -4.5% | -0.1% | -1.6% |
| 1 | 3 | 8.71 | -13.0% | -2.7% | -1.6% | -2.0% |
| 1 | ∞ | 9.02 | -14.8% | -2.0% | -1.7% | -7.2% |
| 2 | 1 | 4.67 | -12.2% | -7.0% | -0.7% | -2.3% |
| 2 | 2 | 6.88 | -22.5% | -9.5% | +0.0% | -1.5% |
| 2 | 3 | 7.66 | -20.2% | -12.2% | +0.6% | -1.7% |
| 2 | ∞ | 7.79 | -21.8% | -10.7% | +0.6% | -4.8% |

`∞` means no practical per-player cap. Abuse value is the personal win-rate edge for
three seats that Contract as aggressively as legally possible.

## Realistic-chaos check of the viable cells

| Fee | Stake | Player cap | Table cap | Signing | Contracts/game | Syndicate Δ | Abuse value | GM refusals/game |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 0 | 1 | 1 | ∞ | 10% | 2.57 | -2.8% | +2.3% | 1.12 |
| 0 | 1 | 1 | ∞ | 15% | 3.34 | +2.0% | +3.2% | 1.07 |
| 0 | 1 | 1 | 2 | 30% | 2.00 | +2.8% | +3.9% | 1.03 |
| 0 | 1 | 1 | 4 | 30% | 3.94 | +3.2% | +2.3% | 1.04 |

## Refundable escrow sensitivity (fee 0)

| Stake each | Limit/player | Contracts/game | Syndicate Δ | Magnate Δ | Abuse value |
|---:|---:|---:|---:|---:|---:|
| 1 | 1 | 4.98 | +0.0% | +7.8% | -2.9% |
| 1 | 2 | 7.91 | -7.8% | +0.0% | +1.1% |
| 2 | 1 | 4.98 | -6.0% | +3.5% | -2.2% |
| 2 | 2 | 7.70 | -5.3% | +5.5% | +2.2% |
| 3 | 1 | 4.64 | -6.5% | -1.8% | +1.5% |
| 3 | 2 | 7.00 | -3.5% | +5.8% | +0.8% |

## Uptake sensitivity (fee 0, stake 1, limit 1)

| Base signing rate | Contracts/game | Syndicate Δ | Magnate Δ | Richest-share Δ | Abuse value |
|---:|---:|---:|---:|---:|---:|
| 5% | 1.47 | -4.3% | +2.5% | -0.3% | +3.5% |
| 10% | 2.61 | -3.3% | +0.8% | -0.3% | +2.3% |
| 15% | 3.41 | -3.3% | +0.3% | -0.8% | +2.4% |
| 20% | 3.99 | -6.8% | +4.5% | -0.8% | +0.8% |
| 30% | 4.98 | +0.0% | +7.8% | -1.2% | -2.9% |

## Table-wide cap sensitivity (fee 0, stake 1, per-player limit 1)

| Total Contracts allowed | Contracts/game | Syndicate Δ | Magnate Δ | Richest-share Δ | Abuse value |
|---:|---:|---:|---:|---:|---:|
| 1 | 1.00 | -5.5% | +3.0% | -0.1% | -0.1% |
| 2 | 2.00 | -1.8% | -1.0% | -1.0% | +1.5% |
| 3 | 2.98 | -8.3% | +2.8% | -0.7% | +0.4% |
| 4 | 3.94 | -0.8% | -0.3% | -0.9% | +1.7% |

## High-sample confirmation of the selected cap

| Table | Contracts/game | Syndicate Δ | Magnate Δ | Richest-share Δ | Abuse value |
|---|---:|---:|---:|---:|---:|
| Clean | 2.00 | -1.5% | -1.0% | -0.6% | +0.2% |
| Realistic chaos | 2.00 | -2.8% | +3.9% | +0.2% | +1.6% |

## Mechanical recommendation

Selected version: **no fee, refundable stake 1 each, one Contract per player, two
Contracts total per game**.

- Clean high-sample result: Syndicate -1.5%,
  Magnates -1.0%, aggressive-use edge
  +0.2%.
- Realistic-chaos result: Syndicate -2.8%,
  Magnates +3.9%, aggressive-use edge
  +1.6%.

The four-Contract cap also looked mechanically viable, but doubles GM registrations
without evidence of twice the pacing benefit. Two is the lower-complexity choice.
The +3.9-point Magnate result under realistic chaos is a live-playtest watch item.

## What remains unknowable without a table

- whether the ritual actually ends circular negotiations;
- whether registration interrupts the GM too often;
- whether Contracts crowd out informal trust and reciprocity;
- whether two per player feels liberating or bureaucratic.
