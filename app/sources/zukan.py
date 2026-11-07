"""Scraper for the official Inazuma Eleven: Victory Road database — https://zukan.inazuma.jp/en/

  chara_list   No., name, nickname, game, gender, element, position, role, age group,
               school year, teams, description
  chara_param  image, stats (Lv50), how to obtain
  skill        special moves (hissatsu): name, categories, description, image, video
  item/emblem  team emblems
"""
import re
import time

import requests
from bs4 import BeautifulSoup

BASE = "https://zukan.inazuma.jp/en"
HEADERS = {"User-Agent": "InazumaElevenVR-API data updater (+https://github.com/Zpidero/InazumaEleven_API)"}
DELAY = 0.5

STAT_MAP = {"Kick": "Power", "Control": "Control", "Technique": "Technique", "Pressure": "Pressure",
            "Physical": "Physical", "Agility": "Agility", "Intelligence": "Intelligence"}


def _get(url: str, tries: int = 3) -> BeautifulSoup:
    for attempt in range(tries):
        try:
            r = requests.get(url, headers=HEADERS, timeout=20)
            r.raise_for_status()
            return BeautifulSoup(r.text, "html.parser")
        except Exception as e:
            if attempt == tries - 1:
                raise
            print(f"  retry {url}: {e}")
            time.sleep(2 * (attempt + 1))


def _last_page(soup: BeautifulSoup) -> int:
    pages = [int(n) for a in soup.select("a[href]") for n in re.findall(r"[?&]page=(\d+)", a["href"])]
    return max(pages) if pages else 1


def _pages(path: str):
    """Yield the soup of every page of a paginated zukan list."""
    first = _get(f"{BASE}/{path}/")
    total = _last_page(first)
    for page in range(1, total + 1):
        soup = first if page == 1 else _get(f"{BASE}/{path}/?page={page}")
        print(f"  {path} page {page}/{total}")
        yield soup
        time.sleep(DELAY)


def _text(el) -> str:
    return el.get_text(" ", strip=True) if el else ""


def _int(s):
    try:
        return int(str(s).strip())
    except (TypeError, ValueError):
        return None


# ── players ──────────────────────────────────────────────────────────────────
def scrape_character_list() -> list[dict]:
    """Every row of chara_list."""
    rows = []
    for soup in _pages("chara_list"):
        for tr in soup.select("table tr"):
            td = tr.find_all("td")
            if len(td) < 13:
                continue
            teams = [t.strip() for t in td[11].get_text("\n", strip=True).split("\n") if t.strip()]
            rows.append({
                "No": _int(td[1].get_text(strip=True)),
                "Name": td[2].get_text(" ", strip=True),
                "Nickname": td[3].get_text(" ", strip=True),
                "Game": td[4].get_text(" ", strip=True),
                "Gender": td[5].get_text(" ", strip=True),
                "Element": td[6].get_text(" ", strip=True),
                "Position": td[7].get_text(" ", strip=True),
                "Role": td[8].get_text(" ", strip=True),
                "Age group": td[9].get_text(" ", strip=True),
                "School year": td[10].get_text(" ", strip=True),
                "Teams": teams,
                "Description": td[12].get_text(" ", strip=True),
            })
    return rows


def _obtain(card) -> list[dict]:
    """'How to Obtain' → [{"method": "Player Universe", "details": ["Handora", ...]}, ...]"""
    out = []
    box = card.select_one("dl.getTxt dd.question")
    if not box:
        return out
    for dl in box.find_all("dl", recursive=False):
        method = _text(dl.find("dt"))
        details = []
        for dd in dl.find_all("dd", recursive=False):
            group = _text(dd.find("p"))
            items = [_text(li) for li in dd.select("li")]
            if group:
                details.append({"route": group, "matches": items})
            else:
                details.extend(items)
        out.append({"method": method, "details": details})
    return out


def scrape_character_params() -> list[dict]:
    """Every card of chara_param: image, Lv50 stats, how to obtain (+ identifying fields)."""
    cards = []
    for soup in _pages("chara_param"):
        for li in soup.select("li"):
            if not li.select_one(".nameBox") or not li.select_one(".detailBox"):
                continue
            img = li.select_one(".lBox img[alt]")
            fields = {}
            for dt in li.select(".param dt, .basic dt"):
                dd = dt.find_next_sibling("dd")
                if dd:
                    fields[_text(dt)] = dd
            stats = {}
            for label, col in STAT_MAP.items():
                dd = fields.get(label)
                if dd:
                    nums = re.findall(r"\d+", _text(dd).replace("Lv50", ""))
                    stats[col] = int(nums[-1]) if nums else None
            cards.append({
                "Name": _text(li.select_one(".nameBox .name")),
                "Nickname": _text(li.select_one(".nickname")),
                "Game": _text(li.select_one(".appearedWorks dd")),
                "Age group": _text(fields.get("Age Group")),
                "Image": img["src"] if img else None,
                "Viewer": ("https://zukan.inazuma.jp" + li.select_one("a.verLink")["href"]) if li.select_one("a.verLink") else None,
                "Obtain": _obtain(li),
                **stats,
            })
    return cards


# ── techniques ───────────────────────────────────────────────────────────────
def scrape_skills() -> list[dict]:
    """Every special move on /skill/."""
    skills = []
    for soup in _pages("skill"):
        for li in soup.select("li"):
            if not li.select_one(".skillLbox"):
                continue
            name = _text(li.select_one(".nameBox .name"))
            if not name or name == "???":
                continue
            buttons = li.select(".btnBox a.btnMovie")
            img = li.select_one(".skillLbox img")
            movie = li.select_one("[data-movie-url]")
            skills.append({
                "Name": name,
                "Categories": [_text(b) for b in buttons],
                "Description": _text(li.select_one(".description")),
                "Image": img["src"] if img else None,
                "Video": movie["data-movie-url"] if movie else None,
            })
    return skills


# ── team emblems ─────────────────────────────────────────────────────────────
def scrape_emblems() -> dict:
    emblems = {}
    for soup in _pages("item/emblem"):
        for li in soup.select("li"):
            img = li.select_one("img[alt]")
            if img and img.get("src", "").startswith("https://dxi4wb638ujep.cloudfront.net/1/k"):
                emblems[img["alt"].strip()] = img["src"].strip()
    return emblems


def scrape_formations() -> list[dict]:
    """Official formations: name and the 11 positions on the pitch (x/y in %, GK at the bottom)."""
    out = []
    for li in _get(f"{BASE}/soccer_formation/").select("ul.formationList > li"):
        name = _text(li.select_one("dt"))
        spots = []
        for w in li.select(".position-marker-wrapper"):
            m = re.search(r"left:\s*([\d.]+)%;\s*top:\s*([\d.]+)%", w.get("style", ""))
            if m:
                spots.append({"x": round(float(m.group(1)), 1), "y": round(float(m.group(2)), 1)})
        if name and spots:
            out.append({"Name": name, "Positions": spots})
    return out
