"""Runner: headline ledgered games, high-N sweeps, and sensitivity analysis."""

from __future__ import annotations

import argparse
import csv
import math
import os
import sqlite3
import statistics
from dataclasses import replace

from .engine import Config, SCALING, run_game

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LEDGER_DIR = os.path.join(HERE, "ledgers")
DB_PATH = os.path.join(HERE, "simulation.db")

COUNTS = [15, 14, 13, 12, 11, 10]
HEADLINE_SEEDS = [1, 2, 3, 4, 5]


# --------------------------------------------------------------------------
# Persistence
# --------------------------------------------------------------------------

SCHEMA = """
DROP TABLE IF EXISTS sim_games;
DROP TABLE IF EXISTS sim_players;
DROP TABLE IF EXISTS sim_ledger;
DROP TABLE IF EXISTS sim_events;
DROP TABLE IF EXISTS sim_snapshots;
DROP TABLE IF EXISTS sim_outcomes;
CREATE TABLE sim_games (game_id TEXT PRIMARY KEY, n_players INT, seed INT, tier TEXT);
CREATE TABLE sim_players (game_id TEXT, seat INT, faction TEXT, role TEXT,
    archetype TEXT, motive TEXT, ambition TEXT, secret TEXT, final_influence INT,
    alive INT, motive_done INT, ambition_done INT);
CREATE TABLE sim_ledger (game_id TEXT, round INT, phase TEXT, src TEXT, dst TEXT,
    amount INT, reason TEXT);
CREATE TABLE sim_events (game_id TEXT, round INT, kind TEXT, subject TEXT,
    value INT, detail TEXT);
CREATE TABLE sim_snapshots (game_id TEXT, round INT, seat INT, influence INT,
    alive INT, stash INT, bank INT);
CREATE TABLE sim_outcomes (game_id TEXT, n_players INT, seed INT, tier TEXT,
    aristocrat_win INT, reformer_win INT, magnate_win INT, syndicate_win INT,
    magnate_total INT, magnate_threshold INT, assassin_total INT,
    assassin_threshold INT, assassin_alive INT, stash INT, circulating INT,
    deaths INT, executions INT, assassinations INT, interrogations INT,
    correct_executions INT, bankruptcies INT, hits_met INT,
    motives_claimed INT, ambitions_claimed INT, winning_faction TEXT);
"""


def init_db(path: str = DB_PATH) -> sqlite3.Connection:
    conn = sqlite3.connect(path)
    conn.executescript(SCHEMA)
    return conn


def persist(conn: sqlite3.Connection, res, tier: str) -> None:
    conn.execute("INSERT INTO sim_games VALUES (?,?,?,?)",
                 (res.game_id, res.n_players, res.seed, tier))
    conn.executemany("INSERT INTO sim_players VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
                     [(res.game_id, p.seat, p.faction, p.role, p.archetype, p.motive,
                       p.ambition, p.secret, p.influence, int(p.alive),
                       int(p.motive_done), int(p.ambition_done)) for p in res.players])
    conn.executemany("INSERT INTO sim_ledger VALUES (?,?,?,?,?,?,?)", res.ledger)
    conn.executemany("INSERT INTO sim_events VALUES (?,?,?,?,?,?)",
                     [(e[0], e[1], e[2], str(e[3]), int(e[4]), str(e[5])) for e in res.events])
    conn.executemany("INSERT INTO sim_snapshots VALUES (?,?,?,?,?,?,?)", res.snapshots)
    conn.execute("INSERT INTO sim_outcomes VALUES (" + ",".join("?" * 25) + ")",
                 (res.game_id, res.n_players, res.seed, tier,
                  int(res.aristocrat_win), int(res.reformer_win), int(res.magnate_win),
                  int(res.syndicate_win), res.magnate_total, res.magnate_threshold,
                  res.assassin_total, res.assassin_threshold, int(res.assassin_alive),
                  res.stash, res.circulating, res.deaths, res.executions,
                  res.assassinations, res.interrogations, res.correct_executions,
                  res.bankruptcies, res.hits_met, res.motives_claimed,
                  res.ambitions_claimed, res.winning_faction or ""))


