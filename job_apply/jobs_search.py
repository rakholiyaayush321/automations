"""
jobs_search.py - Live job search with company validation and deduplication
"""

import json
from pathlib import Path
from datetime import datetime

PROJECT_DIR = Path(__file__).parent
APPLIED_FILE = PROJECT_DIR / "applied_companies.json"


def load_applied_companies() -> set:
    """Load set of companies already applied to."""
    if not APPLIED_FILE.exists():
        return set()
    try:
        with open(APPLIED_FILE, "r") as f:
            data = json.load(f)
            return set(data.get("companies", []))
    except:
        return set()


def save_applied_companies(companies: set) -> None:
    """Save applied companies to file."""
    data = {
        "companies": sorted(list(companies)),
        "last_updated": datetime.now().isoformat(),
        "count": len(companies),
    }
    with open(APPLIED_FILE, "w") as f:
        json.dump(data, f, indent=2)


def is_new_company(company: str, applied: set) -> bool:
    """Check if company is new (not in applied set)."""
    company_clean = company.lower().strip()
    for applied_name in applied:
        if company_clean in applied_name.lower() or applied_name.lower() in company_clean:
            return False
    return True


def search_job_queries() -> list[dict]:
    """
    Return list of search queries for web search.
    Caller should execute web_search for each query.
    """
    return [
        "Python intern Ahmedabad 2026 hiring",
        "AI ML fresher Ahmedabad entry level",
        "junior python developer Ahmedabad jobs",
        "machine learning intern Ahmedabad",
        "data science intern Ahmedabad fresher",
        "FastAPI developer intern Ahmedabad",
        "LLM AI intern Ahmedabad startup",
        "deep learning intern Ahmedabad",
    ]


def parse_search_results(content: str) -> list[dict]:
    """
    Parse web search results to extract company/job info.
    Returns list of job dicts.
    """
    jobs = []
    companies_found = []
    
    # Extract company names from search content
    # Look for patterns like "**Company Name** is hiring"
    import re
    
    # Pattern 1: Bold company names with hiring context
    pattern = r"\*\*([^*]+)\*\*.*?(?:hiring|looking|seeking|opening|jobs)"
    matches = re.findall(pattern, content, re.IGNORECASE)
    
    for company in matches:
        company_clean = company.strip()
        if company_clean and len(company_clean) > 3:
            companies_found.append(company_clean)
    
    # Remove duplicates
    seen = set()
    unique_companies = []
    for c in companies_found:
        if c.lower() not in seen:
            seen.add(c.lower())
            unique_companies.append(c)
    
    return unique_companies


def build_jobs_list(companies: list[str], applied: set, target_count: int = 15) -> list[dict]:
    """
    Build job list from company names, filtering out applied companies.
    Returns exactly `target_count` jobs if possible.
    """
    jobs = []
    applied_count = 0
    
    # Predefined HR emails for known companies
    known_emails = {
        "MindInventory": "career@mindinventory.com",
        "Unidoc Healthcare": "contact@unidoc.in",
        "Softrefine Technology": "hr@softrefine.com",
        "Anblicks": "careers@anblicks.com",
        "Tatvasoft": "careers@tatvasoft.com",
        "Simform": "careers@simform.com",
        "Motadata": "careers@motadata.com",
        "Radixweb": "hr@radixweb.com",
        "OpenXcell": "careers@openxcell.com",
        "Crest Data Systems": "careers@crestdatasystems.com",
    }
    
    for company in companies:
        if len(jobs) >= target_count:
            break
        
        # Check if already applied
        if not is_new_company(company, applied):
            applied_count += 1
            continue
        
        # Determine job title based on company type
        job_title = "Python Intern"
        if any(kw in company.lower() for kw in ["ai", "ml", "data"]):
            job_title = "AI/ML Intern"
        elif any(kw in company.lower() for kw in ["soft", "tech", "web"]):
            job_title = "Junior Python Developer"
        
        # Get email
        email = known_emails.get(company, f"careers@{company.lower().replace(' ', '').replace('pvt', '').replace('ltd', '')}.com")
        
        jobs.append({
            "company": company,
            "job_title": job_title,
            "email": email,
            "source": "web_search",
        })
    
    return jobs, applied_count