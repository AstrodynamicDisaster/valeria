from requests import session
import argparse
import json
import tempfile
from pathlib import Path

import core.a3.tools as a3_tools
from core.models import get_id_by_CIF
import core.production_models as prod_models
import core.database as database
from scripts.extract_vida_ccc import import_vida_laboral
from scripts.reprocess_vida_laboral import process_vida_laboral_csv
from scripts.reprocess_prod_query import process_prod_query
from scripts.generate_missing_payslips_report import generate_missing_payslips_report_programmatically
from scripts.ingest_payrolls_mapped import ingest_payrolls_mapped_from_file
from core.missing_payslips import detect_missing_payslips_for_month

def _load_config(folder_name: str) -> tuple[str, str, str, Path, Path | None]:
    base_dir = Path(__file__).resolve().parent
    parsing_dir = base_dir / "parsing" / folder_name
    config_path = parsing_dir / "config.json"

    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")

    with config_path.open("r", encoding="utf-8") as f:
        config = json.load(f)

    cif = config.get("CIF")
    start_month = config.get("start_date")
    end_month = config.get("end_date")
    msj_path = Path(config.get("msj_path", parsing_dir / "msj"))
    if not msj_path.is_absolute():
        msj_path = (parsing_dir / msj_path).resolve()

    if not cif or not start_month or not end_month:
        raise ValueError(f"Config missing CIF/start_date/end_date: {config_path}")

    mappings_dir = None
    for key in ("mappings_folder", "mappings_path", "mappings_dir", "mappings"):
        if config.get(key):
            mappings_dir = Path(config[key])
            break
    if mappings_dir is None:
        mappings_dir = parsing_dir / "mapping"
    if not mappings_dir.is_absolute():
        mappings_dir = (parsing_dir / mappings_dir).resolve()

    return cif, start_month, end_month, msj_path, mappings_dir


def _resolve_msj_paths(msj_dir: Path) -> list[str]:
    if not msj_dir.exists():
        raise FileNotFoundError(f"MSJ directory not found: {msj_dir}")

    msj_files = sorted(msj_dir.glob("*.msj"))
    if not msj_files:
        raise FileNotFoundError(f"No .msj files found in: {msj_dir}")

    return [str(path.resolve()) for path in msj_files]


def _resolve_mapping_files(mappings_dir: Path | None) -> list[Path]:
    if mappings_dir is None or not mappings_dir.exists():
        return []
    candidates = sorted(mappings_dir.glob("*payrolls_mapped*.json"))
    if not candidates:
        candidates = sorted(mappings_dir.glob("*mapped*.json"))
    return [path.resolve() for path in candidates]


parser = argparse.ArgumentParser(description="Process MSJ files for a parsing folder.")
parser.add_argument("folder", help="Folder name under parsing/ (e.g. danik)")
args = parser.parse_args()

CIF, START_MONTH, END_MONTH, msj_dir, mappings_dir = _load_config(args.folder)
MSJ_PATHS = _resolve_msj_paths(msj_dir)

# CONNECTING TO PRODUCTION
print("Connecting to production database...")
prod_session = prod_models.create_production_session()
print("Connected.")

# CONNECTING TO Local DATABASE
print("Connecting to local database...")
local_session = database.get_session(echo=False)
print("Connected.")

# INSERTING COMPANY LOCATIONS INTO LOCAL DATABASE CLIENTS TABLE
print(f"Inserting company locations for CIF {CIF} into local clients...")
prod_models.insert_company_locations_into_local_clients(prod_session, CIF)
print("Done.")

# CREATE A TEMPORARY DIRECTORY FOR PROCESSING FILES
with tempfile.TemporaryDirectory() as temp_dir:
    print(f"Using temporary directory: {temp_dir}")
    temp_dir_path = str(Path(temp_dir).resolve())

    # PARSE MSJ FILE
    for msj_file in MSJ_PATHS:
        import_vida_laboral(msj_file, temp_dir_path)

    # NOW GET THE LIST OF ALL THE CSV FILES GENERATED
    csv_files = list(Path(temp_dir_path).glob("*.csv"))

    # PROCESS EACH CSV FILE
    for csv_file in csv_files:
        result = process_vida_laboral_csv(
            csv_path=str(csv_file),
            client_identifier=CIF,
            create_employees=True
        )

        if result["success"]:
            print(f"Successfully processed {csv_file}")
        else:
            print(f"Failed to process {csv_file}: {result.get('error', 'Unknown error')}")
    

# IMPORT EMPLOYEES AND EMPLOYEE PERIODS FROM PRODUCTION DATABASE

prod_logs = process_prod_query(client_identifier=CIF)
print(f"Production data import result: {prod_logs}")

uuid_client = str(get_id_by_CIF(CIF, local_session).id)

# INGEST MAPPED PAYROLLS (IF PRESENT)
mapping_files = _resolve_mapping_files(mappings_dir)
if mapping_files:
    for mapping_file in mapping_files:
        print(f"Ingesting mapped payrolls from: {mapping_file}")
        ingest_result = ingest_payrolls_mapped_from_file(str(mapping_file))
        if ingest_result.get("success"):
            print(
                "Ingest complete: "
                f"created={ingest_result.get('created')}, "
                f"skipped={ingest_result.get('skipped')}, "
                f"lines_created={ingest_result.get('lines_created')}"
            )
            if ingest_result.get("skipped_log_path"):
                print(f"Skipped records saved to: {ingest_result['skipped_log_path']}")
        else:
            print(f"Failed to ingest mapped payrolls: {ingest_result.get('error')}")
else:
    if mappings_dir is None:
        print("No mappings folder configured; skipping mapped payrolls ingest.")
    else:
        print(f"No mapped payrolls found in: {mappings_dir}")

# GENERATE REPORT FOR REQUIRED PAYSLIPS
result = generate_missing_payslips_report_programmatically(
        client_id=uuid_client,
        output_format="json",
        save_to_file=True,
        filename=f"{CIF}_report.json",
        last_month=END_MONTH,
        start_month=START_MONTH,
    )

print("Missing payslips report generation result:")
if result["success"]:
    print(f"Report saved to: {result.get('file_path', 'N/A')}")
else:
    print(f"Failed to generate report: {result.get('error', 'Unknown error')}") 

# new_result = detect_missing_payslips_for_month(session=local_session, client_id=uuid_client, month="11-2025")

# print("Detect missing payslips for month result:")
# if new_result["success"]:
#     print(f"Missing payslips detected: {new_result.get('missing_payslips', [])}")
# else:
#     print(f"Failed to detect missing payslips: {new_result.get('error', 'Unknown error')}")


# PROCESS PDFS TO EXTRACT PAYSLIPS


# IMPORT REMAINING PAYSLIPS FROM A3

 ## To do this, I need to change the models in the database and implement the mapping from a3 to our models

# ---------------------_TESTING CODE BELOW -----------------------

# Get all payslips for the cif and ccc in the month of november 2025

# perception_codes = a3_tools.get_perception_type_codes()

# # Save codes to file
# with open("perception_codes.json", "w") as f:
#     import json
#     json.dump(perception_codes, f, indent=4)


# outlist = a3_tools.get_payslip_employee(CIF, DNI, MONTH)

# # Transform the dict to a json file and save it
# import json
# with open("payslip_data.json", "w") as f:
#     json.dump(outlist, f, indent=4)
# print("Payslip data saved to payslip_data.json")
