from __future__ import annotations

DEFAULTS = {
    "make_models": [
        ("Toyota", "Tacoma"),
        ("Toyota", "4Runner"),
        ("Chevrolet", "Colorado"),
    ],
    "zip_code": "18301",
    "radius": 50,
    "year_min": 2017,
    "year_max": 2027,
    "max_price": 38000,
    "max_mileage": 90000,
    "max_pages": 5,
    "db_path": "data/listings.db",
    "csv_path": "data/listings.csv",
    "log_path": "scraper.log",
    "gmail_token_path": "~/.config/truck_finder/token.json",
    "gmail_credentials_path": "credentials.json",
}
