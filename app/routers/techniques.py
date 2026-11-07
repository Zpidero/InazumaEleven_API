from typing import Optional

from fastapi import APIRouter, HTTPException

from app.data import learned_by, technique_by_name, techniques

router = APIRouter(prefix="/techniques", tags=["techniques"])

# friendly words → technique type
TYPE_ALIASES = {
    "shoot": "Shoot", "shot": "Shoot", "shots": "Shoot", "kick": "Shoot", "kicks": "Shoot",
    "dribble": "Dribble", "dribbles": "Dribble", "offense": "Dribble", "offence": "Dribble",
    "block": "Block", "blocks": "Block", "defense": "Block", "defence": "Block",
    "catch": "Catch", "catches": "Catch", "keeper": "Catch", "goalkeeper": "Catch", "gk": "Catch",
    "skill": "Skill", "skills": "Skill", "passive": "Skill",
    "keshin": "Keshin", "avatar": "Keshin",
    "mixmax": "Mix Max", "mix max": "Mix Max", "totem": "Totem", "totems": "Totem", "soul": "Totem", "souls": "Totem",
    "awakening": "Awakening Power", "awakening power": "Awakening Power",
}


def _eq(a, b) -> bool:
    return a is not None and str(a).casefold() == str(b).strip().casefold()


def _type(name: str) -> str:
    return TYPE_ALIASES.get(name.strip().casefold(), name.strip())


def _with_learners(t: dict) -> dict:
    return {**t, "Learned by": learned_by.get(t["Name"].casefold(), [])}


def _filter(type: Optional[str] = None, element: Optional[str] = None):
    return [t for t in techniques
            if (type is None or _eq(t["Type"], _type(type))) and (element is None or _eq(t["Element"], element))]


@router.get("")
def list_techniques(type: Optional[str] = None, element: Optional[str] = None, details: bool = False):
    """All special moves. Filters: ?type=kick&element=fire · ?details=true for full records."""
    items = _filter(type, element)
    return {"Count": len(items), "Techniques": items if details else [t["Name"] for t in items]}


@router.get("/all")
def all_techniques():
    """Every technique with stats, description, image/video and who learns it."""
    return [_with_learners(t) for t in techniques]


@router.get("/types")
def technique_types():
    """Technique types and how many there are of each (+ the friendly aliases you can use)."""
    counts = {}
    for t in techniques:
        if t["Type"]:
            counts[t["Type"]] = counts.get(t["Type"], 0) + 1
    return {"Types": dict(sorted(counts.items())), "Aliases": TYPE_ALIASES}


@router.get("/elements")
def technique_elements():
    return {"Elements": sorted({t["Element"] for t in techniques if t["Element"]})}


@router.get("/type/{type}")
def techniques_by_type(type: str, element: Optional[str] = None):
    """All techniques of one type: /techniques/type/kick, /type/dribble, /type/block, /type/catch …"""
    items = _filter(type, element)
    if not items:
        raise HTTPException(status_code=404, detail=f"No techniques of type '{type}'. See /techniques/types")
    return {"Type": items[0]["Type"], "Count": len(items), "Techniques": items}


@router.get("/element/{element}")
def techniques_by_element(element: str, type: Optional[str] = None):
    """All techniques of one element: /techniques/element/fire (optionally ?type=kick)."""
    items = _filter(type, element)
    if not items:
        raise HTTPException(status_code=404, detail=f"No techniques with element '{element}'")
    return {"Element": items[0]["Element"], "Count": len(items), "Techniques": items}


@router.get("/{name}")
def get_technique(name: str):
    """One technique: stats, description, media and every player who learns it (level, form)."""
    t = technique_by_name.get(name.strip().casefold())
    if not t:
        raise HTTPException(status_code=404, detail=f"Technique '{name}' not found")
    return _with_learners(t)
