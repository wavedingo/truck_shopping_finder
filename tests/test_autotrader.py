from __future__ import annotations

import pytest
from scrapers.autotrader import parse_listing_card

# Fixture HTML matching the selectors in parse_listing_card
FIXTURE_HTML = """
<div class="inventory-listing-thumbs">
  <h2 class="title">
    <a href="/cars-for-sale/listing/abc123">2019 Toyota Tacoma SR5</a>
  </h2>
  <div class="first-price">$29,998</div>
  <div class="text-bold mileage">38,000 miles</div>
  <div class="text-secondary-500">Stroudsburg, PA</div>
</div>
"""


def test_parse_autotrader_title():
    listing = parse_listing_card(FIXTURE_HTML)
    assert listing is not None
    assert "Tacoma" in listing.title


def test_parse_autotrader_price():
    listing = parse_listing_card(FIXTURE_HTML)
    assert listing.price == 29998


def test_parse_autotrader_mileage():
    listing = parse_listing_card(FIXTURE_HTML)
    assert listing.mileage == 38000


def test_parse_autotrader_url():
    listing = parse_listing_card(FIXTURE_HTML)
    assert "autotrader.com" in listing.url


def test_parse_autotrader_site_name():
    listing = parse_listing_card(FIXTURE_HTML)
    assert listing.site == "autotrader.com"


def test_parse_autotrader_returns_none_on_empty():
    listing = parse_listing_card("<div></div>")
    assert listing is None
