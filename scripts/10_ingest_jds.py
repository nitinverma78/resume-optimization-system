#!/usr/bin/env python3
"""
Step 10: Ingest Job Descriptions (Demand Side)

Parses JDs from `data/job_descriptions/` to build `data/jd_content_db.json`.
Extracts:
- Role Title
- Company
- Rubric (Heuristic Weights)
- Keywords/Tags

This defines the "Vocabulary" for the Resume Optimization.
"""

import json, os, re
import pymupdf
from pathlib import Path
from typing import List, Dict, Any

def extract_text(file_path: Path) -> str:
    """Read text from supported file types."""
    text = ""
    try:
        if file_path.suffix.lower() == '.pdf':
            doc = pymupdf.open(file_path)
            for page in doc:
                text += page.get_text() + "\n"
        elif file_path.suffix.lower() in ['.txt', '.md']:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                text = f.read()
        elif file_path.suffix.lower() in ['.docx', '.doc']:
            # Use macOS textutil to convert to txt
            try:
                import subprocess
                cmd = ['textutil', '-convert', 'txt', '-stdout', str(file_path)]
                result = subprocess.run(cmd, capture_output=True, text=True)
                if result.returncode == 0:
                    text = result.stdout
                else:
                    print(f"  [Error] textutil failed for {file_path.name}")
            except Exception as e:
                 print(f"  [Error] textutil execution failed: {e}")
    except Exception as e:
        print(f"  Error reading {file_path.name}: {e}")
    return text

def parse_jd(text: str, filename: str) -> Dict[str, Any]:
    """
    Parse JD text to extract metadata and rubric.
    """
    # 1. Basic Metadata
    # Attempt to find "Company" and "Title" (Very heuristic)
    lines = [l.strip() for l in text.split('\n') if l.strip()]
    title = lines[0] if lines else "Unknown Role"
    company = "Unknown Company"
    
    # 2. Extract Keywords (Rubric Signals)
    # We look for section headers to weight content
    sections = {
        'Responsibilities': [],
        'Requirements': [],
        'Summary': []
    }
    
    current_section = 'Summary'
    
    for line in lines:
        if re.search(r'(?i)(responsibilit|duties|what you will do)', line):
            current_section = 'Responsibilities'
        elif re.search(r'(?i)(requirement|qualification|skills|who you are)', line):
            current_section = 'Requirements'
        else:
            sections[current_section].append(line)
            
    # 3. Rubric Construction (Simplified)
    # We simulate a rubric by extracting Nouns/Keywords from Requirements
    # In a real agentic system, an LLM would do this. Here we use regex for "Skills".
    
    text_requirements = " ".join(sections['Requirements'])
    
    # Simple extraction of capitalized phrases or known outcomes
    # For now, we will just store the Raw Text + Sections so the Matching Engine 
    # (Step 11) can do the heavy lifting.
    
    return {
        "id": filename,
        "title": title,
        "company": company,
        "raw_text": text,
        "structured_sections": sections
    }

def main(
    input_dir: Path = Path(__file__).parent.parent / "data" / "demand" / "raw_jds",
    output_db: Path = Path(__file__).parent.parent / "data" / "demand" / "1_jd_database.json"
):
    """Main ingestion loop."""
    if not input_dir.exists():
        print(f"Error: {input_dir} not found.")
        return

    print("Ingesting Job Descriptions...")
    
    db = []
    files = list(input_dir.glob("*.*"))
    
    for file_path in files:
        if file_path.name.startswith('.'): continue
        
        print(f"  Processing {file_path.name}...")
        text = extract_text(file_path)
        
        if text and len(text) > 100:
            parsed = parse_jd(text, file_path.name)
            db.append(parsed)
        else:
            print(f"    Skipping (Empty or unreadable)")
            
    if not db:
        print("No valid JDs found. Please add files to data/job_descriptions/")
        return
        
    # Save DB
    with open(output_db, 'w', encoding='utf-8') as f:
        json.dump({"roles": db}, f, indent=2, ensure_ascii=False)
        
    print(f"\n✓ Ingested {len(db)} JDs.")
    print(f"  Database saved to: {output_db}")

if __name__ == "__main__":
    main()
