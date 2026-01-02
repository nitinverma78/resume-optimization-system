#!/usr/bin/env python3
"""
Step 9: Build Master Knowledge Base (Supply Side)

Consolidates raw resume content into a rich, queryable 'Master DB'.
Features:
1. Canonicalizes Company Names (Amazon Inc -> Amazon).
2. Deduplicates bullets using fuzzy matching (keeping best version).
3. Applies a comprehensive Rich Taxonomy of tags (Leadership, AI, Business).
4. Extracts Metrics for impact scoring.
"""

import json, re, difflib
from pathlib import Path
from collections import defaultdict
from typing import List, Dict, Set, Any

# --- RICH TAXONOMY ---
TAG_TAXONOMY = {
    "Leadership": [
        "led", "managed", "hired", "mentored", "strategy", "vision", "roadmap", "stakeholder",
        "c-suite", "board", "budget", "transformation", "persuaded", "negotiated", "change management"
    ],
    "AI_ML": [
        "ai", "ml", "machine learning", "genai", "generative ai", "llm", "nlp", "computer vision",
        "pytorch", "tensorflow", "model", "inference", "training", "rag", "agentic", "algorithm"
    ],
    "Tech_Cloud": [
        "architecture", "cloud", "aws", "gcp", "azure", "distributed systems", "microservices",
        "api", "platform", "engineering", "devops", "kubernetes", "docker", "scalability", "latency"
    ],
    "Business_Impact": [
        "revenue", "sales", "cost", "savings", "profit", "roi", "growth", "conversion", "budget",
        "p&l", "market share", "efficiency", "productivity"
    ],
    "Domain_Specific": [
        "supply chain", "e-commerce", "healthcare", "fintech", "retail", "logistics", "fulfillment",
        "inventory", "pricing", "personalization", "search", "recommendation"
    ]
}

def normalize_text(text: str) -> str:
    """Normalize text for fuzzy comparison."""
    return re.sub(r'\W+', ' ', text.lower()).strip()

def get_tags(text: str) -> List[str]:
    """Apply taxonomy tags to text."""
    tags = set()
    text_lower = text.lower()
    
    for category, keywords in TAG_TAXONOMY.items():
        for keyword in keywords:
            # Word boundary check is safer
            if re.search(r'\b' + re.escape(keyword) + r'\b', text_lower):
                tags.add(category) # Add the Category (High Level)
                tags.add(keyword.title()) # Add the specific keyword
                
    # Metric Check
    if re.search(r'(\$\d|\d%|\d\+)', text):
        tags.add("Quantifiable_Impact")
        
    return list(tags)

def canonicalize_company(name: str) -> str:
    """Map company variations to a canonical name."""
    name_clean = name.lower().replace("inc", "").replace("technologies", "").replace(".com", "").strip()
    
    MAPPING = {
        "amazon": "Amazon",
        "staples": "Staples",
        "a": "Amazon", # Heuristic if parser missed it
        "fico": "FICO",
        "fair isaac": "FICO",
        "the aspen group": "Aspen Dental",
        "tag": "Aspen Dental",
        "manifold": "Manifold Systems",
        "zulily": "Zulily"
    }
    
    for key, canonical in MAPPING.items():
        if key in name_clean:
            return canonical
            
    return name.strip()

def merge_bullets(bullet_list: List[Dict]) -> List[Dict]:
    """
    Deduplicate similar bullets.
    Input: List of {'text': '...', 'source': 'file1'}
    Output: List of unique bullets with {'sources': ['file1', 'file2']}
    """
    unique_bullets = []
    
    for new_b in bullet_list:
        is_duplicate = False
        new_text_norm = normalize_text(new_b['text'])
        
        for existing_b in unique_bullets:
            # Similarity check
            ratio = difflib.SequenceMatcher(None, new_text_norm, normalize_text(existing_b['text'])).ratio()
            if ratio > 0.85: # 85% similar provided it's long enough
                is_duplicate = True
                existing_b['sources'].append(new_b['source'])
                # Keep the longer/richer version as the 'text'
                if len(new_b['text']) > len(existing_b['text']):
                    existing_b['text'] = new_b['text']
                break
        
        if not is_duplicate:
            unique_bullets.append({
                'text': new_b['text'],
                'sources': [new_b['source']],
                'tags': get_tags(new_b['text'])
            })
            
    return unique_bullets

def main(
    input_file: Path = Path(__file__).parent.parent / "data" / "supply" / "4_raw_extracted_content.json",
    output_file: Path = Path(__file__).parent.parent / "data" / "supply" / "5_master_knowledge_base.json"
):
    """Main build loop."""
    if not input_file.exists():
        print(f"Error: {input_file} not found. Run Step 8 first.")
        return

    print("Building Master Knowledge Base...")
    with open(input_file, 'r') as f:
        raw_db = json.load(f)
        
    master_db = {
        "meta": {"source_files_count": len(raw_db)},
        "companies": defaultdict(lambda: {"roles": set(), "bullets": []})
    }
    
    # 1. First Pass: Aggregate everything by Company
    temp_company_buckets = defaultdict(list)
    
    for entry in raw_db:
        source = entry.get('source_file')
        
        # Process Recent Experience
        if 'experience' in entry and 'recent' in entry['experience']:
            for block in entry['experience']['recent']:
                company = canonicalize_company(block['company'])
                role = block.get('role', 'Unknown')
                
                master_db['companies'][company]['roles'].add(role)
                
                # Add bullets to temp bucket
                for b in block.get('bullets', []):
                    temp_company_buckets[company].append({'text': b['text'], 'source': source})
                    
        # Process Earlier Experience
        if 'experience' in entry and 'earlier' in entry['experience']:
             for block in entry['experience']['earlier']:
                company = canonicalize_company(block['company'])
                master_db['companies'][company]['roles'].add(block.get('role', 'Unknown'))
                for b in block.get('bullets', []):
                    temp_company_buckets[company].append({'text': b['text'], 'source': source})

    # 2. Second Pass: Deduplicate & Tag
    print(f"  Consolidating {len(temp_company_buckets)} unique companies...")
    
    final_companies = {}
    for co_name, raw_bullets in temp_company_buckets.items():
        unique = merge_bullets(raw_bullets)
        final_companies[co_name] = {
            "name": co_name,
            "roles": list(master_db['companies'][co_name]['roles']),
            "bullet_pool": unique,
            "bullet_count": len(unique)
        }
        print(f"    - {co_name}: {len(raw_bullets)} raw -> {len(unique)} unique bullets")
        
    master_db['companies'] = final_companies
    
    # Save
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(master_db, f, indent=2, ensure_ascii=False)
        
    print(f"\n✓ Knowledge Base built: {output_file}")

if __name__ == "__main__":
    main()
