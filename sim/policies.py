"""Behavioural policies for simulated players.

Every function receives a player's isolated Knowledge plus public information.
None of them receive the Game object, so hidden state cannot leak into decisions.
"""

from __future__ import annotations

import random

from .engine import (
    ARISTOCRAT, REFORMER, MAGNATE, ASSASSIN, ACCOMPLICE,
    SECRETS, VANITY, WRATH, ESPIONAGE, COMMERCE,
    COLLECTOR, RADICAL, BLACKMAILER, DIPLOMAT,
)

_rng = random.Random(0)


def seed_policies(seed: int) -> None:
    _rng.seed(seed)


def debt_rescues(k, persona, influence, debtors, public, cfg):
    """Choose legal Private-Phase transfers that clear another player's debt.

    The player keeps a small reserve and only rescues someone they regard positively
    or whose Faction they have verified as their own. Round 3 is the main rescue
    window because Bankruptcy is fixed immediately afterward.
    """
    if influence <= 1 or not debtors:
        return []
    urgency = 0.75 if public["round"] == 3 else 0.12
    reserve = 2 if persona in ("MERCHANT", "WALLFLOWER") else 1
    available = max(0, influence - reserve)
    if available <= 0:
        return []
    ranked = sorted(
        debtors,
        key=lambda item: (
            item[0] not in k.verified_faction,
            -k.regard(item[0]),
            item[1],
        ),
    )
    out = []
    for seat, debt in ranked:
        allied = k.known_faction.get(seat) == k.faction
        regard = k.regard(seat)
        chance = urgency * (1.0 if allied else max(0.0, 0.35 + 0.2 * regard))
        if available > 0 and _rng.random() < chance:
            amount = min(available, debt)
            if amount:
                out.append((seat, amount))
                available -= amount
    return out


def binding_contract_partner(k, persona, influence, candidates, public, cfg):
    """Choose a counterpart for a limited binding support agreement."""
    total_cost = cfg.binding_contract_fee + cfg.binding_contract_stake
    if influence < total_cost or not candidates:
        return None
    chance = cfg.binding_contract_sign_rate * (
        1.25 if persona in ("POLITICIAN", "MERCHANT") else 0.75
    )
    if _rng.random() >= min(1.0, chance):
        return None
    verified_allies = [
        seat for seat in candidates if k.known_faction.get(seat) == k.faction
    ]
    if verified_allies:
        return max(verified_allies, key=k.regard)
    trusted = [seat for seat in candidates if k.regard(seat) > 0]
    return max(trusted, key=k.regard) if trusted else _rng.choice(candidates)


# --------------------------------------------------------------------------
# Personas
#
# Five recognisable people at a house party. Each is defined by behaviour, not
# by a single propensity number: how much they talk, whether they lie, who they
# trust, how they react to being accused, and what they do at the ballot.
# At 15 players there are exactly three of each.
# --------------------------------------------------------------------------

PERSONAS = ("POLITICIAN", "DETECTIVE", "MERCHANT", "WALLFLOWER", "FIREBRAND")

