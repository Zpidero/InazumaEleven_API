from fastapi import APIRouter, HTTPException

from app.data import df_players
from app.games import GAMES, code, resolve
from app.routers.utils import matches, unique_values

router = APIRouter(tags=["filters"])


def _list(column: str, key: str):
    return {key: unique_values(df_players[column])}


def _players_where(column: str, value: str, key: str):
    rows = df_players[matches(df_players[column], value)]
    if rows.empty:
        raise HTTPException(status_code=404, detail=f"{key} '{value}' not found")
    return {key: rows.iloc[0][column], "Players": rows["Name"].tolist()}


@router.get("/elements/")
def get_all_elements():
    return _list("Element", "Elements")


@router.get("/games/")
def get_all_games():
    """Games with their short codes (usable as ?game=VR in other endpoints)."""
    return {"Games": [{"Code": c, "Game": t} for c, t in GAMES.items()]}


@router.get("/games/{game}")
def get_game_info(game: str):
    """Players and teams of one game: /games/VR, /games/ie2 …"""
    title = resolve(game)
    if not title:
        raise HTTPException(status_code=404, detail=f"Unknown game '{game}'. Use a code: {', '.join(GAMES)}")
    rows = df_players[df_players["Game"] == title]
    teams = sorted({t for ts in rows["Teams"] for t in (ts or [])}, key=str.casefold)
    return {"Game": title, "Code": code(title), "Players": rows["Name"].tolist(), "Teams": teams}


@router.get("/positions/")
def get_all_positions():
    return _list("Position", "Positions")


@router.get("/positions/{position}")
def get_position_info(position: str):
    return _players_where("Position", position, "Position")


@router.get("/ages/")
def get_all_ages():
    return _list("Age group", "Age groups")


@router.get("/ages/{age_group}")
def get_age_group_info(age_group: str):
    return _players_where("Age group", age_group, "Age Group")


@router.get("/genders/")
def get_all_genders():
    return _list("Gender", "Genders")


@router.get("/genders/{gender}")
def get_gender_info(gender: str):
    return _players_where("Gender", gender, "Gender")


@router.get("/roles/")
def get_all_roles():
    return _list("Role", "Roles")


@router.get("/roles/{role}")
def get_role_info(role: str):
    return _players_where("Role", role, "Role")


@router.get("/archetypes/")
def get_all_archetypes():
    return _list("Archetype", "Archetypes")


@router.get("/archetypes/{archetype}")
def get_archetype_info(archetype: str):
    return _players_where("Archetype", archetype, "Archetype")
