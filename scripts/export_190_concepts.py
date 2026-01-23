#!/usr/bin/env python3
"""
Export payroll concepts for Modelo 190 mapping.

Outputs a JSON report grouping by normalized concept to ease mapping.
Optionally exports a YAML bucket template with all concepts in clave A and
empty buckets for commonly-used subclaves.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from collections import defaultdict
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from typing import Any, Iterable

# Ensure repo root is on path
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from core.database import get_session
from core.models import PayrollLine
import importlib

_modelo_190 = importlib.import_module("190")
normalize_concept_key = _modelo_190.normalize_concept_key

try:
    import yaml
except ImportError:  # pragma: no cover - optional dependency for YAML
    yaml = None


DEFAULT_BUCKETS = [
    {"clave": "L", "subclave": "01", "concepts": []},
    {"clave": "L", "subclave": "05", "concepts": []},
    {"clave": "L", "subclave": "24", "concepts": []},
    {"clave": "L", "subclave": "25", "concepts": []},
    {"clave": "L", "subclave": "26", "concepts": []},
]
DEFAULT_PROVINCIA = "98"


def _require_yaml() -> None:
    if yaml is None:
        raise RuntimeError("PyYAML is required for YAML support. Install with `pip install PyYAML`.")


def _load_structured_payload(path: str) -> dict:
    suffix = os.path.splitext(path)[1].lower()
    with open(path, "r", encoding="utf-8") as handle:
        if suffix in {".yml", ".yaml"}:
            _require_yaml()
            return yaml.safe_load(handle) or {}
        return json.load(handle)


def _dump_yaml(payload: dict) -> str:
    _require_yaml()
    return yaml.safe_dump(payload, allow_unicode=True, sort_keys=False)


def _normalize_concepts(values: Iterable[Any]) -> list[str]:
    normalized: list[str] = []
    for value in values:
        key = normalize_concept_key(str(value)) if value is not None else ""
        if key:
            normalized.append(key)
    return normalized


def _dedupe_keep_order(values: Iterable[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        result.append(value)
    return result


def _normalize_manual_nif(value: Any) -> str:
    raw = str(value or "").strip().upper().replace(" ", "")
    if len(raw) == 8 and raw and not raw[0].isalpha():
        raw = f"0{raw}"
    return raw


def _normalize_manual_name(value: Any) -> str:
    return " ".join(str(value or "").strip().upper().split())


def _normalize_provincia(value: Any, default_provincia: str) -> str:
    if value is None or str(value).strip() == "":
        return default_provincia
    raw = str(value).strip()
    if not raw.isdigit():
        raise ValueError(f"Provincia '{raw}' must be numeric.")
    return raw.zfill(2)


def _normalize_manual_date(value: Any) -> str:
    if value is None or str(value).strip() == "":
        raise ValueError("clave G entry missing 'fecha'.")
    raw = str(value).strip()
    for fmt in ("%Y-%m-%d", "%d-%m-%Y", "%d/%m/%Y"):
        try:
            return datetime.strptime(raw, fmt).date().isoformat()
        except ValueError:
            continue
    raise ValueError(f"clave G entry invalid 'fecha' format: {raw!r}. Use YYYY-MM-DD.")


def _to_decimal(value: Any, field_name: str) -> Decimal:
    try:
        return Decimal(str(value))
    except (InvalidOperation, TypeError) as exc:
        raise ValueError(f"Invalid numeric value for '{field_name}': {value!r}") from exc


def _collect_concepts() -> tuple[int, list[dict[str, Any]]]:
    session = get_session()
    try:
        query = session.query(
            PayrollLine.concept,
            PayrollLine.category,
            PayrollLine.is_taxable_income,
            PayrollLine.is_sickpay,
            PayrollLine.is_in_kind,
        )

        aggregates: dict[str, dict[str, Any]] = {}
        total_lines = 0

        for concept, category, is_taxable_income, is_sickpay, is_in_kind in query.yield_per(10000):
            total_lines += 1
            normalized = normalize_concept_key(concept)
            if normalized not in aggregates:
                aggregates[normalized] = {
                    "normalized": normalized,
                    "raw_variants": set(),
                    "count": 0,
                    "category_counts": defaultdict(int),
                    "taxable_income_count": 0,
                    "sickpay_count": 0,
                    "in_kind_count": 0,
                    "mapping": {
                        "clave": None,
                        "subclave": None,
                        "ss_tax": None,
                    },
                }

            entry = aggregates[normalized]
            entry["count"] += 1
            entry["raw_variants"].add(concept or "")
            entry["category_counts"][str(category or "").lower()] += 1
            if is_taxable_income:
                entry["taxable_income_count"] += 1
            if is_sickpay:
                entry["sickpay_count"] += 1
            if is_in_kind:
                entry["in_kind_count"] += 1

        concepts: list[dict[str, Any]] = []
        for entry in aggregates.values():
            entry["raw_variants"] = sorted(value for value in entry["raw_variants"] if value)
            entry["category_counts"] = dict(sorted(entry["category_counts"].items()))
            concepts.append(entry)

        concepts.sort(key=lambda item: (-item["count"], item["normalized"]))
        return total_lines, concepts
    finally:
        session.close()


def export_concepts(output_path: str | None) -> None:
    total_lines, concepts = _collect_concepts()

    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "total_lines": total_lines,
        "concepts": concepts,
    }

    output = json.dumps(payload, ensure_ascii=False, indent=2)
    if output_path:
        with open(output_path, "w", encoding="utf-8") as handle:
            handle.write(output)
    else:
        print(output)


def export_bucket_template(output_path: str | None) -> None:
    total_lines, concepts = _collect_concepts()
    default_devengo: list[str] = []
    default_deduccion: list[str] = []

    for entry in concepts:
        normalized = entry.get("normalized")
        if not normalized:
            continue
        counts = entry.get("category_counts") or {}
        devengo_count = int(counts.get("devengo", 0))
        deduccion_count = int(counts.get("deduccion", 0))

        if devengo_count == 0 and deduccion_count == 0:
            continue
        if devengo_count >= deduccion_count:
            default_devengo.append(normalized)
        else:
            default_deduccion.append(normalized)

    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "total_lines": total_lines,
        "default_provincia": DEFAULT_PROVINCIA,
        "default_clave": "A",
        "concepts_in_default_clave": {
            "devengo": default_devengo,
            "deduccion": default_deduccion,
        },
        "buckets": DEFAULT_BUCKETS,
        "ss_tax_concepts": [],
        "clave G": [],
    }

    output = _dump_yaml(payload)
    if output_path:
        with open(output_path, "w", encoding="utf-8") as handle:
            handle.write(output)
    else:
        print(output)


def _build_mapping_from_report_payload(payload: dict) -> dict:
    concepts = payload.get("concepts", []) or []
    concepts_to_clave_subclave: dict[tuple[str, str | None], list[str]] = {}
    ss_tax_concepts: set[str] = set()

    for entry in concepts:
        normalized = entry.get("normalized") or ""
        if not normalized:
            continue
        mapping = entry.get("mapping") or {}
        clave = mapping.get("clave")
        subclave = mapping.get("subclave")
        ss_tax = mapping.get("ss_tax")

        if isinstance(clave, str) and clave.strip():
            clave = clave.strip().upper()
            if isinstance(subclave, str) and subclave.strip():
                subclave = subclave.strip().zfill(2)
            else:
                subclave = None

            if clave in {"B", "C", "E", "F", "G", "H", "I", "K", "L"} and not subclave:
                raise ValueError(f"Concept '{normalized}' mapped to clave '{clave}' without subclave.")

            key = (clave, subclave)
            concepts_to_clave_subclave.setdefault(key, []).append(normalized)

        if ss_tax is True:
            ss_tax_concepts.add(normalized)

    return {
        "concepts_to_clave_subclave": [
            {"clave": clave, "subclave": subclave, "concepts": sorted(concepts)}
            for (clave, subclave), concepts in sorted(concepts_to_clave_subclave.items())
        ],
        "ss_tax_concepts": sorted(ss_tax_concepts),
    }


def _build_mapping_from_bucket_payload(payload: dict) -> dict:
    default_provincia = _normalize_provincia(payload.get("default_provincia"), DEFAULT_PROVINCIA)
    default_list = payload.get("concepts_in_default_clave", []) or []
    if isinstance(default_list, dict):
        default_list = list(default_list.get("devengo", []) or []) + list(default_list.get("deduccion", []) or [])
    default_concepts = _dedupe_keep_order(_normalize_concepts(default_list))
    if not default_concepts:
        raise ValueError("Bucket mapping requires 'concepts_in_default_clave' to be a non-empty list.")
    buckets = payload.get("buckets", []) or []
    if not isinstance(buckets, list):
        raise ValueError("'buckets' must be a list of bucket entries.")

    concepts_to_clave_subclave: dict[tuple[str, str | None], list[str]] = {}
    seen: set[str] = set()

    for bucket in buckets:
        if not isinstance(bucket, dict):
            raise ValueError("Each bucket entry must be a mapping.")
        clave = bucket.get("clave")
        if not isinstance(clave, str) or not clave.strip():
            raise ValueError("Bucket entries must include a non-empty 'clave'.")
        clave = clave.strip().upper()
        subclave = bucket.get("subclave")
        if isinstance(subclave, str) and subclave.strip():
            subclave = subclave.strip().zfill(2)
        else:
            subclave = None

        if clave in {"B", "C", "E", "F", "G", "H", "I", "K", "L"} and not subclave:
            raise ValueError(f"Bucket clave '{clave}' requires a subclave.")

        raw_concepts = bucket.get("concepts", []) or []
        normalized = _dedupe_keep_order(_normalize_concepts(raw_concepts))

        for concept in normalized:
            if concept in seen:
                raise ValueError(f"Concept '{concept}' appears in multiple buckets.")
            seen.add(concept)

        if normalized:
            concepts_to_clave_subclave.setdefault((clave, subclave), []).extend(normalized)

    ss_tax_raw = payload.get("ss_tax_concepts", []) or []
    ss_tax_concepts = _dedupe_keep_order(_normalize_concepts(ss_tax_raw))

    manual_raw = payload.get("clave G")
    if manual_raw is None:
        manual_raw = payload.get("manual_clave_g", [])
    manual_raw = manual_raw or []
    if not isinstance(manual_raw, list):
        raise ValueError("'clave G' must be a list.")

    manual_entries: list[dict[str, Any]] = []
    seen_manual: dict[str, tuple[str, str]] = {}
    for idx, entry in enumerate(manual_raw, start=1):
        if not isinstance(entry, dict):
            raise ValueError(f"clave G entry {idx} must be a mapping.")
        nif = _normalize_manual_nif(entry.get("nif"))
        if not nif:
            raise ValueError(f"clave G entry {idx} missing 'nif'.")
        if len(nif) != 9:
            raise ValueError(f"clave G entry {idx} NIF must be 9 characters after normalization.")
        nombre = str(entry.get("nombre") or "").strip()
        if not nombre:
            raise ValueError(f"clave G entry {idx} missing 'nombre'.")
        fecha = _normalize_manual_date(entry.get("fecha") or entry.get("date"))
        percep = entry.get("percepciones_integras")
        ret = entry.get("retenciones")
        if percep is None or ret is None:
            raise ValueError(
                f"clave G entry {idx} requires 'percepciones_integras' and 'retenciones'."
            )
        percep_val = _to_decimal(percep, "percepciones_integras")
        ret_val = _to_decimal(ret, "retenciones")
        if percep_val < 0 or ret_val < 0:
            raise ValueError(f"clave G entry {idx} has negative amounts.")
        provincia_default = "98" if default_provincia == "00" else default_provincia
        provincia = _normalize_provincia(entry.get("provincia"), provincia_default)

        name_key = _normalize_manual_name(nombre)
        if nif in seen_manual:
            prev_name, prev_prov = seen_manual[nif]
            if name_key != prev_name:
                raise ValueError(
                    f"clave G entry {idx} NIF '{nif}' has inconsistent nombre."
                )
            if provincia != prev_prov:
                raise ValueError(
                    f"clave G entry {idx} NIF '{nif}' has inconsistent provincia."
                )
        else:
            seen_manual[nif] = (name_key, provincia)

        manual_entries.append(
            {
                "nif": nif,
                "nombre": nombre,
                "provincia": provincia,
                "percepciones_integras": str(percep_val),
                "retenciones": str(ret_val),
                "fecha": fecha,
            }
        )
    return {
        "concepts_to_clave_subclave": [
            {"clave": clave, "subclave": subclave, "concepts": sorted(concepts)}
            for (clave, subclave), concepts in sorted(concepts_to_clave_subclave.items())
        ],
        "ss_tax_concepts": sorted(set(ss_tax_concepts)),
        "clave G": manual_entries,
        "default_provincia": default_provincia,
    }


def build_mapping_from_report(report_path: str, output_path: str) -> None:
    payload = _load_structured_payload(report_path)
    if "concepts" in payload:
        mapping_payload = _build_mapping_from_report_payload(payload)
    elif "concepts_in_default_clave" in payload:
        mapping_payload = _build_mapping_from_bucket_payload(payload)
    else:
        raise ValueError("Unrecognized mapping input. Expected 'concepts' or 'concepts_in_default_clave'.")

    with open(output_path, "w", encoding="utf-8") as handle:
        json.dump(mapping_payload, handle, ensure_ascii=False, indent=2)


def main() -> int:
    parser = argparse.ArgumentParser(description="Export concepts for Modelo 190 mapping.")
    parser.add_argument("--out", help="Output path (defaults to stdout).")
    parser.add_argument(
        "--bucket-template",
        action="store_true",
        help="Export YAML bucket template with all concepts in clave A.",
    )
    parser.add_argument("--mapping-from", help="Input mapping file (JSON report or YAML buckets).")
    parser.add_argument("--mapping-out", help="Output mapping JSON path.")
    args = parser.parse_args()

    if args.mapping_from:
        if not args.mapping_out:
            raise ValueError("--mapping-out is required when using --mapping-from.")
        build_mapping_from_report(args.mapping_from, args.mapping_out)
    elif args.bucket_template:
        export_bucket_template(args.out)
    else:
        export_concepts(args.out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
