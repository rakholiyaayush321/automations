"""
hr_finder.py - Find Hiring Manager / HR contact name for a company
==================================================================
Searches the web for the HR manager or hiring contact at a company.
Falls back to "Hiring Team" if none found.

Uses DuckDuckGo search to find LinkedIn profiles and company pages.
"""

import json
import re
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Tuple

try:
    from ddgs import DDGS
    HAS_DDG = True
except ImportError:
    HAS_DDG = False

try:
    import requests
    from bs4 import BeautifulSoup
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False

# ── Config ───────────────────────────────────────────────────────────────────
PROJECT_DIR = Path(__file__).parent
CACHE_FILE = PROJECT_DIR / "hr_contacts.json"
CACHE_TTL_DAYS = 30  # HR contacts don't change often

# Common Indian first names to validate extracted names
COMMON_TITLES = [
    "mr", "ms", "mrs", "dr", "prof", "sir", "madam",
    "shri", "smt", "er", "ca", "cs",
]

HR_ROLE_KEYWORDS = [
    "hr manager", "human resources", "talent acquisition",
    "hiring manager", "recruiter", "hr head", "hr lead",
    "people operations", "hr director", "recruitment",
    "hr executive", "hr coordinator", "talent partner",
    "head of hr", "head of people", "hr business partner",
]


# ── Cache ────────────────────────────────────────────────────────────────────
def _load_cache() -> dict:
    if CACHE_FILE.exists():
        try:
            with open(CACHE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            return {}
    return {}


def _save_cache(cache: dict) -> None:
    try:
        with open(CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(cache, f, indent=2, ensure_ascii=False)
    except OSError:
        pass


def _cache_get(company: str) -> Optional[dict]:
    cache = _load_cache()
    key = company.lower().strip()
    entry = cache.get(key)
    if not entry:
        return None
    cached_at = datetime.fromisoformat(entry["checked_at"])
    if datetime.now() - cached_at > timedelta(days=CACHE_TTL_DAYS):
        return None
    # Don't return "not_found" entries from cache — always re-search
    if entry.get("source") == "not_found" or not entry.get("name"):
        return None
    return entry


def _cache_set(company: str, name: str, role: str, source: str) -> None:
    cache = _load_cache()
    key = company.lower().strip()
    cache[key] = {
        "name": name,
        "role": role,
        "source": source,
        "checked_at": datetime.now().isoformat(),
    }
    _save_cache(cache)


# ── Name Validation ──────────────────────────────────────────────────────────
def _is_valid_person_name(name: str) -> bool:
    """Check if a string looks like a real person's name."""
    if not name or len(name) < 3 or len(name) > 60:
        return False

    # Must have at least 2 parts (first + last)
    parts = name.strip().split()
    if len(parts) < 2:
        return False

    # Remove titles
    cleaned_parts = [p for p in parts if p.lower().rstrip(".") not in COMMON_TITLES]
    if len(cleaned_parts) < 1:
        return False

    # Each part should be mostly alphabetic
    for part in cleaned_parts:
        clean = part.rstrip(".,")
        if not clean.replace("-", "").replace("'", "").isalpha():
            return False

    # Should not look like a company name or generic term
    lower = name.lower()
    bad_words = [
        "team", "department", "company", "office", "group",
        "pvt", "ltd", "inc", "llc", "corp", "solutions",
        "technologies", "infotech", "software",
    ]
    if any(bw in lower for bw in bad_words):
        return False

    return True


def _extract_first_name(full_name: str) -> str:
    """Extract first name from full name, stripping titles."""
    parts = full_name.strip().split()
    for part in parts:
        clean = part.rstrip(".,")
        if clean.lower() not in COMMON_TITLES and clean.isalpha():
            return clean.capitalize()
    return parts[0].capitalize() if parts else ""


# ── Search Methods ───────────────────────────────────────────────────────────
def _search_ddg(company: str) -> Optional[Tuple[str, str]]:
    """Search DuckDuckGo for HR manager at company."""
    if not HAS_DDG:
        return None

    queries = [
        f'{company} HR manager LinkedIn "Ahmedabad" OR "Pune"',
        f'{company} talent acquisition manager LinkedIn',
        f'site:linkedin.com "{company}" HR manager Ahmedabad Pune',
        f'site:indeed.com "{company}" hiring manager',
        f'"{company}" human resources manager "Ahmedabad" OR "Pune"',
        f'"{company}" recruitment lead',
    ]

    try:
        ddgs = DDGS()
        for query in queries:
            try:
                results = list(ddgs.text(query, max_results=5))
            except Exception:
                continue

            for r in results:
                title = r.get("title", "")
                body = r.get("body", "")
                text = f"{title} {body}"

                # Look for patterns like "Name - HR Manager at Company"
                patterns = [
                    # LinkedIn style: "Name - Title - Company"
                    r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)\s*[-–|]\s*(?:' + '|'.join(HR_ROLE_KEYWORDS) + r')',
                    # "Name, HR Manager"
                    r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)\s*,\s*(?:' + '|'.join(HR_ROLE_KEYWORDS) + r')',
                    # "HR Manager Name"
                    r'(?:' + '|'.join(HR_ROLE_KEYWORDS) + r')\s*[-–|:]\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)',
                ]

                for pat in patterns:
                    match = re.search(pat, text, re.IGNORECASE)
                    if match:
                        name = match.group(1).strip()
                        if _is_valid_person_name(name):
                            # Extract the role
                            role_match = re.search(
                                '(' + '|'.join(HR_ROLE_KEYWORDS) + ')',
                                text, re.IGNORECASE
                            )
                            role = role_match.group(1).title() if role_match else "HR Manager"
                            return name, role

            time.sleep(0.5)  # Rate limit

    except Exception:
        pass

    return None


