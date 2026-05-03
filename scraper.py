from __future__ import annotations

import argparse
import asyncio
import logging
import sys
from datetime import datetime, timezone

from playwright.async_api import async_playwright
from tabulate import tabulate

from config import DEFAULTS
from db import Database
from notifier import send_digest
from scrapers.cars_com import CarsComScraper
from scrapers.autotrader import AutoTraderScraper
from scrapers.cargurus import CarGurusScraper


def setup_logging(log_path: str):
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[
            logging.FileHandler(log_path, mode="a"),
            logging.StreamHandler(sys.stdout),
        ],
    )


def build_summary_table(stats: dict) -> str:
    rows = []
    total_new = total_changes = total_pages = 0
    for site, s in stats.items():
        rows.append([site, s["new"], s["changes"], s["pages"], s["status"]])
        total_new += s["new"]
        total_changes += s["changes"]
        total_pages += s["pages"]
    rows.append(["TOTAL", total_new, total_changes, total_pages, ""])
    return tabulate(rows, headers=["Site", "New", "Price Changes", "Pages", "Status"])


_STATUS_PRIORITY = {"FAILED": 2, "WARN": 1, "OK": 0}

def _merge_status(current: str, new: str) -> str:
    """Only degrade status, never upgrade (FAILED > WARN > OK)."""
    return new if _STATUS_PRIORITY.get(new, 0) > _STATUS_PRIORITY.get(current, 0) else current


async def _run_one(scraper, make, model, browser, db, run_ts):
    listings, errors, pages = await scraper.scrape(make, model, browser)
    new_count = change_count = 0
    for listing in listings:
        result = db.upsert_listing(listing, run_ts)
        if result == "new":
            new_count += 1
        elif result == "price_changed":
            change_count += 1
    return new_count, change_count, errors, pages


async def main(args):
    setup_logging(args.log_path)
    logger = logging.getLogger(__name__)

    make_models = [(args.make, args.model)] if (args.make and args.model) else DEFAULTS["make_models"]

    db = Database(args.db_path)
    run_id = db.start_run()
    run_ts = datetime.now(timezone.utc).isoformat()
    logger.info(f"Run started: {run_ts}")

    scraper_kwargs = dict(
        zip_code=args.zip,
        radius=args.radius,
        year_min=DEFAULTS["year_min"],
        year_max=DEFAULTS["year_max"],
        max_price=args.max_price,
        max_mileage=DEFAULTS["max_mileage"],
        max_pages=DEFAULTS["max_pages"],
    )
    site_scrapers = [
        CarsComScraper(**scraper_kwargs),
        AutoTraderScraper(**scraper_kwargs),
        CarGurusScraper(**scraper_kwargs),
    ]

    stats: dict = {}
    all_errors: list = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)

        coros = [
            _run_one(scraper, make, model, browser, db, run_ts)
            for scraper in site_scrapers
            for make, model in make_models
        ]
        labels = [
            (scraper.SITE_NAME, make, model)
            for scraper in site_scrapers
            for make, model in make_models
        ]

        results = await asyncio.gather(*coros, return_exceptions=True)

        for (site, make, model), result in zip(labels, results):
            if site not in stats:
                stats[site] = {"new": 0, "changes": 0, "pages": 0, "status": "OK"}
            if isinstance(result, Exception):
                stats[site]["status"] = _merge_status(stats[site]["status"], "FAILED")
                all_errors.append(f"[{site}] {make} {model}: {result}")
                logger.error(f"[{site}] {make} {model} failed: {result}")
            else:
                new_count, change_count, errors, pages = result
                stats[site]["new"] += new_count
                stats[site]["changes"] += change_count
                stats[site]["pages"] += pages
                if errors:
                    stats[site]["status"] = _merge_status(stats[site]["status"], "WARN")
                    all_errors.extend(errors)

        await browser.close()

    db.export_new_listings_csv(run_ts, args.csv_path, sort_by=args.sort)

    total_new = sum(s["new"] for s in stats.values())
    total_changes = sum(s["changes"] for s in stats.values())

    db.finish_run(
        run_id,
        sites=list(stats.keys()),
        new=total_new,
        changes=total_changes,
        errors=all_errors,
    )

    print(build_summary_table(stats))
    logger.info(f"Run complete: {total_new} new, {total_changes} price changes")

    if total_new > 0 or total_changes > 0:
        new_listings = db.get_new_listings(run_ts)
        price_changes = db.get_price_changes(run_ts)
        try:
            send_digest(
                new_listings=new_listings,
                price_changes=price_changes,
                site_stats=stats,
                credentials_path=DEFAULTS["gmail_credentials_path"],
                token_path=DEFAULTS["gmail_token_path"],
            )
            logger.info("Email digest sent.")
        except Exception as e:
            logger.error(f"Failed to send email digest: {e}")

    db.close()


def parse_args():
    parser = argparse.ArgumentParser(description="Truck/SUV listing scraper")
    parser.add_argument("--make", help="Override make (use with --model to replace full list)")
    parser.add_argument("--model", help="Override model (use with --make)")
    parser.add_argument("--max-price", type=int, default=DEFAULTS["max_price"], dest="max_price")
    parser.add_argument("--zip", default=DEFAULTS["zip_code"])
    parser.add_argument("--radius", type=int, default=DEFAULTS["radius"])
    parser.add_argument("--sort", choices=["price", "mileage"], default=None)
    parser.add_argument("--db-path", default=DEFAULTS["db_path"], dest="db_path")
    parser.add_argument("--csv-path", default=DEFAULTS["csv_path"], dest="csv_path")
    parser.add_argument("--log-path", default=DEFAULTS["log_path"], dest="log_path")
    args = parser.parse_args()
    if bool(args.make) != bool(args.model):
        parser.error("--make and --model must be used together")
    return args


if __name__ == "__main__":
    asyncio.run(main(parse_args()))
