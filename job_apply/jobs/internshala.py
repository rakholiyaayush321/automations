"""
internshala.py - Internshala internship scraper
Filters for AI/ML/Python internships
"""

import re
import requests
from datetime import datetime, timedelta, timezone
from bs4 import BeautifulSoup

BASE_URL = "https://internshala.com/internships/"
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/122.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
}


def _parse_posted_days(text: str) -> datetime | None:
    """Internshala shows 'X days ago' or 'today'."""
    text = text.lower().strip()
    if "today" in text or "just" in text:
        return datetime.now(timezone.utc)
    m = re.search(r"(\d+)\s*day", text)
    if m:
        days = int(m.group(1))
        return datetime.now(timezone.utc) - timedelta(days=days)
    return None


def _is_recent(dt: datetime) -> bool:
    cutoff = datetime.now(timezone.utc) - timedelta(hours=24)
    return dt > cutoff


def fetch(keywords: list[str]) -> list[dict]:
    results = []

    for kw in keywords:
        params = {
            "q":              kw,
            "location":       "India",
            "part_time":      "off",
            "from_mobile":    "1",
        }

        try:
            resp = requests.get(BASE_URL, params=params, headers=HEADERS, timeout=15)
            resp.raise_for_status()
        except requests.RequestException as e:
            print(f"[Internshala] Request failed for '{kw}': {e}")
            continue

        soup = BeautifulSoup(resp.text, "lxml")
        cards = soup.select(".internship_meta")

        for card in cards:
            try:
                title_el   = card.select_one(".job-title")
                company_el = card.select_one(".company-name")
                link_el    = card.select_one("a.view_detail_button")
                meta_el    = card.select_one(".posted_on")

                title   = title_el.text.strip() if title_el else ""
                company = company_el.text.strip() if company_el else ""
                link    = "https://internshala.com" + link_el["href"] if link_el else ""
                meta    = meta_el.text.strip() if meta_el else ""

                if not title or not company:
                    continue

                posted_dt = _parse_posted_days(meta)
                if posted_dt is None or not _is_recent(posted_dt):
                    continue

                results.append({
                    "company":    company,
                    "job_title":  title,
                    "link":       link,
                    "source":     "Internshala",
                    "posted_raw": meta,
                })
            except Exception as e:
                print(f"[Internshala] Error parsing card: {e}")
                continue

    return results
