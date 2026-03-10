from fastapi import FastAPI, HTTPException, Query
import pandas as pd
from utils import as_json
from pydantic import BaseModel

app = FastAPI(title="Inazuma Eleven VR API")

# Carreguem el CSV
df_players = pd.read_csv("players.csv")
df_teams = pd.read_csv("teams.csv")


class Player(BaseModel):
    ID: int
    Image: str
    Name: str
    Nickname: str
    Game: str
    Archetype: str
    Position: str
    Element: str
    Team: str
    Power: int
    Control: int
    Technique: int
    Pressure: int
    Physical: int
    Agility: int
    Intelligence: int
    Total: int
    Age_Group: str
    School_Year: str
    Gender: str
    Role: str

class Team(BaseModel):
    Image: str
    Team: str

# Endpoints de l'API

@app.get("/")
def home():
    return {"message": "The Inazuma Eleven VR API is running correctly"}

@app.get("/all")
def get_all():
    return as_json(df_players)

# /players endpoints
# Gets de jugadors

@app.get("/players")    
def get_all_players():
    return as_json(df_players["Name"])

@app.get("/players/{name}")
def get_player_by_name(name: str):
    nrml_name = name.title()
    player_rows = df_players[df_players["Name"] == nrml_name]
    if player_rows.empty:
        raise HTTPException(status_code=404, detail=f"Player {nrml_name} not found")
    return player_rows.to_dict(orient="records")  # devuelve una lista de diccionarios

@app.get("/players/apodo/{nickname}")
def get_player_by_nickname(nickname: str):
    nrml_nickname = nickname.title()
    player_rows = df_players[df_players["Nickname"] == nrml_nickname]
    if player_rows.empty:
        raise HTTPException(status_code=404, detail=f"Player with nickname {nrml_nickname} not found")
    return player_rows.to_dict(orient="records")

@app.get("/players/juego/{juego}")
def get_players_by_game(juego: str):
    players = df_players[df_players["Game"].str.lower() == juego.lower()]
    if players.empty:
        raise HTTPException(status_code=404, detail=f"No players found for game {juego}")
    return as_json(players)

@app.get("/players/top/{n}")
def top_players(n: int = 10):
    top = df_players.sort_values("Total", ascending=False).head(n)
    return as_json(top)

#post de jugadors

@app.post("/players")
def add_player(player: Player):
    global df_players
    
    if player.ID in df_players['ID'].values:
        raise HTTPException(status_code=400, detail="The id of the player already exists")
    
    df_players.loc[len(df_players)] = pd.Series(player.dict())
    
    return {"mensaje": "Player added correctly", "player": player.dict()}

# /teams endpoints
# gets de teams
@app.get("/teams/")
def get_all_teams():
    teams = df_teams["Team"].unique().tolist()
    return as_json(teams)


@app.get("/teams/{team_name}")
def get_team_info(team_name: str):
    # Normalizamos el nombre para hacer case-insensitive
    team_name_norm = team_name.lower()
    
    # Buscamos el equipo en df_teams
    team_row = df_teams[df_teams["Team"].str.lower() == team_name_norm]
    
    if team_row.empty:
        raise HTTPException(status_code=404, detail=f"Team '{team_name}' not found")
    
    # Obtenemos la imagen del equipo
    team_image = team_row.iloc[0]["Image"]
    
    # Obtenemos la lista de jugadores de ese equipo desde df_players
    players = df_players[df_players["Team"].str.lower() == team_name_norm.lower()]["Name"].tolist()
    
    return {
        "Team": team_name_norm.title(),
        "Image": team_image,
        "Players": players
    }

@app.get("/teams/{team_name}/images")
def get_team_images(team_name: str):
    # Normalizamos el nombre para hacer case-insensitive
    team_name_norm = team_name.lower()
    
    # Buscamos el equipo en df_teams
    team_row = df_teams[df_teams["Team"].str.lower() == team_name_norm]
    
    if team_row.empty:
        raise HTTPException(status_code=404, detail=f"Team '{team_name}' not found")
    
    # Obtenemos la imagen del equipo
    team_image = team_row.iloc[0]["Image"]
    
    return {"Image": team_image}

