"""
email_verifier.py - Advanced Pre-send Email Verification Engine
===============================================================
Features: Format + Typo + DNS (MX/SPF/DMARC) + Catch-all + SMTP check
Returns robust dictionary with Confidence Scoring and Reputation metrics.
"""

import difflib
import json
import logging
import random
import smtplib
import socket
import string
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta
from pathlib import Path
from typing import Tuple, Dict, Any

try:
    import dns.resolver
    HAS_DNS = True
except ImportError:
    HAS_DNS = False

# ── Config ───────────────────────────────────────────────────────────────────
PROJECT_DIR = Path(__file__).parent
CACHE_FILE = PROJECT_DIR / "verified_emails.json"
CACHE_TTL_DAYS = 7  
SMTP_TIMEOUT = 10   
SENDER_EMAIL = "rakholiyaayush894@gmail.com"
MAX_SMTP_RETRIES = 2
RETRY_DELAY = 2  
BATCH_MAX_WORKERS = 10

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("email_verifier")

KNOWN_BAD_TLDS = {".example", ".test", ".invalid", ".localhost"}

DISPOSABLE_DOMAINS = {
    "mailinator.com", "yopmail.com", "10minutemail.com", "guerrillamail.com", 
    "temp-mail.org", "trashmail.com", "getnada.com", "throwawaymail.com",
    "sharklasers.com", "maildrop.cc", "anonaddy.me", "tempmail.net"
}

POPULAR_DOMAINS = ["gmail.com", "yahoo.com", "outlook.com", "hotmail.com", "iCloud.com"]

ROLE_ACCOUNTS = {
    "admin", "info", "support", "sales", "contact", "webmaster", 
    "postmaster", "hostmaster", "careers", "jobs", "hr", "hello", "marketing"
}


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
    except OSError as e:
        logger.warning(f"Could not save verification cache: {e}")

def _cache_get(email: str) -> Dict[str, Any] | None:
    cache = _load_cache()
    entry = cache.get(email)
    if not entry:
        return None

    try:
        cached_at = datetime.fromisoformat(entry.get("checked_at", "1970-01-01T00:00:00"))
    except ValueError:
        return None

    if datetime.now() - cached_at > timedelta(days=CACHE_TTL_DAYS):
        return None  

    # Handle old cache formats
    if "score" not in entry or isinstance(entry.get("valid"), bool):
        return None # Invalidate old simple string/bool cache because we want rich dicts now

    return entry

def _cache_set(email: str, result_dict: dict) -> None:
    cache = _load_cache()
    # Shallow copy to add checked_at explicitly
    entry = dict(result_dict)
    entry["checked_at"] = datetime.now().isoformat()
    cache[email] = entry
    _save_cache(cache)


# ── Typo & Role Detection ────────────────────────────────────────────────────
def check_typos_and_roles(local: str, domain: str) -> Tuple[bool, bool]:
    is_role = local in ROLE_ACCOUNTS
    is_typo = False
    
    if domain not in POPULAR_DOMAINS:
        matches = difflib.get_close_matches(domain, POPULAR_DOMAINS, n=1, cutoff=0.85)
        if matches and matches[0] != domain:
            is_typo = True
    
    return is_role, is_typo


# ── DNS Check (MX, SPF, DMARC) ───────────────────────────────────────────────
def check_dns(domain: str) -> Dict[str, Any]:
    res = {
        "has_mx": False,
        "mx_hosts": [],
        "mx_msg": "",
        "has_spf": False,
        "has_dmarc": False
    }

    if not HAS_DNS:
        res["has_mx"] = True
        res["mx_msg"] = "DNS library unavailable"
        return res

    for bad_tld in KNOWN_BAD_TLDS:
        if domain.endswith(bad_tld):
            res["mx_msg"] = f"Invalid/Test TLD: {bad_tld}"
            return res

    if domain in DISPOSABLE_DOMAINS:
        res["mx_msg"] = f"Disposable domain blocked: {domain}"
        return res

    # Check MX
    try:
        answers = dns.resolver.resolve(domain, "MX")
        mx_hosts = sorted([(r.preference, str(r.exchange).rstrip(".")) for r in answers], key=lambda x: x[0])
        if mx_hosts:
            res["has_mx"] = True
            res["mx_hosts"] = [h[1] for h in mx_hosts]
            res["mx_msg"] = "MX records found"
    except dns.resolver.NoAnswer:
        try:
            dns.resolver.resolve(domain, "A")
            res["has_mx"] = True
            res["mx_hosts"] = [domain]
            res["mx_msg"] = "No MX but A record exists (implicit MX)"
        except Exception:
            pass
    except Exception as e:
        res["mx_msg"] = f"DNS Error solving MX: {str(e)}"

    # If domain explicitly doesn't have MX, no need to check SPF/DMARC
    if not res["has_mx"] and not res["mx_hosts"]:
        if not res["mx_msg"]:
            res["mx_msg"] = "Domain does not exist or has no MX records"
        return res

    # Check SPF
    try:
        txt_answers = dns.resolver.resolve(domain, "TXT")
        for rdata in txt_answers:
            if b"v=spf1" in rdata.strings[0]:
                res["has_spf"] = True
                break
    except Exception:
        pass

    # Check DMARC
    try:
        dmarc_domain = f"_dmarc.{domain}"
        dmarc_answers = dns.resolver.resolve(dmarc_domain, "TXT")
        for rdata in dmarc_answers:
            if b"v=DMARC1" in rdata.strings[0]:
                res["has_dmarc"] = True
                break
    except Exception:
        pass

    return res


