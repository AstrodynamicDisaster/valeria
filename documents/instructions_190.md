I want to work on the 190.py file. This file shall generate a .txt file with a format consistent with the 190 spanish tax model (resumen anual IRPF)

In general, we are only interested in clave A and Clave L subclaves 01, 05, 24, 25, 26

In our database, in the Payroll Lines table, we already classify a payroll line item as (there are more columns but this are the meaningful ones for this task):

{
    "type": devengo
    "concept": "SALARIO BASE"
    "is_taxable_income": true, 
    "is_taxable_ss": true, 
    "is_sickpay": false, 
    "is_in_kind": false, 
    "is_pay_advance": false, 
    "is_seizure": false
}

{  
    "type": deduccion,
    "concept": "DESC. AT Y DES"
    "is_taxable_income": false, 
    "is_taxable_ss": false, 
    "is_sickpay": false, 
    "is_in_kind": false, 
    "is_pay_advance": false, 
    "is_seizure": false
}

Then, I would map a list of conceptos to define each pair of clave and subclave different than A. That is (made up list)

concepts = [
    {
        "clave": "L",
        "subclave": "05",
        "concepts": ["INDEMNIZACION"]
    },
    {
        "clave": "L",
        "subclave": "25",
        "concepts": ["TRANSPORTE", "ROPA"]    
    },
    ...
]

All the concepts not in the list then default to table A. Additionally, I would define another mapping in the form:

ss_tax_concepts = ["MEI","FORMACION PROFESIONAL","AT Y EP",...]

The idea is that with all the above, we can end up building, for each record, something like below:

{
    "type": devengo
    "concept": "SALARIO BASE"
    "is_taxable_income": true, 
    "is_taxable_ss": true, 
    "is_sickpay": false, 
    "is_in_kind": false, 
    "is_pay_advance": false, 
    "is_seizure": false, 
    "clave": "A", 
    "subclave": null
    "is_ss_tax": false
}

{  
    "type": deduccion,
    "concept": "DESC. AT Y DES"
    "is_taxable_income": false, 
    "is_taxable_ss": false, 
    "is_sickpay": false, 
    "is_in_kind": false, 
    "is_pay_advance": false, 
    "is_seizure": false, 
    "clave": "A", 
    "subclave": null
    "is_ss_tax": true
}

{
    "type": devengo
    "concept": "SALARIO BASE"
    "is_taxable_income": true, 
    "is_taxable_ss": true, 
    "is_sickpay": false, 
    "is_in_kind": false, 
    "is_pay_advance": false, 
    "is_seizure": false, 
    "clave": "A", 
    "subclave": null
    "is_ss_tax": false
}

{  
    "type": deduccion,
    "concept": "DESC. AT Y DES"
    "is_taxable_income": false, 
    "is_taxable_ss": false, 
    "is_sickpay": false, 
    "is_in_kind": false, 
    "is_pay_advance": false, 
    "is_seizure": false, 
    "clave": "A", 
    "subclave": null
    "is_ss_tax": true
}

This does not need to be done explicitly (calculating it and saving it into a variable) but this mapping should help the queries to make sure that the grouping and summing only refers to the right concepts, so the mapping arrays should influence the filters for each query.

With this prologue clear, there are three main tasks:

- Building all the queries to obtain the essential pieces of data from the database. This would be functions that return for a CIF and period, a table with all employees with any payroll within the period so that

    1. Percepción integra NO IT: Sum of all payroll lines (concepts) per employee for each clave and subclave where type is devengo and is_sickpay is false
    2. Retenciones practicadas no IT: For each clave, subclave and each employee and each payroll, sum the amounts of devengos that have is_taxable_income true, multiply it by the tipo_IRPF of that payroll, and sum accross payrolls to end up with a total per employee and subclave
    3. Gastos deducibles: For each clave, subclave and employee, the sum of all devengo payroll items that have is_ss_tax as true.
    4. Percepción integra IT: Sum of all payroll lines (concepts) per employee for each clave and subclave where type is devengo and is_sickpay is false
    5. Retenciones practicadas IT: 

- Setting default values for the fields which are not applicable to our case:

1. Identify which parts are overkill (things about diputaicones forales, navarra, or anything that for the clave or the kind of payroll we do is not applicable here)
2. Identify which parts can be set by default (e.g. pensiones, situación familiar, etc.)

- Generate the proper .txt document with the format required by the spanish tax authority, according to the DISENOS LOGICOS PDF

USE THE spec_190 document and the PDF Disenos logicos as reference as they contain all the info you need.