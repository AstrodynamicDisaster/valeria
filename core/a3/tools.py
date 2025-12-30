import requests
from typing import Any, Optional
import logging
import json
from . import config as Config
from . import mappings
#import config as Config
#import mappings
from datetime import datetime
# Import Payroll models from core/models but imagining we are inside the a3 folder

# PAGINATION_DATA
DEFAULT_PAGESIZE = 25
PAGINATION_HEADER = "X-Pagination"
TOTAL_PAGES = "totalPages"
TOTAL_COUNT = "totalCount"
PAGE_NUMBER = "pageNumber"
PAGE_SIZE = "pageSize"

# THIS IS THE FORMAT FOR DATES '2025-09-30T00:00:00Z'


# API URL ENDPOINTS
COMPANIES_ENDPOINT = "companies"
EMPLOYEES_ENDPOINT = "employees"
SALARY_ENDPOINT = "pactedsalary"
PAYROLLS_ENDPOINT = "pays"
PAYROLL_DATA_ENDPOINT = "paydata"
PAYROLL_CONCEPTS_ENDPOINT = "concepts"
PAYROLL_INTERNAL_CONCEPTS_ENDPOINT = "calculatedinternalconcepts"
AGREEMENTS_ENDPOINT = "agreements"
CONCEPTS_ENDPOINT = "concepts"
PERCEPTION_TYPE_CODES_ENDPOINT = "paytypes"

# ENDPOINT KEYS
COMPANY_CODE = "companyCode"
NIF = "identifierNumber"
EMPLOYEE_A3_CODE = "employeeCode"
START_DATE = "periodStartDate"
END_DATE = "periodEndDate"


def get_bearer_token() -> str | None:
    """
    Retrieves the Bearer token using the refresh token.
    """
    data = {
        "client_id": Config.CLIENT_ID,
        "client_secret": Config.CLIENT_SECRET,
        "grant_type": "refresh_token",
        "refresh_token": Config.REFRESH_TOKEN,
        "update": True
    }
    headers = {"Content-Type": "application/x-www-form-urlencoded"}

    response = requests.post(Config.AUTH_URL, data=data, headers=headers)

    if response.status_code == 200:
        token = response.json().get("access_token")
        if token:
                return f"Bearer {token}"
    return None


def get_headers() -> dict | None:
    try:
        token = get_bearer_token()
    except Exception as e:
        logging.error(f"Exception while obtaining Bearer token: {str(e)}")
        return

    if token is None:
        logging.error("Error obtaining Wolters Bearer token")
        return

    headers = {
        "Authorization": token,
        "Ocp-Apim-Subscription-Key": Config.SUBSCRIPTION_KEY,
        "Content-Type": "application/json",
        "Accept": "*/*",
    }

    return headers


def get_company_id(cif: str) -> str | None:

    headers = get_headers()

    try:
        companies_url = f"{Config.WOLTERS_API_BASE_URL}/{COMPANIES_ENDPOINT}"
        data = {
            PAGE_NUMBER: 1,
            PAGE_SIZE: DEFAULT_PAGESIZE,
            "filter": f"contains({NIF},'{cif}')" 
        }
        response = requests.get(companies_url, headers=headers, params=data)
        if response.status_code != 200:
            logging.error(f"Error fetching companies: {response.status_code} - {response.text}")
            return
        return response.json()[0][COMPANY_CODE]

    except Exception as e:
        logging.error(f"Unexpected error: {e}")


