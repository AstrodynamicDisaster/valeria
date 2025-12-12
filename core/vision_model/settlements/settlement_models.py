"""
Pydantic models for settlement (finiquito) data structure.

These models represent the structured data extracted from Spanish termination settlements.
"""

from typing import List, Optional
from pydantic import BaseModel, Field


class Empresa(BaseModel):
    """Company information from settlement."""
    razon_social: Optional[str] = Field(None, description="Company legal name")
    cif: Optional[str] = Field(None, description="Company tax ID (CIF)")


class Trabajador(BaseModel):
    """Employee information from settlement."""
    nombre: Optional[str] = Field(None, description="Employee full name (UPPERCASE, no commas)")
    dni: Optional[str] = Field(None, description="Employee ID (DNI/NIE)")


class SettlementItem(BaseModel):
    """Settlement item (liquidación item)."""
    concepto: str = Field(..., description="Concept name (e.g., 'Vacaciones', 'Paga extra', etc.)")
    importe: float = Field(..., description="Amount in euros")
    dias: Optional[int] = Field(None, description="Number of days (if applicable)")
    base: Optional[float] = Field(None, description="Base amount for calculation (if applicable)")


class SettlementData(BaseModel):
    """
    Complete settlement (finiquito) data structure.
    
    This model represents the full extracted data from a Spanish termination settlement.
    """
    empresa: Empresa = Field(..., description="Company information")
    trabajador: Trabajador = Field(..., description="Employee information")
    fecha_cese: Optional[str] = Field(None, description="Termination date (YYYY-MM-DD)")
    causa: Optional[str] = Field(None, description="Termination reason")
    fecha_liquidacion: Optional[str] = Field(None, description="Settlement date (YYYY-MM-DD)")
    lugar: Optional[str] = Field(None, description="Place where settlement was signed")
    settlement_items: List[SettlementItem] = Field(
        default_factory=list,
        description="List of settlement items (liquidación items)"
    )
    total: Optional[float] = Field(None, description="Total settlement amount")
    warnings: List[str] = Field(
        default_factory=list,
        description="List of warnings or corrections made during extraction"
    )

    class Config:
        """Pydantic configuration."""
        json_encoders = {
            float: lambda v: round(v, 2) if v is not None else None
        }

    def verify_and_correct_total(self):
        """Verify the total of the settlement items."""
        if self.total is None:
            return False
        computed_total = sum(item.importe for item in self.settlement_items)
        if abs(self.total - computed_total) > 0.01:  # Allow small floating point differences
            correction_message = f"Computed settlement total {computed_total} does not match actual total {self.total}. Correcting..."
            self.warnings.append(correction_message)
            self.total = computed_total
            return True
        return False

