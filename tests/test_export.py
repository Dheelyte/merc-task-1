import json
from datetime import datetime, timezone

from freezegun import freeze_time

from app.config import load_file_config
from app.serializers import get_serializer


def test_serializer_module_comes_from_config():
    name = load_file_config()["export"]["serializer"]
    assert get_serializer().__name__ == name


def test_export_returns_all_notes(client):
    client.post("/notes", json={"title": "one", "tag": "a"})
    client.post("/notes", json={"title": "two", "tag": "b"})
    resp = client.get("/notes/export")
    assert resp.status_code == 200
    data = json.loads(resp.content)
    assert [n["title"] for n in data] == ["one", "two"]


@freeze_time("2024-03-01 12:00:00")
def test_export_timestamps_are_iso(client):
    client.post("/notes", json={"title": "frozen"})
    data = json.loads(client.get("/notes/export").content)
    stamp = datetime.fromisoformat(data[0]["created_at"])
    assert stamp.replace(tzinfo=timezone.utc).year == 2024