PROFILE = {
    # Works the room, builds a bloc, trades favours for votes.
    "POLITICIAN": dict(
        talk=6.0, trade=0.75, expose=0.30, interrogate=0.25, spend=0.70,
        lie_faction=0.45, share_goal=0.60, share_secret=0.45, share_evidence=0.55,
        share_suspicion=0.55, trust_gain=1.2, suspicion_bar=0.75,
        seeks_candidacy=1.0, bloc_voting=1.0, tribute=0.45, retaliates=0.6,
    ),
    # Tracks who paid whom; low trust, high scrutiny, publishes findings.
    "DETECTIVE": dict(
        talk=4.5, trade=0.25, expose=0.55, interrogate=0.85, spend=0.35,
        lie_faction=0.10, share_goal=0.25, share_secret=0.55, share_evidence=0.80,
        share_suspicion=0.85, trust_gain=0.5, suspicion_bar=0.35,
        seeks_candidacy=0.2, bloc_voting=0.5, tribute=0.20, retaliates=0.3,
    ),
    # Maximises Influence, avoids fights, sells votes and information.
    "MERCHANT": dict(
        talk=5.5, trade=0.95, expose=0.20, interrogate=0.10, spend=0.45,
        lie_faction=0.30, share_goal=0.55, share_secret=0.60, share_evidence=0.45,
        share_suspicion=0.30, trust_gain=1.0, suspicion_bar=0.85,
        seeks_candidacy=0.4, bloc_voting=0.3, tribute=0.65, retaliates=0.2,
    ),
    # Quiet, hoards, never initiates, survives by being uninteresting.
    "WALLFLOWER": dict(
        talk=2.0, trade=0.15, expose=0.10, interrogate=0.05, spend=0.15,
        lie_faction=0.15, share_goal=0.15, share_secret=0.15, share_evidence=0.20,
        share_suspicion=0.15, trust_gain=0.8, suspicion_bar=0.95,
        seeks_candidacy=0.1, bloc_voting=0.7, tribute=0.25, retaliates=0.1,
    ),
    # Accuses on thin evidence, lies freely, drives executions.
    "FIREBRAND": dict(
        talk=5.0, trade=0.35, expose=0.70, interrogate=0.95, spend=0.60,
        lie_faction=0.55, share_goal=0.35, share_secret=0.50, share_evidence=0.60,
        share_suspicion=0.75, trust_gain=0.6, suspicion_bar=0.20,
        seeks_candidacy=0.6, bloc_voting=0.4, tribute=0.30, retaliates=0.9,
    ),
}


def _p(persona: str) -> dict:
    return PROFILE.get(persona, PROFILE["WALLFLOWER"])


def _traits(persona: str):
    """Back-compatible 4-tuple view of a persona."""
    d = _p(persona)
    return d["trade"], d["expose"], d["interrogate"], d["spend"]


def _top_suspect(k, living: list[int]) -> tuple[int | None, float]:
    pool = {s: v for s, v in k.suspicion.items()
            if s in living and s != k.seat and s not in k.confirmed_clear}
    for s in k.confirmed_syndicate:
        if s in living:
            pool[s] = pool.get(s, 0.0) + 5.0
    # Grudges colour who you are willing to believe is guilty.
    for s in list(pool):
        pool[s] = pool[s] - 0.35 * k.regard(s)
    if not pool:
        return None, 0.0
    seat = max(pool, key=pool.get)
    return seat, pool[seat]


# --------------------------------------------------------------------------
# Private phase
# --------------------------------------------------------------------------

def transfers(k, archetype, influence, targets, public, cfg):
    """Gifts during the Private Phase. Returns [(dst, amount)]."""
    if influence <= 2 or not targets:
        return []
    trade, _, _, _ = _traits(archetype)

    # Commerce needs three distinct partners; chase it early.
    if k.motive == COMMERCE and len(k.traded_with) < 3:
        trade = max(trade, 0.9)
    if k.ambition == DIPLOMAT and len(k.traded_with) < 2:
        trade = max(trade, 0.7)
    # Magnates, the Syndicate, and anyone chasing the Leaderboard are saving.
    if k.faction == MAGNATE or k.role in (ASSASSIN, ACCOMPLICE):
        trade *= 0.45
    if k.motive == VANITY:
        trade *= 0.5

    out = []
    budget = max(0, influence - 3)
    n = 0
    while n < 3 and budget > 0 and _rng.random() < trade:
        dst = _rng.choice(targets)
        amt = min(budget, _rng.randint(1, 2))
        out.append((dst, amt))
        budget -= amt
        n += 1
    return out


