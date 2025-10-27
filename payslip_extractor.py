# -*- coding: utf-8 -*-
"""
payslip_extractor.py

Deterministic payroll extractor for Spanish payslips (.txt from PyMuPDF).

Implements:
- Template detection for two observed templates (A: "20/21" family, B: "99" family)
- Deterministic parsing of company/employee, period, devengos/deducciones, employer contributions
- Totals reconciliation and warnings
- Optional LLM fallback interface (schema + recommended prompt) without making external calls

Usage (CLI):
    python payslip_extractor.py /path/to/21.txt
    python payslip_extractor.py /path/to/99.txt

Library usage:
    from payslip_extractor import extract_payslip
    data = extract_payslip(text)

Author: ChatGPT (GPT-5 Pro)
"""

from __future__ import annotations

import re
import json
import unicodedata
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from typing import Dict, List, Optional, Tuple
from pathlib import Path

# ------------------------
# Normalization utilities
# ------------------------

def _strip_accents(s: str) -> str:
    return ''.join(c for c in unicodedata.normalize('NFD', s) if unicodedata.category(c) != 'Mn')

def _norm_spaces(s: str) -> str:
    # collapse multiple spaces, keep line breaks
    return re.sub(r'[ \t]+', ' ', s).strip()

def parse_es_num(s: str) -> float:
    """
    Convert Spanish-formatted numbers to float.
    Accepts: "1.663,23", "641,58", "91,48", possibly with euro sign or spaces.
    """
    s = s.strip()
    s = s.replace('€', '').replace('EUR', '').replace(' ', '')
    # handle "1.663,23" -> "1663,23"
    s = s.replace('.', '')
    s = s.replace(',', '.')
    # ensure it looks like a float
    return float(s)

# ------------------------
# Helper regex patterns
# ------------------------

EMPRESA_ROW = re.compile(
    r'^(?P<razon>.+?)\s+(?P<cif>[A-Z]\d{7,8})\s+(?P<cta_pref>\d{1,3})\s+(?P<cta>\d{6,12})(?:\s+.*)?$',
    re.I | re.M
)

# Note: TRA_B captures name + DNI; NSS isn't always needed by the schema here.
TRAB_ROW = re.compile(
    r'^(?P<nombre>.+?)\s+(?P<dni>[A-Z0-9]\d{7,8}[A-Z])\b.*$',
    re.I | re.M
)

PERIODO = re.compile(
    r'Del\s+(?P<d1>\d{2})\s+de\s+(?P<m1>\d{2})\s+al\s+(?P<d2>\d{2})\s+de\s+(?P<m2>\d{2})\s+de\s+(?P<y>\d{4})',
    re.I | re.M
)

TOTAL_DEV_RE = re.compile(r'TOTAL\s+DEVENGO\s+(?P<num>\d{1,3}(?:\.\d{3})*,\d{2})', re.I)
TOTAL_DED_RE = re.compile(r'TOTAL\s+DEDU\.\s+(?P<num>\d{1,3}(?:\.\d{3})*,\d{2})', re.I)
LIQUIDO_RE   = re.compile(r'LIQUIDO\s+TOTAL\s+A\s+PERCIBIR\s+(?P<num>\d{1,3}(?:\.\d{3})*,\d{2})', re.I)

# Each line item ends with a Spanish-number amount.
ITEM = re.compile(
    r'^(?:\d{1,2},\d{2}\s+\d{1,2},\d{3,4}\s+)?'  # optional qty + unit price
    r'(?:[12]\s+)?'                              # optional '1' or '2' marker
    r'(?P<concepto>[A-Z0-9ÁÉÍÓÚÜÑ\/\.\-%,\s]+?)\s+'
    r'(?P<importe>\d{1,3}(?:\.\d{3})*,\d{2})\s*$',
    re.M
)

# ------------------------
# Alias and classification
# ------------------------

