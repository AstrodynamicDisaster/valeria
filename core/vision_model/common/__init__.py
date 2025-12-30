"""
Common utilities for vision model processing.
"""

from core.vision_model.common.pricing_config import (
    get_openai_pricing,
    get_gemini_pricing,
    calculate_cost,
    OPENAI_PRICING,
    GEMINI_PRICING,
)

from core.vision_model.common.compare_json import (
    compare_json,
)

from core.vision_model.common.utils import (
    get_page_as_pdf,
    get_pdf_bytes_and_text,
    find_pdf_files,
    sanitize_filename,
    generate_output_filename,
)

__all__ = [
    # Pricing
    "get_openai_pricing",
    "get_gemini_pricing",
    "calculate_cost",
    "OPENAI_PRICING",
    "GEMINI_PRICING",
    # JSON comparison
    "compare_json",
    # Utilities
    "get_page_as_pdf",
    "get_pdf_bytes_and_text",
    "find_pdf_files",
    "sanitize_filename",
    "generate_output_filename",
]

