from fastapi import FastAPI
from app.routers import players, teams, filters, techniques, keshins, tactics, mixmax

app = FastAPI(
    title="Inazuma Eleven VR API",
    description="Players, teams and special moves (hissatsu) of Inazuma Eleven: Victory Road. "
                "Data: zukan.inazuma.jp (official), the Inazuma Eleven Wiki (CC BY-SA) and the CalculadoraVR sheet.",
)

app.include_router(mixmax.router)          # before players: /players/{name}/mixmax
app.include_router(players.router)
app.include_router(teams.router)
app.include_router(filters.router)
app.include_router(techniques.router)
app.include_router(keshins.router)
app.include_router(tactics.router)

@app.get("/")
def home():
    return {"message": "The Inazuma Eleven VR API is running correctly"}

@app.get("/all")
def get_all():
    from app.data import df_players
    from app.routers.utils import as_json
    return as_json(df_players)