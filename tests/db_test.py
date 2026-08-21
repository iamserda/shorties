from __future__ import annotations

import pytest
from app.db.db import db_engine_factory


def test_db_engine_factory_creates_engine_for_valid_url():
    engine = db_engine_factory(db_url="sqlite://")
    assert engine is not None


def test_db_engine_factory_raises_type_error_for_non_string_url():
    with pytest.raises(TypeError):
        db_engine_factory(db_url=None)


def test_db_engine_factory_raises_value_error_for_empty_url():
    with pytest.raises(ValueError):
        db_engine_factory(db_url="")
