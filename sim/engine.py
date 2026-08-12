"""Dark Council rules engine.

Faithful implementation of dark_council_latest_en.md for economy/balance testing.

Design invariants
-----------------
1. Every Influence movement goes through Game.move(). Nothing mutates balances
   directly. This makes conservation provable.
2. The universe is {players, BANK, STASH}. BANK is the source of all injection and
   the sink of all destruction, so it goes negative. The invariant is therefore:
       sum(player balances) + BANK + STASH == 0
   at every point in the game.
3. Players decide using only their own Knowledge object. Policies never receive the
   Game, so hidden information cannot leak into decisions.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field

# --------------------------------------------------------------------------
# Constants
# --------------------------------------------------------------------------

ARISTOCRAT, REFORMER, MAGNATE = "ARISTOCRAT", "REFORMER", "MAGNATE"
INNOCENT, ASSASSIN, ACCOMPLICE = "INNOCENT", "ASSASSIN", "ACCOMPLICE"

VANITY, WRATH, ESPIONAGE, COMMERCE = "VANITY", "WRATH", "ESPIONAGE", "COMMERCE"
MOTIVES = [VANITY, WRATH, ESPIONAGE, COMMERCE]

COLLECTOR, RADICAL, BLACKMAILER, DIPLOMAT = (
    "COLLECTOR", "RADICAL", "BLACKMAILER", "DIPLOMAT")
AMBITIONS = [COLLECTOR, RADICAL, BLACKMAILER, DIPLOMAT]

SECRETS = ["BLACKMAIL", "TREASON", "CORRUPTION", "HERESY"]

ADV_EVIDENCE, ADV_INTEL = "EVIDENCE", "SECRET_INTEL"

BANK, STASH = "BANK", "STASH"

# players -> (aristocrats, reformers, magnates, magnate_threshold, assassin_threshold)
SCALING = {
    8:  (3, 3, 2, 14, 156),
    9:  (3, 3, 3, 24, 154),
    10: (4, 4, 2, 17, 152),
    11: (4, 4, 3, 28, 152),
    12: (5, 5, 2, 19, 152),
    13: (5, 5, 3, 29, 152),
    14: (6, 6, 2, 20, 152),
    15: (6, 6, 3, 29, 150),
}

HITS = [
    "HIGH_SOCIETY", "GOLDEN_GOOSE", "OLD_GUARD", "NEW_ORDER",
    "PURSE_STRINGS", "BURN_EVIDENCE", "SILENCE_ACCUSED", "UNTOUCHABLE",
]


@dataclass
class Config:
    """Every tunable number in the ruleset, so sweeps can vary one axis at a time."""
    starting_influence: int = 4
    stipend: int = 2
    hits_enabled: bool = True
    private_transfers_enabled: bool = True
    goals_enabled: bool = True
    auction_enabled: bool = True
    expose_enabled: bool = True
    interrogation_enabled: bool = True
    motive_reward: int = 5
    ambition_reward: int = 10
    expose_penalty: int = 4
    expose_reward: int = 1
    expose_fail: int = 2
    interrogation_base: int = 4
    interrogation_step: int = 1
    survivor_bonus: int = 3
    prosecutor_reward: int = 5
    hit_payout: int = 40
    hit_penalty: int = 3
    launder_cap: int = 2
    kill_share: float = 0.5
    execution_share: float = 0.5
    vote_cost: int = 3
    reveal_vote_cost: int = 1
    election_mode: str = "plurality"  # plurality | runoff
    vote_purchase_mode: str = "flat"  # flat | escalating | capped
    vote_purchase_cap: int = 2
    reveal_enabled: bool = True
    rounds: int = 3
    ghost_question: bool = True
    ghost_mode: str = "public"  # public | once | private | off
    ghost_vote_mode: str = "all"  # all | lifetime
    evidence_disclosure_enabled: bool = True
    expose_once: bool = False
    kill_tell_scope: str = "round"  # round (as written) | game (cumulative)
    # --- goal rules ---
    goals_v2: bool = False        # rewritten Espionage + Blackmailer
    cap_goals: bool = False       # deal capped goals no more often than there are slots
    extortion_amount: int = 3
    espionage_targets: int = 2
    espionage_full_profile: bool = False
    commerce_partners: int = 2
    commerce_profit: int = 3
    commerce_min_paid: int = 1
    motive_deadline: int = 1      # last round in which a Motive may be claimed
    ambition_deadline: int = 2
    private_phase_minutes: tuple[int, int, int] = (30, 30, 30)
    # --- F7: make catching the Assassin matter ---
    bounty_mode: str = "none"     # none | all_living | prosecutor_faction
    bounty_amount: int = 3
    bounty_source: str = "bank"   # bank (injects) | stash (confiscates the hoard)
    stash_confiscation: float = 1.0
    # The Stash is inherited wealth: it survives execution and only falls to the room
    # when the whole Syndicate is dead.
    confiscate_on_wipeout: bool = True
    # Personal stakes on the Interrogation vote.
    guilty_vote_reward: int = 0   # paid if the executed player really was the Assassin
    guilty_vote_penalty: int = 0  # charged if they were not
    # On Promotion the GM announces one true statement about the survivor.
    promotion_reveals_evidence: bool = False
    promotion_enabled: bool = True
    promotion_threshold_bump: int = 0
    # Final sequencing: nominate first so the Reveal can target someone on the ballot.
    reveal_after_nomination: bool = False
    candidates_declare: bool = False
    candidate_count: int = 2      # nominators, and therefore Candidates
    ally_hint: str = "none"       # none | all | large | open
    tell_by_either: bool = False  # the Accomplice may pay the kill tell
    kill_tell_required: bool = True
    stash_withdraw_cap: int = 0   # 0 = one-way vault; >0 = two-way war chest
    ghosts_keep_faction_victory: bool = True
    bankruptcy_enabled: bool = True
    expose_eligibility_enabled: bool = True
    interrogation_vote_eligibility_enabled: bool = True
    bankruptcy_lock_at_final: bool = True
    debt_rescue_enabled: bool = True
    assassin_survival_tax: int = 0
    magnate_threshold: int | None = None
    assassin_threshold: int | None = None
    # behavioural band: scales goal-claim and trade propensity
    behaviour_band: str = "expected"  # pessimistic | expected | optimistic
    talkativeness: float = 1.0    # scales how much information is traded privately


@dataclass
class Knowledge:
    """A single player's isolated view. Policies read only this."""
    seat: int
    faction: str
    role: str
    motive: str
    ambition: str
    secret: str
    known_outsider: int
    evidence: list[str] = field(default_factory=list)
    known_secrets: dict[int, str] = field(default_factory=dict)
    suspicion: dict[int, float] = field(default_factory=dict)
    partner: int | None = None          # syndicate only
    traded_with: set[int] = field(default_factory=set)
    confirmed_clear: set[int] = field(default_factory=set)
    confirmed_syndicate: set[int] = field(default_factory=set)
    publicly_exposed: set[int] = field(default_factory=set)
    confirmed_evidence: set[str] = field(default_factory=set)
    # Faction beliefs. Learned, never granted: Public Pacts and the Reveal are
    # truthful; conversational claims may be lies.
    known_faction: dict[int, str] = field(default_factory=dict)
    verified_faction: set[int] = field(default_factory=set)
    not_my_faction: set[int] = field(default_factory=set)
    # learned by talking, never granted at setup
    known_motive: dict[int, str] = field(default_factory=dict)
    known_ambition: dict[int, str] = field(default_factory=dict)
    heard_evidence: list[str] = field(default_factory=list)
    spoke_with: set[int] = field(default_factory=set)
    # --- social layer -------------------------------------------------
    # Directed and personal: how *I* feel about each other player.
    trust: dict[int, float] = field(default_factory=dict)
    received_total: dict[int, int] = field(default_factory=dict)
    given_total: dict[int, int] = field(default_factory=dict)
    accused_me: set[int] = field(default_factory=set)
    voted_against_me: dict[int, int] = field(default_factory=dict)
    caught_lying: set[int] = field(default_factory=set)
    times_accused: int = 0

    def feel(self, seat: int, delta: float) -> None:
        if seat == self.seat:
            return
        self.trust[seat] = max(-3.0, min(3.0, self.trust.get(seat, 0.0) + delta))

    def regard(self, seat: int) -> float:
        return self.trust.get(seat, 0.0)

    def allies(self, living: list[int], bar: float = 0.8) -> list[int]:
        return [s for s in living if s != self.seat and self.regard(s) >= bar]

    def suspect(self, seat: int, amount: float) -> None:
        if seat == self.seat or seat in self.confirmed_clear:
            return
        # Goodwill buys the benefit of the doubt. This is what makes the
        # Assassin's mandatory payment genuinely protective.
        damped = amount / (1.0 + max(0.0, self.regard(seat)))
        self.suspicion[seat] = self.suspicion.get(seat, 0.0) + damped