def get_company_employees(company_id: int, period_start: Optional[str] = None, period_end: Optional[str] = None) -> list | None:

    headers = get_headers()

    employee_list = []
    try:
        employees_url = f"{Config.WOLTERS_API_BASE_URL}/{COMPANIES_ENDPOINT}/{company_id}/{EMPLOYEES_ENDPOINT}"
        data = {
            PAGE_NUMBER: 1,
            PAGE_SIZE: DEFAULT_PAGESIZE 
        }
        response = requests.get(employees_url, headers=headers, params=data)

        employee_list.append(response.json())

        # Get remaining pages from header
        metadata = json.loads(response.headers[PAGINATION_HEADER])
        total_pages = metadata[TOTAL_PAGES]
        total_count = metadata[TOTAL_COUNT]

        if total_pages > 1:
            for page in range(2, total_pages + 1):
                data[PAGE_NUMBER] = page
                response = requests.get(employees_url, headers=headers, params=data)
                employee_list.append(response.json())

            if len(employee_list) != total_count:
                logging.warning(f"Expected {total_count} employees but got {len(employee_list)}")
            
            return employee_list

        if response.status_code != 200:
            logging.error(f"Error fetching companies: {response.status_code} - {response.text}")
            return
        return response.json()

    except Exception as e: 
        logging.error(f"Unexpected error: {e}")


def get_employee_by_dni(company_id: str, dni: str) -> Optional[dict[str, Any]]:

    headers = get_headers()

    try:
        employees_url = f"{Config.WOLTERS_API_BASE_URL}/{COMPANIES_ENDPOINT}/{company_id}/{EMPLOYEES_ENDPOINT}"
        data = {
            PAGE_NUMBER: 1,
            PAGE_SIZE: DEFAULT_PAGESIZE,
            "filter": f"contains({NIF},'{dni}')"
        }
        response = requests.get(employees_url, headers=headers, params=data)

        if response.status_code != 200:
            logging.error(f"Error fetching companies: {response.status_code} - {response.text}")
            return
        return response.json()[0]

    except Exception as e: 
        logging.error(f"Unexpected error: {e}")


def get_employee_salary(employee_id: str, company_id: str) -> str | None:

    headers = get_headers()

    try:
        salary_url = f"{Config.WOLTERS_API_BASE_URL}/{COMPANIES_ENDPOINT}/{company_id}/{EMPLOYEES_ENDPOINT}/{employee_id}/{SALARY_ENDPOINT}"
        response = requests.get(salary_url, headers=headers)

        if response.status_code != 200:
            logging.error(f"Error fetching companies: {response.status_code} - {response.text}")
            return
        return response.json()

    except Exception as e: 
        logging.error(f"Unexpected error: {e}")


def get_employee_payrolls(employee_id: str, company_id: str, date_from: Optional[str] = None, date_to: Optional[str] = None ) -> list | None:

    headers = get_headers()

    try:
        payroll_url = f"{Config.WOLTERS_API_BASE_URL}/{COMPANIES_ENDPOINT}/{company_id}/{EMPLOYEES_ENDPOINT}/{employee_id}/{PAYROLLS_ENDPOINT}"
        data = {
            PAGE_NUMBER: 1,
            PAGE_SIZE: DEFAULT_PAGESIZE
        }
        response = requests.get(payroll_url, headers=headers, params=data)

        if response.status_code != 200:
            logging.error(f"Error fetching payrolls: {response.status_code} - {response.text}")
            return

        first_page = response.json()
        payrolls = first_page if isinstance(first_page, list) else [first_page]

        # Get remaining pages from header
        metadata = json.loads(response.headers[PAGINATION_HEADER])
        total_pages = metadata[TOTAL_PAGES]
        total_count = metadata[TOTAL_COUNT]

        if total_pages > 1:
            for page in range(2, total_pages + 1):
                data[PAGE_NUMBER] = page
                response = requests.get(payroll_url, headers=headers, params=data)

                if response.status_code != 200:
                    logging.error(f"Error fetching payrolls page {page}: {response.status_code} - {response.text}")
                    return

                page_data = response.json()
                if isinstance(page_data, list):
                    payrolls.extend(page_data)
                else:
                    payrolls.append(page_data)

        if len(payrolls) != total_count:
            logging.warning(f"Expected {total_count} payroll records but got {len(payrolls)}")

        return payrolls

    except Exception as e: 
        logging.error(f"Unexpected error: {e}")


