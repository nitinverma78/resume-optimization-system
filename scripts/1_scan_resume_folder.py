#!/usr/bin/env python3
"""Phase 1.1: File Scanner - Scans folder and creates complete file inventory."""
import json,os
from pathlib import Path
from datetime import datetime
from typing import List,Dict,NewType
from pydantic import BaseModel

# Type aliases
FilePath = NewType('FilePath', Path)
FileList = List['FileInfo']

class FileInfo(BaseModel):
    """File metadata model."""
    class Config: frozen = True
    path: str
    name: str
    ext: str           # extension
    sz: int            # size_bytes
    modified: str      # modified_date
    is_dir: bool       # is_directory

class FileInventory(BaseModel):
    """Complete file inventory model."""
    class Config: frozen = True
    scan_date: str
    src_folder: str    # source_folder
    n_files: int       # total_files
    n_dirs: int        # total_directories
    files: FileList

def scan_folder(
    folder: Path,        # Path to folder to scan
    recursive: bool=True # Whether to scan subdirectories
) -> FileList:           # List of FileInfo objects
    """Scan folder and gather file information."""
    files = []
    
    def add_file(fp: Path, is_dir: bool=False):
        try:
            st = fp.stat()
            files.append(FileInfo(
                path=str(fp), name=fp.name,
                ext=fp.suffix.lower() if not is_dir else "",
                sz=st.st_size if not is_dir else 0,
                modified=datetime.fromtimestamp(st.st_mtime).isoformat(),
                is_dir=is_dir
            ))
        except (OSError, PermissionError) as e:
            print(f"Warning: Could not access {fp}: {e}")
    
    def skip(name): return name.startswith('.') or name.startswith('~$')
    
    if recursive:
        for root, dirs, fnames in os.walk(folder):
            for fn in fnames:
                if skip(fn): continue
                add_file(Path(root)/fn, is_dir=False)
            for dn in dirs:
                if skip(dn): continue
                add_file(Path(root)/dn, is_dir=True)
    else:
        for item in folder.iterdir():
            if skip(item.name): continue
            add_file(item, is_dir=item.is_dir())
    
    return files

def main(
    folder: Path = Path.home()/"Downloads"/"MyResumes",  # Folder to scan
    out: Path = Path(__file__).parent.parent/"data"/"supply"/"1_file_inventory.json"  # Output JSON
):
    """Main execution."""
    # Allow env vars to override defaults
    folder = Path(os.getenv('RESUME_FOLDER', str(folder)))
    out    = Path(os.getenv('OUTPUT_FILE', str(out)))
    
    if not folder.exists():
        print(f"Error: Folder not found: {folder}")
        print("Please provide a valid folder path.")
        return
    
    print(f"Scanning folder: {folder}")
    print("This may take a moment for large folders...\n")
    
    files = scan_folder(folder, recursive=True)
    
    # Separate files and directories
    file_list = [f for f in files if not f.is_dir]
    dir_list  = [f for f in files if f.is_dir]
    
    # Create inventory
    inv = FileInventory(
        scan_date=datetime.now().isoformat(),
        src_folder=str(folder),
        n_files=len(file_list), n_dirs=len(dir_list),
        files=files
    )
    
    # Save to JSON
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, 'w', encoding='utf-8') as f:
        json.dump(inv.model_dump(), f, indent=2, ensure_ascii=False)
    
    print(f"✓ Scan complete!")
    print(f"✓ Found {len(file_list)} files in {len(dir_list)} directories")
    print(f"✓ Saved to: {out}\n")
    
    # File type breakdown
    exts = {}
    for f in file_list:
        e = f.ext if f.ext else "(no extension)"
        exts[e] = exts.get(e, 0) + 1
    
    print("File type breakdown:")
    for e, cnt in sorted(exts.items(), key=lambda x: x[1], reverse=True):
        print(f"  {e}: {cnt} files")
    
    # Size summary
    total_sz = sum(f.sz for f in file_list)
    print(f"\nTotal size: {total_sz / (1024*1024):.2f} MB")

if __name__ == "__main__": main()
