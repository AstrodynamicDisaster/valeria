import requests
import os
import logging
from dotenv import load_dotenv

load_dotenv()

SALTRA_API = "https://api.saltra.es/api/v4/seg-social"
SSN_ENDPOINT = "/ipf-by-nss"

base_url = "https://api.saltra.es/api/v4/seg-social"
endpoint = f"{base_url}{SSN_ENDPOINT}"

def fmt_dni(s: str) -> str:
    if not (len(s) == 10 and s.startswith("0")):
        raise ValueError("Expected a 10-digit string starting with 0")
    return s[1:]


def get_ss_employee_data(ssn: str) -> dict:
    
    headers = {
        "Authorization": f"Bearer {os.getenv('SALTRA_TOKEN')}",
        "X-Cert-Secret": f"{os.getenv('SALTRA_SECRET')}",
        "Content-Type": "application/json",
    }

    try:

        params = {"nss": ssn}  # 12-digit NSS
        resp = requests.get(endpoint, headers=headers, params=params, timeout=30)

        if resp.status_code != 200:
            logging.error(f"Error fetching companies: {resp.status_code} - {resp.text}")
            return {}
        
        data = resp.json()["data"]
        dni = fmt_dni(data["dni"])

        employee_info = {
            "name": data["nombres"],
            "surnames": data["apellidos"],
            "dni": dni
        }
        return employee_info
    
    except Exception as e: 
        logging.error(f"Unexpected error: {e}")
        return {}


if  __name__ == "__main__":

    ssn = "281622529040"

    data = get_ss_employee_data(ssn)

    [print(k, v) for k,v in data.items()]
