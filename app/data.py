import pandas as pd

from app.scraper import ARCHETYPE_MAP

STAT_COLUMNS = ["Power", "Control", "Technique", "Pressure", "Physical", "Agility", "Intelligence", "Total"]


def _load_players(path: str = "data/players.csv") -> pd.DataFrame:
    df = pd.read_csv(path)
    # rows without a name are empty lines exported from the source sheet
    df = df[df["Name"].notna() & (df["Name"].astype(str).str.strip() != "")].copy()
    # IDs and stats are whole numbers (the CSV stores them as 1.0, 126.0 ...)
    df["ID"] = pd.to_numeric(df["ID"], errors="coerce").astype("Int64")
    df["Archetype"] = df["Archetype"].map(ARCHETYPE_MAP).fillna(df["Archetype"])   # older CSVs are still in Spanish
    for col in STAT_COLUMNS:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").astype("Int64")
    return df.reset_index(drop=True)


def _load_teams(path: str = "data/teams.csv") -> pd.DataFrame:
    df = pd.read_csv(path)
    return df[df["Team"].notna()].reset_index(drop=True)


df_players = _load_players()
df_teams = _load_teams()
