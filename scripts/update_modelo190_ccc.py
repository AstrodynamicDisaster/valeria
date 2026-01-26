#!/usr/bin/env python3
"""
Update a Modelo 190 fixed-width file:
- Flip the header "numero identificativo" last digit from 0 to 1.
- For each perceptor (type 2) record, set provincia (positions 76-77)
  from the first two digits of the CCC found in the local DB.
"""

from __future__ import annotations

import argparse
import os
import re
import sys
import unicodedata
from difflib import SequenceMatcher
from typing import Dict, Tuple

from sqlalchemy import func

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.database import get_session
from core.models import Client, ClientLocation, Employee, EmployeePeriod


HEADER_NUM_ID_START = 107  # 1-based 108
HEADER_NUM_ID_END = 120    # 1-based 120, end-exclusive in slices
HEADER_CIF_START = 8       # 1-based 9
HEADER_CIF_END = 17        # 1-based 17, end-exclusive in slices

PERCEPTOR_DNI_START = 17   # 1-based 18
PERCEPTOR_DNI_END = 26     # 1-based 26, end-exclusive in slices
PERCEPTOR_NAME_START = 35  # 1-based 36
PERCEPTOR_NAME_END = 75    # 1-based 75, end-exclusive in slices
PERCEPTOR_PROV_START = 75  # 1-based 76
PERCEPTOR_PROV_END = 77    # 1-based 77, end-exclusive in slices

RECORD_LENGTH = 500
NAME_MATCH_THRESHOLD = 0.92
NAME_MATCH_TIE_MARGIN = 0.005

_NON_ALNUM_RE = re.compile(r"[^A-Z0-9]+")


def _split_line_ending(line: str) -> Tuple[str, str]:
    if line.endswith("\r\n"):
        return line[:-2], "\r\n"
    if line.endswith("\n"):
        return line[:-1], "\n"
    return line, ""


def _extract_digits(value: str) -> str:
    return "".join(ch for ch in value if ch.isdigit())


def _normalize_name_key(value: str) -> str:
    if not value:
        return ""
    text = unicodedata.normalize("NFKD", value)
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    text = text.upper()
    return _NON_ALNUM_RE.sub("", text).strip()


def _format_employee_name(first_name: str, last_name: str, last_name2: str | None) -> str:
    parts = [last_name, last_name2 or "", first_name]
    return " ".join(part for part in parts if part).strip()


def _flip_num_identificativo(num_id: str) -> str:
    if len(num_id) != 13:
        raise ValueError(f"Header numero_identificativo length != 13: '{num_id}'")
    if not num_id.startswith("190"):
        raise ValueError(f"Header numero_identificativo does not start with 190: '{num_id}'")
    if num_id[-1] != "0":
        raise ValueError(f"Header numero_identificativo does not end with 0: '{num_id}'")
    return f"{num_id[:-1]}1"


def _query_ccc_for_employee(session, cif: str, dni: str) -> str | None:
    result = (
        session.query(ClientLocation.ccc_ss)
        .join(Client, Client.id == ClientLocation.company_id)
        .join(EmployeePeriod, EmployeePeriod.location_id == ClientLocation.id)
        .join(Employee, Employee.id == EmployeePeriod.employee_id)
        .filter(func.upper(Client.cif) == cif, func.upper(Employee.identity_card_number) == dni)
        .order_by(EmployeePeriod.period_begin_date.desc(), EmployeePeriod.id.asc())
        .first()
    )
    if not result or not result[0]:
        return None
    return result[0]


def _query_ccc_for_employee_name(session, cif: str, name_raw: str) -> str | None:
    name_key = _normalize_name_key(name_raw)
    if not name_key:
        return None

    rows = (
        session.query(
            Employee.id,
            Employee.first_name,
            Employee.last_name,
            Employee.last_name2,
            ClientLocation.ccc_ss,
            EmployeePeriod.period_begin_date,
            EmployeePeriod.id,
        )
        .join(EmployeePeriod, EmployeePeriod.employee_id == Employee.id)
        .join(ClientLocation, ClientLocation.id == EmployeePeriod.location_id)
        .join(Client, Client.id == ClientLocation.company_id)
        .filter(func.upper(Client.cif) == cif)
        .order_by(EmployeePeriod.period_begin_date.desc(), EmployeePeriod.id.asc())
        .all()
    )

    seen_employees = set()
    exact_matches = []
    fuzzy_candidates = []

    for row in rows:
        if row.id in seen_employees:
            continue
        seen_employees.add(row.id)

        full_name = _format_employee_name(row.first_name, row.last_name, row.last_name2)
        candidate_key = _normalize_name_key(full_name)
        if not candidate_key:
            continue

        if candidate_key == name_key:
            exact_matches.append(row)
            continue

        score = SequenceMatcher(None, name_key, candidate_key).ratio()
        if score >= NAME_MATCH_THRESHOLD:
            fuzzy_candidates.append((score, row))

    if len(exact_matches) == 1:
        return exact_matches[0].ccc_ss
    if len(exact_matches) > 1:
        return None

    if not fuzzy_candidates:
        return None

    fuzzy_candidates.sort(key=lambda item: item[0], reverse=True)
    best_score = fuzzy_candidates[0][0]
    tied = [row for score, row in fuzzy_candidates if abs(score - best_score) <= NAME_MATCH_TIE_MARGIN]
    if len(tied) != 1:
        return None
    return tied[0].ccc_ss


