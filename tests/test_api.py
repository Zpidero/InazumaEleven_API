import json

from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


def mark():
    return client.get("/players/id/1").json()[0]


def test_home():
    assert client.get("/").status_code == 200


def test_all_is_valid_json_without_nan():
    r = client.get("/all")
    assert r.status_code == 200
    data = r.json()
    assert isinstance(data, list) and len(data) > 5000
    assert all(p["Name"] for p in data)
    json.dumps(data, allow_nan=False)


def test_name_search_is_case_insensitive():
    for q in ["Mark Evans", "mark evans", "MARK EVANS", "  mark evans "]:
        r = client.get(f"/players/{q}")
        assert r.status_code == 200, q
        assert r.json()[0]["Name"] == "Mark Evans"


def test_player_record_from_zukan():
    p = mark()
    assert p["ID"] == 1 and isinstance(p["ID"], int)
    assert p["Position"] == "GK" and p["Element"] == "Mountain"
    assert p["Image"].startswith("https://")
    assert "Raimon" in p["Teams"] and p["Team"] == "Raimon"
    assert p["Description"]
    assert all(isinstance(p[s], int) for s in ["Power", "Control", "Technique", "Pressure", "Physical", "Agility", "Intelligence", "Total"])
    assert p["Total"] == sum(p[s] for s in ["Power", "Control", "Technique", "Pressure", "Physical", "Agility", "Intelligence"])
    assert any(o["method"] for o in p["Obtain"])


def test_player_extras_from_sheet():
    p = mark()
    assert p["Archetype"] == "Justice"
    assert p["Legendary"]["Power"] > p["Power"]          # legendary rarity > level 50


def test_player_techniques():
    techs = client.get("/players/id/1/techniques").json()["Techniques"]
    assert len(techs) >= 3
    t = techs[0]
    assert set(t) >= {"Name", "Type", "Element", "Level", "Form", "Awakened"}
    assert {"Normal"} <= {m["Form"] for m in techs}


def test_technique_endpoints():
    names = client.get("/techniques").json()["Techniques"]
    assert len(names) > 500
    first_move = client.get("/players/id/1/techniques").json()["Techniques"][0]["Name"]
    t = client.get(f"/techniques/{first_move.lower()}").json()
    assert t["Name"] == first_move
    assert any(p["Name"] == "Mark Evans" for p in t["Learned by"])
    shots = client.get("/techniques?type=shoot&element=fire").json()["Techniques"]
    assert shots and len(shots) < len(names)
    assert "Shoot" in client.get("/techniques/types").json()["Types"]
    assert client.get("/techniques/no such move").status_code == 404


def test_single_field_and_stat_endpoints():
    assert client.get("/players/id/1/position").json() == {"ID": 1, "Position": "GK"}
    assert client.get("/players/id/1/power").json()["Power"] == mark()["Power"]
    assert client.get("/players/mark evans/total").json()["Total"] == mark()["Total"]
    assert client.get("/players/id/1/banana").status_code == 400
    assert client.get("/players/mark evans/banana").status_code == 400


def test_not_found():
    assert client.get("/players/Nobody Atall").status_code == 404
    assert client.get("/players/id/999999").status_code == 404
    assert client.get("/teams/No Such Team").status_code == 404


def test_filters_and_teams():
    elements = client.get("/elements/").json()["Elements"]
    assert set(elements) >= {"Fire", "Wind", "Forest", "Mountain"}
    gk = client.get("/positions/gk").json()
    assert gk["Position"] == "GK" and "Mark Evans" in gk["Players"]
    raimon = client.get("/teams/raimon/IE").json()
    assert raimon["Team"] == "Raimon" and "Mark Evans" in [p["Name"] for p in raimon["Players"]]
    japan = client.get("/teams/inazuma national/IE").json()   # players can belong to several teams
    assert "Mark Evans" in [p["Name"] for p in japan["Players"]]


