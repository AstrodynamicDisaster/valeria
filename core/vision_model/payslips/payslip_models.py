import logging
from typing import List, Optional
from pydantic import BaseModel, Field, field_validator


class Empresa(BaseModel):
    """Company information from payslip."""

    razon_social: Optional[str] = Field(None, description="Company legal name")
    cif: Optional[str] = Field(None, description="Company tax ID (CIF)")


class Trabajador(BaseModel):
    """Employee information from payslip."""

    nombre: Optional[str] = Field(
        None, description="Employee full name (UPPERCASE, no commas)"
    )
    dni: Optional[str] = Field(None, description="Employee ID (DNI/NIE)")
    ss_number: Optional[str] = Field(
        None, description="Social Security affiliation number (12 digits, no spaces)"
    )


class Periodo(BaseModel):
    """Payroll period information."""

    desde: Optional[str] = Field(
        None, description="Start date (YYYY-MM-DD or DD-MM-YYYY)"
    )
    hasta: Optional[str] = Field(
        None, description="End date (YYYY-MM-DD or DD-MM-YYYY)"
    )
    dias: int = Field(0, description="Number of days in period")


class ItemType(BaseModel):
    """
    Metadata about a devengo or deduccion item.
    Provides additional classification information for payroll items.
    """
    
    ind_is_especie: Optional[bool] = Field(
        None,
        description="True if in-kind (especie), False if monetary (dineraria). Most items are False."
    )
    ind_is_IT_IL: Optional[bool] = Field(
        None,
        description="True if corresponds to IT/IL (Incapacidad Temporal/Invalidez Laboral), sickpay or other disability related items"
    )
    ind_is_anticipo: Optional[bool] = Field(
        None,
        description="True if this item is an advance payment (anticipo)"
    )
    ind_is_embargo: Optional[bool] = Field(
        None,
        description="True if this item is a garnishment/attachment/seizure (embargo)"
    )
    ind_tributa_IRPF: Optional[bool] = Field(
        None,
        description="True if this item is subject to IRPF withholding (tributa al IRPF). Most earnings are True. Exempt items like dietas are False."
    )
    ind_cotiza_ss: Optional[bool] = Field(
        None,
        description="True if this item contributes to Social Security (cotiza a la Seguridad Social)"
    )
    ind_settlement_item: Optional[bool] = Field(
        None,
        description="True if this item is related to a settlement item"
    )


class DevengoItem(BaseModel):
    """Earnings item (devengo)."""

    concepto_raw: str = Field(..., description="Raw concept name (as found in the payslip)")
    concepto_standardized: str = Field(..., description="Concept name (standardized)")
    importe: float = Field(..., description="Amount in euros")
    tipo: Optional[float] = Field(None, description="Percentage rate if applicable")
    item_type: Optional[ItemType] = Field(
        None,
        description="Additional metadata about this earnings item (perception type, IT/IL, etc.)"
    )
    
    @field_validator('importe', mode='before')
    @classmethod
    def coerce_importe(cls, v):
        """Convert None to 0.0 to avoid validation errors."""
        if v is None:
            logging.warning(f"Value is None for {cls.__name__}.{v}")
            return 0.0
        return v


class DeduccionItem(BaseModel):
    """Deduction item."""

    concepto_raw: str = Field(..., description="Raw concept name (as found in the payslip)")
    concepto_standardized: str = Field(..., description="Concept name (standardized)")
    importe: float = Field(..., description="Amount deducted in euros")
    tipo: Optional[float] = Field(None, description="Percentage rate (if applicable)")
    item_type: Optional[ItemType] = Field(
        None,
        description="Additional metadata about this deduction item (perception type, IT/IL, etc.)"
    )
    
    @field_validator('importe', mode='before')
    @classmethod
    def coerce_importe(cls, v):
        """Convert None to 0.0 to avoid validation errors."""
        if v is None:
            logging.warning(f"Value is None for {cls.__name__}.{v}")
            return 0.0
        return v



