#!/usr/bin/env python3
"""
Clean and normalize job description text in the JD database.

This script removes:
- Page headers/footers (e.g., "Page 1 of 4")
- Duplicate section headers
- Special characters and junk text
- Error pages and LinkedIn UI boilerplate
- Excessive whitespace and formatting artifacts

Usage:
    python -m scripts.11_clean_jd_text
"""

import json
import re
from pathlib import Path
from typing import Dict, List


def get_data_dir() -> Path:
    """Get the data directory from environment or default."""
    # Use project data directory
    return Path(__file__).parent.parent / "data"


def clean_text_line(line: str) -> str:
    """Clean a single line of text."""
    # Remove excessive whitespace
    line = ' '.join(line.split())
    
    # Replace checkmarks with bullets
    line = line.replace('✓', '•').replace('✔', '•')
    
    # Remove emojis (all Unicode emoji ranges)
    emoji_pattern = re.compile(
        "["
        "\U0001F600-\U0001F64F"  # emoticons
        "\U0001F300-\U0001F5FF"  # symbols & pictographs
        "\U0001F680-\U0001F6FF"  # transport & map symbols
        "\U0001F1E0-\U0001F1FF"  # flags (iOS)
        "\U00002702-\U000027B0"
        "\U000024C2-\U0001F251"
        "]+", 
        flags=re.UNICODE
    )
    line = emoji_pattern.sub('', line)
    
    # Remove common junk patterns
    line = re.sub(r'^[•\-]\s*$', '', line)  # Empty bullets
    line = re.sub(r'\s+', ' ', line)  # Multiple spaces
    
    return line.strip()


def is_page_header(line: str) -> bool:
    """Check if line is a page header/footer."""
    patterns = [
        r'^Page \d+ of \d+$',
        r'^Page \d+$',
        r'^\d+/\d+$',
    ]
    return any(re.match(p, line.strip()) for p in patterns)


def is_duplicate_title(line: str, title: str) -> bool:
    """Check if line is a duplicate of the job title."""
    if not title:
        return False
    # Normalize for comparison
    clean_line = re.sub(r'[^\w\s]', '', line.lower())
    clean_title = re.sub(r'[^\w\s]', '', title.lower())
    return clean_line == clean_title


def is_linkedin_boilerplate(line: str) -> bool:
    """Check if line is LinkedIn UI boilerplate."""
    boilerplate_patterns = [
        'skip to main content',
        'sign in',
        'sign up',
        'join now',
        'join linkedin',
        'already on linkedin',
        'new to linkedin',
        'user agreement',
        'privacy policy',
        'cookie policy',
        'forgot password',
        'email or phone',
        'password',
        'show',
        'apply',
        'save',
        'report this job',
        'use ai to assess',
        'tailor my resume',
        'am i a good fit',
        'get ai-powered',
        'see who .* has hired',
        'applicants',
    ]
    
    line_lower = line.lower().strip()
    return any(re.search(pattern, line_lower) for pattern in boilerplate_patterns)


def is_boilerplate_line(line: str) -> bool:
    """Check if line is boilerplate/junk content."""
    if not line:
        return False
    
    line_lower = line.lower().strip()
    
    # Contact information patterns
    contact_patterns = [
        r'^\w+@\w+\.\w+',  # Email
        r'^\d{3}[-\.\s]?\d{3}[-\.\s]?\d{4}',  # Phone
        r'^[om]:\s*\d{3}',  # o: or m: phone prefix
        'qualified candidates should contact',
        'contact information',
        'heller search',
        'client partner',
        'director of client delivery',
    ]
    
    if any(re.search(p, line_lower) for p in contact_patterns):
        return True
    
    # Boilerplate section headers
    boilerplate = [
        'what makes this opportunity compelling',
        'the successful candidate will enjoy',
        'interview process',
        'background and reference check',
        'offer, acceptance and start',
        'or',  # Standalone "Or"
    ]
    
    if line_lower in boilerplate:
        return True
    
    # Very short lines that are likely junk
    if len(line.strip()) <= 2 and not line.strip().isdigit():
        return True
    
    # LinkedIn boilerplate
    if is_linkedin_boilerplate(line):
        return True
    
    return False