# ── Catch-All Detection ─────────────────────────────────────────────────────
def is_catch_all(mx_hosts: list, domain: str) -> bool:
    if not mx_hosts:
        return False

    fake_user = ''.join(random.choices(string.ascii_lowercase + string.digits, k=15))
    fake_email = f"{fake_user}@{domain}"

    for mx_host in mx_hosts[:1]:
        for port in [25, 587, 465]:
            for _ in range(2):
                try:
                    if port == 465:
                        server = smtplib.SMTP_SSL(timeout=SMTP_TIMEOUT)
                    else:
                        server = smtplib.SMTP(timeout=SMTP_TIMEOUT)
                    server.connect(mx_host, port)
                    server.helo("verify.local")
                    server.mail(SENDER_EMAIL)
                    code, _ = server.rcpt(fake_email)
                    server.quit()
                    if code == 250:
                        return True
                    return False
                except Exception:
                    time.sleep(RETRY_DELAY)
                    continue
    return False


# ── SMTP RCPT TO Check ──────────────────────────────────────────────────────
def check_smtp_recipient(email: str, mx_hosts: list, domain: str) -> Tuple[str, str, bool]:
    if not mx_hosts:
        return "invalid", "No MX hosts available", False

    catch_all = is_catch_all(mx_hosts, domain)

    for mx_host in mx_hosts[:2]:
        for port in [25, 587, 465]:
            for attempt in range(MAX_SMTP_RETRIES):
                try:
                    if port == 465:
                        server = smtplib.SMTP_SSL(timeout=SMTP_TIMEOUT)
                    else:
                        server = smtplib.SMTP(timeout=SMTP_TIMEOUT)
                    server.connect(mx_host, port)
                    server.helo("verify.local")
                    server.mail(SENDER_EMAIL)
                    code, msg = server.rcpt(email)
                    server.quit()
    
                    if code == 250:
                        if catch_all:
                            return "risky", "Domain is catch-all (accepted, but deliverability unconfirmed)", catch_all
                        return "valid", "SMTP accepted recipient", catch_all
                    elif code in (550, 551, 553):
                        msg_lower = str(msg).lower()
                        if "auth" in msg_lower or "authentication" in msg_lower or "relay" in msg_lower:
                            # Submission ports (587/465) require auth, this is not a recipient rejection
                            raise Exception(f"Port {port} requires authentication")
                        return "invalid", f"SMTP rejected recipient (Code: {code} {msg})", catch_all
                    elif code in (450, 451, 452):
                        return "risky", f"Temporary response (greylisting/overload, Code: {code})", catch_all
                    else:
                        return "invalid", f"SMTP rejected: {code} {msg}", catch_all
    
                except (smtplib.SMTPServerDisconnected, smtplib.SMTPConnectError,
                        socket.timeout, ConnectionRefusedError, OSError):
                    time.sleep(RETRY_DELAY)
                    continue
                except Exception:
                    time.sleep(RETRY_DELAY)
                    continue

    return "risky", "Could not connect to MX servers (port 25 blocked or timeout) - Cannot verify", catch_all


