#!/usr/bin/env python3
"""[Supply Public Profile] Step 7: Parse LinkedIn profile PDF."""
import sys,json,os,argparse
from pathlib import Path
from scripts.lib_extract import extract

def get_data_dir(): return Path(os.getenv('DATA_DIR') or Path(__file__).parent.parent/"data")

def main():
    p = argparse.ArgumentParser(); p.add_argument("pdf", nargs="?"); p.add_argument("--out"); args = p.parse_args()
    out = Path(args.out) if args.out else get_data_dir()/"supply"/"profile_data"/"linkedin-profile-parsed.json"
    
    pdf = Path(args.pdf) if args.pdf else Path(os.getenv('LINKEDIN_PDF') or "")
    if not pdf.name: 
        if not (rf:=os.getenv('RESUME_FOLDER')): print("Error: No PDF/RESUME_FOLDER"); sys.exit(1)
        found = list(Path(rf).expanduser().rglob("MyLinkedInProfile.pdf"))
        if not found: print(f"Error: MyLinkedInProfile.pdf not found in {rf}"); sys.exit(1)
        pdf = found[0]

    print(f"Parsing {pdf}...")
    txt = extract(pdf)
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, 'w') as f: json.dump({"raw_text": txt, "metadata": {"source": str(pdf)}}, f, indent=2)
    print(f"✓ Saved to {out}\nExtracted {len(txt)} chars.")

if __name__ == "__main__": main()
