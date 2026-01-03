"""Shared validation library for data isolation and privacy checks."""
import json,os,re
from pathlib import Path
from scripts.lib_extract import extract

def norm(t): return (t or "").lower().strip()

def scan_files(files, check_name, check_email, mode='contains'):
    """
    Scan files for presence/absence of PII.
    
    Args:
        files: List of Path objects to scan
        check_name: Name to check for (e.g., "Jane Doe")
        check_email: Email to check for (e.g., "jane.doe@example.com")
        mode: 'contains' (ensure PII exists) or 'absent' (ensure PII doesn't exist)
    
    Returns:
        (passed, violations) tuple
    """
    violations = []
    name_parts = norm(check_name).split()
    email_norm = norm(check_email)
    
    for fp in files:
        if not fp.exists(): continue
        
        # Fast path: Check filename
        fn_lower = fp.name.lower()
        has_name_in_fn = all(pt in fn_lower for pt in name_parts)
        has_email_in_fn = email_norm in fn_lower
        
        # Content check (skip unsupported formats)
        if fp.suffix.lower() not in ['.pdf','.txt','.md','.html','.json','.py','.sh','.yml','.yaml']:
            if mode == 'contains' and not has_name_in_fn:
                violations.append(f"{fp.name} (unsupported format, filename check failed)")
            continue
        
        try:
            content = extract(fp).lower() if fp.suffix.lower() in ['.pdf','.docx','.doc','.pptx'] else fp.read_text(errors='ignore').lower()
        except:
            continue
        
        has_name = all(pt in content for pt in name_parts)
        has_email = email_norm in content
        
        if mode == 'contains':
            # Data isolation: PII MUST be present
            if not (has_name or has_email or has_name_in_fn or has_email_in_fn):
                violations.append(f"{fp.name} (missing {check_name}/{check_email})")
        elif mode == 'absent':
            # Git privacy: PII MUST NOT be present
            if has_name or has_email or has_name_in_fn or has_email_in_fn:
                violations.append(f"{fp.name} (contains {check_name if has_name or has_name_in_fn else check_email})")
    
    return len(violations) == 0, violations

def get_git_files(root):
    """Get list of all git-tracked files (no exclusions - if it's tracked, scan it)."""
    import subprocess
    
    try:
        result = subprocess.run(['git', 'ls-files'], cwd=root, capture_output=True, text=True, check=True)
        return [Path(root) / f for f in result.stdout.strip().split('\n') if f]
    except subprocess.CalledProcessError:
        return []