# ── Public API ───────────────────────────────────────────────────────────────
def verify_email(email: str) -> Dict[str, Any]:
    """
    Advanced verification pipeline yielding rich dictionary results.
    """
    email = email.strip().lower()

    # Base structure
    result = {
        "email": email,
        "status": "valid",
        "score": 100,
        "reason": "",
        "details": {
            "syntax_valid": False,
            "is_role_account": False,
            "is_typo": False,
            "is_catch_all": False,
            "has_spf": False,
            "has_dmarc": False
        }
    }

    if not email or "@" not in email:
        result["status"] = "invalid"
        result["score"] = 0
        result["reason"] = "Invalid email formatting"
        return result

    local, domain = email.split("@", 1)
    if not domain or "." not in domain or " " in domain:
        result["status"] = "invalid"
        result["score"] = 0
        result["reason"] = "Invalid domain formatting"
        return result

    result["details"]["syntax_valid"] = True

    cached = _cache_get(email)
    if cached is not None:
        # Cache Hit!
        return cached

    # Typo and Role Checks
    is_role, is_typo = check_typos_and_roles(local, domain)
    result["details"]["is_role_account"] = is_role
    result["details"]["is_typo"] = is_typo

    if is_role: result["score"] -= 20
    if is_typo: 
        result["score"] -= 100
        result["status"] = "invalid"
        result["reason"] = "Domain typo detected"
        _cache_set(email, result)
        return result

    # DNS Checks
    dns_res = check_dns(domain)
    result["details"]["has_spf"] = dns_res.get("has_spf", False)
    result["details"]["has_dmarc"] = dns_res.get("has_dmarc", False)

    if not dns_res["has_spf"]: result["score"] -= 10
    if not dns_res["has_dmarc"]: result["score"] -= 10

    if not dns_res["has_mx"]:
        result["score"] = 0
        result["status"] = "invalid"
        result["reason"] = f"MX lookup failed: {dns_res['mx_msg']}"
        _cache_set(email, result)
        return result

    # Disposables Check
    if domain in DISPOSABLE_DOMAINS:
        result["score"] = 0
        result["status"] = "invalid"
        result["reason"] = "Disposable email provider detected"
        _cache_set(email, result)
        return result

    # SMTP Checks (+ Catch-all)
    smtp_status, smtp_msg, catch_all = check_smtp_recipient(email, dns_res["mx_hosts"], domain)
    result["details"]["is_catch_all"] = catch_all

    if catch_all: result["score"] -= 30

    if smtp_status == "invalid":
        result["score"] = 0
        result["status"] = "invalid"
        result["reason"] = f"SMTP Verification Failed: {smtp_msg}"
    elif smtp_status == "risky":
        result["score"] -= 40
        # Prevent score from going below 1 if it's technically risky rather than invalid
        result["score"] = max(result["score"], 10) 
        result["status"] = "risky"
        result["reason"] = smtp_msg
    else:
        # Valid SMTP, update status only if it isn't already degraded
        if result["score"] < 50:
            result["status"] = "risky"
        else:
            result["status"] = "valid"
        result["reason"] = f"Verification successful (Score: {result['score']})"

    _cache_set(email, result)
    return result


def _verify_single(email: str, company: str) -> Dict[str, Any]:
    res = verify_email(email)
    res["company"] = company
    return res


def verify_batch(emails: list) -> dict:
    verified, risky, failed = [], [], []

    with ThreadPoolExecutor(max_workers=BATCH_MAX_WORKERS) as executor:
        futures = {executor.submit(_verify_single, email, company): (email, company) for email, company in emails}
        
        for future in as_completed(futures):
            eval_res = future.result()
            email = eval_res["email"]
            company = eval_res["company"]
            st = eval_res["status"]

            if st == "valid":
                verified.append((email, company))
            elif st == "risky":
                risky.append((email, company, eval_res["reason"]))
            else:
                failed.append((email, company, eval_res["reason"]))

    return {
        "verified": verified,
        "risky": risky,
        "failed": failed,
        "stats": {
            "total": len(emails),
            "passed": len(verified),
            "risky": len(risky),
            "failed": len(failed),
        },
    }

# ── CLI ──────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import sys

    print("=" * 60)
    print("EMAIL VERIFIER — ADVANCED ENGINE")
    print("=" * 60)

    test_emails = [
        ("careers@solulab.com", "SoluLab"),
        ("hr@gmail.com", "Google (Role Account)"),
        ("randomfake1234xx@gmial.com", "Typo Domain"),
        ("testing@mailinator.com", "Disposable"),
    ]

    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        results = verify_batch(test_emails)
        print(f"\n--- Results ---")
        print(f"Passed: {results['stats']['passed']}")
        print(f"Risky:  {results['stats']['risky']}")
        print(f"Failed: {results['stats']['failed']}\n")
    else:
        print("Usage: python email_verifier.py --test")
