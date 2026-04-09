"""
naukri.py - Naukri fresher jobs scraper
Searches Naukri's fresher/entry-level section for AI/ML/Python roles
"""

import re
import requests
from datetime import datetime, timedelta, timezone
from bs4 import BeautifulSoup

BASE_URL = "https://www.naukri.com/fresher-jobs-in-ai-ml"
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/122.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
}


def _parse_date(text: str) -> datetime | None:
    """Parse Naukri date strings like '24 hours ago', '2 days ago'."""
    text = text.lower().strip()
    m = re.search(r"(\d+)\s*(hour|day)", text)
    if m:
        val, unit = int(m.group(1)), m.group(2)
        now = datetime.now(timezone.utc)
        if unit.startswith("hour"):
            return now - timedelta(hours=val)
        return now - timedelta(days=val)
    if "today" in text or "yesterday" in text:
        return datetime.now(timezone.utc) - timedelta(days=1 if "yesterday" in text else 0)
    return None


def _is_recent(dt: datetime) -> bool:
    cutoff = datetime.now(timezone.utc) - timedelta(hours=24)
    return dt > cutoff


def fetch(keywords: list[str]) -> list[dict]:
    results = []

    for kw in keywords:
        # Naukri uses a search endpoint for fresher jobs
        params = {
            "q":      f"{kw} fresher",
            "l":      "India",
            "count":  20,
        }
        search_url = f"https://www.naukri.com/job-search/{kw}-fresher-jobs-in-india"

        try:
            resp = requests.get(search_url, headers=HEADERS, timeout=15)
            resp.raise_for_status()
        except requests.RequestException as e:
            print(f"[Naukri] Request failed for '{kw}': {e}")
            continue

        soup = BeautifulSoup(resp.text, "lxml")
        cards = soup.select(".jobTuple") or soup.select(".job-card")

        for card in cards:
            try:
                title_el   = card.select_one(".title")
                company_el = card.select_one(".companyInfo .subTitle")
                link_el    = card.select_one("a[href*='naukri.com']")
                date_el    = card.select_one(".metaInfo")

                title   = title_el.text.strip() if title_el else ""
                company = company_el.text.strip() if company_el else ""
                link    = link_el["href"].split("?")[0] if link_el else ""
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
                    "source":     "Naukri",
                    "posted_raw": meta,
                })
            except Exception as e:
                print(f"[Naukri] Error parsing card: {e}")
                continue

    return results
