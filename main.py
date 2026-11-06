from fastapi import FastAPI
from app.routers import players, teams, filters, techniques

app = FastAPI(
    title="Inazuma Eleven VR API",
    description="Players, teams and special moves (hissatsu) of Inazuma Eleven: Victory Road. "
                "Data: zukan.inazuma.jp (official), the Inazuma Eleven Wiki (CC BY-SA) and the CalculadoraVR sheet.",
)

app.include_router(players.router)
app.include_router(teams.router)
app.include_router(filters.router)
app.include_router(techniques.router)

@app.get("/")
def home():
    return {"message": "The Inazuma Eleven VR API is running correctly"}

@app.get("/all")
def get_all():
    from app.data import df_players
    from app.routers.utils import as_json
    return as_json(df_players)