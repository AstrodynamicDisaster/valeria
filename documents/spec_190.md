# Modelo 190 – File Generation Spec (Presentación por fichero)

*This spec describes how to generate a fully compliant Modelo 190 file (presentación por fichero) following the AEAT “Diseños de registro Modelo 190 (Ejercicio 2024 – Versión 5 – 18.12.2024)”. *

It’s meant to be consumed by a code model (e.g. Codex). It assumes **all tax/business calculations are already done** and provided by your own endpoints. The generator only:

* Validates structure and compatibility.
* Formats data into the AEAT fixed‑length text format.
* Computes and fills header totals.

---

## 1. Scope and Assumptions

* **Model**: 190 – Declaración informativa. Resumen anual.
* **Exercise**: Layout for **Ejercicio 2024** (file filed in 2025).
* **Data source**:

  * Endpoint 1 returns the declarant + list of perceptors (employees, professionals, etc.) for the year.
  * Endpoint 2 (internally) can provide all aggregates required to build each perceptor record.
* **Out of scope**: deciding claves/subclaves, computing IRPF, classifying payments. Those are done upstream.

---

## 2. File Characteristics

From AEAT diseño general. 

* **Record length**: exactly **500 characters** per line.
* **Encoding**: `ISO‑8859‑1`.
* **Record types**:

  * `1` – Declarant header (exactly 1).
  * `2` – Perceptor record (1..N).
* **Ordering**:

  * First **type 1** record.
  * Then **all type 2** records in any deterministic order (e.g. NIF + clave + subclave).
* **Line terminator**: `\r\n` (CRLF).
* **Alignment & padding**: 

  * Numeric fields: right‑aligned, left‑padded with **zeros**, **no sign**, **no separators**.
  * Alphanumeric/alphabetic fields: left‑aligned, right‑padded with **spaces**, **uppercase**, **no accents / special chars**.
  * Empty numeric ⇒ all zeros; empty alpha ⇒ all spaces.

---

## 3. Input Data Contract

The generator operates on **pure data structures**; no database or business logic inside.

### 3.1. Declarant object

```ts
type Declarant190 = {
  ejercicio: number;                 // e.g. 2024
  modelo: "190";                     // constant
  nif: string;                       // NIF del declarante
  nombre_razon_social: string;       // already uppercase if possible
  contacto_telefono?: string;        // 9 digits
  contacto_nombre?: string;          // "APELLIDO1 APELLIDO2 NOMBRE"
  email_contacto?: string;

  // Filing metadata
  numero_identificativo?: string;    // AEAT 13-digit ID, or undefined/empty for first filing
  tipo_declaracion: "N" | "C" | "S"; // internal convention: N=normal, C=complementaria, S=sustitutiva
  id_declaracion_anterior?: string;  // 13-digit ID if C/S, otherwise empty

  // Perceptors for this declarante
  percepciones: PerceptorRecordInput[];
};
```

### 3.2. Perceptor object

Each **type‑2 record** will be built from one `PerceptorRecordInput`.

> If the same person has different claves/subclaves/contracts/devengos, upstream must produce **multiple** `PerceptorRecordInput` objects.