def _search_company_page(website: str) -> Optional[Tuple[str, str]]:
    """Try to find HR contact from company's about/team page."""
    if not HAS_REQUESTS or not website:
        return None

    # Common team/about page URLs
    domain = website.replace("https://", "").replace("http://", "").rstrip("/")
    urls = [
        f"https://{domain}/about",
        f"https://{domain}/team",
        f"https://{domain}/careers",
        f"https://{domain}/about-us",
        f"https://{domain}/our-team",
        f"https://{domain}/leadership",
        f"https://{domain}/contact",
    ]

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }

    for url in urls:  # Try all
        try:
            resp = requests.get(url, timeout=8, headers=headers)
            if resp.status_code != 200:
                continue

            soup = BeautifulSoup(resp.text, "html.parser")
            text = soup.get_text(separator=" ", strip=True).lower()

            # Look for HR-related roles near names
            for keyword in HR_ROLE_KEYWORDS:
                idx = text.find(keyword)
                if idx == -1:
                    continue

                # Get surrounding text (100 chars before and after)
                start = max(0, idx - 100)
                end = min(len(text), idx + 100)
                context = resp.text[start:end]

                # Look for capitalized names near the keyword
                name_matches = re.findall(
                    r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)', context
                )
                for name in name_matches:
                    if _is_valid_person_name(name):
                        return name, keyword.title()

        except Exception:
            continue

    return None


# ── Public API ───────────────────────────────────────────────────────────────
def _extract_name_from_email(email: str) -> Optional[Tuple[str, str]]:
    """Try to extract a person's name from an email like 'anusha.edunoori@company.com'."""
    if not email or '@' not in email:
        return None
        
    prefix = email.split('@')[0].lower()
    
    # Generic prefixes to ignore
    generic = [
        'hr', 'careers', 'career', 'jobs', 'hiring', 'talent', 'recruitment',
        'info', 'contact', 'support', 'hello', 'admin', 'sales', 'team',
        'office', 'apply', 'candidates', 'recruit', 'people'
    ]
    if prefix in generic or any(prefix.startswith(g + '.') for g in generic):
        return None
        
    # Split by dot, underscore, or dash
    parts = re.split(r'[._-]', prefix)
    
    # Filter out numbers and make title case
    clean_parts = [p.title() for p in parts if p.isalpha() and len(p) > 1]
    
    if len(clean_parts) >= 1:
        # e.g., ["Anusha", "Edunoori"]
        full_name = " ".join(clean_parts)
        if _is_valid_person_name(full_name) or len(clean_parts) > 1:
            return full_name, "HR / Hiring Manager"
            
    return None

def find_hr_contact(company: str, website: str = "", email: str = "") -> dict:
    """
    Find the HR / hiring manager for a company.

    Returns:
        {
            "name": "Priya Sharma",       # Full name
            "first_name": "Priya",        # First name (for greeting)
            "role": "HR Manager",         # Their role
            "greeting": "Dear Priya",     # Ready-to-use greeting
            "source": "web_search",       # How we found them
            "found": True                 # Whether we found someone
        }
    """
    # 1. Try to extract name directly from the email address first
    if email:
        email_result = _extract_name_from_email(email)
        if email_result:
            name, role = email_result
            first = _extract_first_name(name)
            return {
                "name": name,
                "first_name": first,
                "role": role,
                "greeting": f"Dear {first}",
                "source": "email_extraction",
                "found": True,
            }

    # 2. Check cache next
    cached = _cache_get(company)
    if cached:
        first = _extract_first_name(cached["name"])
        return {
            "name": cached["name"],
            "first_name": first,
            "role": cached["role"],
            "greeting": f"Dear {first}" if first else "Dear Hiring Team",
            "source": f"cache ({cached['source']})",
            "found": True,
        }

    # 3. Try DuckDuckGo search
    result = _search_ddg(company)
    if result:
        name, role = result
        first = _extract_first_name(name)
        _cache_set(company, name, role, "web_search")
        return {
            "name": name,
            "first_name": first,
            "role": role,
            "greeting": f"Dear {first}",
            "source": "web_search",
            "found": True,
        }

    # Try company website
    result = _search_company_page(website)
    if result:
        name, role = result
        first = _extract_first_name(name)
        _cache_set(company, name, role, "company_page")
        return {
            "name": name,
            "first_name": first,
            "role": role,
            "greeting": f"Dear {first}",
            "source": "company_page",
            "found": True,
        }

    # No luck — use generic greeting
    _cache_set(company, "", "Unknown", "not_found")
    return {
        "name": "",
        "first_name": "",
        "role": "",
        "greeting": "Dear Hiring Manager",
        "source": "not_found",
        "found": False,
    }


# ── CLI ──────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import sys

    test_companies = [
        ("Simform", "simform.com", "careers@simform.com"),
        ("Adroit", "adroitinnovative.com", "anusha.edunoori@adroitinnovative.com"),
        ("TatvaSoft", "tatvasoft.com", "jobs@tatvasoft.com"),
        ("MindInventory", "mindinventory.com", "rohit.sharma@mindinventory.com"),
    ]

    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        print("=" * 60)
        print("HR CONTACT FINDER — Test Run")
        print("=" * 60)
        for company, website, email in test_companies:
            print(f"\n  Searching: {company} (Email: {email})...")
            result = find_hr_contact(company, website, email)
            if result["found"]:
                print(f"    [OK] {result['name']} -- {result['role']}")
                print(f"      Greeting: {result['greeting']}")
                print(f"      Source: {result['source']}")
            else:
                print(f"    [--] No HR contact found -> {result['greeting']}")
    else:
        print("Usage: python hr_finder.py --test")
