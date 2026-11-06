import json

from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


def test_home():
    r = client.get("/")
    assert r.status_code == 200


def test_all_is_valid_json_without_nan():
    r = client.get("/all")
    assert r.status_code == 200
    data = r.json()
    assert isinstance(data, list) and len(data) > 4000
    assert all(p["Name"] for p in data)               # no empty rows
    json.dumps(data, allow_nan=False)                 # no NaN anywhere


def test_player_with_missing_fields_does_not_crash():
    # these players have no ID / archetype in the source data; they used to return 500
    r = client.get("/players/Garruk Vynce")
    assert r.status_code == 200
    assert r.json()[0]["ID"] is None


def test_name_search_is_case_insensitive():
    for q in ["Mark Evans", "mark evans", "MARK EVANS", "  mark evans "]:
        r = client.get(f"/players/{q}")
        assert r.status_code == 200, q
        assert r.json()[0]["Name"] == "Mark Evans"


def test_ids_are_integers_and_archetypes_english():
    p = client.get("/players/id/1").json()[0]
    assert p["ID"] == 1 and isinstance(p["ID"], int)
    assert p["Archetype"] == "Justice"
    assert isinstance(p["Power"], int)


def test_single_field_and_stat_endpoints():
    assert client.get("/players/id/1/position").json() == {"ID": 1, "Position": "GK"}
    assert client.get("/players/id/1/power").json()["Power"] == 126
    assert client.get("/players/mark evans/total").json()["Total"] == 962
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
    raimon = client.get("/teams/raimon").json()
    assert raimon["Team"] == "Raimon" and "Mark Evans" in raimon["Players"]
