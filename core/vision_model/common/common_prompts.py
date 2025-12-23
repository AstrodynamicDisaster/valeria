# payslip_bible_cotizations_prompt_csv = """
# This is a list of concepts that are commonly found in payslips, and the information about the cotizations, if it's a 'especie' or 'dinerario' and contributions that are applied to them:
#
# Concept;Tipo;Cotiza_Seg.Social;Tributa_IRPF;Is_Especie
# ---
# Salario base;Totales;TRUE;TRUE;FALSE
# Bolsa de estudios;Totales;TRUE;TRUE;FALSE
# Gratificacion - PExtras;Totales;TRUE;TRUE;FALSE
# Mejora Voluntaria;Totales;TRUE;TRUE;FALSE
# Incentivos;Totales;TRUE;TRUE;FALSE
# Bonus;Totales;TRUE;TRUE;FALSE
# Bonus (Neto);Totales;TRUE;TRUE;FALSE
# Plus implicación;Totales;TRUE;TRUE;FALSE
# Plus Reseñas;Totales;TRUE;TRUE;FALSE
# Plus herramientas de trabajo;Totales;TRUE;TRUE;FALSE
# Bonus neto;Totales;FALSE;FALSE;FALSE
# Primas;Totales;TRUE;TRUE;FALSE
# Retr Administrador;Totales;TRUE;TRUE;FALSE
# Sign-in Bonus;Totales;TRUE;TRUE;FALSE
# Autonomos;Totales;FALSE;TRUE;TRUE
# Ajuste SMI;Totales;TRUE;TRUE;FALSE
# Plus Compensable/Absorbible;Totales;TRUE;TRUE;FALSE
# Exclusividad;Totales;TRUE;TRUE;FALSE
# Non-compete;Totales;TRUE;TRUE;FALSE
# Festivos trabajados;Unidades;TRUE;TRUE;FALSE
# Horas nocturnas;Unidades;TRUE;TRUE;FALSE
# Plus Ropa;Unidades;TRUE;TRUE;FALSE
# Plus Ropa (Especie);Unidades;TRUE;TRUE;TRUE
# Manutención (Especie);Unidades;TRUE;TRUE;TRUE
# Manutención (Dinerario);Unidades;TRUE;TRUE;FALSE
# Dietas (sin pernocta) - Viaje;Totales;FALSE;FALSE;FALSE
# Dietas (con pernocta) - Viaje;Totales;FALSE;FALSE;FALSE
# Plus Transporte;Totales;TRUE;TRUE;FALSE
# Kilometraje;Totales;FALSE;FALSE;FALSE
# Gastos locomoción;Totales;FALSE;FALSE;FALSE
# Plus peligrosidad;Totales;TRUE;TRUE;FALSE
# Ajuste vacaciones disfrutadas;Totales;FALSE;FALSE;FALSE
# Ajuste error vacaciones - Descuento;Totales;FALSE;FALSE;FALSE
# Ajuste error vacaciones - Cobro;Totales;FALSE;TRUE;FALSE
# Vacaciones manual;Unidades;TRUE;TRUE;FALSE
# *Parte Proporcional Vacaciones Finiquito ;Unidades;TRUE;TRUE;FALSE
# Horas complementarias;Unidades;TRUE;TRUE;FALSE
# Horas extras;Unidades;TRUE;TRUE;FALSE
# Actividad (H. Extras);Unidades;TRUE;TRUE;FALSE
# Absentismo;Unidades (Horas);TRUE;TRUE;FALSE
# Efectivo;Totales;FALSE;FALSE;FALSE
# CashBalance;Totales;FALSE;FALSE;FALSE
# Devolución efectivo;Totales;FALSE;FALSE;FALSE
# Descuento nomina;Totales;TRUE;TRUE;FALSE
# Vacaciones disfrutadas no generadas;Totales;TRUE;TRUE;FALSE
# Ajuste - Descuento error previo;Totales;TRUE;TRUE;FALSE
# Ajuste - Descuento error horas;Totales;TRUE;TRUE;FALSE
# Ajuste Positivo;Totales;TRUE;TRUE;FALSE
# Seguro Medico Trabajador;Totales;TRUE;FALSE;TRUE
# Seguro Medico Exento;Totales;FALSE;FALSE;TRUE
# Seguro Accidentes;Totales;FALSE;FALSE;TRUE
# Paga extra prorrateada;Totales;TRUE;TRUE;FALSE
# Subida convenio Pendiente;Totales;TRUE;TRUE;FALSE
# Regularizacion meses anteriores;Totales;TRUE;TRUE;FALSE
# Regularizacion meses anteriores;Totales;TRUE;TRUE;FALSE
# Propinas - C/IRPF;Totales;FALSE;TRUE;FALSE
# Propinas - S/IRPF;Totales;FALSE;FALSE;FALSE
# """


