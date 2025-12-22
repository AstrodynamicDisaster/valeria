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
        "amount": float(item.get("importe", 0)),
        "is_taxable_income": not item_type.get("ind_is_exento_IRPF", False),
        "is_taxable_ss": item_type.get("ind_cotiza_ss", False),
        "is_sickpay": item_type.get("ind_is_IT_IL", False),
        "is_in_kind": item_type.get("ind_is_especie", False),
        "is_pay_advance": item_type.get("ind_is_anticipo", False),
        "is_seizure": item_type.get("ind_is_embargo", False),
    }


def map_payslip_json_to_db_format(json_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Mapea un JSON extraído de payslip al formato de la base de datos.
    
    Args:
        json_data: JSON completo de la extracción
    
    Returns:
        Diccionario con formato compatible con la DB o None si hay error
    """
    try:
        # Verificar que es un payslip
        if json_data.get("document_type") != "payslip":
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
        
        # Mapear payroll principal
        payroll = {
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
            
            # Metadata del archivo original
            "source_file": json_data.get("source_pdf"),
            "page": json_data.get("page"),
            "timestamp": json_data.get("timestamp"),
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


def process_json_folder(input_folder: Path) -> List[Dict[str, Any]]:
    """
    Procesa todos los JSONs en una carpeta y los mapea al formato de la DB.
    Solo procesa archivos que empiecen con "PAYSLIP" o "SETTLEMENT".
    
    Args:
        input_folder: Carpeta con los JSONs
    
    Returns:
        Lista de diccionarios mapeados
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
            
            mapped = map_payslip_json_to_db_format(json_data)
            if mapped:
                mapped["source_json_file"] = str(json_file.name)
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
    
    return mapped_payrolls


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

