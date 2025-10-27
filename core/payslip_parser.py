from __future__ import annotations

import argparse
import base64
import json
import os
import pymupdf
import re
import sys
from typing import List, Dict, Tuple, Optional
from openai import OpenAI

"""
Spanish payslip (nómina) deterministic parser (v2)
- Input: plain-text extracted from PDF (e.g., via fitz / PyMuPDF)
- Output: JSON matching a fixed schema.
- Strategy:
  * Robust block slicing ("EMPRESA", "TRABAJADOR", "PERIODO DEVENGADO", "CONCEPTO", "APORTACIÓN EMPRESA").
  * Devengos: locate amount before concept; ignore frequent small "price" tokens (17,00 style).
  * Deducciones: take the closest preceding amount for DTO./RETENCION lines.
  * Aportación empresa: for each concept, find nearest base (>=300) around it, pick tipo from small values after it
    using concept-specific ranges, and compute importe = round(base * tipo/100, 2). If an explicit importe is detected
    near the concept and matches expected within ±1.0, use it; otherwise keep computed importe.
  * Validations: recompute totals; can be extended to verify against "TOTAL DEVENGO"/"APOR.TRAB." lines if present.

CLI:
  python payslip_parser.py --in /path/to/output.txt --out /path/to/result.json
"""

### ------------------------------ ###
###            CONSTANTS           ###
### ------------------------------ ###


SYSTEM_PROMPT = """
You are checking structured data extracted from a Spanish payslip (nómina).
Output only JSON matching the provided input JSON.

## What to do

You need to check the JSON object extracted and compare it to the information in the image, 
modifying any items from the input JSON that are incorrectly extracted or missing.

If you need to perform any modifications, add another string inside the warnings array in the JSON
explaining what you have done.

IMPORTANT:
- If you need to correct the DIAS field in the periodo object because it has 31 days and 30 have been parsed, leave
it as is and do not add any warning.
- If you detect a concept in the devengo_items containing the word "EMBARGO", make sure it is always marked
as a deduction and not as a devengo.

## This is the input and output schema
{
  "empresa": {
    "razon_social": "string|null",
    "cif": "string|null"
  },
  "trabajador": {
    "nombre": "string|null",
    "dni": "string|null"
  },
  "periodo": {
    "desde": "YYYY-MM-DD|string|null",
    "hasta": "YYYY-MM-DD|string|null",
    "dias":  0
  },
  "devengo_items": [
    { "concepto": "string", "importe": 0 }
  ],
  "deduccion_items": [
    { "concepto": "string", "importe": 0 }
  ],
  "aportacion_empresa_items": [
    { "concepto": "string", "base": 0, "tipo": 0, "importe": 0 }
  ],
  "totales": {
    "devengo_total": 0,
    "deduccion_total": 0,
    "aportacion_empresa_total": 0,
    "liquido_a_percibir": 0
  },
  "warnings": ["string"]
}


Return only this JSON.
"""

USER_PROMPT = """Analyze this Spanish payroll document and check whether data is properly extracted and assigned.

Instructions:
- Return only the JSON object above—no markdown, no comments.
- Remember to add warnings if you make any changes.
"""

MONEY2 = re.compile(r"^\d{1,3}(?:\.\d{3})*,\d{2}$")
MONEY_ANY = re.compile(r"^\d{1,3}(?:\.\d{3})*,\d{2,4}$")
DNI = re.compile(r"\b(?:[XYZxyz]\d{7}[A-Za-z]|\d{8}[A-Za-z])\b")
CIF = re.compile(r"\b[ABCDEFGHJNPQRSUVW]\d{8}[A-Z]?\b")

TIPO_RANGES = {
    "CONTINGENCIAS COMUNES": (15.0, 30.0),   # typically ~23.6-24.27
    "AT Y EP": (1.5, 7.15),                   # common 1.5-3.7 depending CNAE
    "DESEMPLEO": (5.5, 6.7),                 # e.g., 5.5
    "FORMACIÓN PROFESIONAL": (0.6, 0.6),     # e.g., 0.6
    "FONDO GARANTÍA SALARIAL": (0.2, 0.2),   # e.g., 0.2
}

