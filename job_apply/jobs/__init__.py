"""jobs/__init__.py - Job fetcher registry"""
from jobs.linkedin   import fetch as linkedin_fetch
from jobs.internshala import fetch as internshala_fetch
from jobs.indeed     import fetch as indeed_fetch
from jobs.wellfound  import fetch as wellfound_fetch
from jobs.naukri     import fetch as naukri_fetch

FETCHERS = {
    "LinkedIn":    linkedin_fetch,
    "Internshala": internshala_fetch,
    "Indeed":      indeed_fetch,
    "Wellfound":   wellfound_fetch,
    "Naukri":      naukri_fetch,
}
