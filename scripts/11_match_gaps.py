#!/usr/bin/env python3
"""[Matching Engine] Step 11: Calculate Gap Analysis between Profile and JDs."""
import json, sys, re, math
from pathlib import Path
from collections import Counter
import argparse

ROOT = Path(__file__).parent.parent
DATA_SUPPLY = ROOT/"data"/"supply"/"profile_data"
DATA_DEMAND = ROOT/"data"/"demand"
OUT_DIR     = ROOT/"data"/"matching"

class Matcher:
    def __init__(self):
        self.profile = self._load_profile()
        self.jds     = self._load_jds()
        OUT_DIR.mkdir(parents=True, exist_ok=True)

    def _load_profile(self):
        """Load structured profile."""
        path = DATA_SUPPLY/"profile-structured.json"
        if not path.exists():
            print(f"❌ Missing profile: {path}")
            sys.exit(1)
        with open(path) as f: return json.load(f)

    def _load_jds(self):
        """Load JDs database."""
        path = DATA_DEMAND/"1_jd_database.json"
        if not path.exists():
            print(f"❌ Missing JD database: {path}")
            sys.exit(1)
        with open(path) as f:
            data = json.load(f)
            # Handle structure: {"roles": [...]} 
            return data.get('roles', [])

    def extract_keywords(self, text):
        """Simple keyword extractor (normalized)."""
        if not text: return set()
        # Basic tokenization: split by non-alphanumeric, lowercase
        tokens = re.findall(r'\b[a-z]{2,50}\b', text.lower())
        # Filter stopwords (mini list)
        stopwords = {'the','and','for','with','this','that','from','have','are','was','can','will','not','but','all','any','your','their','our','each','these','those','has','its','other','which','what','when','where','why','how'}
        return set(t for t in tokens if t not in stopwords)

    def calculate_match(self, profile_text, jd_text):
        """Calculate overlap score."""
        p_keywords = self.extract_keywords(profile_text)
        j_keywords = self.extract_keywords(jd_text)
        
        if not j_keywords: return 0, set(), set()
        
        overlap  = p_keywords & j_keywords
        missing  = j_keywords - p_keywords
        
        # Jaccard-ish score: Overlap / JD size (how much of JD is covered?)
        # We care about covering JD requirements, not about extra stuff in resume.
        score = (len(overlap) / len(j_keywords)) * 100
        return round(score, 1), overlap, missing

    def run(self):
        print("🚀 Running Matching Engine...")
        
        # Flatten profile for matching
        p_data = self.profile
        p_text = f"{p_data.get('headline','')} {p_data.get('summary','')} "
        for exp in p_data.get('experience', []):
            p_text += f"{exp.get('title','')} {exp.get('company','')} {exp.get('description','')} "
        for edu in p_data.get('education', []):
            p_text += f"{edu.get('school','')} {edu.get('degree','')} "
            
        results = []
        for jd in self.jds:
            jd_text = jd.get('content', '')
            score, overlap, missing = self.calculate_match(p_text, jd_text)
            
            res = {
                "id": jd.get('id'),
                "filename": jd.get('filename'),
                "score": score,
                "missing_keywords": sorted(list(missing)),
                "overlap_keywords": sorted(list(overlap))
            }
            results.append(res)
            print(f"  • {jd.get('filename')}: {score}% Match")

        # Save results
        out_path = OUT_DIR/"11_gap_analysis.json"
        with open(out_path, 'w') as f: json.dump(results, f, indent=2)
        print(f"✅ Gap Analysis saved to: {out_path}")
        
        # Generate Markdown Report
        md_path = OUT_DIR/"11_gap_analysis_report.md"
        with open(md_path, 'w') as f:
            f.write("# Gap Analysis Report\n\n")
            for r in results:
                f.write(f"## {r['filename']} (Score: {r['score']}%)\n")
                f.write(f"### Missing Keywords ({len(r['missing_keywords'])})\n")
                f.write(", ".join(r['missing_keywords'][:50])) # Limit output
                f.write("\n\n")
        print(f"✅ Report saved to: {md_path}")

if __name__ == "__main__":
    Matcher().run()