CONCEPTS_EMPRESA = [
    "CONTINGENCIAS COMUNES",
    "AT Y EP",
    "DESEMPLEO",
    "FORMACIÓN PROFESIONAL",
    "FONDO GARANTÍA SALARIAL",
]


### ------------------------------ ###
###      TOTALS COMPUTATION        ###
### ------------------------------ ###
def recompute_totals(payroll_data: Dict) -> Dict:
    """
    Recompute the totales section of a payroll JSON based on line items.

    Args:
        payroll_data: The extracted payroll JSON with devengo_items,
                     deduccion_items, and aportacion_empresa_items

    Returns:
        Updated payroll_data with recomputed totales
    """
    # Helper function to safely sum importes
    def sum_importes(items):
        total = 0.0
        if not items:
            return total
        for item in items:
            if isinstance(item, dict):
                importe = item.get('importe')
                if importe is not None:
                    try:
                        total += float(importe)
                    except (ValueError, TypeError):
                        pass
        return round(total, 2)

    # Get line items
    devengo_items = payroll_data.get('devengo_items') or []
    deduccion_items = payroll_data.get('deduccion_items') or []
    aportacion_empresa_items = payroll_data.get('aportacion_empresa_items') or []

    # Compute totals
    devengo_total = sum_importes(devengo_items)
    deduccion_total = sum_importes(deduccion_items)
    aportacion_empresa_total = sum_importes(aportacion_empresa_items)
    liquido_a_percibir = round(devengo_total - deduccion_total, 2)

    # Update the totales section
    payroll_data['totales'] = {
        'devengo_total': devengo_total,
        'deduccion_total': deduccion_total,
        'aportacion_empresa_total': aportacion_empresa_total,
        'liquido_a_percibir': liquido_a_percibir
    }

    return payroll_data


### ------------------------------ ###
###     VISION MODEL PIPELINE      ###
### ------------------------------ ###
def call_vision_model(image: str, input_json: str, model: str = "gpt-4.1-mini", max_tokens: int = 1200):
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("Set OPENAI_API_KEY environment variable")
    client = OpenAI(api_key=api_key)

    user_parts = [
        {"type": "text", "text": USER_PROMPT},
        {"type": "text", "text": input_json},
        {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{image}", "detail": "high"}}
    ]

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_parts},
    ]

    resp = client.chat.completions.create(
        model=model,
        temperature=0,
        top_p=0,
        response_format={"type": "json_object"},
        messages=messages,
        max_tokens=max_tokens,
    )
    return resp.choices[0].message.content

def process_payslip(pdf_path: str):
    """
    Convert PDF pages to images and process with vision model.

    Yields payroll data for each page immediately after extraction,
    allowing for immediate processing and database commits.

    Yields:
        Dict: Payroll data for each page
    """
    doc = None
    try:
        doc = pymupdf.open(pdf_path)
        if doc.page_count == 0:
            raise ValueError("PDF has no pages")

        total_pages = len(doc)

        for page_num in range(total_pages):
            try:
                # Process page normally (not cached)
                page = doc[page_num]
                # Convert PDF page to image
                mat = pymupdf.Matrix(2, 2)  # Zoom factor
                pix = page.get_pixmap(matrix=mat)
                img_data = pix.tobytes("png")

                # Extract and process text with heuristic
                text = json.dumps(extract_data(page))
                print(f"📝 Extracted text from page {page_num + 1}/{total_pages}")
                # Print the extracted text
                print(json.dumps(extract_data(page), ensure_ascii=False, indent=2))

                # Encode image for OpenAI
                base64_image = base64.b64encode(img_data).decode('utf-8')

                # Progress logging
                print(f"🔄 Processing page {page_num + 1}/{total_pages} with OpenAI Vision API...")
                payroll = call_vision_model(base64_image, text)
                print(f"✅ Page {page_num + 1}/{total_pages} processed - Found 1 employee")

                # Log raw extraction results for debugging
                print("   📊 Extracted data:")
                # print output json pretty
                payroll = json.loads(payroll)
                print(json.dumps(payroll, ensure_ascii=False, indent=2))

                # Recompute totals to ensure accuracy
                payroll = recompute_totals(payroll)

                name = payroll["trabajador"]["nombre"]
                emp_id = payroll["trabajador"]["dni"]
                company = payroll["empresa"]["razon_social"]
                period = f"{payroll["periodo"]["desde"]}/{payroll["periodo"]["hasta"]}"
                liquido = payroll["totales"]["liquido_a_percibir"]

                # Color code based on data quality
                if name and emp_id:
                    status = "✅"
                elif name or emp_id:
                    status = "⚠️"
                else:
                    status = "❌"

                print(f"   {status} Employee: Name='{name}' ID='{emp_id}' Company='{company}' Period={period} Liquido={liquido}")

                # Yield immediately after extraction - allows for immediate commit!
                yield payroll

            except Exception as page_error:
                print(f"⚠️  Error processing page {page_num + 1}/{total_pages}: {page_error}")
                # Continue to next page instead of failing entire PDF
                continue

    except Exception as e:
        print(f"❌ Error processing PDF {pdf_path}: {e}")
        # Generator will simply stop yielding

    finally:
        # Always close the document
        if doc:
            doc.close()


