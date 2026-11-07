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

# keshins (GO → Victory Road) and the Victory Road players who summon each one
keshins = _read("keshins") if (DATA / "keshins.json").exists() else []
keshin_users = defaultdict(list)
for p in df_players.itertuples(index=False):
    if isinstance(p.Keshin, str) and p.Keshin:
        keshin_users[p.Keshin.casefold()].append({
            "ID": None if pd.isna(p.ID) else int(p.ID), "Name": p.Name, "Game": p.Game,
            "Position": p.Position, "Element": p.Element,
        })
keshin_by_name = {}
for k in keshins:
    for n in (k["Display name"], k["Wiki name"], k["Name"]):      # most specific last wins
        if n:
            keshin_by_name[n.casefold()] = k


def _read_optional(name: str) -> list:
    return _read(name) if (DATA / f"{name}.json").exists() else []


tactics = _read_optional("tactics")
formations = _read_optional("formations")
mixmax = _read_optional("mixmax")

# mix max aura → the Victory Road players who can mix max with it
mixmax_users = defaultdict(list)
for p in df_players.itertuples(index=False):
    for m in p.Techniques or []:
        if m["Type"] == "Mix Max":
            mixmax_users[m["Name"].casefold()].append({
                "ID": None if pd.isna(p.ID) else int(p.ID), "Name": p.Name, "Game": p.Game,
                "Level": m["Level"], "Form": m["Form"], "Awakened": m["Awakened"],
            })

items = _read_optional("items")
totems = _read_optional("totems")


def _move_users(move_type: str):
    users = defaultdict(list)
    for p in df_players.itertuples(index=False):
        for m in p.Techniques or []:
            if m["Type"] == move_type:
                users[m["Name"].casefold()].append({
                    "ID": None if pd.isna(p.ID) else int(p.ID), "Name": p.Name, "Game": p.Game,
                    "Level": m["Level"], "Form": m["Form"], "Awakened": m["Awakened"],
                })
    return users


totem_users = _move_users("Totem")
