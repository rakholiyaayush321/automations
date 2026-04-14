"""
emailer_enhanced.py - Enhanced email sender with multiple templates and retry logic
==============================================================================
"""

import json
import re
import smtplib
import socket
import time
from datetime import datetime
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path
from typing import Dict, List, Tuple

from config import (
    EMAIL_FROM, SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASSWORD,
    CANDIDATE, RESUME_PATH, EMAIL_PATTERNS, FAILED_EMAILS_FILE,
    EMAIL_DELAY_SECONDS, RETRY_DELAY_SECONDS, MAX_RETRIES
)

# ── Tracking Lists ────────────────────────────────────────────────────────────
class EmailTracker:
    """Track sent, failed emails and failed companies."""
    
    def __init__(self):
        self.sent_emails: List[str] = []
        self.failed_emails: List[Dict] = []
        self.failed_companies: List[str] = []
        self.current_company: str = "Unknown"
        self.invalid_emails: set = self._load_invalid_emails()
        
    def _load_invalid_emails(self) -> set:
        """Load previously failed emails from file."""
        if FAILED_EMAILS_FILE.exists():
            try:
                with open(FAILED_EMAILS_FILE, 'r') as f:
                    data = json.load(f)
                    return set(data.get('invalid_emails', []))
            except:
                return set()
        return set()
    
    def save_invalid_email(self, email: str, reason: str):
        """Mark email as invalid and save to file."""
        self.invalid_emails.add(email)
        self.failed_emails.append({
            'email': email,
            'reason': reason,
            'timestamp': datetime.now().isoformat(),
            'company': getattr(self, 'current_company', 'Unknown')
        })
        
        # Save to file
        data = {
            'invalid_emails': list(self.invalid_emails),
            'failed_emails': self.failed_emails
        }
        try:
            with open(FAILED_EMAILS_FILE, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"Warning: Could not save failed emails: {e}")
    
    def is_invalid(self, email: str) -> bool:
        """Check if email is already marked as invalid."""
        return email in self.invalid_emails
    
    def add_sent(self, email: str, company: str):
        """Mark email as successfully sent."""
        self.sent_emails.append(email)
        print(f"  [SUCCESS] Email sent to {company} ({email})")
    
    def add_failed_company(self, company: str):
        """Mark company as failed (all emails exhausted)."""
        self.failed_companies.append(company)
        print(f"  [FAILED COMPANY] {company} - All emails exhausted")


# Global tracker
tracker = EmailTracker()


# ── Email Validation ──────────────────────────────────────────────────────────
def validate_email(email: str) -> Tuple[bool, str]:
    """
    Validate email format and check if it's usable.
    
    Returns:
        (is_valid, reason)
    """
    # Check format
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(pattern, email):
        return False, "Invalid email format"
    
    # Check if already marked invalid
    if tracker.is_invalid(email):
        return False, "Email previously failed"
    
    # Check for system emails
    system_patterns = [
        'noreply@', 'no-reply@', 'donotreply@', 'admin@',
        'postmaster@', 'webmaster@', 'root@', 'support@',
        'help@', 'feedback@', 'abuse@'
    ]
    email_lower = email.lower()
    for pattern in system_patterns:
        if pattern in email_lower:
            return False, f"System email detected ({pattern})"
    
    # Extract domain
    try:
        domain = email.split('@')[1]
        if not domain or '.' not in domain:
            return False, "Invalid domain"
    except:
        return False, "Cannot extract domain"
    
    return True, "Valid"


# ── Email Generation ─────────────────────────────────────────────────────────
def generate_alternative_emails(company_name: str, website: str) -> List[str]:
    """Generate alternative email addresses for a company."""
    emails = []
    
    # Extract domain from website
    domain = website.replace('https://', '').replace('http://', '').replace('www.', '').strip('/')
    
    # Generate emails using patterns
    for pattern in EMAIL_PATTERNS:
        email = pattern.format(domain=domain)
        emails.append(email)
    
    # Remove duplicates while preserving order
    seen = set()
    unique_emails = []
    for email in emails:
        if email not in seen:
            seen.add(email)
            unique_emails.append(email)
    
    return unique_emails


# ── SMTP Connection ──────────────────────────────────────────────────────────
def get_smtp_connection():
    """Create and return SMTP connection."""
    if not SMTP_PASSWORD:
        raise ValueError("SMTP password not set (GMAIL_APP_PASSWORD environment variable)")
    
    server = smtplib.SMTP(SMTP_HOST, SMTP_PORT)
    server.starttls()
    server.login(SMTP_USER, SMTP_PASSWORD)
    return server