def merge_fragmented_lines(lines: List[str]) -> List[str]:
    """Intelligently merge fragmented lines."""
    if not lines:
        return []
    
    merged = []
    buffer = ""
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
        
        # If line is just a bullet, hold it
        if line in ['•', '-', '✓', '✔']:
            if buffer:
                merged.append(buffer)
            buffer = "• "
            continue
        
        # If we have a buffered bullet and this line starts with lowercase or doesn't start a sentence
        if buffer == "• " or (buffer and not line[0].isupper() and not buffer.endswith('.')):
            buffer += line
        else:
            if buffer:
                merged.append(buffer)
            buffer = line
    
    if buffer:
        merged.append(buffer)
    
    return merged


def is_error_page_content(sections: Dict) -> bool:
    """Check if sections contain error page content rather than job description."""
    if not sections:
        return False
    
    # Flatten all section content
    all_text = []
    for section_lines in sections.values():
        if isinstance(section_lines, list):
            all_text.extend(section_lines)
    
    if not all_text:
        return False
    
    # Count various indicators
    total_lines = len(all_text)
    linkedin_ui_count = sum(1 for line in all_text if is_linkedin_boilerplate(line))
    non_latin_count = sum(1 for line in all_text if has_high_non_latin(line))
    
    # If >40% is LinkedIn UI boilerplate, it's a failed scrape
    if total_lines > 0 and (linkedin_ui_count / total_lines) > 0.4:
        return True
    
    # If >50% is non-Latin (error pages in other languages)
    if total_lines > 0 and (non_latin_count / total_lines) > 0.5:
        return True
    
    # Check for common error indicators
    text_joined = ' '.join(all_text).lower()
    error_indicators = [
        'page not found',
        '404',
        'page isn\'t available',
        'help center',  # Usually part of error page footer
        'centro de ayuda',  # Spanish
        'centre d\'aide',  # French
        'hilfe-center',  # German
    ]
    
    # If multiple error indicators, likely error page
    error_count = sum(1 for indicator in error_indicators if indicator in text_joined)
    if error_count >= 2:
        return True
    
    return False


def has_high_non_latin(line: str) -> bool:
    """Check if line has high percentage of non-Latin characters."""
    if not line:
        return False
    
    # Count non-Latin characters (beyond Latin Extended)
    non_latin = sum(1 for c in line if ord(c) > 0x0590)
    total_chars = len([c for c in line if c.isalnum()])
    
    # If more than 30% non-Latin, likely non-English
    if total_chars > 0 and (non_latin / total_chars) > 0.3:
        return True
    
    return False


def clean_section_lines(lines: List[str], job_title: str = "") -> List[str]:
    """Clean a list of section lines."""
    if not lines:
        return []
    
    # First pass: clean individual lines
    cleaned = []
    for line in lines:
        cleaned_line = clean_text_line(line)
        
        # Skip empty lines
        if not cleaned_line:
            continue
        
        # Skip boilerplate/junk
        if is_boilerplate_line(cleaned_line):
            continue
        
        # Skip page headers/footers
        if is_page_header(cleaned_line):
            continue
        
        # Skip duplicate job titles
        if is_duplicate_title(cleaned_line, job_title):
            continue
        
        cleaned.append(cleaned_line)
    
    # Second pass: merge fragmented lines
    merged = merge_fragmented_lines(cleaned)
    
    # Third pass: remove duplicates while preserving order
    seen = set()
    final = []
    for line in merged:
        if line not in seen:
            seen.add(line)
            final.append(line)
    
    return final