### ------------------------------ ###
###   TEXT EXTRACTION HEURISTICS   ###
### ------------------------------ ###

# -----------------------------
#         Helpers
# -----------------------------
def f2(s: str) -> float:
    return float(s.replace(".", "").replace(",", "."))

def normalize_ascii(s: str) -> str:
    trans = str.maketrans("ÁÉÍÓÚÜÑáéíóúüñ", "AEIOUUNAEIOUUN")
    return s.upper().translate(trans)

def read_lines_from_text(text: str) -> List[str]:
    return [ln.strip() for ln in text.splitlines() if ln.strip()]

def find_between(lines: List[str], start: str, end: str) -> List[str]:
    try:
        i = next(i for i, line in enumerate(lines) if start.lower() in line.lower())
    except StopIteration:
        return []
    try:
        j = next(j for j in range(i + 1, len(lines)) if end.lower() in lines[j].lower())
    except StopIteration:
        j = len(lines)
    return lines[i + 1 : j]

APORTE_MATCH_EPS = 0.02  # prefer printed importe if within 2 cents


# -----------------------------
# Empresa / Trabajador / Periodo
# -----------------------------
def parse_empresa_trabajador(lines: List[str]) -> Tuple[Dict, Dict]:
    empresa = {"razon_social": None, "cif": None}
    trabajador = {"nombre": None, "dni": None}

    # CIF anywhere near the header
    for ln in lines[:100]:
        m = CIF.search(ln)
        if m:
            empresa["cif"] = m.group(0)
            break

    emp_block = find_between(lines, "EMPRESA (razón social)", "DOMICILIO")
    name_candidates = [ln for ln in emp_block if re.search(r"[A-Za-zÁÉÍÓÚÜÑáéíóúüñ]", ln)]
    if name_candidates:
        empresa["razon_social"] = name_candidates[-1].strip(" .")

    trab_block = find_between(lines, "TRABAJADOR (nombre)", "CONT.")
    for ln in trab_block:
        m = DNI.search(ln)
        if m:
            trabajador["dni"] = m.group(0).upper()

    bad_norm = {normalize_ascii(x) for x in ["D.N.I.", "NºAFILIACION S.S.", "NºAFILIACION", "NUM.AFILIACION", "AFILIACION", "S.S.", "DNI"]}
    best = ""
    for ln in trab_block:
        if normalize_ascii(ln) in bad_norm:
            continue
        if re.search(r"[A-Za-zÁÉÍÓÚÜÑáéíóúüñ]", ln) and not DNI.search(ln):
            if len(ln) > len(best):
                best = ln
    if best:
        trabajador["nombre"] = best

    return empresa, trabajador

def parse_periodo(lines: List[str]) -> Dict:
    periodo = {"desde": None, "hasta": None, "dias": 0}
    blk = find_between(lines, "PERIODO DEVENGADO", "DEVENGO") or find_between(lines, "PERIODO DEVENGADO", "CONCEPTO")
    txt = "\n".join(blk)
    dates = re.findall(r"\b\d{2}-\d{2}-\d{4}\b", txt)
    if dates:
        periodo["hasta"] = sorted(dates)[-1]
        month = periodo["hasta"][3:5]
        year = periodo["hasta"][-4:]
        periodo["desde"] = f"01-{month}-{year}"
    # DIAS: first 20..31 after label
    try:
        idx = next(i for i, line in enumerate(lines) if line.upper() == "DIAS")
        for j in range(idx + 1, min(idx + 15, len(lines))):
            if lines[j].isdigit() and 20 <= int(lines[j]) <= 31:
                periodo["dias"] = int(lines[j])
                break
    except StopIteration:
        pass
    return periodo


