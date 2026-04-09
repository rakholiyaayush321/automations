import json
from pathlib import Path
from datetime import date

PROJECT_DIR = Path(__file__).parent
JSON_FILE = PROJECT_DIR / "verified_companies.json"
JOBS_FILE = PROJECT_DIR / "jobs.txt"

def load_verified_json():
    """Load verified companies from JSON and append to jobs.txt avoiding duplicates"""
    if not JSON_FILE.exists():
        print(f"Error: {JSON_FILE.name} not found.")
        return

    with open(JSON_FILE, "r", encoding="utf-8") as f:
        companies = json.load(f)

    # Read existing jobs to avoid append duplication
    existing = set()
    if JOBS_FILE.exists():
        with open(JOBS_FILE, "r", encoding="utf-8") as f:
            for line in f:
                if not line.strip() or line.startswith("#"):
                    continue
                parts = line.split("|")
                if len(parts) >= 2:
                    existing.add(parts[1].strip().lower())

    added_count = 0
    with open(JOBS_FILE, "a", encoding="utf-8") as f:
        # Check if we need to add a header if file is empty or new
        if not JOBS_FILE.exists() or JOBS_FILE.stat().st_size == 0:
            f.write("# Format: Job Title | Company | Email\n\n")
            
        for comp in companies:
            name = comp.get("company", "").strip()
            if name.lower() in existing:
                print(f"Skipping {name} (already in jobs.txt)")
                continue
                
            email = comp.get("email", "").strip()
            # If email is 'Apply via careers page', we skip or generate a generic one (the system later handles fallback)
            if "Apply via careers page" in email or not email:
                domain = comp.get("website", "").replace("https://", "").replace("http://", "").replace("www.", "").strip("/")
                email = f"careers@{domain}" if domain else ""
                
            # Pick the first role
            roles = comp.get("roles", "Python Developer").split(",")
            title = roles[0].strip()
            
            f.write(f"{title} | {name} | {email}\n")
            existing.add(name.lower())
            added_count += 1
            print(f"Added: {name} -> {email} ({title})")
            
    print(f"\nSuccessfully integrated and loaded {added_count} verified companies into jobs.txt.")
    print("You can now run 'python main.py --run' to apply to them automatically.")

if __name__ == "__main__":
    load_verified_json()