def test_technique_getters():
    # a player returns their techniques, by id and by name
    assert mark()["Techniques"]
    by_name = client.get("/players/mark evans/techniques").json()
    assert by_name[0]["Techniques"] == mark()["Techniques"]
    # all techniques, names or full details
    assert client.get("/techniques?details=true").json()["Techniques"][0]["Name"]
    full = client.get("/techniques/all").json()
    assert "Learned by" in full[0]
    # by type, with friendly aliases
    kicks = client.get("/techniques/type/kick").json()
    assert kicks["Type"] == "Shoot" and kicks["Count"] > 50
    assert all(t["Type"] == "Shoot" for t in kicks["Techniques"])
    assert client.get("/techniques/type/dribble").json()["Count"] > 20
    assert client.get("/techniques/type/defense").json()["Type"] == "Block"
    assert client.get("/techniques/type/keeper").json()["Type"] == "Catch"
    fire = client.get("/techniques/element/fire?type=kick").json()
    assert all(t["Element"] == "Fire" and t["Type"] == "Shoot" for t in fire["Techniques"])
    assert client.get("/techniques/type/banana").status_code == 404


def test_technique_names_are_unique_and_consistent():
    full = client.get("/techniques/all").json()
    names = [t["Name"].casefold() for t in full]
    assert len(names) == len(set(names))
    # the element shown in a player's moveset matches the technique record
    for m in mark()["Techniques"]:
        t = client.get(f"/techniques/{m['Name']}").json()
        assert t["Element"] == m["Element"] and t["Type"] == m["Type"], m["Name"]


def test_teams_are_separate_per_game():
    alpine = client.get("/teams/alpine").json()
    assert len(alpine["Versions"]) > 1 and "VR" in alpine["Games"]
    vr = client.get("/teams/alpine/VR").json()
    ie2 = client.get("/teams/alpine/ie2").json()
    assert vr["Game"] == "Inazuma Eleven: Victory Road" and ie2["Game"].startswith("Inazuma Eleven 2")
    assert {p["Name"] for p in vr["Players"]}.isdisjoint({p["Name"] for p in ie2["Players"]}) or vr["Players"] != ie2["Players"]
    assert client.get("/teams/alpine?game=victory road").json() == vr
    assert client.get("/teams/alpine/ORION").status_code in (404, 200)
    assert client.get("/teams/alpine/banana").status_code == 400
    listing = client.get("/teams/?game=VR").json()["Teams"]
    assert listing and all(t["Game code"] == "VR" for t in listing)


def test_games_and_game_filter():
    codes = [g["Code"] for g in client.get("/games/").json()["Games"]]
    assert codes[0] == "IE" and "VR" in codes
    vr = client.get("/games/vr").json()
    assert vr["Code"] == "VR" and vr["Players"] and vr["Teams"]
    versions = client.get("/players/mark evans").json()
    assert len(versions) > 1
    only_ie = client.get("/players/mark evans?game=IE").json()
    assert all(p["Game code"] == "IE" for p in only_ie)


def test_keshin_getters():
    listing = client.get("/keshins").json()
    assert listing["Count"] >= 90 and len(set(listing["Keshins"])) == listing["Count"]
    k = client.get("/keshins/pegasus arc").json()                  # by display name
    assert k == client.get("/keshins/majin pegasus arc").json()     # or full name
    assert k["Type"] == "Shoot" and k["Hissatsu"] and k["Image"].startswith("https://")
    assert any(u["Name"] == "Arion Sherwind" for u in k["Users"]) and k["In Victory Road"]
    full = client.get("/keshins/all").json()
    assert len(full) == listing["Count"] and "Users" in full[0]
    kicks = client.get("/keshins/type/kick").json()
    assert kicks["Type"] == "Shoot" and all(x["Type"] == "Shoot" for x in kicks["Keshins"])
    assert client.get("/keshins/type/keeper").json()["Type"] == "Catch"
    vr = client.get("/keshins/game/vr").json()
    assert vr["Count"] and all(x["Users"] for x in vr["Keshins"])
    assert client.get("/keshins/game/go").json()["Count"]
    assert client.get("/keshins/game/ares").status_code == 400
    assert client.get("/keshins/element/fire").json()["Count"]
    assert client.get("/keshins/nope").status_code == 404
    # every keshin a player summons has a keshin record
    names = {x["Name"] for x in full}
    for p in client.get("/all").json():
        assert p["Keshin"] is None or p["Keshin"] in names, (p["Name"], p["Keshin"])
    arion = client.get("/players/arion sherwind/keshin").json()
    assert arion[0]["Keshin"]["Name"] == "Majin Pegasus Arc"


