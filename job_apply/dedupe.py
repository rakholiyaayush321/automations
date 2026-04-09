"""
dedupe.py - Duplicate detection using SHA256 hash of company + title
"""

import json
import hashlib
from pathlib import Path
from config import DEDUPE_FILE


def _hash(company: str, title: str) -> str:
    key = f"{company.strip().lower()} | {title.strip().lower()}"
    return hashlib.sha256(key.encode()).hexdigest()


def load_store() -> set[str]:
    if not DEDUPE_FILE.exists():
        return set()
    try:
        return set(json.loads(DEDUPE_FILE.read_text(encoding="utf-8")))
    except (json.JSONDecodeError, IOError):
        return set()


def save_store(store: set[str]) -> None:
    DEDUPE_FILE.parent.mkdir(parents=True, exist_ok=True)
    DEDUPE_FILE.write_text(json.dumps(list(store), indent=2), encoding="utf-8")


def is_duplicate(company: str, title: str) -> bool:
    return _hash(company, title) in load_store()


def mark_applied(company: str, title: str) -> None:
    store = load_store()
    store.add(_hash(company, title))
    save_store(store)
