import re
import json
import sys
import csv


def parse_vida_laboral(filepath):
    employees = []
    current_employee = None
    total_trabajadores_alta_reportado = None

    with open(filepath, 'r', encoding='latin1') as f:
        for line in f:
            line = line.rstrip("\n")

            # Buscar línea que reporte "TOTAL TRABAJADORES EN ALTA"
            match_total = re.search(r'TOTAL TRABAJADORES EN ALTA\s+(\d+)', line)
            if match_total:
                total_trabajadores_alta_reportado = int(match_total.group(1))

            # Detectar cabecera de empleado:
            # Se espera que la línea comience (opcionalmente con espacios) con 2 dígitos, un número de 10 dígitos, otro número y más texto.
            if re.match(r'^\s*\d{2}\s+\d{10}\s+\d+\s+', line):
                tokens = line.split()
                if len(tokens) >= 5:
                    doc = tokens[3]
                    # Si el último token tiene exactamente 3 caracteres, se asume que no forma parte del nombre.
                    if len(tokens[-1]) == 3:
                        name_tokens = tokens[4:-1]
                    else:
                        name_tokens = tokens[4:]
                    nombre = " ".join(name_tokens)
                    current_employee = {'documento': doc, 'nombre': nombre, 'movimientos': []}
                    employees.append(current_employee)
                # No se procesan logs individuales.

            # Detectar línea de movimiento: aquellas que empiezan (ignorando espacios) con ALTA, BAJA o VAC.RETRIB.NO
            elif current_employee is not None and re.match(r'^\s*(ALTA|BAJA|VAC\.?RETRIB\.?NO)', line, re.IGNORECASE):
                movement_type_match = re.match(r'^\s*(\S+)', line)
                movement_type = movement_type_match.group(1).upper() if movement_type_match else None
                dates = re.findall(r'\d{2}-\d{2}-\d{4}', line)
                if len(dates) == 2:
                    if movement_type == "VAC.RETRIB.NO":
                        f_real_alta = None
                        f_efecto_alta = dates[0]
                        f_real_sit = dates[1]
                    else:
                        f_real_alta = dates[0]
                        f_efecto_alta = dates[1]
                        f_real_sit = None
                elif len(dates) >= 4:
                    f_real_alta = dates[0]
                    f_efecto_alta = dates[1]
                    f_real_sit = dates[2]
                else:
                    f_real_alta = f_efecto_alta = f_real_sit = None

                # Extraer TC (codigo_contrato) - buscar un número de 3 dígitos después de las fechas
                codigo_contrato = None
                tc_match = re.search(r'\b(\d{3})\b', line)
                if tc_match:
                    codigo_contrato = tc_match.group(1)

                movement = {
                    'situacion': movement_type,
                    'f_real_alta': f_real_alta,
                    'f_efecto_alta': f_efecto_alta,
                    'f_real_sit': f_real_sit,
                    'codigo_contrato': codigo_contrato
                }
                current_employee['movimientos'].append(movement)
            # Las líneas que no coinciden se ignoran.

    # Aplanar la estructura: cada movimiento se asocia a los datos del empleado
    movimientos = []
    for emp in employees:
        for mov in emp['movimientos']:
            record = {
                'documento': emp['documento'],
                'nombre': emp['nombre'],
                'situacion': mov['situacion'],
                'f_real_alta': mov['f_real_alta'],
                'f_efecto_alta': mov['f_efecto_alta'],
                'f_real_sit': mov['f_real_sit'],
                'codigo_contrato': mov['codigo_contrato']
            }
            movimientos.append(record)

    return movimientos, total_trabajadores_alta_reportado, employees


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python3 script.py <archivo.msj>")
        sys.exit(1)
    filepath = sys.argv[1]

    movimientos, total_reportado, employees = parse_vida_laboral(filepath)

    # Generar archivo CSV
    output_csv = "output.csv"
    fieldnames = ["documento", "nombre", "situacion", "f_real_alta", "f_efecto_alta", "f_real_sit", "codigo_contrato"]
    with open(output_csv, "w", newline='', encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for row in movimientos:
            writer.writerow(row)

    # Final check: cada DNI único cuenta como un trabajador en alta
    unique_trabajadores = len({emp['documento'] for emp in employees})
    print(f"\nTrabajadores en alta extraídos (únicos por DNI): {unique_trabajadores}")
    if total_reportado is not None:
        print(f"Total TRABAJADORES EN ALTA reportado: {total_reportado}")
        if unique_trabajadores == total_reportado:
            print("El total coincide con la extracción.")
        else:
            print("¡Atención! El total extraído no coincide con el reportado.")
    else:
        print("No se encontró la línea 'TOTAL TRABAJADORES EN ALTA' en el archivo.")

    print(f"\nDatos exportados en {output_csv}")