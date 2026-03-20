import pandas as pd
import requests
from bs4 import BeautifulSoup
import time
import re

# ── Google Sheet ──────────────────────────────────────────────
SHEET_URL = "https://docs.google.com/spreadsheets/d/1HW-weeq79GRnoZNcfbj7bINVaDv55WVl/export?format=csv&gid=526070056"

# ── Column mapping ────────────────────────────────────────────
COLUMN_MAP = {
    "Nº":            "ID",
    "Imagen":        "Image",
    "Nombre":        "Name",
    "Apodo":         "Nickname",
    "Juego":         "Game",
    "Arquetipo":     "Archetype",
    "Posición":      "Position",
    "Elemento":      "Element",
    "Potencia":      "Power",
    "Control":       "Control",
    "Técnica":       "Technique",
    "Presión":       "Pressure",
    "Físico":        "Physical",
    "Agilidad":      "Agility",
    "Inteligencia":  "Intelligence",
    "Total":         "Total",
    "Grupo de Edad": "Age group",
    "Año escolar":   "School year",
    "Género":        "Gender",
    "Rol":           "Role",
}

# ── Value translations ────────────────────────────────────────
ELEMENT_MAP = {
    "Viento":   "Wind",
    "Bosque":   "Forest",
    "Fuego":    "Fire",
    "Montaña":  "Mountain",
}
POSITION_MAP = {
    "Portero":        "GK",
    "Defensa":        "DF",
    "Centrocampista": "MF",
    "Delantero":      "FW",
}
GENDER_MAP = {
    "Masculino":   "Male",
    "Femenino":    "Female",
    "Desconocido": "Unknown",
    "Neutral":     "Neutral",
}
ROLE_MAP = {
    "Jugador":     "Player",
    "Coordinador": "Coordinator",
    "Entrenador":  "Coach",
    "Manager":     "Manager",
}
AGE_MAP = {
    "Secundaria": "Middle School",
    "Adulto":     "Adult",
}

# ── Zukan scraper ─────────────────────────────────────────────
def scrape_images() -> dict:
    """Returns {(name, game, age): image} from chara_param"""
    data = {}
    for page in range(1, 110):
        try:
            resp = requests.get(f"https://zukan.inazuma.jp/en/chara_param/?page={page}", timeout=10)
            soup = BeautifulSoup(resp.text, "html.parser")
            for card in soup.select("li"):
                img_tag = card.select_one("img[alt]")
                if not img_tag or not img_tag.get("src", "").startswith("https://dxi4wb638ujep.cloudfront.net/1/k"):
                    continue
                name  = img_tag["alt"].strip()
                image = img_tag["src"].strip()
                game  = ""
                age   = ""
                for dt in card.select("dt"):
                    dd = dt.find_next_sibling("dd")
                    if not dd:
                        continue
                    if "Game" in dt.text:
                        game = dd.text.strip()
                    if "Age Group" in dt.text:
                        age = dd.text.strip()
                if name and game:
                    data[(name, game, age)] = image
            print(f"  📸 Image page {page}/109 — {len(data)} found")
            time.sleep(0.5)
        except Exception as e:
            print(f"  ⚠️  Page {page} failed: {e}")
    return data


def scrape_teams() -> dict:
    """Returns {(name, game, age): team} from chara_list"""
    teams = {}
    for page in range(1, 110):
        try:
            resp = requests.get(f"https://zukan.inazuma.jp/en/chara_list/?page={page}", timeout=10)
            soup = BeautifulSoup(resp.text, "html.parser")
            for row in soup.select("table tr"):
                cols = row.find_all("td")
                if len(cols) < 12:
                    continue
                name = cols[2].text.strip()
                game = cols[4].text.strip()
                age  = cols[9].text.strip()
                br   = cols[11].find("br")
                team = str(br.previous_sibling).strip() if br and br.previous_sibling else cols[11].text.strip()
                if name and game:
                    teams[(name, game, age)] = team
            print(f"  🏟️  Team page {page}/109 — {len(teams)} found")
            time.sleep(0.5)
        except Exception as e:
            print(f"  ⚠️  Page {page} failed: {e}")
    return teams
# ── Main build function ───────────────────────────────────────
def build_players_df() -> pd.DataFrame:
    # 1. Load Google Sheet
    print("📥 Loading Google Sheet...")
    df = pd.read_csv(SHEET_URL, header=1)

    # 2. Rename columns Spanish → English
    df = df.rename(columns=COLUMN_MAP)

    # Remove players with unknown game or position
    df = df[
        (df["Game"] != "???") &
        (df["Position"] != "?")
    ].reset_index(drop=True)

    # 3. Translate values
    df["Element"]   = df["Element"].map(ELEMENT_MAP).fillna(df["Element"])
    df["Position"]  = df["Position"].map(POSITION_MAP).fillna(df["Position"])
    df["Gender"]    = df["Gender"].map(GENDER_MAP).fillna(df["Gender"])
    df["Role"]      = df["Role"].map(ROLE_MAP).fillna(df["Role"])
    df["Age group"] = df["Age group"].map(AGE_MAP).fillna(df["Age group"])

    # 4. Scrape images and teams
    print("\n📸 Scraping images from chara_param...")
    images_data = scrape_images()

    print("\n🏟️  Scraping teams from chara_list...")
    teams_data = scrape_teams()

    def get_team(row):
        return teams_data.get((row["Name"], row["Game"], row["Age group"]), "Unknown")

    images_by_name = {name: img for (name, game, age), img in images_data.items()}

    def get_image(row):
        # Try exact match first
        img = images_data.get((row["Name"], row["Game"], row["Age group"]), "")
        # Fallback to name-only if no match
        if not img:
            img = images_by_name.get(row["Name"], "")
        return img

    df["Team"]  = df.apply(get_team, axis=1)
    df["Image"] = df.apply(get_image, axis=1)

    # 5. Reorder columns
    col_order = [
        "ID", "Image", "Name", "Nickname", "Game", "Archetype",
        "Position", "Element", "Team", "Power", "Control", "Technique",
        "Pressure", "Physical", "Agility", "Intelligence", "Total",
        "Age group", "School year", "Gender", "Role"
    ]
    col_order = [c for c in col_order if c in df.columns]
    df = df[col_order]

    print(f"\n✅ Done — {len(df)} players ready")
    return df

def save_players_csv(df: pd.DataFrame, path: str = "data/players.csv"):
    df.to_csv(path, index=False)
    print(f"💾 Saved to {path}")