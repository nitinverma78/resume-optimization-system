#!/usr/bin/env python3
"""
Step 7: Ingest Resume Content (The "Knowledge Base")

Reads all classified user resumes and cover letters.
Extracts bullet points and text blocks to build a database of 
"phrasing patterns" and "accomplishments".

Output: data/resume_content_db.json
"""

import json, os, re
import pymupdf
from pathlib import Path
from typing import List, Dict

def extract_bullets_from_text(text: str) -> List[str]:
    """Extract lines that look like bullet points."""
    bullets = []
    lines = text.split('\n')
    
    # Common bullet characters
    bullet_indicators = ['•', '·', '-', '*', '➢', '▪', '‣']
    
    for line in lines:
        line = line.strip()
        if not line: continue
        
        # Check if line starts with bullet
        is_bullet = any(line.startswith(char) for char in bullet_indicators)
        
        # Also capture numbered lists like "1. Achievement..."
        is_numbered = re.match(r'^\d+\.', line)
        
        if (is_bullet or is_numbered) and len(line) > 20:
            # Clean up the bullet char
            clean_line = re.sub(r'^[\•\·\-\*\➢\▪\‣\d\.]+\s*', '', line).strip()
            bullets.append(clean_line)
            
    return bullets

def extract_file_content(file_path: Path) -> Dict:
    """Extract text and bullets from a single file."""
    try:
        doc = pymupdf.open(file_path)
        full_text = ""
        for page in doc:
            full_text += page.get_text()
        doc.close()
        
        bullets = extract_bullets_from_text(full_text)
        
        return {
            "text": full_text,
            "bullets_count": len(bullets),
            "bullets": bullets
        }
    except Exception as e:
        print(f"  Error reading {file_path.name}: {e}")
        return None

def main(
    classified_file: Path = Path(__file__).parent.parent / "data" / "classified_files.json",
    output_file: Path = Path(__file__).parent.parent / "data" / "resume_content_db.json"
):
    """Main ingestion loop."""
    # Env overrides
    classified_file = Path(os.getenv('CLASSIFIED_FILE', str(classified_file)))
    
    if not classified_file.exists():
        print(f"Error: {classified_file} not found. Run Step 2 first.")
        return

    with open(classified_file, 'r') as f:
        file_inventory = json.load(f)
        
    print("Ingesting content from historical resumes...")
    
    knowledge_base = []
    
    # We only care about user's own documents
    categories_to_scan = ['user_resumes', 'user_combined', 'user_cover_letters']
    
    total_files = 0
    total_bullets = 0
    
    for category in categories_to_scan:
        if category not in file_inventory: continue
        
        files_list = file_inventory[category]
        print(f"\nScanning {category} ({len(files_list)} files)...")
        
        for file_info in files_list:
            path = Path(file_info['path'])
            if not path.exists(): continue
            
            content_data = extract_file_content(path)
            
            if content_data:
                knowledge_base.append({
                    "source_file": file_info['name'],
                    "category": category,
                    "extracted_bullets": content_data['bullets'],
                    # We store full text but might skip writing it to JSON if it's too huge
                    # "full_text": content_data['text'] 
                })
                total_files += 1
                total_bullets += content_data['bullets_count']
                
                # Progress dot
                print(".", end="", flush=True)

    print(f"\n\n✓ Ingestion complete!")
    print(f"  Files processed: {total_files}")
    print(f"  Total bullet points extracted: {total_bullets}")
    
    # Save DB
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(knowledge_base, f, indent=2, ensure_ascii=False)
        
    print(f"  Saved to: {output_file}")

if __name__ == "__main__":
    main()
