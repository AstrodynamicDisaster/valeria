#!/usr/bin/env python3
"""
ValerIA Test Data Generator
Generates synthetic Spanish payroll data for testing and development

Generates:
1. Vida laboral CSV files with realistic Spanish employment data
2. Spanish payslip PDFs for AI vision model testing
3. Intentional gaps in payslips for missing document detection testing
"""

import os
import csv
import random
from datetime import datetime, date, timedelta
from typing import List, Dict, Tuple
import tempfile

# Spanish Names and Data

SPANISH_FIRST_NAMES_MALE = [
    'ANTONIO', 'JOSE', 'FRANCISCO', 'DAVID', 'JUAN', 'JAVIER', 'MIGUEL', 'ANGEL',
    'CARLOS', 'ALEJANDRO', 'DANIEL', 'ADRIÁN', 'PABLO', 'ÁLVARO', 'RAÚL', 'RUBÉN',
    'SERGIO', 'FERNANDO', 'ALBERTO', 'RICARDO', 'MANUEL', 'RAFAEL', 'PEDRO', 'LUIS'
]

SPANISH_FIRST_NAMES_FEMALE = [
    'MARÍA', 'CARMEN', 'ANA', 'ISABEL', 'PILAR', 'DOLORES', 'TERESA', 'ROSA',
    'CRISTINA', 'PATRICIA', 'MARTA', 'LAURA', 'ELENA', 'SILVIA', 'RAQUEL', 'MÓNICA',
    'SARA', 'NATALIA', 'BEATRIZ', 'ROCÍO', 'ANDREA', 'SONIA', 'JULIA', 'CLARA'
]

SPANISH_SURNAMES = [
    'GARCIA', 'RODRIGUEZ', 'GONZALEZ', 'FERNANDEZ', 'LOPEZ', 'MARTINEZ', 'SANCHEZ',
    'PEREZ', 'MARTIN', 'GOMEZ', 'RUIZ', 'HERNANDEZ', 'JIMENEZ', 'DIAZ', 'MORENO',
    'MUÑOZ', 'ALVAREZ', 'ROMERO', 'GUTIERREZ', 'NAVARRO', 'TORRES', 'DOMINGUEZ',
    'VAZQUEZ', 'RAMOS', 'GIL', 'RAMIREZ', 'SERRANO', 'BLANCO', 'SUAREZ', 'MOLINA',
    'MORALES', 'ORTEGA', 'DELGADO', 'CASTRO', 'ORTIZ', 'RUBIO', 'MARIN', 'SANZ',
    'IGLESIAS', 'NUÑEZ', 'MEDINA', 'GARRIDO', 'CORTES', 'CASTILLO', 'SANTOS',
    'LOZANO', 'GUERRERO', 'CANO', 'PRIETO', 'MENDEZ', 'CRUZ', 'FLORES', 'HERRERA',
    'PEÑA', 'LEON', 'MARQUEZ', 'CABRERA', 'GALLEGO', 'CALVO', 'VIDAL', 'CAMPOS'
]

SPANISH_COMPANIES = [
    'Construcciones García S.L.',
    'Tecnología Innovadora S.A.',
    'Servicios Integrales Madrid S.L.',
    'Consultoría Empresarial Barcelona S.A.',
    'Distribuciones Valencia S.L.',
    'Manufacturas Españolas S.A.',
    'Logística y Transporte Ibérico S.L.',
    'Energías Renovables del Sur S.A.'
]


