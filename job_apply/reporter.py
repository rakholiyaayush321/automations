"""
reporter.py - Daily job digest generator (ASCII-only, Windows safe)
"""

from datetime import datetime


def build_digest(jobs: list[dict], threshold: float) -> str:
    """
    Build a formatted digest showing matched jobs.
    Fully ASCII -- no emoji, no Unicode, no ANSI codes.
    """
    if not jobs:
        lines = [
            "[JOBS] Daily Job Digest",
            "------------------------",
            f"No new jobs found matching your profile (>{threshold}% match).",
            "Nothing to do today.",
        ]
        return "\n".join(lines)

    lines = [
        "[JOBS] Daily Job Digest -- Matched Jobs",
        "=" * 50,
        f"Date            : {datetime.now().strftime('%d %b %Y, %I:%M %p')} IST",
        f"Match threshold : {threshold}%",
        f"Jobs matched    : {len(jobs)}",
        "-" * 50,
    ]

    for i, job in enumerate(jobs, 1):
        skills = ", ".join(job.get("matched_skills", [])) or "none"
        lines.extend([
            f"[{i}] {job['job_title']}",
            f"    Company : {job['company']}",
            f"    Match  : {job['match_pct']}%",
            f"    Skills : {skills}",
            f"    Link   : {job['link']}",
        ])

    lines.append("-" * 50)
    lines.append("Auto-processing jobs.")
    lines.append("=" * 50)

    return "\n".join(lines)
