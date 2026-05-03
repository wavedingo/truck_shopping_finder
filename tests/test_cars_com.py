from __future__ import annotations

import pytest
from scrapers.cars_com import parse_listing_card

# This fixture HTML matches the selectors in parse_listing_card.
FIXTURE_HTML = """
<div class="vehicle-card">
  <h2 class="title">
    <a class="vehicle-card-link" href="/vehicledetail/abc123/">2020 Toyota Tacoma SR5</a>
  </h2>
  <span class="primary-price">$32,500</span>
  <div class="mileage">45,000 mi.</div>
  <div class="vehicle-card-location">Stroudsburg, PA</div>
</div>
"""


def test_parse_cars_com_title():
    listing = parse_listing_card(FIXTURE_HTML)
    assert listing is not None
    assert "Tacoma" in listing.title


def test_parse_cars_com_price():
    listing = parse_listing_card(FIXTURE_HTML)
    assert listing.price == 32500


def test_parse_cars_com_mileage():
    listing = parse_listing_card(FIXTURE_HTML)
    assert listing.mileage == 45000


def test_parse_cars_com_url():
    listing = parse_listing_card(FIXTURE_HTML)
    assert "cars.com" in listing.url


def test_parse_cars_com_site_name():
    listing = parse_listing_card(FIXTURE_HTML)
    assert listing.site == "cars.com"


def test_parse_cars_com_returns_none_on_empty():
    listing = parse_listing_card("<div></div>")
    assert listing is None
