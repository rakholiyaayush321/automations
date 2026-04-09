import sys
sys.path.insert(0, r'C:\Users\rakho\.openclaw\workspace\job_apply')
from matcher import score_job
from config import SKILLS, MAX_SKILL_SCORE

jobs = [
    'AI ML Intern | Freshworks',
    'AI Engineer | CRED',
    'Data Science Intern | CoinDCX',
    'Backend Developer Intern | Postman',
    'ML Engineer Intern | Scale AI',
    'AI Software Intern | TCS',
]

print('MAX_SKILL_SCORE:', MAX_SKILL_SCORE)
print()
for j in jobs:
    title = j.split('|')[0].strip()
    r = score_job(title, title)
    print(f'{title}')
    print(f'  score={r["score"]}  pct={r["match_pct"]}%  passes={r["passes"]}')
    print(f'  matched: {r["matched_skills"]}')
    print()