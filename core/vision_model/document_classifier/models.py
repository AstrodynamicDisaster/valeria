"""
Pydantic models for document classification results.
"""

from typing import Literal
from pydantic import BaseModel, Field


class ClassificationResult(BaseModel):
    """
    Result of document classification.
    
    Represents the classification of a document as either a payslip or settlement.
    """
    reasoning: str = Field(
        ...,
        description="Brief explanation of why this classification was chosen"
    )
    document_type: Literal["payslip", "settlement"] = Field(
        ...,
        description="Type of document: 'payslip' or 'settlement'"
    )
    confidence: Literal["high", "medium", "low"] = Field(
        ...,
        description="Confidence level of the classification"
    )
