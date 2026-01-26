#!/usr/bin/env python3
"""
Update a Modelo 190 main file using a reduced "errors" file.

The errors file is a valid Modelo 190 layout containing only type-2
records flagged by AEAT as incorrect. We only look up and update those
records in the main file, preserving fixed-width formatting.
"""

from __future__ import annotations

import argparse
import os
import re
import sys
from typing import Dict, Iterable, List, Set, Tuple

from sqlalchemy import func

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.a3.tools import get_employee_ssn
from core.database import get_session
from core.models import Client, ClientLocation, Employee, EmployeePeriod
from core.normalization import normalize_ssn
from core.saltra import get_ss_employee_data


RECORD_LENGTH = 500

HEADER_CIF_START = 8       # 1-based 9
HEADER_CIF_END = 17        # 1-based 17, end-exclusive in slices

PERCEPTOR_DNI_START = 17   # 1-based 18
PERCEPTOR_DNI_END = 26     # 1-based 26, end-exclusive in slices
PERCEPTOR_NAME_START = 35  # 1-based 36
PERCEPTOR_NAME_END = 75    # 1-based 75, end-exclusive in slices


_ACCENT_TRANSLATION = str.maketrans(
    {
        "\u00c1": "A",
        "\u00c9": "E",
        "\u00cd": "I",
        "\u00d3": "O",
        "\u00da": "U",
        "\u00c0": "A",
        "\u00c8": "E",
        "\u00cc": "I",
        "\u00d2": "O",
        "\u00d9": "U",
        "\u00c2": "A",
        "\u00ca": "E",
        "\u00ce": "I",
        "\u00d4": "O",
        "\u00db": "U",
        "\u00c4": "A",
        "\u00cb": "E",
        "\u00cf": "I",
        "\u00d6": "O",
        "\u00dc": "U",
    }
)

_ALLOWED_TEXT_RE = re.compile(r"[^A-Z0-9 \u00d1\u00c7]")


def _split_line_ending(line: str) -> Tuple[str, str]:
    if line.endswith("\r\n"):
        return line[:-2], "\r\n"
    if line.endswith("\n"):
        return line[:-1], "\n"
    return line, ""