# ── Email Sending ────────────────────────────────────────────────────────────
def send_email_with_retry(
    to_email: str,
    company_name: str,
    job_title: str,
    resume_path: Path = None,
    max_retries: int = MAX_RETRIES
) -> Dict:
    """
    Send email with retry logic for temporary failures.
    
    Returns:
        {
            'status': 'sent' | 'failed' | 'skipped',
            'message': str,
            'attempts': int,
            'timestamp': str
        }
    """
    from config import build_email_body
    
    # Validate email first
    is_valid, reason = validate_email(to_email)
    if not is_valid:
        tracker.save_invalid_email(to_email, reason)
        return {
            'status': 'skipped',
            'message': reason,
            'attempts': 0,
            'timestamp': datetime.now().isoformat()
        }
    
    # Pre-send verification: DNS MX + SMTP RCPT TO check
    try:
        from email_verifier import verify_email as verify_deliverable
        is_deliverable, verify_reason = verify_deliverable(to_email)
        if not is_deliverable:
            print(f"  [VERIFY-FAIL] {to_email}: {verify_reason}")
            tracker.save_invalid_email(to_email, f"Pre-send verification: {verify_reason}")
            return {
                'status': 'skipped',
                'message': f"Pre-send verification: {verify_reason}",
                'attempts': 0,
                'timestamp': datetime.now().isoformat()
            }
        else:
            print(f"  [VERIFY-OK] {to_email}: {verify_reason}")
    except ImportError:
        print(f"  [WARN] email_verifier not available, skipping pre-send check")
    except Exception as e:
        print(f"  [WARN] Pre-send verification error: {e}")
    
    # Look up HR manager name for personalized greeting
    hr_name = ""
    hr_role = ""
    try:
        from hr_finder import find_hr_contact
        hr_info = find_hr_contact(company_name, email=to_email)
        if hr_info["found"]:
            hr_name = hr_info["first_name"]
            hr_role = hr_info["role"]
            print(f"  [HR] Found: {hr_info['name']} ({hr_role}) -> {hr_info['greeting']}")
        else:
            print(f"  [HR] No contact found -> Dear Hiring Manager")
    except ImportError:
        print(f"  [WARN] hr_finder not available, using generic greeting")
    except Exception as e:
        print(f"  [WARN] HR lookup error: {e}")
    
    # Generate email content
    # Try dynamic ChatGPT generation first (free proxy)
    try:
        from llm_generator import generate_cold_email
        llm_subject, llm_body = generate_cold_email(job_title, company_name, hr_name=hr_name, hr_role=hr_role)
    except Exception as e:
        print(f"  [WARN] Error calling LLM generator: {e}")
        llm_subject, llm_body = None, None
        
    if llm_subject and llm_body:
        subject, body = llm_subject, llm_body
    else:
        # Safe fallback to static configuration
        greeting = f"Dear {hr_name}" if hr_name else "Dear Hiring Manager"
        subject, body = build_email_body(job_title, company_name, greeting=greeting)
    
    # Attempt sending
    for attempt in range(max_retries + 1):
        try:
            # Create message
            msg = MIMEMultipart()
            msg['From'] = EMAIL_FROM
            msg['To'] = to_email
            msg['Subject'] = subject
            
            # Attach body
            msg.attach(MIMEText(body, 'plain', 'utf-8'))
            
            # Use global RESUME_PATH if none provided
            actual_resume_path = resume_path if resume_path is not None else RESUME_PATH
            
            # Attach resume if exists
            if actual_resume_path and actual_resume_path.exists():
                with open(actual_resume_path, 'rb') as f:
                    pdf_attachment = MIMEApplication(f.read(), _subtype='pdf')
                    pdf_attachment.add_header(
                        'Content-Disposition',
                        'attachment',
                        filename=f"{CANDIDATE['name'].replace(' ', '_')}_Resume.pdf"
                    )
                    msg.attach(pdf_attachment)
            
            # Send email
            server = get_smtp_connection()
            server.send_message(msg)
            server.quit()
            
            # Success!
            tracker.add_sent(to_email, company_name)
            return {
                'status': 'sent',
                'message': 'Email sent successfully',
                'attempts': attempt + 1,
                'timestamp': datetime.now().isoformat()
            }
            
        except smtplib.SMTPRecipientsRefused as e:
            # Hard failure - recipient rejected
            tracker.save_invalid_email(to_email, f"Recipient refused: {str(e)}")
            return {
                'status': 'failed',
                'message': f"Recipient refused: {str(e)}",
                'attempts': attempt + 1,
                'timestamp': datetime.now().isoformat()
            }
            
        except (socket.gaierror, socket.error, ConnectionError, smtplib.SMTPConnectError) as e:
            # Network issue - temporary failure
            print(f"  [RETRY] Network connection error, waiting {RETRY_DELAY_SECONDS}s...")
            if attempt < max_retries:
                time.sleep(RETRY_DELAY_SECONDS)
                continue
            else:
                return {
                    'status': 'failed',
                    'message': f"Network error: {str(e)}",
                    'attempts': attempt + 1,
                    'timestamp': datetime.now().isoformat()
                }
            
        except smtplib.SMTPException as e:
            error_msg = str(e).lower()
            
            # Check for hard failures
            hard_failures = [
                '550', '554', '553', '501', '503',  # SMTP error codes
                'user unknown', 'mailbox unavailable',
                'domain not found', 'address rejected',
                'invalid', 'does not exist', 'not found'
            ]
            
            is_hard_failure = any(hf in error_msg for hf in hard_failures)
            
            if is_hard_failure or attempt == max_retries:
                # Mark as invalid and fail
                tracker.save_invalid_email(to_email, str(e))
                return {
                    'status': 'failed',
                    'message': str(e),
                    'attempts': attempt + 1,
                    'timestamp': datetime.now().isoformat()
                }
            else:
                # Temporary failure - retry after delay
                print(f"  [RETRY] Temporary failure, waiting {RETRY_DELAY_SECONDS}s...")
                time.sleep(RETRY_DELAY_SECONDS)
                continue
                
        except Exception as e:
            # Unknown error - mark as failed
            tracker.save_invalid_email(to_email, f"Unexpected error: {str(e)}")
            return {
                'status': 'failed',
                'message': f"Unexpected error: {str(e)}",
                'attempts': attempt + 1,
                'timestamp': datetime.now().isoformat()
            }
    
    # Should not reach here
    return {
        'status': 'failed',
        'message': 'Max retries exceeded',
        'attempts': max_retries + 1,
        'timestamp': datetime.now().isoformat()
    }


