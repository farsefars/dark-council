"""Human-error policy wrapper with randomness isolated from the game deal."""

from __future__ import annotations

from dataclasses import dataclass
import random

from . import policies
from .engine import SECRETS


@dataclass(frozen=True)
class ChaosConfig:
    misremember_rate: float = 0.0
    irrational_rate: float = 0.0
    forget_rate: float = 0.0
    tilt_rate: float = 0.0

    @classmethod
    def clean(cls) -> "ChaosConfig":
        return cls()

    @classmethod
    def realistic(cls) -> "ChaosConfig":
        return cls(0.12, 0.12, 0.12, 0.12)

    @classmethod
    def messy(cls) -> "ChaosConfig":
        return cls(0.30, 0.30, 0.30, 0.30)


PERSONA_MODIFIERS = {
    "POLITICIAN": dict(misremember=0.9, irrational=0.8, forget=0.8, tilt=1.1),
    "DETECTIVE": dict(misremember=0.45, irrational=0.6, forget=0.6, tilt=0.8),
    "MERCHANT": dict(misremember=0.7, irrational=0.5, forget=0.7, tilt=0.7),
    "WALLFLOWER": dict(misremember=1.0, irrational=0.8, forget=1.6, tilt=0.7),
    "FIREBRAND": dict(misremember=1.2, irrational=1.4, forget=0.7, tilt=1.8),
}


class ChaosPolicies:
    """Delegates normal choices, perturbing only selected decisions."""

    PERSONAS = policies.PERSONAS

    def __init__(self, chaos: ChaosConfig):
        self.chaos = chaos
        self.rng = random.Random(0)

    def __getattr__(self, name):
        return getattr(policies, name)

    def seed_policies(self, seed: int) -> None:
        policies.seed_policies(seed)
        self.rng.seed(seed ^ 0xC0A05)

    def _hits(self, channel: str, persona: str) -> bool:
        base = getattr(self.chaos, f"{channel}_rate")
        modifier = PERSONA_MODIFIERS.get(persona, {}).get(channel, 1.0)
        return self.rng.random() < min(1.0, base * modifier)

    def expose(self, k, persona, influence, public, cfg):
        if self._hits("forget", persona):
            return None
        if (influence < cfg.expose_fail
                and self._hits("misremember", persona)):
            pool = [seat for seat in public["living"] if seat != k.seat]
            return ((self.rng.choice(pool), self.rng.choice(SECRETS))
                    if pool else None)
        normal = policies.expose(k, persona, influence, public, cfg)
        if (normal is None and influence >= cfg.expose_fail
                and self._hits("irrational", persona)):
            pool = [seat for seat in public["living"] if seat != k.seat]
            return ((self.rng.choice(pool), self.rng.choice(SECRETS))
                    if pool else None)
        return normal

    def interrogate(self, k, persona, influence, cost, public, cfg):
        if self._hits("forget", persona):
            return None
        normal = policies.interrogate(k, persona, influence, cost, public, cfg)
        if (normal is None and influence >= cost
                and self._hits("irrational", persona)):
            pool = [seat for seat in public["living"] if seat != k.seat]
            return self.rng.choice(pool) if pool else None
        return normal

    def vote_guilty(self, k, persona, accused, public, cfg):
        normal = policies.vote_guilty(k, persona, accused, public, cfg)
        if self._hits("irrational", persona):
            return not normal
        if accused in k.accused_me and self._hits("tilt", persona):
            return True
        return normal

    def would_attempt_ineligible_vote(self, k, persona, accused, public, cfg):
        return self._hits("misremember", persona)

    def transfers(self, k, persona, influence, targets, public, cfg):
        if self._hits("forget", persona):
            return []
        return policies.transfers(k, persona, influence, targets, public, cfg)

    def debt_rescues(self, k, persona, influence, debtors, public, cfg):
        if self._hits("forget", persona):
            return []
        return policies.debt_rescues(k, persona, influence, debtors, public, cfg)

def chaos_policies(config: ChaosConfig) -> ChaosPolicies:
    return ChaosPolicies(config)
