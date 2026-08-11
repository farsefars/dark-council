"""Correctness gate for the Dark Council engine.

Analysis is only trustworthy if the engine implements the rules *in the configuration
that is actually played*. An earlier version of this gate tested the default Config
while every reported result used the recommended one, so it was green while checking a
different game. It now runs the whole battery across a matrix of configurations.
"""

from __future__ import annotations

import ast
from collections import Counter
import dataclasses
import os
import sys

from .engine import (
    Game, Config, SCALING, ARISTOCRAT, REFORMER, MAGNATE,
    ASSASSIN, ACCOMPLICE, DIPLOMAT, run_game,
)
from .final import recommended_config
from .chaos import ChaosConfig, chaos_policies
from .exploits import EXPLOITS, ExploitPolicies

FAILURES: list[str] = []
HERE = os.path.dirname(os.path.abspath(__file__))


def check(name: str, condition: bool, detail: str = "") -> None:
    if not condition:
        FAILURES.append(f"{name}: {detail}")


# --------------------------------------------------------------------------
# Configuration matrix: every configuration whose results we rely on.
# --------------------------------------------------------------------------

def config_matrix(n: int) -> dict[str, Config]:
    return {
        "default": Config(),
        "recommended": recommended_config(n),
        "reveal_first": recommended_config(n, reveal_after_nomination=False),
        "open_factions": recommended_config(n, ally_hint="open"),
        "ghosts_forfeit": recommended_config(n, ghosts_keep_faction_victory=False),
        "ghost_vote_lifetime": recommended_config(n, ghost_vote_mode="lifetime"),
        "runoff": recommended_config(n, election_mode="runoff"),
        "escalating_votes": recommended_config(
            n, vote_purchase_mode="escalating"),
        "minimal_systems": recommended_config(
            n, hits_enabled=False, private_transfers_enabled=False,
            goals_enabled=False, auction_enabled=False, expose_enabled=False,
            interrogation_enabled=False, reveal_enabled=False,
            evidence_disclosure_enabled=False, promotion_enabled=False,
            kill_tell_required=False, bankruptcy_enabled=False),
        "no_incentive": recommended_config(n, guilty_vote_reward=0,
                                           guilty_vote_penalty=0,
                                           promotion_reveals_evidence=False),
        "legacy_rules": Config(expose_once=False, ghost_mode="public",
                               kill_tell_scope="round"),
    }


# --------------------------------------------------------------------------
# Per-game invariants
# --------------------------------------------------------------------------

