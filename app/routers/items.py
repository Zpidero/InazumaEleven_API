from typing import Optional

from fastapi import APIRouter, HTTPException

from app.data import items

router = APIRouter(prefix="/items", tags=["equipment"])

CATEGORY_ALIASES = {"boot": "Boots", "boots": "Boots", "shoes": "Boots", "bracelet": "Bracelet",
                    "bracelets": "Bracelet", "misanga": "Bracelet", "pendant": "Pendant", "pendants": "Pendant",
                    "special": "Special", "specials": "Special", "kit": "Kit", "kits": "Kit", "uniform": "Kit"}
STATS = ["Power", "Control", "Technique", "Pressure", "Physical", "Agility", "Intelligence"]


def _category(c: str) -> str:
    cat = CATEGORY_ALIASES.get(c.strip().casefold())
    if not cat:
        raise HTTPException(status_code=404, detail=f"Unknown category '{c}'. Use boots, bracelet, pendant, special or kit")
    return cat


def _filter(category: Optional[str] = None, stat: Optional[str] = None):
    out = items
    if category:
        cat = _category(category)
        out = [i for i in out if i["Category"] == cat]
    if stat:
        s = next((x for x in STATS if x.casefold() == stat.strip().casefold() or (x == "Power" and stat.casefold() == "kick")), None)
        if not s:
            raise HTTPException(status_code=400, detail=f"Unknown stat '{stat}'. Use {', '.join(STATS)}")
        out = sorted([i for i in out if (i["Stats"] or {}).get(s)], key=lambda i: -i["Stats"][s])
    return out


@router.get("")
def list_items(category: Optional[str] = None, stat: Optional[str] = None, details: bool = False):
    """Equipment and kits. ?category=boots · ?stat=power (items boosting it, best first) · ?details=true"""
    out = _filter(category, stat)
    return {"Count": len(out), "Items": out if details else [i["Name"] for i in out]}


@router.get("/all")
def all_items():
    """Every item: category, image, stat bonuses, effect and how to obtain it."""
    return items


@router.get("/categories")
def item_categories():
    counts = {}
    for i in items:
        counts[i["Category"]] = counts.get(i["Category"], 0) + 1
    return {"Categories": counts}


@router.get("/category/{category}")
def items_by_category(category: str, stat: Optional[str] = None):
    """/items/category/boots, /bracelet, /pendant, /special, /kit (optionally ?stat=agility)"""
    out = _filter(category, stat)
    return {"Category": _category(category), "Count": len(out), "Items": out}


@router.get("/stat/{stat}")
def items_by_stat(stat: str, category: Optional[str] = None):
    """Items that boost a stat, best first: /items/stat/power, /items/stat/agility?category=boots"""
    out = _filter(category, stat)
    return {"Stat": stat.strip().title(), "Count": len(out), "Items": out}


@router.get("/{name}")
def get_item(name: str):
    n = name.strip().casefold()
    hits = [i for i in items if i["Name"].casefold() == n or (i["Japanese name"] or "").casefold() == n]
    if not hits:
        raise HTTPException(status_code=404, detail=f"Item '{name}' not found")
    return hits[0] if len(hits) == 1 else hits
