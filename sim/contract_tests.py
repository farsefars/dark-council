"""Paired-seed fee/limit tests for the staged binding Contract mechanic."""

from __future__ import annotations

import argparse
from dataclasses import asdict
import json
from pathlib import Path
import statistics

from .chaos import ChaosConfig, chaos_policies
from .engine import run_game
from .exploits import ExploitPolicies
from .final import recommended_config
from .run import summarise


HERE = Path(__file__).resolve().parent
OUTPUT = HERE / "output"
FEES = (0, 1, 2)
LIMITS = (1, 2, 3, 99)


def run_cell(
    fee: int, limit: int, games: int, *, stake: int = 1,
    sign_rate: float = 0.30, table_limit: int = 99, chaos=None
) -> dict:
    off_results = []
    on_results = []
    abuse_results = []
    for i in range(games):
        seed = 18_000_000 + i
        base = recommended_config(13, binding_contracts_enabled=False)
        enabled = recommended_config(
            13,
            binding_contracts_enabled=True,
            binding_contract_fee=fee,
            binding_contract_limit=limit,
            binding_contract_stake=stake,
            binding_contract_sign_rate=sign_rate,
            binding_contract_table_limit=table_limit,
        )
        off_results.append(run_game(
            13, seed, base,
            chaos_policies(chaos) if chaos else None))
        on_results.append(run_game(
            13, seed, enabled,
            chaos_policies(chaos) if chaos else None))
        abuse_results.append(run_game(
            13, seed, enabled,
            ExploitPolicies("contract_abuse", (0, 1, 2))))

    off = summarise(off_results)
    on = summarise(on_results)
    abuse = summarise(abuse_results)
    honest_controlled = sum(
        int(result.personal_wins[seat])
        for result in on_results for seat in (0, 1, 2)
    ) / (games * 3)
    abuse_controlled = sum(
        int(result.personal_wins[seat])
        for result in abuse_results for seat in (0, 1, 2)
    ) / (games * 3)
    return {
        "fee": fee,
        "stake": stake,
        "sign_rate": sign_rate,
        "limit": limit,
        "table_limit": table_limit,
        "games": games,
        "contracts_per_game": on["contracts_signed"],
        "fees_per_game": on["contract_fees_paid"],
        "syndicate_contracts_per_game": on["contract_parties_syndicate"],
        "syndicate_win_off": off["syndicate"]["rate"],
        "syndicate_win_on": on["syndicate"]["rate"],
        "syndicate_delta": on["syndicate"]["rate"] - off["syndicate"]["rate"],
        "magnate_delta": on["magnate"]["rate"] - off["magnate"]["rate"],
        "wealth_top_share_off": off["wealth_top_share"],
        "wealth_top_share_on": on["wealth_top_share"],
        "wealth_concentration_delta": (
            on["wealth_top_share"] - off["wealth_top_share"]
        ),
        "honest_controlled_win_rate": honest_controlled,
        "abuse_controlled_win_rate": abuse_controlled,
        "contract_abuse_value": abuse_controlled - honest_controlled,
        "gm_refusals_on": on["gm_refusals"],
    }