def check_game(label: str, g: Game, res, n: int) -> None:
    tag = f"[{label}] {g.game_id}"
    a, r, m, _, _ = SCALING[n]

    # 1. Influence conservation.
    total = sum(p.influence for p in g.players) + g.bank + g.stash
    check("conservation", total == 0, f"{tag} sum={total}")

    # 2. Faction sizes (the extra seat may fall to either major faction).
    by = {f: sum(1 for p in g.players if p.faction == f)
          for f in (ARISTOCRAT, REFORMER, MAGNATE)}
    check("faction_sizes",
          sorted([by[ARISTOCRAT], by[REFORMER]]) == sorted([a, r]) and by[MAGNATE] == m,
          f"{tag} {by} expected {(a, r, m)}")

    # 3. Syndicate is one Aristocrat and one Reformer, never a Magnate.
    syn = [g.players[s] for s in (g.original_assassin, g.accomplice_seat)]
    check("syndicate_placement",
          {syn[0].faction, syn[1].faction} == {ARISTOCRAT, REFORMER},
          f"{tag} {[p.faction for p in syn]}")

    # 4. Evidence: exactly two of the four dealt are false; the Auction piece is true.
    false_dealt = sum(1 for s in g.dealt_evidence if not g.evidence_is_true(s))
    check("evidence_noise_budget", false_dealt == 2, f"{tag} false={false_dealt}")
    check("auction_evidence_true", g.evidence_is_true(g.auction_evidence),
          f"{tag} {g.auction_evidence}")

    # 5. Ghosts never end holding Influence.
    for p in g.players:
        if not p.alive:
            check("ghost_no_holdings", p.influence <= 0,
                  f"{tag} seat {p.seat} holds {p.influence}")

    # 6/7. Assassination legality.
    for rnd, victim in [(e[1], e[3]) for e in res.events if e[2] == "ASSASSINATED"]:
        check("victim_not_accomplice", victim != g.accomplice_seat,
              f"{tag} r{rnd} killed the Accomplice")
        paid = [l for l in res.ledger
                if l[4] == str(victim)
                and l[6] in ("kill_tell", "camouflage", "gift", "tribute")
                and int(l[1]) <= rnd]
        if g.cfg.kill_tell_required:
            check("kill_tell_paid", bool(paid),
                  f"{tag} r{rnd} victim {victim} never paid")

    # 8. Interrogation cost escalation.
    costs = [l[5] for l in res.ledger if l[6] == "interrogation_cost"]
    expected = [g.cfg.interrogation_base + i * g.cfg.interrogation_step
                for i in range(len(costs))]
    check("interrogation_escalation", costs == expected, f"{tag} {costs} != {expected}")

    # 9. No Influence gifts during a public phase.
    bad = [l for l in res.ledger
           if l[2] in ("COUNCIL", "AUCTION")
           and l[6] in ("gift", "camouflage", "kill_tell", "tribute")]
    check("no_public_transfers", not bad, f"{tag} {bad[:2]}")

    # 10. At most one living Assassin.
    check("single_assassin",
          sum(1 for p in g.players if p.alive and p.role == ASSASSIN) <= 1, tag)

    # --- new mechanics -----------------------------------------------------

    # 11. The Stash is inherited wealth: split only when the Syndicate is wiped out.
    seized = [l for l in res.ledger if l[6] in ("stash_confiscated", "stash_wipeout")]
    syn_alive = any(g.players[s].alive for s in (g.original_assassin, g.accomplice_seat))
    if g.cfg.confiscate_on_wipeout and g.cfg.bounty_mode == "none":
        check("stash_survives_while_syndicate_lives", not (seized and syn_alive),
              f"{tag} seized {sum(l[5] for l in seized)} while a member lived")
        if not syn_alive:
            check("stash_split_on_wipeout", g.stash == 0,
                  f"{tag} stash {g.stash} kept after wipeout")

    # 12. Guilty-vote stakes pay only on a correct verdict, and cost only on a wrong one.
    rewards = [l for l in res.ledger if l[6] == "guilty_vote_reward"]
    penalties = [l for l in res.ledger if l[6] == "guilty_vote_penalty"]
    if g.cfg.guilty_vote_reward == 0:
        check("no_unconfigured_rewards", not rewards, f"{tag} {len(rewards)} paid")
    if rewards:
        check("rewards_require_correct_verdict", g.correct_executions > 0,
              f"{tag} rewards paid with no correct execution")
    if penalties:
        check("penalties_require_wrong_verdict",
              g.executions > g.correct_executions,
              f"{tag} penalties charged with no wrong execution")

    # 13. Variant accounting must remain physically payable and internally bounded.
    vote_bundles = [e for e in res.events if e[2] == "VOTE_PURCHASE"]
    for e in vote_bundles:
        seat, extra = int(e[3]), int(e[4])
        cost, _, mode = str(e[5]).partition(":")
        expected = (g.cfg.vote_cost * extra * (extra + 1) // 2
                    if mode == "escalating" else g.cfg.vote_cost * extra)
        check("vote_purchase_cost", int(cost) == expected,
              f"{tag} seat {seat} paid {cost} for {extra} under {mode}")
        if mode == "capped":
            check("vote_purchase_cap", extra <= g.cfg.vote_purchase_cap,
                  f"{tag} seat {seat} bought {extra}")

    if g.cfg.ghost_vote_mode == "lifetime":
        ghost_votes = [int(e[3]) for e in res.events if e[2] == "GHOST_VOTE"]
        check("ghost_lifetime_vote", len(ghost_votes) == len(set(ghost_votes)),
              f"{tag} repeated={ghost_votes}")

    # 14. The successor lead must be TRUE of the surviving Syndicate member.
    for e in res.events:
        if e[2] == "SURVIVOR_LEAD":
            survivor = g.players[int(e[3])]
            kind, _, value = str(e[5]).partition(":")
            truth = {"MOTIVE": survivor.motive, "AMBITION": survivor.ambition,
                     "SECRET": survivor.secret, "ADVANTAGE": survivor.advantage}
            check("survivor_lead_is_true", truth.get(kind) == value,
                  f"{tag} {e[5]} but survivor has {truth.get(kind)}")

    # 15. A verified faction belief must never be false.
    for p in g.players:
        for seat in p.knowledge.verified_faction:
            claimed = p.knowledge.known_faction.get(seat)
            check("verified_faction_is_true", g.players[seat].faction == claimed,
                  f"{tag} seat {p.seat} verified {seat} as {claimed}")

    # 16. A Public Pact fires only on a claimed Ambition, and never twice.
    pacts = [int(e[3]) for e in res.events if e[2] == "PUBLIC_PACT"]
    check("pact_no_duplicates", len(pacts) == len(set(pacts)), f"{tag} {pacts}")
    for seat in pacts:
        p = g.players[seat]
        check("pact_only_when_claimed", p.ambition == DIPLOMAT and p.ambition_done,
              f"{tag} seat {seat} staged a Pact without claiming it")

    # 17. Reveal ordering.
    order = [e[2] for e in res.events if e[2] in ("CANDIDATE", "REVEAL")]
    if g.cfg.reveal_after_nomination and "CANDIDATE" in order and "REVEAL" in order:
        check("reveal_after_nomination",
              order.index("CANDIDATE") < order.index("REVEAL"), f"{tag} {order}")

    # 18. Capped Goals are never dealt more often than they can be achieved.
    if g.cfg.cap_goals:
        collectors = sum(1 for p in g.players if p.ambition == "COLLECTOR")
        vanities = sum(1 for p in g.players if p.motive == "VANITY")
        check("collector_cap", collectors <= 1, f"{tag} {collectors} Collectors")
        check("vanity_cap", vanities <= 3, f"{tag} {vanities} Vanity")


