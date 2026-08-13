"""Derive thresholds that hit the agreed balance targets.

Thresholds only affect scoring, never behaviour, so the observed distributions of
magnate_total and assassin_total can be measured once and then inverted to find the
value that produces the desired win rate.
"""

from __future__ import annotations

import argparse
import statistics

from .engine import Config, SCALING, run_game
from .run import COUNTS, summarise, wilson

TARGET_MAGNATE = 0.35
TARGET_SYNDICATE = 0.30


def quantile_threshold(values: list[int], target_rate: float) -> int:
    """Smallest integer T with P(value >= T) closest to target_rate."""
    if not values:
        return 0
    best, best_err = 0, 9.9
    for t in range(0, max(values) + 2):
        rate = sum(1 for v in values if v >= t) / len(values)
        err = abs(rate - target_rate)
        if err < best_err:
            best, best_err = t, err
    return best


def measure(cfg: Config, games: int, seed0: int = 500_000) -> dict:
    out = {}
    for n in COUNTS:
        results = [run_game(n, seed0 + i, cfg) for i in range(games)]
        mag = [r.magnate_total for r in results]
        # assassin_total is already 0 when dead, so the joint condition is preserved.
        asn = [r.assassin_total for r in results]
        out[n] = {
            "magnate": mag,
            "assassin": asn,
            "alive_rate": statistics.fmean(1.0 if r.assassin_alive else 0.0 for r in results),
            "alive_totals": [r.assassin_total for r in results if r.assassin_alive],
        }
    return out


def recommend(cfg: Config, games: int) -> dict:
    data = measure(cfg, games)
    rec = {}
    for n in COUNTS:
        d = data[n]
        rec[n] = {
            "magnate": quantile_threshold(d["magnate"], TARGET_MAGNATE),
            "assassin": quantile_threshold(d["assassin"], TARGET_SYNDICATE),
            "alive_rate": d["alive_rate"],
            "mag_mean": statistics.fmean(d["magnate"]),
            "mag_max_feasible": max(d["magnate"]),
            "asn_mean_alive": statistics.fmean(d["alive_totals"]) if d["alive_totals"] else 0,
        }
    return rec


def verify(cfg: Config, rec: dict, games: int) -> dict:
    out = {}
    for n in COUNTS:
        c = Config(**{**cfg.__dict__,
                      "magnate_threshold": rec[n]["magnate"],
                      "assassin_threshold": rec[n]["assassin"]})
        results = [run_game(n, 900_000 + i, c) for i in range(games)]
        out[n] = summarise(results)
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--games", type=int, default=1500)
    ap.add_argument("--ghost-mode", default="once")
    ap.add_argument("--expose-once", action="store_true", default=True)
    args = ap.parse_args()

    cfg = Config(expose_once=args.expose_once, ghost_mode=args.ghost_mode)
    print(f"config: expose_once={cfg.expose_once} ghost_mode={cfg.ghost_mode} "
          f"games={args.games}/count\n")

    rec = recommend(cfg, args.games)
    print(f"{'n':>3} {'magnate now':>12} {'-> rec':>7} {'mag mean':>9} {'mag best':>9} "
          f"{'assassin now':>13} {'-> rec':>7} {'alive':>7} {'asn mean':>9}")
    for n in COUNTS:
        r = rec[n]
        print(f"{n:>3} {SCALING[n][3]:>12} {r['magnate']:>7} {r['mag_mean']:>9.1f} "
              f"{r['mag_max_feasible']:>9} {SCALING[n][4]:>13} {r['assassin']:>7} "
              f"{r['alive_rate']:>6.0%} {r['asn_mean_alive']:>9.1f}")

    print("\nverification with recommended thresholds:")
    ver = verify(cfg, rec, args.games)
    print(f"{'n':>3} {'arist':>7} {'reform':>7} {'magnate':>20} {'syndicate':>20}")
    for n in COUNTS:
        s = ver[n]
        print(f"{n:>3} {s['aristocrat']['rate']:>6.1%} {s['reformer']['rate']:>6.1%} "
              f"{s['magnate']['rate']:>7.1%} [{s['magnate']['lo']:.2f},{s['magnate']['hi']:.2f}] "
              f"{s['syndicate']['rate']:>7.1%} [{s['syndicate']['lo']:.2f},{s['syndicate']['hi']:.2f}]")

    agg_m = statistics.fmean(ver[n]["magnate"]["rate"] for n in COUNTS)
    agg_s = statistics.fmean(ver[n]["syndicate"]["rate"] for n in COUNTS)
    agg_a = statistics.fmean(ver[n]["aristocrat"]["rate"] for n in COUNTS)
    agg_r = statistics.fmean(ver[n]["reformer"]["rate"] for n in COUNTS)
    print(f"\naggregate: aristocrat {agg_a:.1%}  reformer {agg_r:.1%}  "
          f"magnate {agg_m:.1%} (target {TARGET_MAGNATE:.0%})  "
          f"syndicate {agg_s:.1%} (target {TARGET_SYNDICATE:.0%})")


if __name__ == "__main__":
    main()
