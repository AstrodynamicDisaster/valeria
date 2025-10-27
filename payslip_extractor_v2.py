# -*- coding: utf-8 -*-
from __future__ import annotations
import re, json, unicodedata
from typing import List, Dict, Optional, Tuple
from datetime import datetime

def _strip_accents(s: str) -> str:
    return ''.join(c for c in unicodedata.normalize('NFD', s) if unicodedata.category(c) != 'Mn')

def _norm_spaces(s: str) -> str:
    return re.sub(r'[ \t]+', ' ', s).strip()

def parse_es_num(s: str) -> float:
    s = s.strip().replace('€','').replace('EUR','').replace(' ', '')
    s = s.replace('.', '').replace(',', '.')
    return float(s)

EMPRESA_ROW = re.compile(
    r'^(?P<razon>.+?)\s+(?P<cif>[A-Z]\d{7,8})\s+\d{1,3}\s+\d{6,12}.*$',
    re.I | re.M
)
TRAB_ROW = re.compile(
    r'^(?P<nombre>.+?)\s+(?P<dni>[A-Z0-9]\d{7,8}[A-Z])\b.*$',
    re.I | re.M
)

PERIODO = re.compile(
    r'Del\s+(?P<d1>\d{2})\s+de\s+(?P<m1>\d{2})\s+al\s+(?P<d2>\d{2})\s+de\s+(?P<m2>\d{2})\s+de\s+(?P<y>\d{4})',
    re.I | re.M
)
DIAS_AFTER_COBRO = re.compile(r'F\.?\.?COBRO.*?\b\d{2}-\d{2}-\d{4}\s+(?P<dias>\d{1,2})', re.I | re.S)

TOTAL_DEV_RE = re.compile(r'TOTAL\s+DEVENGO\s+(?P<num>\d{1,3}(?:\.\d{3})*,\d{2})', re.I)
TOTAL_DED_RE = re.compile(r'TOTAL\s+DEDU\.\s+(?P<num>\d{1,3}(?:\.\d{3})*,\d{2})', re.I)
LIQUIDO_RE   = re.compile(r'LIQUIDO\s+TOTAL\s+A\s+PERCIBIR\s+(?P<num>\d{1,3}(?:\.\d{3})*,\d{2})', re.I)

ALIASES = [
    (re.compile(r'^P\.?\.?PROP\.?\s*EXTRAS$', re.I), 'PRORRATA PAGAS EXTRA'),
    (re.compile(r'^MEJORAS?\s+VOLUNTARIAS?$', re.I), 'MEJORA VOLUNTARIA ABS'),
    (re.compile(r'^TBJO\.DOMINGOS/FESTIVOS$', re.I), 'TBJO.DOMINGOS/FESTIVOS'),
    (re.compile(r'^P\.?TRANSP\.\s*J\.?C\.?$', re.I), 'P.TRANSP. J.C.'),
]

def normalize_concept(concept: str) -> str:
    c = concept.strip()
    c = re.sub(r'\s{2,}', ' ', c)
    for pat, repl in ALIASES:
        if pat.match(c): return repl
    return c

def is_deduction(concept: str) -> bool:
    c = _strip_accents(concept.upper())
    return c.startswith('DTO.') or 'RETENCION IRPF' in c or c.startswith('RETENCION') or 'RETENCI' in c

def detect_template(text: str) -> str:
    up = _strip_accents(text.upper())
    if "COTIZACION ADICIONAL DE SOLIDARIDAD" in up or "COTIZACIÓN ADICIONAL DE SOLIDARIDAD" in up:
        return "A"  # like 20/21
    return "B"      # like 99

def _section_between(text: str, start_pat: str, end_pat: str) -> str:
    m1 = re.search(start_pat, text, re.I | re.M | re.S)
    if not m1: return ''
    start = m1.end()
    m2 = re.search(end_pat, text[start:], re.I | re.M | re.S)
    if not m2: return text[start:]
    return text[start:start+m2.start()]

