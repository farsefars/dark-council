"""Faction knowledge variants, measured on the corrected belief model.

Voters now act on belief rather than truth, so these numbers are honest about what a
player can actually work out at the ballot.
"""

from __future__ import annotations

import collections
import statistics

from .engine import run_game, ARISTOCRAT, REFORMER, MAGNATE, SCALING
from .final import recommended_config

COUNTS = [11, 13, 15]
GAMES = 1200


def measure(label: str, ally_hint: str = "none", **overrides) -> None:
    won = collections.Counter()
    same_faction = 0
    games = 0
    mag = []
    syn = []
    revealed_candidate = 0
    reveals = 0
    signature = None
    for n in COUNTS:
        cfg = recommended_config(n, ally_hint=ally_hint, **overrides)
        if signature is None:
            signature = (cfg.reveal_after_nomination, cfg.candidates_declare,
                         cfg.ally_hint)
        for i in range(GAMES):
            r = run_game(n, 2_300_000 + i, cfg)
            games += 1
            mag.append(r.magnate_win)
            syn.append(r.syndicate_win)
            if r.winning_faction:
                won[r.winning_faction] += 1
            cands = [int(e[3]) for e in r.events if e[2] == "CANDIDATE"]
            cf = [e[5] for e in r.events if e[2] == "CANDIDATE"]
            if len(cf) == 2 and cf[0] == cf[1]:
                same_faction += 1
            for e in r.events:
                if e[2] == "REVEAL":
                    reveals += 1
                    if int(e[3]) in cands:
                        revealed_candidate += 1
    intended = (won[ARISTOCRAT] + won[REFORMER]) / games
    seen = _SEEN.setdefault(signature, label)
    dup = "" if seen == label else f"   <-- IDENTICAL CONFIG TO '{seen}'"
    print(f"{label:<34}{won[ARISTOCRAT]/games:>8.1%}{won[REFORMER]/games:>9.1%}"
          f"{won[MAGNATE]/games:>10.1%}{intended:>11.1%}"
          f"{statistics.fmean(mag):>10.1%}{statistics.fmean(syn):>11.1%}"
          f"{revealed_candidate/max(1,reveals):>11.1%}{dup}")


_SEEN: dict = {}


def main() -> None:
    print(f"{'variant':<34}{'arist':>8}{'reform':>9}{'MAGNATE':>10}{'intended':>11}"
          f"{'mag win':>10}{'syndicate':>11}{'rev->cand':>11}")
    print("-" * 104)
    measure("status quo (Reveal first)", reveal_after_nomination=False)
    measure("REVEAL AFTER NOMINATION", reveal_after_nomination=True)
    measure("Candidates declare truthfully",
            reveal_after_nomination=False, candidates_declare=True)
    measure("reveal-after + declare",
            reveal_after_nomination=True, candidates_declare=True)
    measure("one ally hint (all factions)",
            reveal_after_nomination=False, ally_hint="all")
    measure("ally hint, large factions only",
            reveal_after_nomination=False, ally_hint="large")
    measure("open factions", reveal_after_nomination=False, ally_hint="open")
    measure("open + reveal after nomination",
            reveal_after_nomination=True, ally_hint="open")


if __name__ == "__main__":
    main()
