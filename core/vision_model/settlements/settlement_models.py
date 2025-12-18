import logging
from typing import List, Optional

from pydantic import BaseModel, Field, field_validator


class Empresa(BaseModel):
    """Company information from settlement."""
    razon_social: Optional[str] = Field(None, description="Company legal name")
    cif: Optional[str] = Field(None, description="Company tax ID (CIF)")


class Trabajador(BaseModel):
    """Employee information from settlement."""
    nombre: Optional[str] = Field(None, description="Employee full name (UPPERCASE, no commas)")
    dni: Optional[str] = Field(None, description="Employee ID (DNI/NIE)")


class ItemType(BaseModel):
    """
    Metadata about a settlement item.
    Provides additional classification information for settlement items.
    """
    
    ind_is_especie: Optional[bool] = Field(
        None,
        description="True if in-kind (especie), False if monetary (dineraria). Most items are False."
    )
    ind_is_IT_IL: Optional[bool] = Field(
        None,
        description="True if corresponds to IT/IL (Incapacidad Temporal/Invalidez Laboral)"
    )
    ind_is_anticipo: Optional[bool] = Field(
        None,
        description="True if this item is an advance payment (anticipo)"
    )
    ind_is_embargo: Optional[bool] = Field(
        None,
        description="True if this item is a garnishment/attachment (embargo)"
    )
    ind_is_exento_IRPF: Optional[bool] = Field(
        None,
        description="True if this item is exempt from IRPF withholding"
    )
    ind_cotiza_ss: Optional[bool] = Field(
        None,
        description="True if this item contributes to Social Security (cotiza a la Seguridad Social)"
    )


class SettlementItem(BaseModel):
    """Settlement item (liquidación item)."""
    concepto_raw: str = Field(..., description="Raw concept name as found in the document")
    concepto_standardized: str = Field(..., description="Standardized concept name (e.g., 'VACACIONES NO DISFRUTADAS', 'PAGA EXTRA PRORRATEADA', etc.)")
    importe: float = Field(..., description="Amount in euros")
    tipo: Optional[float] = Field(None, description="Percentage rate if applicable (e.g., IRPF retention)")
    dias: Optional[float] = Field(None, description="Number of days (if applicable)")
    base: Optional[float] = Field(None, description="Base amount for calculation (if applicable)")
    item_type: Optional[ItemType] = Field(
        None,
        description="Additional metadata about this settlement item (perception type, IT/IL, etc.)"
    )
    
    @field_validator('importe', mode='before')
    @classmethod
    def coerce_importe(cls, v):
        """Convert None to 0.0 to avoid validation errors."""
        if v is None:
            logging.warning(f"Value is None for {cls.__name__}.{v}")
            return 0.0
        return v


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

