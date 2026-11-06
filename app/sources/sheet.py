"""Optional extra data from the community spreadsheet "CalculadoraVR" (by @nimofe200, archetypes
by @King.Javii): archetype and stats at Legendary rarity. Everything else comes from the official
zukan; if the sheet is unreachable or changes shape, the update still works without it."""
import pandas as pd

SHEET_URL = "https://docs.google.com/spreadsheets/d/1HW-weeq79GRnoZNcfbj7bINVaDv55WVl/export?format=csv&gid=526070056"

COLUMN_MAP = {
    "Nº": "No", "Nombre": "Name", "Juego": "Game", "Arquetipo": "Archetype", "Grupo de Edad": "Age group",
    "Potencia": "Power", "Control": "Control", "Técnica": "Technique", "Presión": "Pressure",
    "Físico": "Physical", "Agilidad": "Agility", "Inteligencia": "Intelligence",
}
STATS = ["Power", "Control", "Technique", "Pressure", "Physical", "Agility", "Intelligence"]

ARCHETYPE_MAP = {
    "Justicia":     "Justice",
    "Contraataque": "Counterattack",
    "Afinidad":     "Affinity",
    "Brecha":       "Breakthrough",
    "Juego Sucio":  "Rough Play",
    "Tensión":      "Tension",
}


def load() -> dict:
    """Keys: ("no", number) and (name, game, age group) → {"Name", "Archetype", "Legendary": {stat: value, ..., "Total": n}}.
    The number matches zukan's official No.; the name key is only a fallback (names repeat)."""
    try:
        df = pd.read_csv(SHEET_URL, header=1).rename(columns=COLUMN_MAP)
    except Exception as e:
        print(f"  ⚠️  Sheet unavailable, continuing without archetypes / legendary stats: {e}")
        return {}
    out = {}
    for _, r in df.iterrows():
        if pd.isna(r.get("Name")):
            continue
        key = (str(r["Name"]).strip(), str(r.get("Game", "")).strip(), str(r.get("Age group", "")).strip())
        arch = r.get("Archetype")
        arch = None if pd.isna(arch) or arch in ("Unknown", "?") else ARCHETYPE_MAP.get(str(arch).strip(), str(arch).strip())
        legendary = {}
        for s in STATS:
            v = pd.to_numeric(r.get(s), errors="coerce")
            if not pd.isna(v):
                legendary[s] = int(v)
        if len(legendary) == len(STATS):
            legendary["Total"] = sum(legendary.values())
        else:
            legendary = None
        rec = {"Name": key[0], "Archetype": arch, "Legendary": legendary}
        no = pd.to_numeric(r.get("No"), errors="coerce")
        if not pd.isna(no):
            out[("no", int(no))] = rec
        out.setdefault(key, rec)          # first row wins for the fallback key
    print(f"  sheet: {len(out)} rows")
    return out
