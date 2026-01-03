#!/usr/bin/env python3
"""[Supply Discovery] Step 2: Content-based file classifier."""
import json,re,os,sys
from pathlib import Path
from pydantic import BaseModel, ConfigDict
from scripts.lib_extract import extract

class ClassifiedFiles(BaseModel):
    model_config = ConfigDict(frozen=True)
    user_resumes: list=[]; user_cls: list=[]; user_combined: list=[]; other_resumes: list=[]
    presentations: list=[]; jds: list=[]; recruiters: list=[]; companies: list=[]; tracking: list=[]; other: list=[]

KEYS = list(ClassifiedFiles.model_fields.keys())
FOLDERS = {'Presentations':'presentation', 'Roles':'jd', 'Jobs':'jd', 'Recruiters':'recruiter', 'CV samples':'other_resume', 'OthersInfo':'other_resume'}

def get_data_dir(): return Path(os.getenv('DATA_DIR') or Path(__file__).parent.parent/"data")

def get_cat(fp, name, email):
    fn, ext, txt = fp.name.lower(), fp.suffix.lower(), None
    def get_txt(): nonlocal txt; txt = extract(fp) if txt is None else txt; return txt

    for f,c in FOLDERS.items(): 
        if f in fp.parts: return c, f"In {f} folder"

    if 'basic_linkedindataexport' in str(fp).lower(): return 'other','LinkedIn export'
    if any(x in fn for x in ['work search','job search']): return 'jd','Job search log'
    if any(x in fn for x in ['companies','top10k','top50k','jobsearchresults']): return 'company','Company list'
    if ('exec' in fn and 'search' in fn) or 'recruiter' in fn: return 'recruiter','Recruiter info'
    if ext in ['.xlsx','.csv']: return 'other','Spreadsheet'
    if ext not in ['.pdf','.docx','.doc','.pptx','.txt']: return 'other',f'Unsupported {ext}'

    t = get_txt(); 
    if not t: return 'other','No text'

    jd_pats = [r'job description',r'responsibilities',r'requirements',r'qualifications',r'we are (?:looking|seeking)']
    if 'job description' in fn or 'jd' in fn or sum(bool(re.search(p,t)) for p in jd_pats)>=3: return 'jd','JD content/name'

    pres_names = ['enterpriseagenticai','hexagonphysicalai']
    if 'Presentations' in fp.parts or any(p in fn for p in pres_names): return 'presentation','Presentation'

    cfg = get_data_dir().parent/"config"/"classification_config.json"
    oth_names = json.loads(cfg.read_text()).get('other_peoples_names',[]) if cfg.exists() else []
    if any(re.search(n,t) for n in oth_names): return 'other_resume','Other person'

    u_name, u_email = (name or os.getenv('USER_NAME','')).lower(), (email or os.getenv('USER_EMAIL','')).lower()
    is_user = (u_name and (u_name.replace(' ','') in fn.replace(' ','') or u_name in t)) or (u_email and u_email in t)
    
    is_res = sum(bool(re.search(p,t)) for p in [r'experience',r'education',r'skills',r'professional summary'])>=3
    is_cl = sum(bool(re.search(p,t)) for p in [r'dear (?:hiring|recruiter)',r'sincerely',r'cover letter'])>=1

    if not is_user: return ('other_resume' if is_res else 'other'), "Not user doc"
    if is_cl and is_res: return ('user_cl' if len(t.split())<600 else 'user_combined'), "Combined/CL"
    if is_cl: return 'user_cl','Cover Letter'
    if is_res: return 'user_resume','Resume'
    return 'user_resume','Default User Doc'

def main():
    dd = get_data_dir()
    inv_p, out_p = dd/"supply"/"1_file_inventory.json", dd/"supply"/"2_file_inventory.json"
    if not inv_p.exists(): print("Run Step 1 first."); sys.exit(1)

    print("Classifying..."); data = json.loads(inv_p.read_text()); res = {k:[] for k in KEYS}
    
    for i,f in enumerate(data['files']):
        if i%20==0: print(f" {i}/{len(data['files'])}...", end='\r')
        if f.get('is_dir'): continue
        c, r = get_cat(Path(f['path']), None, None)
        f['classification_reason'] = r
        
        MAP = {'user_resume':'user_resumes', 'user_cl':'user_cls', 'user_combined':'user_combined', 'other_resume':'other_resumes', 'presentation':'presentations', 'jd':'jds', 'recruiter':'recruiters', 'company':'companies', 'trending':'tracking'}
        k = MAP.get(c, 'other')
        if k not in res: k = 'other'
        res[k].append(f)

    with open(out_p, 'w') as f: json.dump(res, f, indent=2, ensure_ascii=False)
    print(f"\n✓ Saved to {out_p}")
    print("\n".join(f"  {k}: {len(v)}" for k,v in res.items()))

if __name__ == "__main__": main()
