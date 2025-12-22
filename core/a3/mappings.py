from __future__ import annotations

from typing import Dict, List, Optional, TypedDict


class A3ConceptMapping(TypedDict):
    concept_code: int
    description: str
    collection_type: str
    collection_type_id: Optional[int]
    tributa_irpf: Optional[bool]
    cotiza_ss: Optional[bool]
    en_especie: Optional[bool]

A3_CONCEPT_MAPPINGS: List[A3ConceptMapping] = [
    {"concept_code": 1, "description": "Salario base", "collection_type": "Totales", "collection_type_id": 1, "cotiza_ss": True, "tributa_irpf": True, "en_especie": False},
    {"concept_code": 11, "description": "Bolsa de estudios", "collection_type": "Totales", "collection_type_id": 1, "cotiza_ss": True, "tributa_irpf": True, "en_especie": False},
    {"concept_code": 30, "description": "Gratificacion - PExtras", "collection_type": "Totales", "collection_type_id": 1, "cotiza_ss": True, "tributa_irpf": True, "en_especie": False},
    {"concept_code": 31, "description": "Mejora Voluntaria", "collection_type": "Totales", "collection_type_id": 1, "cotiza_ss": True, "tributa_irpf": True, "en_especie": False},
    {"concept_code": 32, "description": "Incentivos", "collection_type": "Totales", "collection_type_id": 1, "cotiza_ss": True, "tributa_irpf": True, "en_especie": False},
    {"concept_code": 33, "description": "Bonus", "collection_type": "Totales", "collection_type_id": 1, "cotiza_ss": True, "tributa_irpf": True, "en_especie": False},
    {"concept_code": 34, "description": "Bonus (Neto)", "collection_type": "Totales", "collection_type_id": 1, "cotiza_ss": True, "tributa_irpf": True, "en_especie": False},
    {"concept_code": 35, "description": "Plus implicacion", "collection_type": "Totales", "collection_type_id": 1, "cotiza_ss": True, "tributa_irpf": True, "en_especie": False},
    {"concept_code": 36, "description": "Plus Resenas", "collection_type": "Totales", "collection_type_id": 1, "cotiza_ss": True, "tributa_irpf": True, "en_especie": False},
    {"concept_code": 37, "description": "Plus herramientas de trabajo", "collection_type": "Totales", "collection_type_id": 36, "cotiza_ss": True, "tributa_irpf": True, "en_especie": False},
    {"concept_code": 38, "description": "Bonus neto", "collection_type": "Totales", "collection_type_id": 1, "cotiza_ss": False, "tributa_irpf": False, "en_especie": False},
    {"concept_code": 39, "description": "Primas", "collection_type": "Totales", "collection_type_id": 1, "cotiza_ss": True, "tributa_irpf": True, "en_especie": False},
    {"concept_code": 41, "description": "Retr Administrador", "collection_type": "Totales", "collection_type_id": 1, "cotiza_ss": True, "tributa_irpf": True, "en_especie": False},
    {"concept_code": 42, "description": "Sign-in Bonus", "collection_type": "Totales", "collection_type_id": 1, "cotiza_ss": True, "tributa_irpf": True, "en_especie": False},
    {"concept_code": 43, "description": "Autonomos", "collection_type": "Totales", "collection_type_id": 1, "cotiza_ss": False, "tributa_irpf": True, "en_especie": True},
    {"concept_code": 50, "description": "Ajuste SMI", "collection_type": "Totales", "collection_type_id": 1, "cotiza_ss": True, "tributa_irpf": True, "en_especie": False},
    {"concept_code": 60, "description": "Plus Compensable/Absorbible", "collection_type": "Totales", "collection_type_id": 1, "cotiza_ss": True, "tributa_irpf": True, "en_especie": False},
    {"concept_code": 70, "description": "Exclusividad", "collection_type": "Totales", "collection_type_id": 1, "cotiza_ss": True, "tributa_irpf": True, "en_especie": False},
    {"concept_code": 71, "description": "Non-compete", "collection_type": "Totales", "collection_type_id": 1, "cotiza_ss": True, "tributa_irpf": True, "en_especie": False},
    {"concept_code": 101, "description": "Festivos trabajados", "collection_type": "Unidades", "collection_type_id": 1, "cotiza_ss": True, "tributa_irpf": True, "en_especie": False},
    {"concept_code": 151, "description": "Horas nocturnas", "collection_type": "Unidades", "collection_type_id": 1, "cotiza_ss": True, "tributa_irpf": True, "en_especie": False},
    {"concept_code": 160, "description": "Plus Ropa", "collection_type": "Unidades", "collection_type_id": 29, "cotiza_ss": True, "tributa_irpf": True, "en_especie": False},
    {"concept_code": 161, "description": "Plus Ropa (Especie)", "collection_type": "Unidades", "collection_type_id": 29, "cotiza_ss": True, "tributa_irpf": True, "en_especie": True},
    {"concept_code": 170, "description": "Manutencion (Especie)", "collection_type": "Unidades", "collection_type_id": 22, "cotiza_ss": True, "tributa_irpf": True, "en_especie": True},
    {"concept_code": 171, "description": "Manutencion (Dinerario)", "collection_type": "Unidades", "collection_type_id": 22, "cotiza_ss": True, "tributa_irpf": True, "en_especie": False},
    {"concept_code": 172, "description": "Dietas (sin pernocta) - Viaje", "collection_type": "Totales", "collection_type_id": 45, "cotiza_ss": False, "tributa_irpf": False, "en_especie": False},
    {"concept_code": 173, "description": "Dietas (con pernocta) - Viaje", "collection_type": "Totales", "collection_type_id": 43, "cotiza_ss": False, "tributa_irpf": False, "en_especie": False},
    {"concept_code": 180, "description": "Plus Transporte", "collection_type": "Totales", "collection_type_id": 32, "cotiza_ss": True, "tributa_irpf": True, "en_especie": False},
    {"concept_code": 181, "description": "Kilometraje", "collection_type": "Totales", "collection_type_id": 32, "cotiza_ss": False, "tributa_irpf": False, "en_especie": False},
    {"concept_code": 182, "description": "Gastos locomocion", "collection_type": "Totales", "collection_type_id": 50, "cotiza_ss": False, "tributa_irpf": False, "en_especie": False},
    {"concept_code": 190, "description": "Plus peligrosidad", "collection_type": "Totales", "collection_type_id": 1, "cotiza_ss": True, "tributa_irpf": True, "en_especie": False},
    {"concept_code": 195, "description": "Ajuste vacaciones disfrutadas", "collection_type": "Totales", "collection_type_id": 1, "cotiza_ss": False, "tributa_irpf": False, "en_especie": False},
    {"concept_code": 196, "description": "Ajuste error vacaciones - Descuento", "collection_type": "Totales", "collection_type_id": 1, "cotiza_ss": False, "tributa_irpf": False, "en_especie": False},
    {"concept_code": 197, "description": "Ajuste error vacaciones - Cobro", "collection_type": "Totales", "collection_type_id": 1, "cotiza_ss": False, "tributa_irpf": True, "en_especie": False},
    {"concept_code": 198, "description": "Vacaciones manual", "collection_type": "Unidades", "collection_type_id": 1, "cotiza_ss": True, "tributa_irpf": True, "en_especie": False},
    {"concept_code": 199, "description": "*Parte Proporcional Vacaciones Finiquito", "collection_type": "Unidades", "collection_type_id": 6, "cotiza_ss": True, "tributa_irpf": True, "en_especie": False},
    {"concept_code": 201, "description": "Horas complementarias", "collection_type": "Unidades", "collection_type_id": 57, "cotiza_ss": True, "tributa_irpf": True, "en_especie": False},
    {"concept_code": 202, "description": "Horas extras", "collection_type": "Unidades", "collection_type_id": 2, "cotiza_ss": True, "tributa_irpf": True, "en_especie": False},
    {"concept_code": 210, "description": "Actividad (H. Extras)", "collection_type": "Unidades", "collection_type_id": 1, "cotiza_ss": True, "tributa_irpf": True, "en_especie": False},
    {"concept_code": 230, "description": "Absentismo", "collection_type": "Unidades (Horas)", "collection_type_id": 1, "cotiza_ss": True, "tributa_irpf": True, "en_especie": False},
    {"concept_code": 235, "description": "Efectivo", "collection_type": "Totales", "collection_type_id": 1, "cotiza_ss": False, "tributa_irpf": False, "en_especie": False},
    {"concept_code": 236, "description": "CashBalance", "collection_type": "Totales", "collection_type_id": 1, "cotiza_ss": False, "tributa_irpf": False, "en_especie": False},
    {"concept_code": 237, "description": "Devolucion efectivo", "collection_type": "Totales", "collection_type_id": 1, "cotiza_ss": False, "tributa_irpf": False, "en_especie": False},
    {"concept_code": 240, "description": "Descuento nomina", "collection_type": "Totales", "collection_type_id": 1, "cotiza_ss": True, "tributa_irpf": True, "en_especie": False},
    {"concept_code": 241, "description": "Vacaciones disfrutadas no generadas", "collection_type": "Totales", "collection_type_id": 1, "cotiza_ss": True, "tributa_irpf": True, "en_especie": False},
    {"concept_code": 242, "description": "Ajuste - Descuento error previo", "collection_type": "Totales", "collection_type_id": None, "cotiza_ss": True, "tributa_irpf": True, "en_especie": False},
    {"concept_code": 243, "description": "Ajuste - Descuento error horas", "collection_type": "Totales", "collection_type_id": None, "cotiza_ss": True, "tributa_irpf": True, "en_especie": False},
    {"concept_code": 244, "description": "Ajuste Positivo", "collection_type": "Totales", "collection_type_id": 1, "cotiza_ss": True, "tributa_irpf": True, "en_especie": False},
    {"concept_code": 252, "description": "Seguro Medico Trabajador", "collection_type": "Totales", "collection_type_id": 1, "cotiza_ss": None, "tributa_irpf": None, "en_especie": True},
    {"concept_code": 253, "description": "Seguro Medico Exento", "collection_type": "Totales", "collection_type_id": 13, "cotiza_ss": None, "tributa_irpf": None, "en_especie": True},
    {"concept_code": 254, "description": "Seguro Accidentes", "collection_type": "Totales", "collection_type_id": 13, "cotiza_ss": None, "tributa_irpf": None, "en_especie": True},
    {"concept_code": 301, "description": "Paga extra prorrateada", "collection_type": "Totales", "collection_type_id": None, "cotiza_ss": True, "tributa_irpf": True, "en_especie": False},
    {"concept_code": 321, "description": "Subida convenio Pendiente", "collection_type": "Totales", "collection_type_id": None, "cotiza_ss": True, "tributa_irpf": True, "en_especie": False},
    {"concept_code": 322, "description": "Regularizacion meses anteriores", "collection_type": "Totales", "collection_type_id": None, "cotiza_ss": True, "tributa_irpf": True, "en_especie": False},
    {"concept_code": 323, "description": "Regularizacion meses anteriores", "collection_type": "Totales", "collection_type_id": 1, "cotiza_ss": True, "tributa_irpf": True, "en_especie": False},
    {"concept_code": 351, "description": "Propinas - C/IRPF", "collection_type": "Totales", "collection_type_id": 1, "cotiza_ss": False, "tributa_irpf": True, "en_especie": False},
    {"concept_code": 352, "description": "Propinas - S/IRPF", "collection_type": "Totales", "collection_type_id": 1, "cotiza_ss": False, "tributa_irpf": False, "en_especie": False},
]


