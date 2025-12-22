from requests import session
import core.a3.tools as a3_tools
import core.production_models as prod_models
from scripts.extract_vida_ccc import import_vida_laboral
from scripts.reprocess_vida_laboral import process_vida_laboral_csv
from scripts.reprocess_prod_query import process_prod_query
from scripts.generate_missing_payslips_report import generate_missing_payslips_report_programmatically
import tempfile
from pathlib import Path

CIF = "B42524694" # TEPUY BURGERS SL
DNI = "51774361G"
uuid_client = "6733b4f9-0715-42e2-b074-84e086a5fab1"
# CIF = "B56222938"  # DANIK
# DNI = "04304917F"
# CIF = "B75604249"  # JARVIS
# DNI = "Z2435861M"
# CIF = "B66891201"
# DNI = "49348529M"
MONTH = "2025-11"  # November 2025
START_DATE = "2025-01-01"
END_DATE = "2025-12-31"

# MSJ_FILES =[
#                 "/Users/albert/repos/valeria/parsing/fleets/JARVIS_1.msj",
#                 "/Users/albert/repos/valeria/parsing/fleets/JARVIS_2.msj",
#                 "/Users/albert/repos/valeria/parsing/fleets/JARVIS_3.msj",
#                 "/Users/albert/repos/valeria/parsing/fleets/JARVIS_4.msj",
#                 "/Users/albert/repos/valeria/parsing/fleets/JARVIS_5.msj",
#                 "/Users/albert/repos/valeria/parsing/fleets/JARVIS_6.msj",
#                 "/Users/albert/repos/valeria/parsing/fleets/JARVIS_7.msj",
#                 "/Users/albert/repos/valeria/parsing/fleets/JARVIS_8.msj",
#                 "/Users/albert/repos/valeria/parsing/fleets/JARVIS_9.msj",
#                 "/Users/albert/repos/valeria/parsing/fleets/JARVIS_10.msj",
#                 "/Users/albert/repos/valeria/parsing/fleets/JARVIS_11.msj",
#                 "/Users/albert/repos/valeria/parsing/fleets/JARVIS_12.msj"
#                 ]
MSJ_FILES = []
PDF_FILES = [
             "/path/to/first_file.pdf",
             "/path/to/second_file.pdf"]

# CONVERT THE PATHS TO ABSOLUTE PATHS
MSJ_PATHS = [str(Path(path).resolve()) for path in MSJ_FILES]
PDF_PATHS = [str(Path(path).resolve()) for path in PDF_FILES]

# CONNECTING TO PRODUCTION
print("Connecting to production database...")
prod_session = prod_models.create_production_session()
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

# GENERATE REPORT FOR REQUIRED PAYSLIPS
result = generate_missing_payslips_report_programmatically(
        client_id=uuid_client,
        output_format="json",
        save_to_file=True,
        filename="pipeline_test.json",
        last_month="12/2025",
    )

print("Missing payslips report generation result:")
if result["success"]:
    print(f"Report saved to: {result.get('file_path', 'N/A')}")
else:
    print(f"Failed to generate report: {result.get('error', 'Unknown error')}") 


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
