from typing import Optional

from fastapi import APIRouter, HTTPException

from app.data import team_versions
from app.games import GAMES, code, resolve

router = APIRouter(prefix="/teams", tags=["teams"])


def _versions(team_name: str) -> dict:
    v = team_versions.get(team_name.strip().casefold())
    if not v:
        raise HTTPException(status_code=404, detail=f"Team '{team_name}' not found")
    return v


def _game(game: str) -> str:
    title = resolve(game)
    if not title:
        raise HTTPException(status_code=400, detail=f"Unknown game '{game}'. Use a code: {', '.join(GAMES)}")
    return title


def _order(title: str) -> int:
    return list(GAMES.values()).index(title) if title in GAMES.values() else 99


@router.get("/")
def get_all_teams(game: Optional[str] = None):
    """Every team, one entry per game it appears in. ?game=VR for one game only."""
    title = _game(game) if game else None
    items = [{"Team": v["Team"], "Game": v["Game"], "Game code": v["Game code"], "Players": len(v["Players"])}
             for versions in team_versions.values() for v in versions.values()
             if title is None or v["Game"] == title]
    items.sort(key=lambda x: (x["Team"].casefold(), _order(x["Game"])))
    return {"Count": len(items), "Teams": items}


@router.get("/{team_name}")
def get_team_info(team_name: str, game: Optional[str] = None):
    """A team in every game it appears in (each version has its own players). ?game=VR for one version."""
    versions = _versions(team_name)
    if game:
        return get_team_in_game(team_name, game)
    ordered = sorted(versions.values(), key=lambda v: _order(v["Game"]))
    return {"Team": ordered[0]["Team"], "Games": [v["Game code"] for v in ordered], "Versions": ordered}


@router.get("/{team_name}/images")
def get_team_images(team_name: str):
    v = next(iter(_versions(team_name).values()))
    return {"Image": v["Image"]}


@router.get("/{team_name}/{game}")
def get_team_in_game(team_name: str, game: str):
    """One version of a team: /teams/alpine/VR, /teams/alpine/IE2 …"""
    versions = _versions(team_name)
    title = _game(game)
    if title not in versions:
        have = ", ".join(code(g) or g for g in sorted(versions, key=_order))
        raise HTTPException(status_code=404, detail=f"'{team_name}' is not in {code(title) or title}. It appears in: {have}")
    return versions[title]
