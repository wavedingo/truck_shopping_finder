from __future__ import annotations

import csv
import json
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional


@dataclass
class Listing:
    site: str
    title: str
    year: Optional[int]
    make: Optional[str]
    model: Optional[str]
    price: Optional[int]
    mileage: Optional[int]
    location: Optional[str]
    url: str
    vin: Optional[str] = None


CSV_COLUMNS = ["site", "title", "year", "make", "model", "price",
               "mileage", "location", "url", "date_scraped"]


class Database:
    def __init__(self, path: str = "data/listings.db"):
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(path)
        self.conn.row_factory = sqlite3.Row
        self._create_schema()

    def _create_schema(self):
        self.conn.executescript("""
            CREATE TABLE IF NOT EXISTS listings (
                id               INTEGER PRIMARY KEY,
                site             TEXT NOT NULL,
                title            TEXT,
                year             INTEGER,
                make             TEXT,
                model            TEXT,
                price            INTEGER,
                previous_price   INTEGER,
                price_changed_at TEXT,
                mileage          INTEGER,
                location         TEXT,
                url              TEXT UNIQUE,
                vin              TEXT,
                first_seen       TEXT NOT NULL,
                last_seen        TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS runs (
                id                  INTEGER PRIMARY KEY,
                started_at          TEXT NOT NULL,
                finished_at         TEXT,
                sites_scraped       TEXT,
                new_listings_found  INTEGER DEFAULT 0,
                price_changes_found INTEGER DEFAULT 0,
                errors              TEXT DEFAULT '[]'
            );
        """)
        self.conn.commit()

    def close(self):
        self.conn.close()

    def upsert_listing(self, listing: Listing, run_ts: str) -> str:
        """Returns 'new', 'existing', or 'price_changed'."""
        if listing.vin:
            row = self.conn.execute(
                "SELECT id, price FROM listings WHERE vin = ?", (listing.vin,)
            ).fetchone()
            if row:
                return self._handle_existing(row, listing, run_ts)

        if listing.url:
            row = self.conn.execute(
                "SELECT id, price FROM listings WHERE url = ?", (listing.url,)
            ).fetchone()
            if row:
                return self._handle_existing(row, listing, run_ts)

        if listing.title and listing.mileage:
            row = self.conn.execute(
                "SELECT id, price FROM listings WHERE title = ? AND mileage = ? AND site = ?",
                (listing.title, listing.mileage, listing.site),
            ).fetchone()
            if row:
                return self._handle_existing(row, listing, run_ts)

        self.conn.execute(
            """
            INSERT INTO listings
                (site, title, year, make, model, price, mileage, location,
                 url, vin, first_seen, last_seen)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (listing.site, listing.title, listing.year, listing.make, listing.model,
             listing.price, listing.mileage, listing.location, listing.url,
             listing.vin, run_ts, run_ts),
        )
        self.conn.commit()
        return "new"

    def _handle_existing(self, row: sqlite3.Row, listing: Listing, run_ts: str) -> str:
        if listing.price is not None and row["price"] != listing.price:
            self.conn.execute(
                """
                UPDATE listings
                SET price = ?, previous_price = ?, price_changed_at = ?, last_seen = ?
                WHERE id = ?
                """,
                (listing.price, row["price"], run_ts, run_ts, row["id"]),
            )
            self.conn.commit()
            return "price_changed"
        self.conn.execute(
            "UPDATE listings SET last_seen = ? WHERE id = ?", (run_ts, row["id"])
        )
        self.conn.commit()
        return "existing"

    def export_new_listings_csv(self, run_ts: str, path: str, sort_by: Optional[str] = None):
        query = "SELECT * FROM listings WHERE first_seen = ?"
        if sort_by == "price":
            query += " ORDER BY price ASC"
        elif sort_by == "mileage":
            query += " ORDER BY mileage ASC"
        rows = self.conn.execute(query, (run_ts,)).fetchall()
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=CSV_COLUMNS)
            writer.writeheader()
            for row in rows:
                writer.writerow({
                    "site": row["site"], "title": row["title"], "year": row["year"],
                    "make": row["make"], "model": row["model"], "price": row["price"],
                    "mileage": row["mileage"], "location": row["location"],
                    "url": row["url"], "date_scraped": row["first_seen"],
                })

    def start_run(self) -> int:
        now = datetime.now(timezone.utc).isoformat()
        cursor = self.conn.execute("INSERT INTO runs (started_at) VALUES (?)", (now,))
        self.conn.commit()
        return cursor.lastrowid

    def finish_run(self, run_id: int, sites: list, new: int, changes: int, errors: list):
        now = datetime.now(timezone.utc).isoformat()
        self.conn.execute(
            """
            UPDATE runs
            SET finished_at = ?, sites_scraped = ?, new_listings_found = ?,
                price_changes_found = ?, errors = ?
            WHERE id = ?
            """,
            (now, json.dumps(sites), new, changes, json.dumps(errors), run_id),
        )
        self.conn.commit()

    def get_price_changes(self, since_ts: str) -> list:
        return self.conn.execute(
            "SELECT * FROM listings WHERE price_changed_at >= ?", (since_ts,)
        ).fetchall()