payslip_bible_cotizations_prompt = """
### **OFFICIAL CONCEPT REFERENCE TABLE**
Use this table as the absolute source of truth for classifying items. If a concept in the payslip matches one of these (partially or fully), apply the attributes listed below.

| Concept | Type | Cotiza SS | Tributa IRPF | Is Especie |
| :--- | :--- | :---: | :---: | :---: |
| **FIXED SALARY** | | | | |
| SALARIO BASE | Totales | TRUE | TRUE | FALSE |
| AJUSTE SMI | Totales | TRUE | TRUE | FALSE |
| MEJORA VOLUNTARIA | Totales | TRUE | TRUE | FALSE |
| RETR ADMINISTRADOR | Totales | TRUE | TRUE | FALSE |
| **BONUSES & INCENTIVES** | | | | |
| INCENTIVOS | Totales | TRUE | TRUE | FALSE |
| BONUS | Totales | TRUE | TRUE | FALSE |
| PRIMAS | Totales | TRUE | TRUE | FALSE |
| PLUS IMPLICACIÓN | Totales | TRUE | TRUE | FALSE |
| SIGN-IN BONUS | Totales | TRUE | TRUE | FALSE |
| **EXTRAS & NIGHT SHIFTS** | | | | |
| GRATIFICACION - PEXTRAS | Totales | TRUE | TRUE | FALSE |
| PAGA EXTRA PRORRATEADA | Totales | TRUE | TRUE | FALSE |
| HORAS NOCTURNAS | Unidades | TRUE | TRUE | FALSE |
| FESTIVOS TRABAJADOS | Unidades | TRUE | TRUE | FALSE |
| **BENEFITS & IN-KIND** | | | | |
| SEGURO MEDICO TRABAJADOR | Totales | TRUE | FALSE | TRUE |
| SEGURO MEDICO EXENTO | Totales | FALSE | FALSE | TRUE |
| MANUTENCIÓN (ESPECIE) | Unidades | TRUE | TRUE | TRUE |
| TICKET RESTAURANT (ESPECIE) | Totales | FALSE | FALSE | TRUE |
| **EXPENSES & TRAVEL** | | | | |
| PLUS TRANSPORTE | Totales | TRUE | TRUE | FALSE |
| DIETAS (SIN PERNOCTA) | Totales | FALSE | FALSE | FALSE |
| KILOMETRAJE | Totales | FALSE | FALSE | FALSE |
| **ADJUSTMENTS & SETTLEMENTS** | | | | |
| VACACIONES MANUAL | Unidades | TRUE | TRUE | FALSE |
| *PARTE PROP. VACACIONES FINIQUITO | Unidades | TRUE | TRUE | FALSE |
| AJUSTE POSITIVO | Totales | TRUE | TRUE | FALSE |
| DESCUENTO NOMINA | Totales | TRUE | TRUE | FALSE |
| REGULARIZACION MESES ANTERIORES | Totales | TRUE | TRUE | FALSE |

*(Note: If a concept is not listed, use your best judgment based on the most similar category above.)*
"""


