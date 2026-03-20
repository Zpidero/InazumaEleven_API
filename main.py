from fastapi import FastAPI
from app.routers import players, teams, filters

app = FastAPI(title="Inazuma Eleven VR API")

app.include_router(players.router)
app.include_router(teams.router)
app.include_router(filters.router)

@app.get("/")
def home():
    return {"message": "The Inazuma Eleven VR API is running correctly"}

@app.get("/all")
def get_all():
    from app.data import df_players
    from app.routers.utils import as_json
    return as_json(df_players)