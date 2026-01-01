#!/usr/bin/env python3
"""
Phase 1.1: File Scanner
Scans a folder and creates a complete inventory of all files with metadata.
"""

import json, os
from pathlib import Path
from datetime import datetime
from typing import List, Dict
from pydantic import BaseModel


class FileInfo(BaseModel):
    """Model for file information."""
    path: str
    name: str
    extension: str
    size_bytes: int
    modified_date: str
    is_directory: bool


class FileInventory(BaseModel):
    """Model for complete file inventory."""
    scan_date: str
    source_folder: str
    total_files: int
    total_directories: int
    files: List[FileInfo]


def scan_folder(folder_path: Path, recursive: bool = True) -> List[FileInfo]:
    """
    Scan a folder and gather file information.
    
    Args:
        folder_path: Path to folder to scan
        recursive: Whether to scan subdirectories
        
    Returns:
        List of FileInfo objects
    """
    files = []
    
    if recursive:
        # Walk through all subdirectories
        for root, dirs, filenames in os.walk(folder_path):
            for filename in filenames:
                # Skip hidden files and system files
                if filename.startswith('.') or filename.startswith('~$'):
                    continue
                    
                file_path = Path(root) / filename
                try:
                    stat = file_path.stat()
                    files.append(FileInfo(
                        path=str(file_path), name=filename,
                        extension=file_path.suffix.lower(),
                        size_bytes=stat.st_size,
                        modified_date=datetime.fromtimestamp(stat.st_mtime).isoformat(),
                        is_directory=False
                    ))
                except (OSError, PermissionError) as e:
                    print(f"Warning: Could not access {file_path}: {e}")
                    
            # Also track directories
            for dirname in dirs:
                if dirname.startswith('.'):
                    continue
                dir_path = Path(root) / dirname
                try:
                    stat = dir_path.stat()
                    files.append(FileInfo(
                        path=str(dir_path),
                        name=dirname,
                        extension="",
                        size_bytes=0,
                        modified_date=datetime.fromtimestamp(stat.st_mtime).isoformat(),
                        is_directory=True
                    ))
                except (OSError, PermissionError) as e:
                    print(f"Warning: Could not access {dir_path}: {e}")
    else:
        # Only scan top level
        for item in folder_path.iterdir():
            if item.name.startswith('.') or item.name.startswith('~$'):
                continue
            try:
                stat = item.stat()
                files.append(FileInfo(
                    path=str(item),
                    name=item.name,
                    extension=item.suffix.lower() if item.is_file() else "",
                    size_bytes=stat.st_size if item.is_file() else 0,
                    modified_date=datetime.fromtimestamp(stat.st_mtime).isoformat(),
                    is_directory=item.is_dir()
                ))
            except (OSError, PermissionError) as e:
                print(f"Warning: Could not access {item}: {e}")
    
    return files


def main():
    """Main execution."""
    # Configuration
    RESUME_FOLDER = Path.home() / "Downloads" / "NitinResumes"
    OUTPUT_FILE = Path(__file__).parent.parent / "data" / "file_inventory.json"
    
    # Validate folder exists
    if not RESUME_FOLDER.exists():
        print(f"Error: Folder not found: {RESUME_FOLDER}")
        print("Please update RESUME_FOLDER path in the script.")
        return
    
    print(f"Scanning folder: {RESUME_FOLDER}")
    print("This may take a moment for large folders...\n")
    
    # Scan folder
    files = scan_folder(RESUME_FOLDER, recursive=True)
    
    # Separate files and directories
    file_list = [f for f in files if not f.is_directory]
    dir_list = [f for f in files if f.is_directory]
    
    # Create inventory
    inventory = FileInventory(
        scan_date=datetime.now().isoformat(),
        source_folder=str(RESUME_FOLDER),
        total_files=len(file_list), total_directories=len(dir_list),
        files=files
    )
    
    # Save to JSON
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(inventory.model_dump(), f, indent=2, ensure_ascii=False)
    
    # Print summary
    print(f"✓ Scan complete!")
    print(f"✓ Found {len(file_list)} files in {len(dir_list)} directories")
    print(f"✓ Saved to: {OUTPUT_FILE}\n")
    
    # Show file type breakdown
    extensions = {}
    for file in file_list:
        ext = file.extension if file.extension else "(no extension)"
        extensions[ext] = extensions.get(ext, 0) + 1
    
    print("File type breakdown:")
    for ext, count in sorted(extensions.items(), key=lambda x: x[1], reverse=True):
        print(f"  {ext}: {count} files")
    
    # Show size summary
    total_size = sum(f.size_bytes for f in file_list)
    print(f"\nTotal size: {total_size / (1024*1024):.2f} MB")


if __name__ == "__main__":
    main()
