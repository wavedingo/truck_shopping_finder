from __future__ import annotations
import base64
import html as html_lib
import logging
import os
from datetime import datetime, timezone
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


def build_subject(new_count: int, change_count: int, date_str: str) -> str:
    parts = []
    if new_count:
        parts.append(f"{new_count} new listing{'s' if new_count != 1 else ''}")
    if change_count:
        parts.append(f"{change_count} price change{'s' if change_count != 1 else ''}")
    summary = ", ".join(parts) if parts else "no changes"
    return f"[Truck Finder] {summary} — {date_str}"


def _fmt_price(price) -> str:
    return f"${price:,}" if price is not None else "N/A"


def _fmt_mileage(mileage) -> str:
    return f"{mileage:,} mi" if mileage is not None else "N/A"


def _status_color(status: str) -> str:
    if status == "FAILED":
        return "red"
    if status == "WARN":
        return "orange"
    return "green"


def build_email_html(new_listings: list, price_changes: list, site_stats: dict) -> str:
    sections = []

    if new_listings:
        rows_html = "".join(
            f"<tr><td>{html_lib.escape(str(r['site']))}</td>"
            f"<td><a href='{html_lib.escape(str(r['url']), quote=True)}'>{html_lib.escape(str(r['title']))}</a></td>"
            f"<td>{r['year'] or ''}</td>"
            f"<td>{_fmt_price(r['price'])}</td>"
            f"<td>{_fmt_mileage(r['mileage'])}</td>"
            f"<td>{html_lib.escape(str(r['location'] or ''))}</td></tr>"
            for r in new_listings
        )
        sections.append(
            f"<h2>New Listings</h2>"
            f"<table border='1' cellpadding='5' cellspacing='0'>"
            f"<tr><th>Site</th><th>Title</th><th>Year</th>"
            f"<th>Price</th><th>Mileage</th><th>Location</th></tr>"
            f"{rows_html}</table>"
        )

    if price_changes:
        rows_html = "".join(
            f"<tr><td>{html_lib.escape(str(r['site']))}</td>"
            f"<td><a href='{html_lib.escape(str(r['url']), quote=True)}'>{html_lib.escape(str(r['title']))}</a></td>"
            f"<td>{_fmt_price(r['previous_price'])} → {_fmt_price(r['price'])}</td></tr>"
            for r in price_changes
        )
        sections.append(
            f"<h2>Price Changes</h2>"
            f"<table border='1' cellpadding='5' cellspacing='0'>"
            f"<tr><th>Site</th><th>Title</th><th>Price</th></tr>"
            f"{rows_html}</table>"
        )

    footer_rows = "".join(
        f"<tr><td>{html_lib.escape(site)}</td><td>{s['new']}</td><td>{s['changes']}</td>"
        f"<td>{s['pages']}</td>"
        f"<td style='color:{_status_color(s['status'])}'>"
        f"{s['status']}</td></tr>"
        for site, s in site_stats.items()
    )
    footer = (
        f"<hr><h3>Scrape Status</h3>"
        f"<table border='1' cellpadding='5' cellspacing='0'>"
        f"<tr><th>Site</th><th>New</th><th>Price Changes</th><th>Pages</th><th>Status</th></tr>"
        f"{footer_rows}</table>"
        f"<p style='color:gray;font-size:11px'>Check scraper.log for full details.</p>"
    )

    body = "".join(sections) + footer
    return f"<html><body style='font-family:sans-serif'>{body}</body></html>"


def send_digest(
    new_listings: list,
    price_changes: list,
    site_stats: dict,
    token_path: str,
    recipient: Optional[str] = None,
):
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from googleapiclient.discovery import build as build_service

    token_path = os.path.expanduser(token_path)
    if not Path(token_path).exists():
        raise FileNotFoundError(
            f"Gmail token not found at {token_path}. "
            "Run setup_gmail.py first to authorize."
        )
    creds = Credentials.from_authorized_user_file(
        token_path,
        scopes=["https://www.googleapis.com/auth/gmail.send"],
    )
    if creds.expired and creds.refresh_token:
        creds.refresh(Request())
        Path(token_path).write_text(creds.to_json())

    service = build_service("gmail", "v1", credentials=creds)
    profile = service.users().getProfile(userId="me").execute()
    sender = profile["emailAddress"]
    to = recipient or sender

    date_str = datetime.now(timezone.utc).strftime("%b %-d")
    subject = build_subject(len(new_listings), len(price_changes), date_str)
    html = build_email_html(new_listings, price_changes, site_stats)

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = sender
    msg["To"] = to
    msg.attach(MIMEText(html, "html"))

    raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()
    service.users().messages().send(userId="me", body={"raw": raw}).execute()
    logger.info(f"Email sent to {to}: {subject}")