ALIASES: List[Tuple[re.Pattern, str]] = [
    (re.compile(r'^P\.?\.?PROP\.?\s*EXTRAS$', re.I), 'PRORRATA PAGAS EXTRA'),
    (re.compile(r'^P\.?PROP\.?\s*EXTRAS$', re.I), 'PRORRATA PAGAS EXTRA'),
    (re.compile(r'^MEJORAS?\s+VOLUNTARIAS?$', re.I), 'MEJORA VOLUNTARIA ABS'),
    (re.compile(r'^TBJO\.DOMINGOS/FESTIVOS$', re.I), 'TBJO.DOMINGOS/FESTIVOS'),
    (re.compile(r'^P\.?TRANSP\.\s*J\.?C\.?$', re.I), 'P.TRANSP. J.C.'),
]

def normalize_concept(concept: str) -> str:
    c = concept.strip()
    # squeeze spaces
    c = re.sub(r'\s{2,}', ' ', c)
    # Remove accidental page numbers at end
    c = re.sub(r'\s+\d{1,3}$', '', c)
    for pat, repl in ALIASES:
        if pat.match(c):
            return repl
    return c

def is_deduction(concept: str) -> bool:
    c = _strip_accents(concept.upper())
    return c.startswith('DTO.') or 'RETENCION IRPF' in c or 'RETENCI' in c or c.startswith('RETENCION')

# ------------------------
# Core parsing functions
# ------------------------

def _find_line_after(text: str, label_regex: str) -> Optional[str]:
    """Finds the next non-empty line after a label line (regex)."""
    m = re.search(label_regex, text, re.I | re.M)
    if not m:
        return None
    # get rest of text after label
    rest = text[m.end():]
    for line in rest.splitlines():
        if line.strip():
            return line.rstrip()
    return None

def parse_empresa_trabajador(text: str, warnings: List[str]) -> Tuple[Dict, Dict]:
    empresa = {"razon_social": None, "cif": None}
    trabajador = {"nombre": None, "dni": None}

    # Empresa
    emp_line = _find_line_after(text, r'EMPRESA\s*\(.*raz[oó]n.*\)\s*C\.?I\.?F\.?.*')
    if not emp_line:
        # fallback - search any line that matches EMPRESA_ROW
        m = EMPRESA_ROW.search(text)
        emp_line = m.group(0) if m else None
    if emp_line:
        m = EMPRESA_ROW.match(emp_line.strip())
        if m:
            empresa["razon_social"] = _norm_spaces(m.group('razon'))
            empresa["cif"] = m.group('cif').upper()
        else:
            warnings.append("No se pudo parsear la línea de empresa con el patrón esperado.")
    else:
        warnings.append("No se encontró bloque de empresa.")

    # Trabajador
    tra_line = _find_line_after(text, r'TRABAJADOR\s*\(.*nombre.*\).*D\.?N\.?I\.?.*')
    if not tra_line:
        m = TRAB_ROW.search(text)
        tra_line = m.group(0) if m else None
    if tra_line:
        m = TRAB_ROW.match(tra_line.strip())
        if m:
            trabajador["nombre"] = _norm_spaces(m.group('nombre'))
            trabajador["dni"] = m.group('dni').upper()
        else:
            warnings.append("No se pudo parsear la línea de trabajador con el patrón esperado.")
    else:
        warnings.append("No se encontró bloque de trabajador.")

    return empresa, trabajador

def parse_periodo(text: str, warnings: List[str]) -> Dict:
    periodo = {"desde": None, "hasta": None, "dias": None}
    m = PERIODO.search(text)
    if not m:
        warnings.append("No se encontró el patrón de periodo 'Del ... al ... de AAAA'.")
        return periodo

    d1 = m.group('d1'); m1 = m.group('m1'); d2 = m.group('d2'); m2 = m.group('m2'); y = m.group('y')
    desde = f"{y}-{m1}-{d1}"
    hasta = f"{y}-{m2}-{d2}"
    periodo["desde"] = desde
    periodo["hasta"] = hasta

    # Extract declared DIAS (last integer near the F.COBRO/DIAS block), best effort
    dias_declared = None
    # search in the next ~100 chars for an integer
    tail = text[m.end(): m.end()+120]
    m_dias = re.search(r'\b(\d{1,2})\b', tail)
    if m_dias:
        try:
            dias_declared = int(m_dias.group(1))
        except:
            dias_declared = None

    # compute actual inclusive days
    try:
        d_desde = datetime.strptime(desde, "%Y-%m-%d").date()
        d_hasta = datetime.strptime(hasta, "%Y-%m-%d").date()
        dias_calc = (d_hasta - d_desde).days + 1
    except Exception:
        dias_calc = None

    if dias_calc is not None:
        periodo["dias"] = dias_calc
        if dias_declared is not None and dias_declared != dias_calc:
            warnings.append(f"Periodo corregido a {dias_calc} días para coincidir con la fecha final del periodo.")
    else:
        periodo["dias"] = dias_declared

    return periodo