class AportacionEmpresaItem(BaseModel):
    """Employer contribution item."""

    concepto_raw: str = Field(..., description="Raw contribution concept name (as found in the payslip)")
    concepto_standardized: str = Field(..., description="Contribution concept name (standardized)")
    base: float = Field(..., description="Base amount for calculation")
    tipo: float = Field(..., description="Percentage rate")
    importe: float = Field(..., description="Calculated amount (base * tipo / 100)")
    
    @field_validator('importe', 'base', 'tipo', mode='before')
    @classmethod
    def coerce_numeric(cls, v):
        """Convert None to 0.0 to avoid validation errors."""
        if v is None:
            logging.warning(f"Value is None for {cls.__name__}.{v}")
            return 0.0
        return v


class Totales(BaseModel):
    """Totals section of the payslip."""

    devengo_total: float = Field(..., description="Total earnings")
    deduccion_total: float = Field(..., description="Total deductions")
    liquido_a_percibir: float = Field(..., description="Net amount to receive")
    aportacion_empresa_total: float = Field(
        ..., description="Total employer contributions"
    )
    
    # PP EXTRAS
    prorrata_pagas_extra_total: Optional[float] = Field(None, description="Total prorrata of extra pay")

    # BASE Contingencias Comunes
    base_contingencias_comunes_total: Optional[float] = Field(None, description="Total base for Contingencies Common")
    # BASE  Accidente de Trabajo (AT) y Desempleo
    base_accidente_de_trabajo_y_desempleo_total: Optional[float] = Field(None, description="Total base for Accidents & Professional Diseases and Unemployment")
    # BASE IRPF
    base_retencion_irpf_total: Optional[float] = Field(None, description="Total base for IRPF")
    # % Retención IRPF (top level de payroll line)
    porcentaje_retencion_irpf: Optional[float] = Field(None, description="Percentage for IRPF")
    
    # Settlement indicator
    contains_settlement: Optional[bool] = Field(
        None,
        description="Whether this payslip contains any settlement/termination/finiquito items"
    )
    
    @field_validator('devengo_total', 'deduccion_total', 'liquido_a_percibir', 'aportacion_empresa_total', mode='before')
    @classmethod
    def coerce_totals(cls, v):
        """Convert None to 0.0 to avoid validation errors."""
        if v is None:
            logging.warning(f"Value is None for {cls.__name__}.{v}")
            return 0.0
        return v


class PayslipData(BaseModel):
    """
    Complete payslip data structure.
    This model represents the full extracted data from a Spanish payslip.
    """

    empresa: Empresa = Field(..., description="Company information")
    trabajador: Trabajador = Field(..., description="Employee information")
    periodo: Periodo = Field(..., description="Payroll period")
    devengo_items: List[DevengoItem] = Field(
        default_factory=list, description="List of earnings items"
    )
    deduccion_items: List[DeduccionItem] = Field(
        default_factory=list, description="List of deduction items"
    )
    aportacion_empresa_items: List[AportacionEmpresaItem] = Field(
        default_factory=list, description="List of employer contribution items"
    )

    totales: Totales = Field(..., description="Totals section")

    fecha_documento: Optional[str] = Field(None, description="Date of the document (YYYY-MM-DD), when the document was signed/issued")
    
    warnings: List[str] = Field(
        default_factory=list,
        description="List of warnings or corrections made during extraction",
    )

    class Config:
        """Pydantic configuration."""

        json_encoders = {float: lambda v: round(v, 2) if v is not None else None}

    def verify_and_correct_aportacion_empresa_total(self):
        """Verify the total of the employer contributions."""
        actual_total = self.totales.aportacion_empresa_total
        computed_total = round(sum(item.importe for item in self.aportacion_empresa_items), 2)
        if actual_total != computed_total:
            correction_message = f"Computed aportacion empresa total {computed_total} does not match actual total {actual_total} inferred by the model. Correcting..."
            self.warnings.append(correction_message)
            self.totales.aportacion_empresa_total = computed_total
            return True
        return False
