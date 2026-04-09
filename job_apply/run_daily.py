"""
run_daily.py - Daily batch loader + pipeline runner
Run via: python run_daily.py
Called automatically by cron at 10 AM IST
"""
import subprocess
import sys
from pathlib import Path

PROJECT_DIR = Path(__file__).parent

def run(cmd):
    print(f"\n>>> Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=PROJECT_DIR)
    return result.returncode

def main():
    print("=" * 60)
    print("  DAILY JOB APPLICATION RUNNER")
    print("=" * 60)

    # Step 1: Load next batch of 15 companies into jobs.txt
    print("\n[Step 1] Loading next batch of companies...")
    rc = run(["python", "batch_loader.py", "--count", "15"])
    if rc != 0:
        print(f"batch_loader failed with code {rc}")
        sys.exit(rc)

    # Step 2: Run the pipeline
    print("\n[Step 2] Running application pipeline...")
    rc = run(["python", "main.py", "--run"])

    print("\n" + "=" * 60)
    if rc == 0:
        print("  DAILY RUN COMPLETE")
    else:
        print(f"  PIPELINE FAILED (code {rc})")
    print("=" * 60)
    sys.exit(rc)

if __name__ == "__main__":
    main()
