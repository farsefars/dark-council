"""Generate isolated per-player briefings from a real simulated game state.

Used for Tier 2 validation: each briefing contains only what that player legitimately
knows, so LLM agents can be asked to make the pivotal Council decision under exactly
the information the rules grant them.
"""

from __future__ import annotations

import json
import os

from .engine import Game, Config, ASSASSIN, ACCOMPLICE

OUT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                       "scenarios")

RULES_BRIEF = """\
THE DARK COUNCIL - what every player knows about the rules:
- Players compete for Influence (chips) over 3 rounds, then elect a Candidate.
- Two players secretly form the Syndicate: an Assassin and an Accomplice.
- The Syndicate is ALWAYS exactly one Aristocrat and one Reformer. Magnates are
  NEVER Syndicate members. (This is public knowledge.)
- The Assassin kills once per round. To kill someone, the Assassin MUST have
  physically given that victim at least 1 Influence at some point during the game.
- When a player dies they become a Ghost. Ghosts can still talk, and can report
  everyone who has ever given them Influence.
- There are 5 pieces of Evidence about the Syndicate. EXACTLY 2 OF THEM ARE FALSE.
  A true piece may describe EITHER the Assassin OR the Accomplice.
- An Interrogation accuses someone of being the Assassin. It costs Influence, and
  if the room votes to execute an innocent person, the accuser gets nothing.
"""


def build(n_players: int, seed: int, upto_round: int = 2) -> dict:
    from .final import recommended_config
    cfg = recommended_config(n_players)
    g = Game(n_players, seed, cfg)
    victim = None
    for rnd in range(1, upto_round + 1):
        g.round = rnd
        if rnd > 1:
            g.phase = "STIPEND"
            for p in g.living():
                g.move("BANK", p.seat, cfg.stipend, "stipend")
        g.select_hit()
        if rnd == 2:
            g.auction()
        g.private_phase()
        g.phase = "COUNCIL"
        g.resolve_assassination()
        v = [e[3] for e in g.events if e[2] == "ASSASSINATED"]
        if v:
            victim = v[-1]
        if rnd < upto_round:
            g.ghost_question()
            g.resolve_exposes()
            g.resolve_interrogations()
            g.claim_goals()

    donors = g.donor_set(victim) if victim is not None else []

    briefings = {}
    for p in g.players:
        if not p.alive:
            continue
        k = p.knowledge
        lines = [RULES_BRIEF, f"YOU ARE PLAYER {p.seat}.", ""]
        lines.append("YOUR PRIVATE INFORMATION")
        lines.append(f"- Your Faction: {p.faction}")
        lines.append(f"- Your Role: {p.role}")
        if p.role in (ASSASSIN, ACCOMPLICE):
            lines.append(f"- Your Syndicate partner is Player {k.partner}.")
        lines.append(f"- Your Motive: {p.motive}   Your Ambition: {p.ambition}")
        lines.append(f"- Your Secret: {p.secret}")
        lines.append(f"- Player {k.known_outsider} is NOT in your Faction.")
        if k.evidence:
            for e in k.evidence:
                kind, _, val = e.partition(":")
                lines.append(f"- EVIDENCE you hold: \"A Syndicate member's "
                             f"{kind.replace('_',' ').title()} is {val}.\" "
                             f"(may be one of the 2 false pieces)")
        for s, sec in k.known_secrets.items():
            lines.append(f"- You know Player {s}'s Secret is {sec} (this is reliable).")
        lines.append("")
        lines.append("WHAT HAPPENED THIS ROUND (public)")
        lines.append(f"- Living players: {[q.seat for q in g.players if q.alive]}")
        lines.append(f"- Player {victim} was ASSASSINATED at the start of this Council.")
        lines.append(f"- Player {victim}'s Ghost reports that these players have given "
                     f"them Influence at some point in the game: {donors}")
        lines.append(f"  (The Assassin MUST be among them, because a kill requires "
                     f"having paid the victim at least 1 Influence.)")
        lines.append(f"- Current Influence you hold: {p.influence}")
        lines.append("")
        lines.append("YOUR DECISION")
        lines.append("Reply with STRICT JSON only, no other text:")
        lines.append('{"suspect": <player number you most suspect of being the Assassin>, '
                     '"confidence": <0.0-1.0>, '
                     '"interrogate": <true|false, whether you would pay to accuse them now>, '
                     '"reasoning": "<one short sentence>"}')
        briefings[p.seat] = "\n".join(lines)

    truth = {
        "game_id": g.game_id,
        "n_players": n_players,
        "seed": seed,
        "current_assassin": g.assassin_seat,
        "original_assassin": g.original_assassin,
        "accomplice": g.accomplice_seat,
        "promoted": g.assassin_seat != g.original_assassin,
        "victim": victim,
        "donors": donors,
        "living": [q.seat for q in g.players if q.alive],
        "factions": {p.seat: p.faction for p in g.players},
    }
    return {"briefings": briefings, "truth": truth}


def main() -> None:
    os.makedirs(OUT_DIR, exist_ok=True)
    briefing_dir = os.path.join(OUT_DIR, "briefings")
    os.makedirs(briefing_dir, exist_ok=True)
    for i, seed in enumerate((4242, 8888, 13131), start=1):
        data = build(8, seed)
        with open(os.path.join(OUT_DIR, f"scenario{i}.json"), "w", encoding="utf-8") as fh:
            json.dump(data, fh, indent=1)
        for seat, text in data["briefings"].items():
            with open(os.path.join(briefing_dir, f"s{i}_p{seat}.txt"), "w",
                      encoding="utf-8") as fh:
                fh.write(text)
        t = data["truth"]
        print(f"scenario{i}: seed={seed} victim={t['victim']} donors={t['donors']} "
              f"assassin={t['current_assassin']} accomplice={t['accomplice']} "
              f"promoted={t['promoted']} unique_id={'YES' if len(t['donors']) == 1 else 'no'}")


if __name__ == "__main__":
    main()
