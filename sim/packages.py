"""Coherent whole-system balance packages.

These are simulator candidates only. None is part of the published rules.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .engine import Config
from .final import recommended_config


@dataclass(frozen=True)
class BalancePackage:
    key: str
    name: str
    philosophy: str
    overrides: dict[str, Any] = field(default_factory=dict)
    magnate_thresholds: dict[int, int] = field(default_factory=dict)
    assassin_thresholds: dict[int, int] = field(default_factory=dict)

    def config_for(self, player_count: int) -> Config:
        if (
            player_count not in self.magnate_thresholds
            or player_count not in self.assassin_thresholds
        ):
            raise ValueError(
                f"package {self.key!r} is calibrated only for "
                f"{sorted(set(self.magnate_thresholds) & set(self.assassin_thresholds))}; "
                f"received {player_count}"
            )
        values = dict(self.overrides)
        if player_count in self.magnate_thresholds:
            values["magnate_threshold"] = self.magnate_thresholds[player_count]
        if player_count in self.assassin_thresholds:
            values["assassin_threshold"] = self.assassin_thresholds[player_count]
        return recommended_config(player_count, **values)


PACKAGES: dict[str, BalancePackage] = {
    "reward-compression": BalancePackage(
        key="reward-compression",
        name="A - Distributed estates and compressed rewards",
        philosophy=(
            "Fund a slightly stronger Hit by compressing existing Goal rewards, split "
            "estates between three chosen heirs, and preserve the existing Final."
        ),
        overrides={
            "bequest_mode": "three_heirs",
            "motive_reward": 4,
            "ambition_reward": 8,
            "hit_payout": 5,
            "guilty_vote_reward": 2,
            "prosecutor_reward": 2,
        },
        magnate_thresholds={10: 16, 11: 23, 12: 14, 13: 23, 14: 15, 15: 20},
        assassin_thresholds={10: 43, 11: 42, 12: 41, 13: 41, 14: 41, 15: 41},
    ),
    "leader-tribute": BalancePackage(
        key="leader-tribute",
        name="B - Distributed estates and leader tribute",
        philosophy=(
            "Preserve all rewards, but fund a stronger Hit and control table load by "
            "charging each announced Leaderboard leader 2 Influence."
        ),
        overrides={
            "bequest_mode": "three_heirs",
            "leaderboard_tribute": 2,
            "hit_payout": 5,
            "guilty_vote_reward": 2,
            "prosecutor_reward": 3,
        },
        magnate_thresholds={10: 15, 11: 22, 12: 13, 13: 22, 14: 14, 15: 20},
        assassin_thresholds={10: 41, 11: 39, 12: 40, 13: 41, 14: 42, 15: 42},
    ),
    "hybrid-hits": BalancePackage(
        key="hybrid-hits",
        name="C - Hybrid two-Hit Syndicate",
        philosophy=(
            "Keep the affordable stable Hit value, but require two successful Hits in "
            "addition to the Influence threshold; use distributed estates and leader "
            "tribute for physical control while preserving the existing Final."
        ),
        overrides={
            "bequest_mode": "three_heirs",
            "leaderboard_tribute": 2,
            "guilty_vote_reward": 2,
            "prosecutor_reward": 3,
            "syndicate_hits_required": 2,
        },
        magnate_thresholds={10: 15, 11: 21, 12: 13, 13: 21, 14: 13, 15: 21},
        assassin_thresholds={10: 35, 11: 33, 12: 34, 13: 35, 14: 36, 15: 36},
    ),
}


def get_package(key: str) -> BalancePackage:
    try:
        return PACKAGES[key]
    except KeyError as exc:
        raise ValueError(
            f"unknown package {key!r}; choose from {', '.join(PACKAGES)}"
        ) from exc
