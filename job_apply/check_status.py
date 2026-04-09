import sys
sys.path.insert(0, r'C:\Users\rakho\.openclaw\automations\job_apply')
from batch_loader import AHMEDABAD_COMPANIES, normalize, load_sent
import json

sent = load_sent()
sent_normalized = {n for n in sent if n}

# Companies with verified emails that are unapplied
verified = [(n, w, e) for n, w, s, e in AHMEDABAD_COMPANIES if e and normalize(n) not in sent_normalized]
print(f'Verified & unapplied: {len(verified)}')
for n, w, e in verified:
    print(f'  {n} -> {e}')

# Also check applied_companies.json
applied_json = json.load(open(r'C:\Users\rakho\.openclaw\automations\job_apply\applied_companies.json'))
print(f'\napplied_companies.json entries: {len(applied_json["applications"])}')
for app in applied_json['applications']:
    if app['status'] == 'APPLIED':
        print(f'  {app["company"]} - {app["role"]}')
