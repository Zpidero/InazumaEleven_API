from fastapi import APIRouter, HTTPException
from app.data import df_players
from app.routers.utils import as_json

router = APIRouter(prefix="/players", tags=["players"])

@router.get("")
def get_all_players():
    return as_json(df_players["Name"])

@router.get("/{name}")
def get_player_by_name(name: str):
    nrml_name = name.title()
    rows = df_players[df_players["Name"] == nrml_name]
    if rows.empty:
        raise HTTPException(status_code=404, detail=f"Player {nrml_name} not found")
    return rows.to_dict(orient="records")

@router.get("/nickname/{nickname}")
def get_player_by_nickname(nickname: str):
    nrml = nickname.title()
    rows = df_players[df_players["Nickname"] == nrml]
    if rows.empty:
        raise HTTPException(status_code=404, detail=f"Player with nickname {nrml} not found")
    return rows.to_dict(orient="records")

@router.get("/id/{player_id}")
def get_player_by_id(player_id: int):
    rows = df_players[df_players["ID"] == player_id]
    if rows.empty:
        raise HTTPException(status_code=404, detail=f"Player with id {player_id} not found")
    return rows.to_dict(orient="records")

@router.get("/id/{player_id}/archetype")
def get_player_archetype(player_id: int):
    rows = df_players[df_players["ID"] == player_id]
    if rows.empty:
        raise HTTPException(status_code=404, detail=f"Player {player_id} not found")
    return {"ID": player_id, "Archetype": rows.iloc[0]["Archetype"]}

@router.get("/id/{player_id}/position")
def get_player_position(player_id: int):
    rows = df_players[df_players["ID"] == player_id]
    if rows.empty:
        raise HTTPException(status_code=404, detail=f"Player {player_id} not found")
    return {"ID": player_id, "Position": rows.iloc[0]["Position"]}

@router.get("/id/{player_id}/element")
def get_player_element(player_id: int):
    rows = df_players[df_players["ID"] == player_id]
    if rows.empty:
        raise HTTPException(status_code=404, detail=f"Player {player_id} not found")
    return {"ID": player_id, "Element": rows.iloc[0]["Element"]}

@router.get("/id/{player_id}/team")
def get_player_team(player_id: int):
    rows = df_players[df_players["ID"] == player_id]
    if rows.empty:
        raise HTTPException(status_code=404, detail=f"Player {player_id} not found")
    return {"ID": player_id, "Team": rows.iloc[0]["Team"]}

@router.get("/id/{player_id}/game")
def get_player_game(player_id: int):
    rows = df_players[df_players["ID"] == player_id]
    if rows.empty:
        raise HTTPException(status_code=404, detail=f"Player {player_id} not found")
    return {"ID": player_id, "Game": rows.iloc[0]["Game"]}

@router.get("/id/{player_id}/nickname")
def get_player_nickname(player_id: int):
    rows = df_players[df_players["ID"] == player_id]
    if rows.empty:
        raise HTTPException(status_code=404, detail=f"Player {player_id} not found")
    return {"ID": player_id, "Nickname": rows.iloc[0]["Nickname"]}

@router.get("/id/{player_id}/name")
def get_player_name(player_id: int):
    rows = df_players[df_players["ID"] == player_id]
    if rows.empty:
        raise HTTPException(status_code=404, detail=f"Player {player_id} not found")
    return {"ID": player_id, "Name": rows.iloc[0]["Name"]}

@router.get("/id/{player_id}/image")
def get_player_image(player_id: int):
    rows = df_players[df_players["ID"] == player_id]
    if rows.empty:
        raise HTTPException(status_code=404, detail=f"Player {player_id} not found")
    return {"ID": player_id, "Image": rows.iloc[0]["Image"]}

@router.get("/id/{player_id}/age_group")
def get_player_age_group(player_id: int):
    rows = df_players[df_players["ID"] == player_id]
    if rows.empty:
        raise HTTPException(status_code=404, detail=f"Player {player_id} not found")
    return {"ID": player_id, "Age Group": rows.iloc[0]["Age group"]}

@router.get("/id/{player_id}/school_year")
def get_player_school_year(player_id: int):
    rows = df_players[df_players["ID"] == player_id]
    if rows.empty:
        raise HTTPException(status_code=404, detail=f"Player {player_id} not found")
    return {"ID": player_id, "School year": rows.iloc[0]["School year"]}

@router.get("/id/{player_id}/gender")
def get_player_gender(player_id: int):
    rows = df_players[df_players["ID"] == player_id]
    if rows.empty:
        raise HTTPException(status_code=404, detail=f"Player {player_id} not found")
    return {"ID": player_id, "Gender": rows.iloc[0]["Gender"]}

@router.get("/id/{player_id}/role")
def get_player_role(player_id: int):
    rows = df_players[df_players["ID"] == player_id]
    if rows.empty:
        raise HTTPException(status_code=404, detail=f"Player {player_id} not found")
    return {"ID": player_id, "Role": rows.iloc[0]["Role"]}

@router.get("/id/{player_id}/{stat}")
def get_player_stat_by_id(player_id: int, stat: str):
    valid_stats = ["power", "control", "technique", "pressure", "physical", "agility", "intelligence", "total"]
    if stat.lower() not in valid_stats:
        raise HTTPException(status_code=400, detail=f"Invalid stat {stat}")
    rows = df_players[df_players["ID"] == player_id]
    if rows.empty:
        raise HTTPException(status_code=404, detail=f"Player {player_id} not found")
    return {"ID": player_id, stat.title(): int(rows.iloc[0][stat.title()])}

@router.get("/{name}/{stat}")
def get_player_stat(name: str, stat: str):
    valid_stats = ["power", "control", "technique", "pressure", "physical", "agility", "intelligence", "total"]
    if stat.lower() not in valid_stats:
        raise HTTPException(status_code=400, detail=f"Invalid stat {stat}")
    rows = df_players[df_players["Name"].str.lower() == name.lower()]
    if rows.empty:
        raise HTTPException(status_code=404, detail=f"Player {name.title()} not found")
    return {"Name": name.title(), stat.title(): int(rows.iloc[0][stat.title()])}