# --------------------------------------------------------------------------
# Static guards
# --------------------------------------------------------------------------

def check_config_fields_are_read() -> None:
    """A Config field no engine code reads is a silent lie: it lets a variant be
    'tested' while changing nothing. This class of bug has already cost one wrong
    conclusion, so it now fails the gate."""
    sources = ""
    for name in ("engine.py", "policies.py"):
        with open(os.path.join(HERE, name), encoding="utf-8") as fh:
            sources += fh.read() + "\n"
    tree = ast.parse(sources)
    read = {node.attr for node in ast.walk(tree) if isinstance(node, ast.Attribute)}
    read |= {node.id for node in ast.walk(tree) if isinstance(node, ast.Name)}
    read |= {node.value for node in ast.walk(tree)
             if isinstance(node, ast.Constant) and isinstance(node.value, str)}
    for f in dataclasses.fields(Config):
        check("config_field_is_read", f.name in read,
              f"Config.{f.name} is never read by the engine")


def check_no_duplicate_definitions() -> None:
    """A redefined function silently shadows the earlier one. This has already caused
    two live bugs (an omniscient final_vote and a persona-blind nominate), so it now
    fails the gate."""
    import collections
    for name in ("engine.py", "policies.py", "validate.py", "final.py", "run.py",
                 "ab_tests.py", "removal_probe.py"):
        path = os.path.join(HERE, name)
        with open(path, encoding="utf-8") as fh:
            tree = ast.parse(fh.read())
        counts = collections.Counter(
            n.name for n in tree.body if isinstance(n, (ast.FunctionDef, ast.ClassDef)))
        for fn, count in counts.items():
            check("no_duplicate_definitions", count == 1,
                  f"{name}: {fn} defined {count} times")
        for node in tree.body:
            if isinstance(node, ast.ClassDef):
                inner = collections.Counter(
                    c.name for c in node.body if isinstance(c, ast.FunctionDef))
                for fn, count in inner.items():
                    check("no_duplicate_definitions", count == 1,
                          f"{name}: {node.name}.{fn} defined {count} times")


