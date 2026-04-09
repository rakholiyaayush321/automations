"""
run_strict.py - Strict email validation workflow
================================================
Validates all emails before sending, replaces invalid ones.
"""

import re
import sys
import time
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from config import EMAIL_DELAY_SECONDS, RETRY_DELAY_SECONDS
from emailer_enhanced import validate_email, send_email_with_retry

JOBS_FILE = Path(__file__).parent / "jobs.txt"
LOG_FILE = Path(__file__).parent / "strict_run.log"


def log_message(msg: str, level: str = "INFO"):
    """Log message to file and print."""
    timestamp = datetime.now().strftime("%H:%M:%S")
    full_msg = f"[{timestamp}] [{level}] {msg}"
    print(full_msg)
    
    # Append to log
    with open(LOG_FILE, 'a', encoding='utf-8') as f:
        f.write(full_msg + "\n")


def load_jobs():
    """Load jobs from jobs.txt."""
    jobs = []
    if not JOBS_FILE.exists():
        log_message("No jobs.txt found!", "ERROR")
        return jobs
    
    with open(JOBS_FILE, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            
            parts = line.split('|')
            if len(parts) >= 3:
                jobs.append({
                    'title': parts[0].strip(),
                    'company': parts[1].strip(),
                    'email': parts[2].strip()
                })
    
    return jobs


def validate_and_send_jobs(jobs: list, target: int = 20):
    """
    Strict validation workflow:
    1. Validate all emails first
    2. Replace invalid emails
    3. Send only to valid emails
    4. Track replacements
    """
    valid_jobs = []
    invalid_count = 0
    replaced_count = 0
    
    log_message(f"Starting strict validation for {len(jobs)} jobs")
    log_message(f"Target: {target} successful applications")
    
    # Step 1: Validate all emails
    for i, job in enumerate(jobs):
        email = job['email']
        company = job['company']
        
        is_valid, reason = validate_email(email)
        
        if is_valid:
            valid_jobs.append(job)
            log_message(f"[{i+1}] ✓ {company}: {email} - VALID")
        else:
            invalid_count += 1
            log_message(f"[{i+1}] ✗ {company}: {email} - INVALID ({reason})")
            
            # Try to find alternative email
            alt_email = find_alternative_email(company)
            if alt_email:
                job['email'] = alt_email
                job['replaced'] = True
                valid_jobs.append(job)
                replaced_count += 1
                log_message(f"    → Replaced with: {alt_email}")
            else:
                log_message(f"    → No alternative found, SKIPPED")
    
    log_message(f"\nValidation Complete:")
    log_message(f"  Valid: {len(valid_jobs) - replaced_count}")
    log_message(f"  Replaced: {replaced_count}")
    log_message(f"  Invalid (skipped): {invalid_count - replaced_count}")
    
    # Step 2: Send to valid jobs
    sent_count = 0
    failed_count = 0
    
    log_message(f"\nStarting email sending...")
    
    for i, job in enumerate(valid_jobs[:target]):
        if sent_count >= target:
            break
        
        company = job['company']
        email = job['email']
        title = job['title']
        
        log_message(f"\n[{sent_count + 1}/{target}] Sending to {company}...")
        
        # Send email
        result = send_email_with_retry(email, company, title)
        
        if result['status'] == 'sent':
            sent_count += 1
            status = "SENT"
            if job.get('replaced'):
                status += " (replaced email)"
            log_message(f"  ✓ {status}: {email}")
        else:
            failed_count += 1
            log_message(f"  ✗ FAILED: {result['message']}")
            
            # Try alternative
            alt_email = find_alternative_email(company)
            if alt_email and alt_email != email:
                log_message(f"    → Trying alternative: {alt_email}")
                result2 = send_email_with_retry(alt_email, company, title)
                if result2['status'] == 'sent':
                    sent_count += 1
                    log_message(f"    ✓ SENT (alternative): {alt_email}")
                else:
                    log_message(f"    ✗ Alternative also failed")
        
        # Delay before next
        if i < len(valid_jobs) - 1 and sent_count < target:
            delay = EMAIL_DELAY_SECONDS
            log_message(f"  Waiting {delay}s before next email...")
            time.sleep(delay)
    
    # Summary
    log_message(f"\n{'='*60}")
    log_message(f"STRICT RUN COMPLETE")
    log_message(f"{'='*60}")
    log_message(f"Target: {target}")
    log_message(f"Sent: {sent_count}")
    log_message(f"Failed: {failed_count}")
    log_message(f"Success Rate: {(sent_count/max(sent_count+failed_count,1))*100:.1f}%")
    
    return sent_count


def find_alternative_email(company: str) -> str:
    """
    Find alternative email for a company.
    In production, this would search company database or website.
    For now, returns None to skip.
    """
    # This is a placeholder - in real implementation, would:
    # 1. Check company database for alternative emails
    # 2. Try common patterns (hr@, info@, etc.)
    # 3. Return best alternative or None
    return None


def main():
    """Main entry point."""
    print("="*60)
    print("STRICT EMAIL VALIDATION WORKFLOW")
    print("="*60)
    
    # Load jobs
    jobs = load_jobs()
    if not jobs:
        print("No jobs to process!")
        return 1
    
    print(f"\nLoaded {len(jobs)} jobs from jobs.txt")
    print(f"Target: 20 successful applications\n")
    
    # Run strict validation and sending
    sent = validate_and_send_jobs(jobs, target=20)
    
    return 0 if sent >= 15 else 1


if __name__ == "__main__":
    sys.exit(main())
