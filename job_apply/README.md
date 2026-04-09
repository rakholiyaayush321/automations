# Autonomous AI Job Application Pipeline

This project is a fully autonomous, dynamic job sourcing and application system designed specifically for the IT, Software, AI, and ML sectors in Ahmedabad (and eventually Pune). It automatically curates a diverse batch of top companies, handles strict candidate matching, crafts tailored emails, and sends them directly to verified HR departments—without relying on rate-limited web search engines.

## Features

- **Robust Static Company Database:** Relies on a pre-verified database of over 90+ top-tier IT, AI, and Software companies to guarantee direct HR email delivery and eliminate bounces or search engine blocking.
- **Dynamic Role Rotation:** Intelligently assigns randomized, contextually appropriate job titles (e.g., `AI Intern`, `Python Developer`, `ML Trainee`, `Data Science Intern`, `Fresher`) based on the specific company's industry focus.
- **Strict Deduplication:** Ensures that an application is never sent to the same company twice by maintaining a comprehensive log of previously contacted domains.
- **Rate-Limited Executive Safety:** Respects safe email sending configurations (e.g., matching a daily limit of 20 emails per run) to maintain high email deliverability.
- **End-to-End Orchestration:** Uses `main.py` as the command center to seamlessly load a batch, filter applications based on customizable thresholds, and deliver the final emails with detailed success logging.

## Core Modules

* `main.py` — The core operator script that ties everything together. Handles dry-runs (`--dry`) and live runs (`--run`).
* `batch_loader_enhanced.py` — Intercepts the pipeline at Step 0, bypassing broken search engine endpoints by drawing 20 diverse, randomized roles from a rigorous static database. 
* `matcher_enhanced.py` — Filters matches stringently, calculating compatibility to prevent applying to poorly suited or out-of-scale companies.
* `emailer_enhanced.py` — Wraps the email generation and dispatching logic, handling SMTP connections safely.
* `config.py` — Holds environment variables, threshold markers, candidate constraints, and daily targets.

## Setup Instructions

### Prerequisites
- Python 3.10+
- Dependencies (Install via `pip install -r requirements.txt` if available)

### Authentication
To enable live email sending via Gmail, you must generate an **App Password** from your Google Account settings, completely unrelated to your primary password.
Add the password as a System Environment Variable or handle it prior to execution:

```powershell
# Windows PowerShell Example
setx GMAIL_APP_PASSWORD "your-16-digit-app-password"
```

## Usage

**1. Dry Run (Test Configuration)**
Always run a dry check to ensure the batch loader populates exactly 20 companies without dispatching live emails.

```bash
python main.py --dry
```

**2. Live Execution**
Send live applications.

```bash
python main.py --run
```

**3. Daily Scheduling**
Use the provided `run_daily.bat` script through Windows Task Scheduler to automate your lead generation funnel entirely.

## Project History / Why Static Database?
Previous iterations leaned aggressively on HTML web crawling (DuckDuckGo/Bing) to extract leads dynamically. Search engines responded by actively blocking automated queries (HTTP 202/HTTP 403 responses). The pipeline was refactored to employ a highly-validated static JSON/Python company dictionary combined with localized crawling logic on a per-domain career page basis.

## License
*Personal Use* — This is an automation tool designed specifically for individual job-hunting enhancement.
