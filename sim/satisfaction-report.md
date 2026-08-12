# Satisfaction diagnostics

## What this report can say

The simulator measures mechanical conditions that support or undermine satisfaction.
It cannot measure fun, comprehension, social standing, memorable moments or whether a
win feels deserved.

## Information Arc: execution accuracy by round

| Round | Accuracy | Executions/game | Deaths/game |
|---:|---:|---:|---:|
| 1 | 21.1% | 0.93 | 1.93 |
| 2 | 24.7% | 0.92 | 1.89 |
| 3 | 36.2% | 0.68 | 1.57 |

The accuracy curve rises materially from
Round 1 to Round 3. 35.8% of simulated deaths occur in Round 1.

## Personal arcs

### Motive completion

| Motive | Completion |
|---|---:|
| COMMERCE | 27.6% |
| ESPIONAGE | 60.9% |
| VANITY | 38.4% |
| WRATH | 30.9% |

### Ambition completion

| Ambition | Completion |
|---|---:|
| BLACKMAILER | 36.4% |
| COLLECTOR | 20.8% |
| DIPLOMAT | 32.1% |
| RADICAL | 21.2% |

## Consequential-agency proxy

- Players with no completed Goal, successful Expose, initiated Interrogation or
  meaningful transfer: **0.8%**
- Mean share of positive living Influence held by the richest player:
  **35.4%**

This is not a satisfaction score. It identifies players for whom the model recorded no
state-changing personal action.

## Pacing and Round 3 objective variants

| Variant | Ambitions/game | Zero-agency | Richest share | Syndicate |
|---|---:|---:|---:|---:|
| Prior 30/30/30, deadline R2 | 3.43 | 0.8% | 35.4% | 35.8% |
| Published 30/45/60, deadline R2 | 3.49 | 0.8% | 35.7% | 36.6% |
| 30/30/30, deadline R3 | 4.63 | 0.8% | 34.0% | 40.8% |
| Extended phases + deadline R3 | 4.64 | 0.8% | 34.1% | 41.5% |

## Interpretation

1. **Information Arc:** Late executions are more grounded than early ones.
2. **Early elimination:** Round 1 creates 35.8% of deaths; those players spend
   most of the remaining game without economic actions.
3. **Goal vacuum:** extending the Ambition deadline changes completion from
   3.43 to
   4.63 per game.
4. **Longer social time:** 30/45/60 phases change zero-agency from
   0.8% to
   0.8%. The simulator can model more
   conversation opportunities, but not whether the longer phase feels necessary or slow.

## Recommendation

1. **Extended social phases:** 30/45/60-minute Private Phases with 5-minute and
   1-minute warnings. This reflects the observed need for more interaction as the
   15-player information network grows denser. The next live test must measure whether
   the added time produces more useful conversations rather than repetition.
2. **Do not simply extend Ambitions to Round 3.** It raises Ambition completion by
   1.21
   per game but also raises the Syndicate rate from
   35.8% to
   40.8%. The
   extra Round 3 income is not balance-neutral.
3. **Keep the current information schedule for now.** Accuracy rises from
   21.1% to 36.2%; the deduction funnel works. The live
   question is whether the 35.8% of deaths occurring in Round 1 still feels too early.
4. **Do not add a general agency mechanic.** The zero-agency proxy is only
   0.8%. Ghost satisfaction remains a human
   experience question, not evidence of a whole-table agency failure.
5. **Investigate Ambition design rather than its deadline.** Collector and Radical are
   the weakest (20.8% and
   21.2%); targeted rewrites are safer than injecting +10
   Influence during Round 3.

## Human checks still required

- Can every player explain why they lost?
- Does each player identify at least one choice that mattered?
- Are Round 3 negotiations urgent or rushed?
- Do Ghosts still feel involved after losing economic actions?
- Do late Executions feel earned?