```ts
type AdditionalData = {
  anio_nacimiento?: number;
  situacion_familiar?: 1 | 2 | 3;
  nif_conyuge?: string;
  discapacidad?: 0 | 1 | 2 | 3;

  contrato_relacion?: 1 | 2 | 3 | 4;  // only clave A
  movilidad_geografica?: boolean;     // only clave A

  reducciones_aplicables?: number;    // euros
  gastos_deducibles?: number;         // euros

  pension_compensatoria?: number;     // euros
  anualidades_alimentos?: number;     // euros

  hijos_descendientes?: {
    menores_3_total?: number;
    menores_3_entero?: number;
    resto_total?: number;
    resto_entero?: number;
  };

  hijos_discapacidad?: {
    g33_65_total?: number;
    g33_65_entero?: number;
    mov_red_total?: number;
    mov_red_entero?: number;
    g65_total?: number;
    g65_entero?: number;
  };

  ascendientes?: {
    lt75_total?: number;
    lt75_entero?: number;
    gte75_total?: number;
    gte75_entero?: number;
  };

  ascendientes_discapacidad?: {
    g33_65_total?: number;
    g33_65_entero?: number;
    mov_red_total?: number;
    mov_red_entero?: number;
    g65_total?: number;
    g65_entero?: number;
  };

  computo_tres_primeros_hijos?: (0 | 1 | 2)[]; // [hijo1, hijo2, hijo3] – 1=entero, 2=mitad
  comunicacion_prestamo_vivienda?: boolean;

  // L.29 / IMV
  titular_unidad_convivencia?: 1 | 2;
};

type IngresoDinerario = {
  sign?: "N";                  // "N" only for reintegro of previous years
  base: number;                // euros
  retencion?: number;          // euros
};

type IngresoEspecie = {
  sign?: "N";
  base: number;                    // euros, valoración sin ingreso a cuenta
  ingreso_cuenta_efectuado?: number;   // euros
  ingreso_cuenta_repercutido?: number; // euros
};

type Incapacidad = {
  dineraria?: IngresoDinerario;    // only claves A and B.01
  especie?: IngresoEspecie;       // only clave A
};

type ForalSplit = {
  hacienda_estatal?: number;      // euros
  navarra?: number;               // euros
  araba?: number;                 // euros
  gipuzkoa?: number;              // euros
  bizkaia?: number;               // euros
};

type PerceptorRecordInput = {
  nif_perceptor: string;
  nif_representante?: string;
  nombre_perceptor: string;        // "APELLIDO1 APELLIDO2 NOMBRE"
  provincia: string;               // "01".."53" or "98"

  clave: string;                   // "A".."L"
  subclave?: string | null;        // two digits when required

  ejercicio_devengo?: number;      // four digits, 0/undefined if not atrasos/reintegros
  ceuta_melilla_flag?: 0 | 1 | 2;  // 0,1,2 per diseño

  dinerario_no_incapacidad?: IngresoDinerario;
  especie_no_incapacidad?: IngresoEspecie;

  incapacidad?: Incapacidad;       // dineraria+especie IL

  complemento_ayuda_infancia?: 1 | 2;   // only L.29
  excesos_acciones_emergentes?: 0 | 1;  // field 388

  foral_split?: ForalSplit;             // only clave E

  datos_adicionales?: AdditionalData;
};
```

Upstream guarantees:

* Correct **clave/subclave** and IL splitting.
* Amounts already aggregated at the granularity of each type‑2 record.

The generator must **not** change amounts, only format.

---

## 4. Formatting Helpers (Language‑agnostic)

You should implement these primitive helpers in your language of choice.

### 4.1. Text normalization

* Convert to **uppercase**.
* Strip/replace accented characters and other non‑ASCII except Ñ/Ç per AEAT. 
* Remove characters outside `[A-Z0-9 ]` (or map them reasonably).

**Spec:**

```pseudo
normalize_text(s: string) -> string
  if s is null: s = ""
  s = s.upper()
  replace "ÁÉÍÓÚÀÈÌÒÙÂÊÎÔÛÄËÏÖÜ" -> "AEIOUAEIOUAEIOUAEIOU"
  replace "Ñ"->"Ñ", "Ç"->"Ç"
  drop any other non ISO-8859-1 letters that AEAT may reject
  collapse tabs/newlines into spaces
  return s
```

### 4.2. Alpha field formatter

```pseudo
fmt_alpha(value: string | null, length: int) -> string
  v = normalize_text(value or "")
  v = v.slice(0, length)
  return v + " " * (length - len(v))   // left aligned
```

### 4.3. Numeric field formatter

```pseudo
fmt_numeric_int(value: int | null, length: int) -> string
  if value is null: value = 0
  if value < 0: ERROR  // unless explicitly allowed as sign+abs
  s = str(value)
  if len(s) > length: ERROR
  return "0"*(length - len(s)) + s
```

### 4.4. Monetary amount (euros with 2 decimals)

```pseudo
fmt_amount_euros(value: float | int | null,
                 int_len: int, dec_len: int = 2) -> (string, string)
  if value is null:
    return ( "0"*int_len, "0"*dec_len )

  cents = round(value * 100)
  if cents < 0: ERROR  // negative only handled via separate sign fields
  integer = cents // 100
  decimals = cents % 100

  return (fmt_numeric_int(integer, int_len),
          fmt_numeric_int(decimals, dec_len))
```