class SpanishDataGenerator:
    """Generate realistic Spanish business and personal data"""

    def __init__(self):
        self.used_nifs = set()
        self.used_cccs = set()

    def generate_spanish_name(self) -> Tuple[str, str]:
        """Generate a realistic Spanish full name"""
        gender = random.choice(['male', 'female'])

        if gender == 'male':
            first_name = random.choice(SPANISH_FIRST_NAMES_MALE)
        else:
            first_name = random.choice(SPANISH_FIRST_NAMES_FEMALE)

        # Spanish naming convention: First surname + Second surname
        surname1 = random.choice(SPANISH_SURNAMES)
        surname2 = random.choice(SPANISH_SURNAMES)

        # Format: SURNAME1 SURNAME2 --- FIRST_NAME (as appears in vida laboral)
        vida_laboral_format = f"{surname1} {surname2} --- {first_name}"
        normal_format = f"{first_name} {surname1} {surname2}"

        return vida_laboral_format, normal_format

    def generate_spanish_nif(self) -> str:
        """Generate a valid Spanish NIF/DNI with check digit"""
        while True:
            # Generate 8-digit number
            number = random.randint(10000000, 99999999)

            # Calculate check letter
            letters = "TRWAGMYFPDXBNJZSQVHLCKE"
            check_letter = letters[number % 23]

            nif = f"{number:08d}{check_letter}"

            if nif not in self.used_nifs:
                self.used_nifs.add(nif)
                return nif

    def generate_nie(self) -> str:
        """Generate a Spanish NIE (Número de Identidad de Extranjero)"""
        while True:
            # NIE format: Letter + 7 digits + check letter
            prefix = random.choice(['X', 'Y', 'Z'])
            number = random.randint(1000000, 9999999)

            # Convert prefix to number for calculation
            prefix_num = {'X': 0, 'Y': 1, 'Z': 2}[prefix]
            full_number = prefix_num * 10000000 + number

            letters = "TRWAGMYFPDXBNJZSQVHLCKE"
            check_letter = letters[full_number % 23]

            nie = f"{prefix}{number:07d}{check_letter}"

            if nie not in self.used_nifs:
                self.used_nifs.add(nie)
                return nie

    def generate_spanish_cif(self) -> str:
        """Generate a valid Spanish CIF (Código de Identificación Fiscal) for companies"""
        # CIF format: XNNNNNNNC where:
        # X = Organization type letter (A,B,C,D,E,F,G,H,J,N,P,Q,R,S,U,V,W)
        # NNNNNNN = 7-digit number
        # C = Control character

        org_types = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'J', 'N', 'P', 'Q', 'R', 'S', 'U', 'V', 'W']
        org_type = random.choice(org_types)

        # Generate 7-digit number
        number = random.randint(1000000, 9999999)

        # Calculate control character
        number_str = str(number)
        sum_even = sum(int(number_str[i]) for i in range(1, 7, 2))
        sum_odd = sum(int(d) for digit in number_str[::2] for d in str(int(digit) * 2))
        total = sum_even + sum_odd
        control_digit = (10 - (total % 10)) % 10

        # Some CIF types use letters, others numbers for control
        if org_type in ['A', 'B', 'E', 'H']:
            control_char = str(control_digit)
        else:
            control_chars = 'JABCDEFGHI'
            control_char = control_chars[control_digit]

        return f"{org_type}{number:07d}{control_char}"

    def generate_documento(self) -> str:
        """Generate either NIF or NIE (80% NIF, 20% NIE for realism)"""
        if random.random() < 0.8:
            return self.generate_spanish_nif()
        else:
            return self.generate_nie()

    def generate_ccc_code(self) -> str:
        """Generate a Spanish Social Security CCC code"""
        while True:
            # CCC format: 2 digits (province) + 10 digits + 2 check digits
            province = random.randint(1, 52)  # Spanish provinces
            account = random.randint(1000000000, 9999999999)

            # Simplified check digit calculation (not real algorithm)
            check = random.randint(10, 99)

            ccc = f"{province:02d}{account:010d}{check:02d}"

            if ccc not in self.used_cccs:
                self.used_cccs.add(ccc)
                return ccc

    def generate_nss(self) -> str:
        """Generate Spanish Social Security Number"""
        # NSS format: 2 digits (province) + 8 digits + 2 digits
        province = random.randint(1, 52)
        number = random.randint(10000000, 99999999)
        suffix = random.randint(10, 99)

        return f"{province:02d}{number:08d}{suffix:02d}"


