import pandas as pd
import requests
from bs4 import BeautifulSoup
import re
import time

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
    "Viento":  "Wind",
    "Bosque":  "Forest",
    "Fuego":   "Fire",
    "Montaña": "Mountain",
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
# Archetypes come from the community sheet in Spanish
ARCHETYPE_MAP = {
    "Justicia":     "Justice",
    "Contraataque": "Counterattack",
    "Afinidad":     "Affinity",
    "Brecha":       "Breakthrough",
    "Juego Sucio":  "Rough Play",
    "Tensión":      "Tension",
    "Unknown":      "Unknown",
}
AGE_MAP = {
    "Secundaria": "Middle School",
    "Adulto":     "Adult",
}

# ── Team name mapping (players.csv name → zukan emblem name) ──
TEAM_NAME_MAP = {
    "Raimon First Squad":      "Revolutionary Raimon",
    "Baseball Club Team":      "South Cirrus Baseball Club",
    "Eastwind":                "Eastwind International",
    "Milky Way Charter":       "Milky Way",
    "Noble Insight":           "Noble Insight Institute",
    "Polestar Academy":        "Polestar",
    "Lunar Prime Academy":     "Lunar Prime",
    "Rampart Junior High":     "Rampart",
    "South Cirrus Junior High":"South Cirrus",
    "Team Sharp":              "Inazuma National",
    "Umbrella MS":             "Umbrella",
}

# ── Scrapers ──────────────────────────────────────────────────
def last_page(url: str) -> int:
    """Read the pagination of a zukan list page instead of hard-coding the page count."""
    try:
        html = requests.get(url, timeout=10).text
        pages = [int(n) for n in re.findall(r"[?&]page=(\d+)", html)]
        return max(pages) if pages else 1
    except Exception as e:
        print(f"  ⚠️  Couldn't read page count for {url}: {e}")
        return 1


def scrape_images() -> dict:
    """Returns {(name, game, age): image_url} from chara_param"""
    data = {}
    total = last_page("https://zukan.inazuma.jp/en/chara_param/")
    for page in range(1, total + 1):
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
            print(f"Image page {page}/{total} — {len(data)} found")
            time.sleep(0.5)
        except Exception as e:
            print(f"  ⚠️  Page {page} failed: {e}")
    return data


def scrape_teams() -> dict:
    """Returns {(name, game, age): team} from chara_list"""
    teams = {}
    total = last_page("https://zukan.inazuma.jp/en/chara_list/")
    for page in range(1, total + 1):
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
            print(f"Team page {page}/{total} — {len(teams)} found")
            time.sleep(0.5)
        except Exception as e:
            print(f"  ⚠️  Page {page} failed: {e}")
    return teams


def scrape_team_emblems() -> dict:
    """Returns {team_name: image_url} from zukan emblem pages"""
    emblems = {}
    total = last_page("https://zukan.inazuma.jp/en/item/emblem/")
    for page in range(1, total + 1):
        try:
            resp = requests.get(f"https://zukan.inazuma.jp/en/item/emblem/?page={page}", timeout=10)
            soup = BeautifulSoup(resp.text, "html.parser")
            for item in soup.select("li"):
                img = item.select_one("img[alt]")
                if not img or not img.get("src", "").startswith("https://dxi4wb638ujep.cloudfront.net/1/k"):
                    continue
                emblems[img["alt"].strip()] = img["src"].strip()
            print(f"Emblem page {page}/{total} — {len(emblems)} found")
            time.sleep(0.5)
        except Exception as e:
            print(f"  ⚠️  Page {page} failed: {e}")
    return emblems


# ── Build functions ───────────────────────────────────────────
def build_players_df() -> pd.DataFrame:
    print("Loading Google Sheet...")
    df = pd.read_csv(SHEET_URL, header=1)
    df = df.rename(columns=COLUMN_MAP)
    df = df[
        df["Name"].notna() &
        (df["Game"] != "???") &
        (df["Position"] != "?")
    ].reset_index(drop=True)
    df["ID"] = pd.to_numeric(df["ID"], errors="coerce").astype("Int64")
    df["Archetype"] = df["Archetype"].map(ARCHETYPE_MAP).fillna(df["Archetype"])

    df["Element"]   = df["Element"].map(ELEMENT_MAP).fillna(df["Element"])
    df["Position"]  = df["Position"].map(POSITION_MAP).fillna(df["Position"])
    df["Gender"]    = df["Gender"].map(GENDER_MAP).fillna(df["Gender"])
    df["Role"]      = df["Role"].map(ROLE_MAP).fillna(df["Role"])
    df["Age group"] = df["Age group"].map(AGE_MAP).fillna(df["Age group"])

    print("\nScraping images from chara_param...")
    images_data = scrape_images()

    print("\nScraping teams from chara_list...")
    teams_data = scrape_teams()

    images_by_name = {name: img for (name, game, age), img in images_data.items()}

    def get_team(row):
        return teams_data.get((row["Name"], row["Game"], row["Age group"]), "Unknown")

    def get_image(row):
        img = images_data.get((row["Name"], row["Game"], row["Age group"]), "")
        if not img:
            img = images_by_name.get(row["Name"], "")
        return img

    df["Team"]  = df.apply(get_team, axis=1)
    df["Image"] = df.apply(get_image, axis=1)

    col_order = [
        "ID", "Image", "Name", "Nickname", "Game", "Archetype",
        "Position", "Element", "Team", "Power", "Control", "Technique",
        "Pressure", "Physical", "Agility", "Intelligence", "Total",
        "Age group", "School year", "Gender", "Role"
    ]
    df = df[[c for c in col_order if c in df.columns]]
    print(f"\nDone — {len(df)} players ready")
    return df


def build_teams_csv(players_df: pd.DataFrame) -> pd.DataFrame:
    print("\nScraping team emblems...")
    emblems = scrape_team_emblems()

    unique_teams = players_df["Team"].dropna().unique()
    rows = []
    for team in sorted(unique_teams):
        if team == "Unknown":
            continue
        image = emblems.get(team) or emblems.get(TEAM_NAME_MAP.get(team, ""), "")
        rows.append({"Team": team, "Image": image})

    df = pd.DataFrame(rows)
    return df


def save_players_csv(df: pd.DataFrame, path: str = "data/players.csv"):
    df.to_csv(path, index=False)
    print(f"💾 Saved to {path}")