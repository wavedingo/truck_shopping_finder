from __future__ import annotations

import pytest
import sqlite3
from pathlib import Path
from db import Database, Listing


@pytest.fixture
def tmp_db(tmp_path):
    db = Database(str(tmp_path / "test.db"))
    yield db
    db.close()


def make_listing(**kwargs):
    defaults = dict(
        site="cars.com",
        title="2020 Toyota Tacoma SR5",
        year=2020,
        make="Toyota",
        model="Tacoma",
        price=32000,
        mileage=45000,
        location="East Stroudsburg, PA",
        url="https://cars.com/vehicledetail/abc123/",
        vin="1NXBR32E85Z123456",
    )
    defaults.update(kwargs)
    return Listing(**defaults)


def test_schema_creates_listings_table(tmp_db):
    row = tmp_db.conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='listings'"
    ).fetchone()
    assert row is not None


def test_schema_creates_runs_table(tmp_db):
    row = tmp_db.conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='runs'"
    ).fetchone()
    assert row is not None


def test_insert_new_listing_returns_new(tmp_db):
    run_ts = "2026-05-02T07:00:00+00:00"
    result = tmp_db.upsert_listing(make_listing(), run_ts)
    assert result == "new"


def test_same_vin_returns_existing(tmp_db):
    run_ts = "2026-05-02T07:00:00+00:00"
    tmp_db.upsert_listing(make_listing(), run_ts)
    result = tmp_db.upsert_listing(make_listing(), run_ts)
    assert result == "existing"


def test_price_change_via_vin_returns_price_changed(tmp_db):
    run_ts = "2026-05-02T07:00:00+00:00"
    tmp_db.upsert_listing(make_listing(price=32000), run_ts)
    result = tmp_db.upsert_listing(make_listing(price=30000), run_ts)
    assert result == "price_changed"


def test_price_change_stores_previous_price(tmp_db):
    run_ts = "2026-05-02T07:00:00+00:00"
    tmp_db.upsert_listing(make_listing(price=32000), run_ts)
    tmp_db.upsert_listing(make_listing(price=30000), run_ts)
    row = tmp_db.conn.execute(
        "SELECT price, previous_price FROM listings WHERE vin = ?",
        ("1NXBR32E85Z123456",)
    ).fetchone()
    assert row["price"] == 30000
    assert row["previous_price"] == 32000


def test_url_dedup_when_no_vin(tmp_db):
    run_ts = "2026-05-02T07:00:00+00:00"
    listing = make_listing(vin=None)
    tmp_db.upsert_listing(listing, run_ts)
    result = tmp_db.upsert_listing(listing, run_ts)
    assert result == "existing"


def test_title_mileage_dedup_detects_price_change(tmp_db):
    run_ts = "2026-05-02T07:00:00+00:00"
    listing = make_listing(vin=None, url="https://cars.com/abc")
    tmp_db.upsert_listing(listing, run_ts)
    # Different URL forces title+mileage fallback; price changed so expect price_changed
    listing2 = make_listing(vin=None, url="https://cars.com/xyz", price=30000)
    result = tmp_db.upsert_listing(listing2, run_ts)
    assert result == "price_changed"


def test_export_csv_contains_new_listings(tmp_db, tmp_path):
    run_ts = "2026-05-02T07:00:00+00:00"
    tmp_db.upsert_listing(make_listing(), run_ts)
    out = tmp_path / "out.csv"
    tmp_db.export_new_listings_csv(run_ts, str(out))
    content = out.read_text()
    assert "Toyota Tacoma" in content
    assert "date_scraped" in content  # CSV header uses date_scraped not first_seen


def test_export_csv_excludes_earlier_runs(tmp_db, tmp_path):
    old_ts = "2026-05-01T07:00:00+00:00"
    new_ts = "2026-05-02T07:00:00+00:00"
    tmp_db.upsert_listing(make_listing(title="Old Car", vin="VIN1"), old_ts)
    out = tmp_path / "out.csv"
    tmp_db.export_new_listings_csv(new_ts, str(out))
    assert "Old Car" not in out.read_text()


def test_start_run_returns_int(tmp_db):
    run_id = tmp_db.start_run()
    assert isinstance(run_id, int)


def test_finish_run_persists_stats(tmp_db):
    run_id = tmp_db.start_run()
    tmp_db.finish_run(run_id, sites=["cars.com"], new=5, changes=2, errors=["err"])
    row = tmp_db.conn.execute(
        "SELECT new_listings_found, price_changes_found, errors FROM runs WHERE id = ?",
        (run_id,)
    ).fetchone()
    assert row["new_listings_found"] == 5
    assert row["price_changes_found"] == 2
    assert "err" in row["errors"]


def test_get_price_changes_returns_changed_rows(tmp_db):
    run_ts = "2026-05-02T07:00:00+00:00"
    tmp_db.upsert_listing(make_listing(price=32000), run_ts)
    tmp_db.upsert_listing(make_listing(price=30000), run_ts)
    changes = tmp_db.get_price_changes(run_ts)
    assert len(changes) == 1
    assert changes[0]["price"] == 30000
    assert changes[0]["price_changed_at"] == run_ts  # verify deterministic timestamp