class VidaLaboralGenerator:
    """Generate vida laboral CSV files"""

    def __init__(self, data_generator: SpanishDataGenerator):
        self.data_gen = data_generator

    def generate_employee_data(self, num_employees: int = 5) -> List[Dict]:
        """Generate basic employee data"""
        employees = []

        for _ in range(num_employees):
            vida_name, normal_name = self.data_gen.generate_spanish_name()
            documento = self.data_gen.generate_documento()

            employee = {
                'documento': documento,
                'nombre': vida_name,
                'normal_name': normal_name,
                'nss': self.data_gen.generate_nss(),
                'birth_date': self.generate_birth_date()
            }
            employees.append(employee)

        return employees

    def generate_birth_date(self) -> date:
        """Generate realistic birth date (ages 22-65)"""
        today = date.today()
        min_age = 22
        max_age = 65

        birth_year = today.year - random.randint(min_age, max_age)
        birth_month = random.randint(1, 12)
        birth_day = random.randint(1, 28)  # Avoid month-end issues

        return date(birth_year, birth_month, birth_day)

    def generate_employment_events(self, employees: List[Dict], year: int = 2025) -> List[Dict]:
        """Generate ALTA/BAJA employment events for employees"""
        events = []

        for employee in employees:
            # Determine employment scenario
            scenario = random.choices([
                'full_year',      # Employed all year
                'hired_mid_year', # Hired during the year
                'left_mid_year',  # Left during the year
                'hired_and_left', # Hired and left same year
                'vacation_after_baja'  # Had unpaid vacation after leaving
            ], weights=[60, 15, 15, 5, 5])[0]

            if scenario == 'full_year':
                # ALTA at beginning of year (or previous year)
                alta_date = date(year - 1, 1, 1)
                events.append({
                    'documento': employee['documento'],
                    'nombre': employee['nombre'],
                    'situacion': 'ALTA',
                    'f_real_alta': alta_date.strftime('%d-%m-%Y'),
                    'f_efecto_alta': alta_date.strftime('%d-%m-%Y'),
                    'f_real_sit': alta_date.strftime('%d-%m-%Y')
                })

            elif scenario == 'hired_mid_year':
                # ALTA during the year
                alta_date = date(year, random.randint(1, 10), random.randint(1, 28))
                events.append({
                    'documento': employee['documento'],
                    'nombre': employee['nombre'],
                    'situacion': 'ALTA',
                    'f_real_alta': alta_date.strftime('%d-%m-%Y'),
                    'f_efecto_alta': alta_date.strftime('%d-%m-%Y'),
                    'f_real_sit': alta_date.strftime('%d-%m-%Y')
                })

            elif scenario == 'left_mid_year':
                # ALTA in previous year, BAJA during current year
                alta_date = date(year - 1, random.randint(1, 12), random.randint(1, 28))
                baja_date = date(year, random.randint(3, 12), random.randint(1, 28))

                events.extend([
                    {
                        'documento': employee['documento'],
                        'nombre': employee['nombre'],
                        'situacion': 'ALTA',
                        'f_real_alta': alta_date.strftime('%d-%m-%Y'),
                        'f_efecto_alta': alta_date.strftime('%d-%m-%Y'),
                        'f_real_sit': alta_date.strftime('%d-%m-%Y')
                    },
                    {
                        'documento': employee['documento'],
                        'nombre': employee['nombre'],
                        'situacion': 'BAJA',
                        'f_real_alta': alta_date.strftime('%d-%m-%Y'),
                        'f_efecto_alta': alta_date.strftime('%d-%m-%Y'),
                        'f_real_sit': baja_date.strftime('%d-%m-%Y')
                    }
                ])

            elif scenario == 'hired_and_left':
                # ALTA and BAJA in same year
                alta_date = date(year, random.randint(1, 8), random.randint(1, 28))
                baja_date = date(year, random.randint(alta_date.month + 1, 12), random.randint(1, 28))

                events.extend([
                    {
                        'documento': employee['documento'],
                        'nombre': employee['nombre'],
                        'situacion': 'ALTA',
                        'f_real_alta': alta_date.strftime('%d-%m-%Y'),
                        'f_efecto_alta': alta_date.strftime('%d-%m-%Y'),
                        'f_real_sit': alta_date.strftime('%d-%m-%Y')
                    },
                    {
                        'documento': employee['documento'],
                        'nombre': employee['nombre'],
                        'situacion': 'BAJA',
                        'f_real_alta': alta_date.strftime('%d-%m-%Y'),
                        'f_efecto_alta': alta_date.strftime('%d-%m-%Y'),
                        'f_real_sit': baja_date.strftime('%d-%m-%Y')
                    }
                ])

            elif scenario == 'vacation_after_baja':
                # ALTA, BAJA, then VAC.RETRIB.NO
                alta_date = date(year, random.randint(1, 6), random.randint(1, 28))
                baja_date = date(year, random.randint(alta_date.month + 1, 10), random.randint(1, 28))
                vacation_start = baja_date + timedelta(days=1)
                vacation_end = vacation_start + timedelta(days=random.randint(5, 15))

                events.extend([
                    {
                        'documento': employee['documento'],
                        'nombre': employee['nombre'],
                        'situacion': 'ALTA',
                        'f_real_alta': alta_date.strftime('%d-%m-%Y'),
                        'f_efecto_alta': alta_date.strftime('%d-%m-%Y'),
                        'f_real_sit': alta_date.strftime('%d-%m-%Y')
                    },
                    {
                        'documento': employee['documento'],
                        'nombre': employee['nombre'],
                        'situacion': 'BAJA',
                        'f_real_alta': alta_date.strftime('%d-%m-%Y'),
                        'f_efecto_alta': alta_date.strftime('%d-%m-%Y'),
                        'f_real_sit': baja_date.strftime('%d-%m-%Y')
                    },
                    {
                        'documento': employee['documento'],
                        'nombre': employee['nombre'],
                        'situacion': 'VAC.RETRIB.NO',
                        'f_real_alta': '',
                        'f_efecto_alta': '',
                        'f_real_sit': vacation_end.strftime('%d-%m-%Y')
                    }
                ])

        return events

    def generate_vida_laboral_csv(self, ccc_code: str = None, num_employees: int = 5, year: int = 2025) -> str:
        """Generate complete vida laboral CSV content"""
        if not ccc_code:
            ccc_code = self.data_gen.generate_ccc_code()

        employees = self.generate_employee_data(num_employees)
        events = self.generate_employment_events(employees, year)

        # Sort events by documento and date
        events.sort(key=lambda x: (x['documento'], x['f_real_sit']))

        # Generate CSV content
        output = []
        output.append('documento,nombre,situacion,f_real_alta,f_efecto_alta,f_real_sit')

        for event in events:
            line = f"{event['documento']},{event['nombre']},{event['situacion']},{event['f_real_alta']},{event['f_efecto_alta']},{event['f_real_sit']}"
            output.append(line)

        return '\n'.join(output)


