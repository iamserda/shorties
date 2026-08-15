from __future__ import annotations

import app.main as main_module
import pytest
from app.db.models.models import LinkClickEvent
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


@pytest.fixture(scope="module", autouse=True)
def isolated_test_engine():
    """Force every route in this module onto a throwaway in-memory engine.

    See tests/app_main_test.py for why this is necessary: routes resolve
    their session from the module-level `app.main.db_engine`, which can
    point at a real DB via DEV_DATABASE_URL. Tests must never touch that.
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
def clean_tables(isolated_test_engine):
    with Session(isolated_test_engine) as session:
        session.exec(delete(LinkClickEvent))
        session.exec(delete(ShortiLink))
        session.commit()
    yield


def insert_link(engine, **overrides) -> ShortiLink:
    defaults = {
        "shorti_key": "abc123",
        "shorti_url": "https://example.com/one",
        "brand": None,
        "redirect_code": 307,
    }
    defaults.update(overrides)
    with Session(engine) as session:
        link = ShortiLink(**defaults)
        session.add(link)
        session.commit()
        session.refresh(link)
        return link


class TestCreateLink:
    def test_creates_link_and_returns_generated_key(self):
        response = client.post(
            LINKS_URL, json={"url": "https://example.com/x", "brand": "acme"}
        )

        assert response.status_code == 201
        body = response.json()
        assert body["url"] == "https://example.com/x"
        assert body["brand"] == "acme"
        assert body["redirect_code"] == 307
        assert body["hit_count"] == 0
        assert body["last_accessed_at"] is None
        assert len(body["key"]) > 0

    def test_persists_custom_redirect_code(self):
        response = client.post(
            LINKS_URL, json={"url": "https://example.com/x", "redirect_code": 302}
        )

        assert response.status_code == 201
        assert response.json()["redirect_code"] == 302

    def test_rejects_invalid_redirect_code(self):
        response = client.post(
            LINKS_URL, json={"url": "https://example.com/x", "redirect_code": 418}
        )

        assert response.status_code == 422

    def test_created_link_is_immediately_listable(self):
        create_response = client.post(LINKS_URL, json={"url": "https://example.com/x"})
        key = create_response.json()["key"]

        list_response = client.get(LINKS_URL)

        keys = {item["key"] for item in list_response.json()["urls"]}
        assert key in keys


class TestGetLink:
    def test_returns_link_by_key(self, isolated_test_engine):
        insert_link(isolated_test_engine, shorti_key="abc123", brand="acme")

        response = client.get(f"{LINKS_URL}abc123")

        assert response.status_code == 200
        body = response.json()
        assert body["key"] == "abc123"
        assert body["brand"] == "acme"

    def test_returns_404_for_missing_key(self):
        response = client.get(f"{LINKS_URL}doesnotexist")

        assert response.status_code == 404

    def test_returns_404_for_soft_deleted_link(self, isolated_test_engine):
        insert_link(isolated_test_engine, shorti_key="abc123")
        client.delete(f"{LINKS_URL}abc123")

        response = client.get(f"{LINKS_URL}abc123")

        assert response.status_code == 404


class TestUpdateLink:
    def test_updates_url_and_brand(self, isolated_test_engine):
        insert_link(isolated_test_engine, shorti_key="abc123", brand="old")

        response = client.put(
            f"{LINKS_URL}abc123",
            json={"url": "https://example.com/new", "brand": "new"},
        )

        assert response.status_code == 200
        body = response.json()
        assert body["url"] == "https://example.com/new"
        assert body["brand"] == "new"

    def test_partial_update_leaves_other_fields_untouched(self, isolated_test_engine):
        insert_link(
            isolated_test_engine,
            shorti_key="abc123",
            shorti_url="https://example.com/one",
            brand="acme",
        )

        response = client.put(f"{LINKS_URL}abc123", json={"brand": "newbrand"})

        assert response.status_code == 200
        body = response.json()
        assert body["url"] == "https://example.com/one"
        assert body["brand"] == "newbrand"

    def test_updates_redirect_code(self, isolated_test_engine):
        insert_link(isolated_test_engine, shorti_key="abc123", redirect_code=307)

        response = client.put(f"{LINKS_URL}abc123", json={"redirect_code": 301})

        assert response.status_code == 200
        assert response.json()["redirect_code"] == 301

    def test_bumps_updated_at(self, isolated_test_engine):
        link = insert_link(isolated_test_engine, shorti_key="abc123")
        original_updated_at = link.updated_at

        response = client.put(f"{LINKS_URL}abc123", json={"brand": "new"})

        assert response.status_code == 200
        new_updated_at = response.json()["updated_at"]
        assert new_updated_at != original_updated_at.isoformat()

    def test_returns_404_for_missing_key(self):
        response = client.put(f"{LINKS_URL}doesnotexist", json={"brand": "x"})

        assert response.status_code == 404

    def test_returns_404_for_soft_deleted_link(self, isolated_test_engine):
        insert_link(isolated_test_engine, shorti_key="abc123")
        client.delete(f"{LINKS_URL}abc123")

        response = client.put(f"{LINKS_URL}abc123", json={"brand": "x"})

        assert response.status_code == 404


class TestDeleteLink:
    def test_soft_deletes_link(self, isolated_test_engine):
        insert_link(isolated_test_engine, shorti_key="abc123")

        response = client.delete(f"{LINKS_URL}abc123")

        assert response.status_code == 204
        with Session(isolated_test_engine) as session:
            link = session.get(ShortiLink, 1)
            assert link is not None
            assert link.deleted_at is not None

    def test_deleted_link_is_hidden_from_default_list(self, isolated_test_engine):
        insert_link(isolated_test_engine, shorti_key="abc123")
        client.delete(f"{LINKS_URL}abc123")

        response = client.get(LINKS_URL)

        assert response.json() == {"urls": []}

    def test_deleted_link_is_visible_with_include_deleted(self, isolated_test_engine):
        insert_link(isolated_test_engine, shorti_key="abc123")
        client.delete(f"{LINKS_URL}abc123")

        response = client.get(LINKS_URL, params={"include_deleted": True})

        keys = {item["key"] for item in response.json()["urls"]}
        assert keys == {"abc123"}

    def test_returns_404_for_missing_key(self):
        response = client.delete(f"{LINKS_URL}doesnotexist")

        assert response.status_code == 404

    def test_is_idempotent_second_delete_returns_404(self, isolated_test_engine):
        insert_link(isolated_test_engine, shorti_key="abc123")

        first = client.delete(f"{LINKS_URL}abc123")
        second = client.delete(f"{LINKS_URL}abc123")

        assert first.status_code == 204
        assert second.status_code == 404


class TestVisitLink:
    def test_redirects_to_target_url_with_stored_status_code(
        self, isolated_test_engine
    ):
        insert_link(
            isolated_test_engine,
            shorti_key="abc123",
            shorti_url="https://example.com/target",
            redirect_code=302,
        )

        response = client.get(f"{LINKS_URL}abc123/visit", follow_redirects=False)

        assert response.status_code == 302
        assert response.headers["location"] == "https://example.com/target"

    def test_increments_hit_count_and_sets_last_accessed_at(self, isolated_test_engine):
        insert_link(isolated_test_engine, shorti_key="abc123")

        client.get(f"{LINKS_URL}abc123/visit", follow_redirects=False)
        client.get(f"{LINKS_URL}abc123/visit", follow_redirects=False)

        link_response = client.get(f"{LINKS_URL}abc123")
        body = link_response.json()
        assert body["hit_count"] == 2
        assert body["last_accessed_at"] is not None

    def test_records_click_event_with_referrer_and_user_agent(
        self, isolated_test_engine
    ):
        insert_link(isolated_test_engine, shorti_key="abc123")

        client.get(
            f"{LINKS_URL}abc123/visit",
            follow_redirects=False,
            headers={"referer": "https://ref.example", "user-agent": "pytest-agent"},
        )

        analytics = client.get(f"{LINKS_URL}abc123/analytics").json()
        assert len(analytics["recent_clicks"]) == 1
        click = analytics["recent_clicks"][0]
        assert click["referrer"] == "https://ref.example"
        assert click["user_agent"] == "pytest-agent"

    def test_returns_404_for_missing_key(self):
        response = client.get(f"{LINKS_URL}doesnotexist/visit", follow_redirects=False)

        assert response.status_code == 404

    def test_returns_404_for_soft_deleted_link(self, isolated_test_engine):
        insert_link(isolated_test_engine, shorti_key="abc123")
        client.delete(f"{LINKS_URL}abc123")

        response = client.get(f"{LINKS_URL}abc123/visit", follow_redirects=False)

        assert response.status_code == 404


class TestLinkAnalytics:
    def test_returns_zeroed_analytics_for_unvisited_link(self, isolated_test_engine):
        insert_link(isolated_test_engine, shorti_key="abc123")

        response = client.get(f"{LINKS_URL}abc123/analytics")

        assert response.status_code == 200
        body = response.json()
        assert body["key"] == "abc123"
        assert body["hit_count"] == 0
        assert body["last_accessed_at"] is None
        assert body["recent_clicks"] == []

    def test_recent_clicks_are_ordered_most_recent_first(self, isolated_test_engine):
        insert_link(isolated_test_engine, shorti_key="abc123")

        client.get(
            f"{LINKS_URL}abc123/visit",
            follow_redirects=False,
            headers={"user-agent": "first"},
        )
        client.get(
            f"{LINKS_URL}abc123/visit",
            follow_redirects=False,
            headers={"user-agent": "second"},
        )

        response = client.get(f"{LINKS_URL}abc123/analytics")

        clicks = response.json()["recent_clicks"]
        assert [c["user_agent"] for c in clicks] == ["second", "first"]

    def test_returns_404_for_missing_key(self):
        response = client.get(f"{LINKS_URL}doesnotexist/analytics")

        assert response.status_code == 404