### 4.5. Sign field

```pseudo
fmt_sign(is_negative: bool) -> string
  return "N" if is_negative else " "
```

Sign fields are used **only** for reintegros from previous years (fields 81, 108, 255, 282). 

---

## 5. Type‑1 Record (Declarant Header)

Per diseño de registro tipo 1. 

### 5.1. Layout

| Pos     | Len | Type | Field name                                  | Source / logic                                                                           |
| ------- | --- | ---- | ------------------------------------------- | ---------------------------------------------------------------------------------------- |
| 1       | 1   | N    | `TIPO_REGISTRO`                             | Constant `"1"`.                                                                          |
| 2–4     | 3   | N    | `MODELO`                                    | `"190"`.                                                                                 |
| 5–8     | 4   | N    | `EJERCICIO`                                 | `Declarant190.ejercicio`.                                                                |
| 9–17    | 9   | A/N  | `NIF_DECLARANTE`                            | NIF right‑aligned, zero‑padded; control letter on last position.                         |
| 18–57   | 40  | A    | `NOMBRE_RAZON_SOCIAL`                       | `fmt_alpha(nombre_razon_social, 40)`.                                                    |
| 58      | 1   | A    | `TIPO_SOPORTE`                              | `"T"` telemática.                                                                        |
| 59–67   | 9   | N    | `TELEFONO_CONTACTO`                         | Digits only, `fmt_numeric_int`.                                                          |
| 68–107  | 40  | A    | `CONTACTO_APELLIDOS_NOMBRE`                 | `fmt_alpha(contacto_nombre, 40)`.                                                        |
| 108–120 | 13  | N    | `NUMERO_IDENTIFICATIVO_DECLARACION`         | AEAT ID if known; else 13 zeros.                                                         |
| 121     | 1   | A    | `DECLARACION_COMPLEMENTARIA`                | `"C"` if tipo_declaracion = C, else space.                                               |
| 122     | 1   | A    | `DECLARACION_SUSTITUTIVA`                   | `"S"` if tipo_declaracion = S, else space.                                               |
| 123–135 | 13  | N    | `NUMERO_IDENTIFICATIVO_ANTERIOR`            | If C/S, previous declaration ID; else 13 zeros.                                          |
| 136–144 | 9   | N    | `NUMERO_TOTAL_PERCEPCIONES`                 | Count of type‑2 records.                                                                 |
| 145     | 1   | A    | `SIGNO_IMPORTE_TOTAL_PERCEPCIONES`          | `"N"` if total perceptions < 0; else space.                                              |
| 146–158 | 13  | N    | `IMPORTE_TOTAL_PERCEPCIONES_ENTERO`         | Integer part of absolute total perceptions.                                              |
| 159–160 | 2   | N    | `IMPORTE_TOTAL_PERCEPCIONES_DEC`            | Cents.                                                                                   |
| 161–173 | 13  | N    | `IMPORTE_TOTAL_RETENCIONES_INGRESOS_ENTERO` | Integer part of sum of retenciones + ingresos a cuenta.                                  |
| 174–175 | 2   | N    | `IMPORTE_TOTAL_RETENCIONES_INGRESOS_DEC`    | Cents.                                                                                   |
| 176–225 | 50  | A    | `EMAIL_CONTACTO`                            | `fmt_alpha(email_contacto, 50)` (AEAT allows email chars but spec tolerates uppercase).  |
| 226–487 | 262 | A    | BLANKS                                      | Spaces.                                                                                  |
| 488–500 | 13  | A    | `SELLO_ELECTRONICO`                         | Spaces (AEAT fills).                                                                     |

### 5.2. Header totals logic

Using **PerceptorRecordInput** values (not the formatted strings):