def _fetch_ccc_for_employee(session, cif: str, dni: str, name_raw: str) -> str:
    ccc = _query_ccc_for_employee(session, cif, dni)
    if not ccc and dni.startswith("0") and len(dni) > 1:
        ccc = _query_ccc_for_employee(session, cif, dni[1:])
    if not ccc and name_raw:
        ccc = _query_ccc_for_employee_name(session, cif, name_raw)
    if not ccc:
        raise RuntimeError(f"No CCC found for DNI '{dni}' and CIF '{cif}'")
    return ccc


def _update_file_lines(lines: list[str]) -> list[str]:
    if not lines:
        raise ValueError("Input file is empty")

    header_content, header_ending = _split_line_ending(lines[0])
    if len(header_content) != RECORD_LENGTH:
        raise ValueError(f"Header length != {RECORD_LENGTH}: {len(header_content)}")
    if header_content[0] != "1":
        raise ValueError("First record is not type 1 header")

    cif = header_content[HEADER_CIF_START:HEADER_CIF_END].strip().upper()
    if not cif:
        raise ValueError("Header CIF is empty")

    num_id = header_content[HEADER_NUM_ID_START:HEADER_NUM_ID_END]
    new_num_id = _flip_num_identificativo(num_id)
    header_content = (
        header_content[:HEADER_NUM_ID_START]
        + new_num_id
        + header_content[HEADER_NUM_ID_END:]
    )
    updated_lines = [header_content + header_ending]

    session = get_session()
    try:
        dni_cache: Dict[str, str] = {}
        for idx, line in enumerate(lines[1:], start=2):
            content, ending = _split_line_ending(line)
            if len(content) != RECORD_LENGTH:
                raise ValueError(f"Line {idx} length != {RECORD_LENGTH}: {len(content)}")

            record_type = content[0]
            if record_type == "2":
                dni_raw = content[PERCEPTOR_DNI_START:PERCEPTOR_DNI_END]
                dni = dni_raw.strip().upper()
                if not dni:
                    raise ValueError(f"Line {idx} has empty DNI/NIE")
                name_raw = content[PERCEPTOR_NAME_START:PERCEPTOR_NAME_END].strip()

                if dni in dni_cache:
                    ccc = dni_cache[dni]
                else:
                    ccc = _fetch_ccc_for_employee(session, cif, dni, name_raw)
                    dni_cache[dni] = ccc

                ccc_digits = _extract_digits(ccc)
                if len(ccc_digits) < 2:
                    raise ValueError(f"CCC '{ccc}' for DNI '{dni}' has < 2 digits")
                provincia = ccc_digits[:2]

                content = (
                    content[:PERCEPTOR_PROV_START]
                    + provincia
                    + content[PERCEPTOR_PROV_END:]
                )
            elif record_type != "1":
                raise ValueError(f"Unexpected record type '{record_type}' on line {idx}")

            updated_lines.append(content + ending)
    finally:
        session.close()

    return updated_lines


def main() -> int:
    parser = argparse.ArgumentParser(description="Update Modelo 190 file provincias from CCC.")
    parser.add_argument("--input", required=True, help="Path to input .txt file")
    parser.add_argument("--output", help="Path to output file (default: <input>.updated.txt)")
    args = parser.parse_args()

    input_path = args.input
    output_path = args.output or f"{input_path}.updated.txt"

    with open(input_path, "rb") as f:
        raw = f.read()
    text = raw.decode("iso-8859-1")
    lines = text.splitlines(keepends=True)

    updated_lines = _update_file_lines(lines)
    updated_text = "".join(updated_lines)

    with open(output_path, "wb") as f:
        f.write(updated_text.encode("iso-8859-1"))

    print(f"Updated file written to {output_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