def parse_empresa_trabajador(text: str, warnings: List[str]):
    empresa = {"razon_social": None, "cif": None}
    trabajador = {"nombre": None, "dni": None}

    emp_line = None
    # Try next line after label
    m = re.search(r'EMPRESA\s*\(.*raz[oó]n.*\)\s*C\.?I\.?F', text, re.I)
    if m:
        rest = text[m.end():].splitlines()
        for l in rest:
            if l.strip(): emp_line = l.strip(); break
    # Fallback: search any matching line
    m2 = EMPRESA_ROW.search(text) if not emp_line else EMPRESA_ROW.match(emp_line)
    if not m2 and emp_line:
        m2 = EMPRESA_ROW.search(emp_line)
    if not m2:
        m2 = EMPRESA_ROW.search(text)
    if m2:
        empresa["razon_social"] = _norm_spaces(m2.group('razon'))
        empresa["cif"] = m2.group('cif').upper()
    else:
        warnings.append("No se pudo leer la línea de EMPRESA.")

    tra_line = None
    m = re.search(r'TRABAJADOR\s*\(.*nombre.*\).*D\.?N\.?I', text, re.I)
    if m:
        rest = text[m.end():].splitlines()
        for l in rest:
            if l.strip(): tra_line = l.strip(); break
    m2 = TRAB_ROW.match(tra_line) if tra_line else TRAB_ROW.search(text)
    if m2:
        trabajador["nombre"] = _norm_spaces(m2.group('nombre'))
        trabajador["dni"] = m2.group('dni').upper()
    else:
        warnings.append("No se pudo leer la línea de TRABAJADOR.")

    return empresa, trabajador

def parse_periodo(text: str, warnings: List[str]) -> Dict:
    periodo = {"desde": None, "hasta": None, "dias": None}
    m = PERIODO.search(text)
    if not m:
        warnings.append("No se encontró el patrón de periodo.")
        return periodo
    d1, m1, d2, m2, y = m.group('d1'), m.group('m1'), m.group('d2'), m.group('m2'), m.group('y')
    periodo["desde"] = f"{y}-{m1}-{d1}"
    periodo["hasta"] = f"{y}-{m2}-{d2}"

    dcalc = None
    try:
        dcalc = (datetime.strptime(periodo["hasta"], "%Y-%m-%d") - datetime.strptime(periodo["desde"], "%Y-%m-%d")).days + 1
    except:
        pass

    md = DIAS_AFTER_COBRO.search(text)
    if md:
        dias = int(md.group('dias'))
        if dcalc is not None and dias != dcalc:
            warnings.append(f"Periodo corregido a {dcalc} días para coincidir con la fecha final del periodo.")
            periodo["dias"] = dcalc
        else:
            periodo["dias"] = dias
    else:
        periodo["dias"] = dcalc
    return periodo

# Item parsing A: single-line items with trailing amount
ITEM = re.compile(
    r'^(?:\d{1,2},\d{2}\s+\d{1,2},\d{3,4}\s+)?(?:[12]\s+)?(?P<concepto>[A-Z0-9ÁÉÍÓÚÜÑ\/\.\-%,\s]+?)\s+(?P<importe>\d{1,3}(?:\.\d{3})*,\d{2})\s*$',
    re.M
)
def parse_items_A(text: str, warnings: List[str]):
    block = _section_between(text, r'^\s*CONCEPTO\s*$', r'DETERMINACI[ÓO]N?\s+DE\s+LAS\s+BASES')
    devs, deds = [], []
    for m in ITEM.finditer(block):
        concepto = normalize_concept(m.group('concepto'))
        amt = parse_es_num(m.group('importe'))
        (deds if is_deduction(concepto) else devs).append({"concepto": concepto, "importe": round(amt,2)})
    if not devs and not deds:
        warnings.append("No se extrajeron items en el bloque principal (A).")
    return devs, deds