@dataclass
class Player:
    seat: int
    faction: str
    role: str
    archetype: str
    motive: str
    ambition: str
    secret: str
    advantage: str
    influence: int = 0
    alive: bool = True
    motive_done: bool = False
    ambition_done: bool = False
    interrogated: bool = False
    secret_exposed: bool = False
    holds_evidence: bool = False
    initiated_interrogation: bool = False
    won_auction: bool = False
    successful_exposes: int = 0
    extortion_done: bool = False
    guilty_votes_on_executed: int = 0
    was_on_leaderboard: bool = False
    reputation: float = 0.0          # public standing: correct accusations build it
    failed_accusations: int = 0
    bankrupt_locked: bool = False
    vote_exclusions: int = 0
    expose_refusals: int = 0
    debt_rescued: int = 0
    knowledge: Knowledge = None  # type: ignore

    @property
    def persona(self) -> str:
        return self.archetype

    @property
    def bankrupt(self) -> bool:
        return self.bankrupt_locked


@dataclass
class GameResult:
    game_id: str
    n_players: int
    seed: int
    aristocrat_win: bool
    reformer_win: bool
    magnate_win: bool
    syndicate_win: bool
    magnate_total: int
    magnate_threshold: int
    assassin_total: int
    assassin_threshold: int
    assassin_alive: bool
    stash: int
    bank: int
    circulating: int
    deaths: int
    executions: int
    assassinations: int
    interrogations: int
    correct_executions: int
    bankruptcies: int
    hits_met: int
    motives_claimed: int
    ambitions_claimed: int
    winning_faction: str | None
    personal_wins: dict[int, bool]
    ledger: list[tuple]
    events: list[tuple]
    snapshots: list[tuple]
    players: list[Player]
    eligible_vote_opportunities: int = 0
    vote_exclusions: int = 0
    repeat_vote_exclusions: int = 0
    expose_attempts: int = 0
    expose_refusals: int = 0
    gm_refusals: int = 0
    debt_rescue_transfers: int = 0
    debt_rescued: int = 0
    debt_by_cause: dict[str, int] | None = None
    executions_by_round: dict[int, int] | None = None
    correct_executions_by_round: dict[int, int] | None = None
    deaths_by_round: dict[int, int] | None = None
    motive_completion_by_goal: dict[str, int] | None = None
    ambition_completion_by_goal: dict[str, int] | None = None
    zero_agency_players: int = 0
    wealth_top_share: float = 0.0

    def innocent_win_rate(self) -> float:
        """Share of non-Syndicate players who personally won."""
        vals = [w for s, w in self.personal_wins.items()
                if self.players[s].role not in (ASSASSIN, ACCOMPLICE)]
        return sum(vals) / len(vals) if vals else 0.0


