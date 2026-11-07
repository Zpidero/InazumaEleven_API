from typing import Optional

from fastapi import APIRouter, HTTPException

from app.data import df_players, totem_users, totems
from app.routers.techniques import TYPE_ALIASES
from app.routers.utils import clean_value, matches

router = APIRouter(tags=["totems"])


def _with_users(t: dict) -> dict:
    return {**t, "Users": totem_users.get(t["Name"].casefold(), [])}


def _filter(type: Optional[str], element: Optional[str]):
    out = totems
    if type:
        tp = TYPE_ALIASES.get(type.strip().casefold(), type.strip())
        out = [t for t in out if (t["Type"] or "").casefold() == tp.casefold()]
    if element:
        out = [t for t in out if (t["Element"] or "").casefold() == element.strip().casefold()]
    return out


@router.get("/totems")
def list_totems(type: Optional[str] = None, element: Optional[str] = None, details: bool = False):
    """Totems (Souls in Japanese). ?type=kick&element=wind · ?details=true adds stats and users."""
    out = _filter(type, element)
    return {"Count": len(out), "Totems": [_with_users(t) for t in out] if details else [t["Name"] for t in out]}


@router.get("/totems/all")
def all_totems():
    """Every totem with type, element, image, GO Galaxy stats and the Victory Road players who have it."""
    return [_with_users(t) for t in totems]


@router.get("/totems/{name}")
def get_totem(name: str):
    n = name.strip().casefold()
    for t in totems:
        if n in {t["Name"].casefold(), t["Wiki name"].casefold(), *(o.casefold() for o in t["Other names"] or [])}:
            return _with_users(t)
    raise HTTPException(status_code=404, detail=f"Totem '{name}' not found")


@router.get("/players/{name}/totems")
def get_player_totems(name: str):
    rows = df_players[matches(df_players["Name"], name)]
    if rows.empty:
        raise HTTPException(status_code=404, detail=f"Player {name} not found")
    return [{"ID": clean_value(r["ID"]), "Name": r["Name"], "Game": r["Game"],
             "Totems": [m for m in r["Techniques"] or [] if m["Type"] == "Totem"]} for _, r in rows.iterrows()]
