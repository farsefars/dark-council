# The Dark Council — Load-Bearing Classification

This combines:

1. Tier 1 design history;
2. Tier 2 dependency mapping;
3. Tier 3 adversarial absence probes;
4. Tier 4 paired simulator removal probes.

Rules are grouped only where they cannot be removed independently. **Unknown is
protected**, not a synonym for unimportant.

## Verdict definitions

- **Load-bearing:** removal has a named, evidenced consequence.
- **Structural:** other rules depend on it; remove only as a cluster.
- **Decorative:** no consequence found at any tier.
- **Unknown:** evidence is insufficient or the simulator cannot represent the purpose.

## Classification

| Section / element | Verdict | Strongest evidence | Tier 4 result | Reason |
|---|---|---|---:|---|
| §0 concise premise and win summaries | Load-bearing | Tier 3, comprehension | Not modelled | Prevents experienced players exploiting rules asymmetry and clarifies personal vs Faction defeat. |
| §0 innocent/Syndicate/GM reading boundary | Load-bearing | Tier 3, physical secrecy | Not modelled | Prevents operational rules leaking to innocents and reduces required reading. |
| §1 fixed three-round phase order | Load-bearing | Tier 2/3 | Not isolated | Defines action legality, deadlines, stipends, Auction, Leaderboards, Councils, and Final timing. |
| Round 2/3 stipends | Load-bearing | Tier 3/4 | **80.0%** outcomes changed without them | Preserve recovery and reachable economic paths. |
| §2 Factions and hidden membership | Load-bearing | Tier 1/2/3/4 | Open Factions changed **15.9%** | Core coalition-discovery problem; open knowledge undermines Magnate bluff and hidden-team play. |
| One outsider clue | Load-bearing | Tier 3 | Not isolated | Seeds bounded negative information without creating guaranteed-ally chains. |
| Syndicate placement: one A, one R, no Magnate | Load-bearing | Tier 1/3 | Not isolated | Bounds claims and preserves Magnates as trusted but negotiable brokers. |
| Role privacy and Syndicate mutual knowledge | Load-bearing | Tier 3 | Not isolated | Prevents setup tells, accidental friendly fire, and false-partner exploits. |
| Influence economy and physical chips | Structural | Tier 2/3 | Not removable as one axis | Transfers, costs, Goals, Bankruptcy, Auction, nominations, vote buying, and two victories depend on it. |
| Four starting Influence | Load-bearing | Tier 3 | Not isolated | Equal auditable opening capital; avoids setup information leaks and immediate proxy funding. |
| Private-phase transfer window | Load-bearing | Tier 2/3/4 | No ordinary transfers changed **81.4%** | Principal bargaining loop and dependency for Commerce, Blackmailer, and assassination preparation. |
| Agreements are non-binding | Load-bearing | Tier 3 | Not modelled | Keeps promises social rather than selectively GM-enforced. |
| Bankruptcy and debt priority | Load-bearing | **Live playtest / user-confirmed** | Only **10.1%** changed; known model blind spot | Prevents zero/negative players proxy-paying with no repercussions. |
| Motive + Ambition framework | Structural | Tier 2/3/4 | Disabling completion/payouts changed **83.4%** | Eight Goals, two Evidence templates, Espionage, and Promotion leads depend on it. |
| Goal rewards and Round 2 deadline | Load-bearing | Tier 3/4 | Included in **83.4%** | Makes private incentives material and prevents late retroactive Goal cover. |
| Individual Goals | Structural | Tier 2/3 | Not faithfully removable individually | Each supplies innocent behavioural cover; Collector, Radical, etc. depend on Auction/Interrogation/transfers. Exact Goal quality remains a live question. |
| Goal dealing caps | Load-bearing | Simulation | Not isolated | Prevents more copies than completion slots. |
| Secrets | Structural | Tier 2/3 | Not isolated | Secret Intelligence, Expose, Evidence, Untouchable, and Promotion lead depend on them. |
| Secret Intelligence | Structural | Tier 2/3 | Not isolated | Gives non-Evidence players actionable private truth and feeds Expose. |
| Expose action and its risk/reward | Load-bearing | Tier 2/3/4 | Removal changed **82.1%** | Converts Secrets into bargaining/public action; wrong-guess cost prevents brute force. |
| One successful Expose per Secret | Load-bearing | Simulation/agent probe | Repeat Expose changed **84.2%** | Prevents repeat farming and economy destruction. |
| Five Evidence / exactly two false | Load-bearing | User feedback/research/Tier 3 | Not isolated | Bounded noise makes Evidence reason-able rather than arbitrary. |
| Auction Evidence is truthful | Load-bearing | Tier 2/3 | No Auction changed **77.0%** | Provides one certified signal and supports Collector. |
| Mandatory exact Evidence disclosure | Load-bearing | Live feedback/research/Tier 4 | Removal changed **49.0%** | Creates scheduled convergence and prevents paraphrase/memory exploitation. |
| Starting Advantages for everyone | Load-bearing | Tier 3 | Not isolated | Avoids component absence becoming a hard setup tell. |
| Contracts as a system | Load-bearing | Tier 2/3/4 | Removal changed **85.1%**; Syndicate 36.4%→19.6% | Constrains target optimisation and powers Stash risk/reward. |
| Individual Contract cards | Structural | Tier 2/3 | Not isolated | The deck needs varied eligible traits; individual templates are replaceable, but removing categories changes pressure distribution. |
| Contract eligibility/timing controls | Load-bearing | Tier 3 | Not isolated | Prevent one-target Contracts, impossible Round 1 cards, and retroactive success rulings. |
| Private movement and scheduled Council convergence | Load-bearing | Research/Tier 3 | Not modelled | Enables divergent stories, then forces the table to compare them. |
| Leaderboards after Rounds 1/2 | Structural | Tier 2/3 | Not isolated | Vanity, High Society, public wealth signals, and Final forecasting depend on them. |
| Interrogation action | Load-bearing | Tier 2/3/4 | Removal changed **85.6%**; Syndicate 36.4%→57.7% | Principal collective deduction and execution mechanism. |
| Escalating Interrogation cost | Load-bearing | Tier 3 | Not isolated | Prevents rich blocs spamming low-confidence accusations. |
| Failed-vote +3 | Load-bearing | Tier 3 | Not isolated | Compensates a target for public coercion; exact amount remains tunable. |
| Guilty-vote stakes | Load-bearing, tunable | Simulation/research/Tier 4 | Removal changed **70.5%** | Makes hunting matter, but +5/-1 gives a 16.7% break-even and requires live confidence data. |
| Truth reveal after Execution | Load-bearing | Tier 2/3 | Not isolated | Makes collective commitment informative and triggers succession correctly. |
| Death split and bequest | Load-bearing | Tier 2/3/4 | No skim changed **61.5%** | Controls Stash/Bank flow and creates social inheritance. |
| Ghost economic restrictions | Load-bearing | Tier 3 | Not isolated | Prevents unkillable banking, proxy spending, and impossible purchases. |
| Ghost continued participation | Load-bearing, tunable | Research/Tier 3/4 | Lifetime limit changed **66.9%** and increased deaths/low-confidence error | Avoids hard elimination; exact vote budget remains a social question. |
| Shared private Ghost question | Load-bearing | Simulation/research/Tier 3/4 | Removal changed **48.4%** | Gives dead players information agency without public hard proof. |
| Three Candidate nominations by wealth leaders | Load-bearing | Simulation/Tier 2/3/4 | Two Candidates changed **21.9%** | Preserves economic nomination power and reduces Faction lockout. |
| Candidate eligibility and tie procedure | Load-bearing | Tier 3 | Not isolated | Prevents Ghost/debt figureheads and post-hoc GM discretion. |
| Reveal after nominations | Load-bearing | Simulation/Tier 3/4 | Reordering changed **30.4%** | Lets hard Faction information target the actual ballot. |
| One free Reveal vote | Load-bearing | Tier 3 | No Reveal changed **21.8%** | Guarantees broad access to one hard political fact. |
| Paid Reveal votes | Unknown | Tier 2/3/4 | Removal changed only **2.1%** | It connects wealth to the information market, but has no live evidence and little modelled effect. Protected pending playtest. |
| Three-candidate plurality | Load-bearing, tunable | Research/Tier 3/A-B | Runoff barely changed Faction outcomes; winner share rose 55.2%→62.7% | A defined aggregation rule is essential; plurality vs runoff is a legitimacy/time trade-off. |
| One free Final vote for every player/Ghost | Load-bearing | Tier 3 | Not isolated | Prevents wealth from controlling basic participation. |
| Paid Final votes | Load-bearing, tunable | Tier 1 Magnate intent/Tier 2/3/4 | Removal changed **19.7%** | Gives Influence endgame demand and makes Magnate vote deals real. |
| Spending before victory totals | Load-bearing | Tier 3 | Not isolated | Prevents the same Influence buying votes and scoring an economic victory. |
| Magnate combined threshold victory | Load-bearing | **Live playtest / user-confirmed** | Strong economy sensitivity | Creates intentional kingmakers courted for election and Execution votes. |
| Major-Faction Candidate victory | Load-bearing | Tier 2/3 | Not removable locally | Defines the political half of the Final. |
| Multiple simultaneous winners | Load-bearing | Tier 3 | Not modelled | Prevents unnecessary betrayal between compatible objectives. |
| Kill payment prerequisite | Load-bearing | Tier 2/3/4 | Removal changed **75.5%** | Gives assassination a physical preparation cost and a social trace. |
| Cumulative payment history | Load-bearing | Simulation/agent/Tier 4 | Same-round only changed **48.3%** | Same-round payments become a near-direct tell and can be refused for immunity. |
| Either-member payer | Load-bearing | Simulation/Tier 3/4 | Assassin-only changed **71.2%** | Preserves ambiguity while retaining a real courier trail. |
| Private qualifying-transfer record | Load-bearing operational control | Research/Tier 3 | Not modelled | Memory across rooms cannot reliably adjudicate cumulative payments. |
| Stash | Structural | Tier 2/3 | Multiple probes | Contracts, assassination income, Laundering, Promotion, and Syndicate victory depend on it. |
| Laundering | Load-bearing | Tier 2/3/4 | Removal changed **19.5%**, Syndicate 36.4%→33.3% | Gives Accomplice agency and builds inherited value. |
| Stash withdrawal cap | Load-bearing | Simulation/Tier 3/4 | One-way changed **18.3%** | Creates liquidity-vs-victory choice; cap prevents double use/cycling. |
| Stash survives Promotion | Load-bearing | User-confirmed/simulation/Tier 3 | Not isolated | Prevents execution erasing the successor's operation and making Laundering negative EV. |
| Stash split only on full wipeout | Load-bearing | Tier 2/3/4 | Removal changed **6.4%** | Prevents dead Syndicate scoring protected funds and defines physical disposal. |
| Promotion | Load-bearing | Tier 2/3/4 | Removal changed **28.0%**, Syndicate 36.4%→21.6% | Maintains the second-act hunt and shared Syndicate objective. |
| True successor lead | Load-bearing | Simulation/Tier 3/4 | Removal changed **23.4%** | Makes catching the first Assassin produce information progress. |
| Player-count setup and thresholds | Load-bearing | Simulation/Tier 3 | Not isolated | Preserves reachable, comparable outcomes across 8–15 players. |
| GM setup/tracking controls | Load-bearing operational control | Tier 3/research | Not modelled | Prevents illegal composition, false-count errors, cost drift, and hidden-accounting disputes. |

## Verdict count

- **Load-bearing:** 43 grouped elements
- **Structural:** 9 grouped elements
- **Unknown:** 1 grouped element — paid Reveal votes
- **Decorative:** **0**

## Decision

There is no evidence-supported rules cut to make before the live playtest. The correct
Level 1 intervention is **presentation**:

- separate common-player and Syndicate references;
- teach Auction and Final details just in time;
- externalise GM memory into logs;
- use the comprehension gate before Round 1.

No gameplay rule is changed by this classification.