# Item parsing B: reconstruction when columns are out-of-order (99.txt)
def parse_items_B(text: str, warnings: List[str]):
    block = _section_between(text, r'CONCEPTO', r'DETERMINACI[ÓO]N?\s+DE\s+LAS\s+BASES')
    lines = [l.strip() for l in block.splitlines() if l.strip()]
    # Remove header tokens
    headers = re.compile(r'^(CUANTIA|PRECIO|DEVENGO|DEDUCCION|CONCEPTO|1\s+PERCEPCIONES|2\s+PERCEPCIONES)$', re.I)
    clean = [l for l in lines if not headers.match(l)]
    # Helper checks
    two_dec = re.compile(r'^\d{1,3}(?:\.\d{3})*,\d{2}$')     # totals
    four_dec = re.compile(r'^\d{1,2},\d{4}$')                # unit price
    is_concept = lambda s: re.search(r'[A-ZÁÉÍÓÚÜÑ]', s) and not two_dec.match(s) and not four_dec.match(s) and not s.upper().startswith('TOTAL')
    devs, deds = [], []
    used_amounts = set()
    for i, s in enumerate(clean):
        if is_concept(s):
            concepto = normalize_concept(s)
            # find nearest 2-decimal amount within a small window (prefer after)
            cand = []
            for j in range(max(0, i-4), min(len(clean), i+5)):
                if j==i or j in used_amounts: continue
                if two_dec.match(clean[j]):
                    bias = 0 if j > i else 1
                    cand.append((bias, abs(j-i), j))
            if cand:
                cand.sort(key=lambda x: (x[0], x[1]))
                _, _, jbest = cand[0]
                amt = parse_es_num(clean[jbest])
                used_amounts.add(jbest)
                (deds if is_deduction(concepto) else devs).append({"concepto": concepto, "importe": round(amt,2)})
    if not devs and not deds:
        # fallback to A-style as last resort
        return parse_items_A(text, warnings)
    return devs, deds

def parse_totales(text: str, warnings: List[str]) -> Dict:
    totales = {"devengo_total": None, "deduccion_total": None, "liquido_a_percibir": None, "aportacion_empresa_total": None}
    m = TOTAL_DEV_RE.search(text)
    if m: totales["devengo_total"] = round(parse_es_num(m.group('num')),2)
    else: warnings.append("No se encontró TOTAL DEVENGO.")
    m = TOTAL_DED_RE.search(text)
    if m: totales["deduccion_total"] = round(parse_es_num(m.group('num')),2)
    else: warnings.append("No se encontró TOTAL DEDU.")
    m = LIQUIDO_RE.search(text)
    if m: totales["liquido_a_percibir"] = round(parse_es_num(m.group('num')),2)
    else: warnings.append("No se encontró LIQUIDO TOTAL A PERCIBIR.")
    return totales

def _numbers_on_line(line: str) -> List[float]:
    return [parse_es_num(x) for x in re.findall(r'\d{1,3}(?:\.\d{3})*,\d{2}', line)]

def parse_aportacion_empresa(text: str, warnings: List[str]) -> List[Dict]:
    block = _section_between(text, r'APORTACI[ÓO]N\s+EMPRESA', r'BASE\s+SUJETA\s+A\s+RETENC[IÓO]N\s+DEL\s+IRPF')
    if not block.strip():
        warnings.append("No se encontró bloque de APORTACIÓN EMPRESA.")
        return []
    lines = [l.strip() for l in block.splitlines() if l.strip()]
    n_remun = None; n_prorr = None; base_total = None
    for l in lines:
        if re.search(r'REMUNERACI[ÓO]N\s+MENSUAL', l, re.I):
            nums = _numbers_on_line(l); n_remun = nums[-1] if nums else n_remun
        elif re.search(r'PRORRATA\s+PAGAS?\s+EXTRA', l, re.I):
            nums = _numbers_on_line(l); n_prorr = nums[-1] if nums else n_prorr
    if n_remun is not None and n_prorr is not None:
        base_total = round(n_remun + n_prorr, 2)
    contribs = []
    last_base = base_total
    for l in lines:
        up = _strip_accents(l.upper())
        if up.startswith('COTIZACION ADICIONAL'): continue
        if re.match(r'^TOTAL\b', l, re.I):
            nums = _numbers_on_line(l)
            if len(nums) == 3:
                b, a, p = nums
                # disambiguate percent vs importe
                if abs(b*(p/100.0)-a) <= 0.1: tipo, imp = p, a
                elif abs(b*(a/100.0)-p) <= 0.1: tipo, imp = a, p
                else: tipo, imp = (min(a,p), max(a,p))
                contribs.append({"concepto":"CONTINGENCIAS COMUNES","base":round(b,2),"tipo":round(tipo,2),"importe":round(imp,2)})
                last_base = b
            elif len(nums) == 2 and base_total is not None:
                a, p = nums; tipo, imp = (min(a,p), max(a,p))
                contribs.append({"concepto":"CONTINGENCIAS COMUNES","base":round(base_total,2),"tipo":round(tipo,2),"importe":round(imp,2)})
                last_base = base_total
            continue
        for ck in ["AT Y EP","DESEMPLEO","FORMACIÓN PROFESIONAL","FORMACION PROFESIONAL","FONDO GARANTÍA SALARIAL","FONDO GARANTIA SALARIAL"]:
            if re.search(r'\b'+re.escape(ck)+r'\b', l, re.I):
                concept = "FORMACIÓN PROFESIONAL" if "FORMACION" in ck.upper() else ("FONDO GARANTÍA SALARIAL" if "GARANTIA" in ck.upper() else ck)
                nums = _numbers_on_line(l)
                if len(nums) == 3:
                    b,a,p = nums
                    if abs(b*(p/100.0)-a)<=0.1: tipo, imp = p, a
                    elif abs(b*(a/100.0)-p)<=0.1: tipo, imp = a, p
                    else: tipo, imp = (min(a,p), max(a,p))
                    contribs.append({"concepto":concept,"base":round(b,2),"tipo":round(tipo,2),"importe":round(imp,2)})
                    last_base = b
                elif len(nums) == 2 and last_base is not None:
                    a,p = nums; tipo, imp = (min(a,p), max(a,p))
                    contribs.append({"concepto":concept,"base":round(last_base,2),"tipo":round(tipo,2),"importe":round(imp,2)})
                break
    if not contribs:
        warnings.append("No se extrajeron aportaciones de empresa.")
    return contribs