A3_CONCEPT_BY_CODE: Dict[int, A3ConceptMapping] = {
    mapping["concept_code"]: mapping for mapping in A3_CONCEPT_MAPPINGS
}


def _normalize_code(code: object) -> Optional[int]:
    if code is None:
        return None
    try:
        return int(str(code).strip())
    except (TypeError, ValueError):
        return None


def get_concept_mapping(code: object) -> Optional[A3ConceptMapping]:
    normalized = _normalize_code(code)
    if normalized is None:
        return None
    return A3_CONCEPT_BY_CODE.get(normalized)


def taxability_for(code: object) -> Optional[Dict[str, Optional[bool]]]:
    mapping = get_concept_mapping(code)
    if mapping is None:
        return None
    return {
        "tributa_irpf": mapping["tributa_irpf"],
        "cotiza_ss": mapping["cotiza_ss"],
        "en_especie": mapping["en_especie"],
    }


def is_taxable_income(code: object, default: Optional[bool] = None) -> Optional[bool]:
    mapping = get_concept_mapping(code)
    if mapping is None:
        return default
    return mapping["tributa_irpf"] if mapping["tributa_irpf"] is not None else default


def is_taxable_ss(code: object, default: Optional[bool] = None) -> Optional[bool]:
    mapping = get_concept_mapping(code)
    if mapping is None:
        return default
    return mapping["cotiza_ss"] if mapping["cotiza_ss"] is not None else default


def is_in_kind(code: object, default: Optional[bool] = None) -> Optional[bool]:
    mapping = get_concept_mapping(code)
    if mapping is None:
        return default
    return mapping["en_especie"] if mapping["en_especie"] is not None else default
