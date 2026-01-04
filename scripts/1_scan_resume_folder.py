#!/usr/bin/env python3
"""[Supply Discovery] Step 1: Scan folder and create complete file inventory."""
import json,os,sys
from pathlib import Path
from datetime import datetime
from typing import List
from pydantic import BaseModel, ConfigDict

class FileInfo(BaseModel):
    model_config = ConfigDict(frozen=True)
    path: str; name: str; ext: str; sz: int; modified: str; is_dir: bool

class FileInventory(BaseModel):
    model_config = ConfigDict(frozen=True)
    scan_date: str; src_folder: str; n_files: int; n_dirs: int; files: List[FileInfo]

def get_data_dir(): return Path(os.getenv('DATA_DIR')) if os.getenv('DATA_DIR') else Path(__file__).parent.parent/"data"

# Manual .env loading
env_path = Path(__file__).parent.parent / ".env"
if env_path.exists():
    for l in env_path.read_text().splitlines():
        if '=' in l and not l.strip().startswith('#'):
            k, v = l.strip().split('=', 1)
            if not os.getenv(k): os.environ[k] = v.strip('"').strip("'")

def scan_folder(folder: Path) -> List[FileInfo]:
    files = []
    def add(fp, is_dir=False):
        try:
            st = fp.stat()
            files.append(FileInfo(path=str(fp), name=fp.name, ext=fp.suffix.lower() if not is_dir else "",
                                  sz=st.st_size if not is_dir else 0, modified=datetime.fromtimestamp(st.st_mtime).isoformat(), is_dir=is_dir))
        except Exception as e: print(f"Warning: {fp}: {e}")
    
    for root, dirs, fnames in os.walk(folder):
        [add(Path(root)/n, False) for n in fnames if not n.startswith(('.', '~$'))]
        [add(Path(root)/n, True) for n in dirs if not n.startswith(('.', '~$'))]
    return files

def main():
    out = get_data_dir()/"supply"/"1_file_inventory.json"
    if not (fld := os.getenv('RESUME_FOLDER')): print("Error: RESUME_FOLDER not set."); sys.exit(1)
    folder = Path(os.path.expanduser(fld))
    if not folder.exists(): print(f"Error: Not found: {folder}"); sys.exit(1)
    
    print(f"Scanning: {folder}...")
    files = scan_folder(folder)
    f_list, d_list = [f for f in files if not f.is_dir], [f for f in files if f.is_dir]

    inv = FileInventory(scan_date=datetime.now().isoformat(), src_folder=str(folder), n_files=len(f_list), n_dirs=len(d_list), files=files)
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, 'w', encoding='utf-8') as f: json.dump(inv.model_dump(), f, indent=2, ensure_ascii=False)
    
    print(f"✓ Found {len(f_list)} files, {len(d_list)} dirs -> {out}")
    print(f"Total size: {sum(f.sz for f in f_list)/(1024*1024):.2f} MB")

if __name__ == "__main__": main()
