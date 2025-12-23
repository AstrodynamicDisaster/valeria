"""
Vision model parsers for settlement (finiquito) extraction.
"""

from core.vision_model.settlements.settlement_parsers import (
    BaseSettlementParser,
    OpenAISettlementParser,
    GeminiSettlementParser,
    create_openai_settlement_parser,
    create_gemini_settlement_parser,
)

from core.vision_model.settlements.settlement_models import (
    SettlementData,
    Empresa,
    Trabajador,
)

__all__ = [
    # Parsers
    "BaseSettlementParser",
    "OpenAISettlementParser",
    "GeminiSettlementParser",
    "create_openai_settlement_parser",
    "create_gemini_settlement_parser",
    # Models
    "SettlementData",
    "Empresa",
    "Trabajador",
]