def test_tactics_and_formations():
    t = client.get("/tactics").json()
    assert t["Count"] > 50
    one = client.get(f"/tactics/{t['Tactics'][0].lower()}").json()
    assert one["Description"] and one["Image"].startswith("https://")
    off = client.get("/tactics/type/attack").json()
    assert off["Type"] == "Offense" and all(x["Type"] == "Offense" for x in off["Tactics"])
    assert client.get("/tactics/nope").status_code == 404
    f = client.get("/formations").json()
    assert f["Count"] >= 8
    d = client.get("/formations/diamond").json()
    assert d == client.get("/formations/4-4-2 diamond").json()
    assert d["Layout"] == "4-4-2" and len(d["Positions"]) == 11 and d["Description"]
    assert d["Defenders"] + d["Midfielders"] + d["Forwards"] == 10


def test_mixmax():
    names = client.get("/mixmax").json()["Auras"]
    assert len(names) >= 15
    okita = client.get("/mixmax/okita souji").json()
    assert okita["Aura player"] and any(u["Name"] == "Victor Blade" for u in okita["Users"])
    assert client.get(f"/mixmax/{okita['Aura player'][0]['Name']}").json()["Aura"] == okita["Aura"]
    victor = client.get("/players/victor blade/mixmax").json()
    assert any(m["Name"] == "Okita Souji" for v in victor for m in v["Mix Max"])
    assert any(a["Aura for"] for a in victor)          # Victor Blade is also an aura (Tsurugi Kyousuke)
    assert client.get("/mixmax/nope").status_code == 404
    assert client.get("/players/mark evans/power").status_code == 200   # route order still fine


def test_items():
    cats = client.get("/items/categories").json()["Categories"]
    assert set(cats) >= {"Boots", "Bracelet", "Pendant", "Special", "Kit"}
    boots = client.get("/items/category/shoes").json()
    assert boots["Category"] == "Boots" and boots["Count"] > 100
    raimon = client.get("/items/raimon boots").json()
    assert raimon["Stats"] == {"Pressure": 4, "Agility": 6} and raimon["Image"].startswith("https://")
    assert raimon["How to obtain"]
    best = client.get("/items/stat/kick?category=boots").json()["Items"]       # kick = Power
    assert best and best[0]["Stats"]["Power"] >= best[-1]["Stats"]["Power"]
    assert client.get("/items/category/banana").status_code == 404
    assert client.get("/items/stat/banana").status_code == 400
    assert client.get("/items/no such item").status_code == 404


def test_totems():
    t = client.get("/totems").json()
    assert t["Count"] > 30
    pegasus = client.get("/totems/pegasus").json()
    assert pegasus["Image"] and pegasus["Galaxy stats"]
    assert any(u["Name"] == "Arion Sherwind" for u in pegasus["Users"])
    assert client.get("/techniques/type/soul").json()["Type"] == "Totem"
    assert any(x["Name"] == "Pegasus" for v in client.get("/players/arion sherwind/totems").json() for x in v["Totems"])
    assert client.get("/totems/nope").status_code == 404


def test_staff():
    staff = client.get("/staff").json()
    assert staff["Count"] > 100 and "Player" not in staff["Roles"]
    coaches = client.get("/coaches").json()["Coaches"]
    assert coaches and all("Coach" in c["Role"] for c in coaches)
    assert any(m["Name"] == "Ray Dark" for m in client.get("/managers?game=IE").json()["Managers"])
    assert client.get("/coordinators").json()["Count"] >= 50
