#!/usr/bin/env python3
"""[Supply Discovery] Step 2 Confirm: Classification test suite."""
import json,sys
from pathlib import Path

import os, argparse
DATA = Path(__file__).parent.parent/"data"/"supply"/"2_file_inventory.json"

def get_config_path():
    """Resolve config path from Arg > Env > Default."""
    default_dir = Path(__file__).parent.parent/"config"
    
    parser = argparse.ArgumentParser()
    parser.add_argument("--config-dir", help="Path to config directory")
    args, _ = parser.parse_known_args()
    
    cfg_dir = Path(args.config_dir) if args.config_dir else Path(os.getenv('CONFIG_DIR', str(default_dir)))
    print(f"DEBUG: Using config dir: {cfg_dir}")
    return cfg_dir/"classification_config.json"

CFG = get_config_path()

def load_tests() -> dict:
    """Load test cases from config: {filename: expected_category}."""
    if not CFG.exists(): return {}
    with open(CFG) as f: cfg = json.load(f)
    return {fn: cat for cat, fns in cfg.get('test_cases', {}).items() for fn in fns}

def run():
    """Run tests, return (passed, failed, missing, failures)."""
    tests = load_tests()
    if not tests:  return 0, 0, 0, []
    if not DATA.exists():
        print(f"❌ Not found: {DATA}"); return 0, 0, len(tests), []
    
    with open(DATA) as f: data = json.load(f)
    actual = {f['name']: cat for cat, files in data.items() for f in files}
    
    p, f, m, fails = 0, 0, 0, []
    for fn, exp in tests.items():
        if   fn not in actual:   m += 1; fails.append(f"⚠️  MISSING: {fn}")
        elif actual[fn] == exp:  p += 1
        else: f += 1; fails.append(f"❌ {fn}: expected {exp}, got {actual[fn]}")
    return p, f, m, fails

def main():
    print("="*60 + "\nClassification Test Suite\n" + "="*60 + "\n")
    p, f, m, fails = run()
    tot = p + f + m
    
    if tot == 0: print("No tests. Add test_cases to config/classification_config.json"); sys.exit(0)
    if fails:    print("FAILURES:\n" + "\n".join(fails) + "\n")
    
    print("="*60 + f"\nResults: {p}/{tot} passed, {f} failed, {m} missing\n" + "="*60)
    print("✅ All passed!" if f == 0 and m == 0 else "❌ Some failed/missing.")
    sys.exit(0 if f == 0 and m == 0 else 1)

if __name__ == "__main__": main()
