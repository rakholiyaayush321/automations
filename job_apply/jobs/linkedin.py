"""
linkedin.py - LinkedIn job scraper
Searches for internships/fresher AI/ML/Python roles posted in last 24h
"""

import re
import requests
from datetime import datetime, timedelta, timezone
from bs4 import BeautifulSoup

SEARCH_URL = "https://www.linkedin.com/jobs/search/"
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/122.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
}


def _parse_relative_time(text: str) -> datetime | None:
    """Parse LinkedIn's relative time strings like '24 hours ago', '2 days ago'."""
    text = text.lower().strip()
    m = re.search(r"(\d+)\s*(hour|day|d|h)", text)
    if not m:
        return None
    val, unit = int(m.group(1)), m.group(2)
    now = datetime.now(timezone.utc)
    if unit.startswith("hour") or unit == "h":
        return now - timedelta(hours=val)
    if unit.startswith("day") or unit == "d":
        return now - timedelta(days=val)
    return None


def _is_recent(dt: datetime) -> bool:
    cutoff = datetime.now(timezone.utc) - timedelta(hours=24)
    return dt > cutoff


def _fetch_description(link: str) -> str:
    """Fetch the full job description from an individual LinkedIn job page."""
    try:
        resp = requests.get(link, headers=HEADERS, timeout=10)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "lxml")
        desc_el = soup.select_one(".jobs-description__content") or \
                  soup.select_one("#job-details") or \
                  soup.select_one(".job-details-modal__content")
        return desc_el.text.strip() if desc_el else ""
    except Exception:
        return ""


def fetch(keywords: list[str]) -> list[dict]:
    """
    Search LinkedIn for jobs matching keywords, posted in last 24h.
    Returns list of job dicts with descriptions fetched for scoring.
    """
    import urllib.parse
    results = []

    for kw in keywords:
        params = {
            "keywords": "AI ML Python Data Science Intern",
            "location": "India",
            "f_TPR": "r86400",  # last 24h
            "f_JT": "I",        # Internship
            "start": 0,
        }
        # Use keyword-specific search per kw
        params["keywords"] = kw
        url = SEARCH_URL + "?" + urllib.parse.urlencode(params)

        try:
            resp = requests.get(url, headers=HEADERS, timeout=15)
            resp.raise_for_status()
        except requests.RequestException as e:
            print(f"[LinkedIn] Request failed for '{kw}': {e}")
            continue

        soup = BeautifulSoup(resp.text, "lxml")
        job_cards = soup.select(".job-search-card")

        for card in job_cards:
            try:
                title_el   = card.select_one(".job-search-card__title")
                company_el = card.select_one(".job-search-card__subtitle")
                link_el    = card.select_one("a")
                meta_el    = card.select_one(".job-search-card__listing-meta")

                title   = title_el.text.strip() if title_el else ""
                company = company_el.text.strip() if company_el else ""
                link    = link_el["href"].split("?")[0] if link_el else ""
                meta    = meta_el.text.strip() if meta_el else ""

                if not title or not company or not link:
                    continue

                posted_dt = _parse_relative_time(meta)
                if posted_dt is None:
                    continue
                if not _is_recent(posted_dt):
                    continue

                # Fetch description for better skill matching
                description = _fetch_description(link)

                results.append({
                    "company":     company,
                    "job_title":   title,
                    "link":        link,
                    "source":      "LinkedIn",
                    "description": description,
                    "posted_raw":  meta,
                })
            except Exception as e:
                print(f"[LinkedIn] Error parsing card: {e}")
                continue

    return results
