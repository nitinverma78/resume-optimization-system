"""Library for content extraction from various file formats."""
import os,subprocess,pymupdf
from pathlib import Path
from docx import Document
from pptx import Presentation

def extract(fp: Path) -> str:
    try:
        e = fp.suffix.lower()
        if e=='.pdf':  
            with pymupdf.open(fp) as d: return "".join(p.get_text() for p in d).lower()
        if e=='.docx': return "\n".join(p.text for p in Document(fp).paragraphs).lower()
        if e=='.pptx': return "\n".join(sh.text for sl in Presentation(fp).slides for sh in sl.shapes if hasattr(sh,"text")).lower()
        if e=='.doc':  
            r=subprocess.run(['textutil','-convert','txt','-stdout',str(fp)], capture_output=True, text=True)
            return r.stdout.lower() if r.returncode==0 else fp.read_bytes().decode('ascii','ignore').lower()
        return fp.read_text('utf-8','.ignore').lower()
    except Exception as e: print(f"Warning: {fp.name}: {e}"); return ""
