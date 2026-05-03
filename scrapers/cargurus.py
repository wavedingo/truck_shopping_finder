from __future__ import annotations

import logging
import re
from typing import Optional
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from db import Listing
from scrapers.base import BaseScraper, detect_block, random_delay

logger = logging.getLogger(__name__)

BASE_URL = "https://www.cargurus.com"

# CarGurus updated their SRP in 2025 to a Remix-based /search page.
# Selectors confirmed against live site 2026-05.
# If scraping returns 0 results, inspect the live site and update these.
CARD_SELECTOR = "div[data-testid='srp-listing-tile']"
TITLE_SELECTOR = "h5[class*='_title_']"
PRICE_SELECTOR = "h4[class*='_priceText_']"
MILEAGE_SELECTOR = "p[class*='_mileage_']"
LOCATION_SELECTOR = "div[class*='_locationSectionWithIcon_'] div[class*='_textEllipsis_']"


def _parse_int(text: str) -> Optional[int]:
    digits = re.sub(r"[^\d]", "", text)
    return int(digits) if digits else None


def _extract_year(title: str) -> Optional[int]:
    m = re.match(r"(\d{4})", title.strip())
    return int(m.group(1)) if m else None


def _extract_make_model(title: str) -> tuple[Optional[str], Optional[str]]:
    parts = title.strip().split()
    if len(parts) >= 3:
        return parts[1], parts[2]
    return None, None


def parse_listing_card(card_html: str) -> Optional[Listing]:
    soup = BeautifulSoup(card_html, "html.parser")

    title_el = soup.select_one(TITLE_SELECTOR)
    if not title_el:
        return None

    title = title_el.get_text(strip=True)

    # URL may be on the title element itself or on a dedicated link element.
    href = title_el.get("href", "")
    if not href:
        link_el = soup.select_one("a[data-testid='car-blade-link'], a[href*='/details/']")
        href = link_el.get("href", "") if link_el else ""
    url = urljoin(BASE_URL, href) if href else None
    if not url:
        return None

    price_el = soup.select_one(PRICE_SELECTOR)
    price = _parse_int(price_el.get_text(strip=True)) if price_el else None

    mileage_el = soup.select_one(MILEAGE_SELECTOR)
    mileage = _parse_int(mileage_el.get_text(strip=True)) if mileage_el else None

    location_el = soup.select_one(LOCATION_SELECTOR)
    location = location_el.get_text(strip=True) if location_el else None

    year = _extract_year(title)
    make, model = _extract_make_model(title)

    return Listing(
        site="cargurus.com",
        title=title,
        year=year,
        make=make,
        model=model,
        price=price,
        mileage=mileage,
        location=location,
        url=url,
        vin=None,
    )


class CarGurusScraper(BaseScraper):
    SITE_NAME = "cargurus.com"

    # CarGurus entity IDs for Toyota Tacoma (standard + Hybrid trim paths).
    # m7 = Toyota make, d311 = Tacoma, d3428 = Tacoma Hybrid.
    # These are stable integer IDs assigned by CarGurus; update if the model
    # entity changes (e.g. a new generation gets a new ID).
    CG_TACOMA_TRIM_PATHS = "m7/d311,m7/d3428"

    def _build_url(self, make: str, model: str, page: int) -> str:
        # CarGurus migrated from /Cars/listings/searchResults.action to /search in 2025.
        # The new endpoint uses makeModelTrimPaths (entity IDs) and page-based pagination.
        return (
            f"{BASE_URL}/search"
            f"?makeModelTrimPaths={self.CG_TACOMA_TRIM_PATHS.replace('/', '%2F').replace(',', '%2C')}"
            f"&distance={self.radius}&zip={self.zip_code}"
            f"&maxPrice={self.max_price}&maxMileage={self.max_mileage}"
            f"&startYear={self.year_min}&endYear={self.year_max}"
            f"&sortDirection=ASC&sortType=PRICE"
            + (f"&page={page}" if page > 1 else "")
        )

    async def _scrape_pages(self, page, make: str, model: str) -> tuple[list, list[str], int]:
        listings, errors, pages_fetched = [], [], 0

        for page_num in range(1, self.max_pages + 1):
            url = self._build_url(make, model, page_num)
            logger.info(f"[cargurus] {make} {model} p{page_num}: {url}")
            try:
                await page.goto(url, wait_until="domcontentloaded", timeout=30000)
                await random_delay()
                pages_fetched += 1

                title = await page.title()
                content = await page.content()

                if detect_block(title, content):
                    msg = f"[cargurus] Possible block p{page_num} ({make} {model})"
                    logger.warning(msg)
                    errors.append(msg)
                    break

                cards = await page.query_selector_all(CARD_SELECTOR)
                if not cards:
                    logger.info(f"[cargurus] No listings on p{page_num}, stopping")
                    break

                for card in cards:
                    listing = parse_listing_card(await card.inner_html())
                    if listing:
                        listings.append(listing)

            except Exception as e:
                msg = f"[cargurus] Error p{page_num} ({make} {model}): {e}"
                logger.error(msg)
                errors.append(msg)
                break

        logger.info(f"[cargurus] {make} {model}: {len(listings)} listings, {pages_fetched} pages")
        return listings, errors, pages_fetched