payslip_example_output = """
```json
{
 "empresa": {
  "razon_social": "DANIK IMPORT & SUPLY SL",
  "cif": "B56222938"
 },
 "trabajador": {
  "nombre": "AHMED, TUFAYEL",
  "dni": "Y3683098F",
  "ss_number": "071074115236"
 },
 "periodo": {
  "desde": "2025-05-01",
  "hasta": "2025-05-31",
  "dias": 30
 },
 "devengo_items": [
  {
   "concepto_raw": "SALARIO BASE",
   "concepto_standardized": "SALARIO BASE",
   "importe": 259.27,
   "tipo": null,
   "item_type": {
    "ind_is_especie": false,
    "ind_is_IT_IL": false,
    "ind_is_anticipo": false,
    "ind_is_embargo": false,
    "ind_tributa_IRPF": true,
    "ind_cotiza_ss": true
   }
  },
  {
   "concepto_raw": "INCENTIVOS",
   "concepto_standardized": "INCENTIVOS",
   "importe": 41.78,
   "tipo": null,
   "item_type": {
    "ind_is_especie": false,
    "ind_is_IT_IL": false,
    "ind_is_anticipo": false,
    "ind_is_embargo": false,
    "ind_tributa_IRPF": true,
    "ind_cotiza_ss": true
   }
  },
  {
   "concepto_raw": "NOCTURNIDAD",
   "concepto_standardized": "NOCTURNIDAD",
   "importe": 5.22,
   "tipo": null,
   "item_type": {
    "ind_is_especie": false,
    "ind_is_IT_IL": false,
    "ind_is_anticipo": false,
    "ind_is_embargo": false,
    "ind_tributa_IRPF": true,
    "ind_cotiza_ss": true
   }
  },
  {
   "concepto_raw": "TBJO. DOMINGOS/FESTIVOS",
   "concepto_standardized": "TBJO. DOMINGOS/FESTIVOS",
   "importe": 36.54,
   "tipo": null,
   "item_type": {
    "ind_is_especie": false,
    "ind_is_IT_IL": false,
    "ind_is_anticipo": false,
    "ind_is_embargo": false,
    "ind_tributa_IRPF": true,
    "ind_cotiza_ss": true
   }
  },
  {
   "concepto_raw": "MEJORA VOLUNTARIA",
   "concepto_standardized": "MEJORA VOLUNTARIA",
   "importe": 203.32,
   "tipo": null,
   "item_type": {
    "ind_is_especie": false,
    "ind_is_IT_IL": false,
    "ind_is_anticipo": false,
    "ind_is_embargo": false,
    "ind_tributa_IRPF": true,
    "ind_cotiza_ss": true
   }
  },
  {
   "concepto_raw": "PAGA EXTRA",
   "concepto_standardized": "PAGA EXTRA",
   "importe": 43.21,
   "tipo": null,
   "item_type": {
    "ind_is_especie": false,
    "ind_is_IT_IL": false,
    "ind_is_anticipo": false,
    "ind_is_embargo": false,
    "ind_tributa_IRPF": true,
    "ind_cotiza_ss": true
   }
  },
  {
   "concepto_raw": "ENFERMEDAD 60% EMP.",
   "concepto_standardized": "ENFERMEDAD 60% EMP.",
   "importe": 385.57,
   "tipo": null,
   "item_type": {
    "ind_is_especie": false,
    "ind_is_IT_IL": true,
    "ind_is_anticipo": false,
    "ind_is_embargo": false,
    "ind_tributa_IRPF": true,
    "ind_cotiza_ss": true
   }
  },
  {
   "concepto_raw": "ENFERMEDAD 60% INS.",
   "concepto_standardized": "ENFERMEDAD 60% INS.",
   "importe": 128.52,
   "tipo": null,
   "item_type": {
    "ind_is_especie": false,
    "ind_is_IT_IL": true,
    "ind_is_anticipo": false,
    "ind_is_embargo": false,
    "ind_tributa_IRPF": true,
    "ind_cotiza_ss": true
   }
  }
 ],
 "deduccion_items": [
  {
   "concepto_raw": "DTO. CONT. COMUNES 4,83%",
   "concepto_standardized": "DTO. CONT. COMUNES",
   "tipo": 4.83,
   "importe": 75.21,
   "item_type": {
    "ind_is_especie": false,
    "ind_is_IT_IL": false,
    "ind_is_anticipo": false,
    "ind_is_embargo": false,
    "ind_tributa_IRPF": false,
    "ind_cotiza_ss": false
   }
  },
  {
   "concepto_raw": "DTO. BASE ACCIDENTE 1,65%",
   "concepto_standardized": "DTO. BASE ACCIDENTE",
   "tipo": 1.65,
   "importe": 25.69,
   "item_type": {
    "ind_is_especie": false,
    "ind_is_IT_IL": false,
    "ind_is_anticipo": false,
    "ind_is_embargo": false,
    "ind_tributa_IRPF": false,
    "ind_cotiza_ss": false
   }
  },
  {
   "concepto_raw": "RETENCION IRPF 2,89%",
   "concepto_standardized": "RETENCION IRPF",
   "tipo": 2.89,
   "importe": 31.89,
   "item_type": {
    "ind_is_especie": false,
    "ind_is_IT_IL": false,
    "ind_is_anticipo": false,
    "ind_is_embargo": false,
    "ind_tributa_IRPF": false,
    "ind_cotiza_ss": false
   }
  }
 ],
 "aportacion_empresa_items": [
  {
   "concepto_raw": "CONT. COMUNES + PP EXTRAS",
   "concepto_standardized": "TOTAL CONTINGENCIAS COMUNES + PRORRATA PAGAS EXTRAS",
   "base": 1557.19,
   "tipo": 24.27,
   "importe": 377.92
  },
  {
   "concepto_raw": "AT Y EP",
   "concepto_standardized": "AT Y EP",
   "base": 1557.19,
   "tipo": 3.70,
   "importe": 57.63
  },
  {
   "concepto_raw": "DESEMPLEO",
   "concepto_standardized": "DESEMPLEO",
   "base": 1557.19,
   "tipo": 5.50,
   "importe": 85.65
  },
  {
   "concepto_raw": "FORMACIÓN PROFESIONAL",
   "concepto_standardized": "FORMACIÓN PROFESIONAL",
   "base": 1557.19,
   "tipo": 0.60,
   "importe": 9.34
  },
  {
   "concepto_raw": "FOGASA",
   "concepto_standardized": "FONDO GARANTÍA SALARIAL",
   "base": 1557.19,
   "tipo": 0.20,
   "importe": 3.12
  }
 ],
 "totales": {
  "devengo_total": 1103.43,
  "deduccion_total": 132.79,
  "liquido_a_percibir": 970.64,
  "aportacion_empresa_total": 533.66,
  "prorrata_pagas_extra_total": 155.70,
  "base_contingencias_comunes_total": 1557.19,
  "base_accidente_de_trabajo_y_desempleo_total": 1557.19,
  "base_retencion_irpf_total": 1103.43,
  "porcentaje_retencion_irpf": 2.89,
  "contains_settlement": false
 },
 "fecha_documento": "2025-05-31",
 "warnings": [
  "Standardized the format of the Social Security Affiliation Number.",
  "The value 'aportacion_empresa_total' was not found and has been calculated by summing its components."
 ]
}
```
"""

