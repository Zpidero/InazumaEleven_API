"""Victory Road movesets and technique data from the Inazuma Eleven Wiki (Fandom), CC BY-SA 3.0.
https://inazuma-eleven.fandom.com — data modules Module:PlayerData/<game> and Module:WazaData.

The wiki uses Japanese (romanised) names as page titles; English names are found through the
wiki's redirects (e.g. "Mark Evans" → "Endou Mamoru", "The Hand" → "God Hand" …)."""
import re
import time

import requests

from app.sources.lua import parse_module

API = "https://inazuma-eleven.fandom.com/api.php"
HEADERS = {"User-Agent": "InazumaElevenVR-API data updater (+https://github.com/Zpidero/InazumaEleven_API)"}
DELAY = 1.0

# wiki module → zukan "Game" value (the game a character comes from)
MODULE_GAME = {
    "IE": "Inazuma Eleven",
    "IE2": "Inazuma Eleven 2: Firestorm / Blizzard",
    "IE3": "Inazuma Eleven 3: Lightning Bolt / Bomb Blast / Team Ogre Attacks!",
    "GO": "Inazuma Eleven GO: Light / Shadow",
    "CS": "Inazuma Eleven GO Chrono Stones: Wildfire / Thunderflash",
    "GX": "Inazuma Eleven GO Galaxy: Big Bang / Supernova",
    "AT": "Inazuma Eleven Ares",
    "OK": "Inazuma Eleven Orion",
    "VR": "Inazuma Eleven: Victory Road",
}

# moveset key → form label
FORMS = {
    "VR": "Normal",
    "VRH": "Hero",
    "VRB": "Basara",
    "VRS": "Special",
    "VRBeta": "Beta Version",
    "VRBBS": "BB Stadium",
    "VRBBS1": "BB Stadium", "VRBBS2": "BB Stadium", "VRBBS3": "BB Stadium", "VRBBS4": "BB Stadium",
}

WAZA_TYPES = {
    "SH": "Shoot", "Shoot": "Shoot", "OF": "Dribble", "DF": "Block", "GK": "Catch",
    "SK": "Skill", "KH": "Keshin", "KA": "Keshin Armed", "KT": "Keshin Totem",
    "MM": "Mix Max", "SL": "Soul", "MC": "Macro Tactic", "AP": "Armed Power", "PS": "Passive",
}


def _api(params: dict, tries: int = 3) -> dict:
    params = {"format": "json", "formatversion": "2", **params}
    for attempt in range(tries):
        try:
            r = requests.get(API, params=params, headers=HEADERS, timeout=30)
            r.raise_for_status()
            time.sleep(DELAY)
            return r.json()
        except Exception as e:
            if attempt == tries - 1:
                raise
            print(f"  retry wiki api: {e}")
            time.sleep(3 * (attempt + 1))


def fetch_module(title: str) -> str:
    data = _api({"action": "query", "titles": title, "prop": "revisions", "rvprop": "content", "rvslots": "main"})
    page = data["query"]["pages"][0]
    return page["revisions"][0]["slots"]["main"]["content"]


def _clean_level(v):
    """1 → 1 ; '<span …>Story</span>' → 'Story' ; '-' → None"""
    if isinstance(v, (int, float)):
        return int(v)
    s = re.sub(r"<[^>]+>", "", str(v)).strip()
    m = re.fullmatch(r"Lv\.?\s*(\d+)", s)
    if m:
        return int(m.group(1))
    return None if s in ("", "-") else s


