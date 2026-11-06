import json
from collections import defaultdict
from pathlib import Path

import pandas as pd

from app.games import code

STAT_COLUMNS = ["Power", "Control", "Technique", "Pressure", "Physical", "Agility", "Intelligence", "Total"]
DATA = Path(__file__).resolve().parent.parent / "data"


def _read(name: str) -> list:
    return json.loads((DATA / f"{name}.json").read_text(encoding="utf-8"))


def _load_players() -> pd.DataFrame:
    df = pd.DataFrame(_read("players"))
    df = df[df["Name"].notna() & (df["Name"].astype(str).str.strip() != "")].copy()
    df["ID"] = pd.to_numeric(df["ID"], errors="coerce").astype("Int64")
    for col in STAT_COLUMNS:
        df[col] = pd.to_numeric(df[col], errors="coerce").astype("Int64")
    df.insert(df.columns.get_loc("Game") + 1, "Game code", df["Game"].map(code))
    return df.reset_index(drop=True)


df_players = _load_players()
_team_images = {t["Team"]: t.get("Image") for t in _read("teams")}

# A team is a (team name, game) pair: Alpine in Inazuma Eleven 2 and Alpine in Victory Road are different teams.
team_versions = defaultdict(dict)          # team name (casefold) → {game title → version}
for p in df_players.itertuples(index=False):
    for t in p.Teams or []:
        v = team_versions[t.casefold()].setdefault(p.Game, {
            "Team": t, "Game": p.Game, "Game code": code(p.Game), "Image": _team_images.get(t), "Players": [],
        })
        v["Players"].append({"ID": None if pd.isna(p.ID) else int(p.ID), "Name": p.Name, "Position": p.Position, "Element": p.Element})
df_teams = pd.DataFrame([v for versions in team_versions.values() for v in versions.values()])
techniques = _read("techniques")
technique_by_name = {t["Name"].casefold(): t for t in techniques}

# technique name → players who learn it in Victory Road
learned_by = defaultdict(list)
for p in df_players.itertuples(index=False):
    for m in p.Techniques or []:
        learned_by[m["Name"].casefold()].append({
            "ID": None if pd.isna(p.ID) else int(p.ID), "Name": p.Name, "Game": p.Game,
            "Level": m["Level"], "Form": m["Form"], "Awakened": m["Awakened"],
        })
