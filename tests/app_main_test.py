from __future__ import annotations

import pytest
from app.db.models.models import ShortiLink
from app.db.session import get_db_engine
from app.main import app
from fastapi.testclient import TestClient
from sqlalchemy.exc import SQLAlchemyError
from sqlmodel import create_engine
from sqlmodel import delete
from sqlmodel import Session
from sqlmodel import SQLModel
from sqlmodel import StaticPool


TEST_DB_URL = "sqlite://"  # in-memory, discarded after each test


@pytest.fixture(name="engine")
def engine_fixture():
    engine = create_engine(
        TEST_DB_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)

    try:
        yield engine
    finally:
        SQLModel.metadata.drop_all(engine)


@pytest.fixture(name="client")
def client_fixture(engine):
    with Session(engine) as session:
        session.add(
            ShortiLink(
                shorti_key="abc123", shorti_url="https://example.com", brand="example"
            )
        )
        session.commit()

    original_override = app.dependency_overrides.get(get_db_engine)
    app.dependency_overrides[get_db_engine] = lambda: engine

    try:
        with TestClient(app, follow_redirects=False) as client:
            yield client
    finally:
        if original_override is None:
            app.dependency_overrides.pop(get_db_engine, None)
        else:
            app.dependency_overrides[get_db_engine] = original_override


# --- /links tests ---


def test_get_all_links_empty_database_returns_empty_list(client, engine):
    with Session(engine) as session:
        session.exec(delete(ShortiLink))
        session.commit()

    response = client.get("/v1/links")

    assert response.status_code == 200
    assert response.json() == []


def test_get_all_links_unavailable_engine_returns_structured_error(client):
    app.dependency_overrides[get_db_engine] = lambda: None

    response = client.get("/v1/links")

    assert response.status_code == 500
    assert response.json()["detail"]["error"]["type"] == "DBEngineError"


def test_get_all_links_session_failure_returns_structured_error(client, monkeypatch):
    def failing_session(_engine):
        raise SQLAlchemyError("session failed")

    monkeypatch.setattr("app.api.routes.links.Session", failing_session)

    response = client.get("/v1/links")

    assert response.status_code == 500
    assert response.json()["detail"]["error"]["type"] == "DBSessionError"


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
