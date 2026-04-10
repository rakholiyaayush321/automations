# Autonomous AI Job Application System

An intelligent, fully autonomous Python pipeline that aggressively targets Python, AI, and ML roles geographically fenced to **Ahmedabad** and **Pune**.

## Core Features

- **Hyper-Targeted Sourcing:** Employs advanced web scraping and dynamic querying (`dynamic_sourcing.py`, `search_ahm_pune.py`) to bypass traditional job boards and pull fresh, unlisted jobs directly from company career pages.
- **Smart Scoring & Filtering:** (`matcher_enhanced.py`) Parses job descriptions and matches them automatically against your stored resume/skills threshold (e.g. >70% match requirement).
- **Automated Verification:** (`email_verifier.py`) Dynamically performs strict live DNS & MX record lookups to drastically reduce email bounce rates and ensure deliverability before attempting application.
- **Auto-Applying Engine:** Generates hyper-personalized cold-outreach application emails leveraging GenAI LLMs, automatically dispatching them via SMTP.
- **Anti-Spam & Deduplication:** Bulletproof state management (`dedupe.py`, `applications.csv`, `jobs.txt`) ensures that a specific role at a company is never applied to multiple times, preventing blacklist triggers. Incorporates a smart 30-day "re-application" cooldown logic.

## Usage

Create a virtual environment, install requirements, and set your environment variables (like your `GMAIL_APP_PASSWORD` for SMTP).

```bash
python main.py --run
```

To run dynamically restricted sourcing exclusively for Ahmedabad/Pune companies:
```bash
python search_ahm_pune.py
```

## Architecture

- `main.py`: The central orchestrator that manages rounds, daily limits, and step execution.
- `config.py`: Hardcoded restraints (e.g. `LOCATION_FILTERS = ["ahmedabad", "pune"]`, `DAILY_TARGET = 20`).
- `batch_loader_enhanced.py`: In-memory static database of strictly verified tech companies.
- `emailer_enhanced.py`: Reliable SMTP delivery with automatic error suppression and retry functionality.

## Limits

Executes cleanly and quietly. Caps at **20 automated applications per day** to abide by standard email provider guidelines. 

---
*Built with Antigravity.*
