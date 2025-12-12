"""
Pydantic models for payslip data structure.

These models represent the structured data extracted from Spanish payslips.
"""

from typing import List, Optional
from pydantic import BaseModel, Field


class Empresa(BaseModel):
    """Company information from payslip."""
    razon_social: Optional[str] = Field(None, description="Company legal name")
    cif: Optional[str] = Field(None, description="Company tax ID (CIF)")


class Trabajador(BaseModel):
    """Employee information from payslip."""
    nombre: Optional[str] = Field(None, description="Employee full name (UPPERCASE, no commas)")
    dni: Optional[str] = Field(None, description="Employee ID (DNI/NIE)")
    ss_number: Optional[str] = Field(None, description="Social Security affiliation number (12 digits, no spaces)")


class Periodo(BaseModel):
    """Payroll period information."""
    desde: Optional[str] = Field(None, description="Start date (YYYY-MM-DD or DD-MM-YYYY)")
    hasta: Optional[str] = Field(None, description="End date (YYYY-MM-DD or DD-MM-YYYY)")
    dias: int = Field(0, description="Number of days in period")


class DevengoItem(BaseModel):
    """Earnings item (devengo)."""
    concepto: str = Field(..., description="Concept name (standardized)")
    importe: float = Field(..., description="Amount in euros")


class DeduccionItem(BaseModel):
    """Deduction item."""
    concepto: str = Field(..., description="Concept name (standardized)")
    importe: float = Field(..., description="Amount deducted in euros")
    tipo: Optional[float] = Field(None, description="Percentage rate (if applicable)")


class AportacionEmpresaItem(BaseModel):
    """Employer contribution item."""
    concepto: str = Field(..., description="Contribution concept name (standardized)")
    base: float = Field(..., description="Base amount for calculation")
    tipo: float = Field(..., description="Percentage rate")
    importe: float = Field(..., description="Calculated amount (base * tipo / 100)")


class Totales(BaseModel):
    """Totals section of the payslip."""
    devengo_total: float = Field(..., description="Total earnings")
    deduccion_total: float = Field(..., description="Total deductions")
    liquido_a_percibir: float = Field(..., description="Net amount to receive")
    aportacion_empresa_total: float = Field(..., description="Total employer contributions")


class PayslipData(BaseModel):
    """
    Complete payslip data structure.
    
    This model represents the full extracted data from a Spanish payslip.
    """
    empresa: Empresa = Field(..., description="Company information")
    trabajador: Trabajador = Field(..., description="Employee information")
    periodo: Periodo = Field(..., description="Payroll period")
    devengo_items: List[DevengoItem] = Field(default_factory=list, description="List of earnings items")
    deduccion_items: List[DeduccionItem] = Field(default_factory=list, description="List of deduction items")
    aportacion_empresa_items: List[AportacionEmpresaItem] = Field(
        default_factory=list,
        description="List of employer contribution items"
    )
    totales: Totales = Field(..., description="Totals section")
    warnings: List[str] = Field(default_factory=list, description="List of warnings or corrections made during extraction")

    class Config:
        """Pydantic configuration."""
        json_encoders = {
            float: lambda v: round(v, 2) if v is not None else None
        }

    def verify_and_correct_aportacion_empresa_total(self):
        """Verify the total of the employer contributions."""
        actual_total = self.totales.aportacion_empresa_total
        computed_total = sum(item.importe for item in self.aportacion_empresa_items)
        if actual_total != computed_total:
            correction_message = f"Computed aportacion empresa total {computed_total} does not match actual total {actual_total} inferred by the model. Correcting..."
            self.warnings.append(correction_message)
            self.totales.aportacion_empresa_total = computed_total
            return True
        return False
