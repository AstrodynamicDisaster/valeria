from typing import List, Optional, Union, Literal
from pydantic import BaseModel, Field
from core.vision_model.payslips.payslip_models import PayslipData
from core.vision_model.settlements.settlement_models import SettlementData

class LogicalDocument(BaseModel):
    """
    A single logical document extracted from a PDF (e.g., one monthly payslip or one settlement).
    """
    type: Literal["payslip", "settlement"] = Field(..., description="Type of the logical document")
    data: Union[PayslipData, SettlementData] = Field(..., description="The actual extracted data for this document")

class UnifiedExtractionResponse(BaseModel):
    """
    The top-level response structure for the unified document parser.
    A single PDF can contain multiple logical documents.
    """
    logical_documents: List[LogicalDocument] = Field(
        default_factory=list, 
        description="List of logical documents (payslips or settlements) found in the PDF"
    )
    warnings: List[str] = Field(
        default_factory=list,
        description="Global warnings about the PDF processing"
    )

