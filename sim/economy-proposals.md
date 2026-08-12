# Economy recalibration — five proposals for decision

**Status: nothing here is implemented.** The published rulebook is untouched. Every
candidate below exists only as simulator config flags. This document is for you to
decide from.

Method: six specialist economists reviewed the measured data in parallel, then every
proposal was simulated — 150 games × 8 player counts for balance, 250 for threshold
calibration, 80 for the alliance attack. No number below is an opinion; each is measured.
Where the Council disagreed, the disagreement is reported rather than resolved.

---

## 1. The verdict in one table

| | Baseline (today) | A Redenomination | B Closed loop | C Caps & sinks | D Decoupled Syndicate | E Cheap Hit |
|---|---:|---:|---:|---:|---:|---:|
| **Gates passed** | 6/12 | 8/12 | 7/12 | **9/12** | **9/12** | 8/12 |
| Player chips p90 | 240 | 126 | 103 | 111 | 111 | **103** |
| Player chips worst case | 349 | 187 | 176 | 176 | 176 | **168** |
| Stash p90 | 144 | 45 | 43 | 44 | 44 | **32** |
| Richest player p90 | 56 | 33 | 28 | 27 | 27 | **26** |
| Richest player worst case | 184 | 65 | 44 | 44 | 44 | **38** |
| Chips minted per game | 167 | 121 | **109** | 120 | 120 | 120 |
| Hit ÷ bribe capacity (nominal) | 1.81 | **0.64** | **0.69** | **0.66** | **0.66** | 0.40 |
| Hit ÷ bribe capacity (effective) | 3.61 | 1.28 | 1.39 | 1.31 | 1.31 | **0.80** |
| Aristocrat / Reformer | 49/47% | 48/48% | 46/49% | 45/49% | 45/49% | 46/47% |
| Magnate | 35% | 34% | 32% | 33% | 33% | 33% |
| Syndicate | 35% | 30% | 31% | 33% | 31% | 33% |
| **Syndicate under alliance attack** | 12% | 36% | 38% | 32% | **1%** | 40% |
| Purchased votes decide the winner | 8% | 9% | 8% | 6% | 6% | 6% |

Green-ish reading: **C and D tie on gates, but they are not equivalent** — see §4.

---

## 2. Your three problems, and what actually fixes each

### Problem 1 — the chip count. Solved by everything.

Every proposal brings both pools inside your 250-chip budget with room to spare:

- Player pool: **240 → 103–126** at p90; worst case **349 → 168–187**
- Stash pool: **144 → 32–45**; worst case **156 → 39–54**

A 180 / 60 split of your 250 chips covers every proposal, with the worst observed case
still fitting. The Stash no longer needs to be "tracked in writing" — it fits in a real
pile of chips again.

### Problem 2 — the 91-chip stack. Mostly solved, and the fix is one rule.

Sending a dead player's remaining Influence **to the Bank instead of to a chosen heir**
does almost all the work:

| | Richest p90 | Richest worst case |
|---|---:|---:|
| Today (one heir) | 56 | **184** |
| A — still one heir | 33 | 65 |
| C/D/E — estate to the Bank | **27** | **44** |

Note this is the single highest-leverage line in the whole exercise: it cuts the worst
case by 76% on its own. Shrinking the numbers alone (A) still leaves someone holding 65.

**It does not fully clear your bar.** The target was "no player over 25"; the best
proposal reaches 26–27 at p90 and 38–44 at worst. Whether a 27-chip stack is
"manageable to handle and count" is your call — it is roughly five stacks of five.

### Problem 3 — the bribe/hit tension. This is where you have a real choice.

Today one Hit is worth 40 against a Faction's 23 — bribery is impossible. Every proposal
fixes that on paper. But **how much** to fix it is a genuine fork, and the simulator
cannot settle it. See §3.

---

## 3. The one question the simulator cannot answer for you

The Council split down the middle on a single number: **how much of a Faction's wealth
can actually be assembled into a bribe inside one Private Phase?**

- The **mechanism designer** used nominal liquidity (~15 in the new economies). On that
  reading, a Hit should be worth **10**.
- The **bargaining economist** argued nominal is a fantasy: contributors must be found
  across a house, agreements are not binding, everyone free-rides, and the Assassin can
  take the money and kill anyway. He discounted to roughly **half**, and on that reading
  a Hit should be worth **6**.

Both cannot be right, and the difference decides the design:

| Hit value | Bribe on nominal reading | Bribe on effective reading | Syndicate under alliance attack |
|---:|---:|---:|---:|
| 5 | 0.33 too cheap | 0.65 live | 45% |
| **6** | 0.40 too cheap | **0.78 live** | 42% |
| 8 | 0.52 too cheap | 1.04 borderline | 35% |
| **10** | **0.65 live** | 1.30 impossible | 34% |
| 14 | 0.90 live | 1.79 impossible | 29% |
| 40 (today) | 1.81 impossible | 3.61 impossible | 12% |