def _section_between(text: str, start_pat: str, end_pat: str) -> str:
    m1 = re.search(start_pat, text, re.I | re.M | re.S)
    if not m1:
        return ''
    start = m1.end()
    m2 = re.search(end_pat, text[start:], re.I | re.M | re.S)
    if not m2:
        return text[start:]
    return text[start:start+m2.start()]

def parse_items(text: str, warnings: List[str]) -> Tuple[List[Dict], List[Dict]]:
    # between CONCEPTO header and DETERMINACION DE LAS BASES
    block = _section_between(
        text,
        r'^\s*CONCEPTO\s*$',
        r'DETERMINACI[ÓO]N?\s+DE\s+LAS\s+BASES'
    )

    devengos = []; dedus = []

    for m in ITEM.finditer(block):
        concepto_raw = m.group('concepto').strip()
        importe = parse_es_num(m.group('importe'))
        concepto = normalize_concept(concepto_raw)

        if is_deduction(concepto):
            dedus.append({"concepto": concepto, "importe": round(importe, 2)})
        else:
            devengos.append({"concepto": concepto, "importe": round(importe, 2)})

    if not devengos and not dedus:
        warnings.append("No se pudieron extraer líneas de devengo/deducción del bloque principal.")

    return devengos, dedus

def parse_totales(text: str, warnings: List[str]) -> Dict:
    totales = {"devengo_total": None, "deduccion_total": None, "liquido_a_percibir": None, "aportacion_empresa_total": None}

    m = TOTAL_DEV_RE.search(text)
    if m:
        totales["devengo_total"] = round(parse_es_num(m.group('num')), 2)
    else:
        warnings.append("No se encontró TOTAL DEVENGO.")

    m = TOTAL_DED_RE.search(text)
    if m:
        totales["deduccion_total"] = round(parse_es_num(m.group('num')), 2)
    else:
        warnings.append("No se encontró TOTAL DEDU.")

    m = LIQUIDO_RE.search(text)
    if m:
        totales["liquido_a_percibir"] = round(parse_es_num(m.group('num')), 2)
    else:
        warnings.append("No se encontró LIQUIDO TOTAL A PERCIBIR.")

    return totales

def _numbers_on_line(line: str) -> List[float]:
    return [parse_es_num(x) for x in re.findall(r'\d{1,3}(?:\.\d{3})*,\d{2}', line)]

