"""
main.py - Autonomous Job Application Orchestrator
=================================================
Commands:
  python main.py --run     Send applications to jobs in jobs.txt
  python main.py --dry     Test run without sending
  python main.py --test-email  Verify SMTP credentials
"""

import argparse
import re
import sys
import time
from datetime import date, datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from config import (
    MATCH_THRESHOLD, RESUME_PATH, SMTP_PASSWORD,
    DAILY_TARGET, LOCATION, CANDIDATE,
)
from matcher import score_job
from dedupe import is_duplicate, mark_applied
from logger import write_application
from emailer_enhanced import send, print_summary as print_email_report

# ── Constants ────────────────────────────────────────────────────────────────
JOBS_FILE  = Path(__file__).parent / "jobs.txt"
SENT_FILE  = Path(__file__).parent / "sent_companies.txt"

# ── Safe output ─────────────────────────────────────────────────────────────
def _safe_print(text: str) -> None:
    try:
        print(text)
    except UnicodeEncodeError:
        print(text.encode("utf-8", errors="replace").decode("utf-8"))

def log(msg: str, level: str = "INFO") -> None:
    ts = datetime.now().strftime("%H:%M:%S")
    prefix = {"INFO": "[INFO]", "WARN": "[WARN]", "ERROR": "[ERROR]"}
    _safe_print(f"{prefix.get(level, '[MSG]')} [{ts}] {msg}")

# ── Normalized company name matching ─────────────────────────────────────────
def normalize(name: str) -> str:
    """Normalize: lowercase, remove spaces/punctuation for matching."""
    name = name.lower().strip()
    name = re.sub(r'[\s\-\._,\'\"()]+', '', name)
    return name

