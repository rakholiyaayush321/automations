"""
config_enhanced.py - Enhanced configuration for job application automation
===========================================================
All configuration for the job application automation with new features:
- Priority companies
- Multiple email templates
- Alternative email patterns
- Validation settings
- Company classification

"""

import os
from pathlib import Path

# ── Workspace / Paths ────────────────────────────────────────────────────────
WORKSPACE   = Path(__file__).parent.parent
PROJECT_DIR = Path(__file__).parent
RESUME_PATH = PROJECT_DIR / "resume" / "resume.pdf"
LOG_FILE    = PROJECT_DIR / "logs" / "job_apply.log"
CSV_FILE    = PROJECT_DIR / "applications.csv"
DEDUPE_FILE = PROJECT_DIR / "dedupe_store.json"
JOBS_FILE   = PROJECT_DIR / "jobs.txt"
DAILY_TARGET_MAX = 20
DAILY_TARGET = DAILY_TARGET_MAX
FAILED_EMAILS_FILE = PROJECT_DIR / "failed_emails.json"
PRIORITY_LOG = PROJECT_DIR / "priority_applications.log"

# ── Candidate Profile ────────────────────────────────────────────────────────
CANDIDATE = {
    "name": "Ayush Rakholiya",
    "email": "rakholiyaayush894@gmail.com",
    "phone": "+91 9825420436",
    "degree": "B.Tech Computer Engineering",
    "cgpa": "7.69",
    "experience": "6 months AI/ML Intern at Awakeen Studio Pvt. Ltd.",
    "skills": [
        "Python", "NumPy", "Pandas", "Scikit-learn", "PyTorch",
        "FastAPI", "LangChain", "Machine Learning", "Deep Learning",
        "NLP", "REST API", "Git", "AI Automation", "LLMs"
    ],
    "projects": [
        "NeuroCry-AI (infant cry classification using deep learning)",
        "AI Game Analyzer (LLM-based code intelligence)",
        "AI Mental Health Chatbot"
    ]
}

# ── Target Roles ─────────────────────────────────────────────────────────────
TARGET_ROLES = [
    "Python Intern",
    "Python Trainee",
    "Python Developer",
    "AI Intern",
    "AI Trainee",
    "ML Intern",
    "ML Trainee",
    "Data Science Intern",
    "Software Developer",
    "Junior Developer",
    "Fresher",
    "Trainee",
    "Automation Engineer",
]

# ── Location Filter ──────────────────────────────────────────────────────────
LOCATION = "Ahmedabad"
LOCATION_FILTERS = [
    "ahmedabad",
    "pune",
]

# ── Priority Companies (Higher chance of being selected) ─────────────────────
PRIORITY_COMPANIES = [
    "fxis.ai",
    "Inferenz",
    "Neuramonks",
    "SoluLab",
    "OpenXcell",
    "TatvaSoft",
    "Bacancy",
    "Radixweb",
    "Sparx IT Solutions",
    "kenex ai",
    "",
    "Crest Data Systems",
    "MindInventory",
    "Simform",
]

# ── Company Classification ───────────────────────────────────────────────────
COMPANY_SIZES = {
    "STARTUP": (1, 50),
    "SMALL": (51, 200),
    "MID": (201, 700),
    "LARGE": (701, float('inf')),
}

PREFERRED_SIZES = ["STARTUP", "SMALL", "MID"]  # Avoid LARGE

# ── Alternative Email Patterns ───────────────────────────────────────────────
# When primary email fails, try these patterns
EMAIL_PATTERNS = [
    "careers@{domain}",
    "career@{domain}",
    "hr@{domain}",
    "jobs@{domain}",
    "info@{domain}",
    "contact@{domain}",
    "hello@{domain}",
    "recruitment@{domain}",
    "hiring@{domain}",
]

