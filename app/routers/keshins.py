from typing import Optional

from fastapi import APIRouter, HTTPException

from app.data import keshin_by_name, keshin_users, keshins
from app.games import GAMES, code, resolve
from app.routers.techniques import TYPE_ALIASES

router = APIRouter(prefix="/keshins", tags=["keshins"])


def _eq(a, b) -> bool:
    return a is not None and str(a).casefold() == str(b).strip().casefold()


def _values(v) -> list:
    return list(v.values()) if isinstance(v, dict) else [v]


def _with_users(k: dict) -> dict:
    users = keshin_users.get(k["Name"].casefold(), [])
    return {**k, "In Victory Road": bool(users), "Users": users}


def _game_code(game: str) -> str:
    title = resolve(game)
    c = code(title) if title else None
    if c not in ("GO", "CS", "GX", "VR"):
        raise HTTPException(status_code=400, detail=f"Keshins exist in GO, CS, GX and VR, not '{game}'")
    return c


def _filter(type: Optional[str] = None, element: Optional[str] = None, game: Optional[str] = None):
    g = _game_code(game) if game else None
    out = []
    for k in keshins:
        if type and not _eq(k["Type"], TYPE_ALIASES.get(type.strip().casefold(), type)):
            continue
        if element and not any(_eq(e, element) for e in _values(k["Element"])):
            continue
        if g == "VR" and not keshin_users.get(k["Name"].casefold()):
            continue
        if g and g != "VR" and not any(isinstance(k[f], dict) and g in k[f] for f in ("KP", "Attack", "Skill", "Element")):
            continue
        out.append(k)
    return out


@router.get("")
def list_keshins(type: Optional[str] = None, element: Optional[str] = None, game: Optional[str] = None,
                 details: bool = False):
    """All keshins (fighting spirits). Filters: ?type=kick&element=fire&game=VR · ?details=true for full records."""
    items = _filter(type, element, game)
    return {"Count": len(items), "Keshins": [_with_users(k) for k in items] if details else [k["Name"] for k in items]}


@router.get("/all")
def all_keshins():
    """Every keshin with type, element, special move, skill, KP/attack per game, image and users."""
    return [_with_users(k) for k in keshins]


@router.get("/types")
def keshin_types():
    counts = {}
    for k in keshins:
        counts[k["Type"]] = counts.get(k["Type"], 0) + 1
    return {"Types": dict(sorted(counts.items()))}


@router.get("/type/{type}")
def keshins_by_type(type: str, element: Optional[str] = None, game: Optional[str] = None):
    """Keshins of one type: /keshins/type/kick, /type/dribble, /type/block, /type/catch"""
    items = _filter(type, element, game)
    if not items:
        raise HTTPException(status_code=404, detail=f"No keshins of type '{type}'. See /keshins/types")
    return {"Type": items[0]["Type"], "Count": len(items), "Keshins": [_with_users(k) for k in items]}


@router.get("/element/{element}")
def keshins_by_element(element: str, type: Optional[str] = None, game: Optional[str] = None):
    items = _filter(type, element, game)
    if not items:
        raise HTTPException(status_code=404, detail=f"No keshins with element '{element}'")
    return {"Element": element.strip().title(), "Count": len(items), "Keshins": [_with_users(k) for k in items]}


@router.get("/game/{game}")
def keshins_by_game(game: str):
    """Keshins that appear in one game: /keshins/game/VR, /game/GO, /game/CS, /game/GX"""
    g = _game_code(game)
    items = _filter(game=g)
    return {"Game": GAMES[g], "Code": g, "Count": len(items), "Keshins": [_with_users(k) for k in items]}


@router.get("/{name}")
def get_keshin(name: str):
    """One keshin by its English name ('Heavenly Horse Arch Pegasus') or wiki title ('Majin Pegasus Arc')."""
    k = keshin_by_name.get(name.strip().casefold())
    if not k:
        raise HTTPException(status_code=404, detail=f"Keshin '{name}' not found")
    return _with_users(k)
