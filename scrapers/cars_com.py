from __future__ import annotations

import logging
import re
from typing import Optional
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from db import Listing
from scrapers.base import BaseScraper, detect_block, random_delay

logger = logging.getLogger(__name__)

BASE_URL = "https://www.cars.com"

# These selectors match Cars.com's current listing card structure (updated 2026-05).
# Cars.com now uses custom Web Components (<fuse-card>) with data-listing-id attributes.
# If scraping returns 0 results, inspect the live site and update these.
CARD_SELECTOR = "fuse-card[data-listing-id]"
TITLE_SELECTOR = "h2 a"
PRICE_SELECTOR = "span.fuse-body-larger"
MILEAGE_SELECTOR = "div.datum-icon.mileage span"
LOCATION_SELECTOR = "div[slot='footer'] div.datum-icon span"


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
    href = title_el.get("href", "")
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
        site="cars.com",
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


class CarsComScraper(BaseScraper):
    SITE_NAME = "cars.com"

    def _build_url(self, make: str, model: str, page: int) -> str:
        make_slug = make.lower().replace(" ", "-")
        model_slug = f"{make_slug}-{model.lower().replace(' ', '-')}"
        return (
            f"{BASE_URL}/shopping/results/"
            f"?makes[]={make_slug}&models[]={model_slug}"
            f"&list_price_max={self.max_price}"
            f"&mileage_max={self.max_mileage}"
            f"&year_min={self.year_min}&year_max={self.year_max}"
            f"&range={self.radius}&zip={self.zip_code}"
            f"&page={page}&page_size=20&stock_type=used&sort=best_match_desc"
        )

    async def _scrape_pages(self, page, make: str, model: str) -> tuple[list, list[str], int]:
        listings, errors, pages_fetched = [], [], 0

        for page_num in range(1, self.max_pages + 1):
            url = self._build_url(make, model, page_num)
            logger.info(f"[cars.com] {make} {model} p{page_num}: {url}")
            try:
                await page.goto(url, wait_until="domcontentloaded", timeout=30000)
                await random_delay()
                pages_fetched += 1

                title = await page.title()
                content = await page.content()

                if detect_block(title, content):
                    msg = f"[cars.com] Possible block p{page_num} ({make} {model})"
                    logger.warning(msg)
                    errors.append(msg)
                    break

                cards = await page.query_selector_all(CARD_SELECTOR)
                if not cards:
                    logger.info(f"[cars.com] No listings on p{page_num}, stopping")
                    break

                for card in cards:
                    listing = parse_listing_card(await card.inner_html())
                    if listing:
                        listings.append(listing)

            except Exception as e:
                msg = f"[cars.com] Error p{page_num} ({make} {model}): {e}"
                logger.error(msg)
                errors.append(msg)
                break

        logger.info(f"[cars.com] {make} {model}: {len(listings)} listings, {pages_fetched} pages")
        return listings, errors, pages_fetched
