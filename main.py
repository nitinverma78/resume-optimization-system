#!/usr/bin/env python3
"""Resume Optimization System - Main CLI Runner."""
import sys,os,time,argparse,subprocess,shutil,json
from pathlib import Path

ROOT = Path(__file__).parent
PIPELINE = {
    "supply":     ["1_scan_resume_folder.py", "2_classify_files.py", "2_confirm.py", "3_classification_report.py", "4_discover_sections.py", "5_extract_content.py", "6_build_knowledge_base.py"],
    "profile":    ["7_parse_linkedin.py", "8_create_profile_db.py", "9_generate_profile_md.py"],
    "demand":     ["10_ingest_jds.py"],
    "matching":   ["11_match_gaps.py"],
    "validation": ["validate_data_isolation.py"]
}

def check_env(mode="normal", clean=False):
    """Robust Pre-flight Check: Returns (Ok, Message, overrides_dict)."""
    overrides, msgs = {}, []
    
    if mode == "demo":
        print("🔧 Configuring Demo (Isolated)...")
        sim, d_data = ROOT/"simulate", ROOT/"simulate"/"data"
        os.environ.update({'RESUME_FOLDER':str(sim/"input_resumes"), 'USER_NAME':"Jane Doe", 'USER_EMAIL':"jane.doe@example.com", 'DATA_DIR':str(d_data)})
        print(f"📋 Env: USER_NAME={os.getenv('USER_NAME')}, USER_EMAIL={os.getenv('USER_EMAIL')}")
        print(f"📋 Env: RESUME_FOLDER={os.getenv('RESUME_FOLDER')}")
        if d_data.exists(): 
            print(f"🧹 Clearing {d_data.relative_to(ROOT)}")
            for item in d_data.iterdir(): 
                if item.is_dir(): shutil.rmtree(item)
                else: item.unlink()
        for d in ["supply/profile_data", "demand", "matching"]: (d_data/d).mkdir(parents=True, exist_ok=True)
        overrides['2_confirm.py'] = ["--config-dir", str(sim/"config")]
        overrides['6_build_knowledge_base.py'] = ["--config", str(sim/"config"/"knowledge_base.json")]
        return True, "✅ Demo Mode: simulate/data", overrides

    if clean and (d:=ROOT/"data").exists(): print("🧹 Cleaning data/..."); shutil.rmtree(d)
    for d in ["data", "data/supply/profile_data", "data/demand", "data/matching", "simulate", "config"]: (ROOT/d).mkdir(parents=True, exist_ok=True)
    if (env:=ROOT/'.env').exists():
        for l in env.read_text().splitlines():
             if '=' in l and not l.strip().startswith('#'): k,v=l.strip().split('=',1); os.environ[k]=v.strip('"')
    if rf := os.getenv('RESUME_FOLDER'): os.environ['RESUME_FOLDER'] = os.path.expanduser(rf)

    print(f"📋 Env: USER_NAME={os.getenv('USER_NAME')}, USER_EMAIL={os.getenv('USER_EMAIL')}")
    print(f"📋 Env: RESUME_FOLDER={os.getenv('RESUME_FOLDER')}")
    
    if not os.getenv('RESUME_FOLDER') or not Path(os.path.expanduser(os.getenv('RESUME_FOLDER'))).exists(): msgs.append("❌ Missing/Invalid RESUME_FOLDER")
    if not os.getenv('USER_NAME'): msgs.append("⚠️  Missing USER_NAME")
    if not os.getenv('USER_EMAIL'): msgs.append("⚠️  Missing USER_EMAIL")
    return not bool(msgs), "\n".join(msgs) or "✅ Environment OK", overrides

def run_step(script, overrides=None):
    print(f"\n▶️  Running: {script}"); t0 = time.time()
    cmd = [sys.executable, str(ROOT/"scripts"/script)] + (overrides.get(script, []) if overrides else [])
    try:
        env = os.environ.copy(); env["PYTHONPATH"] = str(ROOT) + os.pathsep + env.get("PYTHONPATH","")
        r = subprocess.run(cmd, check=False, env=env)
        print(f"{'✅ Pass' if r.returncode==0 else '❌ Fail'} ({time.time()-t0:.2f}s)")
        return r.returncode == 0
    except Exception as e: print(f"❌ Error: {e}"); return False

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--demo", action="store_true", help="Run simulation")
    p.add_argument("--clean", action="store_true", help="Clean data/")
    p.add_argument("--plan", action="store_true", help="Show plan")
    p.add_argument("--phase", choices=PIPELINE.keys(), help="Run only specific phase")
    p.add_argument("--step", help="Run only specific step")
    args = p.parse_args()

    # If --clean is used alone, just clean and exit
    if args.clean and not (args.demo or args.phase or args.step or args.plan):
        if (d:=ROOT/"data").exists(): print("🧹 Cleaning data/..."); shutil.rmtree(d)
        print("✅ Data cleaned"); sys.exit(0)

    ok, msg, over = check_env("demo" if args.demo else "normal", args.clean)
    print(f"\n{msg}\n"); 
    if not ok: sys.exit(1)

    steps = [s for k,v in PIPELINE.items() if not args.phase or k==args.phase for s in v]
    if args.step: steps = [s for s in steps if args.step in s]

    if args.plan: [print(f" {i}. {s}") for i,s in enumerate(steps,1)]; sys.exit(0)
    
    t0 = time.time()
    for s in steps:
        if not run_step(s, over): print("\n⛔ Stopped."); sys.exit(1)
    print(f"\n🎉 Success ({time.time()-t0:.1f}s)")

if __name__=="__main__": main()
