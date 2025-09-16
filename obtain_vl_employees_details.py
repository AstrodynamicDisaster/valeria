
import requests
import pandas as pd
import sys
import json
from tqdm import tqdm
import time
from datetime import datetime

start_time = datetime.now()
print(f"🚀 Script started at {start_time.strftime('%Y-%m-%d %H:%M:%S')}")

# Constants for the API
API_URL = "https://api.saltra.es/api/v4/seg-social/employees-in-enterprise"
AUTH_BEARER_TOKEN = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJpc3MiOiJodHRwczovL2FwaS5zYWx0cmEuZXMvYXBpL3dlYi92My9hY2Nlc3MtdG9rZW4iLCJpYXQiOjE3MjI5MzU4NzUsImV4cCI6MTc1NDQ3MTg3NSwibmJmIjoxNzIyOTM1ODc1LCJqdGkiOiJOTzBaWkdDcWdzOGVWcVRSIiwic3ViIjoiNTg5MSIsInBydiI6IjIzYmQ1Yzg5NDlmNjAwYWRiMzllNzAxYzQwMDg3MmRiN2E1OTc2ZjciLCJ1c2VySWQiOjU4OTEsImVtYWlsIjoiY2FybG9zQGl0c3ZhbGVyaWEuY28ifQ.rYENY0uNkoN7qJgLQB1aCutxy5RayH5xInTegd92qtY"
CERT_SECRET = "567e5ff1adec76ffe7667bed51428e67eecfbc25"

def parse_date(date_str):
    try:
        return datetime.strptime(date_str, "%Y-%m-%d")
    except Exception:
        return datetime.min

def format_date_ddmmyyyy_to_yyyymmdd(date_str):
    try:
        if "-" in date_str:
            # Caso: formato "dd-mm-yyyy"
            return datetime.strptime(date_str, "%d-%m-%Y").strftime("%Y-%m-%d")
        elif "/" in date_str:
            # Caso: formato "dd/mm/yyyy"
            return datetime.strptime(date_str, "%d/%m/%Y").strftime("%Y-%m-%d")
        else:
            return "Error"
    except Exception:
        return "Error"

# Function to retrieve employees from the API
def get_employees(ccc):
    headers = {
        "Authorization": f"Bearer {AUTH_BEARER_TOKEN}",
        "X-Cert-Secret": CERT_SECRET,
        "Content-Type": "application/json"
    }
    payload = {
        "regimen": "0111",
        "ccc": ccc,
        "options": 1
    }

    response = requests.get(API_URL, headers=headers, json=payload)

    if response.status_code == 200:
        data = response.json()
        if data.get("success") and "employees" in data.get("data", {}):
            return data["data"]["employees"]
        else:
            raise ValueError(f"API Error: {data.get('message')}")
    else:
        raise ValueError(f"HTTP Error {response.status_code}: {response.text}")


def get_more_details(ccc, dni):
    url = "https://api.saltra.es/api/v4/seg-social/employee-situations"
    headers = {
        "Authorization": f"Bearer {AUTH_BEARER_TOKEN}",
        "X-Cert-Secret": CERT_SECRET,
        "Content-Type": "application/json"
    }
    payload = {
        "regimen": "0111",
        "ccc": ccc,
        "dni": dni
    }

    try:
        response = requests.get(url, headers=headers, json=payload)
        if response.status_code == 200:
            data = response.json()
            if data.get("success") and isinstance(data.get("data"), list):
                main_detail = None
                movimientos_previos = []
                for item in data["data"]:
                    # Se considera el registro principal cuando 'situacion' no esté vacío
                    if item.get("situacion"):
                        # Si el registro tiene "fecha_baja", se considerará para elegir el más reciente
                        new_fecha_baja = item.get("fecha_baja")
                        if new_fecha_baja:
                            if main_detail is None:
                                main_detail = item
                            else:
                                current_fecha_baja = main_detail.get("fecha_baja", "1900-01-01")
                                if parse_date(new_fecha_baja) > parse_date(current_fecha_baja):
                                    main_detail = item
                        else:
                            # Si no hay fecha_baja, se puede omitir o tratar según necesidad
                            if main_detail is None:
                                main_detail = item
                    else:
                        movimientos_previos.append({
                            "movimiento": item.get("situacion_text", "Error"),
                            "fecha_alta": item.get("fecha_alta", "Error"),
                            "fecha_baja": item.get("fecha_baja", "Error"),
                            "tipo_contrato": item.get("tipo_contrato", "Error"),
                            "coef": item.get("coef", "Error"),
                        })
                if not main_detail:
                    print(f"No se encontró registro principal para DNI: {dni}")
                    main_detail = {
                        "fnacimiento": "Error",
                        "sexo": "Error",
                        "tipo_contrato": "Error",
                        "coef": "Error",
                        "grupo_cotizacion": "Error",
                        "fecha_alta": "Error",
                        "situacion": "Error"
                    }
                else:
                    main_detail["movimientos_previos"] = movimientos_previos
                return main_detail
            else:
                print(f"API no retornó datos para DNI: {dni} -> {data.get('message')}")
                return {"fnacimiento": "Error", "sexo": "Error", "tipo_contrato": "Error", "coef": "Error", "movimientos_previos": []}
        else:
            print(f"HTTP Error {response.status_code} para DNI: {dni} -> {response.text}")
            return {"fnacimiento": "Error", "sexo": "Error", "tipo_contrato": "Error", "coef": "Error", "movimientos_previos": []}
    except Exception as e:
        print(f"Excepción al obtener detalles para DNI: {dni} -> {e}")
        return {"fnacimiento": "Error", "sexo": "Error", "tipo_contrato": "Error", "coef": "Error", "movimientos_previos": []}