# ── Email Templates ───────────────────────────────────────────────────────────
EMAIL_TEMPLATES = {
    "ai_ml": {
        "subject": "Application for AI/ML Intern Position - {name}",
        "body": """{greeting},

I am writing to express my interest in the AI/ML position at {company}. With hands-on experience in Python, PyTorch, and LangChain, I believe I would be a strong addition to your team.

About Me:
- B.Tech in Computer Engineering (CGPA: {cgpa})
- {experience}
- Skills: {skills}
- Notable Project: {project}

I have practical exposure to ML pipelines, model deployment with FastAPI, and real-world AI applications. My project {project} demonstrates my ability to build production-ready AI solutions.

I am excited about the opportunity to contribute to {company} and grow with your team.

Please find my resume attached. I look forward to hearing from you.

Best regards,
{name}
{phone}
{email}"""
    },
    
    "python_dev": {
        "subject": "Application for Python Developer Role - {name}",
        "body": """{greeting},

I am writing to apply for the Python Developer position at {company}. My background in Python development, FastAPI, and AI integration makes me a strong fit for your team.

About Me:
- B.Tech in Computer Engineering (CGPA: {cgpa})
- {experience}
- Skills: {skills}
- Key Project: {project}

I have built scalable applications using FastAPI and integrated AI capabilities into production systems. My experience includes REST API development, data processing with Pandas/NumPy, and machine learning model deployment.

I am eager to bring my skills to {company} and contribute to your development team.

Please find my resume attached. I look forward to discussing this opportunity.

Best regards,
{name}
{phone}
{email}"""
    },
    
    "fresher": {
        "subject": "Application for Fresher Position - {name}",
        "body": """{greeting},

I am a recent Computer Engineering graduate seeking to start my career at {company}. With strong Python skills and AI/ML project experience, I am eager to contribute and learn.

About Me:
- B.Tech in Computer Engineering (CGPA: {cgpa})
- Internship: {experience}
- Skills: {skills}
- Academic Project: {project}

Through my internship and projects, I have gained hands-on experience in Python development, machine learning, and AI automation. I am a quick learner and passionate about building innovative solutions.

I would welcome the opportunity to grow with {company} and contribute to your success.

Please find my resume attached. I look forward to your response.

Best regards,
{name}
{phone}
{email}"""
    },
    
    "automation": {
        "subject": "Application for Automation/AI Role - {name}",
        "body": """{greeting},

I am writing to express my interest in the automation position at {company}. With expertise in Python, AI tools, and process automation, I can add immediate value to your team.

About Me:
- B.Tech in Computer Engineering (CGPA: {cgpa})
- {experience}
- Skills: {skills}
- Automation Project: {project}

I specialize in building AI-powered automation solutions using Python, LangChain, and LLMs. My experience includes developing intelligent chatbots, automated analysis systems, and ML pipelines.

I am excited about the opportunity to bring my automation expertise to {company}.

Please find my resume attached. I look forward to hearing from you.

Best regards,
{name}
{phone}
{email}"""
    }
}

# ── Daily Limits ─────────────────────────────────────────────────────────────
DAILY_TARGET_MIN = 15
DAILY_TARGET_MAX = 25
MAX_APPLICATIONS_PER_RUN = 25

# ── Timing Configuration ──────────────────────────────────────────────────────
EMAIL_DELAY_SECONDS = 45  # Delay between emails to avoid spam detection
RETRY_DELAY_SECONDS = 60  # Delay before retry on temporary failure
MAX_RETRIES = 1  # Only retry once for temporary failures

# ── Job Search Keywords ──────────────────────────────────────────────────────
JOB_KEYWORDS = [
    "AI Intern",
    "ML Intern",
    "Python Intern",
    "Data Science Intern",
    "AI Trainee",
    "ML Trainee",
    "Junior Python Developer",
    "Entry Level AI Engineer",
    "LLM Intern",
    "FastAPI Intern",
    "Automation Engineer",
    "Software Developer Fresher",
]