```pseudo
compute_totals(perceptors: PerceptorRecordInput[]) -> (total_percepciones_eur: float,
                                                       total_ret_e_ing_eur: float):

  total_percepciones = 0.0
  total_ret_ing = 0.0

  for p in perceptors:
    # Dinerario normal
    if p.dinerario_no_incapacidad:
      s = -1 if p.dinerario_no_incapacidad.sign == "N" else 1
      total_percepciones += s * (p.dinerario_no_incapacidad.base or 0)
      total_ret_ing += (p.dinerario_no_incapacidad.retencion or 0)

    # Especie normal
    if p.especie_no_incapacidad:
      s = -1 if p.especie_no_incapacidad.sign == "N" else 1
      total_percepciones += s * (p.especie_no_incapacidad.base or 0)
      total_ret_ing += (p.especie_no_incapacidad.ingreso_cuenta_efectuado or 0)

    # IL dineraria
    if p.incapacidad and p.incapacidad.dineraria:
      s = -1 if p.incapacidad.dineraria.sign == "N" else 1
      total_percepciones += s * (p.incapacidad.dineraria.base or 0)
      total_ret_ing += (p.incapacidad.dineraria.retencion or 0)

    # IL especie
    if p.incapacidad and p.incapacidad.especie:
      s = -1 if p.incapacidad.especie.sign == "N" else 1
      total_percepciones += s * (p.incapacidad.especie.base or 0)
      total_ret_ing += (p.incapacidad.especie.ingreso_cuenta_efectuado or 0)

  return (total_percepciones, total_ret_ing)
```

* `total_percepciones` may be negative if reintegros > normal amounts; header uses **sign + abs(value)**.
* `total_ret_ing` is always ≥ 0 (reintegros go with 0 retention). 

Header building (simplified):

```pseudo
build_type1(decl: Declarant190, perceptors: PerceptorRecordInput[]) -> string
  buf = 500 spaces
  put(pos_from, pos_to, value)  // helper

  # constants & IDs ...
  # then:

  n_percep = len(perceptors)
  put(136,144, fmt_numeric_int(n_percep, 9))

  (tot_per, tot_ret) = compute_totals(perceptors)
  sign = "N" if tot_per < 0 else " "
  abs_per = abs(tot_per)

  (per_ent, per_dec) = fmt_amount_euros(abs_per, 13)
  put(145,145, sign)
  put(146,158, per_ent)
  put(159,160, per_dec)

  (ret_ent, ret_dec) = fmt_amount_euros(tot_ret, 13)
  put(161,173, ret_ent)
  put(174,175, ret_dec)

  # rest as per layout
  return joined(buf)
```

---

## 6. Type‑2 Record (Perceptor)

Per diseño de registro tipo 2. 

You generate one type‑2 record per `PerceptorRecordInput`.

### 6.1. Identification block (positions 1–80)

| Pos   | Len | Type | Field                        | Mapping                                               |
| ----- | --- | ---- | ---------------------------- | ----------------------------------------------------- |
| 1     | 1   | N    | `TIPO_REGISTRO`              | `"2"`.                                                |
| 2–4   | 3   | N    | `MODELO`                     | `"190"`.                                              |
| 5–8   | 4   | N    | `EJERCICIO`                  | Same as header.                                       |
| 9–17  | 9   | A/N  | `NIF_DECLARANTE`             | From `Declarant190.nif`.                              |
| 18–26 | 9   | A/N  | `NIF_PERCEPTOR`              | `fmt_numeric_int_nif(p.nif_perceptor)`.               |
| 27–35 | 9   | A/N  | `NIF_REPRESENTANTE`          | If `<14` or special, formatted NIF; else spaces.      |
| 36–75 | 40  | A    | `APELLIDOS_NOMBRE_PERCEPTOR` | `fmt_alpha(nombre_perceptor,40)`.                     |
| 76–77 | 2   | N    | `CODIGO_PROVINCIA`           | From `provincia`.                                     |
| 78    | 1   | A    | `CLAVE_PERCEPCION`           | `p.clave`.                                            |
| 79–80 | 2   | N    | `SUBCLAVE`                   | For claves B,C,E,F,G,H,I,K,L mandatory; else spaces.  |

### 6.2. Monetary – non‑IL dinerario (81–107) 

From `p.dinerario_no_incapacidad`.