def check_personas_are_distinguishable() -> None:
    """Personas must produce materially different play, or they are decoration.
    The previous four-float archetypes differed by only 2.5pp in win rate."""
    from . import policies as P
    import statistics
    wins = {p: [0, 0] for p in P.PERSONAS}
    deaths = {p: [0, 0] for p in P.PERSONAS}
    interrogations = {p: [0, 0] for p in P.PERSONAS}
    influence = {p: [] for p in P.PERSONAS}
    for i in range(400):
        r = run_game(15, 700_000 + i, recommended_config(15))
        for p in r.players:
            wins[p.archetype][0] += r.personal_wins[p.seat]
            wins[p.archetype][1] += 1
            deaths[p.archetype][0] += 0 if p.alive else 1
            deaths[p.archetype][1] += 1
            interrogations[p.archetype][0] += int(p.initiated_interrogation)
            interrogations[p.archetype][1] += 1
            influence[p.archetype].append(max(0, p.influence))
    win_rates = {p: w / n for p, (w, n) in wins.items()}
    death_rates = {p: d / n for p, (d, n) in deaths.items()}
    interrogation_rates = {p: x / n for p, (x, n) in interrogations.items()}
    mean_influence = {p: sum(values) / len(values)
                      for p, values in influence.items()}
    check("persona_count", len(P.PERSONAS) == 5, f"{len(P.PERSONAS)} personas")
    death_spread = max(death_rates.values()) - min(death_rates.values())
    interrogation_spread = (
        max(interrogation_rates.values()) - min(interrogation_rates.values()))
    influence_spread = max(mean_influence.values()) - min(mean_influence.values())
    check("personas_differentiated",
          death_spread > 0.05 and interrogation_spread > 0.20
          and influence_spread > 1.0,
          f"death={death_spread:.1%}, interrogation={interrogation_spread:.1%}, "
          f"influence={influence_spread:.2f}")
    return win_rates, death_rates


def check_policy_isolation() -> None:
    """Policies must decide from a player's Knowledge, never from global truth."""
    import inspect
    from . import policies as P
    banned = {"game", "g", "players", "truth", "cand_factions", "state", "engine"}
    for name, fn in inspect.getmembers(P, inspect.isfunction):
        if name.startswith("_") or name == "seed_policies":
            continue
        leak = set(inspect.signature(fn).parameters) & banned
        check("policy_isolation", not leak, f"{name} receives {leak}")


class ForcedCouncilPolicies:
    """Deterministic policy used to test eligibility rules exactly."""

    from . import policies as _base
    PERSONAS = _base.PERSONAS

    def __getattr__(self, name):
        return getattr(self._base, name)

    def seed_policies(self, seed):
        self._base.seed_policies(seed)

    def expose(self, k, persona, influence, public, cfg):
        if k.seat == 0:
            target = next(seat for seat in public["living"] if seat != 0)
            return target, "BLACKMAIL"
        return None

    def interrogate(self, k, persona, influence, cost, public, cfg):
        if k.seat == 0:
            return next(seat for seat in public["living"] if seat != 0)
        return None

    def vote_guilty(self, k, persona, accused, public, cfg):
        return True