def get_payslip_data(payslip_id: str, employee_id: str, company_id: str) -> str | None:

    headers = get_headers()

    try:
        payslip_url = f"{Config.WOLTERS_API_BASE_URL}/{COMPANIES_ENDPOINT}/{company_id}/{EMPLOYEES_ENDPOINT}/{employee_id}/{PAYROLLS_ENDPOINT}/{payslip_id}/{PAYROLL_DATA_ENDPOINT}"
        response = requests.get(payslip_url, headers=headers)

        if response.status_code != 200:
            logging.error(f"Error fetching companies: {response.status_code} - {response.text}")
            return
        return response.json()[0]

    except Exception as e: 
        logging.error(f"Unexpected error: {e}")
        return


def extract_payslip_data(payslip: dict, payslip_data: dict) -> dict:
    """Extract relevant data from a payslip dictionary."""
    
    start_raw = payslip.get(START_DATE)
    end_raw = payslip.get(END_DATE)
    if not isinstance(start_raw, str) or not isinstance(end_raw, str):
        raise ValueError("Payslip start/end dates must be ISO strings.")
    date_from = datetime.fromisoformat(start_raw)
    date_to = datetime.fromisoformat(end_raw)
    days = min(30, (date_to - date_from).days +1)

    payroll = {
        "periodo": {
            "desde": date_from.date().isoformat(),
            "hasta":  date_to.date().isoformat(),
            "dias": days

        },
        "devengo_total": payslip_data["totalGross"],
        "deduccion_total": payslip_data["totalDeduction"],
        "aportacion_empresa_total": payslip_data["costBusiness"],
        "liquido_a_percibir": payslip_data["totalGross"] - payslip_data["totalDeduction"],
        "prorrata_pagas_extra": payslip_data.get("prorratedExtraPay", 0),
        "base_cc": payslip_data.get("baseCC", 0),
        "base_at_ep": payslip_data.get("baseAC", 0),
        "base_irpf": payslip_data.get("totalBaseIRPF", 0),
        "tipo_irpf": payslip_data.get("tipoIRPF", 0),
        "warnings": "downlodaded from a3"}

    return payroll

def extract_payslip_concepts(concept_list: list)-> list:

    extracted_concepts = []
    for concept in concept_list:

        if concept.get("PayConceptAmount") == 0.0:
            continue

        concept_code = concept.get("conceptCode")
        payroll_line = {
            "category": "deduccion" if _bool(concept.get("isDiscount")) else "devengo",
            "concept": concept.get("description"),
            "amount": concept.get("payConceptAmount"),
            "is_taxable_income": mappings.is_taxable_income(concept_code),
            "is_taxable_ss": "",
            "is_sickpay": "",
            "is_in_kind": "",
            "is_pay_advance": "",
            "is_seizure": ""
        }



    
    return extracted_concepts



# def extract_payslip_internal_concepts():

#     date_from = datetime.fromisoformat(payslip.get(START_DATE))
#     date_to = datetime.fromisoformat(payslip.get(END_DATE))
#     days = min(30, (date_to - date_from).days +1)

#     payroll = {
#         "periodo": {
#             "desde": date_from.date().isoformat(),
#             "hasta":  date_to.date().isoformat(),
#             "dias": days

#         },
#         "devengo_total": payslip_data["totalGross"],
#         "deduccion_total": payslip_data["totalDeduction"],
#         "aportacion_empresa_total": payslip_data["costBusiness"],
#         "liquido_a_percibir": payslip_data["totalGross"] - payslip_data["totalDeduction"],
#         "prorrata_pagas_extra": payslip_data.get("prorratedExtraPay", 0),
#         "base_cc": payslip_data.get("baseCC", 0),
#         "base_at_ep": payslip_data.get("baseAC", 0),
#         "base_irpf": payslip_data.get("totalBaseIRPF", 0),
#         "tipo_irpf": payslip_data.get("tipoIRPF", 0),
#         "warnings": "downlodaded from a3"}

#     return payroll

def _parse_iso_date(date_str: str) -> datetime:
    """
    Safely parse ISO date strings that may end with 'Z' by converting
    to a timezone-aware datetime. Falls back to naive UTC if offset is
    missing.
    """
    if date_str.endswith("Z"):
        date_str = date_str.replace("Z", "+00:00")
    return datetime.fromisoformat(date_str)


