import re
import time
import random
import requests
from bs4 import BeautifulSoup
from typing import List

EMAIL_REGEX = re.compile(r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+')
VALID_PREFIXES = ('hr@', 'careers@', 'jobs@', 'talent@', 'recruitment@', 'hiring@', 'career@', 'info@', 'contact@')

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:123.0) Gecko/20100101 Firefox/123.0",
]

def perform_ddg_search(query: str, num_results: int) -> List[str]:
    """Helper to search via DuckDuckGo HTML avoiding Captchas"""
    url = "https://html.duckduckgo.com/html/"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept-Language": "en-US,en;q=0.9"
    }
    data = {"q": query}
    try:
        time.sleep(1.0)
        res = requests.post(url, headers=headers, data=data, timeout=10)
        soup = BeautifulSoup(res.text, "html.parser")
        links = []
        for a in soup.find_all("a", class_="result__url"):
            href = a.get("href")
            # Skip duckduckgo ad tracking links
            if href and href.startswith("http") and "duckduckgo.com" not in href:
                links.append(href)
        return links[:num_results]
    except Exception as e:
        print(f"[FAIL] DDG search failed: {e}")
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

def run_dynamic_pipeline(title="Python Developer", location="Ahmedabad", count=5):
    print(f"\n[PIPELINE] Starting live web search for {title} in {location}...")
    
    # Multiple query variations to maximize hits
    queries = [
        f'{title} {location} careers hr email site:.com',
        f'{title} job {location} company hiring',
        f'{title} {location} apply email',
    ]
    
    all_links = []
    for q in queries:
        links = perform_ddg_search(q, 10)
        all_links.extend(links)
    
    # Deduplicate links
    seen_urls = set()
    ddg_links = []
    for link in all_links:
        domain = link.split("://")[-1].split("/")[0].replace("www.", "")
        if domain not in seen_urls:
            seen_urls.add(domain)
            ddg_links.append(link)
    
    if not ddg_links:
        print("[FAIL] Web search returned no links or was blocked.")
        return []
        
    print(f"[PIPELINE] Found {len(ddg_links)} unique domains. Analyzing pages...")
    session = requests.Session()
    verified_jobs = []
    seen_domains = set()
    
    aggregators = ['naukri', 'glassdoor', 'monster', 'foundit', 
                   'hirist', 'cutshort', 'simplyhired', 'jobsora', 'internshala', 
                   'place1india', 'jooble', 'ambitionbox', 'techgig', 'shine', 
                   'freshersworld', 'naukrigulf', 'apna', 'iimjobs', 'timesjobs',
                   'ziprecruiter', 'wellfound', 'angellist', 'instahyre', 'hirect',
                   'google', 'facebook', 'twitter', 'youtube', 'wikipedia', 'github',
                   'stackoverflow', 'reddit', 'quora', 'medium', 'wordpress']
    
    for real_url in ddg_links:
        if len(verified_jobs) >= count:
            break
        try:
            domain = real_url.split("://")[-1].split("/")[0].replace("www.", "")
            company_name = domain.split(".")[0].capitalize()
            
            # 1. Skip aggregators and known non-company types based on domain
            bad_domain_keywords = [
                'placement', 'academy', 'institute', 
                'staffing', 'recruitment', 'classes', 'training', 'course', 'learn', 
                'tutorial', 'freelance', 'job', 'careers', 'hiring', 'expertini', 'internship'
            ]
            if domain in seen_domains or any(agg in domain for agg in aggregators) or any(bad in domain.lower() for bad in bad_domain_keywords):
                print(f"  [SKIP] Skipping domain (blacklisted/aggregator): {domain}")
                continue
            
            # Try the main URL first, then careers/contact pages
            pages_to_try = [
                real_url,
                f"https://{domain}/careers",
                f"https://{domain}/contact",
                f"https://{domain}/about",
                f"https://{domain}/jobs",
            ]
            
            print(f"  [CRAWL] Scanning company: {domain}")
            best_email = None
            is_valid_company = True
            
            for page_url in pages_to_try:
                try:
                    time.sleep(random.uniform(0.5, 1.5))
                    real_res = session.get(page_url, headers={"User-Agent": random.choice(USER_AGENTS)}, timeout=8)
                    if real_res.status_code == 200:
                        text_lower = real_res.text.lower()
                        # 2. Strict content check: If the page screams 'placement agency' or 'training', skip it.
                        if any(phrase in text_lower for phrase in ['placement agency', 'recruitment agency', 'staffing agency', 'training institute', 'it classes', 'course fees']):
                            print(f"    -> [SKIP] Detected agency/training content in page.")
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
                print(f"    -> [VERIFIED SUCCESS] Extracted HR email: {best_email}")
                verified_jobs.append({
                    "job_title": title,
                    "company": company_name,
                    "email": best_email,
                    "source": "Live Web Search"
                })
                seen_domains.add(domain)
            else:
                # No email found on page — try common patterns and verify via DNS/SMTP
                guessed_email = None
                try:
                    from email_verifier import verify_email as verify_deliverable
                    common_prefixes = ['careers', 'hr', 'jobs', 'hiring', 'info', 'career', 'hello']
                    for prefix in common_prefixes:
                        candidate_email = f"{prefix}@{domain}"
                        is_ok, reason = verify_deliverable(candidate_email)
                        if is_ok:
                            guessed_email = candidate_email
                            break
                except Exception:
                    pass
                
                if guessed_email:
                    print(f"    -> [PATTERN MATCH] Verified: {guessed_email}")
                    verified_jobs.append({
                        "job_title": title,
                        "company": company_name,
                        "email": guessed_email,
                        "source": "Pattern + DNS Verified"
                    })
                    seen_domains.add(domain)
                else:
                    print(f"    -> [NO REAL EMAIL] Skipped.")
                 
        except Exception as e:
            print(f"    -> [ERROR] Failed: {e}")
            
    return verified_jobs
    
if __name__ == "__main__":
    results = run_dynamic_pipeline("AI Intern", "Ahmedabad", count=5)
    print("\n--- TEST RUN RESULTS ---")
    for j in results:
         print(f"{j['job_title']} | {j['company']} | {j['email']}")