def validate_and_merge(devs, deds, contribs, totales, warnings):
    def ssum(lst, key='importe'): return round(sum(x.get(key) or 0 for x in lst), 2)
    dsum, csum = ssum(devs), ssum(deds)
    if totales.get('devengo_total') is not None and abs(dsum - totales['devengo_total']) > 0.02:
        warnings.append(f"Suma de devengos ({dsum}) no coincide con TOTAL DEVENGO ({totales['devengo_total']}).")
    else:
        totales['devengo_total'] = totales.get('devengo_total') or dsum
    if totales.get('deduccion_total') is not None and abs(csum - totales['deduccion_total']) > 0.02:
        warnings.append(f"Suma de deducciones ({csum}) no coincide con TOTAL DEDU. ({totales['deduccion_total']}).")
    else:
        totales['deduccion_total'] = totales.get('deduccion_total') or csum
    if all(totales.get(k) is not None for k in ('devengo_total','deduccion_total','liquido_a_percibir')):
        net = round(totales['devengo_total'] - totales['deduccion_total'], 2)
        if abs(net - totales['liquido_a_percibir']) > 0.02:
            warnings.append(f"Liquido calculado ({net}) difiere del informado ({totales['liquido_a_percibir']}).")
    totales['aportacion_empresa_total'] = ssum(contribs)
    return totales

def extract_payslip(text: str) -> dict:
    warnings: List[str] = []
    # Empresa/Trabajador
    empresa, trabajador = parse_empresa_trabajador(text, warnings)
    # Periodo
    periodo = parse_periodo(text, warnings)
    # Template-driven items
    template = detect_template(text)
    if template == "A":
        devs, deds = parse_items_A(text, warnings)
    else:
        devs, deds = parse_items_B(text, warnings)
    # Totales block
    totales = parse_totales(text, warnings)
    # Aportación empresa
    contribs = parse_aportacion_empresa(text, warnings)
    # Validate & finalize
    totales = validate_and_merge(devs, deds, contribs, totales, warnings)
    return {
        "empresa": empresa,
        "trabajador": trabajador,
        "periodo": periodo,
        "devengo_items": devs,
        "deduccion_items": deds,
        "aportacion_empresa_items": contribs,
        "totales": totales,
        "warnings": warnings
    }

if __name__ == "__main__":
    import sys
    p = sys.argv[1]
    t = open(p, "r", encoding="utf-8", errors="ignore").read()
    print(json.dumps(extract_payslip(t), ensure_ascii=False, indent=2))