# -----------------------------
# Devengos / Deducciones
# -----------------------------
def slice_devengos_block(lines: List[str]) -> List[str]:
    blk = find_between(lines, "CONCEPTO", "TOTAL DEVENGO")
    if not blk:
        blk = find_between(lines, "CONCEPTO", "DETERMINACION")
    return blk

def compute_frequent_small_tokens(block: List[str]) -> set:
    # Many slips include a repeated PRICE like "17,00". We will ignore such tokens when selecting devengo imports.
    counts = {}
    for t in block:
        if MONEY2.match(t):
            counts[t] = counts.get(t, 0) + 1
    return {m for (m, c) in counts.items() if c >= 3 and f2(m) <= 50.0}

def pick_devengo_amount_before(block: list[str], idx: int, ignore_prices: set) -> float | None:
    MAX_BACK = 20            # was 10 — SALARIO BASE may sit further up
    MIN_IMPORT = 5.00  # common unit-like tokens to skip

    # 1) NEAREST good candidate walking backwards
    fallback_small = None
    for j in range(idx - 1, max(0, idx - MAX_BACK), -1):
        tok = block[j]
        if MONEY2.match(tok):
            if tok in ignore_prices:
                continue
            val = round(f2(tok), 2)
            if val >= MIN_IMPORT:
                return val
            if fallback_small is None:
                fallback_small = val

    # 2) Heuristic fallback: take the MAX in the back window (ignoring prices/units)
    cand = [
        round(f2(t), 2)
        for t in block[max(0, idx - MAX_BACK):idx]
        if MONEY2.match(t) and t not in ignore_prices
    ]
    if cand:
        return max(cand)

    # 3) Last resort: short lookahead for the nearest valid number
    for j in range(idx + 1, min(idx + 8, len(block))):
        tok = block[j]
        if MONEY2.match(tok):
            if tok in ignore_prices:
                continue
            val = round(f2(tok), 2)
            if val >= MIN_IMPORT:
                return val
            if fallback_small is None:
                fallback_small = val

    return fallback_small

def pick_deduct_closest_before(block: List[str], idx: int) -> Optional[float]:
    for j in range(idx - 1, max(0, idx - 8), -1):
        if MONEY2.match(block[j]):
            return round(f2(block[j]), 2)
    return None

def parse_devengos_y_deducciones(lines: List[str]) -> Tuple[List[Dict], List[Dict], List[str]]:
    dev, ded, warns = [], [], []
    blk = slice_devengos_block(lines)
    ignore_prices = compute_frequent_small_tokens(blk)

    i = 0
    while i < len(blk):
        ln = blk[i]
        if re.search(r"[A-Za-zÁÉÍÓÚÜÑáéíóúüñ]", ln) and not MONEY_ANY.match(ln):
            up = normalize_ascii(ln)
            if up.startswith("TOTAL") or "DETERMINACION" in up:
                pass
            elif up.startswith("DTO.") or up.startswith("RETENCION IRPF") or up.startswith("RETENCION I.R.P.F"):
                amt = pick_deduct_closest_before(blk, i)
                if amt is not None:
                    label = "RETENCION IRPF" if up.startswith("RETENCION") else ln
                    ded.append({"concepto": label, "importe": amt})
            else:
                amt = pick_devengo_amount_before(blk, i, ignore_prices)
                if amt is not None:
                    dev.append({"concepto": ln, "importe": amt})
                else:
                    warns.append(f"No amount for devengo concept '{ln}'")
        i += 1

    return dev, ded, warns