**And there is a structural sting in the tail.** The price of a bribe and the cost of
skipping a Hit are *the same quantity*. So making the bribe affordable necessarily makes
it cheap for the Assassin to abandon Hits and serve an ally. The table above shows it
directly: as the Hit gets cheaper, the alliance gets more profitable (12% → 45%).

Under an Influence-based Syndicate victory, **you cannot have both.** That is not a
tuning failure; it is arithmetic.

Proposal D is the only way out, because it changes what the Syndicate is scored on.

---

## 4. C versus D — the cleanest comparison in this document

C and D are **identical in every parameter except the Syndicate's victory condition**.
Same chips, same thresholds for Magnates, same balance, same everything. So the
difference between them isolates one variable perfectly:

| | C — Influence victory | D — Hits victory |
|---|---:|---:|
| Syndicate wins honestly | 33% | 31% |
| **Syndicate wins by ignoring Hits to serve an allied Faction** | **32%** | **1%** |

Under C, abandoning the Hit to serve a Faction pays exactly as well as playing straight.
Under D it is close to fatal — because the Stash can *only* be filled by completing Hits,
and personal hoarding no longer counts toward victory.

This is the mechanism your last playtest feedback was complaining about, and D is the
only candidate that closes it while keeping the bribe affordable.

---

## 5. The proposals

### A — Redenomination
*Shrink every number, change nothing structural.*

Starting Influence 4→3, Motive 5→3, Ambition 10→5, Guilty-vote reward 5→3, vote cost
3→2, Hit payout 40→10. Magnate thresholds 11–23, Syndicate 48–55.

- **Buys:** the smallest possible change — pure numbers, no new rules to teach. Fixes the
  chip count outright.
- **Costs:** leaves concentration half-fixed (someone still holds 65 in the worst case),
  and makes the Faction–Syndicate alliance *more* profitable than today (36% vs 12%).
- **Weakest point:** it fixes the symptom you named and worsens the one you named last week.

### B — Closed loop
*Fund the Guilty-vote reward from the executed player's estate rather than the Bank.*

- **Buys:** the lowest minting of any proposal (109/game) and genuinely circular money.
- **Costs:** median wealth falls to 4.9, below your comfortable-counting band. And the
  adversarial economist ranked this **the most exploitable of the five**: if the room is
  paid from the estate, the profitable target is the *richest* player rather than the
  *guiltiest*. "Kill the whale" becomes rational, and a player who sees execution coming
  can dump chips on an ally first to deny the room its reward.
- **Weakest point:** it turns the Interrogation from a deduction mechanic into an
  extraction mechanic. The behavioural economist independently objected that a variable
  "share of the estate" cannot be reasoned about before voting, whereas a flat "+3 if you
  are right" can.
- **My read: do not adopt.** It was worth testing and it failed.

### C — Caps and sinks
*A dead player's remaining Influence goes to the Bank instead of to a chosen heir.*

- **Buys:** the concentration fix (worst case 184 → 44) for one sentence of rule text.
  Best-in-class on gates.
- **Costs:** removes the dying player's last act of kingmaking, which is currently a real
  social moment. Player-to-player circulation drops from 47 to 29 per game — the economy
  gets quieter.
- **Weakest point:** does nothing about the alliance (32% under attack).

### D — Decoupled Syndicate
*Everything in C, plus: the Syndicate wins on Hits completed and a Stash that only Hits
can fill.*

Victory becomes: **the Assassin is alive, at least 2 of 3 Hits succeeded, and the Stash
has reached 40.** Personal Influence no longer counts toward Syndicate victory.

- **Buys:** everything C buys, plus it is the only proposal that makes the
  Faction–Syndicate alliance unprofitable (**1%** vs 32%) while keeping the bribe
  affordable. And it replaces "reach 152 Influence" — a number no player can feel progress
  toward — with a target the whole room can follow.
- **Costs:** the largest conceptual change. Laundering needs re-purposing. The tuning dial
  is steep: a Stash floor of 36 gives a 56% Syndicate win rate, 40 gives 32%, 44 gives 8%.
  That is a knife-edge, and it means this number must be confirmed in live play rather
  than trusted from simulation.
- **Weakest point:** the bribe becomes *state-dependent*. Skipping an early Hit is
  survivable, so an early bribe is payable; skipping a late one can be fatal, so a late
  bribe is not. The mechanism designer flagged this as a risk; I think it is arguably
  better drama — bribery has a season — but you should decide that deliberately rather
  than inherit it.

### E — Cheap Hit, live bribe
*Everything in C, with the Hit worth 6 instead of 10.*

- **Buys:** the only proposal that satisfies the bribe test on the pessimistic
  (bargaining) reading — 0.80, squarely in the live band. Also the lightest table: 103
  chips at p90, Stash 32, richest 26.
- **Costs:** the alliance becomes the most profitable of any candidate (**40%**), and on
  the optimistic reading the bribe is now too cheap (0.40) — the Assassin should just take
  the money every time.
- **Weakest point:** it optimises your stated intent and sacrifices the thing you
  complained about a week ago.