def check_published_rule_gates() -> None:
    cfg = recommended_config(8)

    # Expose requires enough Influence to cover the -2 miss.
    g = Game(8, 41, cfg, ForcedCouncilPolicies())
    g.move(0, "BANK", 3, "test_reduce_to_one")
    before = g.players[0].influence
    g.resolve_exposes()
    check("expose_gate_exact",
          before == 1 and g.expose_refusals == 1
          and g.players[0].influence == 1,
          f"before={before} refusals={g.expose_refusals} after={g.players[0].influence}")

    # A living player below 1 is absent from both the vote and denominator.
    g = Game(8, 42, cfg, ForcedCouncilPolicies())
    g.move(2, "BANK", 4, "test_reduce_to_zero")
    g.resolve_interrogations()
    event = next(e for e in g.events if e[2] == "INTERROGATION")
    total = int(str(event[5]).split(":")[0])
    check("interrogation_vote_gate_exact",
          g.players[2].vote_exclusions == 1
          and g.players[0].vote_exclusions == 1 and total == 6,
          f"seat2={g.players[2].vote_exclusions} "
          f"initiator={g.players[0].vote_exclusions} total={total}")

    # Debt is not Bankruptcy until the Final lock.
    g = Game(8, 43, cfg)
    g.move(0, "BANK", 6, "test_debt")
    check("debt_not_bankruptcy_before_final", not g.players[0].bankrupt,
          f"locked={g.players[0].bankrupt_locked}")
    g.lock_bankruptcy()
    check("bankruptcy_locked_at_final", g.players[0].bankrupt,
          f"influence={g.players[0].influence}")

    # An ally rescue clears debt through the normal transfer/accounting path.
    g = Game(8, 44, cfg)
    g.round = 3
    g.move(0, "BANK", 6, "test_debt")
    g.players[1].knowledge.feel(0, 5.0)
    g.debt_rescue_phase()
    check("debt_rescue_conservation",
          g.players[0].influence >= 0 and g.debt_rescued >= 2,
          f"debtor={g.players[0].influence} rescued={g.debt_rescued}")
    g.check_conservation()


def check_chaos_zero_equivalence() -> None:
    for n in (8, 13, 15):
        for seed in range(10):
            cfg = recommended_config(n)
            base = run_game(n, 70_000 + seed, cfg)
            wrapped = run_game(
                n, 70_000 + seed, cfg, chaos_policies(ChaosConfig.clean()))
            check("chaos_zero_equivalence",
                  base.ledger == wrapped.ledger
                  and base.events == wrapped.events
                  and base.personal_wins == wrapped.personal_wins,
                  f"n={n} seed={seed}")


def check_chaos_and_exploit_plumbing() -> None:
    cfg = recommended_config(13)
    clean = [
        run_game(13, 90_000 + i, cfg, chaos_policies(ChaosConfig.clean()))
        for i in range(80)
    ]
    realistic = [
        run_game(13, 90_000 + i, cfg, chaos_policies(ChaosConfig.realistic()))
        for i in range(80)
    ]
    check("chaos_creates_refusals",
          sum(r.gm_refusals for r in realistic) > sum(r.gm_refusals for r in clean),
          f"clean={sum(r.gm_refusals for r in clean)} "
          f"realistic={sum(r.gm_refusals for r in realistic)}")

    forbidden_debt_causes = {
        "gift", "interrogation_cost", "expose_miss",
        "guilty_vote_penalty", "reveal_votes", "final_votes",
    }
    observed = Counter()
    for result in realistic:
        observed.update(result.debt_by_cause or {})
    illegal = forbidden_debt_causes & set(observed)
    check("voluntary_actions_never_create_debt", not illegal,
          f"causes={sorted(illegal)}")

    for exploit in EXPLOITS:
        changed = 0
        for i in range(30):
            base = run_game(13, 100_000 + i, cfg)
            attacked = run_game(
                13, 100_000 + i, cfg, ExploitPolicies(exploit, (0, 1, 2)))
            changed += int(base.ledger != attacked.ledger
                           or base.personal_wins != attacked.personal_wins)
        check("exploit_strategy_reaches_engine", changed > 0,
              f"{exploit} changed no simulated game")


# --------------------------------------------------------------------------

