#!/usr/bin/env python3
"""
Script para mapear JSONs extraídos de payslips al formato de la base de datos.

Uso:
    python -m core.vision_model.scripts.map_json_to_db <input_folder> [output_file]

Ejemplo:
    python -m core.vision_model.scripts.map_json_to_db processed_documents/old7_tepuy payrolls_mapped.json
"""

import json
import sys
from pathlib import Path
from decimal import Decimal
from typing import Dict, Any, List, Optional
from datetime import datetime


def map_item_to_payroll_line(item: Dict[str, Any], category: str) -> Dict[str, Any]:
    """
    Mapea un item del JSON extraído a formato PayrollLine.
    
    Args:
        item: Item del JSON (devengo_item, deduccion_item, etc.)
        category: Categoría del item ('devengo', 'deduccion', 'aportacion_empresa')
    
    Returns:
        Diccionario con formato PayrollLine
    """
    item_type = item.get("item_type", {})
    
    return {
        "category": category,
        "concept": item.get("concepto_standardized") or item.get("concepto_raw", ""),
        "raw_concept": item.get("concepto_raw", ""),
        "amount": float(item.get("importe", 0)),
        "is_taxable_income": item_type.get("ind_tributa_IRPF", False),
        "is_taxable_ss": item_type.get("ind_cotiza_ss", False),
        "is_sickpay": item_type.get("ind_is_IT_IL", False),
        "is_in_kind": item_type.get("ind_is_especie", False),
        "is_pay_advance": item_type.get("ind_is_anticipo", False),
        "is_seizure": item_type.get("ind_is_embargo", False),
    }


