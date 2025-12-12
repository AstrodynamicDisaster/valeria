"""
Vision model parsers for payslip extraction.
"""

from core.vision_model.payslip_parsers import (
    BasePayslipParser,
    OpenAIPayslipParser,
    GeminiPayslipParser,
    create_openai_parser,
    create_gemini_parser,
)

from core.vision_model.payslip_models import (
    PayslipData,
    Empresa,
    Trabajador,
    Periodo,
    DevengoItem,
    DeduccionItem,
    AportacionEmpresaItem,
    Totales,
)

__all__ = [
    # Parsers
    "BasePayslipParser",
    "OpenAIPayslipParser",
    "GeminiPayslipParser",
    "create_openai_parser",
    "create_gemini_parser",
    # Models
    "PayslipData",
    "Empresa",
    "Trabajador",
    "Periodo",
    "DevengoItem",
    "DeduccionItem",
    "AportacionEmpresaItem",
    "Totales",
]