def load_players() -> list[dict]:
    """Every wiki player entry that has a Victory Road moveset."""
    out = []
    for mod, game in MODULE_GAME.items():
        print(f"  wiki Module:PlayerData/{mod}")
        data = parse_module(fetch_module(f"Module:PlayerData/{mod}"), "PLAYERS")
        for key, p in data.items():
            if not isinstance(p, dict) or not isinstance(p.get("moveset"), dict):
                continue
            moves = []
            for form_key, entries in p["moveset"].items():
                if not form_key.startswith("VR") or not isinstance(entries, list):
                    continue
                form = FORMS.get(form_key, form_key)
                for e in entries:
                    if isinstance(e, dict):
                        items, awakened = e.get("_items", []), bool(e.get("a"))
                    else:
                        items, awakened = e, False
                    if not items:
                        continue
                    moves.append({
                        "waza": items[0],
                        "level": _clean_level(items[1]) if len(items) > 1 else None,
                        "form": form,
                        "awakened": awakened,
                    })
            keshin = p.get("keshin", {}).get("VR") if isinstance(p.get("keshin"), dict) else None
            if not moves and not keshin:
                continue
            out.append({
                "key": key, "module": mod, "game": game, "page": p.get("page"),
                "element": p.get("element"), "position": p.get("position"),
                "gender": {"M": "Male", "F": "Female"}.get(p.get("gender"), p.get("gender")),
                "moves": moves,
                "keshin": keshin[0] if isinstance(keshin, list) and keshin else None,
            })
    return out


def load_techniques() -> dict:
    """WazaData key → {page, type, element, power, cost, power_basara, cost_basara}"""
    data = parse_module(fetch_module("Module:WazaData"), "WAZAS")
    out = {}
    for key, w in data.items():
        if not isinstance(w, dict):
            continue
        power = w.get("power") if isinstance(w.get("power"), dict) else {}
        cost = w.get("cost") if isinstance(w.get("cost"), dict) else {}
        out[key] = {
            "page": w.get("page"),
            "type": WAZA_TYPES.get(w.get("wType"), w.get("wType")),
            "element": w.get("element"),
            "power": power.get("VR"),
            "cost": cost.get("VR"),
            "power_basara": power.get("VRB"),
            "cost_basara": cost.get("VRB"),
            "in_vr": "VR" in power or "VR" in cost,
        }
    return out


def redirects(titles: list[str]) -> dict:
    """page title → set of titles that redirect to it (+ the title itself)."""
    names = {t: {t} for t in titles if t}
    todo = sorted(names)
    for i in range(0, len(todo), 50):
        batch = todo[i:i + 50]
        params = {"action": "query", "titles": "|".join(batch), "prop": "redirects", "rdlimit": "max", "redirects": "1"}
        while True:
            data = _api(params)
            q = data.get("query", {})
            back = {r["to"]: r["from"] for r in q.get("redirects", [])} if q.get("redirects") else {}
            for page in q.get("pages", []):
                title = page.get("title")
                target = names.setdefault(title, {title})
                for src, dst in [(k, v) for k, v in back.items() if k == title]:
                    target.add(dst)
                for r in page.get("redirects", []):
                    target.add(r["title"])
            if "continue" not in data:
                break
            params = {**params, **data["continue"]}
        print(f"  wiki redirects {min(i + 50, len(todo))}/{len(todo)}")
    return names


def load_keshins() -> dict:
    """KeshinData key → raw record (page, title, display, kType, element, hissatsu, skill, KP, attack).
    element / hissatsu / skill can be a single value or a {game: value} table."""
    data = parse_module(fetch_module("Module:KeshinData"), "KESHIN")
    return {k: v for k, v in data.items() if isinstance(v, dict) and v.get("page")}


def image_urls(files: list[str]) -> dict:
    """'Taiyou Shin Apollo icon' → direct image URL (tries .png)."""
    out = {}
    todo = sorted({f for f in files if f})
    for i in range(0, len(todo), 50):
        batch = todo[i:i + 50]
        q = _api({"action": "query", "titles": "|".join(f"File:{f}.png" for f in batch),
                  "prop": "imageinfo", "iiprop": "url"}).get("query", {})
        norm = {n["to"]: n["from"] for n in q.get("normalized", [])}
        for page in q.get("pages", []):
            info = page.get("imageinfo")
            if info:
                title = norm.get(page["title"], page["title"])
                out[title.removeprefix("File:").removesuffix(".png")] = info[0]["url"]
    return out
