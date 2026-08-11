"""Persona analysis: is the game fair across play styles?

Five personas, three of each at a 15-player table. The question is not only who wins,
but whether every play style has something it is good at -- and whether silence is
rewarded, which would mean the game pays you not to play.
"""

from __future__ import annotations

import collections
import statistics

from .engine import run_game, ASSASSIN, ACCOMPLICE, MAGNATE
from .final import recommended_config
from .policies import PERSONAS

GAMES = 2500


def measure(games: int = GAMES, n: int = 15, **overrides) -> dict:
    win = collections.Counter(); seen = collections.Counter()
    death = collections.Counter(); executed = collections.Counter()
    wrongly = collections.Counter(); assassinated = collections.Counter()
    caught = collections.Counter(); prosecuted = collections.Counter()
    infl = collections.defaultdict(list)
    syn_win = collections.Counter(); syn_seen = collections.Counter()
    goals = collections.Counter()

    for i in range(games):
        r = run_game(n, 3_500_000 + i, recommended_config(n, **overrides))
        syn_seats = {p.seat for p in r.players if p.role in (ASSASSIN, ACCOMPLICE)}
        for p in r.players:
            a = p.archetype
            seen[a] += 1
            win[a] += r.personal_wins[p.seat]
            infl[a].append(max(0, p.influence))
            goals[a] += int(p.motive_done) + int(p.ambition_done)
            if not p.alive:
                death[a] += 1
            if p.seat in syn_seats:
                syn_seen[a] += 1
                syn_win[a] += r.syndicate_win
        for e in r.events:
            if e[2] == "EXECUTED":
                seat = int(e[3]); a = r.players[seat].archetype
                executed[a] += 1
                if seat not in syn_seats:
                    wrongly[a] += 1
            elif e[2] == "ASSASSINATED":
                assassinated[r.players[int(e[3])].archetype] += 1
            elif e[2] == "INTERROGATION":
                pass
        # who successfully prosecuted the Assassin
        for p in r.players:
            if p.initiated_interrogation:
                prosecuted[p.archetype] += 1
        if r.correct_executions:
            for p in r.players:
                if p.reputation >= 2.0:
                    caught[p.archetype] += 1

    return dict(win=win, seen=seen, death=death, executed=executed, wrongly=wrongly,
                assassinated=assassinated, infl=infl, syn_win=syn_win,
                syn_seen=syn_seen, goals=goals, caught=caught,
                prosecuted=prosecuted, games=games)


def report(d: dict, title: str) -> None:
    seen = d["seen"]
    print(f"\n=== {title} ({d['games']} games, 15 players, 3 of each) ===")
    print(f"{'persona':<12}{'win':>8}{'death':>8}{'killed':>8}{'executed':>10}"
          f"{'lynched':>9}{'influence':>11}{'goals':>7}{'as SYN':>8}")
    for p in PERSONAS:
        n = seen[p]
        print(f"{p:<12}{d['win'][p]/n:>8.1%}{d['death'][p]/n:>8.1%}"
              f"{d['assassinated'][p]/n:>8.1%}{d['executed'][p]/n:>10.1%}"
              f"{d['wrongly'][p]/n:>9.1%}{statistics.fmean(d['infl'][p]):>11.1f}"
              f"{d['goals'][p]/n:>7.2f}"
              f"{(d['syn_win'][p]/d['syn_seen'][p] if d['syn_seen'][p] else 0):>8.1%}")
    wr = {p: d['win'][p]/seen[p] for p in PERSONAS}
    dr = {p: d['death'][p]/seen[p] for p in PERSONAS}
    mean = statistics.fmean(wr.values())
    print(f"\n  win spread   {(max(wr.values())-min(wr.values()))*100:>5.1f}pp   "
          f"best {max(wr, key=wr.get)}  worst {min(wr, key=wr.get)}")
    print(f"  death spread {(max(dr.values())-min(dr.values()))*100:>5.1f}pp")
    outliers = [p for p in PERSONAS if abs(wr[p]-mean) > 0.08]
    print(f"  outside +/-8pp of mean: {outliers or 'none'}")


def main() -> None:
    report(measure(), "current ruleset")


if __name__ == "__main__":
    main()
