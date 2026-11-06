"""Short codes for the games, so URLs can say ?game=VR instead of the full title."""
from typing import Optional

GAMES = {
    "IE":    "Inazuma Eleven",
    "IE2":   "Inazuma Eleven 2: Firestorm / Blizzard",
    "IE3":   "Inazuma Eleven 3: Lightning Bolt / Bomb Blast / Team Ogre Attacks!",
    "GO":    "Inazuma Eleven GO: Light / Shadow",
    "CS":    "Inazuma Eleven GO Chrono Stones: Wildfire / Thunderflash",
    "GX":    "Inazuma Eleven GO Galaxy: Big Bang / Supernova",
    "ARES":  "Inazuma Eleven Ares",
    "ORION": "Inazuma Eleven Orion",
    "VR":    "Inazuma Eleven: Victory Road",
}
CODE_OF = {v: k for k, v in GAMES.items()}

ALIASES = {
    "1": "IE", "ie1": "IE", "2": "IE2", "3": "IE3", "chronostone": "CS", "chrono stones": "CS",
    "galaxy": "GX", "ares": "ARES", "orion": "ORION", "victory road": "VR", "victoryroad": "VR",
}


def resolve(game: str) -> Optional[str]:
    """'VR', 'vr', 'victory road', 'Inazuma Eleven: Victory Road', 'ares' … → full game title."""
    g = game.strip()
    if g.upper() in GAMES:
        return GAMES[g.upper()]
    if g.casefold() in ALIASES:
        return GAMES[ALIASES[g.casefold()]]
    for title in GAMES.values():
        if title.casefold() == g.casefold():
            return title
    hits = [t for t in GAMES.values() if g.casefold() in t.casefold()]
    return hits[0] if len(hits) == 1 else None


def code(title: str) -> Optional[str]:
    return CODE_OF.get(title)