def send_to_company(
    company_name: str,
    website: str,
    job_title: str,
    primary_email: str = None
) -> Dict:
    """
    Try to send email to a company using primary email or alternatives.
    
    Returns:
        {
            'status': 'sent' | 'failed',
            'email_used': str | None,
            'message': str
        }
    """
    tracker.current_company = company_name
    
    # Get list of emails to try
    emails_to_try = []
    
    if primary_email:
        is_valid, _ = validate_email(primary_email)
        if is_valid:
            emails_to_try.append(primary_email)
    
    # Generate alternatives
    alternative_emails = generate_alternative_emails(company_name, website)
    for email in alternative_emails:
        if email not in emails_to_try:
            emails_to_try.append(email)
    
    # Try each email
    for email in emails_to_try:
        print(f"  [TRY] {email}...")
        result = send_email_with_retry(email, company_name, job_title)
        
        if result['status'] == 'sent':
            return {
                'status': 'sent',
                'email_used': email,
                'message': result['message']
            }
        
        # If hard failure, try next email
        if result['status'] == 'failed':
            print(f"  [FAILED] {email} - trying next...")
            continue
    
    # All emails failed
    tracker.add_failed_company(company_name)
    return {
        'status': 'failed',
        'email_used': None,
        'message': 'All email attempts failed'
    }


def print_summary():
    """Print summary of email sending session."""
    print("\n" + "=" * 65)
    print("EMAIL SENDING SUMMARY")
    print("=" * 65)
    print(f"Successfully sent: {len(tracker.sent_emails)}")
    print(f"Failed emails: {len(tracker.failed_emails)}")
    print(f"Failed companies: {len(tracker.failed_companies)}")
    print(f"Invalid emails (total): {len(tracker.invalid_emails)}")
    print("=" * 65)


# ── Legacy Support ────────────────────────────────────────────────────────────
def send(to_email: str, company_name: str = None, job_title: str = None) -> Dict:
    """Legacy send function for backward compatibility."""
    tracker.current_company = company_name or "Unknown"
    if company_name and job_title:
        return send_email_with_retry(to_email, company_name, job_title)
    else:
        # Minimal send (used by test)
        return send_email_with_retry(to_email, "Unknown", "Unknown")


if __name__ == "__main__":
    print("Enhanced Emailer Module")
    print("Use this module by importing: from emailer_enhanced import send_to_company")
