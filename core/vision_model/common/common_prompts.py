payslip_bible_cotizations_prompt = """
This is a list of concepts that are commonly found in payslips, and the information about the cotizations, if it's a 'especie' or 'dinerario' and contributions that are applied to them:

Concept;Tipo;Cotiza Seg. Social;Tributa IRPF;Is Especie?
---
Salario base;Totales;TRUE;TRUE;FALSE
Bolsa de estudios;Totales;TRUE;TRUE;FALSE
Gratificacion - PExtras;Totales;TRUE;TRUE;FALSE
Mejora Voluntaria;Totales;TRUE;TRUE;FALSE
Incentivos;Totales;TRUE;TRUE;FALSE
Bonus;Totales;TRUE;TRUE;FALSE
Bonus (Neto);Totales;TRUE;TRUE;FALSE
Plus implicación;Totales;TRUE;TRUE;FALSE
Plus Reseñas;Totales;TRUE;TRUE;FALSE
Plus herramientas de trabajo;Totales;TRUE;TRUE;FALSE
Bonus neto;Totales;FALSE;FALSE;FALSE
Primas;Totales;TRUE;TRUE;FALSE
Retr Administrador;Totales;TRUE;TRUE;FALSE
Sign-in Bonus;Totales;TRUE;TRUE;FALSE
Autonomos;Totales;FALSE;TRUE;TRUE
Ajuste SMI;Totales;TRUE;TRUE;FALSE
Plus Compensable/Absorbible;Totales;TRUE;TRUE;FALSE
Exclusividad;Totales;TRUE;TRUE;FALSE
Non-compete;Totales;TRUE;TRUE;FALSE
Festivos trabajados;Unidades;TRUE;TRUE;FALSE
Horas nocturnas;Unidades;TRUE;TRUE;FALSE
Plus Ropa;Unidades;TRUE;TRUE;FALSE
Plus Ropa (Especie);Unidades;TRUE;TRUE;TRUE
Manutención (Especie);Unidades;TRUE;TRUE;TRUE
Manutención (Dinerario);Unidades;TRUE;TRUE;FALSE
Dietas (sin pernocta) - Viaje;Totales;FALSE;FALSE;FALSE
Dietas (con pernocta) - Viaje;Totales;FALSE;FALSE;FALSE
Plus Transporte;Totales;TRUE;TRUE;FALSE
Kilometraje;Totales;FALSE;FALSE;FALSE
Gastos locomoción;Totales;FALSE;FALSE;FALSE
Plus peligrosidad;Totales;TRUE;TRUE;FALSE
Ajuste vacaciones disfrutadas;Totales;FALSE;FALSE;FALSE
Ajuste error vacaciones - Descuento;Totales;FALSE;FALSE;FALSE
Ajuste error vacaciones - Cobro;Totales;FALSE;TRUE;FALSE
Vacaciones manual;Unidades;TRUE;TRUE;FALSE
*Parte Proporcional Vacaciones Finiquito ;Unidades;TRUE;TRUE;FALSE
Horas complementarias;Unidades;TRUE;TRUE;FALSE
Horas extras;Unidades;TRUE;TRUE;FALSE
Actividad (H. Extras);Unidades;TRUE;TRUE;FALSE
Absentismo;Unidades (Horas);TRUE;TRUE;FALSE
Efectivo;Totales;FALSE;FALSE;FALSE
CashBalance;Totales;FALSE;FALSE;FALSE
Devolución efectivo;Totales;FALSE;FALSE;FALSE
Descuento nomina;Totales;TRUE;TRUE;FALSE
Vacaciones disfrutadas no generadas;Totales;TRUE;TRUE;FALSE
Ajuste - Descuento error previo;Totales;TRUE;TRUE;FALSE
Ajuste - Descuento error horas;Totales;TRUE;TRUE;FALSE
Ajuste Positivo;Totales;TRUE;TRUE;FALSE
Seguro Medico Trabajador;Toatles;1;-;-;TRUE
Seguro Medico Exento;Totales;-;-;TRUE
Seguro Accidentes;Totales;-;-;TRUE
Paga extra prorrateada;Totales;RUE;TRUE;FALSE
Subida convenio Pendiente;Totales;RUE;TRUE;FALSE
Regularizacion meses anteriores;Totales;RUE;TRUE;FALSE
Regularizacion meses anteriores;Totales;TRUE;TRUE;FALSE
Propinas - C/IRPF;Totales;FALSE;TRUE;FALSE
Propinas - S/IRPF;Totales;FALSE;FALSE;FALSE
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
    "ind_is_exento_IRPF": false,
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
    "ind_is_exento_IRPF": false,
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
    "ind_is_exento_IRPF": false,
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
    "ind_is_exento_IRPF": false,
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
    "ind_is_exento_IRPF": false,
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
    "ind_is_exento_IRPF": false,
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
    "ind_is_exento_IRPF": false,
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
    "ind_is_exento_IRPF": false,
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
    "ind_is_exento_IRPF": false,
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
    "ind_is_exento_IRPF": false,
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
    "ind_is_exento_IRPF": false,
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
  "contains_finiquito": false
 },
 "warnings": [
  "Standardized the format of the worker's name.",
  "Standardized the format of the Social Security Affiliation Number.",
  "The value 'aportacion_empresa_total' was not found and has been calculated by summing its components."
 ]
}
```
"""