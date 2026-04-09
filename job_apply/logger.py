"""
logger.py - applications.csv writer and reader
"""

import csv
import os
from datetime import date
from pathlib import Path
from config import CSV_FILE

FIELDNAMES = [
    "company",
    "job_title",
    "date_applied",
    "application_link",
    "email_status",
    "match_score",
    "skills_matched",
]


def csv_exists() -> bool:
    return CSV_FILE.exists()


def read_applications() -> list[dict]:
    if not csv_exists():
        return []
    with open(CSV_FILE, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def write_application(row: dict) -> None:
    CSV_FILE.parent.mkdir(parents=True, exist_ok=True)
    file_exists = csv_exists()
    try:
        with open(CSV_FILE, newline="", encoding="utf-8", mode="a") as f:
            writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
            if not file_exists:
                writer.writeheader()
            writer.writerow({
                "company":           row.get("company", ""),
                "job_title":         row.get("job_title", ""),
                "date_applied":      row.get("date_applied", date.today().isoformat()),
                "application_link":   row.get("application_link", ""),
                "email_status":      row.get("email_status", "unknown"),
                "match_score":       row.get("match_score", ""),
                "skills_matched":    ", ".join(row.get("matched_skills", [])),
            })
    except PermissionError:
        # CSV is open in Excel or another program - log to backup file instead
        backup = CSV_FILE.with_suffix(".log")
        with open(backup, "a", encoding="utf-8") as f:
            f.write(f"{date.today().isoformat()} | {row.get('company','')} | {row.get('job_title','')} | {row.get('email_status','')}\n")


def already_applied_link(link: str) -> bool:
    """Return True if this exact link has already been applied to."""
    for app in read_applications():
        if app.get("application_link", "").strip() == link.strip():
            return True
    return False
