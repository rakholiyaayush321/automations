"""
batch_loader_enhanced.py - Enhanced batch loader with priority and validation
============================================================================
"""

import argparse
import re
import sys
from datetime import date
from pathlib import Path

# Use enhanced config
sys.path.insert(0, str(Path(__file__).parent))
from config import (
    PROJECT_DIR, DAILY_TARGET_MIN, DAILY_TARGET_MAX,
    PRIORITY_COMPANIES, PREFERRED_SIZES, CANDIDATE
)
from matcher_enhanced import classify_company_size, is_preferred_size, is_priority_company

JOBS_FILE   = PROJECT_DIR / "jobs.txt"
SENT_FILE   = PROJECT_DIR / "sent_companies.txt"
BATCH_MARKER = PROJECT_DIR / ".current_batch"
PRIORITY_LOG = PROJECT_DIR / "priority_applications.log"

# ── Enhanced Company Database ────────────────────────────────────────────────
# Format: (company_name, website, size, verified_email, industry_focus)
ENHANCED_COMPANIES = [
    # Priority Tier 1: Top AI/ML Companies
    ("Fxis.ai", "fxis.ai", "20-50", "", "AI/ML"),
    ("Inferenz", "inferenz.ai", "20-50", "careers@inferenz.ai", "AI/ML"),
    ("Neuramonks", "neuramonks.com", "20-50", "careers@neuramonks.com", "AI/ML"),
    ("SoluLab", "solulab.com", "200-500", "careers@solulab.com", "Blockchain/AI"),
    ("Bacancy", "bacancytechnology.com", "500+", "careers@bacancytechnology.com", "Software"),
    
    # Priority Tier 2: Established Ahmedabad Companies
    ("OpenXcell", "openxcell.com", "100-500", "careers@openxcell.com", "Software"),
    ("TatvaSoft", "tatvasoft.com", "200-500", "careers@tatvasoft.com", "Software"),
    ("Radixweb", "radixweb.com", "200-500", "hr@radixweb.com", "Software"),
    ("Crest Data Systems", "crestdatasystems.com", "100-300", "careers@crestdatasystems.com", "Data"),
    ("MindInventory", "mindinventory.com", "200-500", "career@mindinventory.com", "Software"),
    ("Simform", "simform.com", "500+", "careers@simform.com", "Software"),
    
    # AI/ML Specialized Companies
    ("Stellar", "stellarai.io", "20-50", "careers@stellarai.io", "AI"),
    ("CloudIRA", "cloudira.io", "20-50", "hr@cloudira.io", "AI/Cloud"),
    ("Softrefine Technology", "softrefine.com", "50-200", "hr@softrefine.com", "AI/ML"),
    ("Solvative", "solvative.com", "100-300", "contact@solvative.com", "AI/ML"),
    ("Anblicks", "anblicks.com", "100-300", "marketing@anblicks.com", "Data/AI"),
    
    # Growing Tech Companies
    ("Sparks to Ideas", "sparkstoideas.com", "50-150", "info@sparkstoideas.com", "Software"),
    ("Maxgen Technologies", "maxgentechnology.com", "50-100", "komal@maxgentechnology.com", "Software"),
    ("iView Labs", "iviewlabs.com", "100-300", "hr@iviewlabs.com", "Software"),
    ("TechAdros", "techadros.com", "20-50", "careers@techadros.com", "AI"),
    ("HashRoot", "hashroot.com", "50-150", "careers@hashroot.com", "Software"),
    
    # Mid-Size Companies
    ("Agile Infoways", "agileinfoways.com", "50-200", "hr@agileinfoways.com", "Software"),
    ("Elsner Technologies", "elsner.com", "100-300", "hr@elsner.com", "Software"),
    ("Inheritx Solutions", "inheritx.com", "50-150", "priya.b@inheritx.com", "Software"),
    ("Bosc Tech Labs", "bosctechlabs.com", "50-150", "hr@bosctechlabs.com", "AI"),
    ("AxisTechnoLab", "axistechnolabs.com", "20-100", "career@axistechnolabs.com", "Software"),
    
    # More Specialized Companies
    ("Metaqualt", "metaqualt.com", "20-50", "hr@metaqualt.com", "AI"),
    ("Green Ping Solutions", "greenping.in", "10-50", "info@greenping.in", "Software"),
    ("NexusLink Services", "nexuslinkservices.com", "20-50", "info@nexuslinkservices.com", "Software"),
    ("Technource", "technource.com", "100-300", "career@technource.com", "Software"),
    ("E2M Solutions", "e2msolutions.com", "50-150", "career@e2msolutions.com", "Software"),
    
    # Startup/Innovation Focused
    ("NeoCell Technologies", "neocelltech.com", "20-100", "careers@neocelltech.com", "Tech"),
    ("MagikKraft", "magikkraft.com", "20-50", "info@magikkraft.com", "AI"),
    ("Whatmaction", "whatmaction.com", "50-150", "hr@whatmaction.com", "Software"),
    ("Prioso", "prioso.com", "20-50", "hr@prioso.com", "Software"),
    ("ArgyleEnigma Tech Labs", "argyleenigma.com", "20-50", "hr@argyleenigma.com", "AI"),
    
    # Additional Quality Companies
    ("Unique IT Solutions", "uniqueitsolutions.com", "20-50", "info@uniqueitsolutions.com", "Software"),
    ("WeServe Codes", "weservecodes.com", "20-50", "hr@weservecodes.com", "Software"),
    ("Vasudevika Software", "vasudevika.com", "20-50", "hr@vasudevika.com", "Software"),
    ("Swan Softweb Solutions", "swansoftweb.com", "20-100", "info@swan.com", "Software"),
    ("Algoscale", "algoscale.com", "100-300", "careers@algoscale.com", "Data/AI"),
    ("Techtic Solutions", "techtic.com", "50-200", "hr@techtic.com", "Software"),
    ("NDZ (nDimensionZ)", "ndimensionz.com", "200-500", "careers@ndz.com", "Software"),
    
    # New AI-Focused Additions
    ("Cybrain Software", "cybrainsoftware.com", "50-200", "careers@cybrainsoftware.com", "AI"),
    ("Q3 Technologies", "q3tech.com", "50-150", "careers@q3tech.com", "Software"),
    ("Peerbits", "peerbits.com", "100-300", "careers@peerbits.com", "Software"),
    ("SemiDot Infotech", "semidotinfotech.com", "20-100", "careers@semidotinfotech.com", "AI"),
    ("Hodusoft", "hodusoft.com", "100-300", "careers@hodusoft.com", "Software"),
    
    # April 7, 2025 - New Web Search Additions
    # AI/ML Focused Startups
    ("Hashtechy", "hashtechy.com", "20-50", "careers@hashtechy.com", "AI"),
    ("WotNot Solutions", "wotnot.io", "50-150", "careers@wotnot.io", "AI"),
    ("TrackNOW", "tracknow.in", "20-100", "careers@tracknow.in", "Software"),
    ("BrainStream Technolabs", "brainstreamtechnolabs.com", "50-200", "careers@brainstreamtechnolabs.com", "Software"),
    ("Yodep Software", "yodep.com", "20-50", "careers@yodep.com", "Software"),
    ("ADDV HealthTech", "addvhealthtech.com", "20-50", "careers@addvhealthtech.com", "AI/Health"),
    ("Robosys Automation", "robosys.co.in", "50-150", "careers@robosys.co.in", "AI/Robotics"),
    ("ProTech ITS", "protechits.com", "50-150", "careers@protechits.com", "Software"),
    ("ESTANOVA TECH SOL", "estanova.com", "20-50", "careers@estanova.com", "Software"),
    ("Zobi Web Solutions", "zobiwebsolutions.com", "20-50", "careers@zobiwebsolutions.com", "Software"),
    
    # Established Companies
    ("IndiaNIC Infotech", "indianic.com", "200-500", "careers@indianic.com", "Software"),
    ("Cybage Software", "cybage.com", "500+", "careers@cybage.com", "Software"),
    ("Sapphire Software Solutions", "sapphiresolutions.net", "100-300", "careers@sapphiresolutions.net", "Software"),
    ("Apexon", "apexon.com", "500+", "careers@apexon.com", "Software"),
    
    # Startup Ecosystem - AI Focused
    ("Bull Agritech", "bullagritech.com", "10-50", "careers@bullagritech.com", "AI/Agri"),
    ("HyprForge", "hyprforge.com", "10-50", "careers@hyprforge.com", "AI"),
    ("Fx31 Labs", "fx31labs.com", "10-50", "careers@fx31labs.com", "AI"),
    ("Infocusp Innovations", "infocusp.com", "20-100", "careers@infocusp.com", "AI"),
    ("EveoAI Research Lab", "eveoai.com", "10-50", "careers@eveoai.com", "AI/Research"),
    ("Matrix One", "matrixone.com", "20-50", "careers@matrixone.com", "Software"),
    ("Soulera", "soulera.com", "10-50", "careers@soulera.com", "Software"),
    ("VIDERIS", "videris.io", "10-50", "careers@videris.io", "AI"),
    ("F(x) Data Labs", "fxdatalabs.com", "20-100", "careers@fxdatalabs.com", "Data/AI"),
    ("Centous Solutions", "centous.com", "10-50", "careers@centous.com", "Software"),
    
    # ── Crawl-Verified Companies (April 2025) ────────────────────────────────
    ("Ecosmob Technologies", "ecosmob.com", "100-300", "careers@ecosmob.com", "Software"),
    ("Azilen Technologies", "azilen.com", "100-300", "careers@azilen.com", "Software"),
    ("Yudiz Solutions", "yudiz.com", "100-300", "career@yudiz.com", "Software"),
    ("Differenz System", "differenzsystem.com", "50-200", "hr@differenz.co.in", "Software"),
    ("Zensar Technologies", "zensar.com", "500+", "careers@zensar.com", "Software"),
    ("KPIT Technologies", "kpit.com", "500+", "careers@kpit.com", "AI/Software"),
    ("SPEC India", "spec-india.com", "200-500", "careers@spec-india.com", "Software"),
    ("iFour Technolab", "ifourtechnolab.com", "100-300", "careers@ifourtechnolab.com", "Software"),
    ("Logistic Infotech", "logisticinfotech.com", "50-150", "hr@logisticinfotech.com", "Software"),
    ("Hyperlink InfoSystem", "hyperlinkinfosystem.com", "200-500", "careers@hyperlinkinfosystem.com", "Software"),
    ("Prismetric", "prismetric.com", "50-200", "careers@prismetric.com", "Software"),
    ("Artoon Solutions", "artoonsolutions.com", "100-300", "hr@artoonsolutions.com", "Software"),
    ("Zealous System", "zealoussystem.com", "50-200", "careers@zealoussystem.com", "Software"),
    ("Persistent Systems", "persistent.com", "500+", "careers@persistent.com", "Software"),
    ("Harbinger Systems", "harbinger-systems.com", "200-500", "careers@harbinger-systems.com", "Software"),
    ("Calsoft Inc", "calsoftinc.com", "200-500", "careers@calsoftinc.com", "Software"),
    ("Sarvatra Technologies", "sarvatra.co.in", "100-300", "hr@sarvatra.co.in", "Software"),
    
    # ── Pune AI/ML Companies ─────────────────────────────────────────────────
    ("Pubmatic", "pubmatic.com", "500+", "careers@pubmatic.com", "AI/Software"),
    ("Icertis", "icertis.com", "500+", "careers@icertis.com", "AI/Software"),
    ("Druva", "druva.com", "500+", "careers@druva.com", "Software"),
    ("Mphasis", "mphasis.com", "500+", "careers@mphasis.com", "AI/Software"),
    ("Veritas Technologies", "veritas.com", "500+", "careers@veritas.com", "Software"),
    ("Cuelogic Technologies", "cuelogic.com", "100-300", "careers@cuelogic.com", "AI"),
    ("ThoughtWorks Pune", "thoughtworks.com", "500+", "careers@thoughtworks.com", "Software"),
    ("Accion Labs", "accionlabs.com", "200-500", "careers@accionlabs.com", "Software"),
    ("Coditas", "coditas.com", "100-300", "careers@coditas.com", "Software"),
    ("Forcepoint", "forcepoint.com", "500+", "careers@forcepoint.com", "Software"),
]


