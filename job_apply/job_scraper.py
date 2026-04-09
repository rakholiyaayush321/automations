#!/usr/bin/env python3
"""
Browser-based Job Scraper for LinkedIn, Naukri, Indeed
Implements anti-block measures: delays, user-agent rotation
"""

import requests
import random
import time
from bs4 import BeautifulSoup
import json
from datetime import datetime
from pathlib import Path
import re

# User agent rotation
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36 Edg/121.0.0.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:123.0) Gecko/20100101 Firefox/123.0",
]

class JobScraper:
    def __init__(self):
        self.session = requests.Session()
        self.jobs = []
        self.request_count = 0
        self.max_requests = 15
        
    def _get_headers(self):
        """Rotate user agents and headers"""
        return {
            "User-Agent": random.choice(USER_AGENTS),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
        }
    
    def _delay(self, min_sec=2, max_sec=5):
        """Random delay between requests"""
        time.sleep(random.uniform(min_sec, max_sec))
    
    def _can_request(self):
        """Check if we haven't exceeded max requests"""
        if self.request_count >= self.max_requests:
            print(f"[WARN]️ Max requests ({self.max_requests}) reached. Stopping.")
            return False
        return True
    
    def scrape_linkedin_jobs(self, keywords="Python", location="Ahmedabad"):
        """
        Scrape LinkedIn Jobs
        Note: LinkedIn requires login for full access, so we use public job search
        """
        if not self._can_request():
            return []
        
        print(f"[SEARCH] Searching LinkedIn for '{keywords}' in {location}...")
        
        # LinkedIn public job search URL
        url = f"https://www.linkedin.com/jobs/search/?keywords={keywords.replace(' ', '%20')}&location={location.replace(' ', '%20')}%2C%20Gujarat%2C%20India"
        
        try:
            self._delay(3, 6)
            response = self.session.get(url, headers=self._get_headers(), timeout=15)
            self.request_count += 1
            
            if response.status_code != 200:
                print(f"[WARN]️ LinkedIn returned {response.status_code}")
                return []
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # LinkedIn job cards
            job_cards = soup.find_all('div', {'data-job-id': True})
            
            jobs = []
            for card in job_cards[:10]:  # Limit to top 10
                try:
                    job_id = card.get('data-job-id', '')
                    title_elem = card.find('h3') or card.find('a')
                    company_elem = card.find('h4') or card.find(class_=re.compile('company'))
                    location_elem = card.find(class_=re.compile('location'))
                    
                    job = {
                        'source': 'LinkedIn',
                        'job_id': job_id,
                        'title': title_elem.text.strip() if title_elem else 'N/A',
                        'company': company_elem.text.strip() if company_elem else 'N/A',
                        'location': location_elem.text.strip() if location_elem else location,
                        'url': f"https://www.linkedin.com/jobs/view/{job_id}" if job_id else url,
                    }
                    jobs.append(job)
                except Exception as e:
                    print(f"[WARN]️ Error parsing job card: {e}")
                    continue
            
            print(f"[OK] Found {len(jobs)} jobs on LinkedIn")
            return jobs
            
        except Exception as e:
            print(f"[FAIL] LinkedIn scraping failed: {e}")
            return []
    
    def scrape_naukri_jobs(self, keywords="Python", location="Ahmedabad"):
        """
        Scrape Naukri.com jobs
        """
        if not self._can_request():
            return []
        
        print(f"[SEARCH] Searching Naukri for '{keywords}' in {location}...")
        
        url = f"https://www.naukri.com/{keywords.lower().replace(' ', '-')}-jobs-in-{location.lower()}"
        
        try:
            self._delay(2, 5)
            response = self.session.get(url, headers=self._get_headers(), timeout=15)
            self.request_count += 1
            
            if response.status_code != 200:
                print(f"[WARN]️ Naukri returned {response.status_code}")
                return []
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Naukri job cards
            job_cards = soup.find_all('article', class_=re.compile('jobTuple'))
            
            jobs = []
            for card in job_cards[:10]:
                try:
                    title_elem = card.find('a', class_=re.compile('title'))
                    company_elem = card.find('a', class_=re.compile('company'))
                    location_elem = card.find('span', class_=re.compile('location'))
                    
                    job = {
                        'source': 'Naukri',
                        'title': title_elem.text.strip() if title_elem else 'N/A',
                        'company': company_elem.text.strip() if company_elem else 'N/A',
                        'location': location_elem.text.strip() if location_elem else location,
                        'url': title_elem['href'] if title_elem and 'href' in title_elem.attrs else url,
                    }
                    jobs.append(job)
                except Exception as e:
                    continue
            
            print(f"[OK] Found {len(jobs)} jobs on Naukri")
            return jobs
            
        except Exception as e:
            print(f"[FAIL] Naukri scraping failed: {e}")
            return []
    
    def scrape_company_careers(self, company_url):
        """
        Scrape individual company career pages
        Priority source as per instructions
        """
        if not self._can_request():
            return []
        
        print(f"[SEARCH] Checking company careers: {company_url}...")
        
        try:
            self._delay(2, 4)
            response = self.session.get(company_url, headers=self._get_headers(), timeout=10)
            self.request_count += 1
            
            if response.status_code != 200:
                return []
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Look for Python-related job links
            job_links = []
            for link in soup.find_all('a', href=True):
                href = link['href'].lower()
                text = link.text.lower()
                if any(k in href or text for k in ['python', 'developer', 'intern', 'engineer', 'ai', 'ml']):
                    job_links.append({
                        'title': link.text.strip(),
                        'url': href if href.startswith('http') else company_url + href
                    })
            
            return job_links[:5]
            
        except Exception as e:
            print(f"[FAIL] Company page failed: {e}")
            return []
    
    def run_full_search(self, keywords_list=None):
        """
        Run complete job search across all sources
        """
        if keywords_list is None:
            keywords_list = ["Python Intern", "AI ML Intern", "Junior Python Developer", "Python Fresher"]
        
        all_jobs = []
        
        print("="*60)
        print("[SEARCH] STARTING BROWSER-BASED JOB SEARCH")
        print("="*60)
        print(f"Max requests: {self.max_requests}")
        print(f"Keywords: {', '.join(keywords_list)}")
        print("="*60)
        
        # Priority 1: LinkedIn
        for keyword in keywords_list[:2]:  # Limit to save requests
            if not self._can_request():
                break
            jobs = self.scrape_linkedin_jobs(keyword, "Ahmedabad")
            all_jobs.extend(jobs)
            self._delay(3, 6)
        
        # Priority 2: Naukri (if requests remaining)
        if self._can_request():
            jobs = self.scrape_naukri_jobs("Python", "Ahmedabad")
            all_jobs.extend(jobs)
        
        # Save results
        results = {
            'search_date': datetime.now().isoformat(),
            'total_requests': self.request_count,
            'total_jobs_found': len(all_jobs),
            'jobs': all_jobs
        }
        
        output_file = Path(__file__).parent / f"scraped_jobs_{datetime.now().strftime('%Y-%m-%d')}.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        print("="*60)
        print(f"[OK] Search complete!")
        print(f"📊 Total jobs found: {len(all_jobs)}")
        print(f"📝 Saved to: {output_file}")
        print("="*60)
        
        return results

if __name__ == "__main__":
    scraper = JobScraper()
    results = scraper.run_full_search()
    print(f"\nRequests made: {results['total_requests']}")
    print(f"Jobs found: {results['total_jobs_found']}")
