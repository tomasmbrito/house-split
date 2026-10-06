import pytest

from app.main import create_app, parse_amount


@pytest.fixture
def client(tmp_path):
    app = create_app(db_path=str(tmp_path / "test.db"))
    return app.test_client()


def add_people(client, *names):
    for name in names:
        client.post("/people", data={"name": name})


def test_parse_amount():
    assert parse_amount("12") == 1200
    assert parse_amount("12.5") == 1250
    assert parse_amount("12,05") == 1205
    assert parse_amount("0") is None
    assert parse_amount("-3") is None
    assert parse_amount("1.234") is None
    assert parse_amount("abc") is None


def test_health(client):
    assert client.get("/health").get_json() == {"status": "ok"}


def test_home_page_loads(client):
    response = client.get("/")
    assert response.status_code == 200
    assert b"House Split" in response.data


def test_add_people(client):
    add_people(client, "Tomas", "henrique")
    assert client.get("/api/summary").get_json()["people"] == ["tomas", "henrique"]


def test_same_person_twice_shows_error(client):
    add_people(client, "tomas")
    response = client.post("/people", data={"name": "tomas"})
    assert "error=" in response.headers["Location"]


def test_expense_shared_by_everyone(client):
    add_people(client, "tomas", "henrique")
    client.post("/expenses", data={"description": "groceries", "amount": "30", "paid_by": "tomas"})

    summary = client.get("/api/summary").get_json()
    assert summary["balances"] == {"tomas": 1500, "henrique": -1500}
    assert summary["payments"] == [{"from": "henrique", "to": "tomas", "amount": 1500}]


def test_expense_shared_by_some(client):
    add_people(client, "tomas", "henrique", "ana")
    client.post(
        "/expenses",
        data={"description": "pizza", "amount": "20", "paid_by": "ana", "shared_by": ["ana", "henrique"]},
    )
    assert client.get("/api/summary").get_json()["balances"] == {"tomas": 0, "henrique": -1000, "ana": 1000}


def test_invalid_expense_is_rejected(client):
    add_people(client, "tomas")
    response = client.post("/expenses", data={"description": "x", "amount": "-5", "paid_by": "tomas"})
    assert "error=" in response.headers["Location"]
    assert client.get("/api/summary").get_json()["expenses"] == []


def test_delete_expense(client):
    add_people(client, "tomas", "henrique")
    client.post("/expenses", data={"description": "rent", "amount": "800", "paid_by": "tomas"})
    expense_id = client.get("/api/summary").get_json()["expenses"][0]["id"]

    client.post(f"/expenses/{expense_id}/delete")
    summary = client.get("/api/summary").get_json()
    assert summary["expenses"] == []
    assert summary["payments"] == []
