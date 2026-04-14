import re
import time
import random
import requests
from bs4 import BeautifulSoup
from typing import List

try:
    from ddgs import DDGS
except ImportError:
    try:
        from duckduckgo_search import DDGS
    except ImportError:
        pass

EMAIL_REGEX = re.compile(r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+')
VALID_PREFIXES = ('hr@', 'careers@', 'jobs@', 'talent@', 'recruitment@', 'hiring@', 'career@', 'info@', 'contact@')

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:123.0) Gecko/20100101 Firefox/123.0",
]

# Aggregators and non-company domains to skip
AGGREGATORS = frozenset([
    'naukri', 'glassdoor', 'monster', 'foundit', 'indeed', 'linkedin',
    'hirist', 'cutshort', 'simplyhired', 'jobsora',
    'place1india', 'jooble', 'ambitionbox', 'techgig', 'shine',
    'freshersworld', 'naukrigulf', 'apna', 'iimjobs', 'timesjobs',
    'ziprecruiter', 'wellfound', 'angellist', 'instahyre', 'hirect',
    'google', 'facebook', 'twitter', 'youtube', 'wikipedia', 'github',
    'stackoverflow', 'reddit', 'quora', 'medium', 'wordpress',
    'selectedfirms', 'goodfirms', 'clutch', 'designrush', 'toptal',
])

BAD_DOMAIN_KEYWORDS = [
    'placement', 'academy', 'institute', 'class', 'school',
    'staffing', 'recruitment', 'classes', 'training', 'course', 'learn',
    'tutorial', 'freelance', 'job', 'expertini', 'internship',
    'consultants', 'consultancy', 'bpo', 'support'
]


def perform_ddg_search(query: str, num_results: int) -> List[str]:
    """Helper to search via DuckDuckGo using ddgs library with retry."""
    for attempt in range(3):
        try:
            delay = 2.0 + attempt * 4.0  # 2s, 6s, 10s backoff
            time.sleep(delay)
            ddgs = DDGS()
            results = list(ddgs.text(query, max_results=num_results))
            links = []
            for r in results:
                href = r.get("href")
                if href and href.startswith("http") and "duckduckgo.com" not in href:
                    links.append(href)
            if links:
                return links
            # No links but no error — DDG returned empty, don't retry
            return []
        except Exception as e:
            if attempt < 2:
                wait = 5.0 + attempt * 5.0  # 5s, 10s between retries
                print(f"[RETRY] DDG search attempt {attempt+1} failed, waiting {wait:.0f}s...", flush=True)
                time.sleep(wait)
            else:
                print(f"[FAIL] DDG search failed after 3 attempts: {e}", flush=True)
    return []


def extract_valid_emails(html_text: str, domain: str) -> str:
    found_emails = EMAIL_REGEX.findall(html_text)
    
    # Clean matches
    for email in found_emails:
        email = email.lower()
        if any(bad in email for bad in ['noreply', 'support', 'sales', 'admin', 'test', 'example', 'sentry', 'complaint', 'help']):
            continue
            
        # Prioritize matching exact HR prefixes
        if any(email.startswith(prefix) for prefix in VALID_PREFIXES):
            return email
            
        # Ensure it is their true domain
        if domain in email:
            return email
            
    return None


def _is_aggregator(domain: str) -> bool:
    """Check if domain is an aggregator or non-company site."""
    domain_lower = domain.lower()
    # Check if any aggregator name appears in the domain
    if any(agg in domain_lower for agg in AGGREGATORS):
        return True
    # Also check exact base domain (handles subdomains like in.indeed.com)
    parts = domain_lower.split('.')
    for part in parts:
        if part in AGGREGATORS:
            return True
    if any(bad in domain_lower for bad in BAD_DOMAIN_KEYWORDS):
        return True
    return False


def run_dynamic_pipeline(title="Python Developer", location="Ahmedabad", count=5):
    """Search the web for real company websites and extract HR emails.
    Returns list of dicts with job_title, company, email, source.
    Never raises — returns [] on any error."""
    try:
        return _run_dynamic_pipeline_inner(title, location, count)
    except Exception as e:
        print(f"[FAIL] Pipeline crashed: {e}", flush=True)
        return []