def get_payslip_employee(company_cif: str, employee_id: str, month_iso: str):
    """
    Return the payslip dict for a given employee (by DNI/NIE) and month.

    Args:
        company_cif: Company CIF used to resolve company code.
        employee_id: Employee DNI/NIE used to resolve employee code.
        month_iso: Month in ISO format. Accepts `YYYY-MM` or any complete
                   ISO date string; only year and month are used.

    Raises:
        ValueError: When no payslip matches the month, or when more than
                    one payslip matches (ambiguous).
    """
    # Normalize target month
    try:
        target_date = datetime.fromisoformat(month_iso + "-01") if len(month_iso) == 7 else datetime.fromisoformat(month_iso)
    except Exception as exc:
        raise ValueError(f"Invalid month format '{month_iso}'. Use 'YYYY-MM'.") from exc

    company_code = get_company_id(company_cif)
    if company_code is None:
        raise ValueError(f"Company not found for CIF {company_cif}.")
    employee_data = get_employee_by_dni(company_code, employee_id)
    if not employee_data or EMPLOYEE_A3_CODE not in employee_data:
        raise ValueError(f"Employee not found for DNI/NIE {employee_id}.")
    employee_code = employee_data[EMPLOYEE_A3_CODE]
    payslips = get_employee_payrolls(employee_code, company_code)

    # Normalise paging shape (get_employee_payrolls may return list of pages)
    if payslips and isinstance(payslips[0], list):
        payslips = [p for page in payslips for p in page]

    if not payslips:
        raise ValueError(f"No payslips found for employee {employee_id}.")

    matching = []
    for payslip in payslips:
        start = _parse_iso_date(payslip.get("periodStartDate"))
        end = _parse_iso_date(payslip.get("periodEndDate"))

        # Use the period start/end dates to match the requested month.
        if start.year == target_date.year and start.month == target_date.month \
           and end.year == target_date.year and end.month == target_date.month:
            matching.append(payslip)
            print("MATCHING PAYSLIP")



    if not matching:
        raise ValueError(f"No payslip found for {employee_id} in {target_date.strftime('%Y-%m')}.")
    #if len(matching) > 1:
        #raise ValueError(f"More than one payslip found for {employee_id} in {target_date.strftime('%Y-%m')}.")
    

    retrieved_payslips = []

    for payslip in matching:

        payslip_glob = payslip
        payslip_id = payslip["payId"]
        payslip_data = get_payslip_data(payslip_id, employee_code, company_code)
        #extracted = extract_payslip_data(matching[0], payslip_data)

        #matching[0]=
        raw_concepts = get_payslip_concepts(company_code, employee_code, payslip_id)
        internal_concepts = get_internal_payslip_concepts(company_code, employee_code, payslip_id)

        extracted_lines = []
        
        # print("RAW CONCEPTS:", internal_concepts)

        out_dict = {
            "payslip": payslip_glob,
            "data": payslip_data,
            "raw_concepts": raw_concepts,
            "internal_concepts": internal_concepts,
        }
        retrieved_payslips.append(out_dict)

    return retrieved_payslips