# -----------------------------
# Aportación Empresa
# -----------------------------
def nearest_base(sec: List[str], idx: int, search_before: int = 16, search_after: int = 16) -> Optional[float]:
    # Prefer a base (>=300) close to the concept; first search BEFORE, then AFTER.
    for j in range(idx - 1, max(-1, idx - search_before), -1):  # include j==0 (stop=-1 is exclusive)
        if MONEY2.match(sec[j]) and f2(sec[j]) >= 300:
            return round(f2(sec[j]), 2)
    for j in range(idx + 1, min(idx + search_after, len(sec))):
        if MONEY2.match(sec[j]) and f2(sec[j]) >= 300:
            return round(f2(sec[j]), 2)
    # Fallback: last >=300 in whole section
    bigs = [round(f2(x), 2) for x in sec if MONEY2.match(x) and f2(x) >= 300]
    return bigs[-1] if bigs else None

def _nearby_numbers(sec: List[str], idx: int, predicate, stop: int = 12) -> List[float]:
    picks: List[Tuple[float,int]] = []
    # forward
    for j in range(idx + 1, min(idx + stop, len(sec))):
        if "TOTAL" in sec[j].upper() or any(c in sec[j].upper() for c in CONCEPTS_EMPRESA):
            break
        if MONEY2.match(sec[j]) and predicate(sec[j]):
            picks.append((round(f2(sec[j]), 2), j - idx))
    # backward
    for j in range(idx - 1, max(0, idx - stop), -1):
        if "TOTAL" in sec[j].upper() or any(c in sec[j].upper() for c in CONCEPTS_EMPRESA): 
            break
        if MONEY2.match(sec[j]) and predicate(sec[j]):
            picks.append((round(f2(sec[j]), 2), idx - j))
    picks.sort(key=lambda t: t[1])  # nearest first
    return [v for v, _ in picks]

def find_tipo_candidates(sec: List[str], idx: int, stop_window: int = 12) -> List[float]:
    return _nearby_numbers(sec, idx, lambda s: f2(s) <= 50, stop_window)

def find_importe_candidates(sec: List[str], idx: int, base: float, stop_window: int = 12) -> List[float]:
    return _nearby_numbers(sec, idx, lambda s: f2(s) < (base if base is not None else 1e9), stop_window)

def choose_tipo_importe(concept: str, tipos: List[float], imps: List[float], base: float) -> Tuple[Optional[float], Optional[float]]:
    if not tipos or base is None:
        return None, None
    lo, hi = TIPO_RANGES.get(concept, (0.0, 50.0))
    # pick tipo in preferred range if available, else nearest to range
    in_range = [t for t in tipos if lo <= t <= hi]
    if in_range:
        tipo_candidates = in_range
    else:
        # choose the tipo closest to the range (distance 0 if inside)
        tipo_candidates = sorted(tipos, key=lambda t: (0 if lo <= t <= hi else min(abs(t - lo), abs(t - hi))))
    best_tipo, best_imp, best_err = None, None, 1e9
    for t in tipo_candidates:
        expected = round(base * (t / 100.0), 2)
        if imps:
            # choose importe that is closest to expected
            m = min(imps, key=lambda x: abs(x - expected))
            err = abs(m - expected)
            if err < best_err:
                best_tipo, best_imp, best_err = t, m, err
        else:
            # no observed importe -> compute
            best_tipo, best_imp, best_err = t, expected, 0.0
            break
    return best_tipo, best_imp