| Pos     | Len | Field                   | Spec                                                         |
| ------- | --- | ----------------------- | ------------------------------------------------------------ |
| 81      | 1   | `SIGNO_PERCEP_INTEGRA`  | `"N"` if reintegration of previous‑year amounts; else space. |
| 82–92   | 11  | `PERCEP_INTEGRA_ENTERA` | Integer part of base.                                        |
| 93–94   | 2   | `PERCEP_INTEGRA_DEC`    | Cents.                                                       |
| 95–105  | 11  | `RETENCIONES_ENTERAS`   | Integer part of IRPF retained.                               |
| 106–107 | 2   | `RETENCIONES_DEC`       | Cents.                                                       |

Rules:

* If no base and no retention: field 81 blank, rest zeros.
* If sign `"N"` then base > 0 and retention must be **0** (reintegro).

### 6.3. Monetary – non‑IL in kind (108–147) 

From `p.especie_no_incapacidad`.

| Pos     | Len | Field                      |
| ------- | --- | -------------------------- |
| 108     | 1   | `SIGNO_ESPECIE`            |
| 109–119 | 11  | `VALORACION_ENTERA`        |
| 120–121 | 2   | `VALORACION_DEC`           |
| 122–132 | 11  | `INGRESOS_CTA_ENTEROS`     |
| 133–134 | 2   | `INGRESOS_CTA_DEC`         |
| 135–145 | 11  | `INGRESOS_CTA_REP_ENTEROS` |
| 146–147 | 2   | `INGRESOS_CTA_REP_DEC`     |

Mapping as for dinerario; all zero if no in‑kind.

### 6.4. Ejercicio devengo & Ceuta/La Palma (148–152)

* **148–151** – `EJERCICIO_DEVENGO`: 4 digits; non‑zero only for **atrasos** or **reintegros** from previous years. 
* **152** – `CEUTA_MELILLA`:

  * `1` – Ceuta/Melilla with special deduction.
  * `2` – Isla de La Palma deduction.
  * `0` – otherwise. 

### 6.5. Datos adicionales (153–254)

Follow the table in the AEAT document. 

Implementation guideline:

* Have a `build_datos_adicionales(buf, p.datos_adicionales, p.clave, p.subclave)` function that:

  * Fills all positions 153–254 with zeros/spaces by default.
  * Writes values only where applicable for that clave/subclave (A, B.01, B.03, C, E.xx, F.01–06, G.01–06,08, H, I, L.05, L.10, L.27, L.29).
* All multi‑component blocks (children, ascendientes, disability etc.) follow the exact micro‑layout in the PDF (see pages 32–43). 

### 6.6. IL dineraria (255–281) 

From `p.incapacidad.dineraria` (only claves **A** and **B.01**):

| Pos     | Len | Field              |
| ------- | --- | ------------------ |
| 255     | 1   | `SIGNO_PERCEP_IL`  |
| 256–266 | 11  | `PERCEP_IL_ENTERA` |
| 267–268 | 2   | `PERCEP_IL_DEC`    |
| 269–279 | 11  | `RET_IL_ENTERAS`   |
| 280–281 | 2   | `RET_IL_DEC`       |

If no IL dineraria: 255 blank, rest zeros.

### 6.7. IL in kind (282–321) 

From `p.incapacidad.especie` (only clave **A**):

| Pos     | Len | Field                                 |
| ------- | --- | ------------------------------------- |
| 282     | 1   | `SIGNO_ESPECIE_IL`                    |
| 283–293 | 11  | `VALORACION_ESPECIE_IL_ENTERA`        |
| 294–295 | 2   | `VALORACION_ESPECIE_IL_DEC`           |
| 296–306 | 11  | `INGRESOS_CTA_ESPECIE_IL_ENTEROS`     |
| 307–308 | 2   | `INGRESOS_CTA_ESPECIE_IL_DEC`         |
| 309–319 | 11  | `INGRESOS_CTA_ESPECIE_IL_REP_ENTEROS` |
| 320–321 | 2   | `INGRESOS_CTA_ESPECIE_IL_REP_DEC`     |

### 6.8. IMV complement and foral split (322–387) 

* **322** – `COMPLEMENTO_AYUDA_INFANCIA` (only L.29):

  * `1` – if IMV includes child support complement.
  * `2` – otherwise.