def export_ledger(res) -> str:
    os.makedirs(LEDGER_DIR, exist_ok=True)
    path = os.path.join(LEDGER_DIR, f"{res.game_id}.csv")
    with open(path, "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["game_id", "round", "phase", "src", "dst", "amount", "reason"])
        w.writerows(res.ledger)
    return path


# --------------------------------------------------------------------------
# Statistics
# --------------------------------------------------------------------------

def wilson(k: int, n: int, z: float = 1.96) -> tuple[float, float]:
    if n == 0:
        return (0.0, 0.0)
    p = k / n
    d = 1 + z * z / n
    centre = p + z * z / (2 * n)
    spread = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return ((centre - spread) / d, (centre + spread) / d)


def summarise(results: list) -> dict:
    n = len(results)

    def rate(attr):
        k = sum(1 for r in results if getattr(r, attr))
        lo, hi = wilson(k, n)
        return {"rate": k / n, "lo": lo, "hi": hi}

    def mean(attr):
        return statistics.fmean(getattr(r, attr) for r in results)

    execs = sum(r.executions for r in results)
    execution_by_round = {
        rnd: sum((r.executions_by_round or {}).get(rnd, 0) for r in results)
        for rnd in (1, 2, 3)
    }
    correct_by_round = {
        rnd: sum((r.correct_executions_by_round or {}).get(rnd, 0) for r in results)
        for rnd in (1, 2, 3)
    }
    deaths_by_round = {
        rnd: statistics.fmean(
            (r.deaths_by_round or {}).get(rnd, 0) for r in results
        )
        for rnd in (1, 2, 3)
    }
    motives = sorted({p.motive for r in results for p in r.players})
    ambitions = sorted({p.ambition for r in results for p in r.players})
    motive_rates = {
        goal: (
            sum(1 for r in results for p in r.players if p.motive == goal and p.motive_done)
            / sum(1 for r in results for p in r.players if p.motive == goal)
        )
        for goal in motives
    }
    ambition_rates = {
        goal: (
            sum(1 for r in results for p in r.players
                if p.ambition == goal and p.ambition_done)
            / sum(1 for r in results for p in r.players if p.ambition == goal)
        )
        for goal in ambitions
    }
    return {
        "games": n,
        "aristocrat": rate("aristocrat_win"),
        "reformer": rate("reformer_win"),
        "magnate": rate("magnate_win"),
        "syndicate": rate("syndicate_win"),
        "assassin_alive": rate("assassin_alive"),
        "magnate_total": mean("magnate_total"),
        "magnate_threshold": results[0].magnate_threshold,
        "assassin_total": mean("assassin_total"),
        "assassin_threshold": results[0].assassin_threshold,
        "stash": mean("stash"),
        "circulating": mean("circulating"),
        "deaths": mean("deaths"),
        "executions": mean("executions"),
        "assassinations": mean("assassinations"),
        "interrogations": mean("interrogations"),
        "bankruptcies": mean("bankruptcies"),
        "vote_exclusions": mean("vote_exclusions"),
        "vote_exclusion_rate": (
            sum(r.vote_exclusions for r in results)
            / sum(r.eligible_vote_opportunities for r in results)
            if sum(r.eligible_vote_opportunities for r in results) else 0.0
        ),
        "repeat_vote_exclusions": mean("repeat_vote_exclusions"),
        "expose_attempts": mean("expose_attempts"),
        "expose_refusals": mean("expose_refusals"),
        "gm_refusals": mean("gm_refusals"),
        "debt_rescue_transfers": mean("debt_rescue_transfers"),
        "debt_rescued": mean("debt_rescued"),
        "hits_met": mean("hits_met"),
        "motives_claimed": mean("motives_claimed"),
        "ambitions_claimed": mean("ambitions_claimed"),
        "execution_accuracy": (sum(r.correct_executions for r in results) / execs
                               if execs else 0.0),
        "execution_accuracy_by_round": {
            rnd: (correct_by_round[rnd] / execution_by_round[rnd]
                  if execution_by_round[rnd] else 0.0)
            for rnd in (1, 2, 3)
        },
        "executions_by_round": {
            rnd: execution_by_round[rnd] / n for rnd in (1, 2, 3)
        },
        "deaths_by_round": deaths_by_round,
        "motive_completion_by_goal": motive_rates,
        "ambition_completion_by_goal": ambition_rates,
        "zero_agency_players": mean("zero_agency_players"),
        "zero_agency_rate": (
            sum(r.zero_agency_players for r in results)
            / sum(r.n_players for r in results)
        ),
        "wealth_top_share": mean("wealth_top_share"),
        "contracts_signed": mean("contracts_signed"),
        "contract_fees_paid": mean("contract_fees_paid"),
        "contract_parties_syndicate": mean("contract_parties_syndicate"),
    }


# --------------------------------------------------------------------------
# Commands
# --------------------------------------------------------------------------

def cmd_headline(args) -> None:
    from .final import recommended_config
    conn = init_db()
    rows = []
    for n in COUNTS:
        for seed in HEADLINE_SEEDS:
            res = run_game(n, seed, recommended_config(n))
            persist(conn, res, "headline")
            export_ledger(res)
            rows.append(res)
    conn.commit()
    conn.close()
    print(f"headline games: {len(rows)}  ledgers -> {LEDGER_DIR}")
    for n in COUNTS:
        subset = [r for r in rows if r.n_players == n]
        s = summarise(subset)
        print(f"  n={n:2d} mag {s['magnate_total']:5.1f}/{s['magnate_threshold']:2d}"
              f"  asn {s['assassin_total']:5.1f}/{s['assassin_threshold']:2d}"
              f"  deaths {s['deaths']:.1f}  syn_win {s['syndicate']['rate']:.0%}")


def sweep(counts, games: int, cfg: Config | None = None, seed0: int = 10_000) -> dict:
    out = {}
    for n in counts:
        results = [run_game(n, seed0 + i, cfg) for i in range(games)]
        out[n] = summarise(results)
    return out


def cmd_sweep(args) -> None:
    stats = sweep(COUNTS, args.games)
    hdr = (f"{'n':>3} {'games':>6} {'arist':>7} {'reform':>7} {'magnate':>16} "
           f"{'syndicate':>16} {'alive':>6} {'magT':>10} {'asnT':>10} {'stash':>6} "
           f"{'deaths':>6} {'exec':>5} {'acc':>5}")
    print(hdr)
    print("-" * len(hdr))
    for n in COUNTS:
        s = stats[n]
        print(f"{n:>3} {s['games']:>6} {s['aristocrat']['rate']:>6.1%} "
              f"{s['reformer']['rate']:>6.1%} "
              f"{s['magnate']['rate']:>6.1%} [{s['magnate']['lo']:.2f},{s['magnate']['hi']:.2f}] "
              f"{s['syndicate']['rate']:>6.1%} [{s['syndicate']['lo']:.2f},{s['syndicate']['hi']:.2f}] "
              f"{s['assassin_alive']['rate']:>5.0%} "
              f"{s['magnate_total']:>6.1f}/{s['magnate_threshold']:<3d} "
              f"{s['assassin_total']:>6.1f}/{s['assassin_threshold']:<3d} "
              f"{s['stash']:>6.1f} {s['deaths']:>6.1f} {s['executions']:>5.1f} "
              f"{s['execution_accuracy']:>5.0%}")


def cmd_detail(args) -> None:
    stats = sweep(COUNTS, args.games)
    print(f"{'n':>3} {'circ':>7} {'bankrupt':>9} {'hits':>10} {'motives':>8} "
          f"{'ambitions':>10} {'interrog':>9} {'assassin':>9}")
    for n in COUNTS:
        s = stats[n]
        print(f"{n:>3} {s['circulating']:>7.1f} {s['bankruptcies']:>9.2f} "
              f"{s['hits_met']:>10.2f} {s['motives_claimed']:>8.1f} "
              f"{s['ambitions_claimed']:>10.1f} {s['interrogations']:>9.2f} "
              f"{s['assassinations']:>9.2f}")


def cmd_sensitivity(args) -> None:
    games = args.games
    axes = {
        "magnate_threshold": [-12, -8, -4, 0, 4],
        "assassin_threshold": [0, 5, 10, 15, 20],
        "hit_payout": [1, 2, 3, 4, 5],
        "stipend": [1, 2, 3, 4],
        "launder_cap": [0, 1, 2, 3],
        "kill_share": [0.25, 0.4, 0.5, 0.6],
    }
    for axis, deltas in axes.items():
        print(f"\n=== {axis} ===")
        for d in deltas:
            per_count = {}
            for n in COUNTS:
                base_mag, base_asn = SCALING[n][3], SCALING[n][4]
                if axis == "magnate_threshold":
                    cfg = Config(magnate_threshold=base_mag + d)
                elif axis == "assassin_threshold":
                    cfg = Config(assassin_threshold=base_asn + d)
                else:
                    cfg = replace(Config(), **{axis: d})
                res = [run_game(n, 20_000 + i, cfg) for i in range(games)]
                per_count[n] = summarise(res)
            mag = statistics.fmean(per_count[n]["magnate"]["rate"] for n in COUNTS)
            syn = statistics.fmean(per_count[n]["syndicate"]["rate"] for n in COUNTS)
            print(f"  {axis}={d:<6} magnate {mag:>6.1%}   syndicate {syn:>6.1%}")


def cmd_bands(args) -> None:
    for band in ("pessimistic", "expected", "optimistic"):
        cfg = Config(behaviour_band=band)
        stats = sweep(COUNTS, args.games, cfg)
        mag = statistics.fmean(stats[n]["magnate"]["rate"] for n in COUNTS)
        syn = statistics.fmean(stats[n]["syndicate"]["rate"] for n in COUNTS)
        circ = statistics.fmean(stats[n]["circulating"] for n in COUNTS)
        print(f"{band:>12}: magnate {mag:>6.1%}  syndicate {syn:>6.1%}  circulating {circ:>6.1f}")


def cmd_ghost(args) -> None:
    for enabled in (True, False):
        cfg = Config(ghost_question=enabled)
        stats = sweep(COUNTS, args.games, cfg)
        syn = statistics.fmean(stats[n]["syndicate"]["rate"] for n in COUNTS)
        acc = statistics.fmean(stats[n]["execution_accuracy"] for n in COUNTS)
        alive = statistics.fmean(stats[n]["assassin_alive"]["rate"] for n in COUNTS)
        print(f"ghost_question={str(enabled):<5}: syndicate {syn:>6.1%}  "
              f"assassin_survival {alive:>6.1%}  execution_accuracy {acc:>6.1%}")


def main() -> None:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name, fn, default in (("headline", cmd_headline, 0), ("sweep", cmd_sweep, 2000),
                              ("detail", cmd_detail, 2000),
                              ("sensitivity", cmd_sensitivity, 400),
                              ("bands", cmd_bands, 800), ("ghost", cmd_ghost, 800)):
        p = sub.add_parser(name)
        p.add_argument("--games", type=int, default=default)
        p.set_defaults(func=fn)
    args = ap.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
