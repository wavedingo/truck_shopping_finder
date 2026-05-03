from __future__ import annotations

import pytest
from scrapers.cargurus import parse_listing_card

# Fixture HTML matching the selectors in parse_listing_card.
# CarGurus migrated to a Remix /search SRP in 2025 (updated fixture 2026-05).
FIXTURE_HTML = """
<div data-testid="srp-listing-tile">
  <a data-testid="car-blade-link" href="/details/123456?zip=18301">
    <div>
      <h5 class="_title_84nkk_1">2021 Toyota Tacoma SR5</h5>
      <h4 class="_priceText_fjflh_1">$34,995</h4>
      <p class="_mileage_84nkk_9">22,000 mi</p>
      <div class="_locationSectionWithIcon_eclgi_13">
        <div class="_textEllipsis_eclgi_8">Stroudsburg, PA</div>
        <div class="_textEllipsis_eclgi_8">5 mi away</div>
      </div>
    </div>
  </a>
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
