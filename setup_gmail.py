from __future__ import annotations
"""
One-time setup to authorize the scraper to send email via your Gmail account.

Steps before running this script:
  1. Go to https://console.cloud.google.com/
  2. Create a project (or select existing)
  3. Enable Gmail API: APIs & Services → Library → search "Gmail API" → Enable
  4. Create credentials: APIs & Services → Credentials → Create Credentials
     → OAuth client ID → Desktop app → Name: TruckFinder → Create
  5. Download the JSON file → save as credentials.json in this project directory
  6. Run: python setup_gmail.py
"""
import os
from pathlib import Path

CREDENTIALS_PATH = "credentials.json"
TOKEN_PATH = os.path.expanduser("~/.config/truck_finder/token.json")
SCOPES = ["https://www.googleapis.com/auth/gmail.send"]


def main():
    if not Path(CREDENTIALS_PATH).exists():
        print(f"ERROR: {CREDENTIALS_PATH} not found in current directory.")
        print(__doc__)
        return

    from google_auth_oauthlib.flow import InstalledAppFlow

    print("Opening browser for Google account authorization...")
    flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_PATH, SCOPES)
    creds = flow.run_local_server(port=0)

    Path(TOKEN_PATH).parent.mkdir(parents=True, exist_ok=True)
    Path(TOKEN_PATH).write_text(creds.to_json())
    print(f"\nAuthorization complete. Token saved to: {TOKEN_PATH}")
    print("You can now run: python scraper.py")


if __name__ == "__main__":
    main()
