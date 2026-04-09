# Job Application Automation — SPEC.md

## Overview

Automated daily job search and application system for Ayush Rakholiya targeting AI/ML internships, trainee roles, and entry-level Python developer positions across multiple job platforms.

**Core behavior:** Scans 5 job platforms daily → scores jobs against Ayush's skills → presents top matches for confirmation → applies via email → logs everything.

---

## Architecture

```
job_apply/
├── SPEC.md                  # This file
├── config.py                # All configuration (keywords, skills, paths, email, schedule)
├── main.py                   # Entry point / scheduler
├── jobs/
│   ├── __init__.py
│   ├── linkedin.py          # LinkedIn scraper
│   ├── internshala.py       # Internshala scraper
│   ├── indeed.py            # Indeed scraper
│   ├── wellfound.py         # Wellfound (AngelList) scraper
│   └── naukri.py            # Naukri fresher jobs scraper
├── matcher.py               # Skill matching + scoring engine
├── dedupe.py                # Duplicate detection (hash-based)
├── emailer.py               # Email sender with SMTP
├── logger.py                # applications.csv writer/reader
├── reporter.py              # Daily summary generator (confirmation digest)
├── resume/
│   └── resume.pdf           # Ayush's resume (symlink/copy of workspace resume)
├── logs/
│   └── job_apply.log        # Execution log
└── applications.csv         # Application tracking (created at runtime)
```

---

## Platforms & Search Strategy

| Platform    | Method           | Search URL / API                          |
|-------------|------------------|-------------------------------------------|
| LinkedIn    | Requests + BS4  | `https://www.linkedin.com/jobs/search/?keywords=...&f_TPR=r86400` |
| Internshala | Requests + BS4  | `https://internshala.com/internships/` |
| Indeed      | Requests + BS4  | `https://www.indeed.com/jobs?q=...&fromage=1` |
| Wellfound   | Requests + BS4  | `https://wellfound.com/jobs/search?query=...&filter=last_24_h=true` |
| Naukri      | Requests + BS4  | `https://www.naukri.com/fresher-jobs-in-ai-ml` |

---

## Job Keywords (OR-matched)

```
AI Intern, ML Intern, Python Intern, Data Science Intern,
AI Trainee, ML Trainee, Junior Python Developer,
Entry Level AI Engineer, LLM Intern, FastAPI Intern
```

Search query format: `"<keyword>" OR "<keyword>"` combined into a single search.

---

## Skill Matching

### Ayush's Skills (from resume)

```python
SKILLS = [
    "python", "machine learning", "pytorch", "scikit-learn",
    "fastapi", "langchain", "llm", "nlp", "numpy", "pandas",
    "neural networks", "deep learning", "feature engineering",
    "classification", "regression", "text classification",
    "rest api", "git", "jupyter"
]
```

### Scoring Algorithm

For each job description:
1. Tokenize and normalize job description (lowercase, remove punctuation)
2. Count occurrences of each skill keyword
3. Weighted score = sum of (count × weight) per skill
4. Max possible = sum of all weights
5. Match % = (weighted_score / max_possible) × 100

Skill weights:
- Core skills (python, machine learning, pytorch, scikit-learn, fastapi): weight 2
- Ecosystem (nlp, llm, langchain, numpy, pandas, neural networks, deep learning): weight 1.5
- Methods (feature engineering, classification, regression, text classification): weight 1
- Tools (git, jupyter, rest api): weight 0.5

**Apply threshold: > 70% match score**

---

## Filters

- **Age filter:** Only jobs posted in the last 24 hours (checked via `fromage=1` param + date parsing)
- **Deduplication:** SHA256 hash of (company_name + job_title). Stored in `dedupe_store.json`
- **Already applied check:** Cross-reference against `applications.csv`

---

## Confirmation Workflow

Before any email is sent, the system generates a **Daily Application Digest**:

1. Run all job fetchers → collect all jobs
2. Apply age filter (last 24h)
3. Apply deduplication filter
4. Score each job against skills
5. Filter jobs with match > 70%
6. Generate digest report (see reporter.py output)
7. **Await confirmation** before sending emails
8. On confirmation → send emails → log to CSV
9. On rejection → skip sending, log as "skipped"

---

## Email Sending

**SMTP Config (configurable):**
- Provider: Gmail SMTP (or configurable)
- From: `rakholiyaayush894@gmail.com`
- To: Extracted from job listing or application portal

**Email Template:**
- Subject: `Application for AI/ML Internship or Trainee Role`
- Body: (as specified by Ayush)
- Attachment: `resume/resume.pdf`

**On success:** Write row to `applications.csv` with status "sent"
**On failure:** Write row with status "failed" + error message

---

## Logging (applications.csv)

```csv
company,job_title,date_applied,application_link,email_status,match_score,skills_matched
Awakeen Studio,AI/ML Intern,2026-04-03,https://...,sent,85%,python,ml,fastapi
```

File location: `{workspace}/job_apply/applications.csv`

---

## Scheduling

- **Trigger:** Daily at 9:00 AM IST
- **Implementation:** Cron job (via OpenClaw cron) that runs `python main.py --run` in isolated session
- **Manual trigger:** `python main.py --run` for on-demand execution

---

## Dependencies

```txt
requests
beautifulsoup4
lxml
python-dateutil
pandas
httpx
```

---

## Acceptance Criteria

- [ ] Scans all 5 platforms and collects jobs
- [ ] Filters to last 24 hours only
- [ ] Scores jobs against skill profile
- [ ] Deduplication prevents same company+role being applied twice
- [ ] Generates confirmation digest before sending any email
- [ ] Sends email with resume attached on confirmation
- [ ] Logs all applications to applications.csv
- [ ] Runs daily at 9 AM automatically
- [ ] Handles platform errors gracefully (one platform down ≠ abort all)
