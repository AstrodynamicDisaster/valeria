import requests
import base64
from datetime import datetime, timedelta
import os
import csv
import re

import pdfplumber
import pandas as pd
from tqdm import tqdm

# ==============================
# CONFIG
# ==============================
API_URL = "https://api.saltra.es/api/v4/seg-social/life-ccc"
AUTH_BEARER_TOKEN = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJpc3MiOiJodHRwczovL2FwaS5zYWx0cmEuZXMvYXBpL3dlYi92My9hY2Nlc3MtdG9rZW4iLCJpYXQiOjE3NTQ1MDM5ODksImV4cCI6MTc4NjAzOTk4OSwibmJmIjoxNzU0NTAzOTg5LCJqdGkiOiJzTmU4THRKTXJoM2NEZDhUIiwic3ViIjoiNTg5MSIsInBydiI6IjIzYmQ1Yzg5NDlmNjAwYWRiMzllNzAxYzQwMDg3MmRiN2E1OTc2ZjciLCJ1c2VySWQiOjU4OTEsImVtYWlsIjoiY2FybG9zQGl0c3ZhbGVyaWEuY28ifQ.5k4roH90yJmcE6cCgc-MPNFgSBksm5vD58RzlgNq1uY"
CERT_SECRET = "567e5ff1adec76ffe7667bed51428e67eecfbc25"

# ==============================
# ITA/RLCE CONFIG
# ==============================
API_URL_ITA = "https://api.saltra.es/api/v4/seg-social/informe-ita"

# Patrón para detectar líneas de trabajadores en el ITA
LINE_REGEX = re.compile(
    r'^(?P<name>.+?)\s(?P<naf1>\d{2})\s(?P<naf2>\d{10})\s(?P<ipf>\d[0-9A-Z]{9,10})\s(?P<rest>.*)$'
)

# ==============================
# FECHAS AUTOMÁTICAS
# ==============================
def get_month_range():
    today = datetime.today()

    start_date = today.replace(day=1).strftime("%Y-%m-%d")
    end_date = today.strftime("%Y-%m-%d")

    return start_date, end_date

class RangeTooLargeError(Exception):
    """Se lanza cuando TGSS devuelve un error de límite de transmisión por rango de fechas demasiado grande."""
    pass

# ==============================
# LLAMADA AL ENDPOINT DE VIDA LABORAL (UNA SOLA PETICIÓN)
# ==============================
def call_life_ccc_api(ccc, start_date, end_date):
    headers = {
        "Authorization": f"Bearer {AUTH_BEARER_TOKEN}",
        "X-Cert-Secret": CERT_SECRET,
        "Content-Type": "application/json"
    }

    payload = {
        "regimen": "0111",
        "ccc": ccc,
        "startDate": start_date,
        "endDate": end_date
    }

    print(f"📡 Llamando a la API de vida laboral para el CCC {ccc} desde {start_date} hasta {end_date}...")

    response = requests.get(API_URL, headers=headers, json=payload)

    # Manejo específico del error de límite de transmisión
    if response.status_code == 500:
        try:
            data = response.json()
            msg = data.get("message", "") or ""
        except ValueError:
            msg = response.text or ""

        if "excede el límite de transmisión permitido" in msg or "excede el l\u00edmite de transmisi\u00f3n permitido" in msg:
            raise RangeTooLargeError(msg)

        # Si es un 500 pero no por el límite de transmisión, lanzamos error genérico
        raise Exception(f"❌ Error HTTP 500: {response.text}")

    if response.status_code != 200:
        raise Exception(f"❌ Error HTTP {response.status_code}: {response.text}")

    data = response.json()

    if not data.get("success"):
        raise Exception(f"❌ Error API: {data.get('message')}")

    file_info = data["data"]["file"]
    b64_content = file_info.get("content")

    if not b64_content:
        raise Exception("❌ La API no devolvió contenido base64 del PDF.")

    return b64_content


