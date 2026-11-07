from typing import Optional

from fastapi import APIRouter, HTTPException

from app.games import GAMES, resolve

from app.data import df_players, keshin_by_name, STAT_COLUMNS
from app.routers.utils import clean_value, matches, records

router = APIRouter(prefix="/players", tags=["players"])

# URL segment -> column, for /players/id/{id}/{field}
FIELDS = {
    "name": "Name", "nickname": "Nickname", "image": "Image", "game": "Game",
    "archetype": "Archetype", "position": "Position", "element": "Element", "team": "Team",
    "age_group": "Age group", "school_year": "School year", "gender": "Gender", "role": "Role",
    "teams": "Teams", "description": "Description", "viewer": "Viewer", "obtain": "Obtain",
    "techniques": "Techniques", "keshin": "Keshin", "legendary": "Legendary",
    **{s.lower(): s for s in STAT_COLUMNS},
}
STATS = {s.lower(): s for s in STAT_COLUMNS}


def _by_id(player_id: int):
    rows = df_players[df_players["ID"] == player_id]
    if rows.empty:
        raise HTTPException(status_code=404, detail=f"Player with id {player_id} not found")
    return rows.iloc[0]


@router.get("")
def get_all_players():
    """All player names."""
    return [clean_value(v) for v in df_players["Name"].tolist()]


@router.get("/nickname/{nickname}")
def get_player_by_nickname(nickname: str):
    rows = df_players[matches(df_players["Nickname"], nickname)]
    if rows.empty:
        raise HTTPException(status_code=404, detail=f"Player with nickname {nickname} not found")
    return records(rows)


@router.get("/id/{player_id}")
def get_player_by_id(player_id: int):
    return records(df_players[df_players["ID"] == player_id]) or _by_id(player_id)


@router.get("/id/{player_id}/{field}")
def get_player_field(player_id: int, field: str):
    """A single field of a player: name, nickname, image, game, archetype, position, element,
    team, age_group, school_year, gender, role, or a stat (power, control, ... total)."""
    col = FIELDS.get(field.lower())
    if not col:
        raise HTTPException(status_code=400, detail=f"Invalid field '{field}'. Valid: {', '.join(FIELDS)}")
    row = _by_id(player_id)
    key = "Age Group" if col == "Age group" else col
    return {"ID": player_id, key: clean_value(row[col])}


def _in_game(rows, game: Optional[str]):
    if not game:
        return rows
    title = resolve(game)
    if not title:
        raise HTTPException(status_code=400, detail=f"Unknown game '{game}'. Use a code: {', '.join(GAMES)}")
    return rows[rows["Game"] == title]


@router.get("/{name}")
def get_player_by_name(name: str, game: Optional[str] = None):
    """Every version of a player (one per game). ?game=VR for one game only."""
    rows = _in_game(df_players[matches(df_players["Name"], name)], game)
    if rows.empty:
        raise HTTPException(status_code=404, detail=f"Player {name} not found")
    return records(rows)


@router.get("/{name}/techniques")
def get_player_techniques_by_name(name: str, game: Optional[str] = None):
    """Techniques a player learns in Victory Road (level / Story, form, awakened). ?game= to pick a version."""
    rows = _in_game(df_players[matches(df_players["Name"], name)], game)
    if rows.empty:
        raise HTTPException(status_code=404, detail=f"Player {name} not found")
    return [{"ID": clean_value(r["ID"]), "Name": r["Name"], "Game": r["Game"], "Game code": r["Game code"],
             "Keshin": clean_value(r["Keshin"]), "Techniques": r["Techniques"] or []}
            for _, r in rows.iterrows()]


def _keshin(name):
    return keshin_by_name.get(name.casefold()) if isinstance(name, str) and name else None


@router.get("/id/{player_id}/keshin/details")
def get_player_keshin_by_id(player_id: int):
    """The full keshin record of a player (type, element, special move, KP/attack, image)."""
    row = _by_id(player_id)
    return {"ID": player_id, "Name": row["Name"], "Keshin": _keshin(row["Keshin"])}


@router.get("/{name}/keshin")
def get_player_keshin_by_name(name: str, game: Optional[str] = None):
    """The keshin a player summons in Victory Road, with its full record. ?game= to pick a version."""
    rows = _in_game(df_players[matches(df_players["Name"], name)], game)
    if rows.empty:
        raise HTTPException(status_code=404, detail=f"Player {name} not found")
    return [{"ID": clean_value(r["ID"]), "Name": r["Name"], "Game": r["Game"], "Game code": r["Game code"],
             "Keshin": _keshin(r["Keshin"])} for _, r in rows.iterrows()]


@router.get("/{name}/{stat}")
def get_player_stat(name: str, stat: str):
    col = STATS.get(stat.lower())
    if not col:
        raise HTTPException(status_code=400, detail=f"Invalid stat {stat}")
    rows = df_players[matches(df_players["Name"], name)]
    if rows.empty:
        raise HTTPException(status_code=404, detail=f"Player {name} not found")
    return {"Name": clean_value(rows.iloc[0]["Name"]), col: clean_value(rows.iloc[0][col])}
