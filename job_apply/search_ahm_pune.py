"""
search_ahm_pune.py - Search ONLY Ahmedabad and Pune for fresh companies
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from dynamic_sourcing import run_dynamic_pipeline
from batch_loader_enhanced import load_sent, normalize

sent = load_sent()
all_jobs = []

# === AHMEDABAD SEARCHES ===
queries_ahm = [
    ("AI Intern", "Ahmedabad"),
    ("Python Developer", "Ahmedabad"),
    ("ML Engineer", "Ahmedabad"),
    ("Backend Developer", "Ahmedabad"),
    ("Software Developer Python", "Ahmedabad"),
    ("Data Science", "Ahmedabad"),
    ("AI ML startup", "Ahmedabad"),
    ("Django Developer", "Ahmedabad"),
    ("FastAPI Developer", "Ahmedabad"),
    ("NLP Engineer", "Ahmedabad"),
]

# === PUNE SEARCHES ===
queries_pune = [
    ("AI Intern", "Pune"),
    ("Python Developer", "Pune"),
    ("ML Engineer", "Pune"),
    ("Backend Developer Python", "Pune"),
    ("Data Science Intern", "Pune"),
    ("Software Developer", "Pune"),
    ("AI ML company", "Pune hiring"),
    ("Deep Learning", "Pune"),
    ("Django Developer", "Pune"),
    ("Automation Engineer", "Pune"),
]

seen_norms = set()

print("=" * 60)
print("SEARCHING AHMEDABAD FOR NEW COMPANIES...")
print("=" * 60)
for title, loc in queries_ahm:
    if len(all_jobs) >= 15:
        break
    results = run_dynamic_pipeline(title, loc, count=5)
    for r in results:
        norm = normalize(r["company"])
        if norm not in sent and norm not in seen_norms:
            r["location"] = "Ahmedabad"
            all_jobs.append(r)
            seen_norms.add(norm)

ahm_count = sum(1 for j in all_jobs if j.get("location") == "Ahmedabad")
print(f"\nAhmedabad companies found: {ahm_count}")

print("\n" + "=" * 60)
print("SEARCHING PUNE FOR NEW COMPANIES...")
print("=" * 60)
for title, loc in queries_pune:
    if len(all_jobs) >= 30:
        break
    results = run_dynamic_pipeline(title, loc, count=5)
    for r in results:
        norm = normalize(r["company"])
        if norm not in sent and norm not in seen_norms:
            r["location"] = "Pune"
            all_jobs.append(r)
            seen_norms.add(norm)

pune_count = sum(1 for j in all_jobs if j.get("location") == "Pune")
print(f"\nPune companies found: {pune_count}")
print(f"TOTAL new companies: {len(all_jobs)}")

# Write to jobs.txt
if all_jobs:
    jobs_file = Path(__file__).parent / "jobs.txt"
    with open(jobs_file, "w", encoding="utf-8") as f:
        f.write("# Fresh Ahmedabad + Pune companies - Web Search\n\n")
        for j in all_jobs:
            line = f"{j['job_title']} | {j['company']} | {j['email']}\n"
            f.write(line)
    
    print("\nWritten to jobs.txt!")
    print("\nCompanies found:")
    for i, j in enumerate(all_jobs, 1):
        print(f"  {i}. {j['company']} ({j.get('location','?')}) -> {j['email']}")
else:
    print("No new companies found!")