class PayslipGenerator:
    """Generate realistic Spanish payslip data and PDFs"""

    def __init__(self, data_generator: SpanishDataGenerator):
        self.data_gen = data_generator
        self.salary_ranges = {
            'junior': (1200, 1800),
            'senior': (1800, 2500),
            'manager': (2500, 4000)
        }

    def generate_payroll_data(self, employee: Dict, year: int, month: int) -> Dict:
        """Generate payroll data for an employee for a specific month"""

        # Determine salary level
        level = random.choices(['junior', 'senior', 'manager'], weights=[60, 30, 10])[0]
        base_salary = random.randint(*self.salary_ranges[level])

        # Calculate components
        plus_convenio = base_salary * 0.1 if random.random() < 0.7 else 0
        plus_nocturnidad = base_salary * 0.05 if random.random() < 0.3 else 0
        horas_extra = random.randint(0, 200) if random.random() < 0.4 else 0

        # Total bruto
        bruto_total = base_salary + plus_convenio + plus_nocturnidad + horas_extra

        # IRPF calculation (simplified)
        if bruto_total <= 12450:
            irpf_rate = 0.19
        elif bruto_total <= 20200:
            irpf_rate = 0.24
        else:
            irpf_rate = 0.30

        irpf_retencion = bruto_total * irpf_rate * 0.8  # Adjusted for deductions

        # Social Security (employee portion)
        ss_rate = 0.063  # Approximate combined SS employee rate
        ss_trabajador = bruto_total * ss_rate

        # Net salary
        neto_total = bruto_total - irpf_retencion - ss_trabajador

        # In-kind benefits (occasional)
        seguro_medico = 50 if random.random() < 0.3 else 0
        ticket_restaurant = 120 if random.random() < 0.6 else 0

        return {
            'employee': employee,
            'period_year': year,
            'period_month': month,
            'period_start': date(year, month, 1),
            'period_end': self.last_day_of_month(year, month),
            'bruto_total': round(bruto_total, 2),
            'neto_total': round(neto_total, 2),
            'irpf_base_monetaria': round(bruto_total, 2),
            'irpf_retencion_monetaria': round(irpf_retencion, 2),
            'ss_trabajador_total': round(ss_trabajador, 2),
            'concepts': {
                '001': {'desc': 'Salario base', 'amount': base_salary},
                '120': {'desc': 'Plus convenio', 'amount': plus_convenio} if plus_convenio > 0 else None,
                '130': {'desc': 'Plus nocturnidad', 'amount': plus_nocturnidad} if plus_nocturnidad > 0 else None,
                '301': {'desc': 'Horas extra', 'amount': horas_extra} if horas_extra > 0 else None,
                '601': {'desc': 'Seguro médico', 'amount': seguro_medico} if seguro_medico > 0 else None,
                '620': {'desc': 'Ticket restaurant', 'amount': ticket_restaurant} if ticket_restaurant > 0 else None,
                '700': {'desc': 'IRPF', 'amount': -irpf_retencion},
                '730': {'desc': 'SS Trabajador', 'amount': -ss_trabajador}
            }
        }

    def last_day_of_month(self, year: int, month: int) -> date:
        """Get the last day of a month"""
        if month == 12:
            return date(year + 1, 1, 1) - timedelta(days=1)
        else:
            return date(year, month + 1, 1) - timedelta(days=1)

    def generate_payslip_html(self, payroll_data: Dict, company_name: str) -> str:
        """Generate HTML representation of a Spanish payslip"""

        # Clean up concepts (remove None values)
        concepts = {k: v for k, v in payroll_data['concepts'].items() if v is not None}

        html_content = f"""
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <title>Nómina - {payroll_data['employee']['normal_name']}</title>
    <style>
        body {{ font-family: Arial, sans-serif; font-size: 12px; margin: 20px; }}
        .header {{ text-align: center; margin-bottom: 20px; }}
        .company {{ font-size: 16px; font-weight: bold; }}
        .title {{ font-size: 14px; margin: 10px 0; }}
        .employee-info {{ border: 1px solid #ccc; padding: 10px; margin: 10px 0; }}
        .payroll-table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
        .payroll-table th, .payroll-table td {{ border: 1px solid #ccc; padding: 8px; text-align: left; }}
        .payroll-table th {{ background-color: #f5f5f5; }}
        .amount {{ text-align: right; }}
        .totals {{ background-color: #f0f0f0; font-weight: bold; }}
        .deduction {{ color: red; }}
    </style>
</head>
<body>
    <div class="header">
        <div class="company">{company_name}</div>
        <div class="title">RECIBO DE SALARIO</div>
        <div>Período: {payroll_data['period_start'].strftime('%d/%m/%Y')} - {payroll_data['period_end'].strftime('%d/%m/%Y')}</div>
    </div>

    <div class="employee-info">
        <strong>Trabajador:</strong> {payroll_data['employee']['normal_name']}<br>
        <strong>DNI/NIE:</strong> {payroll_data['employee']['documento']}<br>
        <strong>N.S.S.:</strong> {payroll_data['employee']['nss']}<br>
        <strong>Categoría:</strong> Empleado
    </div>

    <table class="payroll-table">
        <thead>
            <tr>
                <th>CONCEPTO</th>
                <th>CÓDIGO</th>
                <th class="amount">DEVENGOS</th>
                <th class="amount">DEDUCCIONES</th>
            </tr>
        </thead>
        <tbody>
"""

        # Add concept lines
        total_devengos = 0
        total_deducciones = 0

        for code, concept in concepts.items():
            amount = concept['amount']
            if amount > 0:
                devengo = f"{amount:.2f} €"
                deduccion = ""
                total_devengos += amount
            else:
                devengo = ""
                deduccion = f"{abs(amount):.2f} €"
                total_deducciones += abs(amount)

            html_content += f"""
            <tr>
                <td>{concept['desc']}</td>
                <td>{code}</td>
                <td class="amount">{devengo}</td>
                <td class="amount deduction">{deduccion}</td>
            </tr>
"""

        # Add totals
        html_content += f"""
            <tr class="totals">
                <td colspan="2">TOTALES</td>
                <td class="amount">{total_devengos:.2f} €</td>
                <td class="amount deduction">{total_deducciones:.2f} €</td>
            </tr>
        </tbody>
    </table>

    <div style="margin-top: 20px; font-size: 14px;">
        <strong>TOTAL A PERCIBIR: {payroll_data['neto_total']:.2f} €</strong>
    </div>

    <div style="margin-top: 30px; border-top: 1px solid #ccc; padding-top: 10px;">
        <strong>Bases y Deducciones Fiscales:</strong><br>
        Base IRPF: {payroll_data['irpf_base_monetaria']:.2f} €<br>
        Retención IRPF: {payroll_data['irpf_retencion_monetaria']:.2f} €<br>
        Seguridad Social Trabajador: {payroll_data['ss_trabajador_total']:.2f} €
    </div>
</body>
</html>
"""
        return html_content

    def generate_company_data(self, company_name: str, ccc_code: str) -> Dict:
        """Generate complete company data for accurate payslips"""
        return {
            'name': company_name,
            'cif': self.data_gen.generate_spanish_cif(),
            'ccc': ccc_code,
            'address': 'C/ FICTICIA, 123',
            'city': 'MADRID',
            'postal_code': '28001'
        }

    def generate_accurate_payslip_data(self, employee: Dict, company_data: Dict, year: int, month: int) -> Dict:
        """Generate accurate Spanish payslip data matching real format"""

        # Spanish Social Security rates (2025)
        SS_RATES = {
            'contingencias_comunes': 4.83,  # Employee portion
            'desempleo_fp': 1.65,          # Employee portion (unemployment + professional training)
            'cc_empresa': 24.27,           # Employer portion - common contingencies
            'at_ep_empresa': 1.50,         # Employer portion - workplace accidents
            'desempleo_empresa': 5.85,     # Employer portion - unemployment
            'fp_empresa': 0.70,            # Employer portion - professional training
            'fgs_empresa': 0.20            # Employer portion - salary guarantee fund
        }

        # Generate period dates
        period_start = date(year, month, 1)
        period_end = self.last_day_of_month(year, month)
        pay_date = self.last_day_of_month(year, month)
        days_worked = (period_end - period_start).days + 1

        # Determine salary level and calculate components
        level = random.choices(['junior', 'senior', 'manager'], weights=[60, 30, 10])[0]
        base_monthly = random.randint(*self.salary_ranges[level])
        daily_rate = round(base_monthly / 30, 2)

        # Salary components
        salario_base = round(daily_rate * days_worked, 2)
        p_prop_extras = round(salario_base * 0.1667, 2)  # ~16.67% for extra payments
        p_transp_jc = round(random.uniform(3.0, 6.0) * days_worked, 2) if random.random() < 0.7 else 0

        # Optional components
        autonomo = round(daily_rate * days_worked * 0.05, 2) if random.random() < 0.3 else 0
        mejoras_voluntarias = 50.00 if random.random() < 0.2 else 0

        # Total gross before deductions
        total_devengos_cotizables = salario_base + p_prop_extras + p_transp_jc + mejoras_voluntarias
        total_devengos_no_cotizables = autonomo
        total_bruto = total_devengos_cotizables + total_devengos_no_cotizables

        # Social Security deductions (employee portion)
        base_cotizacion = total_devengos_cotizables
        ss_comunes = round(base_cotizacion * SS_RATES['contingencias_comunes'] / 100, 2)
        ss_desempleo_fp = round(base_cotizacion * SS_RATES['desempleo_fp'] / 100, 2)

        # IRPF calculation
        annual_gross = total_bruto * 12
        if annual_gross <= 12450:
            irpf_rate = 0
        elif annual_gross <= 20200:
            irpf_rate = random.uniform(8, 12)
        elif annual_gross <= 35200:
            irpf_rate = random.uniform(12, 18)
        elif annual_gross <= 60000:
            irpf_rate = random.uniform(18, 24)
        else:
            irpf_rate = random.uniform(24, 30)

        irpf_retencion = round(total_bruto * irpf_rate / 100, 2)

        # Total deductions
        total_deducciones = ss_comunes + ss_desempleo_fp + irpf_retencion

        # Net salary
        liquido_total = round(total_bruto - total_deducciones, 2)

        # Company contributions (for informational section)
        empresa_cc = round(base_cotizacion * SS_RATES['cc_empresa'] / 100, 2)
        empresa_at_ep = round(base_cotizacion * SS_RATES['at_ep_empresa'] / 100, 2)
        empresa_desempleo = round(base_cotizacion * SS_RATES['desempleo_empresa'] / 100, 2)
        empresa_fp = round(base_cotizacion * SS_RATES['fp_empresa'] / 100, 2)
        empresa_fgs = round(base_cotizacion * SS_RATES['fgs_empresa'] / 100, 2)

        return {
            'company': company_data,
            'employee': employee,
            'category': 'ESPECIALISTA' if level == 'senior' else 'TÉCNICO' if level == 'junior' else 'JEFE DE EQUIPO',
            'period': {
                'start': period_start,
                'end': period_end,
                'pay_date': pay_date,
                'days': days_worked
            },
            'salary_components': {
                'salario_base': {'cuantia': days_worked, 'precio': daily_rate, 'total': salario_base},
                'p_prop_extras': {'total': p_prop_extras},
                'p_transp_jc': {'cuantia': days_worked, 'precio': round(p_transp_jc/30, 4), 'total': p_transp_jc} if p_transp_jc > 0 else None,
                'autonomo': {'cuantia': days_worked, 'precio': round(autonomo/days_worked, 4), 'total': autonomo} if autonomo > 0 else None,
                'mejoras_voluntarias': {'cuantia': 1, 'precio': mejoras_voluntarias, 'total': mejoras_voluntarias} if mejoras_voluntarias > 0 else None
            },
            'deductions': {
                'ss_comunes': {'rate': SS_RATES['contingencias_comunes'], 'total': ss_comunes},
                'ss_desempleo_fp': {'rate': SS_RATES['desempleo_fp'], 'total': ss_desempleo_fp},
                'irpf': {'rate': irpf_rate, 'total': irpf_retencion}
            },
            'totals': {
                'base_cotizacion': base_cotizacion,
                'total_devengos': total_bruto,
                'total_deducciones': total_deducciones,
                'liquido_total': liquido_total
            },
            'empresa_contributions': {
                'contingencias_comunes': empresa_cc,
                'at_ep': empresa_at_ep,
                'desempleo': empresa_desempleo,
                'formacion_profesional': empresa_fp,
                'fondo_garantia_salarial': empresa_fgs
            }
        }

    def generate_accurate_payslip_html(self, payslip_data: Dict) -> str:
        """Generate HTML payslip matching exact Spanish legal format"""

        data = payslip_data
        company = data['company']
        employee = data['employee']
        period = data['period']
        salary = data['salary_components']
        deductions = data['deductions']
        totals = data['totals']
        empresa = data['empresa_contributions']

        html = f"""<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <title>Nómina - {employee['normal_name']}</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            font-size: 10px;
            margin: 0;
            padding: 20px;
            line-height: 1.2;
        }}
        .payslip-container {{
            max-width: 210mm;
            margin: 0 auto;
            border: 2px solid black;
            padding: 0;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            font-size: 10px;
        }}
        td, th {{
            border: 1px solid black;
            padding: 3px;
            vertical-align: top;
        }}
        .header-company {{
            font-weight: bold;
            text-align: left;
        }}
        .header-right {{
            text-align: right;
            font-weight: bold;
        }}
        .employee-section {{
            background-color: #f8f8f8;
        }}
        .concepts-header {{
            background-color: #e0e0e0;
            font-weight: bold;
            text-align: center;
            font-size: 9px;
        }}
        .number-right {{
            text-align: right;
        }}
        .totals-section {{
            background-color: #f0f0f0;
            font-weight: bold;
        }}
        .empresa-section {{
            font-size: 9px;
        }}
        .signature-section {{
            border: none;
            padding: 20px;
            font-weight: bold;
        }}
    </style>
</head>
<body>
    <div class="payslip-container">
        <!-- Header Company Info -->
        <table>
            <tr>
                <td class="header-company" style="width: 60%;">EMPRESA (razón social)</td>
                <td class="header-right" style="width: 40%;">RECIBO DE SALARIOS</td>
            </tr>
            <tr>
                <td class="header-company">{company['name']}<br>
                    C.I.F.: {company['cif']}<br>
                    C.C.C.: {company['ccc']}
                </td>
                <td class="header-right">
                    MES DE {period['start'].strftime('%B').upper()} DE {period['start'].year}<br>
                    FECHA DE PAGO: {period['pay_date'].strftime('%d/%m/%Y')}
                </td>
            </tr>
        </table>

        <!-- Employee Information -->
        <table>
            <tr class="employee-section">
                <td style="width: 50%;"><strong>TRABAJADOR</strong></td>
                <td style="width: 50%;"><strong>DATOS PROFESIONALES</strong></td>
            </tr>
            <tr class="employee-section">
                <td>
                    APELLIDOS Y NOMBRE: {employee['normal_name']}<br>
                    D.N.I./N.I.E.: {employee['documento']}<br>
                    Nº AFILIACIÓN S.S.: {employee['nss']}
                </td>
                <td>
                    CATEGORÍA PROFESIONAL: {data['category']}<br>
                    GRUPO DE COTIZACIÓN: 05<br>
                    DÍAS: {period['days']}
                </td>
            </tr>
        </table>

        <!-- Salary Concepts Table -->
        <table>
            <tr class="concepts-header">
                <td style="width: 40%;">CONCEPTO</td>
                <td style="width: 10%;">CUANTÍA</td>
                <td style="width: 10%;">PRECIO</td>
                <td style="width: 10%;">TOTAL</td>
                <td style="width: 15%;">A DEDUCIR POR EL TRABAJADOR</td>
                <td style="width: 15%;">TIPO %</td>
            </tr>"""

        # Salary components (earnings)
        if salary['salario_base']:
            sb = salary['salario_base']
            html += f"""
            <tr>
                <td>SALARIO BASE</td>
                <td class="number-right">{sb['cuantia']:.0f}</td>
                <td class="number-right">{sb['precio']:.2f}</td>
                <td class="number-right">{sb['total']:.2f}</td>
                <td></td>
                <td></td>
            </tr>"""

        if salary['p_prop_extras']:
            ppe = salary['p_prop_extras']
            html += f"""
            <tr>
                <td>P.PROP. EXTRAS</td>
                <td></td>
                <td></td>
                <td class="number-right">{ppe['total']:.2f}</td>
                <td></td>
                <td></td>
            </tr>"""

        if salary['p_transp_jc'] and salary['p_transp_jc']['total'] > 0:
            ptjc = salary['p_transp_jc']
            html += f"""
            <tr>
                <td>P.TRANSP. J.C.</td>
                <td class="number-right">{ptjc['cuantia']:.0f}</td>
                <td class="number-right">{ptjc['precio']:.4f}</td>
                <td class="number-right">{ptjc['total']:.2f}</td>
                <td></td>
                <td></td>
            </tr>"""

        if salary['autonomo'] and salary['autonomo']['total'] > 0:
            auto = salary['autonomo']
            html += f"""
            <tr>
                <td>AUTÓNOMO</td>
                <td class="number-right">{auto['cuantia']:.0f}</td>
                <td class="number-right">{auto['precio']:.4f}</td>
                <td class="number-right">{auto['total']:.2f}</td>
                <td></td>
                <td></td>
            </tr>"""

        if salary['mejoras_voluntarias'] and salary['mejoras_voluntarias']['total'] > 0:
            mv = salary['mejoras_voluntarias']
            html += f"""
            <tr>
                <td>MEJORAS VOLUNTARIAS</td>
                <td class="number-right">{mv['cuantia']:.0f}</td>
                <td class="number-right">{mv['precio']:.2f}</td>
                <td class="number-right">{mv['total']:.2f}</td>
                <td></td>
                <td></td>
            </tr>"""

        # Deductions
        ss_cc = deductions['ss_comunes']
        html += f"""
            <tr>
                <td>DTO. CONT. COMUNES {ss_cc['rate']:.2f}%</td>
                <td></td>
                <td></td>
                <td class="number-right">{totals['base_cotizacion']:.2f}</td>
                <td class="number-right">{ss_cc['total']:.2f}</td>
                <td class="number-right">{ss_cc['rate']:.2f}</td>
            </tr>"""

        ss_df = deductions['ss_desempleo_fp']
        html += f"""
            <tr>
                <td>DTO. DESEMP. F.P. {ss_df['rate']:.2f}%</td>
                <td></td>
                <td></td>
                <td class="number-right">{totals['base_cotizacion']:.2f}</td>
                <td class="number-right">{ss_df['total']:.2f}</td>
                <td class="number-right">{ss_df['rate']:.2f}</td>
            </tr>"""

        irpf = deductions['irpf']
        html += f"""
            <tr>
                <td>RETENCIÓN IRPF {irpf['rate']:.2f}%</td>
                <td></td>
                <td></td>
                <td class="number-right">{totals['total_devengos']:.2f}</td>
                <td class="number-right">{irpf['total']:.2f}</td>
                <td class="number-right">{irpf['rate']:.2f}</td>
            </tr>"""

        # Totals section
        html += f"""
            <tr class="totals-section">
                <td><strong>TOTALES</strong></td>
                <td></td>
                <td></td>
                <td class="number-right"><strong>{totals['total_devengos']:.2f}</strong></td>
                <td class="number-right"><strong>{totals['total_deducciones']:.2f}</strong></td>
                <td></td>
            </tr>
            <tr class="totals-section">
                <td colspan="3"><strong>LÍQUIDO TOTAL A PERCIBIR</strong></td>
                <td colspan="3" class="number-right"><strong>{totals['liquido_total']:.2f} €</strong></td>
            </tr>
        </table>

        <!-- Company Contributions Section -->
        <table>
            <tr class="concepts-header">
                <td colspan="6">BASES Y TIPOS DE COTIZACIÓN - APORTACIÓN EMPRESARIAL</td>
            </tr>
            <tr class="empresa-section">
                <td>CONTINGENCIAS COMUNES</td>
                <td class="number-right">{totals['base_cotizacion']:.2f}</td>
                <td class="number-right">24.27%</td>
                <td class="number-right">{empresa['contingencias_comunes']:.2f}</td>
                <td></td>
                <td></td>
            </tr>
            <tr class="empresa-section">
                <td>ACCIDENTES DE TRABAJO Y E.P.</td>
                <td class="number-right">{totals['base_cotizacion']:.2f}</td>
                <td class="number-right">1.50%</td>
                <td class="number-right">{empresa['at_ep']:.2f}</td>
                <td></td>
                <td></td>
            </tr>
            <tr class="empresa-section">
                <td>DESEMPLEO</td>
                <td class="number-right">{totals['base_cotizacion']:.2f}</td>
                <td class="number-right">5.85%</td>
                <td class="number-right">{empresa['desempleo']:.2f}</td>
                <td></td>
                <td></td>
            </tr>
            <tr class="empresa-section">
                <td>FORMACIÓN PROFESIONAL</td>
                <td class="number-right">{totals['base_cotizacion']:.2f}</td>
                <td class="number-right">0.70%</td>
                <td class="number-right">{empresa['formacion_profesional']:.2f}</td>
                <td></td>
                <td></td>
            </tr>
            <tr class="empresa-section">
                <td>FONDO DE GARANTÍA SALARIAL</td>
                <td class="number-right">{totals['base_cotizacion']:.2f}</td>
                <td class="number-right">0.20%</td>
                <td class="number-right">{empresa['fondo_garantia_salarial']:.2f}</td>
                <td></td>
                <td></td>
            </tr>
        </table>

        <!-- Signature Section -->
        <table>
            <tr>
                <td class="signature-section" style="text-align: center;">El trabajador</td>
            </tr>
        </table>
    </div>
</body>
</html>"""

        return html