#post de teams

@app.post("/teams")
def add_team(team: Team):
    global df_teams
    
    if team.Team in df_teams["Team"].values:
        raise HTTPException(status_code=400, detail="The team already exists")
    
    df_teams.loc[len(df_teams)] = pd.Series(team.dict())
    
    return {"mensaje": "Team added correctly", "team": team.dict()}

# /elementos endpoints
# gets de elementos
@app.get("/elements/")    
def get_all_elements():
    elementos = df_players["Element"].unique().tolist()
    return as_json(elementos)

# /juegos endpoints
# gets de juegos
@app.get("/games/")
def get_all_games():
    juegos = df_players["Game"].unique().tolist()
    return as_json(juegos)

# /posicions endpoints
# gets de posiciones
@app.get("/positions/")
def get_all_positions():
    posicion = df_players["Position"].unique().tolist()
    return as_json(posicion)

# /Edad endpoints
# gets de posiciones
@app.get("/ages/")
def get_all_ages():
    edad = df_players["Age group"].unique().tolist()
    return as_json(edad)

# /Genero endpoints
# gets de generos
@app.get("/genders/")
def get_all_genders():
    genero = df_players["Gender"].unique().tolist()
    return as_json(genero)

@app.get("/genders/{gender}")
def get_gender_info(gender: str):
    # Normalizamos el género para hacer case-insensitive
    gender_norm = gender.lower()
    
    # Filtramos los jugadores por género
    players = df_players[df_players["Gender"].str.lower() == gender_norm]["Name"].tolist()
    
    if not players:
        raise HTTPException(status_code=404, detail=f"Gender '{gender}' not found")
    
    return {"Gender": gender_norm.title(), "Players": players}

# /Rol endpoints
# gets de roles
@app.get("/rol/")
def get_all_roles():
    rol = df_players["Rol"].unique().tolist()
    return as_json(rol)

@app.get("/rol/{role}")
def get_role_info(role: str):
    # Normalizamos el rol para hacer case-insensitive
    role_norm = role.lower()
    
    # Filtramos los jugadores por rol
    players = df_players[df_players["Rol"].str.lower() == role_norm]["Name"].tolist()
    
    if not players:
        raise HTTPException(status_code=404, detail=f"Role '{role}' not found")
    
    return {"Role": role_norm.title(), "Players": players}

# /Arquetipo endpoints
# gets de arquetipos
@app.get("/archetypes/")
def get_all_archetypes():
    arquetipo = df_players["Archetype"].unique().tolist()
    return as_json(arquetipo)

@app.get("/archetypes/{archetype}")
def get_archetype_info(archetype: str):
    # Normalizamos el arquetipo para hacer case-insensitive
    archetype_norm = archetype.lower()
    
    # Filtramos los jugadores por arquetipo
    players = df_players[df_players["Archetype"].str.lower() == archetype_norm]["Name"].tolist()
    
    if not players:
        raise HTTPException(status_code=404, detail=f"Archetype '{archetype}' not found")
    
    return {"Archetype": archetype_norm.title(), "Players": players}


# /Posicion endpoints
@app.get("/positions/{position}")
def get_position_info(position: str):
    # Normalizamos la posición para hacer case-insensitive
    position_norm = position.lower()
    
    # Filtramos los jugadores por posición
    players = df_players[df_players["Position"].str.lower() == position_norm]["Name"].tolist()
    
    if not players:
        raise HTTPException(status_code=404, detail=f"Position '{position}' not found")
    
    return {"Position": position_norm.title(), "Players": players}

# /Id endpoints
@app.get("/players/id/{player_id}")
def get_player_by_id(player_id: int):
    player_rows = df_players[df_players["ID"] == player_id]
    if player_rows.empty:
        raise HTTPException(status_code=404, detail=f"Player with id {player_id} not found")
    return player_rows.to_dict(orient="records")