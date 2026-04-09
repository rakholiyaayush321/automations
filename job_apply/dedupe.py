"""
dedupe.py - Duplicate detection using SHA256 hash of company + title
"""

import json
import hashlib
from pathlib import Path
from datetime import date, datetime, timedelta
from config import DEDUPE_FILE, REAPPLICATION_DAYS


def _hash(company: str, title: str) -> str:
    key = f"{company.strip().lower()} | {title.strip().lower()}"
    return hashlib.sha256(key.encode()).hexdigest()


def load_store() -> dict[str, str]:
    if not DEDUPE_FILE.exists():
        return {}
    try:
        data = json.loads(DEDUPE_FILE.read_text(encoding="utf-8"))
        if isinstance(data, list):
            # Legacy migration: old stores were a list of hashes.
            # Assign an old date (e.g. 35 days ago) so they are eligible for reapplication.
            old_date = (date.today() - timedelta(days=35)).isoformat()
            return {h: old_date for h in data}
        return data
    except (json.JSONDecodeError, IOError):
        return {}


def save_store(store: dict[str, str]) -> None:
    DEDUPE_FILE.parent.mkdir(parents=True, exist_ok=True)
    DEDUPE_FILE.write_text(json.dumps(store, indent=2), encoding="utf-8")


def is_duplicate(company: str, title: str) -> bool:
    store = load_store()
    h = _hash(company, title)
    if h in store:
        try:
            last_applied = datetime.strptime(store[h], "%Y-%m-%d").date()
            days_since = (date.today() - last_applied).days
            if days_since >= REAPPLICATION_DAYS:
                return False  # Eligible for reapplication (30 days passed)
            return True
        except ValueError:
            return True
    return False


def mark_applied(company: str, title: str) -> None:
    store = load_store()
    store[_hash(company, title)] = date.today().isoformat()
    save_store(store)
