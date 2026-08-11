# Testing methodology

## Scope

The simulator answers mechanical questions only. It does not validate enjoyment,
comprehension, persuasion, conflict, table presence or replay intent.

## Experimental rules

1. **Published rules first.** The canonical configuration must match both current
   rulebooks.
2. **Paired seeds.** Every variant comparison uses the same seeds.
3. **Isolated knowledge.** Policies receive player knowledge and public state only.
4. **Separate randomness.** Deal, ordinary policy and chaos streams are seeded
   independently.
5. **No silent failures.** Illegal attempts are refused and counted.
6. **No conclusion from a null alone.** “No simulated effect” may mean “not modelled.”

## Test layers

### 1. Correctness

Conservation, setup, information isolation, rule values, action eligibility, Final
sequencing and outcome accounting.

### 2. Sensible-player baseline

Runs the five personas across 8–15 players. Measures balance, reachability and
participation under competent play.

### 3. Chaos robustness

Runs the same deals with imperfect behaviour at 0%, 12% and 30%. Measures GM
refusals, illegal attempts, forgotten actions and whether balance survives noise.

### 4. Adversarial exploits

Seats one to three strictly legal exploiters and compares their personal results with
the same seats under honest policy.

The permanent catalogue covers:

1. debt squatting;
2. Syndicate debt immunity;
3. coordinated Expose vote-stripping;
4. Interrogation cost griefing;
5. nomination cartel;
6. blanket kill-tell;
7. Final vote dump;
8. Ghost bloc;
9. Stash shelter.

## New published-rule metrics

- living voter opportunities and exclusions;
- exclusion rate per Interrogation;
- repeat exclusion in a later round (poverty spiral);
- Expose attempts and eligibility refusals;
- all GM-refused illegal attempts;
- debt by cause;
- ally rescue transfers and debt cleared;
- Bankruptcy locked at the start of the Final;
- exploit value by Faction, Role and persona.

## Interpretation

- A high exclusion rate is a human-playtest warning, not an automatic rule change.
- A positive exploit value means the written strategy deserves review.
- Debt deterrence succeeds when deliberate debt does not improve the debtor's outcome.
- Results must distinguish Faction, Role and personal victory. In particular, a
  Syndicate member already lacks a Faction Victory, so ordinary Bankruptcy may impose
  little or no additional cost.

## Unresolved rule questions

The report must surface, not silently decide:

1. whether a negative Magnate balance subtracts from combined Magnate Influence or is
   floored at zero; and
2. whether Bankruptcy should impose any consequence beyond negative Influence on
   Syndicate Victory.
