#!/usr/bin/env python3
"""[Supply Discovery] Step 2 Confirm: Classification test suite."""
import json,sys,os,argparse
from pathlib import Path

def get_data_dir(): return Path(os.getenv('DATA_DIR')) if os.getenv('DATA_DIR') else Path(__file__).parent.parent/"data"

def get_cfg():
    p = argparse.ArgumentParser(); p.add_argument("--config-dir"); args, _ = p.parse_known_args()
    return (Path(args.config_dir) if args.config_dir else Path(os.getenv('CONFIG_DIR', str(Path(__file__).parent.parent/"config"))))/"classification_config.json"

def main():
    print("="*60 + "\nClassification Test Suite\n" + "="*60)
    cfg, data_path = get_cfg(), get_data_dir()/"supply"/"2_file_inventory.json"
    
    if not cfg.exists(): print("No config."); sys.exit(0)
    if not data_path.exists(): print(f"❌ Missing: {data_path}"); sys.exit(1)

    tests = {fn: cat for cat, fns in json.loads(cfg.read_text()).get('test_cases', {}).items() for fn in fns}
    if not tests: print("No tests defined."); sys.exit(0)
    
    actual = {f['name']: cat for cat, files in json.loads(data_path.read_text()).items() for f in files}
    fails = [f"⚠️  MISSING: {fn}" if fn not in actual else f"❌ {fn}: exp {exp} got {actual[fn]}" 
             for fn, exp in tests.items() if fn not in actual or actual[fn] != exp]

    if fails: print("FAILURES:\n" + "\n".join(fails))
    print(f"\nResults: {len(tests)-len(fails)}/{len(tests)} passed.")
    print("✅ All passed!" if not fails else "❌ Some failed.")
    sys.exit(bool(fails))

if __name__ == "__main__": main()
