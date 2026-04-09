"""
matcher_enhanced.py - Enhanced skill matching with company classification
=======================================================================
"""

import re
from typing import Dict, List, Tuple

from config import (
    SKILLS, MAX_SKILL_SCORE, QUALITY_THRESHOLD,
    PRIORITY_COMPANIES, PRIORITY_BONUS,
    COMPANY_SIZES, PREFERRED_SIZES
)


def parse_company_size(size_str: str) -> Tuple[int, int]:
    """Parse company size string to min-max range."""
    if not size_str:
        return (0, 0)
    
    # Handle formats like "50-200", "200+", "10-50"
    size_str = size_str.strip()
    
    if '+' in size_str:
        # e.g., "200+"
        min_size = int(size_str.replace('+', '').strip())
        return (min_size, min_size + 1000)
    
    if '-' in size_str:
        parts = size_str.split('-')
        return (int(parts[0].strip()), int(parts[1].strip()))
    
    # Single number
    try:
        size = int(size_str)
        return (size, size)
    except:
        return (0, 0)


def classify_company_size(size_str: str) -> str:
    """Classify company into size category."""
    min_size, max_size = parse_company_size(size_str)
    
    for category, (cat_min, cat_max) in COMPANY_SIZES.items():
        if min_size >= cat_min and min_size <= cat_max:
            return category
    
    return "UNKNOWN"


def is_preferred_size(size_category: str) -> bool:
    """Check if company size is in preferred categories."""
    return size_category in PREFERRED_SIZES


def is_priority_company(company_name: str) -> bool:
    """Check if company is in priority list."""
    company_lower = company_name.lower()
    for priority in PRIORITY_COMPANIES:
        if priority.lower() in company_lower or company_lower in priority.lower():
            return True
    return False


def score_job(description: str, job_title: str, company_name: str = "", company_size: str = "") -> Dict:
    """
    Enhanced job scoring with priority and size classification.
    
    Returns:
        {
            'score': float,
            'match_pct': float,
            'passes': bool,
            'matched_skills': List[str],
            'is_priority': bool,
            'size_category': str,
            'is_preferred_size': bool,
            'final_score': float  # With bonuses
        }
    """
    # Combine description and title for matching
    text = (description + " " + job_title).lower()
    
    # Tokenize (split by non-alphanumeric)
    tokens = set(re.findall(r'[a-zA-Z0-9\-\+]+', text))
    
    # Calculate weighted score
    weighted_score = 0
    matched_skills = []
    
    for skill, weight in SKILLS.items():
        skill_lower = skill.lower()
        # Check for exact match or partial match
        if skill_lower in text:
            weighted_score += weight
            matched_skills.append(skill)
        else:
            # Check token matching
            skill_tokens = set(skill_lower.split())
            if skill_tokens & tokens:
                weighted_score += weight * 0.5  # Partial match
                matched_skills.append(skill + "(partial)")
    
    # Calculate percentage
    match_pct = (weighted_score / MAX_SKILL_SCORE) * 100
    
    # Check priority
    is_priority = is_priority_company(company_name)
    
    # Classify size
    size_category = classify_company_size(company_size)
    is_preferred = is_preferred_size(size_category)
    
    # Calculate final score with bonuses
    final_score = match_pct
    if is_priority:
        final_score += PRIORITY_BONUS
    if not is_preferred:
        final_score -= 10  # Penalty for large companies
    
    # Clamp to 0-100
    final_score = max(0, min(100, final_score))
    
    return {
        'score': weighted_score,
        'match_pct': round(match_pct, 1),
        'passes': final_score >= QUALITY_THRESHOLD,
        'matched_skills': matched_skills,
        'is_priority': is_priority,
        'size_category': size_category,
        'is_preferred_size': is_preferred,
        'final_score': round(final_score, 1)
    }


def score_company_only(company_name: str, company_size: str = "") -> Dict:
    """Quick scoring when only company info is available."""
    is_priority = is_priority_company(company_name)
    size_category = classify_company_size(company_size)
    is_preferred = is_preferred_size(size_category)
    
    # Base score for company
    score = 50  # Neutral base
    
    if is_priority:
        score += PRIORITY_BONUS
    if not is_preferred:
        score -= 10
    
    return {
        'passes': score >= QUALITY_THRESHOLD,
        'is_priority': is_priority,
        'size_category': size_category,
        'is_preferred_size': is_preferred,
        'score': score
    }


# ── Legacy Support ────────────────────────────────────────────────────────────
def score_job_legacy(description: str, job_title: str) -> Dict:
    """Legacy scoring function for backward compatibility."""
    return score_job(description, job_title)


if __name__ == "__main__":
    # Test
    result = score_job(
        "Looking for Python developer with FastAPI and AI experience",
        "Python AI Developer",
        "TatvaSoft",
        "200-500"
    )
    print("Test result:", result)