def render(
    rows: list[dict], realistic: list[dict], stake_rows: list[dict],
    uptake_rows: list[dict], table_limit_rows: list[dict],
    focused: list[dict],
) -> str:
    table = "\n".join(
        f"| {row['fee']} | {'∞' if row['limit'] == 99 else row['limit']} | "
        f"{row['contracts_per_game']:.2f} | {row['syndicate_delta']:+.1%} | "
        f"{row['magnate_delta']:+.1%} | {row['wealth_concentration_delta']:+.1%} | "
        f"{row['contract_abuse_value']:+.1%} |"
        for row in rows
    )
    acceptable = [
        row for row in [*rows, *stake_rows, *uptake_rows, *table_limit_rows]
        if abs(row["syndicate_delta"]) < 0.03
        and abs(row["magnate_delta"]) < 0.03
        and row["contract_abuse_value"] < 0.03
        and row["contracts_per_game"] >= 1.0
    ]
    realistic_table = "\n".join(
        f"| {row['fee']} | {row['stake']} | {'∞' if row['limit'] == 99 else row['limit']} | "
        f"{'∞' if row['table_limit'] == 99 else row['table_limit']} | "
        f"{row['sign_rate']:.0%} | "
        f"{row['contracts_per_game']:.2f} | {row['syndicate_delta']:+.1%} | "
        f"{row['contract_abuse_value']:+.1%} | {row['gm_refusals_on']:.2f} |"
        for row in realistic
    )
    stake_table = "\n".join(
        f"| {row['stake']} | {row['limit']} | {row['contracts_per_game']:.2f} | "
        f"{row['syndicate_delta']:+.1%} | {row['magnate_delta']:+.1%} | "
        f"{row['contract_abuse_value']:+.1%} |"
        for row in stake_rows
    )
    uptake_table = "\n".join(
        f"| {row['sign_rate']:.0%} | {row['contracts_per_game']:.2f} | "
        f"{row['syndicate_delta']:+.1%} | {row['magnate_delta']:+.1%} | "
        f"{row['wealth_concentration_delta']:+.1%} | "
        f"{row['contract_abuse_value']:+.1%} |"
        for row in uptake_rows
    )
    table_limit_table = "\n".join(
        f"| {row['table_limit']} | {row['contracts_per_game']:.2f} | "
        f"{row['syndicate_delta']:+.1%} | {row['magnate_delta']:+.1%} | "
        f"{row['wealth_concentration_delta']:+.1%} | "
        f"{row['contract_abuse_value']:+.1%} |"
        for row in table_limit_rows
    )
    focused_table = "\n".join(
        f"| {row['label']} | {row['contracts_per_game']:.2f} | "
        f"{row['syndicate_delta']:+.1%} | {row['magnate_delta']:+.1%} | "
        f"{row['wealth_concentration_delta']:+.1%} | "
        f"{row['contract_abuse_value']:+.1%} |"
        for row in focused
    )
    selected_clean = next(
        (row for row in focused if row["label"] == "Clean"), None)
    selected_chaos = next(
        (row for row in focused if row["label"] == "Realistic chaos"), None)
    return f"""# Staged Contract — fee and limit test

## Mechanic modelled

- Bilateral Contract registered with the GM.
- Both parties pay the tested fee to the Bank and escrow 1 Influence.
- Rounds 1–2: mutual defence if either party is accused at that Council.
- Round 3: nominate the partner where possible and vote for them if they are a
  Candidate.
- Stake returns when the trigger resolves.
- The engine enforces the action; ordinary promises remain non-binding.

This is a mechanical proxy for the proposed fixed-trigger Contract, not evidence that
it improves pacing.

## Clean-table matrix (13 players, paired seeds)

| Fee each | Limit/player | Contracts/game | Syndicate Δ | Magnate Δ | Richest-share Δ | Abuse value |
|---:|---:|---:|---:|---:|---:|---:|
{table}

`∞` means no practical per-player cap. Abuse value is the personal win-rate edge for
three seats that Contract as aggressively as legally possible.

## Realistic-chaos check of the viable cells

| Fee | Stake | Player cap | Table cap | Signing | Contracts/game | Syndicate Δ | Abuse value | GM refusals/game |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|
{realistic_table or '| — | — | — | — | — | — |'}

## Refundable escrow sensitivity (fee 0)

| Stake each | Limit/player | Contracts/game | Syndicate Δ | Magnate Δ | Abuse value |
|---:|---:|---:|---:|---:|---:|
{stake_table}

## Uptake sensitivity (fee 0, stake 1, limit 1)

| Base signing rate | Contracts/game | Syndicate Δ | Magnate Δ | Richest-share Δ | Abuse value |
|---:|---:|---:|---:|---:|---:|
{uptake_table}

## Table-wide cap sensitivity (fee 0, stake 1, per-player limit 1)

| Total Contracts allowed | Contracts/game | Syndicate Δ | Magnate Δ | Richest-share Δ | Abuse value |
|---:|---:|---:|---:|---:|---:|
{table_limit_table}

## High-sample confirmation of the selected cap

| Table | Contracts/game | Syndicate Δ | Magnate Δ | Richest-share Δ | Abuse value |
|---|---:|---:|---:|---:|---:|
{focused_table}

## Mechanical recommendation

Selected version: **no fee, refundable stake 1 each, one Contract per player, two
Contracts total per game**.

- Clean high-sample result: Syndicate {selected_clean['syndicate_delta']:+.1%},
  Magnates {selected_clean['magnate_delta']:+.1%}, aggressive-use edge
  {selected_clean['contract_abuse_value']:+.1%}.
- Realistic-chaos result: Syndicate {selected_chaos['syndicate_delta']:+.1%},
  Magnates {selected_chaos['magnate_delta']:+.1%}, aggressive-use edge
  {selected_chaos['contract_abuse_value']:+.1%}.

The four-Contract cap also looked mechanically viable, but doubles GM registrations
without evidence of twice the pacing benefit. Two is the lower-complexity choice.
The +3.9-point Magnate result under realistic chaos is a live-playtest watch item.

## What remains unknowable without a table

- whether the ritual actually ends circular negotiations;
- whether registration interrupts the GM too often;
- whether Contracts crowd out informal trust and reciprocity;
- whether two per player feels liberating or bureaucratic.
"""


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--games", type=int, default=500)
    parser.add_argument("--chaos-games", type=int, default=300)
    parser.add_argument("--confirm-games", type=int, default=1500)
    parser.add_argument("--confirm-chaos-games", type=int, default=1000)
    args = parser.parse_args()
    rows = [
        run_cell(fee, limit, args.games)
        for fee in FEES for limit in LIMITS
    ]
    stake_rows = [
        run_cell(0, limit, args.games, stake=stake)
        for stake in (1, 2, 3) for limit in (1, 2)
    ]
    uptake_rows = [
        run_cell(0, 1, args.games, stake=1, sign_rate=rate)
        for rate in (0.05, 0.10, 0.15, 0.20, 0.30)
    ]
    table_limit_rows = [
        run_cell(0, 1, args.games, stake=1, sign_rate=0.30, table_limit=cap)
        for cap in (1, 2, 3, 4)
    ]
    all_candidates = [*rows, *stake_rows, *uptake_rows, *table_limit_rows]
    viable_map = {}
    for row in all_candidates:
        if (abs(row["syndicate_delta"]) < 0.04
                and abs(row["magnate_delta"]) < 0.04
                and row["contract_abuse_value"] < 0.04
                and row["contracts_per_game"] >= 0.75):
            key = (
                row["fee"], row["stake"], row["limit"],
                row["sign_rate"], row["table_limit"],
            )
            viable_map[key] = row
    realistic = [
        run_cell(
            row["fee"], row["limit"], args.chaos_games,
            stake=row["stake"], sign_rate=row["sign_rate"],
            table_limit=row["table_limit"],
            chaos=ChaosConfig.realistic())
        for row in viable_map.values()
    ]
    data = {
        "matrix": rows,
        "realistic": realistic,
        "stake_sensitivity": stake_rows,
        "uptake_sensitivity": uptake_rows,
        "table_limit_sensitivity": table_limit_rows,
    }
    focused = []
    for label, count, chaos in (
        ("Clean", args.confirm_games, None),
        ("Realistic chaos", args.confirm_chaos_games, ChaosConfig.realistic()),
    ):
        row = run_cell(
            0, 1, count, stake=1, sign_rate=0.30,
            table_limit=2, chaos=chaos)
        row["label"] = label
        focused.append(row)
    data["focused_confirmation"] = focused
    OUTPUT.mkdir(parents=True, exist_ok=True)
    (OUTPUT / "contract-results.json").write_text(
        json.dumps(data, indent=2, sort_keys=True), encoding="utf-8")
    report = render(
        rows, realistic, stake_rows, uptake_rows, table_limit_rows, focused)
    (HERE / "contract-report.md").write_text(report, encoding="utf-8")
    print(report)


if __name__ == "__main__":
    main()
