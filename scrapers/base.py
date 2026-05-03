from __future__ import annotations

import asyncio
import random

USER_AGENTS = [
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4.1 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:125.0) Gecko/20100101 Firefox/125.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14.4; rv:125.0) Gecko/20100101 Firefox/125.0",
]

BLOCK_SIGNALS = [
    "just a moment",
    "checking your browser",
    "enable javascript and cookies",
    "access denied",
    "403 forbidden",
    "429 too many requests",
]


def rotate_user_agent() -> str:
    return random.choice(USER_AGENTS)


async def random_delay():
    await asyncio.sleep(random.uniform(2.0, 4.0))


def detect_block(title: str, body_text: str) -> bool:
    for signal in BLOCK_SIGNALS:
        if signal in title.lower() or signal in body_text.lower()[:500]:
            return True
    return len(body_text.strip()) < 100


class BaseScraper:
    SITE_NAME = "base"

    def __init__(self, zip_code: str, radius: int, year_min: int, year_max: int,
                 max_price: int, max_mileage: int, max_pages: int = 5):
        self.zip_code = zip_code
        self.radius = radius
        self.year_min = year_min
        self.year_max = year_max
        self.max_price = max_price
        self.max_mileage = max_mileage
        self.max_pages = max_pages

    async def scrape(self, make: str, model: str, browser) -> tuple[list, list[str], int]:
        """Returns (listings, errors, pages_fetched)."""
        from playwright_stealth import stealth_async

        context = await browser.new_context(
            user_agent=rotate_user_agent(),
            viewport={"width": random.randint(1280, 1440), "height": random.randint(800, 900)},
            locale="en-US",
        )
        page = await context.new_page()
        await stealth_async(page)
        try:
            return await self._scrape_pages(page, make, model)
        finally:
            await context.close()

    async def _scrape_pages(self, page, make: str, model: str) -> tuple[list, list[str], int]:
        raise NotImplementedError