# ── Helper Functions ──────────────────────────────────────────────────────────
def normalize(name: str) -> str:
    """Normalize company name for matching."""
    name = name.lower().strip()
    name = re.sub(r'[\s\-\._]+', '', name)
    return name


def load_sent() -> set:
    """Load already sent company names."""
    sent = set()
    if SENT_FILE.exists():
        with open(SENT_FILE, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '|' in line:
                    parts = line.split('|')
                    if len(parts) >= 2:
                        sent.add(normalize(parts[1]))
    return sent


def get_company_priority(company_name: str, company_size: str) -> int:
    """
    Calculate company priority score (higher = more priority).
    Returns 0-100 score.
    """
    score = 50  # Base score
    
    # Priority list bonus
    if is_priority_company(company_name):
        score += 30
    
    # Size preference
    size_category = classify_company_size(company_size)
    if size_category == "STARTUP":
        score += 15
    elif size_category == "SMALL":
        score += 10
    elif size_category == "MID":
        score += 5
    elif size_category == "LARGE":
        score -= 20  # Penalty for large companies
    
    return score


def select_companies(count: int = 15) -> list:
    """
    Select companies with priority weighting.
    
    Returns list of (company_name, website, size, email, priority_score)
    """
    sent = load_sent()
    available = []
    
    for company in ENHANCED_COMPANIES:
        name, website, size, email, industry = company
        norm_name = normalize(name)
        
        # Skip if already sent
        if norm_name in sent:
            continue
        
        # Calculate priority
        priority = get_company_priority(name, size)
        
        # Generate email if not provided
        if not email:
            domain = website.replace('https://', '').replace('http://', '').replace('www.', '').strip('/')
            email = f"careers@{domain}"
        
        available.append((name, website, size, email, priority, industry))
    
    # Sort by priority (highest first)
    available.sort(key=lambda x: x[4], reverse=True)
    
    # Return top N
    return available[:count]


def generate_job_title(industry: str) -> str:
    """Generate a RANDOM job title from TARGET_ROLES, weighted by industry."""
    import random
    from config import TARGET_ROLES
    
    # AI-focused roles for AI companies
    ai_roles = ["AI Intern", "AI Trainee", "ML Intern", "ML Trainee", "Data Science Intern"]
    # General roles for software companies
    general_roles = ["Python Intern", "Python Trainee", "Python Developer",
                     "Software Developer", "Junior Developer", "Fresher", "Trainee"]
    
    if industry in ("AI", "AI/ML", "AI/Software", "AI/Research", "AI/Robotics", "AI/Health", "AI/Agri"):
        pool = ai_roles + ["Python Intern"]
    elif industry in ("Data", "Data/AI"):
        pool = ["Data Science Intern", "ML Intern", "AI Intern", "Python Intern"]
    else:
        pool = general_roles + ["AI Intern"]
    
    return random.choice(pool)


def load_batch(count: int = 20) -> int:
    """Load next batch of companies into jobs.txt from verified database."""
    
    print(f"\n{'='*60}", flush=True)
    print(f"[BATCH LOADER] Loading {count} companies with diverse roles...", flush=True)
    print(f"  Database size: {len(ENHANCED_COMPANIES)} companies", flush=True)
    print(f"{'='*60}", flush=True)
    
    total_companies = []
    
    # Select companies from verified database with random diverse titles
    static_companies = select_companies(count)
    for sc in static_companies:
        name, website, size, email, priority, industry = sc
        job_title = generate_job_title(industry)
        total_companies.append((name, website, size, email, priority, industry, job_title))
    
    if not total_companies:
        print("No new companies available!")
        return 0
    
    # Write to jobs.txt
    with open(JOBS_FILE, 'w', encoding='utf-8') as f:
        f.write(f"# jobs.txt - Auto-generated batch (Dynamic + Static)\n")
        f.write(f"# Generated: {date.today().isoformat()}\n")
        f.write(f"# Companies: {len(total_companies)}\n")
        f.write(f"# Format: Job Title | Company | Email\n\n")
        
        for company in total_companies:
            name, website, size, email, priority, industry, job_title = company
            
            # Write job entry
            f.write(f"{job_title} | {name} | {email}\n")
            
            # Log priority companies
            if priority >= 70:
                log_priority_company(name, priority)
    
    # Save batch marker
    with open(BATCH_MARKER, 'w') as f:
        f.write(f"batch_date={date.today().isoformat()}\n")
        f.write(f"count={len(total_companies)}\n")
    
    # Print summary
    print(f"Loaded {len(total_companies)} companies into jobs.txt:")
    priority_count = sum(1 for c in total_companies if c[4] >= 70)
    print(f"  - Priority companies: {priority_count}")
    print(f"  - Regular companies: {len(total_companies) - priority_count}")
    
    for company in total_companies[:5]:  # Show first 5
        name, _, size, email, priority, _, _ = company
        print(f"  {name} -> {email} [Priority: {priority}]")
    
    if len(total_companies) > 5:
        print(f"  ... and {len(total_companies) - 5} more")
    
    return len(total_companies)


def log_priority_company(name: str, priority: int):
    """Log priority company application."""
    with open(PRIORITY_LOG, 'a', encoding='utf-8') as f:
        f.write(f"{date.today().isoformat()} | {name} | Priority: {priority}\n")


def show_status():
    """Show current batch status."""
    sent = load_sent()
    available = [c for c in ENHANCED_COMPANIES if normalize(c[0]) not in sent]
    
    print(f"Total companies in database: {len(ENHANCED_COMPANIES)}")
    print(f"Already applied: {len(sent)}")
    print(f"Available: {len(available)}")
    
    if BATCH_MARKER.exists():
        with open(BATCH_MARKER, 'r') as f:
            print(f"\nLast batch:")
            print(f.read())


def list_all():
    """List all companies."""
    sent = load_sent()
    
    print(f"\n{'Company':<30} {'Size':<15} {'Priority':<10} {'Status'}")
    print("-" * 70)
    
    for company in ENHANCED_COMPANIES:
        name, website, size, email, industry = company
        norm = normalize(name)
        priority = get_company_priority(name, size)
        status = "SENT" if norm in sent else "AVAILABLE"
        
        print(f"{name:<30} {size:<15} {priority:<10} {status}")


# ── Main ─────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Enhanced batch loader")
    parser.add_argument("--count", type=int, default=15, help="Number of companies to load")
    parser.add_argument("--status", action="store_true", help="Show status")
    parser.add_argument("--list", action="store_true", help="List all companies")
    
    args = parser.parse_args()
    
    if args.status:
        show_status()
    elif args.list:
        list_all()
    else:
        count = load_batch(args.count)
        sys.exit(0 if count > 0 else 1)