def assassin_plan(k, influence, candidates, public, cfg):
    """Pick a victim and a camouflage spray.

    candidates = [(seat, influence, meets_hit, threat)]. A real Assassin removes
    the people who are closing in, not just the richest body in the room.
    """
    if not candidates:
        return None, []
    matching = [c for c in candidates if c[2]]
    pool = matching or candidates
    # Score = wealth + how dangerous they are to the Syndicate.
    def score(c):
        threat = c[3] if len(c) > 3 else 0.0
        return c[1] + 3.0 * threat + 2.0 * k.suspicion.get(c[0], 0.0)
    pool = sorted(pool, key=score, reverse=True)
    target = pool[0][0] if _rng.random() < 0.75 else _rng.choice(pool)[0]

    spray = []
    others = [c[0] for c in candidates if c[0] != target]
    budget = max(0, influence - 2)
    while others and budget > 0 and len(spray) < 3 and _rng.random() < 0.6:
        pick = _rng.choice(others)
        others.remove(pick)
        spray.append(pick)
        budget -= 1
    return target, spray


def launder(k, influence, cfg):
    if influence <= 4:
        return 0
    return min(cfg.launder_cap, influence - 4)


def withdraw_stash(k, influence, stash, cfg):
    """Take money out of the vault to spend now.

    Stash Influence counts toward victory but buys nothing, so withdrawing trades
    victory progress for live power. Only worth it when short of operating cash.
    """
    if influence >= 6 or stash <= 0:
        return 0
    need = 6 - influence
    return min(need, cfg.stash_withdraw_cap)


def auction_bid(k, archetype, influence, public, cfg):
    if influence < 2:
        return 0
    _, _, _, spend = _traits(archetype)
    want = 0.35 + spend * 0.3
    if k.ambition == COLLECTOR:
        want = 0.98
    if k.role in (ASSASSIN, ACCOMPLICE):
        want += 0.25  # buying the true Evidence keeps it out of hunters' hands
    if k.faction == MAGNATE:
        want *= 0.5
    if _rng.random() > want:
        return 0
    ceiling = max(1, int(influence * (0.8 if k.ambition == COLLECTOR else 0.3)))
    return _rng.randint(1, max(1, ceiling))


# --------------------------------------------------------------------------
# Private conversations
# --------------------------------------------------------------------------

def conversation_count(k, persona, cfg):
    d = _p(persona)
    base = d["talk"]
    if k.motive == ESPIONAGE:
        base += 1.5
    if k.ambition == DIPLOMAT:
        base += 1.0
    if k.motive == COMMERCE:
        base += 1.0
    return max(1, int(round(base * getattr(cfg, "talkativeness", 1.0))))


def shares_own_goal(k, other_seat, cfg, persona="WALLFLOWER"):
    needs_help = k.motive == COMMERCE or k.ambition in (DIPLOMAT, BLACKMAILER)
    p = _p(persona)["share_goal"] * (1.6 if needs_help else 0.35)
    if k.role in (ASSASSIN, ACCOMPLICE):
        p *= 0.6
    if k.regard(other_seat) >= 1.0:
        p += 0.20
    return _rng.random() < p


def shares_secret(k, other_seat, cfg, persona="WALLFLOWER"):
    p = _p(persona)["share_secret"]
    if k.regard(other_seat) >= 1.0:
        p += 0.20
    return _rng.random() < p


def shares_evidence(k, other_seat, cfg, persona="WALLFLOWER"):
    p = _p(persona)["share_evidence"]
    if k.regard(other_seat) <= -0.8:
        p *= 0.4          # you do not brief someone you distrust
    return _rng.random() < p


def shares_suspicion(k, other_seat, cfg, persona="WALLFLOWER"):
    if not k.suspicion or _rng.random() > _p(persona)["share_suspicion"]:
        return None
    if k.role in (ASSASSIN, ACCOMPLICE):
        pool = [s for s in k.suspicion
                if s not in (k.partner, k.seat, other_seat)]
        return _rng.choice(pool) if pool else None
    seat = max(k.suspicion, key=k.suspicion.get)
    return None if seat == other_seat else seat


def extortion_targets(k, others, cfg):
    if not others:
        return []
    # Lean on people who already owe you goodwill.
    ranked = sorted(others, key=lambda s: -k.regard(s))
    return ranked[:3]


def pays_tribute(k, persona, influence, asker, cfg):
    if influence < cfg.extortion_amount + 2:
        return False
    p = _p(persona)["tribute"]
    if asker in k.spoke_with:
        p += 0.15
    p += 0.12 * k.regard(asker)
    if k.role in (ASSASSIN, ACCOMPLICE):
        p += 0.10          # paying for goodwill is cheap cover
    return _rng.random() < p


