# The Dark Council — Design Decisions Log

This log records why non-obvious rules exist. It is evidence for the load-bearing
analysis, not a claim that every decision is permanent.

## Evidence levels

- **P1 — Live playtest:** observed with real players.
- **P2 — User-confirmed intent:** the designer has explicitly confirmed the purpose.
- **S — Simulation:** supported by the current behavioural model.
- **A — Agent/adversarial test:** supported by isolated reasoning tests.
- **R — Research:** supported by the social-deduction research report.
- **U — Unvalidated:** plausible design rationale, not yet tested live.

## Established decisions

| Element | Decision and purpose | Evidence | What failed or would fail without it | Revisit when |
|---|---|---|---|---|
| Bankruptcy | Negative balances are recorded; future income repays them; a player still negative at the Final cannot be a Candidate or personally win with their Faction. | **P1, P2** | Players willingly paid costs for others while at zero balance because taking debt had no consequence. This removed scarcity and let one player externalise another's costs. | Only if another enforceable rule prevents proxy-paying and preserves scarcity. |
| Magnate victory | Magnates pursue a combined Influence threshold rather than the election. Their wealth makes them intentional swing voters and deal partners. | **P1, P2** | Removing the independent economic objective removes the incentive for Aristocrats and Reformers to court Magnates for election and Execution votes. | If live observation shows Magnate deals are arbitrary, one-sided, or exclude one Magnate. |
| One Expose per Secret | A correctly Exposed Secret becomes public and cannot be scored again. | **S, A** | Repeated Expose farming produced 52% of all Influence destruction. | If Expose becomes too rare after live use. |
| Cumulative kill tell | Any qualifying transfer at any earlier point in the game can enable an assassination. | **S, A** | A same-round requirement made the victim's donor list a near-direct pointer to the Assassin. | If the transfer history becomes impossible to adjudicate physically. |
| Either Syndicate member may pay the tell | The Assassin or Accomplice may make the qualifying transfer. | **S, P2** | Assassin-only payment left a uniquely identifying trail. A courier preserves a real physical trail without naming the killer. | If the Accomplice becomes a disposable payment mule with no counterplay. |
| Private Ghost answer | The GM answers the Ghost question privately; Ghosts must persuade the living. | **S, R** | A public truthful answer became free hard proof and sharply reduced Syndicate survival. | If Ghost persuasion is consistently ignored or frustrating. |
| Ghost participation | Ghosts retain Interrogation and Final votes and one shared private question each Council. | **P2, R, U** | Full elimination risks creating bored spectators. | Compare with a one-lifetime Ghost vote in simulation, then validate feelings live. |
| Guilty-vote stakes | Living Guilty voters gain +5 for executing the Assassin and lose 1 for executing an Innocent. | **S, U** | Interrogation did not improve innocent outcomes; hunting the Assassin was not rewarded. | The +5/-1 break-even confidence is only 16.7%; simulate +3/-2 and observe confidence live. |
| Successor lead | When an Assassin is Executed, the GM gives one true statement about the surviving Syndicate member. | **S, U** | Catching the Assassin otherwise advanced the Syndicate succession without giving the room enough progress. | If Promotion becomes either a solved puzzle or an erased achievement. |
| Untouchable inherited Stash | The Stash survives the Assassin's Execution and is split only if both Syndicate members die. | **P2, S** | Confiscating it on the first Execution made early Laundering negative expected value and erased the Accomplice's inherited operation. | If the inherited total makes Promotion feel hopeless for innocents. |
| Two-way Stash | The current Assassin may withdraw up to 2 per round. | **S, U** | A one-way Stash was passive bookkeeping rather than a choice between victory progress and operating cash. | If withdrawals create too much GM load or become automatic. |
| Three Candidates | The three richest living players each nominate a distinct Candidate. | **S, P2** | With two Candidates, a whole Faction was excluded in 66.3% of simulated Finals; three reduced this to 38.9%. | Compare plurality with a top-two runoff; observe spoiler outcomes live. |
| Reveal after nominations | Candidates are chosen before the room spends its Reveal. | **S, P2** | Revealing first could spend the only hard Faction information on someone irrelevant to the ballot. | If every Reveal becomes an automatic Candidate reveal. |
| Bounded Evidence noise | Five Evidence statements exist; exactly two are false; Auction Evidence is truthful. | **P2, R** | Players reported difficulty assessing Evidence without knowing its reliability budget. | If two false statements create either certainty or random noise. |
| Mandatory exact Evidence disclosure | After an Execution, Evidence holders read their original statements word for word. | **P1, R** | Paraphrase and selective disclosure make the signal impossible to audit and increase memory disputes. | If repeated readings slow Council without changing beliefs. |
| Goals v2 | Espionage requires a full Motive+Ambition profile; Blackmailer uses extortion; Commerce has a Round 2 deadline; Radical tracks Guilty votes on executed players. | **S, A** | Old Espionage was often pre-satisfied, Blackmailer completed in 0.7%, Commerce was impossible by its deadline, and Radical lacked personal agency. | After live completion and enjoyment data exist. |
| Goal dealing caps | Collector is dealt at most once; Vanity at most three times. | **S** | Goals were dealt more often than available completion slots. | If Auction/Leaderboard structure changes. |
| Hidden Faction network | Players are not told their Faction members at setup; each learns one outsider instead. | **P2, R** | Guaranteed ally chains reduce uncertainty and undermine the Magnate bluff. | If players cannot form any reliable coalition by the Final. |
| Syndicate placement | Exactly one Aristocrat and one Reformer; Magnates are never Syndicate. | **P2, R** | Preserves cross-faction suspicion while allowing a Magnate claim to function as a bluff. | If Magnate public innocence over-centralises claims. |
| Physical enforceability | Rules must be enforceable by a GM in a house using physical chips and player memory. | **P2** | Frame effects, retroactive payment rewriting, and self-referential Evidence inheritance could not be adjudicated honestly. | Never relax without adding a real physical record or component. |

## Known model limitations

- The simulator cannot model proxy-paying from zero, so it cannot validate Bankruptcy.
- Coded Syndicate players do not initiate accusations as camouflage, although a human
  Assassin did so in an isolated agent test.
- The simulator models social tendencies, not persuasion, tone, charisma, fatigue,
  memory disputes, or whether a mechanic creates a memorable moment.
- A null simulation result means the behaviour may be absent from the model. It is
  never, by itself, permission to remove a rule.

## How to add an entry

Record:

1. the exact rule or design choice;
2. the behaviour it creates or prevents;
3. the strongest available evidence level;
4. what happened without it, if known;
5. the condition that would justify reopening it.
