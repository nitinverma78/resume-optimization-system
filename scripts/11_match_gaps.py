#!/usr/bin/env python3
"""[Matching Engine] Step 11: Calculate Gap Analysis."""
import json,sys,re,os
from pathlib import Path
from collections import Counter
def get_data_dir(): return Path(os.getenv('DATA_DIR') or Path(__file__).parent.parent/"data")

class Matcher:
    def __init__(self):
        dd=get_data_dir(); self.sup, self.dem = dd/"supply"/"profile_data", dd/"demand"
        self.out=dd/"matching"; self.out.mkdir(parents=True, exist_ok=True)
        if not (self.sup/"profile-structured.json").exists() or not (self.dem/"1_jd_database.json").exists(): sys.exit("Missing inputs")
        self.prof=json.loads((self.sup/"profile-structured.json").read_text())
        self.jds=json.loads((self.dem/"1_jd_database.json").read_text()).get('roles',[])

    def kw(self, txt): return {x for x in re.findall(r'\b[a-z]{2,50}\b', (txt or "").lower()) if x not in {'and','the','for','with','this','that','from','have','are','was','can','will','not','but'}} 

    def run(self):
        print("🚀 Matching...")
        p_txt = " ".join([str(v) for k,v in self.prof.items() if isinstance(v,str)] + [x['title']+" "+x['description'] for x in self.prof['experiences']] + [x['degree'] for x in self.prof['education']])
        p_toks = self.kw(p_txt); res=[]
        
        for jd in self.jds:
            j_toks = self.kw(jd.get('raw_text') or jd.get('content',''))
            ov = p_toks & j_toks; sc = round(len(ov)/len(j_toks)*100,1) if j_toks else 0
            res.append({"id":jd.get('id'),"filename":jd.get('id'),"score":sc,"missing":sorted(list(j_toks-p_toks)),"overlap":sorted(list(ov))})
            print(f"  • {jd.get('id')}: {sc}% Match")
        
        (self.out/"11_gap_analysis.json").write_text(json.dumps(res, indent=2))
        rpt = "# Gap Analysis\n\n"+"\n\n".join([f"## {r['filename']} ({r['score']}%)\n### Missing\n{', '.join(r['missing'][:50])}" for r in res])
        (self.out/"11_gap_analysis_report.md").write_text(rpt)
        print(f"✅ Saved to {self.out}")

if __name__ == "__main__": Matcher().run()