def clean_jd_entry(entry: Dict) -> Dict:
    """Clean a single JD entry."""
    # Don't modify stub entries
    if entry.get('type') == 'batch_desc_stub':
        return entry
    
    job_title = entry.get('title', '')
    sections = entry.get('sections', {})
    
    # Check if entire entry is an error page
    if is_error_page_content(sections):
        # Clear sections and mark as error
        entry['sections'] = {}
        entry['scrape_error'] = True
        entry['error_reason'] = 'Error page or LinkedIn UI boilerplate detected'
        return entry
    
    # Clean each section normally
    cleaned_sections = {}
    for section_name, section_lines in sections.items():
        if isinstance(section_lines, list):
            # Check if this specific section is garbage
            if is_garbage_section(section_lines):
                # Skip this section entirely
                continue
            
            cleaned_lines = clean_section_lines(section_lines, job_title)
            
            # Only keep section if it has meaningful content after cleaning
            if cleaned_lines:
                cleaned_sections[section_name] = cleaned_lines
        else:
            cleaned_sections[section_name] = section_lines
    
    # Update entry
    entry['sections'] = cleaned_sections
    
    # If no sections remain after cleaning, mark as error
    if not cleaned_sections:
        entry['scrape_error'] = True
        entry['error_reason'] = 'No meaningful content after cleaning'
    else:
        # Remove error flag if it exists (this is good content)
        if 'scrape_error' in entry:
            del entry['scrape_error']
        if 'error_reason' in entry:
            del entry['error_reason']
    
    return entry


def is_garbage_section(lines: List[str]) -> bool:
    """Check if an individual section is garbage (not job content)."""
    if not lines or len(lines) < 5:
        return False
    
    # Count garbage lines
    garbage_count = sum(1 for line in lines if is_linkedin_boilerplate(line) or is_boilerplate_line(line))
    
    # If >40% of section is garbage, discard it
    if len(lines) > 0 and (garbage_count / len(lines)) > 0.4:
        return True
    
    return False


def main():
    """Main entry point."""
    dd = get_data_dir()
    db_path = dd / "demand" / "1_jd_database.json"
    backup_path = dd / "demand" / "1_jd_database.backup.json"
    
    print(f"📚 Loading JD database from: {db_path}")
    
    # Load database
    with open(db_path, 'r') as f:
        data = json.load(f)
    
    roles = data.get('roles', [])
    print(f"   Found {len(roles)} roles")
    
    # Backup original
    print(f"💾 Creating backup at: {backup_path}")
    with open(backup_path, 'w') as f:
        json.dump(data, f, indent=2)
    
    # Clean each entry
    print("🧹 Cleaning job descriptions...")
    cleaned_roles = []
    error_count = 0
    cleaned_count = 0
    
    for i, role in enumerate(roles):
        cleaned_role = clean_jd_entry(role)
        cleaned_roles.append(cleaned_role)
        
        # Track stats
        if cleaned_role.get('scrape_error'):
            error_count += 1
        elif cleaned_role.get('sections'):
            cleaned_count += 1
        
        if (i + 1) % 100 == 0:
            print(f"   Processed {i + 1}/{len(roles)} roles...")
    
    # Save cleaned database
    data['roles'] = cleaned_roles
    
    print(f"💾 Saving cleaned database to: {db_path}")
    with open(db_path, 'w') as f:
        json.dump(data, f, indent=2)
    
    print("✅ Cleaning complete!")
    print(f"   Original saved to: {backup_path}")
    print(f"   Cleaned saved to: {db_path}")
    print(f"\n📊 Summary:")
    print(f"   • Total roles: {len(roles)}")
    print(f"   • Successfully cleaned: {cleaned_count}")
    print(f"   • Error pages detected: {error_count}")
    print(f"   • Stub entries (no URL): {len(roles) - cleaned_count - error_count}")
    
    if error_count > 0:
        print(f"\n⚠️  {error_count} entries flagged as error pages.")
        print(f"   These have 'scrape_error': true and should be re-scraped.")


if __name__ == "__main__":
    main()
