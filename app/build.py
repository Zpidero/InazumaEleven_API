"""Builds data/players.json, data/techniques.json and data/teams.json from:
  1. zukan.inazuma.jp (official)  — players, stats, images, teams, how to obtain, techniques, emblems
  2. Inazuma Eleven Wiki (CC BY-SA) — which techniques each player learns in Victory Road
  3. community sheet (optional)  — archetype and Legendary-rarity stats
"""
import json
from collections import defaultdict
from pathlib import Path

from app.sources import sheet, wiki, zukan

STATS = ["Power", "Control", "Technique", "Pressure", "Physical", "Agility", "Intelligence"]
DATA = Path("data")


def _key(name, game, age):
    return (str(name).strip(), str(game).strip(), str(age).strip())


def build_players(char_list, params, sheet_rows):
    """Merge chara_list rows with chara_param cards (+ sheet extras)."""
    param_by_key = defaultdict(list)
    for c in params:
        param_by_key[_key(c["Name"], c["Game"], c["Age group"])].append(c)

    players = []
    for row in char_list:
        k = _key(row["Name"], row["Game"], row["Age group"])
        cands = param_by_key.get(k, [])
        card = next((c for c in cands if c["Nickname"] == row["Nickname"]), cands[0] if cands else {})
        if card in cands:
            cands.remove(card)                       # each card used once (duplicates share a key)
        stats = {s: card.get(s) for s in STATS}
        stats["Total"] = sum(v for v in stats.values() if v is not None) if all(stats.values()) else None
        by_no = sheet_rows.get(("no", row["No"]))
        extra = by_no if by_no and by_no["Name"] == row["Name"] else sheet_rows.get(k, {})
        players.append({
            "ID": row["No"],
            "Name": row["Name"],
            "Nickname": row["Nickname"],
            "Game": row["Game"],
            "Image": card.get("Image"),
            "Viewer": card.get("Viewer"),
            "Description": row["Description"],
            "Position": row["Position"],
            "Element": row["Element"],
            "Gender": row["Gender"],
            "Role": row["Role"],
            "Age group": row["Age group"],
            "School year": row["School year"],
            "Team": row["Teams"][0] if row["Teams"] else None,
            "Teams": row["Teams"],
            "Archetype": extra.get("Archetype"),
            **stats,
            "Legendary": extra.get("Legendary"),
            "Obtain": card.get("Obtain", []),
            "Techniques": [],
            "Keshin": None,
        })
    return players


def match_wiki(players, wiki_players, redirects):
    """Attach each wiki moveset to exactly one zukan player."""
    by_name = defaultdict(list)
    for i, p in enumerate(players):
        by_name[p["Name"].casefold()].append(i)

    claimed = {}
    unmatched = []
    pending = defaultdict(list)                     # ambiguous: (page, game) → wiki entries
    for w in wiki_players:
        names = {n.casefold() for n in redirects.get(w["page"], [w["page"]])} if w["page"] else set()
        cands = list(dict.fromkeys(i for n in names for i in by_name.get(n, [])))
        if not cands:
            unmatched.append(w)
            continue
        same_game = [i for i in cands if players[i]["Game"] == w["game"]] or cands
        pick = [i for i in same_game if players[i]["Element"] == w["element"] and players[i]["Position"] == w["position"]] or same_game
        pick = [i for i in pick if players[i]["Gender"] == w["gender"]] or pick
        if len(pick) == 1:
            if pick[0] not in claimed or "_" in claimed[pick[0]]["key"]:
                claimed[pick[0]] = w                # prefer the base entry over variants (Endou vs Endou_B)
        else:
            pending[(w["page"], tuple(pick))].append(w)

    # several versions of one character in the same game: pair them up in order
    for (_, pick), entries in pending.items():
        free = [i for i in pick if i not in claimed]
        for i, w in zip(sorted(free, key=lambda i: players[i]["ID"] or 0), sorted(entries, key=lambda w: w["key"])):
            claimed[i] = w
    return claimed, unmatched


