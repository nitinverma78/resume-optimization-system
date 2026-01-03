#!/usr/bin/env python3
"""Resume Optimization System - Main CLI Runner."""
import sys,os,time,argparse,subprocess,shutil,json
from pathlib import Path

ROOT    = Path(__file__).parent
SCRIPTS = ROOT/"scripts"

# Pipeline Definitions
PIPELINE = {
    "supply_discovery":  {"steps": [
        "1_scan_resume_folder.py",
        "2_classify_files.py",
        "2_confirm.py",
        "3_classification_report.py",
        "4_discover_sections.py",
        "5_extract_content.py",
        "6_build_knowledge_base.py"
    ]},
    "profile_generation": {"steps": [
        "7_parse_linkedin.py",
        "8_create_profile_db.py",
        "9_generate_profile_md.py"
    ]},
    "demand_discovery":  {"steps": ["10_ingest_jds.py"]},
    "matching":          {"steps": ["11_match_gaps.py"]},
    "validation":        {"steps": ["validate_data_isolation.py"]}
}

def check_env(mode="normal", clean=False):
    """Robust Pre-flight Check: Returns (Ok, Message, overrides_dict)."""
    overrides = {}
    msgs = []
    
    # === DEMO MODE ===
    if mode == "demo":
        print("🔧 Configuring Demo Environment (Isolated)...")
        
        sim_dir = ROOT/"simulate"
        demo_data = sim_dir/"data"
        
        # 1. Set Isolated Environment
        os.environ['RESUME_FOLDER'] = str(sim_dir/"input_resumes")
        os.environ['USER_NAME'] = "Jane Doe"
        os.environ['USER_EMAIL'] = "jane.doe@example.com"
        os.environ['DATA_DIR']  = str(demo_data) # Redirect I/O to simulate/data
        
        # 2. Always Clean Simulation Data (Fresh Run)
        if demo_data.exists():
            print(f"🧹 Clearing simulation output: {demo_data.relative_to(ROOT)}")
            shutil.rmtree(demo_data)
            
        # 3. Initialize Simulation Dirs
        for d in ["supply/profile_data", "demand", "matching"]:
             (demo_data/d).mkdir(parents=True, exist_ok=True)
             
        # 4. Config Override
        demo_cfg_dir = sim_dir/"config"
        overrides['2_confirm.py'] = ["--config-dir", str(demo_cfg_dir)]

        return True, "✅ Demo Mode Activated (Output: simulate/data)", overrides

    # === NORMAL MODE ===
    
    # 1. Clean Production Data ONLY if requested
    if clean:
        data_dir = ROOT/"data"
        if data_dir.exists():
            print("🧹 Cleaning production data/ folder...")
            shutil.rmtree(data_dir)
    
    # 2. Initialize Production Dirs
    # Ensure simulate/config exist too for structure
    for d in ["data", "data/supply/profile_data", "data/demand", "data/matching", "simulate", "config"]:
        (ROOT/d).mkdir(parents=True, exist_ok=True); (ROOT/d/".gitkeep").touch()

    # 3. Load .env
    env_path = ROOT / '.env'
    if env_path.exists():
        with open(env_path) as f:
            for line in f:
                if line.strip() and not line.startswith('#'):
                    k, v = line.strip().split('=', 1)
                    if k not in os.environ or not os.environ[k]:
                        os.environ[k] = v.strip('"')
    
    # 4. Validation
    res_folder = os.getenv('RESUME_FOLDER')
    if not res_folder:
        msgs.append("❌ Environment Variable Missing: RESUME_FOLDER")
    elif not Path(os.path.expanduser(res_folder)).exists():
        msgs.append(f"❌ Resume Folder Not Found: {res_folder}")

    if not os.getenv('USER_NAME'):
        msgs.append("⚠️  Environment Variable Missing: USER_NAME")
        
    if not os.getenv('USER_EMAIL'):
        msgs.append("⚠️  Environment Variable Missing: USER_EMAIL")
        msgs.append("   -> Fix: Set USER_EMAIL='you@email.com' (used for ID matching)")
    
    if msgs: return False, "\n".join(msgs), overrides
    return True, "✅ Environment OK (Output: data/)", overrides

def run_step(script_name, overrides=None):
    """Run a single script with optional arg overrides."""
    print(f"\n==================================================")
    print(f"▶️  Running: {script_name}")
    print(f"==================================================")
    
    script_path = ROOT/"scripts"/script_name
    t0 = time.time()
    
    cmd = [sys.executable, str(script_path)]
    if overrides and script_name in overrides:
        cmd.extend(overrides[script_name])

    print(f"DEBUG CMD: {cmd}")

    try:
        # Pass current environment to subprocess
        r = subprocess.run(cmd, check=False, env=os.environ, capture_output=False) # capture_output=False lets stdout flow to terminal
        dt = time.time()-t0
        if r.returncode==0: print(f"✅ Pass ({dt:.2f}s)"); return True
        else:               print(f"❌ Fail ({r.returncode})"); return False
    except Exception as e:  print(f"❌ Error: {e}"); return False

def main():
    parser = argparse.ArgumentParser(description="Resume Optimization Pipeline")
    parser.add_argument("--demo", action="store_true", help="Run end-to-end simulation")
    parser.add_argument("--plan", action="store_true", help="Show execution plan")
    parser.add_argument("--clean", action="store_true", help="Clean data/ folder before running")
    args = parser.parse_args()

    mode = "demo" if args.demo else "normal"
    ok, msg, overrides = check_env(mode, clean=args.clean)
    print(f"\n{msg}\n")
    if not ok: sys.exit(1)

    steps = []
    for stage, config in PIPELINE.items():
        steps.extend(config["steps"])

    if args.plan:
        print("📋 Execution Plan:")
        for i, s in enumerate(steps, 1):
            extra = f" {overrides[s]}" if (overrides and s in overrides) else ""
            print(f" {i}. {s}{extra}")
        sys.exit(0)

    t_start = time.time()
    for step in steps:
        if not run_step(step, overrides):
             print("\n⛔ Pipeline stopped due to failure.")
             sys.exit(1)

    print(f"\n============================================================")
    print(f"🎉 Success ({time.time() - t_start:.1f}s)")

if __name__=="__main__": main()
