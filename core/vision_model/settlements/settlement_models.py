from typing import List, Optional

from pydantic import BaseModel, Field

# Reuse models from payslips for consistency
from core.vision_model.payslips.payslip_models import (
    DevengoItem,
    DeduccionItem,
    Totales,
)


class Empresa(BaseModel):
    """Company information from settlement."""
    razon_social: Optional[str] = Field(None, description="Company legal name")
    cif: Optional[str] = Field(None, description="Company tax ID (CIF)")


class Trabajador(BaseModel):
    """Employee information from settlement."""
    nombre: Optional[str] = Field(None, description="Employee full name (UPPERCASE, no commas)")
    dni: Optional[str] = Field(None, description="Employee ID (DNI/NIE)")
    ss_number: Optional[str] = Field(
        None, description="Social Security affiliation number (12 digits, no spaces)"
    )


class SettlementData(BaseModel):
    """
    Complete settlement data structure.
    
    This model represents the full extracted data from a Spanish termination settlement.
    Uses the same structure as PayslipData (devengo_items, deduccion_items) for consistency.
    """
    empresa: Empresa = Field(..., description="Company information")
    trabajador: Trabajador = Field(..., description="Employee information")
    
    # Settlement-specific fields
    fecha_cese: Optional[str] = Field(None, description="Termination date (YYYY-MM-DD)")
    causa: Optional[str] = Field(None, description="Termination reason")
    fecha_liquidacion: Optional[str] = Field(None, description="Settlement date (YYYY-MM-DD)")
    lugar: Optional[str] = Field(None, description="Place where settlement was signed")
    
    # Use same structure as payslip for items
    devengo_items: List[DevengoItem] = Field(
        default_factory=list, description="List of earnings items (positive amounts paid to employee)"
    )
    deduccion_items: List[DeduccionItem] = Field(
        default_factory=list, description="List of deduction items (negative amounts or deductions)"
    )
    
    # Totals (similar to payslip)
    totales: Totales = Field(..., description="Totals section")
    
    # Document date
    fecha_documento: Optional[str] = Field(None, description="Date of the document (YYYY-MM-DD), when the document was signed/issued")
    
    warnings: List[str] = Field(
        default_factory=list,
        description="List of warnings or corrections made during extraction"
    )

    class Config:
        """Pydantic configuration."""
        json_encoders = {
            float: lambda v: round(v, 2) if v is not None else None
        }

    def verify_and_correct_totals(self):
        """Verify and correct totals from settlement items."""
        # Calculate totals from items
        devengo_total = sum(item.importe for item in self.devengo_items)
        deduccion_total = sum(item.importe for item in self.deduccion_items)
        liquido_total = devengo_total - deduccion_total
        
        # Update totals if they don't match
        corrected = False
        if abs(self.totales.devengo_total - devengo_total) > 0.01:
            self.totales.devengo_total = devengo_total
            corrected = True
        if abs(self.totales.deduccion_total - deduccion_total) > 0.01:
            self.totales.deduccion_total = deduccion_total
            corrected = True
        if abs(self.totales.liquido_a_percibir - liquido_total) > 0.01:
            self.totales.liquido_a_percibir = liquido_total
            corrected = True
        
        if corrected:
            self.warnings.append("Totals were recalculated from settlement items.")
        
        return corrected