def parse_aportacion_empresa(text: str, warnings: List[str]) -> List[Dict]:
    # Section from APORTACIÓN EMPRESA to BASE SUJETA A RETENCION...
    block = _section_between(
        text,
        r'APORTACI[ÓO]N\s+EMPRESA',
        r'BASE\s+SUJETA\s+A\s+RETENC[IÓO]N\s+DEL\s+IRPF'
    )
    if not block.strip():
        warnings.append("No se encontró bloque de APORTACIÓN EMPRESA.")
        return []

    lines = [l.strip() for l in block.splitlines() if l.strip()]

    # find base parts for CC (optional)
    n_remun = None; n_prorr = None; base_total = None

    for l in lines:
        if re.search(r'REMUNERACI[ÓO]N\s+MENSUAL', l, re.I):
            nums = _numbers_on_line(l)
            if nums: n_remun = nums[-1]
        elif re.search(r'PRORRATA\s+PAGAS?\s+EXTRA', l, re.I):
            nums = _numbers_on_line(l)
            if nums: n_prorr = nums[-1]

    if n_remun is not None and n_prorr is not None:
        base_total = round(n_remun + n_prorr, 2)

    contribs: List[Dict] = []
    last_base = base_total

    # Map lines to contributions
    # CC line often appears as "TOTAL <base> <tipo> <importe>"
    for l in lines:
        up = _strip_accents(l.upper())
        if up.startswith('COTIZACION ADICIONAL') or up.startswith('COTIZACIÓN ADICIONAL'):
            continue

        if re.match(r'^TOTAL\b', l, re.I):
            nums = _numbers_on_line(l)
            if len(nums) == 3:
                b, a, p = nums  # but order may be swapped (amount vs percent)
                # decide percent vs amount
                # Try both
                tipo1, imp1 = p, a  # assume a is amount, p is percent (typical if numbers extracted in swapped order)
                tipo2, imp2 = a, p
                # choose the pair that fits base*tipo≈importe
                if abs(b * (tipo1/100.0) - imp1) <= 0.1:
                    tipo, imp = tipo1, imp1
                elif abs(b * (tipo2/100.0) - imp2) <= 0.1:
                    tipo, imp = tipo2, imp2
                else:
                    # fallback: choose the smaller as percent
                    tipo, imp = (min(a, p), max(a, p))
                contribs.append({"concepto": "CONTINGENCIAS COMUNES", "base": round(b,2), "tipo": round(tipo,2), "importe": round(imp,2)})
                last_base = b
            elif len(nums) == 2 and base_total is not None:
                # rare case: only percent and amount, take base_total
                a, p = nums
                tipo, imp = (min(a, p), max(a, p))
                contribs.append({"concepto": "CONTINGENCIAS COMUNES", "base": round(base_total,2), "tipo": round(tipo,2), "importe": round(imp,2)})
                last_base = base_total
            continue

        # Other known concepts
        for concept_key in ["AT Y EP", "DESEMPLEO", "FORMACIÓN PROFESIONAL", "FORMACION PROFESIONAL", "FONDO GARANTÍA SALARIAL", "FONDO GARANTIA SALARIAL"]:
            if re.search(r'\b' + re.escape(concept_key) + r'\b', l, re.I):
                cap_concept = "FORMACIÓN PROFESIONAL" if "FORMACION" in concept_key.upper() else (
                    "FONDO GARANTÍA SALARIAL" if "GARANTIA" in concept_key.upper() else concept_key
                )
                nums = _numbers_on_line(l)
                if len(nums) == 3:
                    b, a, p = nums
                    # decide percent vs amount (swap-aware)
                    tipo1, imp1 = p, a
                    tipo2, imp2 = a, p
                    if abs(b * (tipo1/100.0) - imp1) <= 0.1:
                        tipo, imp = tipo1, imp1
                    elif abs(b * (tipo2/100.0) - imp2) <= 0.1:
                        tipo, imp = tipo2, imp2
                    else:
                        tipo, imp = (min(a, p), max(a, p))
                    contribs.append({"concepto": cap_concept, "base": round(b,2), "tipo": round(tipo,2), "importe": round(imp,2)})
                    last_base = b
                elif len(nums) == 2 and last_base is not None:
                    a, p = nums
                    # choose which is percent / amount
                    # prefer smaller as percent
                    tipo, imp = (min(a, p), max(a, p))
                    contribs.append({"concepto": cap_concept, "base": round(last_base,2), "tipo": round(tipo,2), "importe": round(imp,2)})
                elif len(nums) == 1 and last_base is not None:
                    # Unusual line with only amount; we cannot infer percent.
                    contribs.append({"concepto": cap_concept, "base": round(last_base,2), "tipo": None, "importe": round(nums[0],2)})
                else:
                    warnings.append(f"No se pudieron mapear números para '{cap_concept}'.")
                break

    if not contribs:
        warnings.append("No se extrajeron aportaciones de empresa.")

    return contribs

def detect_template(text: str) -> str:
    up = _strip_accents(text.upper())
    if "COTIZACION ADICIONAL DE SOLIDARIDAD" in up or "COTIZACIÓN ADICIONAL DE SOLIDARIDAD" in up:
        return "A"  # template like 20/21
    return "B"      # template like 99 (default)

# ------------------------
# Validation & assembly
# ------------------------

