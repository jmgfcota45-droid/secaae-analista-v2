
import pytest

from data.database import Database


def test_rejects_non_select(tmp_path):
    db = Database(str(tmp_path / "test.duckdb"))
    try:
        with pytest.raises(ValueError):
            db.safe_query("DROP TABLE foo")
    finally:
        db.close()


def test_rejects_multiple_statements(tmp_path):
    db = Database(str(tmp_path / "test.duckdb"))
    try:
        with pytest.raises(ValueError):
            db.safe_query("SELECT 1; SELECT 2")
    finally:
        db.close()


def test_allows_select(tmp_path):
    db = Database(str(tmp_path / "test.duckdb"))
    try:
        result = db.safe_query("SELECT 1 AS valor")
        assert result.iloc[0]["valor"] == 1
    finally:
        db.close()