def get_payslip_concepts(company_code: str, employee_code: str, payslip_id: str) -> list | None:

    headers = get_headers()

    try:
        payslip_concepts_url = f"{Config.WOLTERS_API_BASE_URL}/{COMPANIES_ENDPOINT}/{company_code}/{EMPLOYEES_ENDPOINT}/{employee_code}/{PAYROLLS_ENDPOINT}/{payslip_id}/{PAYROLL_CONCEPTS_ENDPOINT}"
        data = {
            PAGE_NUMBER: 1,
            PAGE_SIZE: DEFAULT_PAGESIZE
        }
        response = requests.get(payslip_concepts_url, headers=headers, params=data)

        if response.status_code != 200:
            logging.error(f"Error fetching payslip concepts: {response.status_code} - {response.text}")
            return

        first_page = response.json()
        concepts = first_page if isinstance(first_page, list) else [first_page]

        # Get remaining pages from header
        metadata = json.loads(response.headers[PAGINATION_HEADER])
        total_pages = metadata[TOTAL_PAGES]
        total_count = metadata[TOTAL_COUNT]

        if total_pages > 1:
            for page in range(2, total_pages + 1):
                data[PAGE_NUMBER] = page
                response = requests.get(payslip_concepts_url, headers=headers, params=data)

                if response.status_code != 200:
                    logging.error(f"Error fetching payslip concepts page {page}: {response.status_code} - {response.text}")
                    return

                page_data = response.json()
                if isinstance(page_data, list):
                    concepts.extend(page_data)
                else:
                    concepts.append(page_data)

        if len(concepts) != total_count:
            logging.warning(f"Expected {total_count} payslip concept records but got {len(concepts)}")

        return concepts

    except Exception as e: 
        logging.error(f"Unexpected error: {e}")
        return
    
def get_internal_payslip_concepts(company_code: str, employee_code: str, payslip_id: str) -> list | None:

    headers = get_headers()

    try:
        payslip_internal_concepts_url = f"{Config.WOLTERS_API_BASE_URL}/{COMPANIES_ENDPOINT}/{company_code}/{EMPLOYEES_ENDPOINT}/{employee_code}/{PAYROLLS_ENDPOINT}/{payslip_id}/{PAYROLL_INTERNAL_CONCEPTS_ENDPOINT}"
        data = {
            PAGE_NUMBER: 1,
            PAGE_SIZE: DEFAULT_PAGESIZE
        }
        response = requests.get(payslip_internal_concepts_url, headers=headers, params=data)

        if response.status_code != 200:
            logging.error(f"Error fetching payslip concepts: {response.status_code} - {response.text}")
            return

        first_page = response.json()
        internal_concepts = first_page if isinstance(first_page, list) else [first_page]

        # Get remaining pages from header
        metadata = json.loads(response.headers[PAGINATION_HEADER])
        total_pages = metadata[TOTAL_PAGES]
        total_count = metadata[TOTAL_COUNT]

        if total_pages > 1:
            for page in range(2, total_pages + 1):
                data[PAGE_NUMBER] = page
                response = requests.get(payslip_internal_concepts_url, headers=headers, params=data)

                if response.status_code != 200:
                    logging.error(f"Error fetching payslip concepts page {page}: {response.status_code} - {response.text}")
                    return

                page_data = response.json()
                if isinstance(page_data, list):
                    internal_concepts.extend(page_data)
                else:
                    internal_concepts.append(page_data)

        if len(internal_concepts) != total_count:
            logging.warning(f"Expected {total_count} payslip concept records but got {len(internal_concepts)}")

        return internal_concepts

    except Exception as e: 
        logging.error(f"Unexpected error: {e}")
        return

def get_company_agreements(company_cif: str) -> list | None:

    company_id = get_company_id(company_cif)

    headers = get_headers()

    agreements_list = []
    try:
        company_agreements_url = f"{Config.WOLTERS_API_BASE_URL}/{COMPANIES_ENDPOINT}/{company_id}/{AGREEMENTS_ENDPOINT}"
        data = {
            PAGE_NUMBER: 1,
            PAGE_SIZE: DEFAULT_PAGESIZE 
        }
        response = requests.get(company_agreements_url, headers=headers, params=data)

        agreements_list.append(response.json())

        # Get remaining pages from header
        metadata = json.loads(response.headers[PAGINATION_HEADER])
        total_pages = metadata[TOTAL_PAGES]
        total_count = metadata[TOTAL_COUNT]

        if total_pages > 1:
            for page in range(2, total_pages + 1):
                data[PAGE_NUMBER] = page
                response = requests.get(company_agreements_url, headers=headers, params=data)
                agreements_list.append(response.json())

            if len(agreements_list) != total_count:
                logging.warning(f"Expected {total_count} employees but got {len(agreements_list)}")
            
            return agreements_list

        if response.status_code != 200:
            logging.error(f"Error fetching companies: {response.status_code} - {response.text}")
            return
        return response.json()

    except Exception as e: 
        logging.error(f"Unexpected error: {e}")

