import json
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime

# Reuse logic from V1 where possible
from core.vision_model.scripts.map_json_to_db import (
    map_item_to_payroll_line, 
    safe_decimal,
    group_and_merge_payrolls
)

def parse_yyyy_mm_dd(value: Optional[str]) -> Optional[datetime]:
    """Helper to parse YYYY-MM-DD strings."""
    if not value or not isinstance(value, str):
        return None
    try:
        return datetime.strptime(value, "%Y-%m-%d")
    except ValueError:
        return None


def map_payslip_v2_to_db_format(json_data: Dict[str, Any], source_file: str) -> List[Dict[str, Any]]:
    """
    Maps a V2 JSON (which contains a list of logical_documents) to DB format.
    Each logical document becomes an independent payroll entry.
    """
    mapped_payrolls = []
    
    source_pdf = json_data.get("source_pdf")
    logical_docs = json_data.get("logical_documents", [])
    
    for i, doc in enumerate(logical_docs):
        doc_type = doc.get("type")
        data = doc.get("data", {})
        
        totales = data.get("totales", {})
        periodo = data.get("periodo", {})
        empresa = data.get("empresa", {})
        trabajador = data.get("trabajador", {})
        
        # Mapear periodo
        # For settlements, periodo might be missing or different.
        # Ensure we have at least dictionary structure
        if not periodo: 
            periodo = {}

        # Para settlements sin periodo, derivarlo desde fecha_cese (del 1 del mes hasta fecha_cese)
        if doc_type == "settlement" and not periodo.get("desde"):
            fecha_cese_raw = data.get("fecha_cese")
            fecha_cese_dt = parse_yyyy_mm_dd(fecha_cese_raw)
            if fecha_cese_dt:
                desde_dt = fecha_cese_dt.replace(day=1)
                dias = (fecha_cese_dt - desde_dt).days + 1
                periodo = {
                    "desde": desde_dt.strftime("%Y-%m-%d"),
                    "hasta": fecha_cese_dt.strftime("%Y-%m-%d"),
                    "dias": dias,
                }

        periodo_mapped = {
            "desde": periodo.get("desde"),
            "hasta": periodo.get("hasta"),
            "dias": periodo.get("dias"),
        }
        
        # Determine payroll type for DB
        payroll_type = "payslip"
        if doc_type == "settlement":
            payroll_type = "settlement"
            # For settlements, sometimes 'fecha_cese' or 'fecha_liquidacion' is relevant
            # If 'hasta' is missing in period, we could fallback to 'fecha_cese'
            if not periodo_mapped["hasta"]:
                periodo_mapped["hasta"] = data.get("fecha_cese") or data.get("fecha_liquidacion")
                
        elif totales.get("contains_settlement"):
            payroll_type = "hybrid"

        # Map main payroll object
        payroll = {
            "type": payroll_type,
            "empresa": {
                "razon_social": empresa.get("razon_social"),
                "cif": empresa.get("cif"),
            },
            "trabajador": {
                "nombre": trabajador.get("nombre"),
                "dni": trabajador.get("dni"),
                "ss_number": trabajador.get("ss_number"),
            },
            "periodo": periodo_mapped,
            "devengo_total": safe_decimal(totales.get("devengo_total")),
            "deduccion_total": safe_decimal(totales.get("deduccion_total")),
            "aportacion_empresa_total": safe_decimal(totales.get("aportacion_empresa_total")),
            "liquido_a_percibir": safe_decimal(totales.get("liquido_a_percibir")),
            "prorrata_pagas_extra": safe_decimal(totales.get("prorrata_pagas_extra_total")),
            "base_cc": safe_decimal(totales.get("base_contingencias_comunes_total")),
            "base_at_ep": safe_decimal(totales.get("base_accidente_de_trabajo_y_desempleo_total")),
            "base_irpf": safe_decimal(totales.get("base_retencion_irpf_total")),
            "tipo_irpf": safe_decimal(totales.get("porcentaje_retencion_irpf")),
            "warnings": data.get("warnings", []) + json_data.get("global_warnings", []),
            "fecha_documento": data.get("fecha_documento"),
            "source_file": source_pdf,
            "page": f"Logical Doc {i+1} of {len(logical_docs)} (V2)",
            "processing_time": json_data.get("processing_time_seconds"),
            "parsing_cost": json_data.get("parsing_cost_usd"),
        }
        
        # Map line items
        payroll_lines = []
        for item in data.get("devengo_items", []):
            payroll_lines.append(map_item_to_payroll_line(item, "devengo"))
        for item in data.get("deduccion_items", []):
            payroll_lines.append(map_item_to_payroll_line(item, "deduccion"))
        for item in data.get("aportacion_empresa_items", []):
            payroll_lines.append(map_item_to_payroll_line(item, "aportacion_empresa"))
        
        payroll["payroll_lines"] = payroll_lines
        mapped_payrolls.append(payroll)
        
    return mapped_payrolls

def process_v2_folder(input_folder: Path) -> List[Dict[str, Any]]:
    """Processes all V2 JSONs in a folder."""
    all_mapped = []
    json_files = list(input_folder.glob("V2_*.json"))
    
    print(f"Mapeando {len(json_files)} archivos JSON V2...")
    for json_file in sorted(json_files):
        try:
            with open(json_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            mapped = map_payslip_v2_to_db_format(data, str(json_file.name))
            all_mapped.extend(mapped)
            print(f"  ✓ {json_file.name} ({len(mapped)} docs)")
        except Exception as e:
            print(f"  ✗ {json_file.name} (Error: {e})")
            
    return all_mapped

def main():
    if len(sys.argv) < 2:
        print("Uso: python -m core.vision_model.scripts.map_json_to_db_v2 <v2_folder> [output_file]")
        sys.exit(1)
        
    input_folder = Path(sys.argv[1])
    output_file = Path(sys.argv[2]) if len(sys.argv) > 2 else Path("results_parsing/payrolls_mapped_v2.json")
    
    payrolls = process_v2_folder(input_folder)
    
    if payrolls:
        print("\nAgrupando y mergeando nóminas (deduplicación)...")
        # Apply the same deduplication logic as V1 (useful if multiple JSONs cover the same worker/period)
        final_payrolls = group_and_merge_payrolls(payrolls)
    else:
        final_payrolls = []
    
    output_data = {
        "metadata": {
            "source_folder": str(input_folder),
            "total_extracted_docs": len(payrolls),
            "total_merged_docs": len(final_payrolls),
            "generated_at": datetime.now().isoformat(),
        },
        "payrolls": final_payrolls,
    }
    
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)
    print(f"\n✓ Mapeo V2 completado: {output_file}")
    print(f"  Total documentos finales: {len(final_payrolls)}")

if __name__ == "__main__":
    main()
