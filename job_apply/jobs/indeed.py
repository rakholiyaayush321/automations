"""
indeed.py - Indeed job scraper
Filters for fresher/intern AI/ML/Python jobs in India, last 24h
"""

import re
import requests
from datetime import datetime, timedelta, timezone
from bs4 import BeautifulSoup

SEARCH_URL = "https://www.indeed.com/jobs"
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/122.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
}


def _parse_date(text: str) -> datetime | None:
    """Parse Indeed date strings: '24 hours ago', '2 days ago', '30+ days ago'."""
    text = text.lower().strip()
    m = re.search(r"(\d+)\s*(hour|day|d)", text)
    if m:
        val, unit = int(m.group(1)), m.group(2)
        now = datetime.now(timezone.utc)
        if unit.startswith("hour") or unit == "h":
            return now - timedelta(hours=val)
        return now - timedelta(days=val)
    if "yesterday" in text:
        return datetime.now(timezone.utc) - timedelta(days=1)
    return None


def _is_recent(dt: datetime) -> bool:
    cutoff = datetime.now(timezone.utc) - timedelta(hours=24)
    return dt > cutoff


def fetch(keywords: list[str]) -> list[dict]:
    results = []

    for kw in keywords:
        params = {
            "q":      kw,
            "l":      "India",
            "jt":     "internship",   # internship/fresher
            "fromage": "1",            # last 24 hours
            "sort":   "date",
        }

        try:
            resp = requests.get(SEARCH_URL, params=params, headers=HEADERS, timeout=15)
            resp.raise_for_status()
        except requests.RequestException as e:
            print(f"[Indeed] Request failed for '{kw}': {e}")
            continue

        soup = BeautifulSoup(resp.text, "lxml")
        cards = soup.select(".jobsearch-ResultsList > li")

        for card in cards:
            try:
                title_el   = card.select_one(".jobTitle > span")
                company_el = card.select_one(".companyName")
                link_el    = card.select_one("a.jcs-JobTitle")
                date_el    = card.select_one(".date")

                title   = title_el.text.strip() if title_el else ""
                company = company_el.text.strip() if company_el else ""
                link    = "https://www.indeed.com" + link_el["href"] if link_el else ""
                meta    = date_el.text.strip() if date_el else ""

                if not title:
                    continue

                posted_dt = _parse_date(meta)
                if posted_dt is None or not _is_recent(posted_dt):
                    continue

                results.append({
                    "company":    company,
                    "job_title":  title,
                    "link":       link,
                    "source":     "Indeed",
                    "posted_raw": meta,
                })
            except Exception as e:
                print(f"[Indeed] Error parsing card: {e}")
                continue

    return results