def validate_and_merge(devengos, dedus, contribs, totales, warnings):
    # sum checks
    def sum_list(lst, key='importe'):
        return round(sum(x.get(key) or 0 for x in lst), 2)

    dev_sum = sum_list(devengos)
    ded_sum = sum_list(dedus)
    emp_sum = sum_list(contribs)

    if totales.get('devengo_total') is not None:
        if abs(dev_sum - totales['devengo_total']) > 0.02:
            warnings.append(f"Suma de devengos ({dev_sum}) no coincide con TOTAL DEVENGO ({totales['devengo_total']}).")
    else:
        totales['devengo_total'] = dev_sum

    if totales.get('deduccion_total') is not None:
        if abs(ded_sum - totales['deduccion_total']) > 0.02:
            warnings.append(f"Suma de deducciones ({ded_sum}) no coincide con TOTAL DEDU. ({totales['deduccion_total']}).")
    else:
        totales['deduccion_total'] = ded_sum

    if totales.get('liquido_a_percibir') is not None and totales.get('devengo_total') is not None and totales.get('deduccion_total') is not None:
        net_calc = round(totales['devengo_total'] - totales['deduccion_total'], 2)
        if abs(net_calc - totales['liquido_a_percibir']) > 0.02:
            warnings.append(f"Liquido calculado ({net_calc}) difiere del informado ({totales['liquido_a_percibir']}).")
    # employer total
    totales['aportacion_empresa_total'] = emp_sum if emp_sum else None
    return totales

# ------------------------
# LLM fallback (interface only)
# ------------------------

LLM_SYSTEM_PROMPT = """You extract structured data from Spanish payslips.
- Only use information present in the provided text; never guess.
- Numbers use Spanish format (1.663,23). Convert to JSON numbers using dot decimal (1663.23).
- Dates “Del DD de MM al DD de MM de YYYY” must become YYYY-MM-DD.
- Classify line items in the main table as:
  * devengos (e.g., SALARIO BASE, INCENTIVOS, PLUS, TBJO.DOMINGOS/FESTIVOS, PRORRATA PAGAS EXTRA / P.PROP. EXTRAS, MEJORA VOLUNTARIA ABS)
  * deducciones (e.g., lines starting with DTO., RETENCION IRPF, ANTICIPO, EMBARGO).
- Employer contributions are ONLY those under the “APORTACIÓN EMPRESA” block (e.g., CONTINGENCIAS COMUNES, AT Y EP, DESEMPLEO, FORMACIÓN PROFESIONAL, FONDO GARANTÍA SALARIAL).
  * If a line has two numbers besides the base, identify which is the percent vs the amount by checking: amount ≈ base * percent/100.
- Return strictly the JSON object following the provided schema.
- If something is missing or inconsistent, include a clear message in `warnings`.
"""

LLM_SCHEMA_DOC = {
    "empresa": {"razon_social": "string", "cif": "string"},
    "trabajador": {"nombre": "string", "dni": "string"},
    "periodo": {"desde": "YYYY-MM-DD", "hasta": "YYYY-MM-DD", "dias": "int"},
    "devengo_items": [{"concepto": "string", "importe": "number"}],
    "deduccion_items": [{"concepto": "string", "importe": "number"}],
    "aportacion_empresa_items": [{"concepto": "string", "base": "number", "tipo": "number", "importe": "number"}],
    "totales": {"devengo_total": "number", "deduccion_total": "number", "aportacion_empresa_total": "number", "liquido_a_percibir": "number"},
    "warnings": ["string"]
}

def llm_fallback_extract(text: str, client=None) -> Optional[dict]:
    """
    Placeholder for integrating an LLM fallback (e.g., GPT-4o mini).
    Implementers can pass a pre-configured client and call it here.
    This function should return a dict matching LLM_SCHEMA_DOC or None on failure.
    """
    # Example (pseudo):
    # if client is not None:
    #     resp = client.chat.completions.create(
    #        model="gpt-4o-mini",
    #        messages=[{"role":"system","content":LLM_SYSTEM_PROMPT},
    #                  {"role":"user","content": f"=== PAYSLIP TEXT BEGIN ===\n{text}\n=== PAYSLIP TEXT END ==="}],
    #        response_format={"type":"json_object"}
    #     )
    #     return json.loads(resp.choices[0].message.content)
    return None

# ------------------------
# Public API
# ------------------------

