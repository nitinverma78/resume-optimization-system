#!/usr/bin/env python3
"""Resume Optimization System - Main CLI Runner."""
import sys,os,time,argparse,subprocess
from pathlib import Path

ROOT    = Path(__file__).parent
SCRIPTS = ROOT/"scripts"

PHASES = {
    "init":              {"steps": []},
    "supply_discovery":  {"steps": ["1_scan_resume_folder.py", "2_classify_files.py", "2_confirm.py", "3_classification_report.py"]},
    "supply_extraction": {"steps": ["4_discover_sections.py", "5_extract_content.py", "6_build_knowledge_base.py"]},
    "supply_profile":    {"steps": ["7_parse_linkedin.py", "8_create_profile_db.py", "9_generate_profile_md.py"]},
    "demand_discovery":  {"steps": ["10_ingest_jds.py"]}
}

def check_env():
    """Robust Pre-flight Check: Returns (Ok, Message)."""
    # 1. Init directories
    for d in ["data", "data/supply", "data/demand", "data/supply/profile_data", "examples", "config"]:
        (ROOT/d).mkdir(parents=True, exist_ok=True); (ROOT/d/".gitkeep").touch()

    # 2. Load .env
    if (ROOT/".env").exists():
        with open(ROOT/".env") as f:
            for l in filter(None, (l.strip() for l in f)):
                if not l.startswith('#'): k,v = l.split('=',1); os.environ[k] = v.strip('"\'')
    
    # 3. Check critical vars
    msgs = []
    res_folder = os.getenv('RESUME_FOLDER')
    if not res_folder:
        msgs.append("❌ Environment Variable Missing: RESUME_FOLDER")
        msgs.append("   -> Upstream: System doesn't know where your resumes are.")
        msgs.append("   -> Downstream: Skipping supply discovery (Step 1-3 will fail).")
        msgs.append("   -> Fix: Export RESUME_FOLDER=/path/to/resumes OR add to .env file.")
    elif not Path(os.path.expanduser(res_folder)).exists():
        msgs.append(f"❌ Resume Folder Not Found: {res_folder}")
        msgs.append("   -> Upstream: The path specified in RESUME_FOLDER does not exist.")
        msgs.append("   -> Fix: Check the path or mount proper docker volume.")

    if not os.getenv('USER_NAME'):
        msgs.append("⚠️  Environment Variable Missing: USER_NAME")
        msgs.append("   -> Downstream: Ownership detection (Step 2) will be less accurate.")
        msgs.append("   -> Fix: Set USER_NAME='Your Name' in .env or docker-compose.yml")

    if not os.getenv('USER_EMAIL'):
        msgs.append("⚠️  Environment Variable Missing: USER_EMAIL")
        msgs.append("   -> Downstream: Resume parsing and profile generation (Step 9) need this.")
        msgs.append("   -> Fix: Set USER_EMAIL='you@email.com' (used for ID matching)")
    
    if msgs: return False, "\n".join(msgs)
    return True, "✅ Environment OK"

def run(name):
    """Run script, return Success."""
    path = SCRIPTS/name
    if not path.exists(): print(f"❌ Missing: {name}"); return False
    
    print(f"\n{'='*50}\n▶️  Running: {name}\n{'='*50}")
    t0 = time.time()
    try:
        r = subprocess.run([sys.executable, str(path)], check=False)
        dt = time.time()-t0
        if r.returncode==0: print(f"✅ Pass ({dt:.2f}s)"); return True
        else:               print(f"❌ Fail ({r.returncode})"); return False
    except Exception as e:  print(f"❌ Error: {e}"); return False

def main():
    p = argparse.ArgumentParser(description="Resume Optimization CLI")
    p.add_argument("--phase", help="Run specific phase")
    p.add_argument("--step",  help="Run specific step number")
    p.add_argument("--plan",  action="store_true", help="Show execution plan without running")
    args = p.parse_args()
    
    # Pre-flight Check
    ok, msg = check_env()
    if not ok:
        print("\n🛑 Pre-flight Check Failed:\n")
        print(msg)
        print("\nCannot proceed with full pipeline. Fix errors above.")
        sys.exit(1)
    
    # Select scripts
    all_steps = [(pid, s) for pid, d in PHASES.items() for s in d['steps']]
    if args.step:  to_run = [s for _,s in all_steps if s.startswith(f"{args.step}_")]
    elif args.phase:to_run = [s for pid,s in all_steps if pid==args.phase]
    else:          to_run = [s for _,s in all_steps]
    
    if not to_run: print("No steps found."); sys.exit(1)
    
    if args.plan:
        print(f"\n📋 Plan: {len(to_run)} steps")
        for s in to_run: print(f" - {s}")
        sys.exit(0)
    
    # Execute Default
    print(msg) # Print Env OK
    t0, fail = time.time(), []
    for s in to_run:
        if not run(s): fail.append(s); print(f"\n🛑 Halted at {s}"); break
    
    print(f"\n{'='*60}")
    print(f"❌ Failed" if fail else f"🎉 Success ({time.time()-t0:.1f}s)")
    sys.exit(1 if fail else 0)

if __name__=="__main__": main()
