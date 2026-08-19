from __future__ import annotations

import pytest
from app.db.models.models import ShortiLink
from app.main import app
from fastapi.testclient import TestClient
from sqlmodel import create_engine
from sqlmodel import Session
from sqlmodel import SQLModel
from sqlmodel import StaticPool


TEST_DB_URL = "sqlite://"  # in-memory, discarded after each test


@pytest.fixture(name="client")
def client_fixture():
    engine = create_engine(
        TEST_DB_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)

    with Session(engine) as session:
        session.add(
            ShortiLink(
                shorti_key="abc123", shorti_url="https://example.com", brand="example"
            )
        )
        session.commit()

    # Patch the module-level engine used by the route handlers
    import app.main as main_module

    original_engine = main_module.db_engine
    main_module.db_engine = engine

    with TestClient(app, follow_redirects=False) as client:
        yield client

    main_module.db_engine = original_engine
    SQLModel.metadata.drop_all(engine)


# --- /redirect/ tests ---


def test_redirect_known_key_returns_redirect(client):
    response = client.get("/v1/redirect/abc123")
    assert response.status_code in (301, 302, 307, 308)
    assert response.headers["location"] == "https://example.com"


def test_redirect_known_key_location_is_correct(client):
    response = client.get("/v1/redirect/abc123")
    assert "example.com" in response.headers["location"]


def test_redirect_unknown_key_returns_404(client):
    response = client.get("/v1/redirect/doesnotexist")
    assert response.status_code == 404


def test_redirect_unknown_key_error_message(client):
    response = client.get("/v1/redirect/doesnotexist")
    body = response.json()
    assert "doesnotexist" in body["detail"]["error"]