def run_checks(counts=(8, 11, 13, 15), seeds=range(25)) -> None:
    check_config_fields_are_read()
    check_policy_isolation()
    check_no_duplicate_definitions()
    check_personas_are_distinguishable()
    check_published_rule_gates()
    check_chaos_zero_equivalence()
    check_chaos_and_exploit_plumbing()

    # Canonical parity: these values are stated in both playable rulebooks.
    for n in counts:
        cfg = recommended_config(n)
        check("canonical_guilty_reward", cfg.guilty_vote_reward == 5,
              f"n={n} reward={cfg.guilty_vote_reward}")
        check("canonical_guilty_penalty", cfg.guilty_vote_penalty == 1,
              f"n={n} penalty={cfg.guilty_vote_penalty}")
        check("canonical_candidate_count", cfg.candidate_count == 3,
              f"n={n} candidates={cfg.candidate_count}")
        check("canonical_election_mode", cfg.election_mode == "plurality",
              f"n={n} mode={cfg.election_mode}")
        check("canonical_ghost_votes", cfg.ghost_vote_mode == "all",
              f"n={n} mode={cfg.ghost_vote_mode}")
        check("canonical_vote_market", cfg.vote_purchase_mode == "flat",
              f"n={n} mode={cfg.vote_purchase_mode}")
        check("canonical_expose_gate", cfg.expose_eligibility_enabled,
              f"n={n}")
        check("canonical_vote_gate", cfg.interrogation_vote_eligibility_enabled,
              f"n={n}")
        check("canonical_bankruptcy_lock", cfg.bankruptcy_lock_at_final,
              f"n={n}")
        check("canonical_debt_rescue", cfg.debt_rescue_enabled,
              f"n={n}")

    for n in counts:
        for label, cfg in config_matrix(n).items():
            for seed in seeds:
                g = Game(n, seed, cfg)
                res = g.run()
                check_game(label, g, res, n)

    # Determinism: the same seed and config must reproduce exactly.
    for n in (10, 13, 15):
        a = run_game(n, 99, recommended_config(n))
        b = run_game(n, 99, recommended_config(n))
        check("determinism",
              a.ledger == b.ledger and a.syndicate_win == b.syndicate_win
              and a.magnate_total == b.magnate_total, f"n={n}")

    # Config plumbing: overrides must reach the victory check.
    res = run_game(13, 7, recommended_config(13, magnate_threshold=1,
                                             assassin_threshold=1))
    check("config_override", res.magnate_threshold == 1 and res.assassin_threshold == 1,
          f"{res.magnate_threshold}/{res.assassin_threshold}")

    # Variants must change engine behaviour, not merely how results are scored.
    for name, override in (("ghosts_forfeit", dict(ghosts_keep_faction_victory=False)),
                           ("reveal_first", dict(reveal_after_nomination=False)),
                           ("open_factions", dict(ally_hint="open")),
                           ("ghost_vote_lifetime", dict(ghost_vote_mode="lifetime")),
                           ("runoff", dict(election_mode="runoff")),
                           ("escalating_votes",
                            dict(vote_purchase_mode="escalating"))):
        base = [run_game(13, 8_000 + i, recommended_config(13)) for i in range(200)]
        alt = [run_game(13, 8_000 + i, recommended_config(13, **override))
               for i in range(200)]
        changed = sum(1 for x, y in zip(base, alt)
                      if x.winning_faction != y.winning_faction
                      or x.syndicate_win != y.syndicate_win
                      or x.personal_wins != y.personal_wins)
        check("variant_has_effect", changed > 0, f"{name} changed no outcome")


def main() -> int:
    run_checks()
    if FAILURES:
        unique = sorted({f.split(":")[0] for f in FAILURES})
        print(f"FAILED ({len(FAILURES)} issues across {len(unique)} checks: "
              f"{', '.join(unique)})")
        for f in FAILURES[:25]:
            print("  -", f)
        return 1
    print("ALL CHECKS PASSED across config matrix: default, recommended, reveal_first, "
          "open_factions, ghosts_forfeit, ghost_vote_lifetime, runoff, "
          "escalating_votes, minimal_systems, no_incentive, legacy_rules")
    return 0


if __name__ == "__main__":
    sys.exit(main())