def get_contract_details(dni, start_date):
    url = "https://api.saltra.es/api/v4/sepe/contrata/data"
    headers = {
        "Authorization": f"Bearer {AUTH_BEARER_TOKEN}",
        "X-Cert-Secret": "8142cf5927331ef0e16681e87d44bc5f2673f91a",
        "Content-Type": "application/json"
    }
    payload = {
        "dni": dni,
        "startDate": start_date
    }

    try:
        response = requests.get(url, headers=headers, json=payload)
        if response.status_code == 200:
            data = response.json()
            if data.get("success") and "employee_data" in data.get("data", {}):
                employee_data = data["data"]["employee_data"]
                return {
                    "nivel_formativo": employee_data.get("nivel_formativo", "Error"),
                    "nacionalidad": employee_data.get("nacionalidad", "Error"),
                    "municipio_de_domicilio": employee_data.get("municipio_de_domicilio", "Error"),
                    "cno": data.get("data", {}).get("contract_data", {}).get("cno", "Error"),
                    "fin_contrato": data.get("data", {}).get("contract_data", {}).get("fecha_fin_del_contrato", "-")
                }
            else:
                print(f"[Contract API] No data found for DNI: {dni} -> {data.get('message')}")
                return {"nivel_formativo": "Error", "nacionalidad": "Error", "municipio_de_domicilio": "Error"}
        else:
            print(f"[Contract API] HTTP Error {response.status_code} for DNI: {dni} -> {response.text}")
            return {"nivel_formativo": "Error", "nacionalidad": "Error", "municipio_de_domicilio": "Error"}
    except Exception as e:
        print(f"[Contract API] Exception for DNI: {dni} -> {e}")
        return {"nivel_formativo": "Error", "nacionalidad": "Error", "municipio_de_domicilio": "Error"}

# Main script execution
if __name__ == "__main__":
    start_time = datetime.now()
    print(f"🚀 Script started at {start_time.strftime('%Y-%m-%d %H:%M:%S')}")

    try:
        employees_df = pd.read_csv("vl_ccc.csv", dtype={"ccc": str, "ipf": str})
        #employees_df = pd.read_csv("vl_ccc.csv", dtype={"ccc": str, "ipf": str}).head(2)
        processed_data = []
        progress_bar = tqdm(employees_df.iterrows(), desc="Procesando empleados", total=len(employees_df), unit="empleado")

        for index, row in progress_bar:
            ipf = row["ipf"]
            ccc = row["ccc"]

            more_details = get_more_details(ccc, ipf)
            fecha_alta = more_details.get("fecha_alta", "Error")

            contract_details = get_contract_details(ipf, fecha_alta)

            processed_data.append({
                "Name": more_details.get("nombres", "Error"),
                "Last Name": more_details.get("apellidos", "Error"),
                "ipf": ipf,
                "nss": more_details.get("nss", "Error"),
                "begin_date": fecha_alta,
                "fnacimiento": more_details.get("fnacimiento", "Error"),
                "sexo": more_details.get("sexo", "Error"),
                "tipo_contrato": more_details.get("tipo_contrato", "Error"),
                "coef": more_details.get("coef", "Error"),
                "grupo_cotizacion": more_details.get("grupo_cotizacion", "Error"),

                "nivel_formativo": contract_details.get("nivel_formativo", "Error"),
                "nacionalidad": contract_details.get("nacionalidad", "Error"),
                "municipio_de_domicilio": contract_details.get("municipio_de_domicilio", "Error"),
                "cno": contract_details.get("cno", "Error"),
                "end_date": more_details.get("fecha_baja", "Error"),
                "movimientos_previos": more_details.get("movimientos_previos", []),
                "situacion_baja": more_details.get("situacion", "Error"),
            })

        total_time = progress_bar.format_dict['elapsed']
        avg_time = total_time / progress_bar.format_dict['n'] if progress_bar.format_dict['n'] > 0 else 0

        print(f"\n✅ Finished processing {len(employees_df)} employees.")
        print(f"⏱️ Total time: {total_time:.2f} seconds")
        print(f"⚙️ Average time per employee: {avg_time:.2f} seconds")

        df = pd.DataFrame(processed_data)
        csv_filename = "employees_vl_ccc.csv"
        df.to_csv(csv_filename, index=False)
        print(f"📁 CSV file '{csv_filename}' created successfully.")

        end_time = datetime.now()
        print(f"✅ Script finished at {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"🕒 Total runtime: {str(end_time - start_time)}")

    except Exception as e:
        print(f"❌ Error en el proceso: {e}")