# ── Skill Profile for Matching ───────────────────────────────────────────────
SKILLS = {
    # Core skills (weight 2)
    "python":                2,
    "machine learning":      2,
    "ml":                    2,
    "artificial intelligence": 2,
    "ai":                    2,
    "pytorch":               2,
    "scikit-learn":          2,
    "fastapi":               2,
    # Ecosystem skills (weight 1.5)
    "nlp":                   1.5,
    "llm":                   1.5,
    "langchain":             1.5,
    "numpy":                 1.5,
    "pandas":                1.5,
    "neural networks":       1.5,
    "deep learning":         1.5,
    # Methods (weight 1)
    "feature engineering":   1,
    "classification":        1,
    "regression":            1,
    "text classification":   1,
    "data science":          1,
    "backend":               1,
    "developer":             0.5,
    "software":              0.5,
    # Tools (weight 0.5)
    "git":                   0.5,
    "jupyter":               0.5,
    "rest api":              0.5,
    "api":                   0.5,
    "intern":                0.5,
    "trainee":               0.5,
    "fresher":               0.5,
    "data":                  0.5,
    "automation":            1.5,
    "llms":                  1.5,
}
MAX_SKILL_SCORE = sum(SKILLS.values())

# Match thresholds
MATCH_THRESHOLD = 5          # Minimum for file-based (title-only)
QUALITY_THRESHOLD = 60       # Minimum match % for quality control (reduced from 70)
PRIORITY_BONUS = 10          # Extra percentage for priority companies

# ── Email Config ─────────────────────────────────────────────────────────────
EMAIL_FROM     = "rakholiyaayush894@gmail.com"
SMTP_HOST      = "smtp.gmail.com"
SMTP_PORT      = 587
SMTP_USER      = "rakholiyaayush894@gmail.com"
SMTP_PASSWORD  = os.getenv("GMAIL_APP_PASSWORD", "")

# ── Scheduler ─────────────────────────────────────────────────────────────────
DAILY_RUN_HOUR    = 10   # 10 AM IST
DAILY_RUN_MINUTE  = 0

# ── Notifications ─────────────────────────────────────────────────────────────
ENABLE_WHATSAPP_NOTIFICATIONS = False  # Disabled - use email only


def get_email_template(job_title: str, match_score: int) -> str:
    """Select appropriate email template based on job role and match score."""
    job_lower = job_title.lower()
    
    # Check for AI/ML roles
    if any(keyword in job_lower for keyword in ["ai", "ml", "machine learning", "deep learning", "neural"]):
        return "ai_ml"
    
    # Check for automation roles
    if any(keyword in job_lower for keyword in ["automation", "langchain", "llm"]):
        return "automation"
    
    # Check for fresher/trainee roles
    if any(keyword in job_lower for keyword in ["fresher", "trainee", "entry", "junior", "0-"]):
        return "fresher"
    
    # Default to python dev
    return "python_dev"


def build_email_subject(job_title: str, company_name: str) -> str:
    """Generate email subject line."""
    return f"Application for {job_title} - {CANDIDATE['name']}"


def build_email_body(job_title: str, company_name: str, greeting: str = "Dear Hiring Manager") -> str:
    """Generate personalized email body using templates."""
    template_key = get_email_template(job_title, 70)
    template = EMAIL_TEMPLATES[template_key]
    
    # Select relevant project
    job_lower = job_title.lower()
    if "ml" in job_lower or "machine" in job_lower:
        project = CANDIDATE["projects"][0]  # NeuroCry-AI
    elif "nlp" in job_lower or "llm" in job_lower or "chatbot" in job_lower:
        project = CANDIDATE["projects"][1]  # AI Game Analyzer
    elif "automation" in job_lower:
        project = CANDIDATE["projects"][2]  # Mental Health Chatbot
    else:
        project = CANDIDATE["projects"][0]  # Default
    
    # Format skills
    skills_str = ", ".join(CANDIDATE["skills"][:8])  # Top 8 skills
    
    # Fill template
    body = template["body"].format(
        company=company_name,
        name=CANDIDATE["name"],
        email=CANDIDATE["email"],
        phone=CANDIDATE["phone"],
        cgpa=CANDIDATE["cgpa"],
        experience=CANDIDATE["experience"],
        skills=skills_str,
        project=project,
        greeting=greeting
    )
    
    subject = template["subject"].format(
        company=company_name,
        name=CANDIDATE["name"]
    )
    
    return subject, body
