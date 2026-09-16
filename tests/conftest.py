import os

os.environ["NOTES_DATABASE_URL"] = "sqlite://"
os.environ["NOTES_JWT_SECRET"] = "test-secret-that-is-long-enough-for-hs256"

import pytest
from fastapi.testclient import TestClient

from app.db import Base, engine
from app.main import app


@pytest.fixture()
def client():
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    with TestClient(app) as c:
        yield c


@pytest.fixture()
def auth_headers(client):
    resp = client.post("/auth/token", json={"username": "admin", "password": "pw"})
    return {"Authorization": f"Bearer {resp.json()['access_token']}"}