def map_payslip_json_to_db_format(json_data: Dict[str, Any], source_file: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """
    Mapea un JSON extraído de payslip al formato de la base de datos.
    
    Args:
        json_data: JSON completo de la extracción
        source_file: Nombre del archivo JSON fuente (opcional)
    
    Returns:
        Diccionario con formato compatible con la DB o None si hay error
    """
    try:
        # Verificar que es un payslip o payslip+settlement
        doc_type = json_data.get("document_type", "")
        if doc_type not in ("payslip", "payslip+settlement", "settlement"):
            return None
        
        data = json_data.get("data", {})
        if not data:
            return None
        
        totales = data.get("totales", {})
        periodo = data.get("periodo", {})
        empresa = data.get("empresa", {})
        trabajador = data.get("trabajador", {})
        
        # Mapear periodo
        periodo_mapped = {
            "desde": periodo.get("desde"),
            "hasta": periodo.get("hasta"),
            "dias": periodo.get("dias"),
        }
        
        # Mapear totales (manejar nulls)
        def safe_decimal(value, default=0.0):
            """Convierte valor a float, manejando None"""
            if value is None:
                return default
            try:
                return float(value)
            except (ValueError, TypeError):
                return default
        
        # Determinar el tipo de nómina para la DB
        payroll_type = "payslip"
        if doc_type == "settlement":
            payroll_type = "settlement"
        elif doc_type == "payslip+settlement":
            payroll_type = "hybrid"

        # Mapear payroll principal
        payroll = {
            "type": payroll_type,
            # Información de identificación (para matching)
            "empresa": {
                "razon_social": empresa.get("razon_social"),
                "cif": empresa.get("cif"),
            },
            "trabajador": {
                "nombre": trabajador.get("nombre"),
                "dni": trabajador.get("dni"),
                "ss_number": trabajador.get("ss_number"),
            },
            
            # Periodo
            "periodo": periodo_mapped,
            
            # Totales
            "devengo_total": safe_decimal(totales.get("devengo_total")),
            "deduccion_total": safe_decimal(totales.get("deduccion_total")),
            "aportacion_empresa_total": safe_decimal(totales.get("aportacion_empresa_total")),
            "liquido_a_percibir": safe_decimal(totales.get("liquido_a_percibir")),
            "prorrata_pagas_extra": safe_decimal(totales.get("prorrata_pagas_extra_total")),
            "base_cc": safe_decimal(totales.get("base_contingencias_comunes_total")),
            "base_at_ep": safe_decimal(totales.get("base_accidente_de_trabajo_y_desempleo_total")),
            "base_irpf": safe_decimal(totales.get("base_retencion_irpf_total")),
            "tipo_irpf": safe_decimal(totales.get("porcentaje_retencion_irpf")),
            
            # Warnings
            "warnings": data.get("warnings", []),
            
            # Fecha del documento
            "fecha_documento": data.get("fecha_documento"),
            
            # Metadata del archivo original
            "source_file": json_data.get("source_pdf"),
            "page": json_data.get("page"),
            "timestamp": json_data.get("timestamp"),
            "source_json_file": source_file,  # Archivo JSON fuente
        }
        
        # Mapear line items
        payroll_lines = []
        
        # Devengo items
        for item in data.get("devengo_items", []):
            payroll_lines.append(map_item_to_payroll_line(item, "devengo"))
        
        # Deduccion items
        for item in data.get("deduccion_items", []):
            payroll_lines.append(map_item_to_payroll_line(item, "deduccion"))
        
        # Aportacion empresa items
        for item in data.get("aportacion_empresa_items", []):
            payroll_lines.append(map_item_to_payroll_line(item, "aportacion_empresa"))
        
        payroll["payroll_lines"] = payroll_lines
        
        return payroll
        
    except Exception as e:
        print(f"Error mapeando JSON: {e}", file=sys.stderr)
        return None


def is_valid_document_file(filename: str) -> bool:
    """
    Verifica si un archivo debe ser procesado basándose en su nombre.
    
    Args:
        filename: Nombre del archivo
    
    Returns:
        True si el archivo empieza con "PAYSLIP" o "SETTLEMENT"
    """
    filename_upper = filename.upper()
    return filename_upper.startswith("PAYSLIP") or filename_upper.startswith("SETTLEMENT")


def get_payroll_key(payroll: Dict[str, Any]) -> Optional[tuple]:
    """
    Genera una clave única para agrupar nóminas del mismo trabajador y fecha de documento.
    Usa fecha_documento en lugar de periodo porque no siempre está el periodo en el documento.
    
    Args:
        payroll: Payroll mapeado
    
    Returns:
        Tupla (dni, fecha_documento) o None si falta información
    """
    trabajador = payroll.get("trabajador", {})
    dni = trabajador.get("dni")
    fecha_documento = payroll.get("fecha_documento")
    
    if dni and fecha_documento:
        return (dni, fecha_documento)
    
    # Fallback: si no hay fecha_documento, intentar con periodo
    periodo = payroll.get("periodo", {})
    desde = periodo.get("desde")
    hasta = periodo.get("hasta")
    
    if dni and desde and hasta:
        return (dni, desde, hasta)
    
    return None


def merge_payrolls(payrolls: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Mergea múltiples nóminas del mismo trabajador y periodo en una sola.
    
    Args:
        payrolls: Lista de nóminas a mergear (debe tener al menos 1)
    
    Returns:
        Nómina mergeada
    """
    if not payrolls:
        raise ValueError("No se pueden mergear nóminas vacías")
    
    if len(payrolls) == 1:
        return payrolls[0]
    
    # Usar la primera nómina como base
    base = payrolls[0].copy()
    
    # Recopilar todos los archivos fuente
    source_files = []
    all_warnings = []
    
    # Inicializar listas de items por categoría
    all_devengo_items = []
    all_deduccion_items = []
    all_aportacion_items = []
    
    # Procesar todas las nóminas (incluyendo la base)
    for payroll in payrolls:
        source_file = payroll.get("source_json_file", "")
        if source_file:
            source_files.append(source_file)
        all_warnings.extend(payroll.get("warnings", []))
        
        # Agregar items de esta nómina
        for item in payroll.get("payroll_lines", []):
            if item["category"] == "devengo":
                all_devengo_items.append(item)
            elif item["category"] == "deduccion":
                all_deduccion_items.append(item)
            elif item["category"] == "aportacion_empresa":
                all_aportacion_items.append(item)
    
    # Recalcular totales sumando los items
    def sum_items(items: List[Dict[str, Any]]) -> float:
        return sum(item.get("amount", 0) for item in items)
    
    devengo_total = sum_items(all_devengo_items)
    deduccion_total = sum_items(all_deduccion_items)
    aportacion_total = sum_items(all_aportacion_items)
    liquido_total = devengo_total - deduccion_total
    
    # Actualizar base con valores mergeados
    base["devengo_total"] = devengo_total
    base["deduccion_total"] = deduccion_total
    base["aportacion_empresa_total"] = aportacion_total
    base["liquido_a_percibir"] = liquido_total
    
    # Combinar todos los items
    base["payroll_lines"] = all_devengo_items + all_deduccion_items + all_aportacion_items
    
    # Añadir warning sobre el merge
    merge_warning = f"Merged {len(payrolls)} payroll parts from files: {', '.join([f for f in source_files if f])}"
    all_warnings.append(merge_warning)
    base["warnings"] = all_warnings
    
    # Metadata del merge
    base["merged_from"] = source_files
    base["merged_parts_count"] = len(payrolls)
    base["is_merged"] = True
    
    # Determinar el tipo combinado
    types = {p.get("type") for p in payrolls}
    if "hybrid" in types or ("payslip" in types and "settlement" in types):
        base["type"] = "hybrid"
    elif "settlement" in types:
        base["type"] = "settlement"
    else:
        base["type"] = "payslip"

    # Usar el primer source_file y page como referencia
    base["source_file"] = payrolls[0].get("source_file")
    base["page"] = payrolls[0].get("page")
    
    return base


def group_and_merge_payrolls(payrolls: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Agrupa nóminas por trabajador y periodo, y mergea las que pertenecen a la misma nómina.
    
    Args:
        payrolls: Lista de nóminas mapeadas
    
    Returns:
        Lista de nóminas agrupadas y mergeadas
    """
    # Agrupar por clave (dni, desde, hasta)
    groups: Dict[tuple, List[Dict[str, Any]]] = {}
    
    for payroll in payrolls:
        key = get_payroll_key(payroll)
        if key:
            if key not in groups:
                groups[key] = []
            groups[key].append(payroll)
        else:
            # Si no tiene clave válida, añadirlo como individual
            groups[(id(payroll),)] = [payroll]
    
    # Mergear grupos
    merged_payrolls = []
    merge_count = 0
    
    for key, group in groups.items():
        if len(group) > 1:
            # Hay múltiples partes de la misma nómina, mergear
            merged = merge_payrolls(group)
            merged_payrolls.append(merged)
            merge_count += 1
            # Mostrar fecha_documento si está disponible, sino periodo.desde como fallback
            fecha = group[0].get('fecha_documento') or group[0].get('periodo', {}).get('desde', '?')
            print(f"  ↻ Merged {len(group)} parts for {group[0].get('trabajador', {}).get('dni', '?')} - {fecha}")
        else:
            # Solo una parte, añadir tal cual
            merged_payrolls.append(group[0])
    
    if merge_count > 0:
        print(f"\n  Total merges realizados: {merge_count}")
    
    return merged_payrolls


def process_json_folder(input_folder: Path) -> List[Dict[str, Any]]:
    """
    Procesa todos los JSONs en una carpeta y los mapea al formato de la DB.
    Solo procesa archivos que empiecen con "PAYSLIP" o "SETTLEMENT".
    Agrupa y mergea nóminas del mismo trabajador y fecha_documento.
    
    Args:
        input_folder: Carpeta con los JSONs
    
    Returns:
        Lista de diccionarios mapeados y mergeados
    """
    if not input_folder.exists():
        raise FileNotFoundError(f"La carpeta {input_folder} no existe")
    
    # Obtener todos los JSONs
    all_json_files = list(input_folder.glob("*.json"))
    
    # Filtrar solo los que empiezan con PAYSLIP o SETTLEMENT
    json_files = [f for f in all_json_files if is_valid_document_file(f.name)]
    
    if not json_files:
        skipped = len(all_json_files) - len(json_files)
        print(f"No se encontraron archivos JSON válidos (PAYSLIP/SETTLEMENT) en {input_folder}")
        if skipped > 0:
            print(f"  (Se omitieron {skipped} archivos que no empiezan con PAYSLIP o SETTLEMENT)")
        return []
    
    skipped_count = len(all_json_files) - len(json_files)
    print(f"Procesando {len(json_files)} archivos JSON válidos...")
    if skipped_count > 0:
        print(f"  (Omitiendo {skipped_count} archivos que no empiezan con PAYSLIP o SETTLEMENT)")
    
    mapped_payrolls = []
    errors = []
    
    for json_file in sorted(json_files):
        try:
            with open(json_file, "r", encoding="utf-8") as f:
                json_data = json.load(f)
            
            mapped = map_payslip_json_to_db_format(json_data, source_file=str(json_file.name))
            if mapped:
                mapped_payrolls.append(mapped)
                print(f"  ✓ {json_file.name}")
            else:
                print(f"  ✗ {json_file.name} (no es payslip o falta data)")
                errors.append(str(json_file.name))
        except Exception as e:
            print(f"  ✗ {json_file.name} (error: {e})", file=sys.stderr)
            errors.append(str(json_file.name))
    
    print(f"\nProcesados: {len(mapped_payrolls)} payslips")
    if errors:
        print(f"Errores: {len(errors)} archivos")
    
    # Agrupar y mergear nóminas del mismo trabajador y periodo
    print(f"\nAgrupando y mergeando nóminas...")
    merged_payrolls = group_and_merge_payrolls(mapped_payrolls)
    
    print(f"\nResultado final: {len(merged_payrolls)} nóminas (de {len(mapped_payrolls)} partes procesadas)")
    
    return merged_payrolls


def main():
    """Función principal del script"""
    if len(sys.argv) < 2:
        print(__doc__, file=sys.stderr)
        sys.exit(1)
    
    input_folder = Path(sys.argv[1])
    output_file = Path(sys.argv[2]) if len(sys.argv) > 2 else Path("payrolls_mapped.json")
    
    try:
        # Procesar carpeta
        mapped_payrolls = process_json_folder(input_folder)
        
        if not mapped_payrolls:
            print("No se encontraron payslips válidos para mapear.", file=sys.stderr)
            sys.exit(1)
        
        # Crear estructura de salida
        output_data = {
            "metadata": {
                "source_folder": str(input_folder),
                "total_payrolls": len(mapped_payrolls),
                "generated_at": datetime.now().isoformat(),
            },
            "payrolls": mapped_payrolls,
        }
        
        # Guardar JSON
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(output_data, f, ensure_ascii=False, indent=2)
        
        print(f"\n✓ JSON mapeado guardado en: {output_file}")
        print(f"  Total de payslips: {len(mapped_payrolls)}")
        
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()

