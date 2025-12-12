"""
Utility functions for payslip parser tests.
"""

import pymupdf
from typing import Tuple


def get_page_as_pdf(pdf_path: str, page_num: int) -> Tuple[bytes, str]:
    """
    Get PDF bytes and extracted text for a specific page.
    
    Args:
        pdf_path: Path to PDF file
        page_num: Page number (0-indexed)
    
    Returns:
        Tuple of (pdf_bytes, text_pdf)
        - pdf_bytes: Raw bytes of the page as a single-page PDF
        - text_pdf: Extracted text from the page
    """
    doc = pymupdf.open(pdf_path)
    
    try:
        # Create a new PDF with just this page
        new_doc = pymupdf.open()
        new_doc.insert_pdf(doc, from_page=page_num, to_page=page_num)
        pdf_bytes = new_doc.tobytes()
        
        # Extract text from the page
        text_pdf = ""
        for i, page in enumerate(new_doc):
            text_pdf += f"\n\nPAGE {i + 1}\n\n"
            text_pdf += page.get_text("text")
        
        new_doc.close()
        return pdf_bytes, text_pdf
    finally:
        doc.close()