def parse_aportacion_empresa(lines):
    """
    New employer-contributions parser implementing the requested logic:
      - Detect 'HORAS EXTRA' anywhere in the doc (not 'PAGAS EXTRA').
      - If NO 'HORAS EXTRA': all company concepts use BTC (Base Total de Cotización) as base.
         * FOGASA = 0.20% of BTC
         * FORMACIÓN PROFESIONAL = 0.60% of BTC
         * DESEMPLEO in {5.50, 6.70} -> choose the one that best matches nearby importe
         * AT Y EP in [1.50, 7.15]   -> find nearby importe and back out tipo; else use nearby small (%), else 3.70
         * CONTINGENCIAS COMUNES: use nearby % in [15, 30] (prefer 24.27); else fallback 24.27
      - If YES 'HORAS EXTRA': placeholder — still use BTC for now and warn (future: BTC + importe_horas_extra).
    """
    # locate APORTACIÓN EMPRESA section
    start = next((i for i, ln in enumerate(lines) if "APORTACIÓN EMPRESA" in ln.upper()), None)
    if start is None:
        return [], ["No APORTACIÓN EMPRESA section"]
    end = next((i for i in range(start + 1, len(lines))
                if "BASE SUJETA A RETENCIÓN" in lines[i].upper() or "RECIBI" in lines[i].upper()), len(lines))
    sec = lines[start + 1 : end]

    # detect HORAS EXTRA (not 'PAGAS EXTRA')
    has_horas_extra = any("HORAS EXTRA" in ln.upper() for ln in lines)

    # --- Base Total de Cotización (BTC): prefer 'TOTAL' line's next money token (>=300)
    btc = None
    for j in range(len(sec)):
        if "TOTAL" in sec[j].upper():
            for k in range(j + 1, min(j + 4, len(sec))):
                if MONEY2.match(sec[k]):
                    val = round(f2(sec[k]), 2)
                    if val >= 300:
                        btc = val
                        break
            if btc is not None:
                break
    if btc is None:
        bigs = [round(f2(x), 2) for x in sec if MONEY2.match(x) and f2(x) >= 300]
        btc = bigs[-1] if bigs else None
    if btc is None:
        return [], ["No se pudo detectar la Base Total de Cotización (TOTAL)."]

    # Placeholder: if HORAS EXTRA appears, keep BTC for now and warn (future: BTC + importe_horas_extra)
    base_emp = btc
    warns = []
    if has_horas_extra:
        warns.append("HORAS EXTRA detectado: por ahora se usa BTC como base; pendiente aplicar BTC + importe_horas_extra.")

    def concept_index(name: str):
        up = name.upper()
        return next((i for i, ln in enumerate(sec) if up in ln.upper()), None)

    def nearby_numbers(idx: int, stop: int = 10):
        """Collect money tokens around idx (both sides), nearest-first, unique preserving order."""
        picks = []
        for d in range(1, stop + 1):
            for j in (idx - d, idx + d):
                if 0 <= j < len(sec) and MONEY2.match(sec[j]):
                    v = round(f2(sec[j]), 2)
                    if v not in picks:
                        picks.append(v)
        return picks
    
    def _snap_importes_to_printed(items: List[Dict]) -> List[Dict]:
        """
        For each aportación concept, if a printed importe exists near the concept
        and it's within ±APORTE_MATCH_EPS of base*tipo/100, keep the printed one.
        """
        for it in items:
            idx = concept_index(it["concepto"])
            if idx is None:
                continue
            computed = round(it["base"] * (it["tipo"] / 100.0), 2)
            around = nearby_numbers(idx, 10)  # nearest-first money tokens
            # choose the observed importe closest to the computed value, but only values < base
            obs = min((v for v in around if v < it["base"]), key=lambda v: abs(v - computed), default=None)
            if obs is not None and abs(obs - computed) <= APORTE_MATCH_EPS:
                it["importe"] = obs
        return items

    items = []
    used_importes = set()

    # --- FP (0.60%) and FOGASA (0.20%) directly from BTC
    items.append({
        "concepto": "FORMACIÓN PROFESIONAL",
        "base": base_emp,
        "tipo": 0.60,
        "importe": round(base_emp * 0.006, 2),
    })
    used_importes.add(round(base_emp * 0.006, 2))

    items.append({
        "concepto": "FONDO GARANTÍA SALARIAL",
        "base": base_emp,
        "tipo": 0.20,
        "importe": round(base_emp * 0.002, 2),
    })
    used_importes.add(round(base_emp * 0.002, 2))

    # --- DESEMPLEO: choose 5.50 or 6.70 that best matches nearby importe
    idx_des = concept_index("DESEMPLEO")
    if idx_des is not None:
        around = nearby_numbers(idx_des, 10)
        candidates = [5.50, 6.70]
        best_t, best_imp, best_err = None, None, 1e9
        for t in candidates:
            target = round(base_emp * (t / 100.0), 2)
            if around:
                err = min(abs(target - v) for v in around)
            else:
                err = 0.0
            if err < best_err:
                best_t, best_imp, best_err = t, target, err

        items.append({"concepto": "DESEMPLEO", "base": base_emp, "tipo": best_t, "importe": best_imp})
        used_importes.add(best_imp)
    else:
        # fallback to 5.50
        items.append({
            "concepto": "DESEMPLEO",
            "base": base_emp,
            "tipo": 5.50,
            "importe": round(base_emp * 0.055, 2),
        })
        used_importes.add(round(base_emp * 0.055, 2))

    # --- AT Y EP: find an importe near concept; back out tipo; constrain to [1.50, 7.15]
    idx_at = concept_index("AT Y EP")
    at_tipo, at_imp = None, None
    if idx_at is not None:
        around = nearby_numbers(idx_at, 10)
        # exclude importes already used by DES/FP/FOGASA (avoid collisions)
        used = {it["importe"] for it in items}
        around = [v for v in around if v not in used]
        best_gap = 1e9
        for v in around:
            t = round(100.0 * v / base_emp, 2)
            if 1.50 <= t <= 7.15:
                # small consistency gap (should be ~0 when it's the right pair)
                gap = abs(round(base_emp * (t / 100.0), 2) - v)
                if gap < best_gap:
                    best_gap = gap
                    at_tipo = t
                    at_imp = round(base_emp * (t / 100.0), 2)
    if at_tipo is None:
        # fallback: if a small (%) is visible near AT/EP, prefer it; else default 3.70
        # (We intentionally do not rely on generic small-number scans beyond money tokens here.)
        at_tipo = 3.70
        at_imp = round(base_emp * (at_tipo / 100.0), 2)
    items.append({"concepto": "AT Y EP", "base": base_emp, "tipo": at_tipo, "importe": at_imp})
    used_importes.add(at_imp)

    # --- CONTINGENCIAS COMUNES: use nearby % in [15, 30]; fallback 24.27
    idx_cc = concept_index("CONTINGENCIAS COMUNES")
    cc_tipo = None
    if idx_cc is not None:
        # Reuse money tokens around CC and infer % if any are <= 50 and within [15, 30]
        around = nearby_numbers(idx_cc, 10)
        percentish = [v for v in around if v <= 50 and 15.0 <= v <= 30.0]
        if percentish:
            # prefer closest to 24.27
            cc_tipo = min(percentish, key=lambda t: abs(t - 24.27))
    if cc_tipo is None:
        cc_tipo = 24.27
    items.append({
        "concepto": "CONTINGENCIAS COMUNES",
        "base": base_emp,
        "tipo": cc_tipo,
        "importe": round(base_emp * (cc_tipo / 100.0), 2),
    })
    used_importes.add(round(base_emp * (cc_tipo / 100.0), 2))

    items = _snap_importes_to_printed(items)

    return items, warns


