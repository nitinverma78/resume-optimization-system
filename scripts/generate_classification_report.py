#!/usr/bin/env python3
"""
Generate a readable classification report for user review.
"""

import json
from pathlib import Path
import os


def generate_classification_report(classified_path: Path, output_md: Path):
    """Generate a markdown report of classifications."""
    
    with open(classified_path, 'r', encoding='utf-8') as f:
        classified = json.load(f)
    
    report = []
    report.append("# File Classification Report\n")
    report.append(f"Total files analyzed: {sum(len(v) for v in classified.values())}\n")
    report.append("---\n\n")
    
    # User Resumes
    report.append(f"## User Resumes ({len(classified['user_resumes'])} files)\n")
    report.append("*Files identified as your resume variations*\n\n")
    for idx, file in enumerate(sorted(classified['user_resumes'], key=lambda x: x['name']), 1):
        report.append(f"{idx}. `{file['name']}`\n")
    report.append("\n---\n\n")
    
    # User Cover Letters
    report.append(f"## User Cover Letters ({len(classified['user_cover_letters'])} files)\n")
    report.append("*Files identified as your cover letters (cover letter only)*\n\n")
    for idx, file in enumerate(sorted(classified['user_cover_letters'], key=lambda x: x['name']), 1):
        report.append(f"{idx}. `{file['name']}`\n")
    report.append("\n---\n\n")
    
    # User Combined (Resume + Cover Letter)
    report.append(f"## User Combined Documents ({len(classified['user_combined'])} files)\n")
    report.append("*Files containing BOTH resume and cover letter in one document*\n\n")
    for idx, file in enumerate(sorted(classified['user_combined'], key=lambda x: x['name']), 1):
        report.append(f"{idx}. `{file['name']}`\n")
    report.append("\n---\n\n")
    
    # Other Resumes
    report.append(f"## Other Resumes ({len(classified['other_resumes'])} files)\n")
    report.append("*Resumes that don't appear to be yours*\n\n")
    for idx, file in enumerate(sorted(classified['other_resumes'], key=lambda x: x['name']), 1):
        report.append(f"{idx}. `{file['name']}`\n")
    report.append("\n---\n\n")
    
    # Tracking Files
    report.append(f"## Tracking Files ({len(classified['tracking_files'])} files)\n")
    report.append("*Spreadsheets for tracking applications, contacts, companies*\n\n")
    for idx, file in enumerate(sorted(classified['tracking_files'], key=lambda x: x['name']), 1):
        report.append(f"{idx}. `{file['name']}`\n")
    report.append("\n---\n\n")
    
    # Other Files
    report.append(f"## Other Files ({len(classified['other'])} files)\n")
    report.append("*Job descriptions, templates, presentations, CSV exports, and miscellaneous*\n\n")
    for idx, file in enumerate(sorted(classified['other'], key=lambda x: x['name']), 1):
        ext = file['extension'] if file['extension'] else '(no ext)'
        report.append(f"{idx}. `{file['name']}` {ext}\n")
    
    # Write report
    with open(output_md, 'w', encoding='utf-8') as f:
        f.writelines(report)


def main(
    classified_file: Path = Path(__file__).parent.parent / "data" / "classified_files.json",  # Input classified
    output_md: Path = Path(__file__).parent.parent / "data" / "classification_report.md"  # Output report
):
    """Main execution."""
    # Allow environment variables to override defaults
    classified_file = Path(os.getenv('CLASSIFIED_FILE', str(classified_file)))
    output_md = Path(os.getenv('REPORT_FILE', str(output_md)))
    
    if not classified_file.exists():
        print(f"Error: Classified files not found at {classified_file}")
        print("Please run 2_classify_files.py first.")
        return
    
    print("Generating classification report...")
    generate_classification_report(classified_file, output_md)
    
    print(f"✓ Report generated: {output_md}")
    print(f"\nYou can review the classifications in: {output_md}")


if __name__ == "__main__":
    main()