def build_techniques(wiki_tech, used_keys, skills, tech_redirects):
    """One record per technique used in Victory Road, named in English when zukan has it."""
    by_name = {s["Name"].casefold(): s for s in skills}

    # Pick the English (zukan) name for each wiki technique. Several wiki techniques can reach
    # the same English name through redirects: an exact title match wins, the rest keep their wiki name.
    claim = {}                                       # english name → (priority, key)
    wanted = {}
    for key in sorted(used_keys):
        w = wiki_tech.get(key)
        if not w:
            continue
        page = w["page"] or key
        for prio, n in [(0, page)] + [(1, r) for r in sorted(tech_redirects.get(page, [])) if r != page]:
            if n.casefold() in by_name:
                wanted[key] = n.casefold()
                if n.casefold() not in claim or (prio, key) < claim[n.casefold()]:
                    claim[n.casefold()] = (prio, key)
                break

    out, name_of = [], {}
    for key in sorted(used_keys):
        w = wiki_tech.get(key)
        if not w:
            continue
        page = w["page"] or key
        en = wanted.get(key)
        z = by_name[en] if en and claim[en][1] == key else None
        name = z["Name"] if z else page
        out.append({
            "_key": key, "_plain": bool(z),
            "Name": name,
            "Wiki name": page,
            "Type": w["type"],
            "Element": w["element"],
            "Power": w["power"],
            "Cost": w["cost"],
            "Basara power": w["power_basara"],
            "Basara cost": w["cost_basara"],
            "Categories": z["Categories"] if z else [],
            "Description": z["Description"] if z else None,
            "Image": z["Image"] if z else None,
            "Video": z["Video"] if z else None,
        })
    # Variants that share a wiki name (God Hand Mountain/Forest, Mode Change …) get the element as suffix;
    # the one matched to zukan keeps the plain name.
    groups = defaultdict(list)
    for t in out:
        groups[t["Name"].casefold()].append(t)
    taken = set(groups)
    for same in groups.values():
        if len(same) == 1:
            continue
        same.sort(key=lambda t: (not t["_plain"], t["_key"]))
        for t in same[1:]:
            base = f'{t["Name"]} ({t["Element"]})' if t["Element"] else t["Name"]
            name, n = base, 2
            while name.casefold() in taken:
                name, n = f"{base} {n}", n + 1
            taken.add(name.casefold())
            t["Name"] = name
    for t in out:
        name_of[t.pop("_key")] = t["Name"]
        t.pop("_plain")

    # zukan techniques that no player list mentions (e.g. new ones) are still useful
    known = {t["Name"].casefold() for t in out}
    for s in skills:
        if s["Name"].casefold() not in known:
            known.add(s["Name"].casefold())
            out.append({"Name": s["Name"], "Wiki name": None, "Type": None, "Element": None, "Power": None, "Cost": None,
                        "Basara power": None, "Basara cost": None, "Categories": s["Categories"],
                        "Description": s["Description"], "Image": s["Image"], "Video": s["Video"]})
    return sorted(out, key=lambda t: t["Name"].casefold()), name_of


def build_teams(players, emblems):
    alias = {
        "Raimon First Squad": "Revolutionary Raimon", "Baseball Club Team": "South Cirrus Baseball Club",
        "Eastwind": "Eastwind International", "Milky Way Charter": "Milky Way",
        "Noble Insight": "Noble Insight Institute", "Polestar Academy": "Polestar",
        "Lunar Prime Academy": "Lunar Prime", "Rampart Junior High": "Rampart",
        "South Cirrus Junior High": "South Cirrus", "Team Sharp": "Inazuma National", "Umbrella MS": "Umbrella",
    }
    # emblem per team name; the API groups players into (team, game) versions itself
    names = sorted({t for p in players for t in p["Teams"]}, key=str.casefold)
    return [{"Team": t, "Image": emblems.get(t) or emblems.get(alias.get(t, ""))} for t in names]


def run():
    print("⚡ zukan: characters");  char_list = zukan.scrape_character_list()
    print("⚡ zukan: parameters");  params = zukan.scrape_character_params()
    print("⚡ zukan: techniques");  skills = zukan.scrape_skills()
    print("⚡ zukan: emblems");     emblems = zukan.scrape_emblems()
    print("⚡ sheet");               sheet_rows = sheet.load()
    print("⚡ wiki: movesets");     wiki_players = wiki.load_players()
    print("⚡ wiki: techniques");   wiki_tech = wiki.load_techniques()

    players = build_players(char_list, params, sheet_rows)

    print("⚡ wiki: English names")
    player_red = wiki.redirects(sorted({w["page"] for w in wiki_players if w["page"]}))
    used = {m["waza"] for w in wiki_players for m in w["moves"]} | {w["keshin"] for w in wiki_players if w["keshin"]}
    tech_red = wiki.redirects(sorted({wiki_tech[k]["page"] for k in used if k in wiki_tech and wiki_tech[k]["page"]}))

    techniques, name_of = build_techniques(wiki_tech, used, skills, tech_red)
    claimed, unmatched = match_wiki(players, wiki_players, player_red)
    for i, w in claimed.items():
        players[i]["Techniques"] = [
            {"Name": name_of.get(m["waza"], m["waza"]), "Type": wiki_tech.get(m["waza"], {}).get("type"),
             "Element": wiki_tech.get(m["waza"], {}).get("element"), "Level": m["level"],
             "Form": m["form"], "Awakened": m["awakened"]}
            for m in w["moves"]
        ]
        players[i]["Keshin"] = name_of.get(w["keshin"], w["keshin"]) if w["keshin"] else None

    teams = build_teams(players, emblems)

    DATA.mkdir(exist_ok=True)
    for name, obj in [("players", players), ("techniques", techniques), ("teams", teams)]:
        (DATA / f"{name}.json").write_text(json.dumps(obj, ensure_ascii=False, separators=(",", ":")))
    with_moves = sum(1 for p in players if p["Techniques"])
    print(f"\n💾 {len(players)} players ({with_moves} with techniques), {len(techniques)} techniques, {len(teams)} teams")
    print(f"   wiki movesets without an English match: {len(unmatched)}")
    return players, techniques, teams