# -----------------------------
# Totals & assembly
# -----------------------------
def compute_totales(dev: List[Dict], ded: List[Dict], ap: List[Dict]) -> Dict:
    tot_dev = round(sum(x["importe"] for x in dev), 2)
    tot_ded = round(sum(x["importe"] for x in ded), 2)
    tot_ap = round(sum(x["importe"] for x in ap), 2)
    return {
        "devengo_total": tot_dev,
        "deduccion_total": tot_ded,
        "aportacion_empresa_total": tot_ap,
        "liquido_a_percibir": round(tot_dev - tot_ded, 2),
    }

def parse_text_to_json(text: str) -> Dict:
    lines = read_lines_from_text(text)
    empresa, trabajador = parse_empresa_trabajador(lines)
    periodo = parse_periodo(lines)
    dev, ded, w1 = parse_devengos_y_deducciones(lines)
    ap, w2 = parse_aportacion_empresa(lines)
    totales = compute_totales(dev, ded, ap)
    return {
        "empresa": empresa,
        "trabajador": trabajador,
        "periodo": periodo,
        "devengo_items": dev,
        "deduccion_items": ded,
        "aportacion_empresa_items": ap,
        "totales": totales,
        "warnings": [*w1, *w2],
    }


# -----------------------------
#  Extractor function
# -----------------------------
def extract_data(pdf_page: pymupdf.Page) -> Dict:
    
    result = parse_text_to_json(pdf_page.get_text())
    return result


# -----------------------------
#  Standalone main
# -----------------------------
def main():
    p = argparse.ArgumentParser(description="Deterministic Spanish payslip parser (text → JSON)")
    p.add_argument("--in", dest="inp", required=True, help="Input payslip in PDF")
    p.add_argument("--out", dest="out", required=True, help="Output JSON file")
    args = p.parse_args()

    result = process_payslip(args.inp)

    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    # Simple stdout summary
    print(json.dumps(result, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    sys.exit(main())