* **323–387** – for **clave E** only (administradores):

  Split total retenciones+ingresos by tax administration:

  * 323–335 – Estado (13 digits).
  * 336–348 – Navarra.
  * 349–361 – Araba/Álava.
  * 362–374 – Gipuzkoa.
  * 375–387 – Bizkaia.

  Sum of these five must equal `RETENCIONES + INGRESOS_CTA` of the same record (95–107 + 122–134).

### 6.9. Acciones empresas emergentes & tail (388–500) 

* **388** – `EXCESOS_ACCIONES_EMERGENTES` (only clave A):

  * `1` – if the in‑kind income (108–147) includes startup shares exceeding the exemption.
  * `0` – otherwise.
* **389–500** – blanks.

---

## 7. Record‑building Functions (Pseudocode)

### 7.1. Type‑2 record

```pseudo
build_type2_record(decl: Declarant190, p: PerceptorRecordInput) -> string:
  buf = array[500] filled with " "

  def put(from_pos, to_pos, s):
    assert len(s) == (to_pos - from_pos + 1)
    buf[from_pos-1 : to_pos] = s

  # 1–80 identification
  put(1,1,"2")
  put(2,4,"190")
  put(5,8, fmt_numeric_int(decl.ejercicio,4))
  put(9,17, fmt_nif(decl.nif))
  put(18,26, fmt_nif(p.nif_perceptor))
  put(27,35, fmt_nif_or_spaces(p.nif_representante))
  put(36,75, fmt_alpha(p.nombre_perceptor,40))
  put(76,77, fmt_numeric_int(int(p.provincia),2))
  put(78,78, p.clave)
  if p.clave in {"B","C","E","F","G","H","I","K","L"}:
    put(79,80, fmt_numeric_int(int(p.subclave or 0),2))
  else:
    put(79,80, "  ")

  # 81–107 dinerario normal
  dn = p.dinerario_no_incapacidad
  if dn and dn.base:
    sign = fmt_sign(dn.sign == "N")
    (ent, dec)   = fmt_amount_euros(dn.base, 11)
    (rent,rdec) = fmt_amount_euros(dn.retencion or 0, 11)
  else:
    sign = " "; ent="0"*11; dec="00"; rent="0"*11; rdec="00"
  put(81,81, sign)
  put(82,92, ent); put(93,94, dec)
  put(95,105, rent); put(106,107, rdec)

  # 108–147 especie normal
  es = p.especie_no_incapacidad
  if es and es.base:
    sign = fmt_sign(es.sign == "N")
    (ent,dec) = fmt_amount_euros(es.base, 11)
    (ing_ent, ing_dec) = fmt_amount_euros(es.ingreso_cuenta_efectuado or 0,11)
    (rep_ent, rep_dec) = fmt_amount_euros(es.ingreso_cuenta_repercutido or 0,11)
  else:
    sign=" "; ent="0"*11; dec="00"
    ing_ent="0"*11; ing_dec="00"
    rep_ent="0"*11; rep_dec="00"
  put(108,108,sign)
  put(109,119,ent); put(120,121,dec)
  put(122,132,ing_ent); put(133,134,ing_dec)
  put(135,145,rep_ent); put(146,147,rep_dec)

  # 148–151 ejercicio devengo
  put(148,151, fmt_numeric_int(p.ejercicio_devengo or 0,4))

  # 152 Ceuta/La Palma
  put(152,152, str(p.ceuta_melilla_flag or 0))

  # 153–254 datos adicionales
  build_datos_adicionales(buf, p)

  # 255–281 IL dineraria
  build_incapacidad_dineraria(buf, p)

  # 282–321 IL especie
  build_incapacidad_especie(buf, p)

  # 322 complemento IMV
  put(322,322, str(p.complemento_ayuda_infancia or 0))

  # 323–387 foral split (only clave E)
  build_foral_split(buf, p)

  # 388 exceso acciones emergentes
  put(388,388, str(p.excesos_acciones_emergentes or 0))

  # 389–500 already spaces
  return join(buf)
```

Each `build_*` helper fills its respective range with zeros/spaces when not applicable.

### 7.2. Type‑1 header and top‑level generator

