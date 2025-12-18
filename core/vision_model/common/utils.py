import pymupdf
from pathlib import Path
from typing import Tuple
import re


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


def find_pdf_files(directory: Path) -> list[Path]:
    """
    Find all PDF files in the given directory recursively.
    
    Args:
        directory: Directory path to search
    
    Returns:
        List of PDF file paths
    """
    return list(directory.rglob("*.pdf"))


def sanitize_filename(filename: str, max_length: int = 200) -> str:
    """
    Sanitize a filename by removing invalid characters and limiting length.
    
    Args:
        filename: Original filename
        max_length: Maximum length of the filename
    
    Returns:
        Sanitized filename safe for filesystem
    """
    # Remove invalid characters for filenames
    # Keep alphanumeric, spaces, hyphens, underscores, and dots
    sanitized = re.sub(r'[<>:"/\\|?*]', '', filename)
    
    # Replace multiple spaces with single space
    sanitized = re.sub(r'\s+', ' ', sanitized)
    
    # Trim whitespace
    sanitized = sanitized.strip()
    
    # Limit length
    if len(sanitized) > max_length:
        sanitized = sanitized[:max_length]
    
    return sanitized


def generate_output_filename(
    document_type: str,
    dni: str = None,
    employee_name: str = None,
    company: str = None,
    page_num: int = None,
    date: str = None,
) -> str:
    """
    Generate output filename in format: {TYPE}_{DNI}_{EMPLOYEE_NAME}_{COMPANY}_{YYYY-MM-DD}.json
    
    Args:
        document_type: "PAYSLIP" or "SETTLEMENT"
        dni: Employee DNI/NIE
        employee_name: Employee name
        company: Company name
        page_num: Optional page number (if None, not included)
        date: Date string in YYYY-MM-DD format (will be normalized to YYYY-MM-DD)
    
    Returns:
        Sanitized filename
    """
    parts = [document_type.upper()]
    
    if dni:
        parts.append(sanitize_filename(dni, 20))
    else:
        parts.append("UNKNOWN")
    
    if employee_name:
        parts.append(sanitize_filename(employee_name, 50))
    else:
        parts.append("UNKNOWN")
    
    if company:
        parts.append(sanitize_filename(company, 50))
    else:
        parts.append("UNKNOWN")
    
    # Add date (full date YYYY-MM-DD) if provided
    if date:
        # Normalize date to YYYY-MM-DD format
        try:
            import re
            from datetime import datetime
            
            # Try to parse various date formats
            date_str = None
            
            # Check if already in YYYY-MM-DD format
            if re.match(r'^\d{4}-\d{2}-\d{2}$', date):
                date_str = date
            # Check DD-MM-YYYY format
            elif re.match(r'^\d{2}-\d{2}-\d{4}$', date):
                try:
                    dt = datetime.strptime(date, '%d-%m-%Y')
                    date_str = dt.strftime('%Y-%m-%d')
                except ValueError:
                    pass
            # Check DD/MM/YYYY format
            elif re.match(r'^\d{2}/\d{2}/\d{4}$', date):
                try:
                    dt = datetime.strptime(date, '%d/%m/%Y')
                    date_str = dt.strftime('%Y-%m-%d')
                except ValueError:
                    pass
            # Try to extract date from other formats
            else:
                # Look for YYYY-MM-DD pattern
                match = re.search(r'(\d{4})[-/](\d{2})[-/](\d{2})', date)
                if match:
                    date_str = f"{match.group(1)}-{match.group(2)}-{match.group(3)}"
                # Look for DD-MM-YYYY pattern
                else:
                    match = re.search(r'(\d{2})[-/](\d{2})[-/](\d{4})', date)
                    if match:
                        try:
                            dt = datetime.strptime(f"{match.group(1)}-{match.group(2)}-{match.group(3)}", '%d-%m-%Y')
                            date_str = dt.strftime('%Y-%m-%d')
                        except ValueError:
                            pass
            
            if date_str:
                parts.append(date_str)
        except Exception:
            # If date parsing fails, skip adding date to filename
            pass
    
    if page_num is not None:
        parts.append(f"P{page_num + 1}")
    
    filename = "_".join(parts)
    return f"{filename}.json"

