from fastapi import APIRouter, HTTPException

from app.data import df_players, STAT_COLUMNS
from app.routers.utils import clean_value, matches, records

router = APIRouter(prefix="/players", tags=["players"])

# URL segment -> column, for /players/id/{id}/{field}
FIELDS = {
    "name": "Name", "nickname": "Nickname", "image": "Image", "game": "Game",
    "archetype": "Archetype", "position": "Position", "element": "Element", "team": "Team",
    "age_group": "Age group", "school_year": "School year", "gender": "Gender", "role": "Role",
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


@router.get("/{name}")
def get_player_by_name(name: str):
    rows = df_players[matches(df_players["Name"], name)]
    if rows.empty:
        raise HTTPException(status_code=404, detail=f"Player {name} not found")
    return records(rows)


@router.get("/{name}/{stat}")
def get_player_stat(name: str, stat: str):
    col = STATS.get(stat.lower())
    if not col:
        raise HTTPException(status_code=400, detail=f"Invalid stat {stat}")
    rows = df_players[matches(df_players["Name"], name)]
    if rows.empty:
        raise HTTPException(status_code=404, detail=f"Player {name} not found")
    return {"Name": clean_value(rows.iloc[0]["Name"]), col: clean_value(rows.iloc[0][col])}
