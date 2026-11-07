from typing import Optional

from fastapi import APIRouter, HTTPException

from app.data import df_players
from app.games import GAMES, resolve
from app.routers.utils import clean_value

router = APIRouter(tags=["coaches & staff"])

# zukan "Role": Player, Coach, Manager, Coordinator, Player Manager, Player Coordinator
STAFF = {"coach": "Coach", "coaches": "Coach", "manager": "Manager", "managers": "Manager",
         "coordinator": "Coordinator", "coordinators": "Coordinator"}
COLUMNS = ["ID", "Name", "Role", "Game", "Game code", "Team", "Teams", "Position", "Element", "Image", "Description"]


def _staff(role: Optional[str] = None, game: Optional[str] = None):
    rows = df_players[df_players["Role"].fillna("Player") != "Player"]
    if role:
        r = STAFF.get(role.strip().casefold())
        if not r:
            raise HTTPException(status_code=404, detail=f"Unknown role '{role}'. Use coach, manager or coordinator")
        rows = rows[rows["Role"].str.contains(r, case=False)]
    if game:
        title = resolve(game)
        if not title:
            raise HTTPException(status_code=400, detail=f"Unknown game '{game}'. Use a code: {', '.join(GAMES)}")
        rows = rows[rows["Game"] == title]
    return [{c: clean_value(r[c]) for c in COLUMNS} for _, r in rows.iterrows()]


@router.get("/staff")
def all_staff(game: Optional[str] = None):
    """Coaches, managers and coordinators (characters whose role isn't just Player). ?game=IE"""
    out = _staff(game=game)
    counts = {}
    for s in out:
        counts[s["Role"]] = counts.get(s["Role"], 0) + 1
    return {"Count": len(out), "Roles": counts, "Staff": out}


@router.get("/coaches")
def coaches(game: Optional[str] = None):
    """Coaches (incl. Player Coach). Their full card and stats are at /players/id/{ID}."""
    out = _staff("coach", game)
    return {"Count": len(out), "Coaches": out}


@router.get("/managers")
def managers(game: Optional[str] = None):
    out = _staff("manager", game)
    return {"Count": len(out), "Managers": out}


@router.get("/coordinators")
def coordinators(game: Optional[str] = None):
    out = _staff("coordinator", game)
    return {"Count": len(out), "Coordinators": out}