class Game:
    def __init__(self, n_players: int, seed: int, config: Config | None = None,
                 policy_module=None, game_id: str | None = None):
        if n_players not in SCALING:
            raise ValueError(f"unsupported player count: {n_players}")
        self.n = n_players
        self.seed = seed
        self.rng = random.Random(seed)
        self.cfg = config or Config()
        self.game_id = game_id or f"g{n_players}_{seed}"

        a, r, m, mag_thr, asn_thr = SCALING[n_players]
        self.magnate_threshold = self.cfg.magnate_threshold or mag_thr
        self.assassin_threshold = self.cfg.assassin_threshold or asn_thr

        from . import policies as default_policies
        self.pol = policy_module or default_policies
        if hasattr(self.pol, "seed_policies"):
            self.pol.seed_policies(seed)

        self.bank = 0
        self.stash = 0
        self.round = 0
        self.phase = "SETUP"
        self.ledger: list[tuple] = []
        self.events: list[tuple] = []
        self.snapshots: list[tuple] = []

        self.interrogation_cost = self.cfg.interrogation_base
        self.interrogation_count = 0
        self.executions_by_round: dict[int, int] = {}
        self.correct_executions_by_round: dict[int, int] = {}
        self.deaths_by_round: dict[int, int] = {}
        self.used_hits: list[str] = []
        self.hit: str | None = None
        self.hits_met = 0
        self.promoted = False
        self.assassinations = 0
        self.executions = 0
        self.correct_executions = 0
        self.transfers_this_round: dict[int, set[int]] = {}
        self.cumulative_transfers: dict[int, set[int]] = {}
        self.received_this_phase: dict[int, dict[int, int]] = {}
        self.received_total: dict[int, dict[int, int]] = {}
        self.auction_evidence: str | None = None
        self.ghost_vote_spent: set[int] = set()
        self.eligible_vote_opportunities = 0
        self.vote_exclusions = 0
        self.expose_attempts = 0
        self.expose_refusals = 0
        self.gm_refusals = 0
        self.debt_rescue_transfers = 0
        self.debt_rescued = 0
        self.debt_by_cause: dict[str, int] = {}
        self.excluded_rounds: dict[int, set[int]] = {}

        self.players = self._setup(a, r, m)

    # ------------------------------------------------------------------
    # Accounting
    # ------------------------------------------------------------------

    def _balance(self, holder) -> int:
        if holder == BANK:
            return self.bank
        if holder == STASH:
            return self.stash
        return self.players[holder].influence

    def move(self, src, dst, amount: int, reason: str) -> int:
        """The only mutation path for Influence. Returns amount actually moved."""
        if amount <= 0:
            return 0
        # Ghosts cannot receive: income is voided to the Bank.
        if isinstance(dst, int) and not self.players[dst].alive:
            self.events.append((self.game_id, self.round, "GHOST_INCOME_VOID", dst, amount, reason))
            dst = BANK
        before = self.players[src].influence if isinstance(src, int) else None
        if isinstance(src, int):
            self.players[src].influence -= amount
        elif src == BANK:
            self.bank -= amount
        elif src == STASH:
            self.stash -= amount
        if isinstance(dst, int):
            self.players[dst].influence += amount
        elif dst == BANK:
            self.bank += amount
        elif dst == STASH:
            self.stash += amount
        self.ledger.append(
            (self.game_id, self.round, self.phase, str(src), str(dst), amount, reason))
        if isinstance(src, int) and before is not None:
            after = self.players[src].influence
            newly_created = max(0, -after) - max(0, -before)
            if newly_created > 0:
                self.debt_by_cause[reason] = self.debt_by_cause.get(reason, 0) + newly_created
        return amount

    def check_conservation(self) -> None:
        total = sum(p.influence for p in self.players) + self.bank + self.stash
        if total != 0:
            raise AssertionError(
                f"conservation broken in {self.game_id}: {total} != 0")

    # ------------------------------------------------------------------
    # Setup
    # ------------------------------------------------------------------

    def _setup(self, a: int, r: int, m: int) -> list[Player]:
        factions = [ARISTOCRAT] * a + [REFORMER] * r + [MAGNATE] * m
        self.rng.shuffle(factions)

        archetypes = list(self.pol.PERSONAS) if hasattr(self.pol, "PERSONAS") else [
            "HOARDER", "AGGRESSOR", "TRADER", "SCHEMER", "FOLLOWER"]
        motives = self._deal_goals(MOTIVES, {VANITY: 3})
        ambitions = self._deal_goals(AMBITIONS, {COLLECTOR: 1})
        players: list[Player] = []
        for seat, fac in enumerate(factions):
            players.append(Player(
                seat=seat,
                faction=fac,
                role=INNOCENT,
                archetype=archetypes[seat % len(archetypes)],
                motive=motives[seat],
                ambition=ambitions[seat],
                secret=self.rng.choice(SECRETS),
                advantage=ADV_INTEL,
            ))
        self.players = players

        # Syndicate: always exactly one Aristocrat and one Reformer.
        aris = [p.seat for p in players if p.faction == ARISTOCRAT]
        refs = [p.seat for p in players if p.faction == REFORMER]
        s1 = self.rng.choice(aris)
        s2 = self.rng.choice(refs)
        pair = [s1, s2]
        self.rng.shuffle(pair)
        self.assassin_seat, self.accomplice_seat = pair[0], pair[1]
        self.original_assassin = self.assassin_seat
        players[self.assassin_seat].role = ASSASSIN
        players[self.accomplice_seat].role = ACCOMPLICE

        # Starting Advantages must be fixed before Evidence is written, because one
        # Evidence template describes a Syndicate member's Advantage.
        holders = self.rng.sample(range(self.n), 4)
        for seat in holders:
            players[seat].advantage = ADV_EVIDENCE
            players[seat].holds_evidence = True

        evidence_pool = self._build_evidence()
        self.dealt_evidence = evidence_pool[:4]
        self.auction_evidence = evidence_pool[4]

        for p in players:
            outsiders = [q.seat for q in players if q.faction != p.faction]
            k = Knowledge(
                seat=p.seat, faction=p.faction, role=p.role, motive=p.motive,
                ambition=p.ambition, secret=p.secret,
                known_outsider=self.rng.choice(outsiders),
            )
            k.not_my_faction.add(k.known_outsider)
            p.knowledge = k

        self._grant_ally_hints(players)

        for seat, text in zip(holders, evidence_pool[:4]):
            players[seat].knowledge.evidence.append(text)

        for p in players:
            if p.advantage == ADV_INTEL:
                others = [q.seat for q in players if q.seat != p.seat]
                target = self.rng.choice(others)
                p.knowledge.known_secrets[target] = players[target].secret

        players[self.assassin_seat].knowledge.partner = self.accomplice_seat
        players[self.accomplice_seat].knowledge.partner = self.assassin_seat

        self.phase = "SETUP"
        for p in players:
            self.move(BANK, p.seat, self.cfg.starting_influence, "starting_influence")
        return players

    def _grant_ally_hints(self, players: list[Player]) -> None:
        """Optional setup knowledge about who shares your Faction."""
        mode = self.cfg.ally_hint
        if mode == "none":
            return
        for p in players:
            if mode == "large" and p.faction == MAGNATE:
                continue
            allies = [q.seat for q in players
                      if q.faction == p.faction and q.seat != p.seat]
            if not allies:
                continue
            targets = allies if mode == "open" else [self.rng.choice(allies)]
            for seat in targets:
                p.knowledge.known_faction[seat] = p.faction
                p.knowledge.verified_faction.add(seat)

    def _deal_goals(self, pool: list[str], caps: dict[str, int]) -> list[str]:
        """Deal one goal per seat. A capped goal is never dealt more often than
        there are ways to achieve it (only one Auction, only three Leaderboard slots)."""
        counts = {g: 0 for g in pool}
        out = []
        for _ in range(self.n):
            if self.cfg.cap_goals:
                avail = [g for g in pool if counts[g] < caps.get(g, self.n)]
            else:
                avail = list(pool)
            g = self.rng.choice(avail or list(pool))
            counts[g] += 1
            out.append(g)
        self.rng.shuffle(out)
        return out

    def _build_evidence(self) -> list[str]:
        """Five statements about the Syndicate; exactly two of the four dealt are false.

        A template is only falsifiable when a value exists that is untrue for *both*
        Syndicate members. Advantage can be unfalsifiable when the pair holds one of
        each type, so that template is preferentially routed to the Auction, which
        must be truthful anyway (rules SS12.3).
        """
        a = self.players[self.assassin_seat]
        c = self.players[self.accomplice_seat]

        def falsify(options, actual):
            pool = [o for o in options if o not in actual]
            return self.rng.choice(pool) if pool else None

        truths = [
            f"MOTIVE:{self.rng.choice([a.motive, c.motive])}",
            f"AMBITION:{self.rng.choice([a.ambition, c.ambition])}",
            f"SECRET:{self.rng.choice([a.secret, c.secret])}",
            f"ASSASSIN_FACTION:{a.faction}",
            f"ADVANTAGE:{self.rng.choice([a.advantage, c.advantage])}",
        ]
        prefixes = ["MOTIVE", "AMBITION", "SECRET", "ASSASSIN_FACTION", "ADVANTAGE"]
        lie_values = [
            falsify(MOTIVES, {a.motive, c.motive}),
            falsify(AMBITIONS, {a.ambition, c.ambition}),
            falsify(SECRETS, {a.secret, c.secret}),
            REFORMER if a.faction == ARISTOCRAT else ARISTOCRAT,
            falsify([ADV_EVIDENCE, ADV_INTEL], {a.advantage, c.advantage}),
        ]
        lies = [f"{p}:{v}" if v is not None else None
                for p, v in zip(prefixes, lie_values)]

        unfalsifiable = [i for i in range(5) if lies[i] is None]
        auction_idx = (self.rng.choice(unfalsifiable) if unfalsifiable
                       else self.rng.randrange(5))
        remaining = [i for i in range(5) if i != auction_idx]
        falsifiable = [i for i in remaining if lies[i] is not None]
        self.rng.shuffle(falsifiable)
        false_idx = set(falsifiable[:2])

        dealt = [lies[i] if i in false_idx else truths[i] for i in remaining]
        self.rng.shuffle(dealt)
        self.false_count = len(false_idx)
        return dealt + [truths[auction_idx]]

    def evidence_is_true(self, statement: str) -> bool:
        a = self.players[self.original_assassin]
        c = self.players[self.accomplice_seat]
        kind, _, value = statement.partition(":")
        if kind == "MOTIVE":
            return value in {a.motive, c.motive}
        if kind == "AMBITION":
            return value in {a.ambition, c.ambition}
        if kind == "SECRET":
            return value in {a.secret, c.secret}
        if kind == "ASSASSIN_FACTION":
            return value == a.faction
        if kind == "ADVANTAGE":
            return value in {a.advantage, c.advantage}
        return False

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def living(self) -> list[Player]:
        return [p for p in self.players if p.alive]

    def public_view(self) -> dict:
        return {
            "living": [p.seat for p in self.living()],
            "round": self.round,
            "interrogation_cost": self.interrogation_cost,
            "hit": self.hit,
            "leaderboard": self.leaderboard(),
            "n_players": self.n,
            "influence": {p.seat: p.influence for p in self.players if p.alive},
        }

    def leaderboard(self) -> list[int]:
        ranked = sorted(self.living(), key=lambda p: -p.influence)
        return [p.seat for p in ranked[:3]]

    def is_bankrupt(self, player: Player) -> bool:
        if not self.cfg.bankruptcy_enabled:
            return False
        return (player.bankrupt_locked if self.cfg.bankruptcy_lock_at_final
                else player.influence < 0)

    def broadcast(self, fn) -> None:
        for p in self.players:
            fn(p.knowledge)

    # ------------------------------------------------------------------
    # Round phases
    # ------------------------------------------------------------------

    def run(self) -> GameResult:
        for rnd in range(1, self.cfg.rounds + 1):
            self.round = rnd
            if rnd > 1:
                self.phase = "STIPEND"
                for p in self.living():
                    self.move(BANK, p.seat, self.cfg.stipend, "stipend")
            if self.cfg.hits_enabled:
                self.select_hit()
            else:
                self.hit = None
            if rnd == 2 and self.cfg.auction_enabled:
                self.auction()
            self.private_phase()
            self.council()
            self.snapshot()
            self.check_conservation()
        self.final()
        self.check_conservation()
        return self.result()

    def select_hit(self) -> None:
        self.phase = "HIT"
        available = [c for c in HITS if c not in self.used_hits]
        valid = [c for c in available
                 if sum(1 for p in self.living()
                        if p.seat != self.assassin_seat
                        and p.seat != self.accomplice_seat
                        and self.hit_matches(c, p)) >= 2]
        self.hit = self.rng.choice(valid) if valid else self.rng.choice(available)
        self.used_hits.append(self.hit)
        options = [
            p.seat for p in self.living()
            if p.seat != self.assassin_seat
            and p.seat != self.accomplice_seat
            and self.hit_matches(self.hit, p)
        ]
        self.events.append((
            self.game_id, self.round, "HIT", self.hit, len(options),
            ",".join(map(str, options)),
        ))

    def hit_matches(self, hit: str, victim: Player) -> bool:
        if hit == "HIGH_SOCIETY":
            return victim.seat in self.leaderboard()
        if hit == "GOLDEN_GOOSE":
            return victim.influence >= 10
        if hit == "OLD_GUARD":
            return victim.faction == ARISTOCRAT
        if hit == "NEW_ORDER":
            return victim.faction == REFORMER
        if hit == "PURSE_STRINGS":
            return victim.faction == MAGNATE
        if hit == "BURN_EVIDENCE":
            return victim.holds_evidence
        if hit == "SILENCE_ACCUSED":
            return victim.interrogated
        if hit == "UNTOUCHABLE":
            return not victim.interrogated and not victim.secret_exposed
        return False

    def auction(self) -> None:
        self.phase = "AUCTION"
        bids = {}
        for p in self.living():
            bid = self.pol.auction_bid(p.knowledge, p.archetype, p.influence,
                                       self.public_view(), self.cfg)
            if bid >= 1:
                bids[p.seat] = bid
        if not bids:
            return
        top = max(bids.values())
        winners = [s for s, b in bids.items() if b == top]
        winner = self.rng.choice(winners)
        self.move(winner, BANK, top, "auction_bid")
        w = self.players[winner]
        w.won_auction = True
        w.holds_evidence = True
        w.knowledge.evidence.append(self.auction_evidence)
        self.events.append((self.game_id, self.round, "AUCTION", winner, top, self.auction_evidence))

    def private_phase(self) -> None:
        self.phase = "PRIVATE"
        self.transfers_this_round = {}
        self.received_this_phase = {}

        self.information_exchange()

        if self.cfg.private_transfers_enabled:
            for p in self.living():
                if p.role == ASSASSIN:
                    continue
                targets = [q.seat for q in self.living() if q.seat != p.seat]
                for dst, amt in self.pol.transfers(
                        p.knowledge, p.archetype, p.influence,
                        targets, self.public_view(), self.cfg):
                    if amt <= 0 or p.influence < amt:
                        continue
                    self._pay(p.seat, dst, amt, "gift")

            self.extortion_phase()
            if self.cfg.debt_rescue_enabled:
                self.debt_rescue_phase()

        # Assassin acts last so camouflage can reflect the round state.
        assassin = self.players[self.assassin_seat]
        self.pending_kill = None
        if assassin.alive:
            candidates = [q for q in self.living()
                          if q.seat not in (self.assassin_seat, self.accomplice_seat)]
            if candidates:
                target, spray = self.pol.assassin_plan(
                    assassin.knowledge, assassin.influence,
                    [(q.seat, q.influence, self.hit_matches(self.hit, q),
                      self.threat_level(q))
                     for q in candidates],
                    self.public_view(), self.cfg)
                for dst in spray:
                    if assassin.influence >= 1:
                        self._pay(self.assassin_seat, dst, 1, "camouflage")
                if target is not None:
                    payer = self.assassin_seat
                    acc = self.players[self.accomplice_seat]
                    # The courier may deliver the bribe, so the trail leads to them.
                    if (self.cfg.tell_by_either and acc.alive
                            and acc.seat != self.assassin_seat
                            and acc.influence >= 1 and self.rng.random() < 0.5):
                        payer = acc.seat
                    already_paid = (self.cfg.kill_tell_scope == "game"
                                    and (self.assassin_seat in
                                         self.cumulative_transfers.get(target, set())
                                         or (self.cfg.tell_by_either and acc.seat in
                                             self.cumulative_transfers.get(target, set()))))
                    if not self.cfg.kill_tell_required:
                        self.pending_kill = target
                    elif already_paid:
                        self.pending_kill = target
                    elif self.players[payer].influence >= 1:
                        self._pay(payer, target, 1, "kill_tell")
                        self.pending_kill = target

        acc = self.players[self.accomplice_seat]
        if acc.alive and acc.role == ACCOMPLICE:
            amt = self.pol.launder(acc.knowledge, acc.influence, self.cfg)
            amt = max(0, min(amt, self.cfg.launder_cap, max(0, acc.influence)))
            if amt:
                self.move(acc.seat, STASH, amt, "launder")

        # The Stash as a two-way war chest: victory progress can be converted into
        # live spending power, and Laundering converts it back.
        if self.cfg.stash_withdraw_cap > 0:
            boss = self.players[self.assassin_seat]
            if boss.alive and self.stash > 0:
                want = self.pol.withdraw_stash(boss.knowledge, boss.influence,
                                               self.stash, self.cfg)
                want = max(0, min(want, self.cfg.stash_withdraw_cap, self.stash))
                if want:
                    self.move(STASH, boss.seat, want, "stash_withdrawal")

        if self.cfg.goals_v2:
            need = self.cfg.extortion_amount
            for p in self.living():
                rec = self.received_total.get(p.seat, {})
                if sum(1 for v in rec.values() if v >= need) >= 2:
                    p.extortion_done = True

    def _pay(self, src: int, dst: int, amount: int, reason: str) -> int:
        debt_before = max(0, -self.players[dst].influence)
        moved = self.move(src, dst, amount, reason)
        if moved:
            self._record_transfer(src, dst)
            bucket = self.received_this_phase.setdefault(dst, {})
            bucket[src] = bucket.get(src, 0) + moved
            total = self.received_total.setdefault(dst, {})
            total[src] = total.get(src, 0) + moved
            # Reciprocity: money buys goodwill, and goodwill damps suspicion.
            # This is why the Assassin's mandatory tell is protective rather than
            # merely incriminating.
            if isinstance(src, int) and isinstance(dst, int):
                giver, taker = self.players[src].knowledge, self.players[dst].knowledge
                taker.received_total[src] = taker.received_total.get(src, 0) + moved
                giver.given_total[dst] = giver.given_total.get(dst, 0) + moved
                taker.feel(src, min(0.9, 0.30 * moved))
                giver.feel(dst, 0.05 * moved)
            if reason == "debt_rescue":
                cleared = min(debt_before, moved)
                self.debt_rescue_transfers += 1
                self.debt_rescued += cleared
                self.players[dst].debt_rescued += cleared
        return moved

    def debt_rescue_phase(self) -> None:
        debtors = [(p.seat, -p.influence) for p in self.living() if p.influence < 0]
        if not debtors:
            return
        for p in self.living():
            if p.influence <= 0:
                continue
            available = [(seat, debt) for seat, debt in debtors
                         if seat != p.seat and self.players[seat].influence < 0]
            if not available:
                break
            chooser = getattr(self.pol, "debt_rescues", None)
            if chooser is None:
                continue
            for dst, amount in chooser(
                    p.knowledge, p.archetype, p.influence,
                    available, self.public_view(), self.cfg):
                debt = max(0, -self.players[dst].influence)
                amount = min(max(0, amount), max(0, p.influence), debt)
                if amount:
                    self._pay(p.seat, dst, amount, "debt_rescue")

    # ---------------- information trading ----------------

    def information_exchange(self) -> None:
        """Private conversations. This is what a 30-minute phase in a house is made of."""
        living = self.living()
        if len(living) < 2:
            return
        for p in living:
            others = [q for q in living if q.seat != p.seat]
            n = self.pol.conversation_count(p.knowledge, p.archetype, self.cfg)
            minutes = self.cfg.private_phase_minutes[
                min(self.round - 1, len(self.cfg.private_phase_minutes) - 1)
            ]
            n *= minutes / 30
            n = max(0, min(int(n), len(others)))
            for q in self.rng.sample(others, n):
                p.knowledge.spoke_with.add(q.seat)
                q.knowledge.spoke_with.add(p.seat)
                self._tell(p, q)
                self._tell(q, p)

    def _tell(self, src: Player, dst: Player) -> None:
        k, o = src.knowledge, dst.knowledge
        lying = src.role in (ASSASSIN, ACCOMPLICE)
        persona = src.archetype

        # Faction claims. Unverifiable, so they are the natural place to lie -- and
        # everyone wants to claim Magnate, because Magnates are publicly cleared.
        if self.pol.claims_faction(k, o.seat, self.cfg, persona):
            claim = src.faction
            if self.pol.lies_about_faction(k, self.cfg, persona):
                claim = self.rng.choice([f for f in (ARISTOCRAT, REFORMER, MAGNATE)
                                         if f != src.faction])
            if src.seat not in o.verified_faction:
                o.known_faction[src.seat] = claim
                # Being caught contradicting a verified fact costs trust.
                if src.seat in o.verified_faction and claim != src.faction:
                    o.caught_lying.add(src.seat)
                    o.feel(src.seat, -1.0)

        if self.pol.shares_own_goal(k, o.seat, self.cfg, persona):
            deceive = lying and self.rng.random() < 0.6
            if self.rng.random() < 0.5:
                o.known_motive[src.seat] = (self.rng.choice(MOTIVES) if deceive
                                            else src.motive)
            else:
                o.known_ambition[src.seat] = (self.rng.choice(AMBITIONS) if deceive
                                              else src.ambition)

        if k.known_secrets and self.pol.shares_secret(k, o.seat, self.cfg, persona):
            seat = self.rng.choice(list(k.known_secrets))
            if seat != o.seat:
                o.known_secrets[seat] = (self.rng.choice(SECRETS)
                                         if lying and self.rng.random() < 0.5
                                         else k.known_secrets[seat])

        pool = k.evidence + k.heard_evidence
        if pool and self.pol.shares_evidence(k, o.seat, self.cfg, persona):
            stmt = self.rng.choice(pool)
            if lying and self.rng.random() < 0.7:
                stmt = f"{self.rng.choice(['MOTIVE', 'AMBITION', 'SECRET'])}:" \
                       f"{self.rng.choice(MOTIVES + AMBITIONS + SECRETS)}"
            o.heard_evidence.append(stmt)
            self._apply_evidence(dst, stmt)

        tip = self.pol.shares_suspicion(k, o.seat, self.cfg, persona)
        if tip is not None and tip != o.seat:
            o.suspect(tip, 0.25)
        # Talking builds rapport regardless of what was said.
        o.feel(src.seat, 0.12)

    def _apply_evidence(self, listener: Player, statement: str) -> None:
        """Evidence only bites when the listener knows the trait it describes."""
        kind, _, value = statement.partition(":")
        k = listener.knowledge
        for q in self.players:
            if q.seat == listener.seat or not q.alive:
                continue
            if kind == "MOTIVE":
                if k.known_motive.get(q.seat) == value:
                    k.suspect(q.seat, 0.50)
                elif q.initiated_interrogation and value == WRATH:
                    k.suspect(q.seat, 0.25)
            elif kind == "AMBITION":
                if k.known_ambition.get(q.seat) == value:
                    k.suspect(q.seat, 0.50)
                elif q.won_auction and value == COLLECTOR:
                    k.suspect(q.seat, 0.25)
                elif q.successful_exposes >= 2 and value == BLACKMAILER:
                    k.suspect(q.seat, 0.25)
            elif kind == "SECRET":
                if k.known_secrets.get(q.seat) == value:
                    k.suspect(q.seat, 0.50)

    # ---------------- extortion (rewritten Blackmailer) ----------------

    def extortion_phase(self) -> None:
        if not self.cfg.goals_v2:
            return
        amt = self.cfg.extortion_amount
        for p in self.living():
            if p.ambition != BLACKMAILER or p.extortion_done:
                continue
            others = [q.seat for q in self.living() if q.seat != p.seat]
            for t in self.pol.extortion_targets(p.knowledge, others, self.cfg):
                q = self.players[t]
                if q.influence >= amt and self.pol.pays_tribute(
                        q.knowledge, q.archetype, q.influence, p.seat, self.cfg):
                    self._pay(t, p.seat, amt, "tribute")

    def _record_transfer(self, src: int, dst: int) -> None:
        self.transfers_this_round.setdefault(dst, set()).add(src)
        self.cumulative_transfers.setdefault(dst, set()).add(src)
        self.players[src].knowledge.traded_with.add(dst)
        self.players[dst].knowledge.traded_with.add(src)

    def donor_set(self, seat: int) -> list[int]:
        """Who the victim's Ghost can name as having paid them."""
        if self.cfg.kill_tell_scope == "game":
            return sorted(self.cumulative_transfers.get(seat, set()))
        return sorted(self.transfers_this_round.get(seat, set()))

    # ------------------------------------------------------------------
    # Council
    # ------------------------------------------------------------------

    def threat_level(self, p: Player) -> float:
        """How dangerous a player is to the Syndicate: credibility plus aggression."""
        return (max(0.0, p.reputation) * 0.5
                + p.initiated_interrogation * 1.0
                + p.holds_evidence * 0.6
                + (1.0 if p.seat in self.leaderboard() else 0.0))

    def social_pressure(self) -> None:
        """The room reads the room.

        Real tables suspect both the loudest voice and the person who has said
        nothing. Sitting quietly is not the safe strategy it is in a pure model.
        """
        living = self.living()
        if len(living) < 3:
            return
        talk = {p.seat: len(p.knowledge.spoke_with) for p in living}
        avg = sum(talk.values()) / len(talk)
        for p in living:
            quiet = avg - talk[p.seat]
            for q in living:
                if q.seat == p.seat:
                    continue
                if quiet > 1.5:
                    # "We have not heard a word from you all evening."
                    q.knowledge.suspect(p.seat, 0.10 * min(3.0, quiet))
                if p.failed_accusations:
                    q.knowledge.suspect(p.seat, 0.12 * p.failed_accusations)

    def council(self) -> None:
        self.phase = "COUNCIL"
        self.resolve_assassination()
        self.social_pressure()
        self.ghost_question()
        if self.cfg.expose_enabled:
            self.resolve_exposes()
        if self.cfg.interrogation_enabled:
            self.resolve_interrogations()
        if self.cfg.goals_enabled:
            self.claim_goals()

    def resolve_assassination(self) -> None:
        target = getattr(self, "pending_kill", None)
        met = False
        if target is not None and self.players[target].alive:
            victim = self.players[target]
            met = self.hit_matches(self.hit, victim)
            donors = self.donor_set(target)
            self.kill(victim, to=STASH, share=self.cfg.kill_share, cause="ASSASSINATED")
            self.assassinations += 1
            # The victim becomes a Ghost and can name everyone who paid them.
            self.broadcast(lambda k, d=donors: [k.suspect(s, 1.0 / max(1, len(d)))
                                                for s in d if s != k.seat])
            self.events.append((self.game_id, self.round, "ASSASSINATION", target,
                                len(donors), self.hit))
        if not self.cfg.hits_enabled:
            return
        if met:
            self.hits_met += 1
            self.move(BANK, STASH, self.cfg.hit_payout, "hit_success")
        else:
            penalty = self.cfg.hit_penalty
            from_stash = min(self.stash, penalty)
            if from_stash:
                self.move(STASH, BANK, from_stash, "hit_failure")
            shortfall = penalty - from_stash
            a = self.players[self.assassin_seat]
            if shortfall and a.alive:
                self.move(a.seat, BANK, shortfall, "hit_failure_personal")

    def kill(self, victim: Player, to, share: float, cause: str) -> None:
        amount = victim.influence
        if amount > 0:
            skim = int(amount * share)
            self.move(victim.seat, to, skim, f"{cause.lower()}_skim")
            heirs = [q.seat for q in self.living() if q.seat != victim.seat]
            if heirs:
                heir = self.pol.choose_heir(victim.knowledge, heirs)
                self.move(victim.seat, heir, victim.influence, f"{cause.lower()}_bequest")
        victim.alive = False
        self.deaths_by_round[self.round] = self.deaths_by_round.get(self.round, 0) + 1
        self.events.append((self.game_id, self.round, cause, victim.seat, amount, victim.faction))

    def ghost_question(self) -> None:
        mode = self.cfg.ghost_mode
        if not self.cfg.ghost_question or mode == "off":
            return
        if mode == "once" and getattr(self, "ghost_asked", False):
            return
        ghosts = [p for p in self.players if not p.alive]
        if not ghosts:
            return
        pooled: dict[int, float] = {}
        for g in ghosts:
            for seat, val in g.knowledge.suspicion.items():
                if self.players[seat].alive:
                    pooled[seat] = pooled.get(seat, 0.0) + val
        if not pooled:
            return
        asked = max(pooled, key=pooled.get)
        answer = self.players[asked].role in (ASSASSIN, ACCOMPLICE)
        self.ghost_asked = True
        # "private" keeps the answer with the Ghosts, who must then persuade the living.
        audience = ghosts if mode == "private" else self.players
        for p in audience:
            if answer:
                p.knowledge.confirmed_syndicate.add(asked)
            else:
                p.knowledge.confirmed_clear.add(asked)
                p.knowledge.suspicion.pop(asked, None)
        self.events.append((self.game_id, self.round, "GHOST_QUESTION", asked, int(answer), mode))

    def resolve_exposes(self) -> None:
        for p in list(self.living()):
            if not p.alive:
                continue
            guess = self.pol.expose(p.knowledge, p.archetype, p.influence,
                                    self.public_view(), self.cfg)
            if not guess:
                continue
            self.expose_attempts += 1
            if self.cfg.expose_eligibility_enabled and p.influence < self.cfg.expose_fail:
                self.expose_refusals += 1
                self.gm_refusals += 1
                p.expose_refusals += 1
                self.events.append((self.game_id, self.round, "GM_REFUSAL",
                                    p.seat, "EXPOSE", p.influence))
                continue
            seat, secret = guess
            if not self.players[seat].alive:
                continue
            # As written the rules place no limit on re-Exposing a public Secret.
            # expose_once models the proposed fix.
            if self.cfg.expose_once and self.players[seat].secret_exposed:
                continue
            correct = self.players[seat].secret == secret
            if correct:
                self.move(seat, BANK, self.cfg.expose_penalty, "expose_hit")
                self.move(BANK, p.seat, self.cfg.expose_reward, "expose_reward")
                self.players[seat].secret_exposed = True
                p.successful_exposes += 1
                self.broadcast(lambda k, s=seat, sec=secret: (
                    k.known_secrets.__setitem__(s, sec), k.publicly_exposed.add(s)))
            else:
                self.move(p.seat, BANK, self.cfg.expose_fail, "expose_miss")
            self.events.append((self.game_id, self.round, "EXPOSE", seat, int(correct), p.seat))

    def resolve_interrogations(self) -> None:
        for p in list(self.living()):
            if not p.alive:
                continue
            accused = self.pol.interrogate(p.knowledge, p.archetype, p.influence,
                                           self.interrogation_cost,
                                           self.public_view(), self.cfg)
            if accused is None or not self.players[accused].alive or accused == p.seat:
                continue
            cost = self.interrogation_cost
            self.move(p.seat, BANK, cost, "interrogation_cost")
            self.interrogation_cost += self.cfg.interrogation_step
            self.interrogation_count += 1
            p.initiated_interrogation = True
            self.players[accused].interrogated = True
            self.players[accused].knowledge.times_accused += 1

            # Being publicly accused is personal, and the room takes sides.
            self.players[accused].knowledge.accused_me.add(p.seat)
            self.players[accused].knowledge.feel(p.seat, -1.4)
            for ally in self.players[accused].knowledge.allies(
                    [q.seat for q in self.living()]):
                self.players[ally].knowledge.feel(p.seat, -0.3)

            guilty_voters = []
            total = 0
            for voter in self.players:
                if voter.alive:
                    self.eligible_vote_opportunities += 1
                    if (self.cfg.interrogation_vote_eligibility_enabled
                            and voter.influence < self.cfg.guilty_vote_penalty):
                        self.vote_exclusions += 1
                        voter.vote_exclusions += 1
                        self.excluded_rounds.setdefault(voter.seat, set()).add(self.round)
                        attempt = getattr(self.pol, "would_attempt_ineligible_vote", None)
                        if attempt and attempt(
                                voter.knowledge, voter.archetype, accused,
                                self.public_view(), self.cfg):
                            self.gm_refusals += 1
                            self.events.append((self.game_id, self.round, "GM_REFUSAL",
                                                voter.seat, "INTERROGATION_VOTE",
                                                voter.influence))
                        continue
                elif self.cfg.ghost_vote_mode == "lifetime":
                    if voter.seat in self.ghost_vote_spent:
                        continue
                    if not self.pol.use_ghost_vote(
                            voter.knowledge, accused, "interrogation",
                            self.public_view(), self.cfg):
                        continue
                    self.ghost_vote_spent.add(voter.seat)
                    self.events.append((self.game_id, self.round, "GHOST_VOTE",
                                        voter.seat, accused, "interrogation"))
                total += 1
                if self.pol.vote_guilty(voter.knowledge, voter.archetype, accused,
                                        self.public_view(), self.cfg):
                    guilty_voters.append(voter.seat)
                    if voter.seat != accused:
                        self.players[accused].knowledge.voted_against_me[voter.seat] = (
                            self.players[accused].knowledge.voted_against_me.get(
                                voter.seat, 0) + 1)
                        self.players[accused].knowledge.feel(voter.seat, -0.5)
            guilty = len(guilty_voters)
            passed = guilty * 2 > total
            self.events.append((self.game_id, self.round, "INTERROGATION", accused,
                                guilty, f"{total}:{int(passed)}"))
            if not passed:
                self.move(BANK, accused, self.cfg.survivor_bonus, "survivor_bonus")
                self.broadcast(lambda k, s=accused: k.suspicion.__setitem__(
                    s, k.suspicion.get(s, 0.0) * 0.5))
                # A failed accusation costs the prosecutor public standing.
                p.failed_accusations += 1
                p.reputation -= 1.0
                for q in self.players:
                    q.knowledge.feel(p.seat, -0.35)
                continue

            victim = self.players[accused]
            was_assassin = victim.role == ASSASSIN
            self.kill(victim, to=BANK, share=self.cfg.execution_share, cause="EXECUTED")
            self.executions += 1
            for v in guilty_voters:
                self.players[v].guilty_votes_on_executed += 1
            self.executions_by_round[self.round] = self.executions_by_round.get(self.round, 0) + 1
            self.settle_guilty_votes(guilty_voters, was_assassin)
            if was_assassin:
                self.correct_executions += 1
                self.correct_executions_by_round[self.round] = (
                    self.correct_executions_by_round.get(self.round, 0) + 1
                )
                p.reputation += 2.0
                for q in self.players:
                    q.knowledge.feel(p.seat, 0.6)
                self.move(BANK, p.seat, cost, "prosecutor_refund")
                self.move(BANK, p.seat, self.cfg.prosecutor_reward, "prosecutor_reward")
                self.pay_bounty(p)
                self.promote_accomplice()
            else:
                # Executing an innocent damages everyone who pushed for it.
                p.reputation -= 1.5
                for v in guilty_voters:
                    self.players[v].reputation -= 0.4
            self.check_wipeout()
            # Mandatory Evidence disclosure after every Execution.
            if self.cfg.evidence_disclosure_enabled:
                self.disclose_evidence()

    def settle_guilty_votes(self, guilty_voters: list[int], was_assassin: bool) -> None:
        """Personal stakes: being right about the Assassin pays, being wrong costs."""
        for seat in guilty_voters:
            voter = self.players[seat]
            if not voter.alive:
                continue          # Ghosts vote but cannot hold Influence
            if was_assassin and self.cfg.guilty_vote_reward:
                self.move(BANK, seat, self.cfg.guilty_vote_reward, "guilty_vote_reward")
            elif not was_assassin and self.cfg.guilty_vote_penalty:
                self.move(seat, BANK, self.cfg.guilty_vote_penalty, "guilty_vote_penalty")

    def check_wipeout(self) -> None:
        """The Stash only falls to the room once the whole Syndicate is dead."""
        if not self.cfg.confiscate_on_wipeout or self.stash <= 0:
            return
        syndicate = {self.original_assassin, self.accomplice_seat}
        if any(self.players[s].alive for s in syndicate):
            return
        recipients = self.living()
        if not recipients:
            return
        share, remainder = divmod(self.stash, len(recipients))
        for i, q in enumerate(recipients):
            amt = share + (1 if i < remainder else 0)
            if amt:
                self.move(STASH, q.seat, amt, "stash_wipeout")
        self.events.append((self.game_id, self.round, "SYNDICATE_WIPEOUT", 0, 0, ""))

    def pay_bounty(self, prosecutor: Player) -> None:
        """F7: give innocents a reason to actually hunt the Assassin."""
        mode = self.cfg.bounty_mode
        if mode == "none":
            return
        recipients = [q for q in self.living()
                      if mode == "all_living"
                      or (mode == "prosecutor_faction" and q.faction == prosecutor.faction)]
        if not recipients:
            return
        if self.cfg.bounty_source == "stash":
            # The hoard is seized and split. No new Influence enters the economy,
            # and the Syndicate loses exactly what its victory is measured on.
            pot = int(self.stash * self.cfg.stash_confiscation)
            if pot <= 0:
                return
            share, remainder = divmod(pot, len(recipients))
            for i, q in enumerate(recipients):
                amt = share + (1 if i < remainder else 0)
                if amt:
                    self.move(STASH, q.seat, amt, "stash_confiscated")
        elif self.cfg.bounty_amount > 0:
            for q in recipients:
                self.move(BANK, q.seat, self.cfg.bounty_amount, "assassin_bounty")

    def promote_accomplice(self) -> None:
        if not self.cfg.promotion_enabled:
            return
        acc = self.players[self.accomplice_seat]
        if not acc.alive:
            return
        self.assassin_seat = self.accomplice_seat
        acc.role = ASSASSIN
        self.promoted = True
        self.assassin_threshold += self.cfg.promotion_threshold_bump
        self.events.append((self.game_id, self.round, "PROMOTION", acc.seat, 0, ""))
        if self.cfg.promotion_reveals_evidence:
            self.reveal_survivor_lead(acc)

    def reveal_survivor_lead(self, survivor: Player) -> None:
        """Catching the Assassin earns the room one true lead on who replaced them.

        With promotion happening in most games, the second half of the game is a hunt
        for the successor; without this, no fresh information is ever generated for it.
        """
        options = [
            f"MOTIVE:{survivor.motive}",
            f"AMBITION:{survivor.ambition}",
            f"SECRET:{survivor.secret}",
            f"ADVANTAGE:{survivor.advantage}",
        ]
        stmt = self.rng.choice(options)
        kind, _, value = stmt.partition(":")
        for p in self.players:
            p.knowledge.heard_evidence.append(stmt)
            p.knowledge.confirmed_evidence.add(stmt)
            self._apply_evidence(p, stmt)
            if kind == "SECRET":
                # A confirmed true Secret is a strong, checkable lead.
                for q in self.players:
                    if q.alive and p.knowledge.known_secrets.get(q.seat) == value:
                        p.knowledge.suspect(q.seat, 1.2)
        self.events.append((self.game_id, self.round, "SURVIVOR_LEAD", survivor.seat, 0, stmt))

    def disclose_evidence(self) -> None:
        """Every Evidence holder reads their statement aloud; listeners update suspicion."""
        statements = []
        for p in self.players:
            statements.extend(p.knowledge.evidence)
        if not statements:
            return
        for p in self.players:
            for stmt in statements:
                kind, _, value = stmt.partition(":")
                for q in self.players:
                    if q.seat == p.seat or not q.alive:
                        continue
                    if kind == "MOTIVE" and q.initiated_interrogation and value == WRATH:
                        p.knowledge.suspect(q.seat, 0.30)
                    elif kind == "AMBITION" and q.won_auction and value == COLLECTOR:
                        p.knowledge.suspect(q.seat, 0.30)
                    elif kind == "AMBITION" and q.successful_exposes >= 2 and value == BLACKMAILER:
                        p.knowledge.suspect(q.seat, 0.30)
                    elif kind == "SECRET" and p.knowledge.known_secrets.get(q.seat) == value:
                        p.knowledge.suspect(q.seat, 0.60)
        self.events.append((self.game_id, self.round, "EVIDENCE_DISCLOSURE",
                            len(statements), 0, ""))

    def claim_goals(self) -> None:
        band = {"pessimistic": 0.6, "expected": 0.8, "optimistic": 0.95}[self.cfg.behaviour_band]
        board = self.leaderboard()
        for p in self.living():
            if p.seat in board:
                p.was_on_leaderboard = True
        for p in self.living():
            if not p.motive_done and self.round <= self.cfg.motive_deadline:
                if self._motive_met(p, board) and self.rng.random() < band:
                    p.motive_done = True
                    self.move(BANK, p.seat, self.cfg.motive_reward, "motive_claim")
            if not p.ambition_done and self.round <= self.cfg.ambition_deadline:
                if self._ambition_met(p) and self.rng.random() < band:
                    p.ambition_done = True
                    if p.ambition == DIPLOMAT:
                        self.stage_public_pact(p)
                    self.move(BANK, p.seat, self.cfg.ambition_reward, "ambition_claim")

    def pact_partners(self, p: Player) -> list[int]:
        """Two living players from the two other Factions who would stand with you."""
        by_faction: dict[str, list[int]] = {}
        for s in sorted(p.knowledge.spoke_with):
            q = self.players[s]
            if q.alive and q.faction != p.faction:
                by_faction.setdefault(q.faction, []).append(s)
        if len(by_faction) < 2:
            return []
        return [group[0] for group in list(by_faction.values())[:2]]

    def stage_public_pact(self, p: Player) -> None:
        """The Pact is public and truthful, so the whole room learns three Factions."""
        partners = self.pact_partners(p)
        if not partners:
            return
        for seat in [p.seat] + partners:
            faction = self.players[seat].faction
            self.broadcast(lambda k, s=seat, f=faction: (
                k.known_faction.__setitem__(s, f), k.verified_faction.add(s)))
        self.events.append((self.game_id, self.round, "PUBLIC_PACT", p.seat,
                            len(partners), p.faction))

    def _motive_met(self, p: Player, board: list[int]) -> bool:
        k = p.knowledge
        if p.motive == VANITY:
            return p.was_on_leaderboard if self.cfg.goals_v2 else p.seat in board
        if p.motive == WRATH:
            return p.initiated_interrogation
        if p.motive == ESPIONAGE:
            if not self.cfg.goals_v2:
                return bool(k.known_secrets)      # as written: Secret Intel satisfies it
            # v2: name the Motive or Ambition of two different players. Neither is
            # ever granted at setup, so this can only be done by talking to people.
            if self.cfg.espionage_full_profile:
                named = {s for s in set(k.known_motive) & set(k.known_ambition)
                         if self.players[s].motive == k.known_motive[s]
                         and self.players[s].ambition == k.known_ambition[s]}
            else:
                named = {s for s, v in k.known_motive.items()
                         if self.players[s].motive == v}
                named |= {s for s, v in k.known_ambition.items()
                          if self.players[s].ambition == v}
            return len(named) >= self.cfg.espionage_targets
        if p.motive == COMMERCE:
            if not self.cfg.goals_v2:
                return len(k.traded_with) >= 3
            paid = sum(k.given_total.values())
            received = sum(k.received_total.values())
            return (
                len(k.traded_with) >= self.cfg.commerce_partners
                and paid >= self.cfg.commerce_min_paid
                and received - paid >= self.cfg.commerce_profit
            )
        return False

    def _ambition_met(self, p: Player) -> bool:
        if p.ambition == COLLECTOR:
            return p.won_auction
        if p.ambition == RADICAL:
            if self.cfg.goals_v2:
                # Give the player agency instead of depending on the whole table.
                return p.guilty_votes_on_executed >= 2
            return (self.executions_by_round.get(1, 0) > 0
                    and self.executions_by_round.get(2, 0) > 0)
        if p.ambition == BLACKMAILER:
            if self.cfg.goals_v2:
                return p.extortion_done
            return p.successful_exposes >= 2
        if p.ambition == DIPLOMAT:
            # Pure test only: two players from the two other Factions must be willing
            # to stand with you. The Pact itself is staged in claim_goals().
            partners = self.pact_partners(p)
            if len(partners) < 2:
                return False
            return all(self.rng.random() < 0.55 for _ in partners)
        return False

    def snapshot(self) -> None:
        for p in self.players:
            self.snapshots.append((self.game_id, self.round, p.seat, p.influence,
                                   int(p.alive), self.stash, self.bank))

    # ------------------------------------------------------------------
    # Final
    # ------------------------------------------------------------------

    def final(self) -> GameResult | None:
        self.phase = "FINAL"
        self.lock_bankruptcy()
        # Candidates stand first, so the room can spend its Reveal on someone who is
        # actually on the ballot -- or on a suspect, if catching the killer matters more.
        candidates = self.nominate() if self.cfg.reveal_after_nomination else []
        if self.cfg.reveal_enabled:
            self.reveal(candidates)
        if not self.cfg.reveal_after_nomination:
            candidates = self.nominate()
        winner_faction = self.election(candidates)
        self.winning_faction = winner_faction
        tax = self.cfg.assassin_survival_tax
        if tax and self.players[self.assassin_seat].alive:
            for q in self.living():
                if q.seat in (self.assassin_seat, self.accomplice_seat):
                    continue
                self.move(q.seat, BANK, min(tax, max(0, q.influence)),
                          "assassin_survival_tax")
        return None

    def lock_bankruptcy(self) -> None:
        for p in self.players:
            p.bankrupt_locked = bool(self.cfg.bankruptcy_enabled and p.influence < 0)
            if p.bankrupt_locked:
                self.events.append((self.game_id, self.round, "BANKRUPTCY_LOCKED",
                                    p.seat, p.influence, "FINAL_START"))

    def reveal(self, candidates: list[int] | None = None) -> None:
        candidates = candidates or []
        votes: dict[int, int] = {}
        for p in self.players:
            target = self.pol.reveal_target(p.knowledge, self.public_view(),
                                            candidates, p.archetype)
            if target is None:
                continue
            votes[target] = votes.get(target, 0) + 1
            if p.alive:
                extra = self.pol.reveal_buy(p.knowledge, p.archetype, p.influence, self.cfg)
                affordable = (max(0, p.influence) // self.cfg.reveal_vote_cost
                              if self.cfg.reveal_vote_cost > 0 else 0)
                extra = max(0, min(extra, affordable))
                if extra:
                    self.move(p.seat, BANK, extra * self.cfg.reveal_vote_cost, "reveal_votes")
                    votes[target] = votes.get(target, 0) + extra
        if not votes:
            return
        top = max(votes.values())
        for seat, v in votes.items():
            if v == top:
                revealed = self.players[seat].faction
                self.broadcast(lambda k, s=seat, f=revealed: (
                    k.known_faction.__setitem__(s, f), k.verified_faction.add(s)))
                self.events.append((self.game_id, self.round, "REVEAL", seat, v, revealed))

    def nominate(self) -> list[int]:
        eligible = [p for p in self.living()
                    if not self.is_bankrupt(p)]
        if not eligible:
            return []
        ranked = sorted(self.living(), key=lambda p: -p.influence)
        nominators = ranked[:max(2, self.cfg.candidate_count)]
        candidates: list[int] = []
        for nom in nominators:
            pick = self.pol.nominate(nom.knowledge, [p.seat for p in eligible],
                                     candidates, self.public_view(), nom.archetype)
            if pick is not None and pick not in candidates:
                candidates.append(pick)
        if not candidates and eligible:
            candidates.append(eligible[0].seat)
        for c in candidates:
            if self.cfg.candidates_declare:
                self.broadcast(lambda k, s=c, f=self.players[c].faction: (
                    k.known_faction.__setitem__(s, f), k.verified_faction.add(s)))
            self.events.append((self.game_id, self.round, "CANDIDATE", c, 0,
                                self.players[c].faction))
        return candidates

    def election(self, candidates: list[int]) -> str | None:
        if not candidates:
            return None
        ballots: list[tuple[Player, int]] = []
        for p in self.players:
            if not p.alive and self.cfg.ghost_vote_mode == "lifetime":
                if p.seat in self.ghost_vote_spent:
                    continue
                if not self.pol.use_ghost_vote(
                        p.knowledge, None, "final", self.public_view(), self.cfg):
                    continue
                self.ghost_vote_spent.add(p.seat)
                self.events.append((self.game_id, self.round, "GHOST_VOTE",
                                    p.seat, -1, "final"))
            # Voters act on belief, never on the true faction of a Candidate.
            weight = 1
            if p.alive:
                extra = self.pol.buy_votes(p.knowledge, p.archetype, p.influence,
                                           candidates, self.cfg)
                extra = max(0, min(extra, self.max_affordable_votes(p.influence)))
                if extra:
                    cost = self.vote_purchase_cost(extra)
                    self.move(p.seat, BANK, cost, "vote_purchase")
                    self.events.append((self.game_id, self.round, "VOTE_PURCHASE",
                                        p.seat, extra,
                                        f"{cost}:{self.cfg.vote_purchase_mode}"))
                    weight += extra
            ballots.append((p, weight))

        def count(options: list[int]) -> dict[int, int]:
            tally = {c: 0 for c in options}
            for voter, weight in ballots:
                choice = self.pol.final_vote(
                    voter.knowledge, options, voter.archetype)
                if choice is not None:
                    tally[choice] = tally.get(choice, 0) + weight
            return tally

        tally = count(candidates)
        if not tally or sum(tally.values()) == 0:
            return None
        self.events.append((self.game_id, self.round, "ELECTION_ROUND1",
                            max(tally, key=tally.get), max(tally.values()),
                            f"{sum(tally.values())}:{self.cfg.election_mode}"))

        if self.cfg.election_mode == "runoff" and len(candidates) > 2:
            shuffled = list(candidates)
            self.rng.shuffle(shuffled)
            finalists = sorted(shuffled, key=lambda c: tally[c], reverse=True)[:2]
            tally = count(finalists)

        top = max(tally.values())
        winners = [c for c, v in tally.items() if v == top]
        if len(winners) > 1:
            tally = count(winners)
            top = max(tally.values())
            winners = [c for c, v in tally.items() if v == top]
        winner = self.rng.choice(winners)
        total = sum(tally.values())
        share_bp = round(10_000 * tally[winner] / total) if total else 0
        self.events.append((self.game_id, self.round, "ELECTION", winner,
                            tally[winner], self.players[winner].faction))
        self.events.append((self.game_id, self.round, "ELECTION_META", winner,
                            share_bp, self.cfg.election_mode))
        return self.players[winner].faction

    def vote_purchase_cost(self, extra_votes: int) -> int:
        """Cost of a bundle of extra Final votes under the configured market."""
        if extra_votes <= 0:
            return 0
        if self.cfg.vote_purchase_mode == "escalating":
            return self.cfg.vote_cost * extra_votes * (extra_votes + 1) // 2
        return self.cfg.vote_cost * extra_votes

    def max_affordable_votes(self, influence: int) -> int:
        """Maximum extra Final votes purchasable without creating debt."""
        influence = max(0, influence)
        if self.cfg.vote_cost <= 0:
            return 0
        if self.cfg.vote_purchase_mode == "escalating":
            votes = 0
            while self.vote_purchase_cost(votes + 1) <= influence:
                votes += 1
        else:
            votes = influence // self.cfg.vote_cost
        if self.cfg.vote_purchase_mode == "capped":
            votes = min(votes, self.cfg.vote_purchase_cap)
        return votes

    # ------------------------------------------------------------------
    # Scoring
    # ------------------------------------------------------------------

    def result(self) -> GameResult:
        assassin = self.players[self.assassin_seat]
        assassin_total = max(0, assassin.influence) + self.stash if assassin.alive else 0
        syndicate_win = assassin.alive and assassin_total >= self.assassin_threshold

        magnate_total = sum(p.influence for p in self.players
                            if p.faction == MAGNATE and p.alive and p.influence > 0)
        magnate_win = magnate_total >= self.magnate_threshold

        wf = getattr(self, "winning_faction", None)
        personal = self.adjudicate(wf, magnate_win, syndicate_win)
        motive_completion = {
            motive: sum(1 for p in self.players if p.motive == motive and p.motive_done)
            for motive in MOTIVES
        }
        ambition_completion = {
            ambition: sum(
                1 for p in self.players if p.ambition == ambition and p.ambition_done
            )
            for ambition in AMBITIONS
        }
        zero_agency = sum(
            1 for p in self.players
            if not p.successful_exposes
            and not p.initiated_interrogation
            and not p.knowledge.traded_with
            and not p.motive_done
            and not p.ambition_done
        )
        positive = sorted(
            (max(0, p.influence) for p in self.living()), reverse=True
        )
        top_share = positive[0] / sum(positive) if positive and sum(positive) else 0.0
        return GameResult(
            game_id=self.game_id, n_players=self.n, seed=self.seed,
            aristocrat_win=(wf == ARISTOCRAT), reformer_win=(wf == REFORMER),
            magnate_win=magnate_win, syndicate_win=syndicate_win,
            magnate_total=magnate_total, magnate_threshold=self.magnate_threshold,
            assassin_total=assassin_total, assassin_threshold=self.assassin_threshold,
            assassin_alive=assassin.alive, stash=self.stash, bank=self.bank,
            circulating=sum(p.influence for p in self.living()),
            deaths=sum(1 for p in self.players if not p.alive),
            executions=self.executions, assassinations=self.assassinations,
            interrogations=self.interrogation_count,
            correct_executions=self.correct_executions,
            bankruptcies=sum(1 for p in self.players if self.is_bankrupt(p)),
            hits_met=self.hits_met,
            motives_claimed=sum(1 for p in self.players if p.motive_done),
            ambitions_claimed=sum(1 for p in self.players if p.ambition_done),
            winning_faction=wf, personal_wins=personal, ledger=self.ledger,
            events=self.events, snapshots=self.snapshots, players=self.players,
            eligible_vote_opportunities=self.eligible_vote_opportunities,
            vote_exclusions=self.vote_exclusions,
            repeat_vote_exclusions=sum(
                1 for rounds in self.excluded_rounds.values() if len(rounds) > 1),
            expose_attempts=self.expose_attempts,
            expose_refusals=self.expose_refusals,
            gm_refusals=self.gm_refusals,
            debt_rescue_transfers=self.debt_rescue_transfers,
            debt_rescued=self.debt_rescued,
            debt_by_cause=dict(self.debt_by_cause),
            executions_by_round=dict(self.executions_by_round),
            correct_executions_by_round=dict(self.correct_executions_by_round),
            deaths_by_round=dict(self.deaths_by_round),
            motive_completion_by_goal=motive_completion,
            ambition_completion_by_goal=ambition_completion,
            zero_agency_players=zero_agency,
            wealth_top_share=top_share,
        )

    def adjudicate(self, wf: str | None, magnate_win: bool,
                   syndicate_win: bool) -> dict[int, bool]:
        """Who personally won. The single source of truth for victory.

        Kept in the engine so every analysis reads the same adjudication; recomputing
        it per script is how an unimplemented variant went unnoticed.
        """
        out: dict[int, bool] = {}
        for p in self.players:
            if p.role in (ASSASSIN, ACCOMPLICE):
                out[p.seat] = syndicate_win
                continue
            if not p.alive and not self.cfg.ghosts_keep_faction_victory:
                out[p.seat] = False          # death forfeits the Faction Victory
                continue
            if self.is_bankrupt(p):
                out[p.seat] = False          # Bankruptcy is a personal penalty
                continue
            out[p.seat] = magnate_win if p.faction == MAGNATE else (p.faction == wf)
        return out


def run_game(n_players: int, seed: int, config: Config | None = None,
             policy_module=None) -> GameResult:
    return Game(n_players, seed, config, policy_module).run()