---

## 6. Two gates nothing passes — you should know before deciding

### Purchased votes almost never matter, and cheaper votes will not fix it

Target was 20%; every proposal lands at **6–9%**, and halving the vote price made it
*worse*, not better. The public choice economist predicted cheaper votes would push
decisiveness to 25–30%. **Measurement refuted him.**

The diagnosis: only **1.7 players buy any votes at all**, buying **4.5 extra votes**
between them, against ~13 free votes. A quarter of games see zero purchases. Players only
buy votes when they *believe* a Candidate is their own Faction — and Faction knowledge is
scarce. **The binding constraint is information, not price.**

So "Influence buys votes" is currently a much weaker indirect win condition than your
design intends, and it cannot be fixed from the economy. It needs an information or
ballot-access change, which is a separate decision.

### The 25-chip handling target

Best achieved is 26–27 at p90 and 38–44 at worst, versus today's 56 and 184. A large
improvement, not a clean pass. Getting under 25 reliably would need a hard holding cap,
and the adversarial economist showed caps are evadable by parking chips with allies and
create a "spend it or lose it" cliff. I did not pursue it.

---

## 7. Where the Council disagreed

1. **Nominal versus effective bribe capacity** — the fork in §3. Mechanism design said
   Hit 10–16; bargaining said 6–8. Unresolvable by simulation; it depends on how well real
   players coordinate under time pressure. **This is the main thing a playtest should
   settle.**
2. **Decoupling the Syndicate** — behavioural strongly for ("complete the Hits" is
   dramatically clearer than "reach 152"); public choice against (removes a bidder from
   the Influence market, making it less contested); mechanism warned it makes bribes
   state-dependent; adversarial warned a naive "all three Hits" is brittle and blockable.
   **The 2-of-3-plus-Stash-floor form tested here is a direct response to those
   objections** — measured, it neither collapses nor dominates.
3. **Variable versus fixed rewards** — monetary wanted estate-funded rewards to stop
   minting; behavioural and adversarial both objected. Measurement sided against it (B).
4. **Bequest splitting** — monetary proposed splitting the estate among all living
   players; adversarial showed that turns killing into faction-wide funding and rival
   dilution. C and D therefore retire it to the Bank instead, which was the adversarial
   economist's counter-proposal.

---

## 8. My recommendation

**Adopt D**, with one reservation stated up front.

Reasoning, in order of weight:

1. It is the only candidate that resolves the §3 arithmetic. Every Influence-scored
   proposal forces you to choose between an affordable bribe and a resistant alliance. D
   is the only one that gives you both, and it does so by fixing the underlying cause
   rather than trading the two off.
2. It ties for best on gates while producing the cleanest table: 111 chips at p90, Stash
   44, nobody over 44 in the worst case.
3. Its victory condition is the only one a player can actually feel progress toward,
   which matters for a game where the room needs to sense a rising threat.

**The reservation:** D's Stash floor of 40 is a steep dial — 36 gives 56%, 44 gives 8%.
Simulation is weakest exactly where a number is most sensitive, so I would treat 40 as
provisional and expect to adjust it after one live game.

**If you reject D as too large a change,** take **C**. It fixes the chips and the 91-chip
stack for one sentence of rule text, and leaves the alliance question open for a separate
decision. It is the safe, honest partial fix.

**Do not take B.** It failed on measurement and on two independent Council objections.

---

## 9. What adoption costs, per proposal

| Proposal | Rule sections touched | Size |
|---|---|---|
| A | §4 economy numbers, §5 goal rewards, §6 Interrogation rewards, §9 vote cost, §11.3 Hit payout, §12.1 scaling table | Numbers only — no new concepts |
| B | A's changes, plus §6.2 rewritten so Guilty voters share the estate | Numbers + one reworked mechanic |
| C | A's changes, plus §8 step 2 ("gives all remaining Influence to one living player of their choice" → returns to the Bank) | Numbers + one sentence |
| D | C's changes, plus §10 Syndicate victory rewritten, §11.2 Stash re-framed as a scoreboard only Hits can fill, §11.5 Laundering re-purposed | Numbers + one concept |
| E | Identical to C, different Hit value | Numbers + one sentence |

All five also require the §12.1 scaling table to be regenerated, and the playtest aids and
teaching script updated to match. None of that is done.

---

## 10. What this document cannot tell you

- **Whether a bribe actually happens at a real table.** The simulator models chips, not
  persuasion. The entire §3 fork rests on a human coordination question.
- **Whether 27 chips feels manageable.** That is a physical judgement.
- **Whether "2 Hits and a full Stash" teaches well.** The behavioural economist argued it
  is far clearer than 152; that is a claim about people, not about the model.
- **The alliance attack is deliberately pessimistic.** It assumes a perfectly coordinated
  faction with complete knowledge of the Assassin. The allied Faction wins 76–93% in every
  candidate including today's, because bloc voting is a *voting* problem the economy
  cannot reach. Only the Syndicate's own win rate under attack is an economic signal, and
  that is the column reported.
