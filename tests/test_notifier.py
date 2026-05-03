from __future__ import annotations
from unittest.mock import MagicMock
from notifier import build_subject, build_email_html


def make_row(**kwargs):
    defaults = dict(
        title="2020 Toyota Tacoma SR5", site="cars.com", price=32000,
        previous_price=None, mileage=45000, location="East Stroudsburg, PA",
        url="https://cars.com/abc", year=2020, make="Toyota", model="Tacoma",
    )
    defaults.update(kwargs)
    row = MagicMock()
    data = defaults
    row.__getitem__ = lambda self, key: data[key]
    return row


def test_subject_new_only():
    s = build_subject(new_count=4, change_count=0, date_str="May 2")
    assert "4 new" in s
    assert "change" not in s.lower()


def test_subject_with_changes():
    s = build_subject(new_count=2, change_count=3, date_str="May 2")
    assert "2 new" in s
    assert "3 price" in s


def test_subject_changes_only():
    s = build_subject(new_count=0, change_count=1, date_str="May 2")
    assert "1 price" in s


def test_email_html_new_listings_section():
    html = build_email_html(new_listings=[make_row()], price_changes=[], site_stats={})
    assert "New Listings" in html
    assert "Tacoma" in html
    assert "cars.com" in html


def test_email_html_price_changes_section():
    row = make_row(price=30000, previous_price=32000)
    html = build_email_html(new_listings=[], price_changes=[row], site_stats={})
    assert "Price Changes" in html
    assert "32,000" in html or "$32,000" in html
    assert "30,000" in html or "$30,000" in html


def test_email_html_footer_shows_site_status():
    stats = {"cars.com": {"new": 5, "changes": 1, "pages": 3, "status": "OK"}}
    html = build_email_html(new_listings=[], price_changes=[], site_stats=stats)
    assert "cars.com" in html
    assert "OK" in html


def test_email_html_footer_shows_failed_status():
    stats = {"autotrader.com": {"new": 0, "changes": 0, "pages": 0, "status": "FAILED"}}
    html = build_email_html(new_listings=[], price_changes=[], site_stats=stats)
    assert "FAILED" in html