payslip_bible_cotizations_prompt_yaml = """
### **OFFICIAL CONCEPT REFERENCE (YAML)**
Use this structured reference as the absolute source of truth for classifying items. 

concepts:
  fixed_salary:
    - { name: "SALARIO BASE", type: "Totales", cotiza_ss: true, tributa_irpf: true, is_especie: false }
    - { name: "BOLSA DE ESTUDIOS", type: "Totales", cotiza_ss: true, tributa_irpf: true, is_especie: false }
    - { name: "MEJORA VOLUNTARIA", type: "Totales", cotiza_ss: true, tributa_irpf: true, is_especie: false }
    - { name: "RETR ADMINISTRADOR", type: "Totales", cotiza_ss: true, tributa_irpf: true, is_especie: false }
    - { name: "AJUSTE SMI", type: "Totales", cotiza_ss: true, tributa_irpf: true, is_especie: false }
    - { name: "PLUS COMPENSABLE/ABSORBIBLE", type: "Totales", cotiza_ss: true, tributa_irpf: true, is_especie: false }
    - { name: "EXCLUSIVIDAD", type: "Totales", cotiza_ss: true, tributa_irpf: true, is_especie: false }
    - { name: "NON-COMPETE", type: "Totales", cotiza_ss: true, tributa_irpf: true, is_especie: false }

  bonuses_and_incentives:
    - { name: "INCENTIVOS", type: "Totales", cotiza_ss: true, tributa_irpf: true, is_especie: false }
    - { name: "BONUS", type: "Totales", cotiza_ss: true, tributa_irpf: true, is_especie: false }
    - { name: "BONUS (NETO)", type: "Totales", cotiza_ss: true, tributa_irpf: true, is_especie: false }
    - { name: "BONUS NETO", type: "Totales", cotiza_ss: false, tributa_irpf: false, is_especie: false }
    - { name: "PLUS IMPLICACIÓN", type: "Totales", cotiza_ss: true, tributa_irpf: true, is_especie: false }
    - { name: "PLUS RESEÑAS", type: "Totales", cotiza_ss: true, tributa_irpf: true, is_especie: false }
    - { name: "PLUS HERRAMIENTAS DE TRABAJO", type: "Totales", cotiza_ss: true, tributa_irpf: true, is_especie: false }
    - { name: "PRIMAS", type: "Totales", cotiza_ss: true, tributa_irpf: true, is_especie: false }
    - { name: "SIGN-IN BONUS", type: "Totales", cotiza_ss: true, tributa_irpf: true, is_especie: false }

  extra_pay_and_shifts:
    - { name: "GRATIFICACION - PEXTRAS", type: "Totales", cotiza_ss: true, tributa_irpf: true, is_especie: false }
    - { name: "PAGA EXTRA PRORRATEADA", type: "Totales", cotiza_ss: true, tributa_irpf: true, is_especie: false }
    - { name: "HORAS NOCTURNAS", type: "Unidades", cotiza_ss: true, tributa_irpf: true, is_especie: false }
    - { name: "FESTIVOS TRABAJADOS", type: "Unidades", cotiza_ss: true, tributa_irpf: true, is_especie: false }
    - { name: "HORAS COMPLEMENTARIAS", type: "Unidades", cotiza_ss: true, tributa_irpf: true, is_especie: false }
    - { name: "HORAS EXTRAS", type: "Unidades", cotiza_ss: true, tributa_irpf: true, is_especie: false }
    - { name: "ACTIVIDAD (H. EXTRAS)", type: "Unidades", cotiza_ss: true, tributa_irpf: true, is_especie: false }
    - { name: "PLUS PELIGROSIDAD", type: "Totales", cotiza_ss: true, tributa_irpf: true, is_especie: false }

  benefits_and_in_kind:
    - { name: "AUTONOMOS", type: "Totales", cotiza_ss: false, tributa_irpf: true, is_especie: true }
    - { name: "PLUS ROPA", type: "Unidades", cotiza_ss: true, tributa_irpf: true, is_especie: false }
    - { name: "PLUS ROPA (ESPECIE)", type: "Unidades", cotiza_ss: true, tributa_irpf: true, is_especie: true }
    - { name: "MANUTENCIÓN (ESPECIE)", type: "Unidades", cotiza_ss: true, tributa_irpf: true, is_especie: true }
    - { name: "MANUTENCIÓN (DINERARIO)", type: "Unidades", cotiza_ss: true, tributa_irpf: true, is_especie: false }
    - { name: "SEGURO MEDICO TRABAJADOR", type: "Totales", cotiza_ss: true, tributa_irpf: false, is_especie: true }
    - { name: "SEGURO MEDICO EXENTO", type: "Totales", cotiza_ss: false, tributa_irpf: false, is_especie: true }
    - { name: "SEGURO ACCIDENTES", type: "Totales", cotiza_ss: false, tributa_irpf: false, is_especie: true }

  expenses_and_travel:
    - { name: "DIETAS (SIN PERNOCTA) - VIAJE", type: "Totales", cotiza_ss: false, tributa_irpf: false, is_especie: false }
    - { name: "DIETAS (CON PERNOCTA) - VIAJE", type: "Totales", cotiza_ss: false, tributa_irpf: false, is_especie: false }
    - { name: "PLUS TRANSPORTE", type: "Totales", cotiza_ss: true, tributa_irpf: true, is_especie: false }
    - { name: "KILOMETRAJE", type: "Totales", cotiza_ss: false, tributa_irpf: false, is_especie: false }
    - { name: "GASTOS LOCOMOCIÓN", type: "Totales", cotiza_ss: false, tributa_irpf: false, is_especie: false }

  adjustments_and_settlements:
    - { name: "VACACIONES MANUAL", type: "Unidades", cotiza_ss: true, tributa_irpf: true, is_especie: false }
    - { name: "*PARTE PROPORCIONAL VACACIONES FINIQUITO", type: "Unidades", cotiza_ss: true, tributa_irpf: true, is_especie: false }
    - { name: "AJUSTE VACACIONES DISFRUTADAS", type: "Totales", cotiza_ss: false, tributa_irpf: false, is_especie: false }
    - { name: "AJUSTE ERROR VACACIONES - DESCUENTO", type: "Totales", cotiza_ss: false, tributa_irpf: false, is_especie: false }
    - { name: "AJUSTE ERROR VACACIONES - COBRO", type: "Totales", cotiza_ss: false, tributa_irpf: true, is_especie: false }
    - { name: "VACACIONES DISFRUTADAS NO GENERADAS", type: "Totales", cotiza_ss: true, tributa_irpf: true, is_especie: false }
    - { name: "AJUSTE - DESCUENTO ERROR PREVIO", type: "Totales", cotiza_ss: true, tributa_irpf: true, is_especie: false }
    - { name: "AJUSTE - DESCUENTO ERROR HORAS", type: "Totales", cotiza_ss: true, tributa_irpf: true, is_especie: false }
    - { name: "AJUSTE POSITIVO", type: "Totales", cotiza_ss: true, tributa_irpf: true, is_especie: false }
    - { name: "ABSENTISMO", type: "Unidades (Horas)", cotiza_ss: true, tributa_irpf: true, is_especie: false }
    - { name: "DESCUENTO NOMINA", type: "Totales", cotiza_ss: true, tributa_irpf: true, is_especie: false }
    - { name: "REGULARIZACION MESES ANTERIORES", type: "Totales", cotiza_ss: true, tributa_irpf: true, is_especie: false }
    - { name: "SUBIDA CONVENIO PENDIENTE", type: "Totales", cotiza_ss: true, tributa_irpf: true, is_especie: false }

  cash_and_others:
    - { name: "EFECTIVO", type: "Totales", cotiza_ss: false, tributa_irpf: false, is_especie: false }
    - { name: "CASHBALANCE", type: "Totales", cotiza_ss: false, tributa_irpf: false, is_especie: false }
    - { name: "DEVOLUCIÓN EFECTIVO", type: "Totales", cotiza_ss: false, tributa_irpf: false, is_especie: false }
    - { name: "PROPINAS - C/IRPF", type: "Totales", cotiza_ss: false, tributa_irpf: true, is_especie: false }
    - { name: "PROPINAS - S/IRPF", type: "Totales", cotiza_ss: false, tributa_irpf: false, is_especie: false }
"""
