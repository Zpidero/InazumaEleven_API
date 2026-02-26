from fastapi import FastAPI, HTTPException
import pandas as pd
from utils import as_json

app = FastAPI(title="Inazuma Eleven VR API")

# Carreguem el CSV
df = pd.read_csv("app/InazumaElevenVRDataBase.csv")

@app.get("/")
def home():
    return {"message": "API funcionant"}

@app.get("/all")
def get_all():
    return as_json(df)

@app.get("/players")    
def get_all_players():
    return as_json(df["Nombre"])

@app.get("/players/{name}")
def get_player_by_name(name: str):
    nrml_name = name.title()
    player_rows = df[df["Nombre"] == nrml_name]
    if player_rows.empty:
        raise HTTPException(status_code=404, detail=f"Player {nrml_name} not found")
    return player_rows.iloc[0].to_dict()

@app.get("/elemento/")
def get_all_elements():
    return as_json(df["Elemento"].unique().tolist(), title="elementos")