# --------------------------------------------------------------------------
# Council
# --------------------------------------------------------------------------

def expose(k, persona, influence, public, cfg):
    if getattr(cfg, "expose_eligibility_enabled", False) and influence < cfg.expose_fail:
        return None
    exp = _p(persona)["expose"]
    living = public["living"]
    if k.ambition == BLACKMAILER:
        exp = max(exp, 0.8)
    if k.motive == ESPIONAGE:
        exp = max(exp, 0.5)

    known = [(s, sec) for s, sec in k.known_secrets.items() if s in living and s != k.seat]
    if getattr(cfg, "expose_once", False):
        known = [(s, sec) for s, sec in known if s not in k.publicly_exposed]
    # You are far likelier to burn someone you dislike.
    known.sort(key=lambda pair: k.regard(pair[0]))
    if known and _rng.random() < exp:
        pick = known[0] if _rng.random() < 0.6 else _rng.choice(known)
        return pick
    if k.ambition == BLACKMAILER and influence > 4 and _rng.random() < 0.35:
        pool = [s for s in living if s != k.seat]
        if pool:
            return (_rng.choice(pool), _rng.choice(SECRETS))
    return None


def interrogate(k, persona, influence, cost, public, cfg):
    d = _p(persona)
    if influence < cost:
        return None
    living = public["living"]
    seat, score = _top_suspect(k, living)

    if k.motive == WRATH and public["round"] == 1 and influence >= cost:
        if seat is None:
            pool = [s for s in living if s != k.seat and s not in k.confirmed_clear]
            if pool:
                return _rng.choice(pool)
        return seat
    if k.ambition == RADICAL and public["round"] <= 2:
        d = dict(d, interrogate=max(d["interrogate"], 0.6))

    # Retaliation: some personas answer an accusation with an accusation.
    if k.accused_me and _rng.random() < d["retaliates"]:
        enemies = [s for s in k.accused_me if s in living]
        if enemies:
            return _rng.choice(enemies)

    if seat is None or score < d["suspicion_bar"]:
        return None
    if k.role in (ASSASSIN, ACCOMPLICE) and seat == k.partner:
        return None
    return seat if _rng.random() < d["interrogate"] * min(1.0, score) else None


def vote_guilty(k, persona, accused, public, cfg):
    d = _p(persona)
    if accused == k.seat:
        return False
    if k.role in (ASSASSIN, ACCOMPLICE) and accused == k.partner:
        return False
    if accused in k.confirmed_syndicate:
        return True
    if accused in k.confirmed_clear:
        return False
    if k.role in (ASSASSIN, ACCOMPLICE):
        return _rng.random() < 0.55
    score = k.suspicion.get(accused, 0.0)
    # You defend your friends and condemn those who crossed you.
    regard = k.regard(accused)
    if regard >= 1.0 and score < 1.5:
        return False
    if accused in k.accused_me and _rng.random() < d["retaliates"]:
        return True
    if score >= 0.6 + 0.4 * regard:
        return True
    # Wallflowers follow the room rather than lead it.
    base = min(0.45, score) * (1.3 if persona == "FIREBRAND" else 1.0)
    return _rng.random() < base


def would_attempt_ineligible_vote(k, persona, accused, public, cfg):
    """Sensible players understand the eligibility rule."""
    return False


def use_ghost_vote(k, accused, context, public, cfg):
    """Choose when to spend the optional one-lifetime Ghost vote.

    Ghosts conserve it during Interrogations unless they have a strong read; an
    unspent vote is always used in the Final.
    """
    if context == "final":
        return True
    if accused in k.confirmed_syndicate:
        return True
    if accused in k.confirmed_clear:
        return False
    return k.suspicion.get(accused, 0.0) >= 0.8


def choose_heir(k, heirs):
    if k.role in (ASSASSIN, ACCOMPLICE) and k.partner in heirs:
        return k.partner
    # You leave your money to a friend, not to the person who accused you.
    ranked = sorted(heirs, key=lambda s: -k.regard(s))
    return ranked[0] if ranked else _rng.choice(heirs)


