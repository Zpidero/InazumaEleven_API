from fastapi import APIRouter, HTTPException
from app.data import df_players
from app.routers.utils import as_json

router = APIRouter(tags=["filters"])

@router.get("/elements/")
def get_all_elements():
    return as_json(df_players["Element"].unique().tolist())

@router.get("/games/")
def get_all_games():
    return as_json(df_players["Game"].unique().tolist())

@router.get("/positions/")
def get_all_positions():
    return as_json(df_players["Position"].unique().tolist())

@router.get("/positions/{position}")
def get_position_info(position: str):
    players = df_players[df_players["Position"].str.lower() == position.lower()]["Name"].tolist()
    if not players:
        raise HTTPException(status_code=404, detail=f"Position '{position}' not found")
    return {"Position": position.title(), "Players": players}

@router.get("/ages/")
def get_all_ages():
    return as_json(df_players["Age group"].unique().tolist())

@router.get("/ages/{age_group}")
def get_age_group_info(age_group: str):
    players = df_players[df_players["Age group"].str.lower() == age_group.lower()]["Name"].tolist()
    if not players:
        raise HTTPException(status_code=404, detail=f"Age group '{age_group}' not found")
    return {"Age Group": age_group.title(), "Players": players}

@router.get("/genders/")
def get_all_genders():
    return as_json(df_players["Gender"].unique().tolist())

@router.get("/genders/{gender}")
def get_gender_info(gender: str):
    players = df_players[df_players["Gender"].str.lower() == gender.lower()]["Name"].tolist()
    if not players:
        raise HTTPException(status_code=404, detail=f"Gender '{gender}' not found")
    return {"Gender": gender.title(), "Players": players}

@router.get("/roles/")
def get_all_roles():
    return as_json(df_players["Role"].unique().tolist())

@router.get("/roles/{role}")
def get_role_info(role: str):
    players = df_players[df_players["Role"].str.lower() == role.lower()]["Name"].tolist()
    if not players:
        raise HTTPException(status_code=404, detail=f"Role '{role}' not found")
    return {"Role": role.title(), "Players": players}

@router.get("/archetypes/")
def get_all_archetypes():
    return as_json(df_players["Archetype"].unique().tolist())

@router.get("/archetypes/{archetype}")
def get_archetype_info(archetype: str):
    players = df_players[df_players["Archetype"].str.lower() == archetype.lower()]["Name"].tolist()
    if not players:
        raise HTTPException(status_code=404, detail=f"Archetype '{archetype}' not found")
    return {"Archetype": archetype.title(), "Players": players}