def extract_payslip(text: str, use_llm: bool=False, llm_client=None) -> dict:
    """
    Deterministically extract payslip data. Optionally use LLM fallback.
    """
    warnings: List[str] = []

    template = detect_template(text)

    empresa, trabajador = parse_empresa_trabajador(text, warnings)
    periodo = parse_periodo(text, warnings)
    devengos, dedus = parse_items(text, warnings)
    totales = parse_totales(text, warnings)
    contribs = parse_aportacion_empresa(text, warnings)

    totales = validate_and_merge(devengos, dedus, contribs, totales, warnings)

    # If critical fields missing, optional LLM fallback
    need_fallback = False
    required_present = all([empresa.get("razon_social"), empresa.get("cif"),
                            trabajador.get("nombre"), trabajador.get("dni"),
                            periodo.get("desde"), periodo.get("hasta")])
    if not required_present:
        need_fallback = True
    if totales.get("devengo_total") is None or totales.get("deduccion_total") is None or totales.get("liquido_a_percibir") is None:
        need_fallback = True
    if (not devengos) or (not dedus):
        # optional trigger
        need_fallback = True

    if use_llm and need_fallback:
        llm_data = llm_fallback_extract(text, client=llm_client)
        if llm_data:
            # merge only missing fields
            if not empresa.get("razon_social") and llm_data.get("empresa"): empresa["razon_social"] = llm_data["empresa"].get("razon_social")
            if not empresa.get("cif") and llm_data.get("empresa"): empresa["cif"] = llm_data["empresa"].get("cif")
            if not trabajador.get("nombre") and llm_data.get("trabajador"): trabajador["nombre"] = llm_data["trabajador"].get("nombre")
            if not trabajador.get("dni") and llm_data.get("trabajador"): trabajador["dni"] = llm_data["trabajador"].get("dni")
            if (not periodo.get("desde") or not periodo.get("hasta")) and llm_data.get("periodo"):
                periodo["desde"] = periodo.get("desde") or llm_data["periodo"].get("desde")
                periodo["hasta"] = periodo.get("hasta") or llm_data["periodo"].get("hasta")
                periodo["dias"] = periodo.get("dias") or llm_data["periodo"].get("dias")
            if not devengos and llm_data.get("devengo_items"):
                devengos = llm_data["devengo_items"]
            if not dedus and llm_data.get("deduccion_items"):
                dedus = llm_data["deduccion_items"]
            if not contribs and llm_data.get("aportacion_empresa_items"):
                contribs = llm_data["aportacion_empresa_items"]
            if totales.get("devengo_total") is None and llm_data.get("totales"):
                totales["devengo_total"] = llm_data["totales"].get("devengo_total")
            if totales.get("deduccion_total") is None and llm_data.get("totales"):
                totales["deduccion_total"] = llm_data["totales"].get("deduccion_total")
            if totales.get("liquido_a_percibir") is None and llm_data.get("totales"):
                totales["liquido_a_percibir"] = llm_data["totales"].get("liquido_a_percibir")
            if llm_data.get("warnings"):
                warnings.extend(llm_data["warnings"])

            totales = validate_and_merge(devengos, dedus, contribs, totales, warnings)

    result = {
        "empresa": {"razon_social": empresa.get("razon_social"), "cif": empresa.get("cif")},
        "trabajador": {"nombre": trabajador.get("nombre"), "dni": trabajador.get("dni")},
        "periodo": {"desde": periodo.get("desde"), "hasta": periodo.get("hasta"), "dias": periodo.get("dias")},
        "devengo_items": devengos,
        "deduccion_items": dedus,
        "aportacion_empresa_items": contribs,
        "totales": totales,
        "warnings": warnings
    }
    return result

# ------------------------
# CLI for quick checks
# ------------------------

def _main():
    import sys
    if len(sys.argv) < 2:
        print("Usage: python payslip_extractor.py /path/to/payslip.txt [--json]")
        return
    p = sys.argv[1]
    text = Path(p).read_text(encoding="utf-8", errors="ignore")
    data = extract_payslip(text, use_llm=False)
    if "--json" in sys.argv:
        print(json.dumps(data, ensure_ascii=False, indent=2))
    else:
        print(json.dumps(data, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    _main()