def _run_dynamic_pipeline_inner(title, location, count):
    print(f"\n[PIPELINE] Starting live web search for {title} in {location}...", flush=True)
    
    # Only 3 queries per call to avoid DDG rate limiting
    # Rotate different queries each call using a simple hash
    all_queries = [
        f'"{location}" software company careers page -site:naukri.com -site:indeed.com -site:linkedin.com',
        f'"{location}" IT company "contact us" OR "careers" -site:glassdoor.com -site:monster.com',
        f'"{location}" AI ML startup "we are hiring" OR "join us" -site:linkedin.com',
        f'"{location}" technology company "about us" -site:naukri.com -site:indeed.com',
        f'{title} "{location}" company website -site:glassdoor.com -site:linkedin.com -site:indeed.com',
        f'"{location}" Python developer company hiring -site:naukri.com -site:linkedin.com',
    ]
    # Pick 3 queries based on title hash to rotate across calls
    start = hash(title) % len(all_queries)
    queries = [all_queries[(start + i) % len(all_queries)] for i in range(3)]
    
    all_links = []
    for q in queries:
        links = perform_ddg_search(q, 10)
        all_links.extend(links)
    
    # Deduplicate links and pre-filter aggregators
    seen_urls = set()
    ddg_links = []
    for link in all_links:
        domain = link.split("://")[-1].split("/")[0].replace("www.", "")
        if domain not in seen_urls and not _is_aggregator(domain):
            seen_urls.add(domain)
            ddg_links.append(link)
    
    if not ddg_links:
        print("[FAIL] Web search returned no links or was blocked.", flush=True)
        return []
        
    print(f"[PIPELINE] Found {len(ddg_links)} unique company domains. Crawling...", flush=True)
    session = requests.Session()
    verified_jobs = []
    seen_domains = set()
    
    for real_url in ddg_links:
        if len(verified_jobs) >= count:
            break
        try:
            domain = real_url.split("://")[-1].split("/")[0].replace("www.", "")
            company_name = domain.split(".")[0].capitalize()
            
            if domain in seen_domains:
                continue
            
            # Only try 2 pages max (main URL + /careers) to save time
            pages_to_try = [
                real_url,
                f"https://{domain}/careers",
            ]
            
            print(f"  [CRAWL] {domain}", flush=True)
            best_email = None
            is_valid_company = True
            
            for page_url in pages_to_try:
                try:
                    time.sleep(random.uniform(0.3, 0.7))
                    real_res = session.get(page_url, headers={"User-Agent": random.choice(USER_AGENTS)}, timeout=5)
                    if real_res.status_code == 200:
                        text_lower = real_res.text.lower()
                        # Strict content check: skip placement agencies / training institutes
                        if any(phrase in text_lower for phrase in ['placement agency', 'recruitment agency', 'staffing agency', 'training institute', 'it classes', 'course fees', 'bpo services', 'call center']):
                            print(f"    -> [SKIP] Agency/training content", flush=True)
                            is_valid_company = False
                            break
                            
                        # Ensure it's a real tech company
                        if not any(tech in text_lower for tech in ['software', 'it services', 'ai', 'development', 'technologies', 'startup', 'web', 'machine learning', 'cloud', 'data', 'digital']):
                            is_valid_company = False
                            break
                            
                        found = extract_valid_emails(real_res.text, domain)
                        if found:
                            best_email = found
                            break
                except Exception:
                    continue
            
            if not is_valid_company:
                continue

            if best_email:
                print(f"    -> [OK] {best_email}", flush=True)
                verified_jobs.append({
                    "job_title": title,
                    "company": company_name,
                    "email": best_email,
                    "source": "Live Web Search"
                })
                seen_domains.add(domain)
            else:
                # Fallback to generic careers@ email
                guessed_email = f"careers@{domain}"
                print(f"    -> [FALLBACK] {guessed_email}", flush=True)
                verified_jobs.append({
                    "job_title": title,
                    "company": company_name,
                    "email": guessed_email,
                    "source": "Live Pattern Search"
                })
                seen_domains.add(domain)
                 
        except Exception as e:
            print(f"    -> [ERROR] {e}", flush=True)
            
    print(f"[PIPELINE] Done. Found {len(verified_jobs)} companies.", flush=True)
    return verified_jobs
    
if __name__ == "__main__":
    results = run_dynamic_pipeline("AI Intern", "Ahmedabad", count=5)
    print("\n--- TEST RUN RESULTS ---")
    for j in results:
         print(f"{j['job_title']} | {j['company']} | {j['email']}")

