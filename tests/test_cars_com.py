from __future__ import annotations

import pytest
from scrapers.cars_com import parse_listing_card

# This fixture HTML matches the selectors in parse_listing_card.
# Cars.com now renders listings as <fuse-card> Web Components (updated 2026-05).
FIXTURE_HTML = """
<fuse-card data-listing-id="abc123" layout="vertical">
  <div>
    <h2>
      <a href="https://www.cars.com/vehicledetail/abc123/" data-card-link="">
        2020 Toyota Tacoma SR5
      </a>
    </h2>
    <span class="fuse-body-larger">$32,500</span>
    <div class="datum-icon mileage">
      <span>45,000 mi.</span>
    </div>
  </div>
  <div slot="footer">
    <div class="datum-icon">
      <span>Stroudsburg, PA</span>
    </div>
  </div>
</fuse-card>
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