def normalize_text(value: str | None) -> str:
    if not value:
        return ""
    text = value.upper()
    text = text.translate(_ACCENT_TRANSLATION)
    text = re.sub(r"[\t\n\r]+", " ", text)
    text = _ALLOWED_TEXT_RE.sub(" ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def fmt_alpha(value: str | None, length: int) -> str:
    normalized = normalize_text(value)
    if len(normalized) > length:
        normalized = normalized[:length]
    return normalized + (" " * (length - len(normalized)))


def fmt_nif(value: str | None) -> str:
    if not value:
        raise ValueError("Missing NIF value")
    cleaned = normalize_text(value).replace(" ", "")
    if len(cleaned) > 9:
        raise ValueError(f"NIF '{value}' exceeds 9 characters")
    return cleaned.rjust(9, "0")


def _normalize_key(value: str) -> str:
    return normalize_text(value).replace(" ", "")


def _render_progress(label: str, current: int, total: int) -> None:
    if total <= 0:
        return
    percent = (current / total) * 100
    print(f"\r{label}: {current}/{total} ({percent:5.1f}%)", end="", file=sys.stderr, flush=True)


def _finish_progress(label: str, total: int) -> None:
    if total <= 0:
        return
    print(f"\r{label}: {total}/{total} (100.0%)", file=sys.stderr)


def _extract_cif(lines: List[str], label: str) -> str:
    if not lines:
        raise ValueError(f"{label} file is empty")

    header_content, _ = _split_line_ending(lines[0])
    if len(header_content) != RECORD_LENGTH:
        raise ValueError(f"{label} header length != {RECORD_LENGTH}: {len(header_content)}")
    if header_content[0] != "1":
        raise ValueError(f"{label} first record is not type 1 header")

    cif = header_content[HEADER_CIF_START:HEADER_CIF_END].strip().upper()
    if not cif:
        raise ValueError(f"{label} header CIF is empty")
    return cif


def _collect_type2_keys(lines: List[str], label: str) -> List[Tuple[str, str]]:
    seen = set()
    unique: List[Tuple[str, str]] = []
    for idx, line in enumerate(lines[1:], start=2):
        content, _ = _split_line_ending(line)
        if len(content) != RECORD_LENGTH:
            raise ValueError(f"{label} line {idx} length != {RECORD_LENGTH}: {len(content)}")

        record_type = content[0]
        if record_type == "2":
            dni_raw = content[PERCEPTOR_DNI_START:PERCEPTOR_DNI_END]
            name_raw = content[PERCEPTOR_NAME_START:PERCEPTOR_NAME_END]
            dni_key = _normalize_key(dni_raw)
            name_key = normalize_text(name_raw)
            if not dni_key:
                raise ValueError(f"{label} line {idx} has empty DNI/NIE")
            key = (dni_key, name_key)
            if key not in seen:
                seen.add(key)
                unique.append(key)
        elif record_type != "1":
            raise ValueError(f"{label} line {idx} has unexpected record type '{record_type}'")

    return unique


def _fetch_employee_data(cif: str, dni: str, name_key: str) -> Dict[str, str]:
    ssn = None
    try:
        ssn = get_employee_ssn(cif, dni)
    except Exception:
        ssn = None

    if not ssn:
        ssn = _fetch_ssn_from_db(cif, dni)

    if not ssn:
        raise RuntimeError(f"SSN not found for CIF '{cif}' and DNI '{dni}' via A3 or local DB")

    data = get_ss_employee_data(ssn)
    if not data:
        raise RuntimeError(f"Saltra lookup failed for SSN '{ssn}' (DNI '{dni}', name '{name_key}')")

    required = ("dni", "name", "surnames")
    if any(not data.get(field) for field in required):
        raise RuntimeError(
            f"Saltra response missing fields for SSN '{ssn}' (DNI '{dni}', name '{name_key}')"
        )

    return data


def _build_employee_cache(
    cif: str,
    keys: List[Tuple[str, str]],
    progress: bool,
) -> Dict[Tuple[str, str], Dict[str, str]]:
    employee_cache: Dict[Tuple[str, str], Dict[str, str]] = {}
    total = len(keys)
    for idx, (dni_key, name_key) in enumerate(keys, start=1):
        employee_cache[(dni_key, name_key)] = _fetch_employee_data(cif, dni_key, name_key)
        if progress:
            _render_progress("Lookups", idx, total)
    if progress:
        _finish_progress("Lookups", total)
    return employee_cache


def _dni_variants(dni: str) -> List[str]:
    variants = [dni]
    if dni.startswith("0") and len(dni) > 1:
        variants.append(dni[1:])
    return variants


def _query_ssn_for_employee(session, cif: str, dni: str) -> str | None:
    result = (
        session.query(Employee.ss_number)
        .join(EmployeePeriod, EmployeePeriod.employee_id == Employee.id)
        .join(ClientLocation, ClientLocation.id == EmployeePeriod.location_id)
        .join(Client, Client.id == ClientLocation.company_id)
        .filter(func.upper(Client.cif) == cif, func.upper(Employee.identity_card_number) == dni)
        .order_by(EmployeePeriod.period_begin_date.desc(), EmployeePeriod.id.asc())
        .first()
    )
    if not result or not result[0]:
        return None
    normalized = normalize_ssn(result[0])
    if not normalized:
        return None
    return normalized.replace("/", "")


def _fetch_ssn_from_db(cif: str, dni: str) -> str | None:
    session = get_session()
    try:
        for variant in _dni_variants(dni):
            ssn = _query_ssn_for_employee(session, cif, variant)
            if ssn:
                return ssn
        return None
    finally:
        session.close()


def _assert_unique_names_for_dni(lines: List[str], label: str, dni_set: Set[str]) -> None:
    names_by_dni: Dict[str, Set[str]] = {dni: set() for dni in dni_set}
    for idx, line in enumerate(lines[1:], start=2):
        content, _ = _split_line_ending(line)
        if len(content) != RECORD_LENGTH:
            raise ValueError(f"{label} line {idx} length != {RECORD_LENGTH}: {len(content)}")
        if content[0] != "2":
            continue
        dni_raw = content[PERCEPTOR_DNI_START:PERCEPTOR_DNI_END]
        dni_key = _normalize_key(dni_raw)
        if dni_key in names_by_dni:
            name_raw = content[PERCEPTOR_NAME_START:PERCEPTOR_NAME_END]
            name_key = normalize_text(name_raw)
            names_by_dni[dni_key].add(name_key)

    for dni, names in names_by_dni.items():
        if len(names) > 1:
            raise ValueError(f"{label} has multiple names for DNI '{dni}': {sorted(names)}")


def _update_main_with_errors(
    main_lines: List[str],
    error_lines: List[str],
    progress: bool,
) -> List[str]:
    main_cif = _extract_cif(main_lines, "Main")
    error_cif = _extract_cif(error_lines, "Errors")
    if main_cif != error_cif:
        raise ValueError(f"CIF mismatch: main '{main_cif}' vs errors '{error_cif}'")

    error_keys = _collect_type2_keys(error_lines, "Errors")
    if not error_keys:
        raise ValueError("Errors file contains no type-2 records")

    error_key_set = set(error_keys)
    error_dni_set = {dni for dni, _ in error_key_set}

    _assert_unique_names_for_dni(main_lines, "Main", error_dni_set)

    employee_cache = _build_employee_cache(main_cif, error_keys, progress)

    updated: List[str] = []
    matched_keys = set()
    total_lines = len(main_lines)
    for idx, line in enumerate(main_lines, start=1):
        content, ending = _split_line_ending(line)
        if len(content) != RECORD_LENGTH:
            raise ValueError(f"Main line {idx} length != {RECORD_LENGTH}: {len(content)}")

        if content[0] == "2":
            dni_raw = content[PERCEPTOR_DNI_START:PERCEPTOR_DNI_END]
            name_raw = content[PERCEPTOR_NAME_START:PERCEPTOR_NAME_END]
            dni_key = _normalize_key(dni_raw)
            name_key = normalize_text(name_raw)
            key = (dni_key, name_key)

            if key in error_key_set:
                data = employee_cache[key]
                matched_keys.add(key)

                new_dni = fmt_nif(data["dni"])
                full_name = f"{data['surnames']} {data['name']}"
                new_name = fmt_alpha(full_name, 40)

                content = (
                    content[:PERCEPTOR_DNI_START]
                    + new_dni
                    + content[PERCEPTOR_DNI_END:]
                )
                content = (
                    content[:PERCEPTOR_NAME_START]
                    + new_name
                    + content[PERCEPTOR_NAME_END:]
                )

        updated.append(content + ending)
        if progress:
            _render_progress("Scanning main", idx, total_lines)

    if progress:
        _finish_progress("Scanning main", total_lines)

    missing = error_key_set - matched_keys
    if missing:
        raise ValueError(f"{len(missing)} error record(s) not found in main file: {sorted(missing)[:5]}")

    return updated


def _read_lines(path: str) -> List[str]:
    with open(path, "rb") as f:
        raw = f.read()
    text = raw.decode("iso-8859-1")
    return text.splitlines(keepends=True)


def _write_lines(path: str, lines: Iterable[str]) -> None:
    text = "".join(lines)
    with open(path, "wb") as f:
        f.write(text.encode("iso-8859-1"))


def main() -> int:
    parser = argparse.ArgumentParser(description="Update a Modelo 190 main file using an errors file.")
    parser.add_argument("--main", required=True, help="Path to main .txt file")
    parser.add_argument("--errors", required=True, help="Path to errors .txt file")
    parser.add_argument("--output", help="Output path (default: <main>.updated.txt)")
    parser.add_argument("--dry-run", action="store_true", help="Do not write files; just validate")
    parser.add_argument("--no-progress", action="store_true", help="Disable progress output")
    args = parser.parse_args()

    main_lines = _read_lines(args.main)
    error_lines = _read_lines(args.errors)
    progress = not args.no_progress
    updated = _update_main_with_errors(main_lines, error_lines, progress)

    if args.dry_run:
        print(f"{args.main}: OK ({len(updated)} lines)")
        return 0

    output_path = args.output or f"{args.main}.updated.txt"
    _write_lines(output_path, updated)
    print(f"{args.main}: updated -> {output_path}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