def load_sent() -> tuple[set, dict]:
    """Load sent companies. Returns (normalized_set, original_dict)."""
    if not SENT_FILE.exists():
        return set(), {}
    normalized = set()
    original = {}
    with open(SENT_FILE, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            parts = line.split('|')
            if len(parts) >= 2:
                norm = parts[0].strip()
                orig = parts[1].strip()
                normalized.add(norm)
                original[norm] = orig
    return normalized, original

def is_already_sent(company: str) -> bool:
    """Check if company was already sent (normalized match)."""
    return normalize(company) in load_sent()[0]

def mark_sent(company: str) -> None:
    """Append company to sent_companies.txt after successful send."""
    norm = normalize(company)
    today = date.today().isoformat()
    with open(SENT_FILE, 'a', encoding='utf-8') as f:
        f.write(f"{norm}|{company}|{today}\n")

def log_sent_report(sent: list, skipped: list, failed: list) -> None:
    """Print clean report of what happened."""
    _safe_print("")
    _safe_print("=" * 65)
    _safe_print("APPLICATION REPORT")
    _safe_print("=" * 65)

    if sent:
        _safe_print(f"\n  SENT ({len(sent)}):")
        for c in sent:
            _safe_print(f"    [SENT]   {c['company']} -> {c['email']}")

    if skipped:
        _safe_print(f"\n  SKIPPED ({len(skipped)}):")
        for c in skipped:
            _safe_print(f"    [SKIP]   {c['company']}: {c['reason']}")

    if failed:
        _safe_print(f"\n  FAILED ({len(failed)}):")
        for c in failed:
            _safe_print(f"    [FAIL]   {c['company']}: {c['reason']}")

    _safe_print("=" * 65)
    total_sent = len(load_sent()[0])
    _safe_print(f"  Total unique companies applied (all-time): {total_sent}")
    _safe_print("=" * 65)

# ── Load jobs from jobs.txt ─────────────────────────────────────────────────
def load_jobs() -> list[dict]:
    sent_norm, _ = load_sent()
    jobs = []
    if not JOBS_FILE.exists():
        return jobs
    with open(JOBS_FILE, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            parts = line.split("|")
            if len(parts) < 2:
                continue
            title   = parts[0].strip()
            company = parts[1].strip()
            email   = parts[2].strip() if len(parts) >= 3 else ""

            # Skip if already sent (normalized match)
            if normalize(company) in sent_norm:
                log(f"  [SKIP] Already applied: {company}", "WARN")
                continue

            jobs.append({
                "job_title":  title,
                "company":    company,
                "email":      email,
                "description": title,
                "link":       "N/A",
            })
    return jobs

# ── Scoring & Filter ────────────────────────────────────────────────────────
def score_and_filter(jobs: list[dict]) -> list[dict]:
    scored = []
    for job in jobs:
        desc = job.get("description", "") + " " + job.get("job_title", "")
        result = score_job(desc, job.get("job_title", ""))
        job.update(result)
        scored.append(job)
    filtered = []
    for job in scored:
        if not job["passes"]:
            continue
        if is_duplicate(job["company"], job["job_title"]):
            log(f"  [SKIP] duplicate: {job['company']}", "WARN")
            continue
        filtered.append(job)
    return filtered

# ── Apply to jobs ────────────────────────────────────────────────────────────
def apply_to_jobs(jobs: list[dict], dry: bool = False) -> dict:
    results = {"sent": [], "failed": [], "skipped": [], "email_results": []}
    sent_norm, _ = load_sent()

    if not jobs:
        log("No jobs to apply to.")
        return results

    if dry:
        # Dry run: validate emails only
        to_apply = jobs
        log(f"Dry run: validating up to {DAILY_TARGET} job emails out of {len(to_apply)} candidates...")
        for job in to_apply:
            if len(results["sent"]) >= DAILY_TARGET:
                log(f"Reached dry-run target of {DAILY_TARGET} successful validations. Stopping.")
                break
            to_email = job.get("email", "").strip()
            from emailer_enhanced import validate_email
            valid, reason = validate_email(to_email)
            if not valid:
                results["skipped"].append({"company": job["company"], "reason": reason, "email": to_email})
                log(f"  [SKIP] {job['company']}: {reason}")
            else:
                log(f"  [OK]   {job['company']} -> {to_email}")
                results["sent"].append({"company": job["company"], "email": to_email})
        return results

    if not SMTP_PASSWORD:
        log("Email skipped: GMAIL_APP_PASSWORD not set", "WARN")
        results["skipped"] = [{"company": j["company"], "reason": "no password"} for j in jobs]
        return results

    to_apply = jobs
    log(f"Applying to maximum {DAILY_TARGET} jobs from pool of {len(to_apply)} candidates...")

    for job in to_apply:
        if len(results["sent"]) >= DAILY_TARGET:
            log(f"Reached daily target of {DAILY_TARGET} successful applications. Stopping.")
            break

        to_email = job.get("email", "").strip()

        # Double-check not already sent (race condition protection)
        if normalize(job["company"]) in sent_norm:
            log(f"  [SKIP] Already sent: {job['company']}")
            results["skipped"].append({"company": job["company"], "reason": "already sent", "email": to_email})
            continue

        # Send with retry + bounce detection
        email_result = send(to_email, company_name=job["company"], job_title=job["job_title"])
        results["email_results"].append(email_result)

        if email_result["status"] == "sent":
            mark_sent(job["company"])
            sent_norm.add(normalize(job["company"]))
            write_application({
                "company":          job["company"],
                "job_title":        job["job_title"],
                "date_applied":     date.today().isoformat(),
                "application_link": job.get("link", "N/A"),
                "email_status":     "sent",
                "match_score":      f"{job['match_pct']}%",
                "matched_skills":   job["matched_skills"],
            })
            log(f"  [SENT] {job['company']} - {job['job_title']}")
            results["sent"].append({"company": job["company"], "email": to_email})

        elif email_result["status"] == "skipped":
            log(f"  [SKIP] {job['company']}: {email_result['message']}")
            results["skipped"].append({
                "company": job["company"],
                "reason": email_result["message"],
                "email": to_email
            })

        else:
            write_application({
                "company":          job["company"],
                "job_title":        job["job_title"],
                "date_applied":     date.today().isoformat(),
                "application_link": job.get("link", "N/A"),
                "email_status":     f"failed: {email_result['message']}",
                "match_score":      f"{job['match_pct']}%",
                "matched_skills":   job["matched_skills"],
            })
            log(f"  [FAIL] {job['company']}: {email_result['message']}", "ERROR")
            results["failed"].append({
                "company": job["company"],
                "reason": email_result["message"],
                "email": to_email
            })

        time.sleep(45)

    return results

# ── Test email ──────────────────────────────────────────────────────────────
def test_email() -> None:
    log("Sending test email...")
    result = send(
        to_email="rakholiyaayush894@gmail.com",
        company_name="Test Company",
        job_title="AI Intern",
    )
    if result["status"] == "sent":
        log("Test email sent successfully!")
    else:
        log(f"Test email failed: {result['message']} [{result['code']}]", "ERROR")
        sys.exit(1)

# ── Run pipeline ────────────────────────────────────────────────────────────
def run(dry: bool = False) -> None:
    log(f"Starting job pipeline -- {'DRY RUN' if dry else 'LIVE'}")
    log(f"Target: {DAILY_TARGET} apps | Location: {LOCATION} | Threshold: {MATCH_THRESHOLD}%")

    # Step 0: Auto-load fresh batch of jobs from verified database
    log("Step 0 -- Loading fresh batch from company database...")
    try:
        from batch_loader_enhanced import load_batch
        loaded = load_batch(count=100)
        log(f"Batch loader populated jobs.txt with {loaded} companies")
    except Exception as e:
        log(f"Batch loader warning: {e} -- will use existing jobs.txt", "WARN")

    # Step 1: Load jobs
    log("Step 1 -- Loading jobs from jobs.txt...")
    all_jobs = load_jobs()
    log(f"Jobs loaded: {len(all_jobs)}")

    if not all_jobs:
        log("No new jobs in jobs.txt. All companies already applied.", "WARN")
        return

    # Step 2: Score & filter
    log("Step 2 -- Scoring and filtering...")
    filtered = score_and_filter(all_jobs)
    log(f"Jobs passing threshold: {len(filtered)}")

    if not filtered:
        log("No jobs passed. Exiting.")
        return

    # Step 3: Apply
    log("Step 3 -- Applying to jobs...")
    results = apply_to_jobs(filtered, dry=dry)

    # Email delivery report
    try:
        print_email_report()
    except Exception:
        pass

    # Final report
    log_sent_report(results["sent"], results["skipped"], results["failed"])

    if not dry and not SMTP_PASSWORD:
        _safe_print("")
        _safe_print("Set GMAIL_APP_PASSWORD to enable email sending:")
        _safe_print('  setx GMAIL_APP_PASSWORD "your-app-password"')

# ── Entry point ─────────────────────────────────────────────────────────────
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Ayush's Autonomous Job Application System")
    parser.add_argument("--run", action="store_true", help="Run full pipeline")
    parser.add_argument("--dry", action="store_true", help="Dry run (no emails)")
    parser.add_argument("--test-email", action="store_true", help="Send test email")
    args = parser.parse_args()

    try:
        if args.test_email:
            test_email()
        elif args.run:
            run(dry=False)
        elif args.dry:
            run(dry=True)
        else:
            parser.print_help()
    except Exception as e:
        _safe_print(f"[FATAL] {e}")
        import traceback; traceback.print_exc()
        sys.exit(1)
