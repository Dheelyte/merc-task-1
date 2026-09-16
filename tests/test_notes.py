import httpx
from faker import Faker

fake = Faker()
Faker.seed(1234)


def make_note(client, **overrides):
    payload = {"title": fake.sentence(nb_words=3), "body": fake.paragraph(), "tag": "work"}
    payload.update(overrides)
    resp = client.post("/notes", json=payload)
    assert resp.status_code == 201
    return resp.json()


def test_health(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


def test_create_note_generates_slug_and_html(client):
    note = make_note(client, title="Hello World!", body="**bold**")
    assert note["slug"] == "hello-world"
    assert "<strong>bold</strong>" in note["html"]


def test_create_note_requires_title(client):
    resp = client.post("/notes", json={"title": "", "body": "x"})
    assert resp.status_code == 422


def test_get_note(client):
    created = make_note(client)
    resp = client.get(f"/notes/{created['id']}")
    assert resp.status_code == 200
    assert resp.json()["title"] == created["title"]


def test_get_missing_note_returns_404(client):
    assert client.get("/notes/999").status_code == 404


def test_list_notes_filters_by_tag(client):
    make_note(client, tag="work")
    make_note(client, tag="home")
    make_note(client, tag="work")
    resp = client.get("/notes", params={"tag": "work"})
    assert resp.status_code == 200
    assert len(resp.json()) == 2


def test_list_notes_pagination(client):
    for _ in range(5):
        make_note(client)
    resp = client.get("/notes", params={"limit": 2, "offset": 3})
    assert [n["id"] for n in resp.json()] == [4, 5]


def test_update_note_changes_slug(client):
    created = make_note(client, title="Old title")
    resp = client.put(f"/notes/{created['id']}", json={"title": "New title"})
    assert resp.status_code == 200
    assert resp.json()["slug"] == "new-title"


def test_delete_requires_token(client):
    created = make_note(client)
    assert client.delete(f"/notes/{created['id']}").status_code == 401


def test_delete_note_with_token(client, auth_headers):
    created = make_note(client)
    resp = client.delete(f"/notes/{created['id']}", headers=auth_headers)
    assert resp.status_code == 204
    assert client.get(f"/notes/{created['id']}").status_code == 404


def test_login_rejects_wrong_user(client):
    resp = client.post("/auth/token", json={"username": "bob", "password": "pw"})
    assert resp.status_code == 401


def test_metrics_endpoint_is_mounted(client):
    client.get("/health")
    resp = client.get("/metrics/")
    assert resp.status_code == 200
    assert "notes_requests_total" in resp.text


def test_client_is_httpx_based(client):
    # TestClient is built on httpx; keep an eye on that if we ever swap it out
    assert isinstance(client, httpx.Client)