```pseudo
build_type1_record(decl: Declarant190,
                   perceptors: PerceptorRecordInput[]) -> string:

  buf = 500 spaces
  put = ...

  # 1–8
  put(1,1,"1")
  put(2,4,"190")
  put(5,8, fmt_numeric_int(decl.ejercicio,4))

  # 9–57
  put(9,17, fmt_nif(decl.nif))
  put(18,57, fmt_alpha(decl.nombre_razon_social,40))

  # 58–107
  put(58,58,"T")
  put(59,67, fmt_numeric_int(int(decl.contacto_telefono or 0),9))
  put(68,107, fmt_alpha(decl.contacto_nombre or "",40))

  # 108–135 identificativos
  put(108,120, fmt_numeric_int(int(decl.numero_identificativo or 0),13))
  if decl.tipo_declaracion == "C":
    put(121,121,"C"); put(122,122," ")
  elif decl.tipo_declaracion == "S":
    put(121,121," "); put(122,122,"S")
  else:
    put(121,121," "); put(122,122," ")
  put(123,135, fmt_numeric_int(int(decl.id_declaracion_anterior or 0),13))

  # Totals
  n = len(perceptors)
  put(136,144, fmt_numeric_int(n,9))

  (tot_per, tot_ret) = compute_totals(perceptors)
  sign = "N" if tot_per < 0 else " "
  abs_per = abs(tot_per)
  (per_ent, per_dec) = fmt_amount_euros(abs_per,13)
  put(145,145,sign)
  put(146,158,per_ent)
  put(159,160,per_dec)

  (ret_ent, ret_dec) = fmt_amount_euros(tot_ret,13)
  put(161,173,ret_ent)
  put(174,175,ret_dec)

  put(176,225, fmt_alpha(decl.email_contacto or "",50))

  # 226–500 remain spaces
  return join(buf)


generate_190_file(decl: Declarant190) -> bytes:
  perceptor_inputs = decl.percepciones
  type2_records = [build_type2_record(decl,p) for p in perceptor_inputs]
  header = build_type1_record(decl, perceptor_inputs)

  file_text = header + "\r\n" + "\r\n".join(type2_records) + "\r\n"
  return encode_iso_8859_1(file_text)
```

---

## 8. Validation Rules

The generator should enforce these **before** producing the file:

1. **Structural**

   * Each record **must** be 500 chars.
   * No field may overflow its length.
   * At least **1** type‑2 record.

2. **Clave/subclave**

   * If `clave ∈ {B,C,E,F,G,H,I,K,L}` ⇒ `subclave` not empty.
   * If `clave` outside that set ⇒ `subclave` must be spaces.

3. **Incapacidad**

   * If IL fields present:

     * `clave` must be `A` or (`B` and `subclave == "01"`), as per diseño. 

4. **Foral split (clave E)**

   * If any `foral_split` amount > 0:

     * Sum(forales) == dinerario.retencion + especie.ingreso_cuenta_efectuado (rounded to cents).

5. **Signs**

   * If any sign field = `"N"`:

     * Corresponding base > 0.
     * Retención/ingresos on that component are 0.
   * Header: sign `"N"` only if total perceptions < 0.

6. **Amounts**

   * All component monetary values (base, retención, ingresos a cuenta) ≥ 0.
   * After converting to cents, integer part fits allocated digits.

7. **Consistency**

   * For each record, at least one of: dinerario normal, especie normal, IL dineraria, IL especie, or (if clave L/exempt) an exempt amount upstream (if you choose to encode via bases) must be non‑zero; otherwise reject as empty.

---

## 9. How Codex Should Use This Spec

Given this `.md` as context, Codex should:

1. Implement the helper functions (`normalize_text`, `fmt_alpha`, `fmt_numeric_int`, `fmt_amount_euros`, `fmt_sign`, `fmt_nif`, etc.).
2. Implement:

   * `build_datos_adicionales`
   * `build_incapacidad_dineraria`
   * `build_incapacidad_especie`
   * `build_foral_split`
     strictly following the position ranges and semantics in section **6** and the AEAT PDF.
3. Implement `build_type2_record`, `build_type1_record`, `compute_totals`, `generate_190_file`.
4. Wrap it all in a module/class that:

   * Accepts a `Declarant190` instance (populated from your endpoints).
   * Emits a `bytes` or `str` suitable for upload to AEAT.

You can paste this markdown as‑is into a file like `modelo190_spec.md` and feed it to Codex alongside your target language file.