# ==============================
# LLAMADAS RECURSIVAS DIVIDIENDO EL RANGO SI ES DEMASIADO GRANDE
# ==============================
def get_life_labour_pdfs_for_range(ccc, start_date, end_date):
    """
    Devuelve una lista de tuplas (base64_pdf, start_date, end_date) cubriendo todo el rango.
    Si TGSS devuelve que el rango es demasiado grande, se divide en dos subrangos y se reintenta.
    """
    try:
        b64_content = call_life_ccc_api(ccc, start_date, end_date)
        return [(b64_content, start_date, end_date)]
    except RangeTooLargeError as e:
        # Convertir strings de fecha a objetos date
        start = datetime.strptime(start_date, "%Y-%m-%d").date()
        end = datetime.strptime(end_date, "%Y-%m-%d").date()

        if start >= end:
            # Ya estamos en un rango de 1 día y sigue fallando por tamaño
            raise Exception(
                f"❌ El rango {start_date} a {end_date} es de un solo día pero sigue excediendo el límite de transmisión: {e}"
            )

        delta_days = (end - start).days
        mid = start + timedelta(days=delta_days // 2)

        first_start = start
        first_end = mid
        second_start = mid + timedelta(days=1)
        second_end = end

        print(
            f"⚠️ Rango demasiado grande ({start_date} a {end_date}), dividiendo en "
            f"{first_start} a {first_end} y {second_start} a {second_end}"
        )

        results = []
        results.extend(
            get_life_labour_pdfs_for_range(
                ccc,
                first_start.strftime("%Y-%m-%d"),
                first_end.strftime("%Y-%m-%d"),
            )
        )
        results.extend(
            get_life_labour_pdfs_for_range(
                ccc,
                second_start.strftime("%Y-%m-%d"),
                second_end.strftime("%Y-%m-%d"),
            )
        )
        return results

# ==============================
# GUARDAR PDF A PARTIR DE BASE64
# ==============================
def save_pdf_from_base64(base64_data, filename):
    pdf_bytes = base64.b64decode(base64_data)

    with open(filename, "wb") as f:
        f.write(pdf_bytes)

    print(f"📁 PDF guardado correctamente: {filename}")

# ==============================
# DESCARGAR ITA Y EXTRAER RLCE
# ==============================
def download_ita_pdf_for_ccc(ccc: str, output_pdf_path: str) -> str:
    """
    Descarga el informe ITA para un CCC concreto desde la API de Saltra y lo guarda como PDF.
    Devuelve la ruta al fichero PDF guardado.
    """
    headers = {
        "Authorization": f"Bearer {AUTH_BEARER_TOKEN}",
        "X-Cert-Secret": CERT_SECRET,
        "Content-Type": "application/json",
    }
    payload = {
        "regimen": "0111",
        "ccc": ccc,
    }

    print(f"[INFO] Solicitando ITA para CCC {ccc}...")

    # La documentación indica GET; usamos requests.get con body JSON.
    response = requests.get(API_URL_ITA, headers=headers, json=payload)

    if response.status_code != 200:
        raise RuntimeError(f"Error HTTP {response.status_code} al solicitar ITA: {response.text}")

    data = response.json()
    if not data.get("success"):
        raise RuntimeError(f"Error API ITA: {data.get('message')}")

    file_info = data.get("data", {}).get("file", {})
    b64_content = file_info.get("content")
    if not b64_content:
        raise RuntimeError("La API ITA no devolvió contenido de fichero en base64.")

    pdf_bytes = base64.b64decode(b64_content)

    with open(output_pdf_path, "wb") as f:
        f.write(pdf_bytes)

    print(f"[OK] ITA descargado y guardado en: {output_pdf_path}")
    return output_pdf_path


def extract_rlce_map_from_pdf(pdf_path: str) -> dict:
    """
    Extrae un diccionario {dni: rlce} a partir de un PDF ITA.
    El patrón sigue la misma lógica que en el script extraer_dni_rlce.py.
    """
    rlce_map = {}

    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text = page.extract_text() or ""
            for line in text.splitlines():
                m = LINE_REGEX.match(line)
                if not m:
                    continue

                ipf = m.group("ipf")
                rest = m.group("rest")

                # IPF tiene un dígito delante → nos quedamos con los últimos 10 caracteres como DNI.
                dni = ipf[-10:]

                tokens = rest.split()
                if len(tokens) < 8:
                    continue

                # RLCE es el 8º token en este formato concreto del ITA.
                rlce = tokens[7]

                rlce_map[dni] = rlce

    print(f"[OK] RLCE extraído para {len(rlce_map)} trabajadores desde ITA.")
    return rlce_map

# ==============================
# UTILIDADES PARA PARSEAR FECHAS
# ==============================
def parse_ddmmyyyy(date_str):
    """
    Convierte 'dd-mm-aaaa' en datetime.date.
    Si viene vacío o mal formado, devuelve None.
    """
    if not date_str:
        return None
    try:
        return datetime.strptime(date_str, "%d-%m-%Y").date()
    except ValueError:
        return None


# ==============================
# EXTRACCIÓN DE DATOS DESDE LOS PDFs DE VIDA LABORAL
# ==============================
def extract_data_from_pdf(file_path, ccc, employees):
    """
    Lee un PDF de vida laboral y actualiza el diccionario 'employees' con:
    - NAF
    - DNI/NIE
    - fechas de ALTA
    - fechas de BAJA
    - periodos VAC.RETRIB.NO
    """
    with pdfplumber.open(file_path) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if not text:
                continue

            lines = text.split("\n")

            header_found = False
            current_naf = None
            current_doc = None

            for line in lines:
                line = line.strip()
                if not line:
                    continue

                # Detectar la cabecera de la tabla de datos laborales
                if ("NÚMERO DE AFILIACION" in line and "DOCUMENTO IDENTIFICATIVO" in line) or \
                   ("NUMERO DE AFILIACION" in line and "DOCUMENTO IDENTIFICATIVO" in line):
                    header_found = True
                    continue

                if not header_found:
                    continue

                tokens = line.split()

                # Línea tipo "08 1195043403 1 030313369J NOMBRE APELLIDOS ..."
                # Es decir, encabezado de trabajador con NAF y DNI/NIE.
                if (
                    len(tokens) >= 4
                    and tokens[0].isdigit()
                    and tokens[1].isdigit()
                    and tokens[2].isdigit()
                ):
                    naf = "".join(tokens[:3])  # p.ej. "08" + "1195043403" + "1"
                    doc = tokens[3]

                    current_naf = naf
                    current_doc = doc

                    if naf not in employees:
                        employees[naf] = {
                            "ccc": ccc,
                            "dni": doc,
                            "naf": naf,
                            "alta_dates": [],
                            "baja_dates": [],
                            "vac_periods": [],
                        }
                    else:
                        # Actualizar DNI si no lo teníamos
                        if not employees[naf].get("dni"):
                            employees[naf]["dni"] = doc

                    continue

                if not tokens:
                    continue

                # Línea de situación: ALTA / BAJA / VAC.RETRIB.NO
                situacion = tokens[0]

                if situacion not in ("ALTA", "BAJA", "VAC.RETRIB.NO"):
                    continue

                if not current_naf:
                    # No tenemos NAF asociado aún, no podemos asignar esta situación
                    continue

                emp = employees.setdefault(
                    current_naf,
                    {
                        "ccc": ccc,
                        "dni": current_doc,
                        "naf": current_naf,
                        "alta_dates": [],
                        "baja_dates": [],
                        "vac_periods": [],
                    },
                )

                # SITUACIÓN = ALTA
                if situacion == "ALTA":
                    # Esperamos algo como: "ALTA 19-06-2025 19-06-2025 ..."
                    if len(tokens) >= 2:
                        real_alta = tokens[1]  # dd-mm-aaaa
                        emp["alta_dates"].append(real_alta)

                # SITUACIÓN = BAJA
                elif situacion == "BAJA":
                    # Ejemplo: "BAJA 15-09-2025 15-09-2025 05-12-2025 05-12-2025 ..."
                    # tokens[1] -> F.REAL ALTA (inicio del contrato/situación)
                    # tokens[3] -> F.REAL SIT. (fecha real de baja)
                    # Guardamos también la fecha de alta que viene en la línea de BAJA
                    if len(tokens) >= 2:
                        real_alta_desde_baja = tokens[1]
                        emp["alta_dates"].append(real_alta_desde_baja)
                    # Y la baja como ya hacíamos
                    if len(tokens) >= 4:
                        real_baja = tokens[3]
                        emp["baja_dates"].append(real_baja)

                # SITUACIÓN = VAC.RETRIB.NO
                elif situacion == "VAC.RETRIB.NO":
                    # Ejemplo: "VAC.RETRIB.NO 29-11-2025 01-12-2025 1,00 0,75 ..."
                    if len(tokens) >= 3:
                        vac_inicio = tokens[1]
                        vac_fin = tokens[2]
                        emp["vac_periods"].append((vac_inicio, vac_fin))


# ==============================
# GENERACIÓN DEL CSV FINAL
# ==============================
def generate_csv_from_employees(employees, output_csv_path):
    """
    Genera un CSV con columnas:
    CCC,DNI/NIE,NAF,fecha_real_alta,fecha_baja,VAC.RETRIB.NO_inicio,VAC.RETRIB.NO_final

    - Si un empleado tiene varias VAC.RETRIB.NO, se genera una fila por cada periodo.
    - Si no tiene VAC.RETRIB.NO, se genera una única fila con las columnas de vacaciones vacías.
    """
    fieldnames = [
        "CCC",
        "DNI/NIE",
        "NAF",
        "fecha_real_alta",
        "fecha_baja",
        "VAC.RETRIB.NO_inicio",
        "VAC.RETRIB.NO_final",
    ]

    with open(output_csv_path, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()

        for emp in employees.values():
            ccc = emp.get("ccc", "")
            dni = emp.get("dni", "")
            naf = emp.get("naf", "")

            alta_dates_parsed = [
                parse_ddmmyyyy(d) for d in emp.get("alta_dates", []) if parse_ddmmyyyy(d)
            ]
            # Si no tenemos ninguna fecha de alta válida, no incluimos este empleado en el CSV
            if not alta_dates_parsed:
                continue
            min_alta_date = min(alta_dates_parsed)
            fecha_real_alta = min_alta_date.strftime("%d-%m-%Y")

            # Calcular fecha_baja (máxima entre todas las BAJAS, si hay)
            baja_dates_parsed = [
                parse_ddmmyyyy(d) for d in emp.get("baja_dates", []) if parse_ddmmyyyy(d)
            ]
            if baja_dates_parsed:
                max_baja_date = max(baja_dates_parsed)
                fecha_baja = max_baja_date.strftime("%d-%m-%Y")
            else:
                fecha_baja = ""

            vac_periods = emp.get("vac_periods", [])

            # Si hay periodos de vacaciones retribuidas, una fila por periodo
            if vac_periods:
                for (vac_inicio, vac_fin) in vac_periods:
                    writer.writerow(
                        {
                            "CCC": ccc,
                            "DNI/NIE": dni,
                            "NAF": naf,
                            "fecha_real_alta": fecha_real_alta,
                            "fecha_baja": fecha_baja,
                            "VAC.RETRIB.NO_inicio": vac_inicio,
                            "VAC.RETRIB.NO_final": vac_fin,
                        }
                    )
            else:
                # Sin vacaciones: una única fila por empleado
                writer.writerow(
                    {
                        "CCC": ccc,
                        "DNI/NIE": dni,
                        "NAF": naf,
                        "fecha_real_alta": fecha_real_alta,
                        "fecha_baja": fecha_baja,
                        "VAC.RETRIB.NO_inicio": "",
                        "VAC.RETRIB.NO_final": "",
                    }
                )

# ==============================
# UTILIDADES ADICIONALES PARA FORMATO DE FECHAS (YYYY-MM-DD)
# ==============================
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

# ==============================
# CÁLCULO DE DÍAS DE VACACIONES A PARTIR DE FECHAS (dd-mm-yyyy)
# ==============================
def compute_vacation_days(vac_inicio, vac_fin):
    """
    Devuelve el número de días de vacaciones (inclusive) entre vac_inicio y vac_fin
    en formato 'dd-mm-yyyy'. Si alguna fecha está vacía o es inválida, devuelve "".
    Si vac_inicio == vac_fin, devuelve 1.
    """
    if not vac_inicio or not vac_fin:
        return ""
    start_date = parse_ddmmyyyy(vac_inicio)
    end_date = parse_ddmmyyyy(vac_fin)
    if not start_date or not end_date:
        return ""
    # Diferencia inclusiva: si son el mismo día => 1
    return (end_date - start_date).days + 1


# ==============================
# LLAMADA ADHOC: employee-situations (get_more_details)
# ==============================
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
                active_detail = None
                movimientos_previos = []
                latest_item = None

                for item in data["data"]:
                    if not item.get("fecha_baja"):
                        active_detail = {
                            "fnacimiento": item.get("fnacimiento", "Error"),
                            "sexo": item.get("sexo", "Error"),
                            "tipo_contrato": item.get("tipo_contrato", "Error"),
                            "coef": item.get("coef", "Error"),
                            "grupo_cotizacion": item.get("grupo_cotizacion", "Error"),
                            "worker_collective": item.get("worker_collective", ""),
                            "nombres": item.get("nombres", "Error"),
                            "apellidos": item.get("apellidos", "Error"),
                        }
                    else:
                        movimientos_previos.append({
                            "movimiento": item.get("situacion_text", "Error"),
                            "fecha_alta": item.get("fecha_alta", "Error"),
                            "fecha_baja": item.get("fecha_baja", "Error"),
                            "tipo_contrato": item.get("tipo_contrato", "Error"),
                            "coef": item.get("coef", "Error"),
                        })
                    latest_item = item

                if not active_detail:
                    print(f"No active situation found for DNI: {dni}")
                    if latest_item is not None:
                        # Usamos la última situación (aunque esté de baja) para poblar los datos básicos
                        active_detail = {
                            "fnacimiento": latest_item.get("fnacimiento", "Error"),
                            "sexo": latest_item.get("sexo", "Error"),
                            "tipo_contrato": latest_item.get("tipo_contrato", "Error"),
                            "coef": latest_item.get("coef", "Error"),
                            "grupo_cotizacion": latest_item.get("grupo_cotizacion", "Error"),
                            "worker_collective": latest_item.get("worker_collective", ""),
                            "nombres": latest_item.get("nombres", "Error"),
                            "apellidos": latest_item.get("apellidos", "Error"),
                        }
                    else:
                        active_detail = {
                            "fnacimiento": "Error",
                            "sexo": "Error",
                            "tipo_contrato": "Error",
                            "coef": "Error",
                            "grupo_cotizacion": "Error",
                            "worker_collective": "",
                            "nombres": "Error",
                            "apellidos": "Error",
                        }

                # Sort movimientos_previos by fecha_baja descending
                try:
                    movimientos_previos = sorted(
                        movimientos_previos,
                        key=lambda x: datetime.strptime(x["fecha_baja"], "%Y-%m-%d")
                        if x["fecha_baja"] not in ("", "Error")
                        else (
                            datetime.strptime(x["fecha_alta"], "%Y-%m-%d")
                            if x["fecha_alta"] not in ("", "Error")
                            else datetime.min
                        ),
                        reverse=True,
                    )
                except Exception:
                    # Si alguna fecha está mal formada, mantenemos el orden original
                    pass

                # Filtrar movimientos al mes en curso (año/mes actuales)
                now = datetime.today()
                current_year = now.year
                current_month = now.month
                movimientos_filtrados = []
                for mov in movimientos_previos:
                    date_str = mov.get("fecha_baja") or mov.get("fecha_alta")
                    if not date_str or date_str == "Error":
                        continue
                    try:
                        d = datetime.strptime(date_str, "%Y-%m-%d")
                    except Exception:
                        continue
                    if d.year == current_year and d.month == current_month:
                        movimientos_filtrados.append(mov)

                active_detail["movimientos_previos"] = movimientos_filtrados
                return active_detail
            else:
                print(f"API returned no data for DNI: {dni} -> {data.get('message')}")
                return {
                    "fnacimiento": "Error",
                    "sexo": "Error",
                    "tipo_contrato": "Error",
                    "coef": "Error",
                    "grupo_cotizacion": "Error",
                    "worker_collective": "",
                    "nombres": "Error",
                    "apellidos": "Error",
                    "movimientos_previos": [],
                }
        else:
            print(f"HTTP Error {response.status_code} for DNI: {dni} -> {response.text}")
            return {
                "fnacimiento": "Error",
                "sexo": "Error",
                "tipo_contrato": "Error",
                "coef": "Error",
                "grupo_cotizacion": "Error",
                "worker_collective": "",
                "nombres": "Error",
                "apellidos": "Error",
                "movimientos_previos": [],
            }
    except Exception as e:
        print(f"Exception while fetching details for DNI: {dni} -> {e}")
        return {
            "fnacimiento": "Error",
            "sexo": "Error",
            "tipo_contrato": "Error",
            "coef": "Error",
            "grupo_cotizacion": "Error",
            "worker_collective": "",
            "nombres": "Error",
            "apellidos": "Error",
            "movimientos_previos": [],
        }


# ==============================
# LLAMADA ADHOC: SEPE contrata/data (get_contract_details)
# ==============================
def get_contract_details(dni, start_date):
    url = "https://api.saltra.es/api/v4/sepe/contrata/data"
    headers = {
        "Authorization": f"Bearer {AUTH_BEARER_TOKEN}",
        # En tu script original usabas otro secret para SEPE; si es distinto, cámbialo aquí.
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
                    "fin_contrato": data.get("data", {}).get("contract_data", {}).get("fecha_fin_del_contrato", "-"),
                }
            else:
                print(f"[Contract API] No data found for DNI: {dni} -> {data.get('message')}")
                return {
                    "nivel_formativo": "Error",
                    "nacionalidad": "Error",
                    "municipio_de_domicilio": "Error",
                    "cno": "Error",
                    "fin_contrato": "-",
                }
        else:
            print(f"[Contract API] HTTP Error {response.status_code} for DNI: {dni} -> {response.text}")
            return {
                "nivel_formativo": "Error",
                "nacionalidad": "Error",
                "municipio_de_domicilio": "Error",
                "cno": "Error",
                "fin_contrato": "-",
            }
    except Exception as e:
        print(f"[Contract API] Exception for DNI: {dni} -> {e}")
        return {
            "nivel_formativo": "Error",
            "nacionalidad": "Error",
            "municipio_de_domicilio": "Error",
            "cno": "Error",
            "fin_contrato": "-",
        }


# ==============================
# ENRIQUECER EMPLEADOS USANDO EL CSV DE VIDA LABORAL + APIS ADHOC
# ==============================
def enrich_employees_with_apis(csv_input_path, ccc, csv_output_path, rlce_map=None):
    """
    Lee el CSV de vida laboral (csv_input_path), lanza get_more_details y get_contract_details
    para cada empleado, y genera un CSV enriquecido en csv_output_path.
    Si se proporciona rlce_map, añade la columna RLCE.
    """
    df = pd.read_csv(csv_input_path, dtype=str).fillna("")

    processed_rows = []
    progress_bar = tqdm(df.to_dict(orient="records"), desc="Enriching employees", unit="employee")

    for row in progress_bar:
        dni = row.get("DNI/NIE", "")
        naf = row.get("NAF", "")
        fecha_real_alta = row.get("fecha_real_alta", "")
        fecha_baja = row.get("fecha_baja", "")
        vac_inicio = row.get("VAC.RETRIB.NO_inicio", "")
        vac_fin = row.get("VAC.RETRIB.NO_final", "")

        vac_dias = compute_vacation_days(vac_inicio, vac_fin)

        formatted_start_date = format_date_ddmmyyyy_to_yyyymmdd(fecha_real_alta)

        more_details = get_more_details(ccc, dni)
        contract_details = get_contract_details(dni, formatted_start_date)

        formatted_end_date = format_date_ddmmyyyy_to_yyyymmdd(contract_details.get("fin_contrato", "-"))

        rlce_value = ""
        if rlce_map:
            rlce_value = rlce_map.get(dni, "")

        processed_rows.append(
            {
                "CCC": row.get("CCC", ""),
                "DNI/NIE": dni,
                "NAF": naf,
                "nombres": more_details.get("nombres", "Error"),
                "apellidos": more_details.get("apellidos", "Error"),

                "fecha_real_alta": fecha_real_alta,
                "fecha_baja": fecha_baja,
                "fnacimiento": more_details.get("fnacimiento", "Error"),
                "sexo": more_details.get("sexo", "Error"),

                "tipo_contrato": more_details.get("tipo_contrato", "Error"),
                "coef": more_details.get("coef", "Error"),
                "grupo_cotizacion": more_details.get("grupo_cotizacion", "Error"),
                "worker_collective": more_details.get("worker_collective", ""),

                "VAC.RETRIB.NO_dias": vac_dias,
                "RLCE": rlce_value,

                "nivel_formativo": contract_details.get("nivel_formativo", "Error"),
                "nacionalidad": contract_details.get("nacionalidad", "Error"),
                "municipio_de_domicilio": contract_details.get("municipio_de_domicilio", "Error"),
                "cno": contract_details.get("cno", "Error"),
                "end_date_contrata": formatted_end_date,
                "movimientos_previos": more_details.get("movimientos_previos", []),
            }
        )

    enriched_df = pd.DataFrame(processed_rows)
    enriched_df.to_csv(csv_output_path, index=False)

# ==============================
# MAIN
# ==============================
if __name__ == "__main__":
    try:
        ccc = input("Introduce el CCC: ").strip()

        # Rango por defecto: desde el primer día del mes actual hasta hoy
        start_date, end_date = get_month_range()

        # 1) Descargar y trocear vida laboral, guardar PDFs
        pdf_chunks = get_life_labour_pdfs_for_range(ccc, start_date, end_date)

        # Diccionario acumulado de empleados a partir de TODOS los PDFs generados
        employees = {}

        for idx, (base64_pdf, chunk_start, chunk_end) in enumerate(pdf_chunks, start=1):
            output_filename = f"vida_laboral_{ccc}_{chunk_start}_a_{chunk_end}.pdf"
            save_pdf_from_base64(base64_pdf, output_filename)

            # Extraer datos de este PDF y acumularlos
            extract_data_from_pdf(output_filename, ccc, employees)

        # 2) Generar CSV base con la información de vida laboral
        csv_output_base = f"vida_laboral_resumen_{ccc}.csv"
        generate_csv_from_employees(employees, csv_output_base)

        print(
            f"✅ Proceso de vida laboral completado. Se han generado {len(pdf_chunks)} fichero(s) de PDF "
            f"y el CSV base: {csv_output_base}"
        )

        # 2b) Descargar ITA y extraer RLCE para este CCC
        rlce_map = {}
        try:
            ita_pdf_filename = f"ita_{ccc}.pdf"
            download_ita_pdf_for_ccc(ccc, ita_pdf_filename)
            rlce_map = extract_rlce_map_from_pdf(ita_pdf_filename)
        except Exception as e:
            print(f"⚠️ No se pudo obtener ITA/RLCE para el CCC {ccc}: {e}")
            rlce_map = {}

        # 3) Enriquecer con get_more_details, get_contract_details y RLCE
        csv_output_enriched = f"vida_laboral_enriched_{ccc}.csv"
        enrich_employees_with_apis(csv_output_base, ccc, csv_output_enriched, rlce_map)

        print(f"✅ Enriquecimiento completado. CSV final generado: {csv_output_enriched}")

    except Exception as e:
        print(f"❌ Error: {e}")