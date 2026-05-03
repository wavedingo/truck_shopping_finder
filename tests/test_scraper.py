from __future__ import annotations

from scraper import build_summary_table


def test_summary_table_contains_all_sites():
    stats = {
        "cars.com": {"new": 5, "changes": 1, "pages": 3, "status": "OK"},
        "autotrader.com": {"new": 3, "changes": 0, "pages": 2, "status": "OK"},
        "cargurus.com": {"new": 0, "changes": 0, "pages": 1, "status": "FAILED"},
    }
    table = build_summary_table(stats)
    assert "cars.com" in table
    assert "autotrader.com" in table
    assert "cargurus.com" in table
    assert "FAILED" in table
    assert "TOTAL" in table


def test_summary_table_sums_new_correctly():
    stats = {
        "cars.com": {"new": 5, "changes": 1, "pages": 3, "status": "OK"},
        "autotrader.com": {"new": 3, "changes": 0, "pages": 2, "status": "OK"},
    }
    table = build_summary_table(stats)
    assert "8" in table  # total new = 5 + 3


def test_summary_table_sums_pages_correctly():
    stats = {
        "cars.com": {"new": 2, "changes": 0, "pages": 4, "status": "OK"},
        "autotrader.com": {"new": 1, "changes": 0, "pages": 3, "status": "OK"},
    }
    table = build_summary_table(stats)
    assert "7" in table  # total pages = 4 + 3
