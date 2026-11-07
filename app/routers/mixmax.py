from fastapi import APIRouter, HTTPException

from app.data import df_players, mixmax, mixmax_users
from app.routers.utils import clean_value, matches

router = APIRouter(tags=["mix max"])


def _with_users(m: dict) -> dict:
    return {**m, "Users": mixmax_users.get(m["Aura"].casefold(), [])}


def _lookup(name: str):
    n = name.strip().casefold()
    for m in mixmax:
        names = {m["Aura"].casefold(), m["Wiki name"].casefold()} | {p["Name"].casefold() for p in m["Aura player"] or []}
        if n in names:
            return m
    raise HTTPException(status_code=404, detail=f"Mix Max aura '{name}' not found")


@router.get("/mixmax")
def list_mixmax(details: bool = False):
    """Mix Max auras in Victory Road. ?details=true adds the aura player and who can use it."""
    return {"Count": len(mixmax), "Auras": [_with_users(m) for m in mixmax] if details else [m["Aura"] for m in mixmax]}


@router.get("/mixmax/all")
def all_mixmax():
    """Every aura, the character it comes from (when playable) and the players who can Mix Max with it."""
    return [_with_users(m) for m in mixmax]


@router.get("/mixmax/{name}")
def get_mixmax(name: str):
    """One aura by its name or the aura character's name: 'Okita Souji', 'Soji Okita', 'Joan of Arc' …"""
    return _with_users(_lookup(name))


@router.get("/players/{name}/mixmax")
def get_player_mixmax(name: str):
    """Who a player Mix Maxes with (aura, aura player, level, form) — or which players use them as aura."""
    rows = df_players[matches(df_players["Name"], name)]
    if rows.empty:
        raise HTTPException(status_code=404, detail=f"Player {name} not found")
    by_aura = {m["Aura"].casefold(): m for m in mixmax}
    out = []
    for _, r in rows.iterrows():
        uses = [{**m, "Aura player": (by_aura.get(m["Name"].casefold()) or {}).get("Aura player")}
                for m in r["Techniques"] or [] if m["Type"] == "Mix Max"]
        as_aura = [m["Aura"] for m in mixmax if any(p["ID"] == r["ID"] for p in m["Aura player"] or [])]
        out.append({"ID": clean_value(r["ID"]), "Name": r["Name"], "Game": r["Game"],
                    "Mix Max": uses, "Aura for": [{"Aura": a, "Users": mixmax_users.get(a.casefold(), [])} for a in as_aura]})
    return out
