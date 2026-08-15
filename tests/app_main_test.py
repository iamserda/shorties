from __future__ import annotations

import app.main as main_module
import pytest
from app.db.models.models import ShortiLink
from app.main import app
from fastapi.testclient import TestClient
from sqlalchemy.pool import StaticPool
from sqlmodel import create_engine
from sqlmodel import delete
from sqlmodel import Session
from sqlmodel import SQLModel

client = TestClient(app)
API_VERSION = "v1"
LINKS_URL = f"/{API_VERSION}/links/"
HEALTHZ_URL = f"/{API_VERSION}/healthz/"


@pytest.fixture(scope="module", autouse=True)
def isolated_test_engine():
    """Force every route in this module onto a throwaway in-memory engine.

    Routes in main.py read the module-level `app.main.db_engine` global
    directly rather than via dependency injection, and that global can point
    at a real (e.g. Postgres) database via DEV_DATABASE_URL. Tests must NEVER
    touch that database, so we swap the global for a dedicated StaticPool
    sqlite engine for the duration of this module and restore it afterward,
    regardless of what .env configures.
    """
    test_engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    SQLModel.metadata.create_all(test_engine)

    original_engine = main_module.db_engine
    main_module.db_engine = test_engine
    try:
        yield test_engine
    finally:
        main_module.db_engine = original_engine


@pytest.fixture(autouse=True)
def clean_links_table(isolated_test_engine):
    with Session(isolated_test_engine) as session:
        session.exec(delete(ShortiLink))
        session.commit()
    yield


def insert_link(
    engine, shorti_key: str, shorti_url: str, brand: str | None = None
) -> None:
    with Session(engine) as session:
        session.add(
            ShortiLink(shorti_key=shorti_key, shorti_url=shorti_url, brand=brand)
        )
        session.commit()


class TestHealthz:
    def test_returns_200_and_alive_status(self):
        response = client.get(HEALTHZ_URL)

        assert response.status_code == 200
        assert response.json() == {"status": "alive"}


class TestGetAllLinks:
    def test_returns_empty_list_when_database_has_no_links(self):
        response = client.get(LINKS_URL)

        assert response.status_code == 200
        assert response.json() == {"urls": []}

    def test_returns_all_links_present_in_database(self, isolated_test_engine):
        insert_link(
            isolated_test_engine, "abc123", "https://example.com/one", brand="acme"
        )
        insert_link(
            isolated_test_engine, "def456", "https://example.com/two", brand=None
        )

        response = client.get(LINKS_URL)

        assert response.status_code == 200
        body = response.json()
        assert len(body["urls"]) == 2
        keys = {item["key"] for item in body["urls"]}
        assert keys == {"abc123", "def456"}
        by_key = {item["key"]: item for item in body["urls"]}
        assert by_key["abc123"]["url"] == "https://example.com/one"
        assert by_key["abc123"]["brand"] == "acme"
        assert by_key["abc123"]["hit_count"] == 0
        assert by_key["def456"]["brand"] is None

    def test_respects_limit_query_parameter(self, isolated_test_engine):
        for i in range(5):
            insert_link(isolated_test_engine, f"key{i}", f"https://example.com/{i}")

        response = client.get(LINKS_URL, params={"limit": 2})

        assert response.status_code == 200
        assert len(response.json()["urls"]) == 2

    def test_respects_offset_query_parameter(self, isolated_test_engine):
        for i in range(5):
            insert_link(isolated_test_engine, f"key{i}", f"https://example.com/{i}")

        first_page = client.get(LINKS_URL, params={"offset": 0, "limit": 5}).json()[
            "urls"
        ]
        second_page = client.get(LINKS_URL, params={"offset": 3, "limit": 5}).json()[
            "urls"
        ]

        assert len(second_page) == 2
        first_keys = {item["key"] for item in first_page}
        second_keys = {item["key"] for item in second_page}
        assert second_keys.issubset(first_keys)

    def test_rejects_limit_above_maximum(self):
        response = client.get(LINKS_URL, params={"limit": 21})

        assert response.status_code == 422

    def test_rejects_negative_offset(self):
        response = client.get(LINKS_URL, params={"offset": -1})

        assert response.status_code == 422

    def test_default_limit_is_twenty(self, isolated_test_engine):
        for i in range(25):
            insert_link(isolated_test_engine, f"key{i}", f"https://example.com/{i}")

        response = client.get(LINKS_URL)

        assert response.status_code == 200
        assert len(response.json()["urls"]) == 20

    def test_returns_500_when_db_engine_is_unavailable(self, monkeypatch):
        monkeypatch.setattr("app.main.db_engine", None)

        response = client.get(LINKS_URL)

        assert response.status_code == 500
        detail = response.json()["detail"]
        assert detail["error"]["type"] == "DBEngineError"
        assert detail["error"]["status-code"] == 500
