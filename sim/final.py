"""Final verification of the recommended ruleset across all supported player counts."""

from __future__ import annotations

import statistics

from .engine import Config, SCALING, run_game
from .run import summarise

ALL_COUNTS = [8, 9, 10, 11, 12, 13, 14, 15]
GAMES = 2000

# Recommended structure: Magnate threshold keys off the number of Magnates,
# not the number of players; the Assassin threshold is flat.
MAGNATE_BY_COUNT = {2: 16, 3: 24}
# The Assassin's reachable total falls as the table grows (more competition for the
# same Influence), so the threshold tracks player count rather than being flat.
ASSASSIN_BY_PLAYERS = {8: 46, 9: 44, 10: 42, 11: 42, 12: 40, 13: 40, 14: 41, 15: 39}
ASSASSIN_FLAT = 42

GOALS_V2 = dict(goals_v2=True, cap_goals=True, motive_deadline=2,
                espionage_full_profile=True, espionage_targets=1,
                commerce_partners=3, extortion_amount=2)

# The Stash is inherited wealth and survives execution; the room is rewarded for
# catching the Assassin through personal stakes on the verdict and a lead on whoever
# replaces them.
F7_FIX = dict(bounty_mode="none", confiscate_on_wipeout=True,
              guilty_vote_reward=5, guilty_vote_penalty=1,
              promotion_reveals_evidence=True)

# Decisions validated under the persona model.
PERSONA_FIXES = dict(candidate_count=3, tell_by_either=True, stash_withdraw_cap=2)


def recommended_config(n: int, **overrides) -> Config:
    magnates = SCALING[n][2]
    base = dict(expose_once=True, ghost_mode="private", kill_tell_scope="game",
                reveal_after_nomination=True,
                magnate_threshold=MAGNATE_BY_COUNT[magnates],
                assassin_threshold=ASSASSIN_BY_PLAYERS[n],
                binding_contracts_enabled=True,
                binding_contract_fee=0,
                binding_contract_stake=1,
                binding_contract_limit=1,
                binding_contract_table_limit=2,
                binding_contract_sign_rate=0.30,
                private_phase_minutes=(30, 45, 60),
                **GOALS_V2, **F7_FIX, **PERSONA_FIXES)
    base.update(overrides)
    return Config(**base)


def run_block(counts, games, seed0=700_000, **overrides):
    out = {}
    for n in counts:
        cfg = recommended_config(n, **overrides)
        out[n] = summarise([run_game(n, seed0 + i, cfg) for i in range(games)])
    return out


def show(title, stats, counts):
    print(f"\n=== {title} ===")
    print(f"{'n':>3} {'A/R split':>12} {'magnate':>21} {'syndicate':>21} "
          f"{'alive':>6} {'deaths':>7} {'bankrupt':>9}")
    for n in counts:
        s = stats[n]
        a, r = s["aristocrat"]["rate"], s["reformer"]["rate"]
        split = f"{a:.0%}/{r:.0%}"
        print(f"{n:>3} {split:>12} "
              f"{s['magnate']['rate']:>8.1%} [{s['magnate']['lo']:.2f},{s['magnate']['hi']:.2f}] "
              f"{s['syndicate']['rate']:>8.1%} [{s['syndicate']['lo']:.2f},{s['syndicate']['hi']:.2f}] "
              f"{s['assassin_alive']['rate']:>6.0%} {s['deaths']:>7.1f} {s['bankruptcies']:>9.2f}")
    m = statistics.fmean(stats[n]["magnate"]["rate"] for n in counts)
    sy = statistics.fmean(stats[n]["syndicate"]["rate"] for n in counts)
    ar = statistics.fmean(stats[n]["aristocrat"]["rate"] for n in counts)
    rf = statistics.fmean(stats[n]["reformer"]["rate"] for n in counts)
    print(f"    aggregate  aristocrat {ar:.1%}  reformer {rf:.1%}  "
          f"magnate {m:.1%}  syndicate {sy:.1%}")
    return m, sy


def main() -> None:
    print(f"RECOMMENDED RULESET  ({GAMES} games per player count)")
    print(f"  personas: 5 behavioural profiles, 3 of each at 15 players")
    print(f"  expose_once, ghost_mode=private, kill_tell_scope=game, goals v2,")
    print(f"  Stash untouchable + two-way, guilty stakes +5/-1, successor lead,")
    print(f"  Reveal after nomination, 3 Candidates, either member pays the tell,")
    print(f"  magnate={MAGNATE_BY_COUNT}, assassin={ASSASSIN_BY_PLAYERS}")
    stats = run_block(ALL_COUNTS, GAMES)
    show("headline balance, all supported counts", stats, ALL_COUNTS)

    print("\n=== robustness: behavioural assumptions ===")
    for band in ("pessimistic", "expected", "optimistic"):
        s = run_block(ALL_COUNTS, 700, seed0=810_000, behaviour_band=band)
        m = statistics.fmean(s[n]["magnate"]["rate"] for n in ALL_COUNTS)
        sy = statistics.fmean(s[n]["syndicate"]["rate"] for n in ALL_COUNTS)
        circ = statistics.fmean(s[n]["circulating"] for n in ALL_COUNTS)
        print(f"  {band:>12}: magnate {m:>6.1%}  syndicate {sy:>6.1%}  circulating {circ:>6.1f}")

    print("\n=== sensitivity: one axis at a time (13-15 players) ===")
    focus = [13, 14, 15]
    axes = {
        "stipend": [1, 2, 3, 4],
        "hit_payout": [1, 2, 3, 4, 5],
        "launder_cap": [0, 1, 2, 3, 4],
        "kill_share": [0.25, 0.4, 0.5, 0.6],
        "expose_penalty": [2, 3, 4, 5],
        "interrogation_base": [3, 4, 5, 6],
    }
    for axis, values in axes.items():
        line = []
        for v in values:
            s = run_block(focus, 500, seed0=820_000, **{axis: v})
            m = statistics.fmean(s[n]["magnate"]["rate"] for n in focus)
            sy = statistics.fmean(s[n]["syndicate"]["rate"] for n in focus)
            line.append(f"{v}: M{m:.0%}/S{sy:.0%}")
        print(f"  {axis:<20} " + "   ".join(line))


if __name__ == "__main__":
    main()
