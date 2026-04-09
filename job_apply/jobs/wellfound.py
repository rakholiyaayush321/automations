"""
wellfound.py - Wellfound (formerly AngelList) job scraper
Filters for AI/ML/Python internships and early-stage roles
"""

import re
import requests
from datetime import datetime, timedelta, timezone
from bs4 import BeautifulSoup

BASE_URL = "https://wellfound.com/jobs/search"
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/122.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
}


def _parse_posted(text: str) -> datetime | None:
    """Parse relative time strings like '24h ago', '3d ago', '2 weeks ago'."""
    text = text.lower().strip()
    m = re.search(r"(\d+)\s*(h|d|w|hour|day|week)", text)
    if m:
        val = int(m.group(1))
        unit = m.group(2)[0]  # h, d, or w
        now = datetime.now(timezone.utc)
        if unit == "h":
            return now - timedelta(hours=val)
        if unit == "d":
            return now - timedelta(days=val)
        if unit == "w":
            return now - timedelta(weeks=val)
    return None


def _is_recent(dt: datetime) -> bool:
    cutoff = datetime.now(timezone.utc) - timedelta(hours=24)
    return dt > cutoff


def fetch(keywords: list[str]) -> list[dict]:
    results = []

    for kw in keywords:
        params = {
            "query": kw,
            "filter[duration][]": "internship",
            "sort": "newest_first",
        }

        try:
            resp = requests.get(BASE_URL, params=params, headers=HEADERS, timeout=15)
            resp.raise_for_status()
        except requests.RequestException as e:
            print(f"[Wellfound] Request failed for '{kw}': {e}")
            continue

        soup = BeautifulSoup(resp.text, "lxml")
        cards = soup.select(".job-row") or soup.select("[data-job-id]")

        for card in cards:
            try:
                title_el   = card.select_one(".job-title, h2")
                company_el = card.select_one(".startup-name, .company-name")
                link_el    = card.select_one("a[href*='/jobs/']")
                meta_el    = card.select_one(".posted-date, .time")

                title   = title_el.text.strip() if title_el else ""
                company = company_el.text.strip() if company_el else ""
                link    = "https://wellfound.com" + link_el["href"] if link_el else ""
                meta    = meta_el.text.strip() if meta_el else ""

                if not title or not company:
                    continue

                posted_dt = _parse_posted(meta)
                if posted_dt is None or not _is_recent(posted_dt):
                    continue

                results.append({
                    "company":    company,
                    "job_title":  title,
                    "link":       link,
                    "source":     "Wellfound",
                    "posted_raw": meta,
                })
            except Exception as e:
                print(f"[Wellfound] Error parsing card: {e}")
                continue

    return results