def get_agreement_details(agreement_id: str) -> None:
    pass

def get_company_concepts(company_cif: str) -> list | None:

    company_id = get_company_id(company_cif)

    headers = get_headers()

    concepts_list = []
    try:
        company_concepts_url = f"{Config.WOLTERS_API_BASE_URL}/{COMPANIES_ENDPOINT}/{company_id}/{CONCEPTS_ENDPOINT}"
        data = {
            PAGE_NUMBER: 1,
            PAGE_SIZE: DEFAULT_PAGESIZE 
        }
        response = requests.get(company_concepts_url, headers=headers, params=data)

        concepts_list.append(response.json())

        # Get remaining pages from header
        metadata = json.loads(response.headers[PAGINATION_HEADER])
        total_pages = metadata[TOTAL_PAGES]
        total_count = metadata[TOTAL_COUNT]

        if total_pages > 1:
            for page in range(2, total_pages + 1):
                data[PAGE_NUMBER] = page
                response = requests.get(company_concepts_url, headers=headers, params=data)
                concepts_list.append(response.json())

            if len(concepts_list) != total_count:
                logging.warning(f"Expected {total_count} employees but got {len(concepts_list)}")
            
            return concepts_list

        if response.status_code != 200:
            logging.error(f"Error fetching companies: {response.status_code} - {response.text}")
            return
        return response.json()

    except Exception as e: 
        logging.error(f"Unexpected error: {e}")

def get_perception_type_codes() -> list | None:
    """
    Fetches the catalog of perception type codes exposed by the A3 API.

    Returns:
        A list with the perception type code objects, or None if the call fails.
    """
    headers = get_headers()
    try:
        url = f"{Config.WOLTERS_API_BASE_URL}/{PERCEPTION_TYPE_CODES_ENDPOINT}"
        response = requests.get(url, headers=headers)

        if response.status_code != 200:
            logging.error(
                f"Error fetching perception type codes: {response.status_code} - {response.text}"
            )
            return

        return response.json()
    except Exception as e:
        logging.error(f"Unexpected error: {e}")
        return


# Write a function that converts a3 true and false ("true", "false") to python boolean
def _bool(value: Optional[object], default: bool = False) -> bool:
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    raw = str(value).strip().lower()
    if raw in {"true", "t", "1", "yes", "y"}:
        return True
    if raw in {"false", "f", "0", "no", "n"}:
        return False
    return default


def main(company_cif: str ) -> None:
    
    return None
    # First 

if  __name__ == "__main__":

    # Import from parent folder
    # import sys
    # import os
    # sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    # import core.production_models as prod_models

    company_cif = "B56222938"

    result = get_company_concepts(company_cif)
    print("AGREEMENTS RESULT:", result)
    # Write results in danik_convenios.json
    with open("danik_convenios.json", "w") as f:
        json.dump(result, f, indent=4)


    agreement_code = "07000835011982"

    # Print the output of mappings.get_concept_mapping()
    concept_mapping = mappings.get_concept_mapping(352)
    print("CONCEPT MAPPING:", concept_mapping)



    # Get company from prod by CIF
    # company = prod_models.get_production_company_by_cif(prod_models.create_production_session(), company_cif)

    # Get com
    

    # Insert a company in the database in the client table with cif, name, 
    # company_code = get_company_id("B56222938")
    # employee_data = get_employee_by_dni(company_code, "Z3692032P")
    # employee_code = employee_data["employeeCode"]
    # first_payslip = get_employee_payrolls(employee_code, company_code)
    # first_payslip_id = first_payslip[0]["payId"]
    # payslip_data = get_payslip_data(first_payslip_id, employee_code, company_code)
    # extracted_data = extract_payslip_data(first_payslip[0], payslip_data)

    # match = get_payslip_employee("B56222938", "Z3692032P", "2025-10")
    
    # print(match)  
