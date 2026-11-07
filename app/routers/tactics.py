from typing import Optional

from fastapi import APIRouter, HTTPException

from app.data import formations, tactics

router = APIRouter(tags=["tactics & formations"])

TACTIC_ALIASES = {"of": "Offense", "offense": "Offense", "offence": "Offense", "attack": "Offense",
                  "df": "Defense", "defense": "Defense", "defence": "Defense",
                  "both": "Offense / Defense", "ofdf": "Offense / Defense", "other": "Other"}


def _find(items, name, what):
    n = name.strip().casefold()
    hit = next((x for x in items if x["Name"].casefold() == n), None) \
        or next((x for x in items if x.get("Style", "").casefold() == n), None)
    if not hit:
        raise HTTPException(status_code=404, detail=f"{what} '{name}' not found")
    return hit


@router.get("/tactics")
def list_tactics(type: Optional[str] = None, details: bool = False):
    """Victory Road tactics (team special moves). ?type=offense|defense|both · ?details=true"""
    items = tactics
    if type:
        t = TACTIC_ALIASES.get(type.strip().casefold(), type.strip())
        items = [x for x in tactics if x["Type"].casefold() == t.casefold()]
    return {"Count": len(items), "Tactics": items if details else [x["Name"] for x in items]}


@router.get("/tactics/all")
def all_tactics():
    """Every tactic: type, power, cost, description, effect, geoglyph effect and icon."""
    return tactics


@router.get("/tactics/type/{type}")
def tactics_by_type(type: str):
    res = list_tactics(type, details=True)
    if not res["Count"]:
        raise HTTPException(status_code=404, detail=f"No tactics of type '{type}'. Use offense, defense or both")
    return {"Type": res["Tactics"][0]["Type"], **res}


@router.get("/tactics/{name}")
def get_tactic(name: str):
    return _find(tactics, name, "Tactic")


@router.get("/formations")
def list_formations(details: bool = False):
    """Victory Road formations. ?details=true for layout, ratings, description and pitch positions."""
    return {"Count": len(formations), "Formations": formations if details else [f["Name"] for f in formations]}


@router.get("/formations/all")
def all_formations():
    return formations


@router.get("/formations/{name}")
def get_formation(name: str):
    """One formation: '4-4-2 Diamond' or just 'diamond'. Positions are x/y in % of the pitch (GK at y≈97)."""
    return _find(formations, name, "Formation")
