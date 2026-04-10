"""
email_verifier.py - Pre-send email verification via DNS MX + SMTP RCPT TO
==========================================================================
Verifies that an email address can actually receive mail BEFORE sending.
Two-stage check:
  1. DNS MX lookup — does the domain have mail servers at all?
  2. SMTP RCPT TO — does the mail server accept this recipient?

Caches results in verified_emails.json to avoid redundant lookups.
"""

import json
import smtplib
import socket
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Tuple

try:
    import dns.resolver
    HAS_DNS = True
except ImportError:
    HAS_DNS = False

# ── Config ───────────────────────────────────────────────────────────────────
PROJECT_DIR = Path(__file__).parent
CACHE_FILE = PROJECT_DIR / "verified_emails.json"
CACHE_TTL_DAYS = 7  # Re-verify after 7 days
SMTP_TIMEOUT = 10   # seconds
SENDER_EMAIL = "rakholiyaayush894@gmail.com"

# Known bad domains (no mail servers / parked / fake)
KNOWN_BAD_TLDS = {".example", ".test", ".invalid", ".localhost"}


# ── Cache ────────────────────────────────────────────────────────────────────
def _load_cache() -> dict:
    """Load the verification cache."""
    if CACHE_FILE.exists():
        try:
            with open(CACHE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            return {}
    return {}


def _save_cache(cache: dict) -> None:
    """Persist the verification cache."""
    try:
        with open(CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(cache, f, indent=2, ensure_ascii=False)
    except OSError as e:
        print(f"  [WARN] Could not save verification cache: {e}")


def _cache_get(email: str) -> Tuple[bool, str] | None:
    """Return cached result if still valid, else None."""
    cache = _load_cache()
    entry = cache.get(email)
    if not entry:
        return None

    # Check TTL
    cached_at = datetime.fromisoformat(entry["checked_at"])
    if datetime.now() - cached_at > timedelta(days=CACHE_TTL_DAYS):
        return None  # expired

    return entry["valid"], entry["reason"]


def _cache_set(email: str, valid: bool, reason: str) -> None:
    """Store a verification result."""
    cache = _load_cache()
    cache[email] = {
        "valid": valid,
        "reason": reason,
        "checked_at": datetime.now().isoformat(),
    }
    _save_cache(cache)


# ── DNS MX Check ─────────────────────────────────────────────────────────────
def check_mx(domain: str) -> Tuple[bool, str, list]:
    """
    Check if the domain has MX records (can receive email).

    Returns:
        (has_mx, message, mx_hosts)
    """
    if not HAS_DNS:
        # Fallback: assume domain is valid (skip DNS check)
        return True, "DNS library not available, skipping MX check", []

    # Quick check for obviously bad TLDs
    for bad_tld in KNOWN_BAD_TLDS:
        if domain.endswith(bad_tld):
            return False, f"Test/invalid TLD: {bad_tld}", []

    try:
        answers = dns.resolver.resolve(domain, "MX")
        mx_hosts = sorted(
            [(r.preference, str(r.exchange).rstrip(".")) for r in answers],
            key=lambda x: x[0],
        )
        if mx_hosts:
            return True, "MX records found", [h[1] for h in mx_hosts]
        # No MX but resolve succeeded — assume valid (implicit MX)
        return True, "No MX records but domain resolves", [domain]

    except dns.resolver.NXDOMAIN:
        return False, "Domain does not exist (NXDOMAIN)", []
    except dns.resolver.NoAnswer:
        # Some domains use A record as implicit MX
        try:
            dns.resolver.resolve(domain, "A")
            return True, "No MX but A record exists (implicit MX)", [domain]
        except Exception:
            # DNS is unreliable — be lenient, assume valid
            return True, "DNS inconclusive — assuming valid", [domain]
    except dns.resolver.NoNameservers:
        # Network issue — assume valid and let SMTP handle it
        return True, "DNS nameserver issue — assuming valid", [domain]
    except dns.resolver.Timeout:
        # Network issue — assume valid and let SMTP handle it
        return True, "DNS timeout — assuming valid", [domain]
    except Exception as e:
        # Any other DNS error — assume valid
        return True, f"DNS error ({e}) — assuming valid", [domain]


# ── SMTP RCPT TO Check ──────────────────────────────────────────────────────
def check_smtp_recipient(email: str, mx_hosts: list) -> Tuple[bool, str]:
    """
    Connect to the MX server and test if the recipient exists.

    Returns:
        (accepted, message)
    """
    if not mx_hosts:
        # No MX hosts available — assume valid, let actual send handle failures
        return True, "No MX hosts available — assuming valid (will verify on send)"

    for mx_host in mx_hosts[:2]:  # Try top 2 MX servers
        try:
            server = smtplib.SMTP(timeout=SMTP_TIMEOUT)
            server.connect(mx_host, 25)
            server.helo("verify.local")
            server.mail(SENDER_EMAIL)
            code, msg = server.rcpt(email)
            server.quit()

            if code == 250:
                return True, "SMTP accepted recipient"
            elif code == 550:
                return False, f"Mailbox does not exist (550)"
            elif code == 553:
                return False, f"Mailbox name invalid (553)"
            elif code == 551:
                return False, f"User not local (551)"
            elif code in (450, 451, 452):
                # Temporary error — assume valid (greylisting, etc.)
                return True, f"Temporary response ({code}) — assuming valid"
            else:
                return False, f"SMTP rejected: {code} {msg}"

        except smtplib.SMTPServerDisconnected:
            continue
        except smtplib.SMTPConnectError:
            continue
        except socket.timeout:
            continue
        except ConnectionRefusedError:
            continue
        except OSError:
            continue
        except Exception:
            continue

    # Could not connect to any MX — assume valid if MX records exist
    # (many servers block port 25 from residential IPs)
    return True, "Could not connect to MX servers (port 25 blocked?) — assuming valid based on MX"


# ── Public API ───────────────────────────────────────────────────────────────
def verify_email(email: str) -> Tuple[bool, str]:
    """
    Full email verification pipeline:
      1. Format check
      2. Cache lookup
      3. DNS MX check
      4. SMTP RCPT TO check (if MX found)

    Returns:
        (is_deliverable, reason)
    """
    email = email.strip().lower()

    # Basic format check
    if not email or "@" not in email:
        return False, "Invalid email format"

    domain = email.split("@")[1]
    if not domain or "." not in domain:
        return False, "Invalid domain"

    # Spaces in domain = definitely fake
    if " " in domain:
        return False, f"Invalid domain (contains spaces): {domain}"

    # Check cache first
    cached = _cache_get(email)
    if cached is not None:
        return cached

    # Step 1: DNS MX check
    has_mx, mx_msg, mx_hosts = check_mx(domain)
    if not has_mx:
        _cache_set(email, False, f"MX check failed: {mx_msg}")
        return False, f"MX check failed: {mx_msg}"

    # Step 2: SMTP RCPT TO check
    accepted, smtp_msg = check_smtp_recipient(email, mx_hosts)
    if not accepted:
        _cache_set(email, False, f"SMTP rejected: {smtp_msg}")
        return False, f"SMTP rejected: {smtp_msg}"

    # Passed all checks
    _cache_set(email, True, f"Verified ({mx_msg}; {smtp_msg})")
    return True, f"Verified ({mx_msg}; {smtp_msg})"


def verify_batch(emails: list) -> dict:
    """
    Verify a list of emails. Returns summary dict.

    Args:
        emails: list of (email, company_name) tuples

    Returns:
        {
            'verified': [(email, company), ...],
            'failed': [(email, company, reason), ...],
            'stats': {'total': N, 'passed': N, 'failed': N}
        }
    """
    verified = []
    failed = []

    for email, company in emails:
        is_valid, reason = verify_email(email)
        if is_valid:
            verified.append((email, company))
        else:
            failed.append((email, company, reason))

        # Small delay to avoid overwhelming DNS/SMTP servers
        time.sleep(0.3)

    return {
        "verified": verified,
        "failed": failed,
        "stats": {
            "total": len(emails),
            "passed": len(verified),
            "failed": len(failed),
        },
    }


# ── CLI ──────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import sys

    print("=" * 60)
    print("EMAIL VERIFIER — DNS MX + SMTP RCPT TO")
    print("=" * 60)

    # Test with some known emails
    test_emails = [
        ("careers@solulab.com", "SoluLab"),
        ("careers@simform.com", "Simform"),
        ("careers@estanova.com", "ESTANOVA"),
        ("careers@techbud.in", "TechBud (fake)"),
        ("careers@fakexyz123domain.com", "Totally Fake"),
    ]

    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        results = verify_batch(test_emails)
        print(f"\n--- Results ---")
        print(f"Passed: {results['stats']['passed']}/{results['stats']['total']}")
        for email, company in results["verified"]:
            print(f"  [OK]   {company}: {email}")
        for email, company, reason in results["failed"]:
            print(f"  [FAIL] {company}: {email} — {reason}")
    else:
        print("Usage: python email_verifier.py --test")
        print("       Verifies a set of test emails to demonstrate the checker.")
