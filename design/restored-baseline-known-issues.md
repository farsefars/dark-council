# Restored baseline: known issues

The stable economy was restored from `a581b50`. These issues were deliberately
reintroduced with that exact tree and are recorded rather than silently mixed into the
revert.

## R1 - GM setup wording contradicts the scaling table

`playtest/gm-reference-en.md` and `playtest/gm-reference-ua.md` tell the GM to randomly
assign an extra major-Faction seat. The current scaling table always assigns equal
Aristocrat and Reformer counts, so there is no extra seat to assign.

**Effect:** documentation only; no balance or simulation effect.  
**Proposed later fix:** remove the stale instruction and tell the GM to use the selected
row's equal Faction counts. This should be a separate one-line rules-aid correction, not
part of an economy package.

## R2 - Unreachable random seat-swap branch

`sim/engine.py` contains:

```python
if a != r and self.rng.random() < 0.5:
    a, r = r, a
```

No current `SCALING` row has unequal Aristocrat and Reformer counts, so the branch cannot
run.

**Effect:** none in the current rules. It is dead code and a misleading description of
the setup.  
**Proposed later fix:** remove it with R1 after the documentation correction is approved.

## R3 - The stable engine lacked whole-system measurements

The restored engine did not expose physical chip peaks, Bank injection and retirement,
player circulation, or whether purchased votes changed the winning Faction.

**Effect:** no gameplay effect, but it made local tuning easier than system-level
assessment.  
**Resolution:** passive counters and `sim/scorecard.py` now measure these values. No
decision branches read the counters.

