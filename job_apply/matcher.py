"""
matcher.py - Skill matching and scoring engine
"""

import re
from config import SKILLS, MAX_SKILL_SCORE, MATCH_THRESHOLD


def normalize(text: str) -> str:
    """Lowercase, strip, and normalize whitespace."""
    return re.sub(r'\s+', ' ', text.lower().strip())


def tokenize(text: str) -> set[str]:
    """Split on non-alphanumeric characters."""
    return set(re.findall(r'[a-z0-9]+', normalize(text)))


def score_job(job_description: str, job_title: str = "") -> dict:
    """
    Score a job against Ayush's skill profile.
    Returns a dict with score, percentage, and matched skills.
    """
    full_text = normalize(f"{job_title} {job_description}")

    matched_skills = {}
    raw_score = 0.0

    for skill, weight in SKILLS.items():
        # Skill can appear as phrase (multi-word) or individual tokens
        if skill in full_text:
            matched_skills[skill] = weight
            raw_score += weight

    match_pct = (raw_score / MAX_SKILL_SCORE) * 100 if MAX_SKILL_SCORE > 0 else 0

    return {
        "score":      round(raw_score, 2),
        "match_pct":  round(match_pct, 1),
        "threshold":  MATCH_THRESHOLD,
        "passes":     match_pct > MATCH_THRESHOLD,
        "matched_skills": list(matched_skills.keys()),
    }
