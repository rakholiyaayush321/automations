import sys
sys.path.insert(0, r'C:\Users\rakho\.openclaw\workspace\job_apply')

# Test loading jobs
from pathlib import Path
JOBS_FILE = Path(r'C:\Users\rakho\.openclaw\workspace\job_apply\jobs.txt')

jobs = []
with open(JOBS_FILE, 'r', encoding='utf-8') as f:
    for line in f:
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        parts = line.split('|')
        if len(parts) >= 2:
            jobs.append({
                'job_title': parts[0].strip(),
                'company': parts[1].strip(),
                'email': parts[2].strip() if len(parts) >= 3 else ''
            })

print(f'Jobs loaded: {len(jobs)}')
for j in jobs:
    print(f"  {j['job_title']} | {j['company']} | {j['email']}")
