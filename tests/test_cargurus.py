from __future__ import annotations

import pytest
from scrapers.cargurus import parse_listing_card

# Fixture HTML matching the selectors in parse_listing_card.
# CarGurus uses data-testid attributes for stability.
FIXTURE_HTML = """
<div data-testid="listing-card">
  <a data-testid="car-blade-link" href="/Cars/new/nl_New_d2417_z18301?listing=123">
    2021 Toyota Tacoma SR5
  </a>
  <span data-testid="price">$34,995</span>
  <span data-testid="mileage">22,000 mi</span>
  <span data-testid="seller-location">Stroudsburg, PA</span>
</div>
"""


def test_parse_cargurus_title():
    listing = parse_listing_card(FIXTURE_HTML)
    assert listing is not None
    assert "Tacoma" in listing.title


def test_parse_cargurus_price():
    listing = parse_listing_card(FIXTURE_HTML)
    assert listing.price == 34995


def test_parse_cargurus_mileage():
    listing = parse_listing_card(FIXTURE_HTML)
    assert listing.mileage == 22000


def test_parse_cargurus_url():
    listing = parse_listing_card(FIXTURE_HTML)
    assert "cargurus.com" in listing.url


def test_parse_cargurus_site_name():
    listing = parse_listing_card(FIXTURE_HTML)
    assert listing.site == "cargurus.com"


def test_parse_cargurus_returns_none_on_empty():
    listing = parse_listing_card("<div></div>")
    assert listing is None
