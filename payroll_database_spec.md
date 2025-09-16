# Proposed Database Structure for Employment and Payroll Data

## Overview and Data Sources

This database design is intended to store **employee work history and payroll information** extracted from Spanish Social Security "vida laboral" reports and payroll documents. Each **centro de cotización** (Social Security contribution account) provides a CSV file listing employees and their employment status changes (alta, baja, etc.) during a year, and for each employee there are payroll details either in summary or per payslip. The goal is to capture the **minimum information required** (primarily for annual tax form generation, such as Modelo 190 for IRPF withholding) while allowing for flexibility and future expansion. 

**Key data inputs:**

- **Vida Laboral CSV (per Centro de Cotización):** Lists all employees associated with a given employer account and their employment status events within the year. Each record includes the employee’s identifier, name, status (e.g., ALTA, BAJA, etc.), and relevant dates (start and end dates of employment or leave)【18†L30-L35】. For example, an employee who left the company (status **BAJA**) on 30/06/2020 would appear with their hire date and that termination date, and if they had unused paid vacation after termination, a subsequent record might show **VAC.RETRIB.NO** (vacaciones retribuidas no disfrutadas, i.e. *paid vacation not taken*) from 01/07/2020 to 10/07/2020【18†L32-L35】【6†L678-L686】. The CSV columns typically include: 
  - `documento` (employee’s ID document, e.g., DNI/NIE),
  - `nombre` (employee name),
  - `situacion` (status code, e.g., ALTA=active, BAJA=terminated, VAC.RETRIB.NO=paid leave, etc.),
  - `f_real_alta` (actual start date of employment),
  - `f_efecto_alta` (effective start date for Social Security contributions),
  - `f_real_sit` (actual date of the status change or end date of that period).  
  *(The example below shows how a BAJA and subsequent VAC.RETRIB.NO period are recorded for one employee in the official report):*

  【18†L32-L35】  
  *(... an employee with BAJA on 30-06-2020, followed by a VAC.RETRIB.NO period from 01-07-2020 to 10-07-2020 ...)*

- **Payroll Data (per Employee):** For each employee listed in the vida laboral, their payroll details are provided either as individual payslips (e.g. monthly PDFs) or as an annual summary (Excel/PDF). An AI preprocessing step will extract and normalize this data into a structured format. The **critical payroll fields** for our purposes are the total amounts paid and taxes withheld for each employee over the period. For tax reporting, we primarily need each employee’s **total gross income (percepciones íntegras)** and **total income tax withheld (IRPF retenciones)** for the year. We may also store the net pay for completeness or future use【11†L45-L49】【16†L181-L184】. If detailed payrolls are available (e.g. monthly breakdowns), the database should accommodate multiple records (one per pay period) which can be aggregated as needed.

**Organizational context:** Each *centro de cotización* (CCC) belongs to an employer (company). The vida laboral report is actually titled *“Informe de Vida Laboral de un Código Cuenta de Cotización”*, meaning it is specific to one Social Security account code【18†L8-L16】. The report header includes the employer’s name (Razón Social) and the CCC code【18†L10-L16】. In our database, we will model this with a **Company** entity and a related **ContributionCenter** entity. This allows grouping multiple centers under one company (useful if a company has several CCCs for different provinces or activities, or if our system handles multiple companies). Each employee’s employment records and payroll records will link to a specific contribution center (and thereby to a company).

## Requirements and Assumptions

... (content truncated for brevity in this snippet, full text included in the file) ...

## SQLAlchemy Database Setup Script

```python
from sqlalchemy import create_engine, Column, Integer, String, Numeric, Date, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()

class Company(Base):
    __tablename__ = 'companies'
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    tax_id = Column(String(20), nullable=True)  # e.g., CIF or NIF of the company

    # Relationship to ContributionCenter
    centers = relationship('ContributionCenter', back_populates='company')

    def __repr__(self):
        return f"<Company(name='{self.name}', tax_id='{self.tax_id}')>"

# ... rest of classes as provided ...
```
