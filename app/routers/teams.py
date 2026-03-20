from fastapi import APIRouter, HTTPException
from app.data import df_players, df_teams
from app.routers.utils import as_json

router = APIRouter(prefix="/teams", tags=["teams"])

@router.get("/")
def get_all_teams():
    return as_json(df_teams["Team"].unique().tolist())

@router.get("/{team_name}")
def get_team_info(team_name: str):
    norm = team_name.lower()
    row = df_teams[df_teams["Team"].str.lower() == norm]
    if row.empty:
        raise HTTPException(status_code=404, detail=f"Team '{team_name}' not found")
    players = df_players[df_players["Team"].str.lower() == norm]["Name"].tolist()
    return {"Team": team_name.title(), "Image": row.iloc[0]["Image"], "Players": players}

@router.get("/{team_name}/images")
def get_team_images(team_name: str):
    norm = team_name.lower()
    row = df_teams[df_teams["Team"].str.lower() == norm]
    if row.empty:
        raise HTTPException(status_code=404, detail=f"Team '{team_name}' not found")
    return {"Image": row.iloc[0]["Image"]}