"""Which transitional incentive makes hunting the Assassin worth it?

The Stash is now untouchable, so the room can no longer be paid out of the hoard.
The original failure was that a table which never interrogates did just as well as one
that did, because innocents had no personal stake in the verdict. This measures each
candidate against exactly that test.
"""

from __future__ import annotations

import statistics
import types

from .engine import run_game, MAGNATE, ASSASSIN, ACCOMPLICE
from .final import recommended_config
from . import policies as P

COUNTS = [11, 13, 15]
GAMES = 900


class _Silent(types.ModuleType):
    def __getattr__(self, name):
        return getattr(P, name)


SILENT = _Silent("silent")
SILENT.interrogate = lambda *a, **k: None
SILENT.seed_policies = P.seed_policies

BASE = dict(bounty_mode="none", guilty_vote_reward=0, guilty_vote_penalty=0,
            promotion_reveals_evidence=False, promotion_threshold_bump=0)


def innocent_win_rate(results) -> float:
    """Read the engine's adjudication rather than recomputing it here."""
    return statistics.fmean(r.innocent_win_rate() for r in results)


def evaluate(label: str, **overrides) -> tuple:
    cfgs = {**BASE, **overrides}
    normal, silent = [], []
    for n in COUNTS:
        cfg = recommended_config(n, **cfgs)
        normal += [run_game(n, 2_000_000 + i, cfg) for i in range(GAMES)]
        silent += [run_game(n, 2_000_000 + i, cfg, SILENT) for i in range(GAMES)]
    a, b = innocent_win_rate(normal), innocent_win_rate(silent)
    syn_a = statistics.fmean(1.0 if r.syndicate_win else 0.0 for r in normal)
    syn_b = statistics.fmean(1.0 if r.syndicate_win else 0.0 for r in silent)
    mag = statistics.fmean(1.0 if r.magnate_win else 0.0 for r in normal)
    execs = statistics.fmean(r.executions for r in normal)
    acc = statistics.fmean(r.correct_executions for r in normal) / max(0.01, execs)
    print(f"{label:<36}{a:>8.1%}{b:>9.1%}{(a - b) * 100:>+8.1f}pp"
          f"{syn_a:>9.1%}{syn_b:>9.1%}{mag:>9.1%}{execs:>7.2f}{acc:>8.1%}")
    return label, a - b, syn_a, syn_b, mag


def main() -> None:
    print(f"{'transitional incentive':<36}{'normal':>8}{'silent':>9}{'gap':>10}"
          f"{'syn':>9}{'syn-sil':>9}{'magnate':>9}{'exec':>7}{'acc':>8}")
    print("-" * 95)
    rows = [
        evaluate("none (baseline)"),
        evaluate("A: guilty stakes +3/-1",
                 guilty_vote_reward=3, guilty_vote_penalty=1),
        evaluate("A': guilty stakes +5/-2",
                 guilty_vote_reward=5, guilty_vote_penalty=2),
        evaluate("B: lead on the successor", promotion_reveals_evidence=True),
        evaluate("A+B combined",
                 guilty_vote_reward=3, guilty_vote_penalty=1,
                 promotion_reveals_evidence=True),
        evaluate("C: bank bounty +3 all living",
                 bounty_mode="all_living", bounty_amount=3, bounty_source="bank"),
        evaluate("D: threshold +5 on promotion", promotion_threshold_bump=5),
    ]
    print()
    best = max(rows, key=lambda r: r[1])
    print(f"largest incentive gap: {best[0]} ({best[1] * 100:+.1f}pp)")


if __name__ == "__main__":
    main()