def generate_test_dataset(output_dir: str = "./test_data", num_employees: int = 4, year: int = 2025):
    """Generate complete test dataset with vida laboral and payslips"""

    # Create output directory
    os.makedirs(output_dir, exist_ok=True)

    # Initialize generators
    data_gen = SpanishDataGenerator()
    vida_gen = VidaLaboralGenerator(data_gen)
    payslip_gen = PayslipGenerator(data_gen)

    # Generate company info
    company_name = random.choice(SPANISH_COMPANIES)
    ccc_code = data_gen.generate_ccc_code()
    company_data = payslip_gen.generate_company_data(company_name, ccc_code)

    print(f"🏢 Generating test data for: {company_name}")
    print(f"📋 CCC Code: {ccc_code}")
    print(f"👥 Employees: {num_employees}")
    print(f"📅 Year: {year}")

    # Generate vida laboral CSV
    print("\n📄 Generating vida laboral CSV...")
    vida_csv_content = vida_gen.generate_vida_laboral_csv(ccc_code, num_employees, year)

    # Save vida laboral CSV
    vida_csv_path = os.path.join(output_dir, f"vida_laboral_{ccc_code}_{year}.csv")
    with open(vida_csv_path, 'w', encoding='utf-8') as f:
        f.write(vida_csv_content)

    print(f"✓ Vida laboral saved: {vida_csv_path}")

    # Parse the CSV to get employee data
    employees_data = {}
    lines = vida_csv_content.strip().split('\n')[1:]  # Skip header

    for line in lines:
        parts = line.split(',')
        documento = parts[0]
        nombre_vida = parts[1]

        if documento not in employees_data:
            # Convert vida laboral name format to normal format
            name_parts = nombre_vida.split(' --- ')
            surnames = name_parts[0].strip()
            first_name = name_parts[1].strip() if len(name_parts) > 1 else "UNKNOWN"
            normal_name = f"{first_name} {surnames}"

            employees_data[documento] = {
                'documento': documento,
                'normal_name': normal_name,
                'vida_name': nombre_vida,
                'nss': data_gen.generate_nss()
            }

    print(f"\n💼 Generating payslips for {len(employees_data)} employees...")

    # Create payslips directory
    payslips_dir = os.path.join(output_dir, "payslips")
    os.makedirs(payslips_dir, exist_ok=True)

    # Generate payslips for each employee
    for employee_doc, employee in employees_data.items():
        print(f"   📋 {employee['normal_name']}")

        # Create employee directory
        employee_dir = os.path.join(payslips_dir, f"employee_{employee_doc}")
        os.makedirs(employee_dir, exist_ok=True)

        # Generate payslips for most months (with some gaps)
        months_to_generate = random.sample(range(1, 13), random.randint(8, 11))  # 8-11 months

        for month in months_to_generate:
            # Generate accurate payroll data
            payroll_data = payslip_gen.generate_accurate_payslip_data(employee, company_data, year, month)

            # Generate accurate HTML payslip
            html_content = payslip_gen.generate_accurate_payslip_html(payroll_data)

            # Save HTML file (can be converted to PDF later with tools like wkhtmltopdf)
            filename = f"nomina_{year}_{month:02d}.html"
            file_path = os.path.join(employee_dir, filename)

            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(html_content)

        missing_months = set(range(1, 13)) - set(months_to_generate)
        if missing_months:
            print(f"     ⚠️  Missing months: {sorted(missing_months)} (for testing)")

    # Generate summary report
    summary_path = os.path.join(output_dir, "test_data_summary.txt")
    with open(summary_path, 'w', encoding='utf-8') as f:
        f.write(f"ValerIA Test Data Summary\n")
        f.write(f"========================\n\n")
        f.write(f"Company: {company_name}\n")
        f.write(f"CCC Code: {ccc_code}\n")
        f.write(f"Year: {year}\n")
        f.write(f"Employees: {len(employees_data)}\n\n")
        f.write(f"Files generated:\n")
        f.write(f"- vida_laboral_{ccc_code}_{year}.csv\n")
        f.write(f"- payslips/ (directory with HTML payslips)\n\n")
        f.write(f"Employee details:\n")

        for employee_doc, employee in employees_data.items():
            f.write(f"- {employee['normal_name']} ({employee_doc})\n")

    print(f"\n✅ Test data generation complete!")
    print(f"📁 Output directory: {output_dir}")
    print(f"📄 Summary: {summary_path}")
    print(f"\n💡 To convert HTML payslips to PDF, you can use:")
    print(f"   wkhtmltopdf payslips/employee_*/nomina_*.html payslips/employee_*/nomina_*.pdf")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='Generate synthetic Spanish payroll test data')
    parser.add_argument('--output-dir', default='./test_data', help='Output directory')
    parser.add_argument('--employees', type=int, default=4, help='Number of employees')
    parser.add_argument('--year', type=int, default=2025, help='Year for data generation')

    args = parser.parse_args()

    generate_test_dataset(args.output_dir, args.employees, args.year)