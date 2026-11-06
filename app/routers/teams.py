from fastapi import APIRouter, HTTPException

from app.data import df_players, df_teams
from app.routers.utils import clean_value, matches, unique_values

router = APIRouter(prefix="/teams", tags=["teams"])


def _team_row(team_name: str):
    row = df_teams[matches(df_teams["Team"], team_name)]
    if row.empty:
        raise HTTPException(status_code=404, detail=f"Team '{team_name}' not found")
    return row.iloc[0]


@router.get("/")
def get_all_teams():
    return {"Teams": unique_values(df_teams["Team"])}


@router.get("/{team_name}")
def get_team_info(team_name: str):
    row = _team_row(team_name)
    players = df_players[matches(df_players["Team"], team_name)]["Name"].tolist()
    return {"Team": row["Team"], "Image": clean_value(row["Image"]), "Players": players}


@router.get("/{team_name}/images")
def get_team_images(team_name: str):
    return {"Image": clean_value(_team_row(team_name)["Image"])}
