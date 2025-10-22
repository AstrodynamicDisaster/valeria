import requests
from typing import Optional
import logging
import json
import config as Config
from datetime import datetime
# Import Payroll models from core/models but imagining we are inside the a3 folder


# SEARCH PARAMS
PAGESIZE = 25

# THIS IS THE FORMAT FOR DATES '2025-09-30T00:00:00Z'


# API URL ENDPOINTS
COMPANIES_ENDPOINT = "companies"
EMPLOYEES_ENDPOINT = "employees"
SALARY_ENDPOINT = "pactedsalary"
PAYROLLS_ENDPOINT = "pays"
PAYROLL_DATA_ENDPOINT = "paydata"

# ENDPOINT KEYS
COMPANY_CODE = "companyCode"
NIF = "identifierNumber"


def get_bearer_token() -> str:
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


def get_headers() -> dict:
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


def get_company_id(cif: str) -> str:

    headers = get_headers()

    try:
        companies_url = f"{Config.WOLTERS_API_BASE_URL}/{COMPANIES_ENDPOINT}"
        data = {
            "pageNumber": 1,
            "pageSize": PAGESIZE,
            "filter": f"contains({NIF},'{cif}')" 
        }
        response = requests.get(companies_url, headers=headers, params=data)
        if response.status_code != 200:
            logging.error(f"Error fetching companies: {response.status_code} - {response.text}")
            return
        return response.json()[0]["companyCode"]

    except Exception as e:
        logging.error(f"Unexpected error: {e}")


def get_company_employees(company_id: int, period_start: Optional[str] = None, period_end: Optional[str] = None) -> list:

    headers = get_headers()

    employee_list = []
    try:
        employees_url = f"{Config.WOLTERS_API_BASE_URL}/{COMPANIES_ENDPOINT}/{company_id}/{EMPLOYEES_ENDPOINT}"
        data = {
            "pageNumber": 1,
            "pageSize": PAGESIZE 
        }
        response = requests.get(employees_url, headers=headers, params=data)

        employee_list.append(response.json())

        # Get remaining pages from header
        metadata = json.loads(response.headers["X-Pagination"])
        total_pages = metadata["totalPages"]
        total_count = metadata["totalCount"]

        if total_pages > 1:
            for page in range(2, total_pages + 1):
                data["pageNumber"] = page
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


def get_employee_by_dni(company_id: int, dni: str) -> str:

    headers = get_headers()

    try:
        employees_url = f"{Config.WOLTERS_API_BASE_URL}/{COMPANIES_ENDPOINT}/{company_id}/{EMPLOYEES_ENDPOINT}"
        data = {
            "pageNumber": 1,
            "pageSize": PAGESIZE,
            "filter": f"{NIF} eq '{dni}'"
        }
        response = requests.get(employees_url, headers=headers, params=data)

        if response.status_code != 200:
            logging.error(f"Error fetching companies: {response.status_code} - {response.text}")
            return
        return response.json()[0]

    except Exception as e: 
        logging.error(f"Unexpected error: {e}")


def get_employee_salary(employee_id: int, company_id: int) -> str:

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


def get_employee_payrolls(employee_id: int, company_id: int, date_from: Optional[str] = None, date_to: Optional[str] = None ) -> list:

    headers = get_headers()

    payroll_list = []

    try:
        payroll_url = f"{Config.WOLTERS_API_BASE_URL}/{COMPANIES_ENDPOINT}/{company_id}/{EMPLOYEES_ENDPOINT}/{employee_id}/{PAYROLLS_ENDPOINT}"
        data = {
            "pageNumber": 1,
            "pageSize": PAGESIZE 
        }
        response = requests.get(payroll_url, headers=headers, params=data)

        payroll_list.append(response.json())

        # Get remaining pages from header
        metadata = json.loads(response.headers["X-Pagination"])
        total_pages = metadata["totalPages"]
        total_count = metadata["totalCount"]

        if total_pages > 1:
            for page in range(2, total_pages + 1):
                data["pageNumber"] = page
                response = requests.get(payroll_url, headers=headers, params=data)
                payroll_list.append(response.json())

            if len(payroll_url) != total_count:
                logging.warning(f"Expected {total_count} employees but got {len(payroll_list)}")
            
            return payroll_list

        if response.status_code != 200:
            logging.error(f"Error fetching companies: {response.status_code} - {response.text}")
            return
        return response.json()

    except Exception as e: 
        logging.error(f"Unexpected error: {e}")


def get_payslip_data(payslip_id: str, employee_id: int, company_id: int) -> str:

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


def extract_payslip_data(payslip: dict, payslip_data: dict) -> dict:
    """Extract relevant data from a payslip dictionary."""
    
    date_from = datetime.fromisoformat(payslip.get("periodStartDate"))
    date_to = datetime.fromisoformat(payslip.get("periodEndDate"))
    days = max(30, (date_to - date_from).days +1)

    payroll = {
        "periodo": {
            "desde": date_from.date().isoformat(),
            "hasta":  date_to.date().isoformat(),
            "dias": days

        },
        "devengo_total": payslip_data["totalGross"],
        "deduccion_total": payslip_data["totalDeduction"],
        "aportacion_empresa_total": payslip_data["costBusiness"]-payslip_data["totalGross"],
        "liquido_a_percibir": payslip_data["totalGross"] - payslip_data["totalDeduction"],
        "warnings": "downlodaded from a3"}

    return payroll



if  __name__ == "__main__":
    company_code = get_company_id("B56222938")
    employee_data = get_employee_by_dni(company_code, "49771496W")
    employee_code = employee_data["employeeCode"]
    first_payslip = get_employee_payrolls(employee_code, company_code)
    first_payslip_id = first_payslip[0]["payId"]
    payslip_data = get_payslip_data(first_payslip_id, employee_code, company_code)
    extracted_data = extract_payslip_data(first_payslip[0], payslip_data)
    
    #print(payslip_data)  