# --------------------------------------------------------------------------
# Final
# --------------------------------------------------------------------------

def claims_faction(k, other_seat, cfg, persona="WALLFLOWER"):
    return _rng.random() < 0.35 + 0.5 * _p(persona)["share_goal"]


def lies_about_faction(k, cfg, persona="WALLFLOWER"):
    # Magnates are publicly cleared of Syndicate membership, so claiming Magnate is
    # the standard bluff -- which is exactly why nobody can trust the claim.
    p = _p(persona)["lie_faction"]
    if k.role in (ASSASSIN, ACCOMPLICE):
        p = min(0.9, p + 0.25)
    if k.faction == MAGNATE:
        p *= 0.3
    return _rng.random() < p


def reveal_target(k, public, candidates=None, persona="WALLFLOWER"):
    """Spend the Reveal on a Candidate for political value, or a suspect to hunt."""
    d = _p(persona)
    living = public["living"]
    candidates = [c for c in (candidates or []) if c in living]
    unknown = [c for c in candidates if c not in k.verified_faction]
    seat, score = _top_suspect(k, living)

    # Detectives and Firebrands hunt; Politicians and Merchants play the election.
    political = d["seeks_candidacy"] + d["bloc_voting"]
    if unknown and (seat is None or score < 1.0 or _rng.random() < 0.35 + 0.3 * political):
        return _rng.choice(unknown)
    if seat is not None:
        return seat
    pool = [s for s in living if s != k.seat]
    return _rng.choice(pool) if pool else None


def reveal_buy(k, persona, influence, cfg):
    if influence < 6:
        return 0
    if k.faction == MAGNATE or k.role in (ASSASSIN, ACCOMPLICE):
        return 0
    return 1 if _rng.random() < _p(persona)["spend"] * 0.5 else 0


def nominate(k, eligible, already, public, persona="WALLFLOWER"):
    pool = [s for s in eligible if s not in already]
    if not pool:
        return None
    d = _p(persona)
    if k.seat in pool and _rng.random() < d["seeks_candidacy"]:
        return k.seat
    # Otherwise back the ally you trust most.
    allies = [s for s in pool if k.regard(s) >= 0.8]
    if allies and _rng.random() < d["bloc_voting"]:
        return max(allies, key=k.regard)
    return _rng.choice(pool)


def _believed_own(k, candidates):
    return [c for c in candidates if k.known_faction.get(c) == k.faction]


def final_vote(k, candidates, persona="WALLFLOWER"):
    """Vote on belief. A Candidate whose colours you never learned is a gamble."""
    if not candidates:
        return None
    own = _believed_own(k, candidates)
    if own:
        return own[0]
    plausible = [c for c in candidates
                 if k.known_faction.get(c) in (None, k.faction)]
    pool = plausible or candidates
    # With no political read, back a friend and never back an enemy.
    ranked = sorted(pool, key=lambda c: -k.regard(c))
    if k.regard(ranked[0]) >= 0.8 and _rng.random() < _p(persona)["bloc_voting"]:
        return ranked[0]
    return _rng.choice(pool)


def buy_votes(k, persona, influence, candidates, cfg):
    if k.faction == MAGNATE or k.role in (ASSASSIN, ACCOMPLICE):
        return 0
    own = _believed_own(k, candidates)
    if not own or influence < cfg.vote_cost:
        return 0
    d = _p(persona)
    spend = d["spend"] * (0.5 + 0.5 * d["bloc_voting"])
    if own[0] not in k.verified_faction:
        spend *= 0.5
    if cfg.vote_purchase_mode == "escalating":
        affordable = 0
        while (cfg.vote_cost * (affordable + 1) * (affordable + 2) // 2
               <= influence):
            affordable += 1
    else:
        affordable = influence // cfg.vote_cost
    if cfg.vote_purchase_mode == "capped":
        affordable = min(affordable, cfg.vote_purchase_cap)
    return min(affordable, max(0, int(affordable * spend)))
