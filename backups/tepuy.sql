--
-- PostgreSQL database dump
--

\restrict qafPVpfZ0ZYawMcyUUFVybWG8l8JoSv9pW6vHBn7Zcwyn3ZXuquQXqmyln0LtvR

-- Dumped from database version 16.11
-- Dumped by pg_dump version 16.11 (Homebrew)

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

ALTER TABLE IF EXISTS ONLY public.payrolls DROP CONSTRAINT IF EXISTS payrolls_employee_id_fkey;
ALTER TABLE IF EXISTS ONLY public.payroll_lines DROP CONSTRAINT IF EXISTS payroll_lines_payroll_id_fkey;
ALTER TABLE IF EXISTS ONLY public.employee_periods DROP CONSTRAINT IF EXISTS employee_periods_location_id_fkey;
ALTER TABLE IF EXISTS ONLY public.employee_periods DROP CONSTRAINT IF EXISTS employee_periods_employee_id_fkey;
ALTER TABLE IF EXISTS ONLY public.documents DROP CONSTRAINT IF EXISTS documents_payroll_id_fkey;
ALTER TABLE IF EXISTS ONLY public.documents DROP CONSTRAINT IF EXISTS documents_employee_id_fkey;
ALTER TABLE IF EXISTS ONLY public.documents DROP CONSTRAINT IF EXISTS documents_client_id_fkey;
ALTER TABLE IF EXISTS ONLY public.client_locations DROP CONSTRAINT IF EXISTS client_locations_company_id_fkey;
ALTER TABLE IF EXISTS ONLY public.checklist_items DROP CONSTRAINT IF EXISTS checklist_items_payroll_id_fkey;
ALTER TABLE IF EXISTS ONLY public.checklist_items DROP CONSTRAINT IF EXISTS checklist_items_employee_id_fkey;
ALTER TABLE IF EXISTS ONLY public.checklist_items DROP CONSTRAINT IF EXISTS checklist_items_document_id_fkey;
ALTER TABLE IF EXISTS ONLY public.checklist_items DROP CONSTRAINT IF EXISTS checklist_items_client_id_fkey;
DROP INDEX IF EXISTS public.idx_payrolls_employee_id;
DROP INDEX IF EXISTS public.idx_payrolls_created_at;
DROP INDEX IF EXISTS public.idx_payroll_lines_payroll_id;
DROP INDEX IF EXISTS public.idx_payroll_lines_concept;
DROP INDEX IF EXISTS public.idx_payroll_lines_category;
DROP INDEX IF EXISTS public.idx_employees_identity_card;
DROP INDEX IF EXISTS public.idx_employee_periods_type;
DROP INDEX IF EXISTS public.idx_employee_periods_location_id;
DROP INDEX IF EXISTS public.idx_employee_periods_employee_id;
DROP INDEX IF EXISTS public.idx_employee_periods_dates;
DROP INDEX IF EXISTS public.idx_documents_status;
DROP INDEX IF EXISTS public.idx_documents_employee_id;
DROP INDEX IF EXISTS public.idx_documents_client_id;
DROP INDEX IF EXISTS public.idx_client_locations_company_id;
DROP INDEX IF EXISTS public.idx_client_locations_ccc_ss;
DROP INDEX IF EXISTS public.idx_checklist_items_status;
DROP INDEX IF EXISTS public.idx_checklist_items_due_date;
DROP INDEX IF EXISTS public.idx_checklist_items_client_id;
ALTER TABLE IF EXISTS ONLY public.payrolls DROP CONSTRAINT IF EXISTS payrolls_pkey;
ALTER TABLE IF EXISTS ONLY public.payroll_lines DROP CONSTRAINT IF EXISTS payroll_lines_pkey;
ALTER TABLE IF EXISTS ONLY public.nomina_concepts DROP CONSTRAINT IF EXISTS nomina_concepts_pkey;
ALTER TABLE IF EXISTS ONLY public.employees DROP CONSTRAINT IF EXISTS employees_pkey;
ALTER TABLE IF EXISTS ONLY public.employee_periods DROP CONSTRAINT IF EXISTS employee_periods_pkey;
ALTER TABLE IF EXISTS ONLY public.documents DROP CONSTRAINT IF EXISTS documents_pkey;
ALTER TABLE IF EXISTS ONLY public.clients DROP CONSTRAINT IF EXISTS clients_pkey;
ALTER TABLE IF EXISTS ONLY public.clients DROP CONSTRAINT IF EXISTS clients_cif_key;
ALTER TABLE IF EXISTS ONLY public.client_locations DROP CONSTRAINT IF EXISTS client_locations_pkey;
ALTER TABLE IF EXISTS ONLY public.client_locations DROP CONSTRAINT IF EXISTS client_locations_ccc_ss_key;
ALTER TABLE IF EXISTS ONLY public.checklist_items DROP CONSTRAINT IF EXISTS checklist_items_pkey;
ALTER TABLE IF EXISTS public.payrolls ALTER COLUMN id DROP DEFAULT;
ALTER TABLE IF EXISTS public.payroll_lines ALTER COLUMN id DROP DEFAULT;
ALTER TABLE IF EXISTS public.employees ALTER COLUMN id DROP DEFAULT;
ALTER TABLE IF EXISTS public.employee_periods ALTER COLUMN id DROP DEFAULT;
ALTER TABLE IF EXISTS public.documents ALTER COLUMN id DROP DEFAULT;
ALTER TABLE IF EXISTS public.client_locations ALTER COLUMN id DROP DEFAULT;
ALTER TABLE IF EXISTS public.checklist_items ALTER COLUMN id DROP DEFAULT;
DROP SEQUENCE IF EXISTS public.payrolls_id_seq;
DROP TABLE IF EXISTS public.payrolls;
DROP SEQUENCE IF EXISTS public.payroll_lines_id_seq;
DROP TABLE IF EXISTS public.payroll_lines;
DROP TABLE IF EXISTS public.nomina_concepts;
DROP SEQUENCE IF EXISTS public.employees_id_seq;
DROP TABLE IF EXISTS public.employees;
DROP SEQUENCE IF EXISTS public.employee_periods_id_seq;
DROP TABLE IF EXISTS public.employee_periods;
DROP SEQUENCE IF EXISTS public.documents_id_seq;
DROP TABLE IF EXISTS public.documents;
DROP TABLE IF EXISTS public.clients;
DROP SEQUENCE IF EXISTS public.client_locations_id_seq;
DROP TABLE IF EXISTS public.client_locations;
DROP SEQUENCE IF EXISTS public.checklist_items_id_seq;
DROP TABLE IF EXISTS public.checklist_items;
DROP TYPE IF EXISTS public.payroll_type;
--
-- Name: payroll_type; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.payroll_type AS ENUM (
    'payslip',
    'settlement',
    'hybrid'
);


SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: checklist_items; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.checklist_items (
    id integer NOT NULL,
    client_id uuid NOT NULL,
    employee_id integer,
    payroll_id integer,
    item_type text NOT NULL,
    description text NOT NULL,
    period_year integer,
    period_month integer,
    due_date date,
    status text,
    priority text,
    reminder_count integer,
    last_reminder_sent_at timestamp with time zone,
    next_reminder_due_at timestamp with time zone,
    document_id integer,
    notes text,
    created_at timestamp with time zone,
    updated_at timestamp with time zone
);


--
-- Name: checklist_items_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.checklist_items_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: checklist_items_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.checklist_items_id_seq OWNED BY public.checklist_items.id;


--
-- Name: client_locations; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.client_locations (
    id integer NOT NULL,
    company_id uuid NOT NULL,
    ccc_ss text NOT NULL,
    created_at timestamp with time zone,
    updated_at timestamp with time zone
);


--
-- Name: client_locations_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.client_locations_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: client_locations_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.client_locations_id_seq OWNED BY public.client_locations.id;


--
-- Name: clients; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.clients (
    id uuid NOT NULL,
    name text NOT NULL,
    cif text NOT NULL,
    fiscal_address text,
    email text,
    phone text,
    begin_date timestamp with time zone,
    managed_by text,
    payslips boolean NOT NULL,
    legal_repr_first_name text,
    legal_repr_last_name1 text,
    legal_repr_last_name2 text,
    legal_repr_nif text,
    legal_repr_role text,
    legal_repr_phone text,
    legal_repr_email text,
    status text,
    active boolean,
    created_at timestamp with time zone,
    updated_at timestamp with time zone
);


--
-- Name: documents; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.documents (
    id integer NOT NULL,
    client_id uuid,
    employee_id integer,
    payroll_id integer,
    document_type text NOT NULL,
    original_filename text,
    file_path text NOT NULL,
    file_hash text,
    file_size_bytes integer,
    received_at timestamp with time zone,
    processed_at timestamp with time zone,
    status text,
    ocr_text text,
    extraction_result json,
    extraction_confidence numeric(3,2),
    created_at timestamp with time zone,
    updated_at timestamp with time zone
);


--
-- Name: documents_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.documents_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: documents_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.documents_id_seq OWNED BY public.documents.id;


--
-- Name: employee_periods; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.employee_periods (
    id integer NOT NULL,
    employee_id integer NOT NULL,
    location_id integer NOT NULL,
    period_begin_date date NOT NULL,
    period_end_date date,
    period_type text NOT NULL,
    tipo_contrato text,
    salary numeric(12,2),
    role text,
    notes text,
    created_at timestamp with time zone,
    updated_at timestamp with time zone
);


--
-- Name: employee_periods_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.employee_periods_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: employee_periods_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.employee_periods_id_seq OWNED BY public.employee_periods.id;


--
-- Name: employees; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.employees (
    id integer NOT NULL,
    first_name text NOT NULL,
    last_name text NOT NULL,
    last_name2 text,
    identity_card_number text NOT NULL,
    identity_doc_type text,
    ss_number text,
    birth_date date,
    address text,
    phone text,
    mail text,
    created_at timestamp with time zone,
    updated_at timestamp with time zone
);


--
-- Name: employees_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.employees_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: employees_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.employees_id_seq OWNED BY public.employees.id;


--
-- Name: nomina_concepts; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.nomina_concepts (
    concept_code text NOT NULL,
    short_desc text NOT NULL,
    long_desc text,
    tributa_irpf boolean,
    cotiza_ss boolean,
    en_especie boolean,
    default_group text,
    created_at timestamp with time zone,
    updated_at timestamp with time zone
);


--
-- Name: payroll_lines; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.payroll_lines (
    id integer NOT NULL,
    payroll_id integer NOT NULL,
    category character varying NOT NULL,
    concept text NOT NULL,
    raw_concept text,
    amount numeric(12,2) NOT NULL,
    is_taxable_income boolean NOT NULL,
    is_taxable_ss boolean NOT NULL,
    is_sickpay boolean NOT NULL,
    is_in_kind boolean NOT NULL,
    is_pay_advance boolean NOT NULL,
    is_seizure boolean NOT NULL,
    created_at timestamp with time zone,
    updated_at timestamp with time zone
);


--
-- Name: payroll_lines_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.payroll_lines_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: payroll_lines_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.payroll_lines_id_seq OWNED BY public.payroll_lines.id;


--
-- Name: payrolls; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.payrolls (
    id integer NOT NULL,
    employee_id integer NOT NULL,
    type public.payroll_type NOT NULL,
    periodo json NOT NULL,
    devengo_total numeric(12,2) NOT NULL,
    deduccion_total numeric(12,2) NOT NULL,
    aportacion_empresa_total numeric(12,2) NOT NULL,
    liquido_a_percibir numeric(12,2) NOT NULL,
    prorrata_pagas_extra numeric(12,2) NOT NULL,
    base_cc numeric(12,2) NOT NULL,
    base_at_ep numeric(12,2) NOT NULL,
    base_irpf numeric(12,2) NOT NULL,
    tipo_irpf numeric(5,2) NOT NULL,
    warnings text,
    is_merged boolean,
    merged_from_files text,
    created_at timestamp with time zone,
    updated_at timestamp with time zone
);


--
-- Name: payrolls_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.payrolls_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: payrolls_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.payrolls_id_seq OWNED BY public.payrolls.id;


--
-- Name: checklist_items id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.checklist_items ALTER COLUMN id SET DEFAULT nextval('public.checklist_items_id_seq'::regclass);


--
-- Name: client_locations id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.client_locations ALTER COLUMN id SET DEFAULT nextval('public.client_locations_id_seq'::regclass);


--
-- Name: documents id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.documents ALTER COLUMN id SET DEFAULT nextval('public.documents_id_seq'::regclass);


--
-- Name: employee_periods id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.employee_periods ALTER COLUMN id SET DEFAULT nextval('public.employee_periods_id_seq'::regclass);


--
-- Name: employees id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.employees ALTER COLUMN id SET DEFAULT nextval('public.employees_id_seq'::regclass);


--
-- Name: payroll_lines id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.payroll_lines ALTER COLUMN id SET DEFAULT nextval('public.payroll_lines_id_seq'::regclass);


--
-- Name: payrolls id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.payrolls ALTER COLUMN id SET DEFAULT nextval('public.payrolls_id_seq'::regclass);


--
-- Data for Name: checklist_items; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.checklist_items (id, client_id, employee_id, payroll_id, item_type, description, period_year, period_month, due_date, status, priority, reminder_count, last_reminder_sent_at, next_reminder_due_at, document_id, notes, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: client_locations; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.client_locations (id, company_id, ccc_ss, created_at, updated_at) FROM stdin;
1	0401d4b5-a2fe-4f2b-a17f-373ea88f7b55	03138689725	2025-12-31 11:47:25.731574+00	2025-12-31 11:47:25.731574+00
\.


--
-- Data for Name: clients; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.clients (id, name, cif, fiscal_address, email, phone, begin_date, managed_by, payslips, legal_repr_first_name, legal_repr_last_name1, legal_repr_last_name2, legal_repr_nif, legal_repr_role, legal_repr_phone, legal_repr_email, status, active, created_at, updated_at) FROM stdin;
0401d4b5-a2fe-4f2b-a17f-373ea88f7b55	TEPUY BURGER SL	B42524694	Calle Granja de Rocamora 16	manuel@tepuyburger.com	+34694411314	2024-12-01 00:00:00+00	0193730cdf5d3cc1	t	Manuel Alejandro	Zambrano	Perales	48800739Y	CEO	+34694411314	info@tepuyburger.es	Active	t	2025-12-31 11:47:25.731574+00	2025-12-31 11:47:25.731574+00
\.


--
-- Data for Name: documents; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.documents (id, client_id, employee_id, payroll_id, document_type, original_filename, file_path, file_hash, file_size_bytes, received_at, processed_at, status, ocr_text, extraction_result, extraction_confidence, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: employee_periods; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.employee_periods (id, employee_id, location_id, period_begin_date, period_end_date, period_type, tipo_contrato, salary, role, notes, created_at, updated_at) FROM stdin;
1	1	1	2025-06-03	\N	alta	100	1500.00	Empleado	ALTA from vida laboral: Arianna Matheus Valdivieso	2025-12-31 11:47:25.797932+00	2025-12-31 11:47:25.797932+00
2	2	1	2025-06-20	2025-06-26	baja	502	1500.00	Empleado	BAJA without prior ALTA: May Femenia Lecea	2025-12-31 11:47:25.797932+00	2025-12-31 11:47:25.797932+00
3	3	1	2025-06-17	2025-08-20	baja	200	1500.00	Empleado	BAJA without prior ALTA: Paola Cristina Jurado Cruz	2025-12-31 11:47:25.797932+00	2025-12-31 11:47:25.797932+00
4	2	1	2025-07-07	2025-09-07	baja	300_p	1500.00	Empleado	BAJA without prior ALTA: May Femenia Lecea	2025-12-31 11:47:25.797932+00	2025-12-31 11:47:25.797932+00
5	4	1	2023-07-13	2024-12-16	baja	200	1500.00	Empleado	BAJA without prior ALTA: Luis Miguel Romero Guevara	2025-12-31 11:47:25.797932+00	2025-12-31 11:47:25.797932+00
6	5	1	2017-12-05	\N	alta	289	1500.00	Empleado	ALTA from vida laboral: Mario Andres Rosadoro	2025-12-31 11:47:25.797932+00	2025-12-31 11:47:25.797932+00
7	6	1	2023-08-16	2025-08-07	baja	200	1500.00	Empleado	BAJA without prior ALTA: Alvin David Schumller Estrada	2025-12-31 11:47:25.797932+00	2025-12-31 11:47:25.797932+00
8	7	1	2025-09-03	2025-09-10	baja	200	1500.00	Empleado	BAJA without prior ALTA: Sebastian Teran Rendon	2025-12-31 11:47:25.797932+00	2025-12-31 11:47:25.797932+00
9	8	1	2025-09-08	\N	alta	200	1500.00	Empleado	ALTA from vida laboral: Andrea Brito Ortiz	2025-12-31 11:47:25.797932+00	2025-12-31 11:47:25.797932+00
10	9	1	2025-09-12	\N	alta	200	1500.00	Empleado	ALTA from vida laboral: Luis Enrique Colmenarez Vargas	2025-12-31 11:47:25.797932+00	2025-12-31 11:47:25.797932+00
11	10	1	2024-09-06	2025-02-11	baja	200	1500.00	Empleado	BAJA without prior ALTA: Luis Jose Briceño Urdaneta	2025-12-31 11:47:25.797932+00	2025-12-31 11:47:25.797932+00
12	11	1	2024-09-23	\N	alta	200	1500.00	Empleado	ALTA from vida laboral: Javier Guijarro Lillo	2025-12-31 11:47:25.797932+00	2025-12-31 11:47:25.797932+00
13	12	1	2025-02-21	2025-07-10	baja	200	1500.00	Empleado	BAJA without prior ALTA: Pedro Roldan Vera	2025-12-31 11:47:25.797932+00	2025-12-31 11:47:25.797932+00
14	13	1	2022-04-22	\N	alta	100	1500.00	Empleado	ALTA from vida laboral: Carlos Martin Jurado Garcia	2025-12-31 11:47:25.797932+00	2025-12-31 11:47:25.797932+00
15	14	1	2022-03-01	2025-06-11	baja	200	1500.00	Empleado	BAJA without prior ALTA: Manu Garcia Salmeron	2025-12-31 11:47:25.797932+00	2025-12-31 11:47:25.797932+00
16	15	1	2023-04-07	2025-09-14	baja	200	1500.00	Empleado	BAJA without prior ALTA: Paola Alejandra Castillo Mendez	2025-12-31 11:47:25.797932+00	2025-12-31 11:47:25.797932+00
17	16	1	2017-12-05	\N	alta	Aut	1500.00	Empleado	ALTA from vida laboral: Manuel Alejandro Zambrano	2025-12-31 11:47:25.797932+00	2025-12-31 11:47:25.797932+00
18	17	1	2025-01-14	\N	alta	200	1500.00	Empleado	ALTA from vida laboral: Angy Paola Reyes Leonett	2025-12-31 11:47:25.797932+00	2025-12-31 11:47:25.797932+00
19	18	1	2025-02-17	\N	alta	100	1500.00	Empleado	ALTA from vida laboral: Federico Emiliano Dabrowski Donati	2025-12-31 11:47:25.797932+00	2025-12-31 11:47:25.797932+00
20	19	1	2017-12-05	\N	alta	Aut	1500.00	Empleado	ALTA from vida laboral: Nazaria Coromoto Perales	2025-12-31 11:47:25.797932+00	2025-12-31 11:47:25.797932+00
21	20	1	2025-01-08	2025-01-10	baja	200	1500.00	Empleado	BAJA without prior ALTA: Aleix Moreno Victoria	2025-12-31 11:47:25.797932+00	2025-12-31 11:47:25.797932+00
22	21	1	2025-01-21	2025-02-07	baja	200	1500.00	Empleado	BAJA without prior ALTA: Lenna García Barrera	2025-12-31 11:47:25.797932+00	2025-12-31 11:47:25.797932+00
23	22	1	2025-09-15	2025-11-04	baja	200	1500.00	Empleado	BAJA without prior ALTA: Meriem Lounici Zenati	2025-12-31 11:47:25.797932+00	2025-12-31 11:47:25.797932+00
24	2	1	2025-11-08	\N	alta	200	1500.00	Empleado	ALTA from vida laboral: May Femenía Lecea	2025-12-31 11:47:25.797932+00	2025-12-31 11:47:25.797932+00
25	23	1	2023-08-01	2025-01-31	baja	100	1500.00	Empleado	BAJA without prior ALTA: Anthony Samuel Guerra Aguilar	2025-12-31 11:47:25.797932+00	2025-12-31 11:47:25.797932+00
26	24	1	2024-07-05	2024-12-29	baja	200	1500.00	Empleado	BAJA without prior ALTA: Matias Albertario La Volpe	2025-12-31 11:47:25.797932+00	2025-12-31 11:47:25.797932+00
27	25	1	2024-04-10	2025-02-22	baja	200	1500.00	Empleado	BAJA without prior ALTA: Larisa Stefania Avadanei	2025-12-31 11:47:25.797932+00	2025-12-31 11:47:25.797932+00
\.


--
-- Data for Name: employees; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.employees (id, first_name, last_name, last_name2, identity_card_number, identity_doc_type, ss_number, birth_date, address, phone, mail, created_at, updated_at) FROM stdin;
1	Arianna	Matheus Valdivieso	\N	Z2553378S	NIE	281665604114	\N	\N	\N	\N	2025-12-31 11:47:25.797932+00	2025-12-31 11:47:25.797932+00
2	May	Femenia Lecea	\N	53249237M	DNI	031124442338	\N	\N	\N	\N	2025-12-31 11:47:25.797932+00	2025-12-31 11:47:25.797932+00
3	Paola Cristina	Jurado Cruz	\N	55018719M	DNI	031132342481	\N	\N	\N	\N	2025-12-31 11:47:25.797932+00	2025-12-31 11:47:25.797932+00
4	Luis Miguel	Romero Guevara	\N	Z0258655W	NIE	281604783292	\N	\N	\N	\N	2025-12-31 11:47:25.797932+00	2025-12-31 11:47:25.797932+00
5	Mario Andres	Rosadoro	\N	Y5381343R	NIE	031123804764	\N	\N	\N	\N	2025-12-31 11:47:25.797932+00	2025-12-31 11:47:25.797932+00
6	Alvin David	Schumller Estrada	\N	4725214W	DNI	031116248060	\N	\N	\N	\N	2025-12-31 11:47:25.797932+00	2025-12-31 11:47:25.797932+00
7	Sebastian	Teran	Rendon	Z2477711H	NIE	081508189311	\N	\N	\N	\N	2025-12-31 11:47:25.797932+00	2025-12-31 11:47:25.797932+00
8	Andrea	Brito Ortiz	\N	Z0673117G	NIE	031163238500	\N	\N	\N	\N	2025-12-31 11:47:25.797932+00	2025-12-31 11:47:25.797932+00
9	Luis Enrique	Colmenarez Vargas	\N	Z2779517H	NIE	031174903556	\N	\N	\N	\N	2025-12-31 11:47:25.797932+00	2025-12-31 11:47:25.797932+00
10	Luis Jose	Briceño Urdaneta	\N	Y9224360V	NIE	031156890050	\N	\N	\N	\N	2025-12-31 11:47:25.797932+00	2025-12-31 11:47:25.797932+00
11	Javier	Guijarro Lillo	\N	51774361G	DNI	031125323220	\N	\N	\N	\N	2025-12-31 11:47:25.797932+00	2025-12-31 11:47:25.797932+00
12	Pedro	Roldan Vera	\N	46083684X	DNI	031145101217	\N	\N	\N	\N	2025-12-31 11:47:25.797932+00	2025-12-31 11:47:25.797932+00
13	Carlos Martin	Jurado Garcia	\N	Y7509823S	NIE	031137009393	\N	\N	\N	\N	2025-12-31 11:47:25.797932+00	2025-12-31 11:47:25.797932+00
14	Manu	Garcia Salmeron	\N	53231738D	DNI	031029253410	\N	\N	\N	\N	2025-12-31 11:47:25.797932+00	2025-12-31 11:47:25.797932+00
15	Paola Alejandra	Castillo Mendez	\N	Y9711595C	NIE	031154836276	\N	\N	\N	\N	2025-12-31 11:47:25.797932+00	2025-12-31 11:47:25.797932+00
16	Manuel Alejandro	Zambrano	\N	48800739Y	DNI	031102408079	\N	\N	\N	\N	2025-12-31 11:47:25.797932+00	2025-12-31 11:47:25.797932+00
17	Angy Paola	Reyes Leonett	\N	Z1994241P	NIE	031169450540	\N	\N	\N	\N	2025-12-31 11:47:25.797932+00	2025-12-31 11:47:25.797932+00
18	Federico Emiliano	Dabrowski Donati	\N	Y7724535E	NIE	031138029917	\N	\N	\N	\N	2025-12-31 11:47:25.797932+00	2025-12-31 11:47:25.797932+00
19	Nazaria Coromoto	Perales	\N	48794244C	DNI	031089765646	\N	\N	\N	\N	2025-12-31 11:47:25.797932+00	2025-12-31 11:47:25.797932+00
20	Aleix	Moreno Victoria	\N	54454402Q	DNI	031087635383	\N	\N	\N	\N	2025-12-31 11:47:25.797932+00	2025-12-31 11:47:25.797932+00
21	Lenna	García Barrera	\N	Z0232553M	NIE	031154907109	\N	\N	\N	\N	2025-12-31 11:47:25.797932+00	2025-12-31 11:47:25.797932+00
22	Meriem	Lounici	Zenati	78152210G	DNI	181063641173	\N	\N	\N	\N	2025-12-31 11:47:25.797932+00	2025-12-31 11:47:25.797932+00
23	Anthony Samuel	Guerra Aguilar	\N	Y9174572R	NIE	031156440618	\N	\N	\N	\N	2025-12-31 11:47:25.797932+00	2025-12-31 11:47:25.797932+00
24	Matias Albertario	La Volpe	\N	4716833Q	DNI	031145810630	\N	\N	\N	\N	2025-12-31 11:47:25.797932+00	2025-12-31 11:47:25.797932+00
25	Larisa Stefania	Avadanei	\N	X9799225Y	NIE	161010992437	\N	\N	\N	\N	2025-12-31 11:47:25.797932+00	2025-12-31 11:47:25.797932+00
\.


--
-- Data for Name: nomina_concepts; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.nomina_concepts (concept_code, short_desc, long_desc, tributa_irpf, cotiza_ss, en_especie, default_group, created_at, updated_at) FROM stdin;
001	Salario base	\N	t	t	f	ordinaria	2025-12-31 11:46:28.74679+00	2025-12-31 11:46:28.74679+00
002	Antigüedad	\N	t	t	f	ordinaria	2025-12-31 11:46:28.74679+00	2025-12-31 11:46:28.74679+00
120	Plus convenio	\N	t	t	f	ordinaria	2025-12-31 11:46:28.74679+00	2025-12-31 11:46:28.74679+00
301	Horas extra	\N	t	t	f	variable	2025-12-31 11:46:28.74679+00	2025-12-31 11:46:28.74679+00
601	Seguro médico	\N	t	f	t	especie	2025-12-31 11:46:28.74679+00	2025-12-31 11:46:28.74679+00
620	Ticket restaurant	\N	t	f	t	especie	2025-12-31 11:46:28.74679+00	2025-12-31 11:46:28.74679+00
700	IRPF	\N	f	f	f	deduccion	2025-12-31 11:46:28.74679+00	2025-12-31 11:46:28.74679+00
730	SS Trabajador	\N	f	f	f	deduccion	2025-12-31 11:46:28.74679+00	2025-12-31 11:46:28.74679+00
\.


--
-- Data for Name: payroll_lines; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.payroll_lines (id, payroll_id, category, concept, raw_concept, amount, is_taxable_income, is_taxable_ss, is_sickpay, is_in_kind, is_pay_advance, is_seizure, created_at, updated_at) FROM stdin;
1	1	devengo	SALARIO BASE	*SALARIO BASE	883.54	t	t	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
2	1	devengo	HORAS NOCTURNAS	*HORAS NOCTURNAS	29.29	t	t	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
3	1	devengo	PAGA EXTRA	*PAGA EXTRA	218.49	t	t	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
4	1	deduccion	DTO. CONT. COMUNES	COTIZACIÓN CONTINGENCIAS COMUNES (4,70%)	56.06	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
5	1	deduccion	MEI	COTIZACIÓN MECANISMO EQUIDAD INTERGENERACIONAL (0,13%)	1.56	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
6	1	deduccion	FORMACIÓN PROFESIONAL	COTIZACIÓN FORMACIÓN PROFESIONAL (0,10%)	1.19	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
7	1	deduccion	DESEMPLEO	COTIZACIÓN DESEMPLEO (1,55%)	18.48	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
8	1	aportacion_empresa	TOTAL CONTINGENCIAS COMUNES + PRORRATA PAGAS EXTRAS	BASE INCAPACIDAD TEMPORAL TOTAL	281.52	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
9	1	aportacion_empresa	MEI	MECANISMO EQUIDAD INTERGENERACIONAL	7.98	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
10	1	aportacion_empresa	AT Y EP	AT Y EP	17.89	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
11	1	aportacion_empresa	DESEMPLEO	DESEMPLEO	65.61	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
12	1	aportacion_empresa	FORMACIÓN PROFESIONAL	FORMACIÓN PROFESIONAL	7.17	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
13	1	aportacion_empresa	FONDO GARANTÍA SALARIAL	FONDO DE GARANTÍA SALARIAL	2.39	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
14	2	devengo	SALARIO BASE	*SALARIO BASE	841.00	t	t	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
15	2	devengo	HORAS NOCTURNAS	*HORAS NOCTURNAS	26.26	t	t	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
16	2	devengo	PAGA EXTRA	*PAGA EXTRA	207.97	t	t	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
17	2	deduccion	DTO. CONT. COMUNES	COTIZACIÓN CONTINGENCIAS COMUNES (4,70%)	52.28	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
18	2	deduccion	MEI	COTIZACIÓN MECANISMO EQUIDAD INTERGENERACIONAL (0,13%)	1.45	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
19	2	deduccion	DTO. SEGURIDAD SOCIAL	COTIZACIÓN FORMACIÓN PROFESIONAL (0,10%)	1.11	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
20	2	deduccion	DTO. SEGURIDAD SOCIAL	COTIZACIÓN DESEMPLEO (1,55%)	17.24	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
21	2	aportacion_empresa	TOTAL CONTINGENCIAS COMUNES + PRORRATA PAGAS EXTRAS	CONTINGENCIAS COMUNES	262.52	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
22	2	aportacion_empresa	MEI	MECANISMO EQUIDAD INTERGENERACIONAL	7.45	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
23	2	aportacion_empresa	AT Y EP	AT Y EP	16.68	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
24	2	aportacion_empresa	DESEMPLEO	DESEMPLEO	61.18	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
25	2	aportacion_empresa	FORMACIÓN PROFESIONAL	FORMACIÓN PROFESIONAL	6.67	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
26	2	aportacion_empresa	FONDO GARANTÍA SALARIAL	FONDO DE GARANTÍA SALARIAL	2.22	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
27	3	devengo	SALARIO BASE	*SALARIO BASE	897.74	t	t	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
28	3	devengo	NOCTURNIDAD	*HORAS NOCTURNAS	18.18	t	t	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
29	3	devengo	PAGA EXTRA	*PAGA EXTRA	221.99	t	t	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
30	3	deduccion	DTO. CONT. COMUNES	COTIZACIÓN CONTINGENCIAS COMUNES (4,70%)	55.03	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
31	3	deduccion	MEI	COTIZACIÓN MECANISMO EQUIDAD INTERGENERACIONAL (0,13%)	1.53	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
32	3	deduccion	FORMACIÓN PROFESIONAL	COTIZACIÓN FORMACIÓN PROFESIONAL (0,10%)	1.17	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
33	3	deduccion	DESEMPLEO	COTIZACIÓN DESEMPLEO (1,55%)	18.15	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
34	3	aportacion_empresa	TOTAL CONTINGENCIAS COMUNES + PRORRATA PAGAS EXTRAS	BASE INCAPACIDAD TEMPORAL TOTAL	276.32	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
35	3	aportacion_empresa	MEI	MECANISMO EQUIDAD INTERGENERACIONAL	7.84	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
36	3	aportacion_empresa	AT Y EP	AT Y EP	17.57	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
37	3	aportacion_empresa	DESEMPLEO	DESEMPLEO	64.40	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
38	3	aportacion_empresa	FORMACIÓN PROFESIONAL	FORMACIÓN PROFESIONAL	7.03	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
39	3	aportacion_empresa	FONDO GARANTÍA SALARIAL	FONDO DE GARANTÍA SALARIAL	2.35	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
40	4	devengo	SALARIO BASE	*SALARIO BASE	884.49	t	t	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
41	4	devengo	HORAS NOCTURNAS	*HORAS NOCTURNAS	22.22	t	t	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
42	4	devengo	PAGA EXTRA	*PAGA EXTRA	218.72	t	t	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
43	4	deduccion	DTO. CONT. COMUNES	COTIZACIÓN CONTINGENCIAS COMUNES (4,70%)	52.90	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
44	4	deduccion	MEI	COTIZACIÓN MECANISMO EQUIDAD INTERGENERACIONAL (0,13%)	1.46	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
45	4	deduccion	FORMACIÓN PROFESIONAL	COTIZACIÓN FORMACIÓN PROFESIONAL (0,10%)	1.13	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
46	4	deduccion	DESEMPLEO	COTIZACIÓN DESEMPLEO (1,55%)	17.44	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
47	4	aportacion_empresa	TOTAL CONTINGENCIAS COMUNES + PRORRATA PAGAS EXTRAS	CONTINGENCIAS COMUNES	265.60	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
48	4	aportacion_empresa	MEI	MECANISMO EQUIDAD INTERGENERACIONAL	7.54	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
49	4	aportacion_empresa	AT Y EP	AT Y EP	16.88	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
50	4	aportacion_empresa	DESEMPLEO	DESEMPLEO	61.90	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
51	4	aportacion_empresa	FORMACIÓN PROFESIONAL	FORMACIÓN PROFESIONAL	6.75	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
52	4	aportacion_empresa	FONDO GARANTÍA SALARIAL	FONDO DE GARANTÍA SALARIAL	2.25	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
53	5	devengo	SALARIO BASE	*SALARIO BASE	884.49	t	t	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
54	5	devengo	HORAS NOCTURNAS	*HORAS NOCTURNAS	27.27	t	t	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
55	5	devengo	HORAS COMPLEMENTARIAS	*HORAS COMPLEMENTARIAS	25.05	t	t	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
56	5	devengo	PAGA EXTRA	*PAGA EXTRA	218.72	t	t	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
57	5	deduccion	DTO. CONT. COMUNES	COTIZACIÓN CONTINGENCIAS COMUNES (4,70%)	54.31	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
58	5	deduccion	MEI	COTIZACIÓN MECANISMO EQUIDAD INTERGENERACIONAL (0,13%)	1.50	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
59	5	deduccion	FORMACIÓN PROFESIONAL	COTIZACIÓN FORMACIÓN PROFESIONAL (0,10%)	1.16	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
60	5	deduccion	DESEMPLEO	COTIZACIÓN DESEMPLEO (1,55%)	17.91	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
61	5	aportacion_empresa	TOTAL CONTINGENCIAS COMUNES + PRORRATA PAGAS EXTRAS	CONTINGENCIAS COMUNES	272.71	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
62	5	aportacion_empresa	MEI	MECANISMO EQUIDAD INTERGENERACIONAL	7.74	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
63	5	aportacion_empresa	AT Y EP	AT Y EP	17.33	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
64	5	aportacion_empresa	DESEMPLEO	DESEMPLEO	63.55	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
65	5	aportacion_empresa	FORMACIÓN PROFESIONAL	FORMACIÓN PROFESIONAL	6.93	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
66	5	aportacion_empresa	FONDO GARANTÍA SALARIAL	FONDO DE GARANTÍA SALARIAL	2.31	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
67	6	devengo	SALARIO BASE	*SALARIO BASE	884.49	t	t	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
68	6	devengo	HORAS NOCTURNAS	*HORAS NOCTURNAS	25.25	t	t	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
69	6	devengo	PAGA EXTRA	*PAGA EXTRA	218.72	t	t	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
70	6	deduccion	ABSENTISMO	*ABSENTISMO	115.29	t	t	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
71	6	deduccion	DTO. CONT. COMUNES	COTIZACIÓN CONTINGENCIAS COMUNES (4,70%)	53.04	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
72	6	deduccion	MEI	COTIZACIÓN MECANISMO EQUIDAD INTERGENERACIONAL (0,13%)	1.47	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
73	6	deduccion	FORMACIÓN PROFESIONAL	COTIZACIÓN FORMACIÓN PROFESIONAL (0,10%)	1.13	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
74	6	deduccion	DESEMPLEO	COTIZACIÓN DESEMPLEO (1,55%)	17.49	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
75	6	aportacion_empresa	TOTAL CONTINGENCIAS COMUNES + PRORRATA PAGAS EXTRAS	CONTINGENCIAS COMUNES	266.32	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
76	6	aportacion_empresa	MEI	MECANISMO EQUIDAD INTERGENERACIONAL	7.56	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
77	6	aportacion_empresa	AT Y EP	AT Y EP	16.93	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
78	6	aportacion_empresa	DESEMPLEO	DESEMPLEO	62.07	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
79	6	aportacion_empresa	FORMACIÓN PROFESIONAL	FORMACIÓN PROFESIONAL	6.77	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
80	6	aportacion_empresa	FONDO GARANTÍA SALARIAL	FONDO DE GARANTÍA SALARIAL	2.26	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
81	7	devengo	SALARIO BASE	SALARIO BASE	884.49	t	t	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
82	7	devengo	HORAS NOCTURNAS	HORAS NOCTURNAS	22.22	t	t	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
83	7	devengo	PAGA EXTRA	PAGA EXTRA	218.72	t	t	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
84	7	deduccion	ABSENTISMO	ABSENTISMO	102.48	t	t	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
85	7	deduccion	DTO. CONT. COMUNES	COTIZACIÓN CONTINGENCIAS COMUNES (4,70%)	52.90	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
86	7	deduccion	MEI	COTIZACIÓN MECANISMO EQUIDAD INTERGENERACIONAL (0,13%)	1.46	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
87	7	deduccion	FORMACIÓN PROFESIONAL	COTIZACIÓN FORMACIÓN PROFESIONAL (0,10%)	1.13	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
88	7	deduccion	DESEMPLEO	COTIZACIÓN DESEMPLEO (1,55%)	17.44	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
89	7	aportacion_empresa	TOTAL CONTINGENCIAS COMUNES + PRORRATA PAGAS EXTRAS	CONTINGENCIAS COMUNES	265.60	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
90	7	aportacion_empresa	MEI	MECANISMO EQUIDAD INTERGENERACIONAL	7.54	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
91	7	aportacion_empresa	AT Y EP	AT Y EP	16.88	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
92	7	aportacion_empresa	DESEMPLEO	DESEMPLEO	61.90	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
93	7	aportacion_empresa	FORMACIÓN PROFESIONAL	FORMACIÓN PROFESIONAL	6.75	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
94	7	aportacion_empresa	FONDO GARANTÍA SALARIAL	FONDO DE GARANTÍA SALARIAL	2.25	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
95	8	devengo	SALARIO BASE	*SALARIO BASE	243.18	t	t	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
96	8	devengo	PAGA EXTRA	*PAGA EXTRA	60.13	t	t	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
97	8	deduccion	DTO. CONT. COMUNES	COTIZACIÓN CONTINGENCIAS COMUNES (4,70%)	14.26	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
98	8	deduccion	MEI	COTIZACIÓN MECANISMO EQUIDAD INTERGENERACIONAL (0,13%)	0.39	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
99	8	deduccion	FORMACIÓN PROFESIONAL	COTIZACIÓN FORMACIÓN PROFESIONAL (0,10%)	0.30	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
100	8	deduccion	DESEMPLEO	COTIZACIÓN DESEMPLEO (1,55%)	4.70	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
101	8	aportacion_empresa	TOTAL CONTINGENCIAS COMUNES + PRORRATA PAGAS EXTRAS	BASE INCAPACIDAD TEMPORAL TOTAL	71.58	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
102	8	aportacion_empresa	MEI	MECANISMO EQUIDAD INTERGENERACIONAL	2.04	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
103	8	aportacion_empresa	AT Y EP	AT Y EP	4.55	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
104	8	aportacion_empresa	DESEMPLEO	DESEMPLEO	16.68	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
105	8	aportacion_empresa	FORMACIÓN PROFESIONAL	FORMACIÓN PROFESIONAL	1.82	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
106	8	aportacion_empresa	FONDO GARANTÍA SALARIAL	FONDO DE GARANTÍA SALARIAL	0.61	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
107	9	devengo	SALARIO BASE	*SALARIO BASE	729.53	t	t	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
108	9	devengo	HORAS NOCTURNAS	*HORAS NOCTURNAS	10.10	t	t	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
109	9	devengo	PAGA EXTRA	*PAGA EXTRA	180.40	t	t	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
110	9	deduccion	DTO. CONT. COMUNES	COTIZACIÓN CONTINGENCIAS COMUNES (4,70%)	43.24	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
111	9	deduccion	MEI	COTIZACIÓN MECANISMO EQUIDAD INTERGENERACIONAL (0,13%)	1.20	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
112	9	deduccion	FORMACIÓN PROFESIONAL	COTIZACIÓN FORMACIÓN PROFESIONAL (0,10%)	0.92	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
113	9	deduccion	DESEMPLEO	COTIZACIÓN DESEMPLEO (1,55%)	14.26	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
114	9	aportacion_empresa	TOTAL CONTINGENCIAS COMUNES + PRORRATA PAGAS EXTRAS	CONTINGENCIAS COMUNES	217.13	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
115	9	aportacion_empresa	MEI	MECANISMO EQUIDAD INTERGENERACIONAL	6.16	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
116	9	aportacion_empresa	AT Y EP	AT Y EP	13.80	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
117	9	aportacion_empresa	DESEMPLEO	DESEMPLEO	50.60	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
118	9	aportacion_empresa	FORMACIÓN PROFESIONAL	FORMACIÓN PROFESIONAL	5.52	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
119	9	aportacion_empresa	FONDO GARANTÍA SALARIAL	FONDO DE GARANTÍA SALARIAL	1.84	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
120	10	devengo	SALARIO BASE	*SALARIO BASE	829.95	t	t	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
121	10	devengo	HORAS NOCTURNAS	*HORAS NOCTURNAS	33.33	t	t	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
122	10	devengo	HORAS COMPLEMENTARIAS	*HORAS COMPLEMENTARIAS	77.24	t	t	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
123	10	devengo	PAGA EXTRA	*PAGA EXTRA	205.24	t	t	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
124	10	deduccion	DTO. CONT. COMUNES	COTIZACIÓN CONTINGENCIAS COMUNES (4,70%)	54.42	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
125	10	deduccion	MEI	COTIZACIÓN MECANISMO EQUIDAD INTERGENERACIONAL (0,13%)	1.51	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
126	10	deduccion	FORMACIÓN PROFESIONAL	COTIZACIÓN FORMACIÓN PROFESIONAL (0,10%)	1.16	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
127	10	deduccion	DESEMPLEO	COTIZACIÓN DESEMPLEO (1,55%)	17.94	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
128	10	aportacion_empresa	TOTAL CONTINGENCIAS COMUNES + PRORRATA PAGAS EXTRAS	CONTINGENCIAS COMUNES	273.25	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
129	10	aportacion_empresa	MEI	MECANISMO EQUIDAD INTERGENERACIONAL	7.75	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
130	10	aportacion_empresa	AT Y EP	AT Y EP	17.37	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
197	23	devengo	PAGA EXTRA	*PAGA EXTRA	197.33	t	t	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
131	10	aportacion_empresa	DESEMPLEO	DESEMPLEO	63.68	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
132	10	aportacion_empresa	FORMACIÓN PROFESIONAL	FORMACIÓN PROFESIONAL	6.96	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
133	10	aportacion_empresa	FONDO GARANTÍA SALARIAL	FONDO DE GARANTÍA SALARIAL	2.32	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
134	11	devengo	SALARIO BASE	*SALARIO BASE	601.14	t	t	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
135	11	devengo	HORAS NOCTURNAS	*HORAS NOCTURNAS	30.30	t	t	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
136	11	devengo	PAGA EXTRA	*PAGA EXTRA	148.65	t	t	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
137	11	devengo	ENFERMEDAD 60% EMP.	PREST. ENFERMEDAD CARGO EMPRESA	77.88	t	t	t	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
138	11	deduccion	DTO. CONT. COMUNES	COTIZACIÓN CONTINGENCIAS COMUNES (4,70%)	47.34	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
139	11	deduccion	MEI	COTIZACIÓN MECANISMO EQUIDAD INTERGENERACIONAL (0,13%)	1.31	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
140	11	deduccion	FORMACIÓN PROFESIONAL	COTIZACIÓN FORMACIÓN PROFESIONAL (0,10%)	1.01	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
141	11	deduccion	DESEMPLEO	COTIZACIÓN DESEMPLEO (1,55%)	15.61	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
142	11	aportacion_empresa	TOTAL CONTINGENCIAS COMUNES + PRORRATA PAGAS EXTRAS	BASE INCAPACIDAD TEMPORAL TOTAL	237.71	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
143	11	aportacion_empresa	MEI	MECANISMO EQUIDAD INTERGENERACIONAL	6.75	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
144	11	aportacion_empresa	AT Y EP	AT Y EP	15.11	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
145	11	aportacion_empresa	DESEMPLEO	DESEMPLEO	55.40	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
146	11	aportacion_empresa	FORMACIÓN PROFESIONAL	FORMACIÓN PROFESIONAL	6.04	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
147	11	aportacion_empresa	FONDO GARANTÍA SALARIAL	FONDO DE GARANTÍA SALARIAL	2.01	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
148	12	devengo	HORAS NOCTURNAS	*HORAS NOCTURNAS	28.28	t	t	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
149	12	devengo	ENFERMEDAD 60% EMP.	PREST. ENFERMEDAD CARGO EMPRESA	155.76	t	t	t	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
150	12	devengo	ENFERMEDAD 60% INS.	PREST. ENFERMEDAD	511.13	t	t	t	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
151	12	deduccion	DTO. CONT. COMUNES	COTIZACIÓN CONTINGENCIAS COMUNES (4,70%)	45.75	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
152	12	deduccion	MEI	COTIZACIÓN MECANISMO EQUIDAD INTERGENERACIONAL (0,13%)	1.27	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
153	12	deduccion	FORMACIÓN PROFESIONAL	COTIZACIÓN FORMACIÓN PROFESIONAL (0,10%)	0.97	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
154	12	deduccion	DESEMPLEO	COTIZACIÓN DESEMPLEO (1,55%)	15.09	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
155	12	aportacion_empresa	TOTAL CONTINGENCIAS COMUNES + PRORRATA PAGAS EXTRAS	BASE INCAPACIDAD TEMPORAL	229.75	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
156	12	aportacion_empresa	MEI	MECANISMO EQUIDAD INTERGENERACIONAL	6.52	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
157	12	aportacion_empresa	AT Y EP	AT Y EP	14.60	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
158	12	aportacion_empresa	DESEMPLEO	DESEMPLEO	53.54	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
159	12	aportacion_empresa	FORMACIÓN PROFESIONAL	FORMACIÓN PROFESIONAL	5.84	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
160	12	aportacion_empresa	FONDO GARANTÍA SALARIAL	FONDO DE GARANTÍA SALARIAL	1.95	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
161	13	devengo	SALARIO BASE	SALARIO BASE	225.43	t	t	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
162	13	devengo	PAGA EXTRA	PAGA EXTRA	55.75	t	t	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
163	13	devengo	ENFERMEDAD 60% EMP.	PREST. ENFERMEDAD	24.34	t	t	t	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
164	13	deduccion	DTO. CONT. COMUNES	COTIZACIÓN CONTINGENCIAS COMUNES (4,70%)	14.82	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
165	13	deduccion	MEI	COTIZACIÓN MECANISMO EQUIDAD INTERGENERACIONAL (0,13%)	0.41	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
166	13	deduccion	FORMACIÓN PROFESIONAL	COTIZACIÓN FORMACIÓN PROFESIONAL (0,10%)	0.32	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
167	13	deduccion	DESEMPLEO	COTIZACIÓN DESEMPLEO (1,55%)	4.89	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
168	13	aportacion_empresa	TOTAL CONTINGENCIAS COMUNES + PRORRATA PAGAS EXTRAS	CONTINGENCIAS COMUNES	74.42	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
169	13	aportacion_empresa	MEI	MECANISMO EQUIDAD INTERGENERACIONAL	2.11	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
170	13	aportacion_empresa	AT Y EP	AT Y EP	4.73	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
171	13	aportacion_empresa	DESEMPLEO	DESEMPLEO	17.34	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
172	13	aportacion_empresa	FORMACIÓN PROFESIONAL	FORMACIÓN PROFESIONAL	1.89	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
173	13	aportacion_empresa	FONDO GARANTÍA SALARIAL	FONDO DE GARANTÍA SALARIAL	0.63	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
174	14	devengo	RETR ADMINISTRADOR	*RETR ADMINISTRADOR	750.00	t	t	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
175	14	deduccion	RETENCION IRPF	TRIBUTACIÓN IRPF (35,00%)	262.50	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
176	15	devengo	RETR ADMINISTRADOR	*RETR ADMINISTRADOR	750.00	t	t	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
177	15	deduccion	RETENCION IRPF	TRIBUTACIÓN IRPF (35,00%)	262.50	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
178	16	devengo	RETR ADMINISTRADOR	*RETR ADMINISTRADOR	750.00	t	t	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
179	16	deduccion	RETENCION IRPF	TRIBUTACIÓN IRPF (35,00%)	262.50	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
180	17	devengo	RETR ADMINISTRADOR	*RETR ADMINISTRADOR	750.00	t	t	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
181	17	deduccion	RETENCION IRPF	TRIBUTACIÓN IRPF (35,00%)	262.50	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
182	18	devengo	RETR ADMINISTRADOR	*RETR ADMINISTRADOR	750.00	t	t	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
183	18	deduccion	RETENCION IRPF	TRIBUTACIÓN IRPF (35,00%)	262.50	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
184	19	devengo	RETR ADMINISTRADOR	*RETR ADMINISTRADOR	750.00	t	t	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
185	19	deduccion	RETENCION IRPF	TRIBUTACIÓN IRPF (35,00%)	262.50	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
186	20	devengo	RETR ADMINISTRADOR	*RETR ADMINISTRADOR	750.00	t	t	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
187	20	deduccion	RETENCION IRPF	TRIBUTACIÓN IRPF (35,00%)	262.50	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
188	21	devengo	SALARIO BASE	SALARIO BASE	1385.89	t	t	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
189	21	devengo	MEJORA VOLUNTARIA	MEJORA VOLUNTARIA	17.34	t	t	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
190	21	devengo	PAGA EXTRA	PAGA EXTRA	611.77	t	t	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
191	21	deduccion	RETENCION IRPF	TRIBUTACIÓN IRPF (11,00%)	221.65	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
192	22	devengo	SALARIO BASE	*SALARIO BASE	1385.89	t	t	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
193	22	devengo	MEJORA VOLUNTARIA	*MEJORA VOLUNTARIA	17.34	t	t	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
194	22	devengo	PAGA EXTRA	*PAGA EXTRA	611.77	t	t	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
195	22	deduccion	RETENCION IRPF	TRIBUTACIÓN IRPF (11,00%)	221.65	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
196	23	devengo	SALARIO BASE	*SALARIO BASE	1184.00	t	t	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
198	23	deduccion	RETENCION IRPF	TRIBUTACIÓN IRPF (2,91%)	40.20	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
199	24	devengo	SALARIO BASE	*SALARIO BASE	1470.29	t	t	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
200	24	devengo	PAGA EXTRA	*PAGA EXTRA	245.05	t	t	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
201	24	deduccion	RETENCION IRPF	TRIBUTACIÓN IRPF (2,91%)	49.92	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
202	25	devengo	SALARIO BASE	*SALARIO BASE	1470.29	t	t	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
203	25	devengo	PAGA EXTRA	*PAGA EXTRA	245.05	t	t	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
204	25	deduccion	RETENCION IRPF	TRIBUTACIÓN IRPF (2,91%)	49.92	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
205	26	devengo	SALARIO BASE	*SALARIO BASE	1470.29	t	t	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
206	26	devengo	PAGA EXTRA	*PAGA EXTRA	245.05	t	t	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
207	26	deduccion	RETENCION IRPF	TRIBUTACIÓN IRPF (2,91%)	49.92	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
208	27	devengo	SALARIO BASE	*SALARIO BASE	1470.29	t	t	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
209	27	devengo	PAGA EXTRA	*PAGA EXTRA	245.05	t	t	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
210	27	deduccion	RETENCION IRPF	TRIBUTACIÓN IRPF (2,91%)	49.92	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
211	28	devengo	SALARIO BASE	*SALARIO BASE	1470.29	t	t	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
212	28	devengo	PAGA EXTRA	*PAGA EXTRA	245.05	t	t	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
213	28	deduccion	RETENCION IRPF	TRIBUTACIÓN IRPF (2,91%)	49.92	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
214	29	devengo	SALARIO BASE	*SALARIO BASE	1470.29	t	t	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
215	29	devengo	PAGA EXTRA	*PAGA EXTRA	245.05	t	t	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
216	29	deduccion	RETENCION IRPF	TRIBUTACIÓN IRPF (15,00%)	257.30	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
217	30	devengo	SALARIO BASE	*SALARIO BASE	1470.29	t	t	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
218	30	devengo	PAGA EXTRA	*PAGA EXTRA	245.05	t	t	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
219	30	deduccion	RETENCION IRPF	TRIBUTACIÓN IRPF (15,00%)	257.30	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
220	31	devengo	SALARIO BASE	*SALARIO BASE	1470.29	t	t	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
221	31	devengo	PAGA EXTRA	*PAGA EXTRA	245.05	t	t	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
222	31	deduccion	RETENCION IRPF	TRIBUTACIÓN IRPF (15,00%)	257.30	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
223	32	devengo	SALARIO BASE	*SALARIO BASE	667.93	t	t	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
224	32	devengo	HORAS NOCTURNAS	*HORAS NOCTURNAS	13.13	t	t	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
225	32	devengo	PAGA EXTRA	*PAGA EXTRA	165.17	t	t	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
226	32	deduccion	DTO. CONT. COMUNES	COTIZACIÓN CONTINGENCIAS COMUNES (4,70%)	40.38	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
227	32	deduccion	MEI	COTIZACIÓN MECANISMO EQUIDAD INTERGENERACIONAL (0,13%)	1.12	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
228	32	deduccion	FORMACIÓN PROFESIONAL	COTIZACIÓN FORMACIÓN PROFESIONAL (0,10%)	0.85	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
229	32	deduccion	DESEMPLEO	COTIZACIÓN DESEMPLEO (1,55%)	13.31	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
230	32	aportacion_empresa	TOTAL CONTINGENCIAS COMUNES + PRORRATA PAGAS EXTRAS	BASE INCAPACIDAD TEMPORAL TOTAL	202.73	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
231	32	aportacion_empresa	MEI	MECANISMO EQUIDAD INTERGENERACIONAL	5.74	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
232	32	aportacion_empresa	AT Y EP	AT Y EP	12.87	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
233	32	aportacion_empresa	DESEMPLEO	DESEMPLEO	47.24	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
234	32	aportacion_empresa	FORMACIÓN PROFESIONAL	FORMACIÓN PROFESIONAL	5.16	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
235	32	aportacion_empresa	FONDO GARANTÍA SALARIAL	FONDO DE GARANTÍA SALARIAL	1.72	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
236	33	devengo	SALARIO BASE	*SALARIO BASE	702.93	t	t	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
237	33	devengo	HORAS NOCTURNAS	*HORAS NOCTURNAS	24.24	t	t	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
238	33	devengo	PAGA EXTRA	*PAGA EXTRA	173.82	t	t	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
239	33	deduccion	DTO. CONT. COMUNES	COTIZACIÓN CONTINGENCIAS COMUNES (4,70%)	44.52	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
240	33	deduccion	MEI	COTIZACIÓN MECANISMO EQUIDAD INTERGENERACIONAL (0,13%)	1.24	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
241	33	deduccion	FORMACIÓN PROFESIONAL	COTIZACIÓN FORMACIÓN PROFESIONAL (0,10%)	0.94	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
242	33	deduccion	DESEMPLEO	COTIZACIÓN DESEMPLEO (1,55%)	14.68	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
243	33	aportacion_empresa	TOTAL CONTINGENCIAS COMUNES + PRORRATA PAGAS EXTRAS	BASE INCAPACIDAD TEMPORAL TOTAL	223.56	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
244	33	aportacion_empresa	MEI	MECANISMO EQUIDAD INTERGENERACIONAL	6.34	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
245	33	aportacion_empresa	AT Y EP	AT Y EP	14.21	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
246	33	aportacion_empresa	DESEMPLEO	DESEMPLEO	52.10	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
247	33	aportacion_empresa	FORMACIÓN PROFESIONAL	FORMACIÓN PROFESIONAL	5.69	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
248	33	aportacion_empresa	FONDO GARANTÍA SALARIAL	FONDO DE GARANTÍA SALARIAL	1.90	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
249	34	devengo	SALARIO BASE	*SALARIO BASE	630.74	t	t	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
250	34	devengo	HORAS NOCTURNAS	*HORAS NOCTURNAS	23.23	t	t	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
251	34	devengo	HORAS COMPLEMENTARIAS	*HORAS COMPLEMENTARIAS	37.58	t	t	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
252	34	devengo	PAGA EXTRA	*PAGA EXTRA	155.97	t	t	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
253	34	deduccion	DTO. CONT. COMUNES	COTIZACIÓN CONTINGENCIAS COMUNES (4,70%)	39.83	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
254	34	deduccion	MEI	COTIZACIÓN MECANISMO EQUIDAD INTERGENERACIONAL (0,13%)	1.10	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
255	34	deduccion	DTO. SEGURIDAD SOCIAL	COTIZACIÓN FORMACIÓN PROFESIONAL (0,10%)	0.85	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
256	34	deduccion	DTO. SEGURIDAD SOCIAL	COTIZACIÓN DESEMPLEO (1,55%)	13.14	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
257	34	aportacion_empresa	TOTAL CONTINGENCIAS COMUNES + PRORRATA PAGAS EXTRAS	CONTINGENCIAS COMUNES	200.01	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
258	34	aportacion_empresa	MEI	MECANISMO EQUIDAD INTERGENERACIONAL	5.68	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
259	34	aportacion_empresa	AT Y EP	AT Y EP	12.71	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
260	34	aportacion_empresa	DESEMPLEO	DESEMPLEO	46.61	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
261	34	aportacion_empresa	FORMACIÓN PROFESIONAL	FORMACIÓN PROFESIONAL	5.09	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
262	34	aportacion_empresa	FONDO GARANTÍA SALARIAL	FONDO DE GARANTÍA SALARIAL	1.70	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
263	35	devengo	SALARIO BASE	*SALARIO BASE	660.89	t	t	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
264	35	devengo	HORAS NOCTURNAS	*HORAS NOCTURNAS	18.18	t	t	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
265	35	devengo	PAGA EXTRA	*PAGA EXTRA	163.43	t	t	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
266	35	deduccion	DTO. CONT. COMUNES	COTIZACIÓN CONTINGENCIAS COMUNES (4,70%)	40.75	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
267	35	deduccion	MEI	COTIZACIÓN MECANISMO EQUIDAD INTERGENERACIONAL (0,13%)	1.13	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
268	35	deduccion	FORMACIÓN PROFESIONAL	COTIZACIÓN FORMACIÓN PROFESIONAL (0,10%)	0.87	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
269	35	deduccion	DESEMPLEO	COTIZACIÓN DESEMPLEO (1,55%)	13.44	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
270	35	aportacion_empresa	TOTAL CONTINGENCIAS COMUNES + PRORRATA PAGAS EXTRAS	CONTINGENCIAS COMUNES	204.60	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
271	35	aportacion_empresa	MEI	MECANISMO EQUIDAD INTERGENERACIONAL	5.80	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
272	35	aportacion_empresa	AT Y EP	AT Y EP	13.00	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
273	35	aportacion_empresa	DESEMPLEO	DESEMPLEO	47.68	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
274	35	aportacion_empresa	FORMACIÓN PROFESIONAL	FORMACIÓN PROFESIONAL	5.21	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
275	35	aportacion_empresa	FONDO GARANTÍA SALARIAL	FONDO DE GARANTÍA SALARIAL	1.74	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
276	36	devengo	SALARIO BASE	*Salario Base	671.59	t	t	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
277	36	devengo	HORAS NOCTURNAS	*Horas nocturnas	23.23	t	t	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
278	36	devengo	PAGA EXTRA	*Paga Extra	166.08	t	t	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
279	36	deduccion	DTO. CONT. COMUNES	Cotización Contingencias Comunes (4,70%)	42.32	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
280	36	deduccion	MEI	Cotización Mecanismo Equidad Intergeneracional (0,13%)	1.17	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
281	36	deduccion	FORMACIÓN PROFESIONAL	Cotización Formación Profesional (0,10%)	0.90	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
282	36	deduccion	DESEMPLEO	Cotización Desempleo (1,55%)	13.96	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
283	36	aportacion_empresa	TOTAL CONTINGENCIAS COMUNES + PRORRATA PAGAS EXTRAS	Base Incapacidad Temporal Total	212.53	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
284	36	aportacion_empresa	MEI	Mecanismo Equidad Intergeneracional	6.04	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
285	36	aportacion_empresa	AT Y EP	AT y EP	13.51	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
286	36	aportacion_empresa	DESEMPLEO	Desempleo	49.53	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
287	36	aportacion_empresa	FORMACIÓN PROFESIONAL	Formación Profesional	5.41	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
288	36	aportacion_empresa	FONDO GARANTÍA SALARIAL	Fondo de garantía salarial	1.80	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
289	37	devengo	SALARIO BASE	*SALARIO BASE	730.03	t	t	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
290	37	devengo	HORAS NOCTURNAS	*HORAS NOCTURNAS	21.21	t	t	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
291	37	devengo	PAGA EXTRA	*PAGA EXTRA	180.54	t	t	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
292	37	deduccion	DTO. CONT. COMUNES	COTIZACIÓN CONTINGENCIAS COMUNES (4,70%)	44.49	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
293	37	deduccion	MEI	COTIZACIÓN MECANISMO EQUIDAD INTERGENERACIONAL (0,13%)	1.22	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
294	37	deduccion	FORMACIÓN PROFESIONAL	COTIZACIÓN FORMACIÓN PROFESIONAL (0,10%)	0.95	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
295	37	deduccion	DESEMPLEO	COTIZACIÓN DESEMPLEO (1,55%)	14.67	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
296	37	aportacion_empresa	TOTAL CONTINGENCIAS COMUNES + PRORRATA PAGAS EXTRAS	BASE INCAPACIDAD TEMPORAL TOTAL	223.34	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
297	37	aportacion_empresa	MEI	MECANISMO EQUIDAD INTERGENERACIONAL	6.35	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
298	37	aportacion_empresa	AT Y EP	AT Y EP	14.19	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
299	37	aportacion_empresa	DESEMPLEO	DESEMPLEO	52.05	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
300	37	aportacion_empresa	FORMACIÓN PROFESIONAL	FORMACIÓN PROFESIONAL	5.68	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
301	37	aportacion_empresa	FONDO GARANTÍA SALARIAL	FONDO DE GARANTÍA SALARIAL	1.89	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
302	38	devengo	SALARIO BASE	*SALARIO BASE	749.08	t	t	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
303	38	devengo	HORAS NOCTURNAS	*HORAS NOCTURNAS	29.29	t	t	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
304	38	devengo	HORAS COMPLEMENTARIAS	*HORAS COMPLEMENTARIAS	20.88	t	t	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
305	38	devengo	PAGA EXTRA	*PAGA EXTRA	185.24	t	t	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
306	38	deduccion	DTO. CONT. COMUNES	COTIZACIÓN CONTINGENCIAS COMUNES (4,70%)	50.36	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
307	38	deduccion	MEI	COTIZACIÓN MECANISMO EQUIDAD INTERGENERACIONAL (0,13%)	1.40	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
308	38	deduccion	FORMACIÓN PROFESIONAL	COTIZACIÓN FORMACIÓN PROFESIONAL (0,10%)	1.08	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
309	38	deduccion	DESEMPLEO	COTIZACIÓN DESEMPLEO (1,55%)	16.60	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
310	38	aportacion_empresa	TOTAL CONTINGENCIAS COMUNES + PRORRATA PAGAS EXTRAS	BASE INCAPACIDAD TEMPORAL TOTAL	252.86	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
311	38	aportacion_empresa	MEI	MECANISMO EQUIDAD INTERGENERACIONAL	7.17	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
312	38	aportacion_empresa	AT Y EP	AT Y EP	16.07	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
313	38	aportacion_empresa	DESEMPLEO	DESEMPLEO	58.93	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
314	38	aportacion_empresa	FORMACIÓN PROFESIONAL	FORMACIÓN PROFESIONAL	6.43	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
315	38	aportacion_empresa	FONDO GARANTÍA SALARIAL	FONDO DE GARANTÍA SALARIAL	2.14	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
316	39	devengo	SALARIO BASE	*SALARIO BASE	1166.22	t	t	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
317	39	devengo	HORAS NOCTURNAS	*HORAS NOCTURNAS	26.26	t	t	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
318	39	devengo	PAGA EXTRA	*PAGA EXTRA	288.38	t	t	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
319	39	deduccion	DTO. CONT. COMUNES	COTIZACIÓN CONTINGENCIAS COMUNES (4,70%)	70.60	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
320	39	deduccion	MEI	COTIZACIÓN MECANISMO EQUIDAD INTERGENERACIONAL (0,13%)	1.95	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
321	39	deduccion	FORMACIÓN PROFESIONAL	COTIZACIÓN FORMACIÓN PROFESIONAL (0,10%)	1.50	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
322	39	deduccion	DESEMPLEO	COTIZACIÓN DESEMPLEO (1,55%)	23.28	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
323	39	aportacion_empresa	TOTAL CONTINGENCIAS COMUNES + PRORRATA PAGAS EXTRAS	BASE INCAPACIDAD TEMPORAL TOTAL	354.48	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
324	39	aportacion_empresa	MEI	MECANISMO EQUIDAD INTERGENERACIONAL	10.06	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
325	39	aportacion_empresa	AT Y EP	AT Y EP	22.53	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
326	39	aportacion_empresa	DESEMPLEO	DESEMPLEO	82.60	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
327	39	aportacion_empresa	FORMACIÓN PROFESIONAL	FORMACIÓN PROFESIONAL	9.01	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
328	39	aportacion_empresa	FONDO GARANTÍA SALARIAL	FONDO DE GARANTÍA SALARIAL	3.01	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
329	40	devengo	SALARIO BASE	*SALARIO BASE	747.77	t	t	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
330	40	devengo	HORAS NOCTURNAS	*HORAS NOCTURNAS	38.38	t	t	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
331	40	devengo	PAGA EXTRA	*PAGA EXTRA	184.91	t	t	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
332	40	deduccion	DTO. CONT. COMUNES	COTIZACIÓN CONTINGENCIAS COMUNES (4,70%)	46.48	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
333	40	deduccion	MEI	COTIZACIÓN MECANISMO EQUIDAD INTERGENERACIONAL (0,13%)	1.29	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
334	40	deduccion	FORMACIÓN PROFESIONAL	COTIZACIÓN FORMACIÓN PROFESIONAL (0,10%)	0.99	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
335	40	deduccion	DESEMPLEO	COTIZACIÓN DESEMPLEO (1,55%)	15.33	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
336	40	aportacion_empresa	TOTAL CONTINGENCIAS COMUNES + PRORRATA PAGAS EXTRAS	BASE INCAPACIDAD TEMPORAL TOTAL	233.36	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
337	40	aportacion_empresa	MEI	MECANISMO EQUIDAD INTERGENERACIONAL	6.61	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
338	40	aportacion_empresa	AT Y EP	AT Y EP	14.82	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
339	40	aportacion_empresa	DESEMPLEO	DESEMPLEO	54.38	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
340	40	aportacion_empresa	FORMACIÓN PROFESIONAL	FORMACIÓN PROFESIONAL	5.93	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
341	40	aportacion_empresa	FONDO GARANTÍA SALARIAL	FONDO DE GARANTÍA SALARIAL	1.97	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
342	41	devengo	SALARIO BASE	*SALARIO BASE	630.89	t	t	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
343	41	devengo	HORAS NOCTURNAS	*HORAS NOCTURNAS	17.17	t	t	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
344	41	devengo	PAGA EXTRA	*PAGA EXTRA	156.01	t	t	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
345	41	deduccion	DTO. CONT. COMUNES	COTIZACIÓN CONTINGENCIAS COMUNES (4,70%)	40.98	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
346	41	deduccion	MEI	COTIZACIÓN MECANISMO EQUIDAD INTERGENERACIONAL (0,13%)	1.13	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
347	41	deduccion	FORMACIÓN PROFESIONAL	COTIZACIÓN FORMACIÓN PROFESIONAL (0,10%)	0.86	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
348	41	deduccion	DESEMPLEO	COTIZACIÓN DESEMPLEO (1,55%)	13.52	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
349	41	aportacion_empresa	TOTAL CONTINGENCIAS COMUNES + PRORRATA PAGAS EXTRAS	CONTINGENCIAS COMUNES	205.80	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
350	41	aportacion_empresa	MEI	MECANISMO EQUIDAD INTERGENERACIONAL	5.85	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
351	41	aportacion_empresa	AT Y EP	AT Y EP	13.08	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
352	41	aportacion_empresa	DESEMPLEO	DESEMPLEO	47.96	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
353	41	aportacion_empresa	FORMACIÓN PROFESIONAL	FORMACIÓN PROFESIONAL	5.24	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
354	41	aportacion_empresa	FONDO GARANTÍA SALARIAL	FONDO DE GARANTÍA SALARIAL	1.75	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
355	42	devengo	SALARIO BASE	*SALARIO BASE	652.80	t	t	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
356	42	devengo	HORAS NOCTURNAS	*HORAS NOCTURNAS	23.23	t	t	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
357	42	devengo	PAGA EXTRA	*PAGA EXTRA	161.42	t	t	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
358	42	deduccion	DTO. CONT. COMUNES	COTIZACIÓN CONTINGENCIAS COMUNES (4,70%)	39.36	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
359	42	deduccion	MEI	COTIZACIÓN MECANISMO EQUIDAD INTERGENERACIONAL (0,13%)	1.08	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
360	42	deduccion	FORMACIÓN PROFESIONAL	COTIZACIÓN FORMACIÓN PROFESIONAL (0,10%)	0.84	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
361	42	deduccion	DESEMPLEO	COTIZACIÓN DESEMPLEO (1,55%)	12.99	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
362	42	aportacion_empresa	TOTAL CONTINGENCIAS COMUNES + PRORRATA PAGAS EXTRAS	BASE INCAPACIDAD TEMPORAL TOTAL	197.64	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
363	42	aportacion_empresa	MEI	MECANISMO EQUIDAD INTERGENERACIONAL	5.62	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
364	42	aportacion_empresa	AT Y EP	AT Y EP	12.57	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
365	42	aportacion_empresa	DESEMPLEO	DESEMPLEO	46.06	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
366	42	aportacion_empresa	FORMACIÓN PROFESIONAL	FORMACIÓN PROFESIONAL	5.03	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
367	42	aportacion_empresa	FONDO GARANTÍA SALARIAL	FONDO DE GARANTÍA SALARIAL	1.67	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
368	43	devengo	SALARIO BASE	*SALARIO BASE	621.97	t	t	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
369	43	devengo	HORAS COMPLEMENTARIAS	*HORAS COMPLEMENTARIAS	45.93	t	t	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
370	43	devengo	PAGA EXTRA	*PAGA EXTRA	154.14	t	t	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
371	43	deduccion	DTO. CONT. COMUNES	COTIZACIÓN CONTINGENCIAS COMUNES (4,70%)	38.64	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
372	43	deduccion	MEI	COTIZACIÓN MECANISMO EQUIDAD INTERGENERACIONAL (0,13%)	1.07	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
373	43	deduccion	FORMACIÓN PROFESIONAL	COTIZACIÓN FORMACIÓN PROFESIONAL (0,10%)	0.82	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
374	43	deduccion	DESEMPLEO	COTIZACIÓN DESEMPLEO (1,55%)	12.74	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
375	43	aportacion_empresa	TOTAL CONTINGENCIAS COMUNES + PRORRATA PAGAS EXTRAS	CONTINGENCIAS COMUNES	194.00	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
376	43	aportacion_empresa	MEI	MECANISMO EQUIDAD INTERGENERACIONAL	5.51	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
377	43	aportacion_empresa	AT Y EP	AT Y EP	12.33	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
378	43	aportacion_empresa	DESEMPLEO	DESEMPLEO	45.21	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
379	43	aportacion_empresa	FORMACIÓN PROFESIONAL	FORMACIÓN PROFESIONAL	4.93	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
380	43	aportacion_empresa	FONDO GARANTÍA SALARIAL	FONDO DE GARANTIA SALARIAL	1.64	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
381	44	devengo	SALARIO BASE	*SALARIO BASE	621.97	t	t	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
382	44	devengo	HORAS NOCTURNAS	*HORAS NOCTURNAS	18.18	t	t	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
383	44	devengo	PAGA EXTRA	*PAGA EXTRA	154.14	t	t	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
384	44	deduccion	DTO. CONT. COMUNES	COTIZACIÓN CONTINGENCIAS COMUNES (4,70%)	37.33	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
385	44	deduccion	MEI	COTIZACIÓN MECANISMO EQUIDAD INTERGENERACIONAL (0,13%)	1.03	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
386	44	deduccion	FORMACIÓN PROFESIONAL	COTIZACIÓN FORMACIÓN PROFESIONAL (0,10%)	0.79	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
387	44	deduccion	DESEMPLEO	COTIZACIÓN DESEMPLEO (1,55%)	12.31	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
388	44	aportacion_empresa	TOTAL CONTINGENCIAS COMUNES + PRORRATA PAGAS EXTRAS	CONTINGENCIAS COMUNES	187.45	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
389	44	aportacion_empresa	MEI	MECANISMO EQUIDAD INTERGENERACIONAL	5.32	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
390	44	aportacion_empresa	AT Y EP	AT Y EP	11.91	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
391	44	aportacion_empresa	DESEMPLEO	DESEMPLEO	43.69	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
392	44	aportacion_empresa	FORMACIÓN PROFESIONAL	FORMACIÓN PROFESIONAL	4.77	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
393	44	aportacion_empresa	FONDO GARANTÍA SALARIAL	FONDO DE GARANTIA SALARIAL	1.59	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
394	45	devengo	SALARIO BASE	*SALARIO BASE	228.05	t	t	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
395	45	devengo	PAGA EXTRA	*PAGA EXTRA	56.52	t	t	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
396	45	deduccion	DTO. CONT. COMUNES	COTIZACIÓN CONTINGENCIAS COMUNES (4,70%)	13.37	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
397	45	deduccion	MEI	COTIZACIÓN MECANISMO EQUIDAD INTERGENERACIONAL (0,13%)	0.37	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
398	45	deduccion	FORMACIÓN PROFESIONAL	COTIZACIÓN FORMACIÓN PROFESIONAL (0,10%)	0.28	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
399	45	deduccion	DESEMPLEO	COTIZACIÓN DESEMPLEO (1,55%)	4.41	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
400	45	aportacion_empresa	TOTAL CONTINGENCIAS COMUNES + PRORRATA PAGAS EXTRAS	CONTINGENCIAS COMUNES	67.16	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
401	45	aportacion_empresa	MEI	MECANISMO EQUIDAD INTERGENERACIONAL	1.91	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
402	45	aportacion_empresa	AT Y EP	AT Y EP	4.27	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
403	45	aportacion_empresa	DESEMPLEO	DESEMPLEO	15.65	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
404	45	aportacion_empresa	FORMACIÓN PROFESIONAL	FORMACIÓN PROFESIONAL	1.71	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
405	45	aportacion_empresa	FONDO GARANTÍA SALARIAL	FONDO DE GARANTIA SALARIAL	0.57	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
406	46	devengo	SALARIO BASE	*SALARIO BASE	116.89	t	t	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
407	46	devengo	PAGA EXTRA	*PAGA EXTRA	28.91	t	t	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
408	46	deduccion	DTO. CONT. COMUNES	COTIZACIÓN CONTINGENCIAS COMUNES (4,70%)	6.85	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
409	46	deduccion	MEI	COTIZACIÓN MECANISMO EQUIDAD INTERGENERACIONAL (0,13%)	0.19	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
410	46	deduccion	FORMACIÓN PROFESIONAL	COTIZACIÓN FORMACIÓN PROFESIONAL (0,10%)	0.15	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
411	46	deduccion	DESEMPLEO	COTIZACIÓN DESEMPLEO (1,60%)	2.33	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
412	46	deduccion	RETENCION IRPF	TRIBUTACIÓN IRPF (2,00%)	2.92	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
413	46	aportacion_empresa	TOTAL CONTINGENCIAS COMUNES + PRORRATA PAGAS EXTRAS	CONTINGENCIAS COMUNES	34.41	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
414	46	aportacion_empresa	MEI	MECANISMO EQUIDAD INTERGENERACIONAL	0.98	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
415	46	aportacion_empresa	AT Y EP	AT Y EP	2.19	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
416	46	aportacion_empresa	DESEMPLEO	DESEMPLEO	9.77	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
417	46	aportacion_empresa	FORMACIÓN PROFESIONAL	FORMACIÓN PROFESIONAL	0.87	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
418	46	aportacion_empresa	FONDO GARANTÍA SALARIAL	FONDO DE GARANTÍA SALARIAL	0.29	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
419	47	devengo	SALARIO BASE	*SALARIO BASE	411.24	t	t	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
420	47	devengo	HORAS NOCTURNAS	*HORAS NOCTURNAS	10.10	t	t	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
421	47	devengo	PAGA EXTRA	*PAGA EXTRA	101.69	t	t	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
422	47	deduccion	DTO. CONT. COMUNES	COTIZACIÓN CONTINGENCIAS COMUNES (4,70%)	27.36	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
423	47	deduccion	MEI	COTIZACIÓN MECANISMO EQUIDAD INTERGENERACIONAL (0,13%)	0.76	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
424	47	deduccion	FORMACIÓN PROFESIONAL	COTIZACIÓN FORMACIÓN PROFESIONAL (0,10%)	0.57	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
425	47	deduccion	DESEMPLEO	COTIZACIÓN DESEMPLEO (1,55%)	9.01	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
426	47	deduccion	RETENCION IRPF	TRIBUTACIÓN IRPF (2,00%)	10.45	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
427	47	aportacion_empresa	TOTAL CONTINGENCIAS COMUNES + PRORRATA PAGAS EXTRAS	BASE INCAPACIDAD TEMPORAL TOTAL	137.35	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
428	47	aportacion_empresa	MEI	MECANISMO EQUIDAD INTERGENERACIONAL	3.89	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
429	47	aportacion_empresa	AT Y EP	AT Y EP	8.72	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
430	47	aportacion_empresa	DESEMPLEO	DESEMPLEO	32.01	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
431	47	aportacion_empresa	FORMACIÓN PROFESIONAL	FORMACIÓN PROFESIONAL	3.50	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
432	47	aportacion_empresa	FONDO GARANTÍA SALARIAL	FONDO DE GARANTÍA SALARIAL	1.17	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
433	48	devengo	SALARIO BASE	SALARIO BASE	531.73	t	t	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
434	48	devengo	HORAS NOCTURNAS	HORAS NOCTURNAS	33.33	t	t	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
435	48	devengo	PAGA EXTRA	PAGA EXTRA	131.49	t	t	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
436	48	deduccion	DTO. CONT. COMUNES	COTIZACIÓN CONTINGENCIAS COMUNES (4,70%)	33.19	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
437	48	deduccion	MEI	COTIZACIÓN MECANISMO EQUIDAD INTERGENERACIONAL (0,13%)	0.92	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
438	48	deduccion	FORMACIÓN PROFESIONAL	COTIZACIÓN FORMACIÓN PROFESIONAL (0,10%)	0.71	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
439	48	deduccion	DESEMPLEO	COTIZACIÓN DESEMPLEO (1,55%)	10.94	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
440	48	deduccion	RETENCION IRPF	TRIBUTACIÓN IRPF (2,00%)	13.92	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
441	48	aportacion_empresa	TOTAL CONTINGENCIAS COMUNES + PRORRATA PAGAS EXTRAS	BASE INCAPACIDAD TEMPORAL TOTAL	166.64	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
442	48	aportacion_empresa	MEI	MECANISMO EQUIDAD INTERGENERACIONAL	4.73	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
443	48	aportacion_empresa	AT Y EP	AT Y EP	10.59	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
444	48	aportacion_empresa	DESEMPLEO	DESEMPLEO	38.83	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
445	48	aportacion_empresa	FORMACIÓN PROFESIONAL	FORMACIÓN PROFESIONAL	4.25	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
446	48	aportacion_empresa	FONDO GARANTÍA SALARIAL	FONDO DE GARANTÍA SALARIAL	1.42	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
447	49	devengo	SALARIO BASE	SALARIO BASE	91.32	t	t	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
448	49	devengo	PAGA EXTRA	PAGA EXTRA	22.58	t	t	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
449	49	deduccion	DTO. CONT. COMUNES	COTIZACIÓN CONTINGENCIAS COMUNES (4,70%)	5.35	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
450	49	deduccion	MEI	COTIZACIÓN MECANISMO EQUIDAD INTERGENERACIONAL (0,13%)	0.15	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
451	49	deduccion	FORMACIÓN PROFESIONAL	COTIZACIÓN FORMACIÓN PROFESIONAL (0,10%)	0.11	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
452	49	deduccion	DESEMPLEO	COTIZACIÓN DESEMPLEO (1,55%)	1.77	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
453	49	deduccion	RETENCION IRPF	TRIBUTACIÓN IRPF (2,00%)	2.28	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
454	49	aportacion_empresa	TOTAL CONTINGENCIAS COMUNES + PRORRATA PAGAS EXTRAS	CONTINGENCIAS COMUNES	26.88	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
455	49	aportacion_empresa	MEI	MECANISMO EQUIDAD INTERGENERACIONAL	0.76	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
456	49	aportacion_empresa	AT Y EP	AT Y EP	1.71	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
457	49	aportacion_empresa	DESEMPLEO	DESEMPLEO	6.26	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
458	49	aportacion_empresa	FORMACIÓN PROFESIONAL	FORMACIÓN PROFESIONAL	0.68	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
459	49	aportacion_empresa	FONDO GARANTÍA SALARIAL	FONDO DE GARANTÍA SALARIAL	0.23	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
460	50	devengo	SALARIO BASE	*SALARIO BASE	328.49	t	t	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
461	50	devengo	HORAS NOCTURNAS	*HORAS NOCTURNAS	13.13	t	t	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
462	50	deduccion	DTO. CONT. COMUNES	COTIZACIÓN CONTINGENCIAS COMUNES (4,70%)	17.08	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
463	50	deduccion	MEI	COTIZACIÓN MECANISMO EQUIDAD INTERGENERACIONAL (0,13%)	0.47	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
464	50	deduccion	FORMACIÓN PROFESIONAL	COTIZACIÓN FORMACIÓN PROFESIONAL (0,10%)	0.36	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
465	50	deduccion	DESEMPLEO	COTIZACIÓN DESEMPLEO (1,55%)	5.63	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
466	50	deduccion	RETENCION IRPF	TRIBUTACIÓN IRPF (2,00%)	6.83	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
467	50	aportacion_empresa	TOTAL CONTINGENCIAS COMUNES + PRORRATA PAGAS EXTRAS	BASE INCAPACIDAD TEMPORAL TOTAL	85.75	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
468	50	aportacion_empresa	MEI	MECANISMO EQUIDAD INTERGENERACIONAL	2.43	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
469	50	aportacion_empresa	AT Y EP	AT Y EP	5.44	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
470	50	aportacion_empresa	DESEMPLEO	DESEMPLEO	19.98	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
471	50	aportacion_empresa	FORMACIÓN PROFESIONAL	FORMACIÓN PROFESIONAL	2.18	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
472	50	aportacion_empresa	FONDO GARANTÍA SALARIAL	FONDO DE GARANTÍA SALARIAL	0.73	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
473	51	devengo	SALARIO BASE	*SALARIO BASE	22.77	t	t	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
474	51	deduccion	DTO. CONT. COMUNES	COTIZACIÓN CONTINGENCIAS COMUNES (4,70%)	1.12	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
475	51	deduccion	MEI	COTIZACIÓN MECANISMO EQUIDAD INTERGENERACIONAL (0,13%)	0.03	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
476	51	deduccion	FORMACIÓN PROFESIONAL	COTIZACIÓN FORMACIÓN PROFESIONAL (0,10%)	0.02	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
477	51	deduccion	DESEMPLEO	COTIZACIÓN DESEMPLEO (1,55%)	0.37	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
478	51	aportacion_empresa	TOTAL CONTINGENCIAS COMUNES + PRORRATA PAGAS EXTRAS	BASE INCAPACIDAD TEMPORAL TOTAL	5.64	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
479	51	aportacion_empresa	MEI	MECANISMO EQUIDAD INTERGENERACIONAL	0.16	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
480	51	aportacion_empresa	AT Y EP	AT Y EP	0.36	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
481	51	aportacion_empresa	DESEMPLEO	DESEMPLEO	1.32	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
482	51	aportacion_empresa	FORMACIÓN PROFESIONAL	FORMACIÓN PROFESIONAL	0.14	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
483	51	aportacion_empresa	FONDO GARANTÍA SALARIAL	FONDO DE GARANTIA SALARIAL	0.05	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
484	52	devengo	SALARIO BASE	*SALARIO BASE	212.91	t	t	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
485	52	devengo	PAGA EXTRA	*PAGA EXTRA	52.65	t	t	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
486	52	deduccion	DTO. CONT. COMUNES	COTIZACIÓN CONTINGENCIAS COMUNES (4,70%)	12.89	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
487	52	deduccion	MEI	COTIZACIÓN MECANISMO EQUIDAD INTERGENERACIONAL (0,13%)	0.35	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
488	52	deduccion	FORMACIÓN PROFESIONAL	COTIZACIÓN FORMACIÓN PROFESIONAL (0,10%)	0.28	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
489	52	deduccion	DESEMPLEO	COTIZACIÓN DESEMPLEO (1,55%)	4.25	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
490	52	deduccion	RETENCION IRPF	TRIBUTACIÓN IRPF (2,00%)	5.32	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
491	52	aportacion_empresa	TOTAL CONTINGENCIAS COMUNES + PRORRATA PAGAS EXTRAS	BASE INCAPACIDAD TEMPORAL TOTAL	64.76	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
492	52	aportacion_empresa	MEI	MECANISMO EQUIDAD INTERGENERACIONAL	1.84	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
493	52	aportacion_empresa	AT Y EP	AT Y EP	4.12	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
494	52	aportacion_empresa	DESEMPLEO	DESEMPLEO	15.09	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
495	52	aportacion_empresa	FORMACIÓN PROFESIONAL	FORMACIÓN PROFESIONAL	1.65	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
496	52	aportacion_empresa	FONDO GARANTÍA SALARIAL	FONDO DE GARANTÍA SALARIAL	0.55	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
497	53	devengo	SALARIO BASE	*SALARIO BASE	490.77	t	t	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
498	53	devengo	HORAS NOCTURNAS	*HORAS NOCTURNAS	15.15	t	t	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
499	53	devengo	PAGA EXTRA	*PAGA EXTRA	121.36	t	t	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
500	53	deduccion	DTO. CONT. COMUNES	COTIZACIÓN CONTINGENCIAS COMUNES (4,70%)	32.53	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
501	53	deduccion	MEI	COTIZACIÓN MECANISMO EQUIDAD INTERGENERACIONAL (0,13%)	0.89	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
502	53	deduccion	FORMACIÓN PROFESIONAL	COTIZACIÓN FORMACIÓN PROFESIONAL (0,10%)	0.69	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
503	53	deduccion	DESEMPLEO	COTIZACIÓN DESEMPLEO (1,55%)	10.74	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
504	53	deduccion	RETENCION IRPF	TRIBUTACIÓN IRPF (2,00%)	12.55	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
505	53	aportacion_empresa	TOTAL CONTINGENCIAS COMUNES + PRORRATA PAGAS EXTRAS	CONTINGENCIAS COMUNES	163.33	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
506	53	aportacion_empresa	MEI	MECANISMO EQUIDAD INTERGENERACIONAL	4.65	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
507	53	aportacion_empresa	AT Y EP	AT Y EP	10.39	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
508	53	aportacion_empresa	DESEMPLEO	DESEMPLEO	38.07	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
509	53	aportacion_empresa	FORMACIÓN PROFESIONAL	FORMACIÓN PROFESIONAL	4.16	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
510	53	aportacion_empresa	FONDO GARANTÍA SALARIAL	FONDO DE GARANTÍA SALARIAL	1.39	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
511	54	devengo	SALARIO BASE	*SALARIO BASE	253.09	t	t	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
512	54	devengo	PAGA EXTRA	*PAGA EXTRA	62.58	t	t	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
513	54	deduccion	DTO. CONT. COMUNES	COTIZACIÓN CONTINGENCIAS COMUNES (4,70%)	15.30	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
514	54	deduccion	MEI	COTIZACIÓN MECANISMO EQUIDAD INTERGENERACIONAL (0,13%)	0.42	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
515	54	deduccion	FORMACIÓN PROFESIONAL	COTIZACIÓN FORMACIÓN PROFESIONAL (0,10%)	0.32	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
516	54	deduccion	DESEMPLEO	COTIZACIÓN DESEMPLEO (1,55%)	5.06	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
517	54	deduccion	RETENCION IRPF	TRIBUTACIÓN IRPF (2,00%)	6.32	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
518	54	aportacion_empresa	TOTAL CONTINGENCIAS COMUNES + PRORRATA PAGAS EXTRAS	CONTINGENCIAS COMUNES	76.82	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
519	54	aportacion_empresa	MEI	MECANISMO EQUIDAD INTERGENERACIONAL	2.19	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
520	54	aportacion_empresa	AT Y EP	AT Y EP	4.88	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
521	54	aportacion_empresa	DESEMPLEO	DESEMPLEO	17.90	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
522	54	aportacion_empresa	FORMACIÓN PROFESIONAL	FORMACIÓN PROFESIONAL	1.95	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
523	54	aportacion_empresa	FONDO GARANTÍA SALARIAL	FONDO DE GARANTÍA SALARIAL	0.66	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
524	55	devengo	SALARIO BASE	*SALARIO BASE	294.83	t	t	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
525	55	devengo	HORAS NOCTURNAS	*HORAS NOCTURNAS	15.15	t	t	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
526	55	devengo	PAGA EXTRA	*PAGA EXTRA	72.91	t	t	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
527	55	deduccion	DTO. CONT. COMUNES	COTIZACIÓN CONTINGENCIAS COMUNES (4,70%)	18.83	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
528	55	deduccion	MEI	COTIZACIÓN MECANISMO EQUIDAD INTERGENERACIONAL (0,13%)	0.52	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
529	55	deduccion	FORMACIÓN PROFESIONAL	COTIZACIÓN FORMACIÓN PROFESIONAL (0,10%)	0.40	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
530	55	deduccion	DESEMPLEO	COTIZACIÓN DESEMPLEO (1,55%)	6.21	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
531	55	deduccion	RETENCION IRPF	TRIBUTACIÓN IRPF (2,00%)	7.66	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
532	55	aportacion_empresa	TOTAL CONTINGENCIAS COMUNES + PRORRATA PAGAS EXTRAS	BASE INCAPACIDAD TEMPORAL TOTAL	94.55	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
533	55	aportacion_empresa	MEI	MECANISMO EQUIDAD INTERGENERACIONAL	2.68	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
534	55	aportacion_empresa	AT Y EP	AT Y EP	6.01	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
535	55	aportacion_empresa	DESEMPLEO	DESEMPLEO	22.03	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
536	55	aportacion_empresa	FORMACIÓN PROFESIONAL	FORMACIÓN PROFESIONAL	2.40	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
537	55	aportacion_empresa	FONDO GARANTÍA SALARIAL	FONDO DE GARANTÍA SALARIAL	0.80	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
538	56	devengo	SALARIO BASE	*SALARIO BASE	682.28	t	t	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
539	56	devengo	NOCTURNIDAD	*HORAS NOCTURNAS	31.31	t	t	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
540	56	devengo	PAGA EXTRA	*PAGA EXTRA	168.72	t	t	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
541	56	deduccion	DTO. CONT. COMUNES	COTIZACIÓN CONTINGENCIAS COMUNES (4,70%)	45.57	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
542	56	deduccion	MEI	COTIZACIÓN MECANISMO EQUIDAD INTERGENERACIONAL (0,13%)	1.25	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
543	56	deduccion	DTO. SEGURIDAD SOCIAL	COTIZACIÓN FORMACIÓN PROFESIONAL (0,10%)	0.96	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
544	56	deduccion	DTO. SEGURIDAD SOCIAL	COTIZACIÓN DESEMPLEO (1,55%)	15.03	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
545	56	deduccion	RETENCION IRPF	TRIBUTACIÓN IRPF (2,00%)	17.66	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
546	56	aportacion_empresa	TOTAL CONTINGENCIAS COMUNES + PRORRATA PAGAS EXTRAS	BASE INCAPACIDAD TEMPORAL TOTAL	228.80	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
547	56	aportacion_empresa	MEI	MECANISMO EQUIDAD INTERGENERACIONAL	6.50	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
548	56	aportacion_empresa	AT Y EP	AT Y EP	14.53	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
549	56	aportacion_empresa	DESEMPLEO	DESEMPLEO	53.31	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
550	56	aportacion_empresa	FORMACIÓN PROFESIONAL	FORMACIÓN PROFESIONAL	5.82	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
551	56	aportacion_empresa	FONDO GARANTÍA SALARIAL	FONDO DE GARANTÍA SALARIAL	1.95	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
552	57	devengo	SALARIO BASE	*SALARIO BASE	94.97	t	t	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
553	57	devengo	PAGA EXTRA	*PAGA EXTRA	23.48	t	t	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
554	57	deduccion	DTO. CONT. COMUNES	COTIZACIÓN CONTINGENCIAS COMUNES (4,70%)	7.43	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
555	57	deduccion	MEI	COTIZACIÓN MECANISMO EQUIDAD INTERGENERACIONAL (0,13%)	0.21	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
556	57	deduccion	DTO. SEGURIDAD SOCIAL	COTIZACIÓN FORMACIÓN PROFESIONAL (0,10%)	0.16	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
557	57	deduccion	DTO. SEGURIDAD SOCIAL	COTIZACIÓN DESEMPLEO (1,55%)	2.45	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
558	57	deduccion	RETENCION IRPF	TRIBUTACIÓN IRPF (2,00%)	2.37	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
559	57	aportacion_empresa	TOTAL CONTINGENCIAS COMUNES + PRORRATA PAGAS EXTRAS	BASE INCAPACIDAD TEMPORAL TOTAL	37.31	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
560	57	aportacion_empresa	MEI	MECANISMO EQUIDAD INTERGENERACIONAL	1.05	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
561	57	aportacion_empresa	AT Y EP	AT Y EP	2.37	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
562	57	aportacion_empresa	DESEMPLEO	DESEMPLEO	8.69	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
563	57	aportacion_empresa	FORMACIÓN PROFESIONAL	FORMACIÓN PROFESIONAL	0.95	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
564	57	aportacion_empresa	FONDO GARANTÍA SALARIAL	FONDO DE GARANTÍA SALARIAL	0.32	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
565	58	devengo	SALARIO BASE	*SALARIO BASE	206.38	t	t	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
566	58	devengo	VACACIONES	*VACACIONES	441.24	t	t	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
567	58	devengo	PAGA EXTRA	*PAGA EXTRA	51.03	t	t	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
568	58	deduccion	DTO. CONT. COMUNES	COTIZACIÓN CONTINGENCIAS COMUNES (4,70%)	32.84	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
569	58	deduccion	MEI	COTIZACIÓN MECANISMO EQUIDAD INTERGENERACIONAL (0,13%)	0.91	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
570	58	deduccion	FORMACIÓN PROFESIONAL	COTIZACIÓN FORMACIÓN PROFESIONAL (0,10%)	0.70	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
571	58	deduccion	DESEMPLEO	COTIZACIÓN DESEMPLEO (1,55%)	10.83	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
572	58	aportacion_empresa	TOTAL CONTINGENCIAS COMUNES + PRORRATA PAGAS EXTRAS	CONTINGENCIAS COMUNES	164.88	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
573	58	aportacion_empresa	MEI	MECANISMO EQUIDAD INTERGENERACIONAL	4.68	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
574	58	aportacion_empresa	AT Y EP	AT Y EP	10.48	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
575	58	aportacion_empresa	DESEMPLEO	DESEMPLEO	38.43	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
576	58	aportacion_empresa	FORMACIÓN PROFESIONAL	FORMACIÓN PROFESIONAL	4.19	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
577	58	aportacion_empresa	FONDO GARANTÍA SALARIAL	FONDO DE GARANTÍA SALARIAL	1.40	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
578	59	devengo	VACACIONES NO DISFRUTADAS	PARTE PROPORCIONAL VACACIONES	45.74	t	t	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
579	59	deduccion	DTO. CONT. COMUNES	COTIZACIÓN CONTINGENCIAS COMUNES (4,70%)	3.68	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
580	59	deduccion	MEI	COTIZACIÓN MECANISMO EQUIDAD INTERGENERACIONAL (0,13%)	0.10	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
581	59	deduccion	FORMACIÓN PROFESIONAL	COTIZACIÓN FORMACIÓN PROFESIONAL (0,10%)	0.08	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
582	59	deduccion	DESEMPLEO	COTIZACIÓN DESEMPLEO (1,55%)	1.21	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
583	59	deduccion	RETENCION IRPF	TRIBUTACIÓN IRPF (2,00%)	0.91	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
584	59	aportacion_empresa	TOTAL CONTINGENCIAS COMUNES + PRORRATA PAGAS EXTRAS	CONTINGENCIAS COMUNES	18.47	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
585	59	aportacion_empresa	MEI	MECANISMO EQUIDAD INTERGENERACIONAL	0.53	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
586	59	aportacion_empresa	AT Y EP	AT Y EP	1.18	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
587	59	aportacion_empresa	DESEMPLEO	DESEMPLEO	4.30	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
588	59	aportacion_empresa	FORMACIÓN PROFESIONAL	FORMACIÓN PROFESIONAL	0.47	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
589	59	aportacion_empresa	FONDO GARANTÍA SALARIAL	FONDO DE GARANTÍA SALARIAL	0.16	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
590	60	devengo	VACACIONES NO DISFRUTADAS	PARTE PROPORCIONAL VACACIONES	89.16	t	t	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
591	60	deduccion	DTO. CONT. COMUNES	COTIZACIÓN CONTINGENCIAS COMUNES (4,70%)	4.76	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
592	60	deduccion	MEI	COTIZACIÓN MECANISMO EQUIDAD INTERGENERACIONAL (0,13%)	0.13	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
593	60	deduccion	FORMACIÓN PROFESIONAL	COTIZACIÓN FORMACIÓN PROFESIONAL (0,10%)	0.11	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
594	60	deduccion	DESEMPLEO	COTIZACIÓN DESEMPLEO (1,55%)	1.57	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
595	60	aportacion_empresa	TOTAL CONTINGENCIAS COMUNES + PRORRATA PAGAS EXTRAS	BASE INCAPACIDAD TEMPORAL TOTAL	23.91	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
596	60	aportacion_empresa	MEI	MECANISMO EQUIDAD INTERGENERACIONAL	0.68	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
597	60	aportacion_empresa	AT Y EP	AT Y EP	1.52	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
598	60	aportacion_empresa	DESEMPLEO	DESEMPLEO	5.57	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
599	60	aportacion_empresa	FORMACIÓN PROFESIONAL	FORMACIÓN PROFESIONAL	0.61	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
600	60	aportacion_empresa	FONDO GARANTÍA SALARIAL	FONDO DE GARANTIA SALARIAL	0.20	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
601	61	devengo	PARTE PROPORCIONAL VACACIONES FINIQUITO	PARTE PROPORCIONAL VACACIONES	267.50	t	t	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
602	61	deduccion	DTO. CONT. COMUNES	COTIZACIÓN CONTINGENCIAS COMUNES (4,70%)	14.51	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
603	61	deduccion	MEI	COTIZACIÓN MECANISMO EQUIDAD INTERGENERACIONAL (0,13%)	0.40	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
604	61	deduccion	FORMACIÓN PROFESIONAL	COTIZACIÓN FORMACIÓN PROFESIONAL (0,10%)	0.31	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
605	61	deduccion	DESEMPLEO	COTIZACIÓN DESEMPLEO (1,55%)	4.78	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
606	61	deduccion	RETENCION IRPF	TRIBUTACIÓN IRPF (5,23%)	13.99	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
607	61	aportacion_empresa	TOTAL CONTINGENCIAS COMUNES + PRORRATA PAGAS EXTRAS	BASE INCAPACIDAD TEMPORAL TOTAL	72.85	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
608	61	aportacion_empresa	MEI	MECANISMO EQUIDAD INTERGENERACIONAL	2.07	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
609	61	aportacion_empresa	AT Y EP	AT Y EP	4.63	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
610	61	aportacion_empresa	DESEMPLEO	DESEMPLEO	16.98	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
611	61	aportacion_empresa	FORMACIÓN PROFESIONAL	FORMACIÓN PROFESIONAL	1.85	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
612	61	aportacion_empresa	FONDO GARANTÍA SALARIAL	FONDO DE GARANTÍA SALARIAL	0.62	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
613	62	devengo	SALARIO BASE	*SALARIO BASE	243.18	t	t	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
614	62	devengo	HORAS NOCTURNAS	*HORAS NOCTURNAS	13.13	t	t	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
615	62	devengo	PAGA EXTRA	*PAGA EXTRA	60.13	t	t	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
616	62	deduccion	DTO. CONT. COMUNES	COTIZACIÓN CONTINGENCIAS COMUNES (4,70%)	14.87	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
617	62	deduccion	MEI	COTIZACIÓN MECANISMO EQUIDAD INTERGENERACIONAL (0,13%)	0.41	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
618	62	deduccion	FORMACIÓN PROFESIONAL	COTIZACIÓN FORMACIÓN PROFESIONAL (0,10%)	0.32	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
619	62	deduccion	DESEMPLEO	COTIZACIÓN DESEMPLEO (1,55%)	4.90	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
620	62	aportacion_empresa	TOTAL CONTINGENCIAS COMUNES + PRORRATA PAGAS EXTRAS	BASE INCAPACIDAD TEMPORAL TOTAL	74.68	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
621	62	aportacion_empresa	MEI	MECANISMO EQUIDAD INTERGENERACIONAL	2.12	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
622	62	aportacion_empresa	AT Y EP	AT Y EP	4.75	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
623	62	aportacion_empresa	DESEMPLEO	DESEMPLEO	17.40	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
624	62	aportacion_empresa	FORMACIÓN PROFESIONAL	FORMACIÓN PROFESIONAL	1.90	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
625	62	aportacion_empresa	FONDO GARANTÍA SALARIAL	FONDO DE GARANTÍA SALARIAL	0.63	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
626	63	devengo	SALARIO BASE	SALARIO BASE	178.33	t	t	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
627	63	devengo	HORAS NOCTURNAS	HORAS NOCTURNAS	13.13	t	t	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
628	63	devengo	HORAS COMPLEMENTARIAS	HORAS COMPLEMENTARIAS	27.14	t	t	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
629	63	devengo	PAGA EXTRA	PAGA EXTRA	44.10	t	t	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
630	63	deduccion	DTO. CONT. COMUNES	COTIZACIÓN CONTINGENCIAS COMUNES (4,70%)	12.35	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
631	63	deduccion	MEI	COTIZACIÓN MECANISMO EQUIDAD INTERGENERACIONAL (0,13%)	0.34	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
632	63	deduccion	FORMACIÓN PROFESIONAL	COTIZACIÓN FORMACIÓN PROFESIONAL (0,10%)	0.26	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
633	63	deduccion	DESEMPLEO	COTIZACIÓN DESEMPLEO (1,55%)	4.07	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
634	63	aportacion_empresa	TOTAL CONTINGENCIAS COMUNES + PRORRATA PAGAS EXTRAS	CONTINGENCIAS COMUNES	62.00	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
635	63	aportacion_empresa	MEI	MECANISMO EQUIDAD INTERGENERACIONAL	1.76	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
636	63	aportacion_empresa	AT Y EP	AT Y EP	3.94	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
637	63	aportacion_empresa	DESEMPLEO	DESEMPLEO	14.45	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
638	63	aportacion_empresa	FORMACIÓN PROFESIONAL	FORMACIÓN PROFESIONAL	1.58	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
639	63	aportacion_empresa	FONDO GARANTÍA SALARIAL	FONDO DE GARANTÍA SALARIAL	0.53	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
640	64	devengo	SALARIO BASE	*SALARIO BASE	1033.51	t	t	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
641	64	devengo	PAGA EXTRA	*PAGA EXTRA	255.57	t	t	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
642	64	deduccion	DTO. CONT. COMUNES	COTIZACIÓN CONTINGENCIAS COMUNES (4,70%)	60.59	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
643	64	deduccion	MEI	COTIZACIÓN MECANISMO EQUIDAD INTERGENERACIONAL (0,13%)	1.68	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
644	64	deduccion	FORMACIÓN PROFESIONAL	COTIZACIÓN FORMACIÓN PROFESIONAL (0,10%)	1.29	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
645	64	deduccion	DESEMPLEO	COTIZACIÓN DESEMPLEO (1,55%)	19.98	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
646	64	aportacion_empresa	TOTAL CONTINGENCIAS COMUNES + PRORRATA PAGAS EXTRAS	CONTINGENCIAS COMUNES	304.22	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
647	64	aportacion_empresa	MEI	MECANISMO EQUIDAD INTERGENERACIONAL	8.63	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
648	64	aportacion_empresa	AT Y EP	AT Y EP	19.33	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
649	64	aportacion_empresa	DESEMPLEO	DESEMPLEO	70.90	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
650	64	aportacion_empresa	FORMACIÓN PROFESIONAL	FORMACIÓN PROFESIONAL	7.73	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
651	64	aportacion_empresa	FONDO GARANTÍA SALARIAL	FONDO DE GARANTÍA SALARIAL	2.58	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
652	65	devengo	SALARIO BASE	SALARIO BASE	1033.51	t	t	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
653	65	devengo	PAGA EXTRA	PAGA EXTRA	255.57	t	t	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
654	65	deduccion	DTO. CONT. COMUNES	COTIZACIÓN CONTINGENCIAS COMUNES (4,70%)	60.59	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
655	65	deduccion	MEI	COTIZACIÓN MECANISMO EQUIDAD INTERGENERACIONAL (0,13%)	1.68	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
656	65	deduccion	FORMACIÓN PROFESIONAL	COTIZACIÓN FORMACIÓN PROFESIONAL (0,10%)	1.29	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
657	65	deduccion	DESEMPLEO	COTIZACIÓN DESEMPLEO (1,55%)	19.98	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
658	65	aportacion_empresa	TOTAL CONTINGENCIAS COMUNES + PRORRATA PAGAS EXTRAS	BASE INCAPACIDAD TEMPORAL TOTAL	304.22	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
659	65	aportacion_empresa	MEI	MECANISMO EQUIDAD INTERGENERACIONAL	8.63	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
660	65	aportacion_empresa	AT Y EP	AT Y EP	19.33	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
661	65	aportacion_empresa	DESEMPLEO	DESEMPLEO	70.90	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
662	65	aportacion_empresa	FORMACIÓN PROFESIONAL	FORMACIÓN PROFESIONAL	7.73	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
663	65	aportacion_empresa	FONDO GARANTÍA SALARIAL	FONDO DE GARANTÍA SALARIAL	2.58	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
664	66	devengo	SALARIO BASE	SALARIO BASE	1064.51	t	t	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
665	66	devengo	PAGA EXTRA	PAGA EXTRA	263.24	t	t	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
666	66	deduccion	DTO. CONT. COMUNES	COTIZACIÓN CONTINGENCIAS COMUNES (4,70%)	62.40	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
667	66	deduccion	MEI	COTIZACIÓN MECANISMO EQUIDAD INTERGENERACIONAL (0,13%)	1.73	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
668	66	deduccion	FORMACIÓN PROFESIONAL	COTIZACIÓN FORMACIÓN PROFESIONAL (0,10%)	1.33	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
669	66	deduccion	DESEMPLEO	COTIZACIÓN DESEMPLEO (1,55%)	20.58	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
670	66	aportacion_empresa	TOTAL CONTINGENCIAS COMUNES + PRORRATA PAGAS EXTRAS	BASE INCAPACIDAD TEMPORAL TOTAL	313.35	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
671	66	aportacion_empresa	MEI	MECANISMO EQUIDAD INTERGENERACIONAL	8.89	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
672	66	aportacion_empresa	AT Y EP	AT Y EP	19.91	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
673	66	aportacion_empresa	DESEMPLEO	DESEMPLEO	73.03	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
674	66	aportacion_empresa	FORMACIÓN PROFESIONAL	FORMACIÓN PROFESIONAL	7.97	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
675	66	aportacion_empresa	FONDO GARANTÍA SALARIAL	FONDO DE GARANTÍA SALARIAL	2.66	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
676	67	devengo	SALARIO BASE	*SALARIO BASE	1064.51	t	t	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
677	67	devengo	PAGA EXTRA	*PAGA EXTRA	263.24	t	t	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
678	67	deduccion	DTO. CONT. COMUNES	COTIZACIÓN CONTINGENCIAS COMUNES (4,70%)	62.40	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
679	67	deduccion	MEI	COTIZACIÓN MECANISMO EQUIDAD INTERGENERACIONAL (0,13%)	1.73	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
680	67	deduccion	FORMACIÓN PROFESIONAL	COTIZACIÓN FORMACIÓN PROFESIONAL (0,10%)	1.33	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
681	67	deduccion	DESEMPLEO	COTIZACIÓN DESEMPLEO (1,55%)	20.58	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
682	67	aportacion_empresa	TOTAL CONTINGENCIAS COMUNES + PRORRATA PAGAS EXTRAS	BASE INCAPACIDAD TEMPORAL TOTAL	313.35	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
683	67	aportacion_empresa	MEI	MECANISMO EQUIDAD INTERGENERACIONAL	8.89	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
684	67	aportacion_empresa	AT Y EP	AT Y EP	19.91	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
685	67	aportacion_empresa	DESEMPLEO	DESEMPLEO	73.03	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
686	67	aportacion_empresa	FORMACIÓN PROFESIONAL	FORMACIÓN PROFESIONAL	7.97	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
687	67	aportacion_empresa	FONDO GARANTÍA SALARIAL	FONDO DE GARANTÍA SALARIAL	2.66	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
688	68	devengo	SALARIO BASE	SALARIO BASE	1064.51	t	t	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
689	68	devengo	PAGA EXTRA	PAGA EXTRA	263.24	t	t	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
690	68	deduccion	DTO. CONT. COMUNES	COTIZACIÓN CONTINGENCIAS COMUNES (4,70%)	62.40	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
691	68	deduccion	MEI	COTIZACIÓN MECANISMO EQUIDAD INTERGENERACIONAL (0,13%)	1.73	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
692	68	deduccion	FORMACIÓN PROFESIONAL	COTIZACIÓN FORMACIÓN PROFESIONAL (0,10%)	1.33	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
693	68	deduccion	DESEMPLEO	COTIZACIÓN DESEMPLEO (1,55%)	20.58	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
694	68	aportacion_empresa	TOTAL CONTINGENCIAS COMUNES + PRORRATA PAGAS EXTRAS	BASE INCAPACIDAD TEMPORAL TOTAL	313.35	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
695	68	aportacion_empresa	MEI	MECANISMO EQUIDAD INTERGENERACIONAL	8.89	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
696	68	aportacion_empresa	AT Y EP	AT Y EP	19.91	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
697	68	aportacion_empresa	DESEMPLEO	DESEMPLEO	73.03	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
698	68	aportacion_empresa	FORMACIÓN PROFESIONAL	FORMACIÓN PROFESIONAL	7.97	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
699	68	aportacion_empresa	FONDO GARANTÍA SALARIAL	FONDO DE GARANTÍA SALARIAL	2.66	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
700	69	devengo	SALARIO BASE	SALARIO BASE	1064.51	t	t	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
701	69	devengo	PAGA EXTRA	PAGA EXTRA	263.24	t	t	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
702	69	deduccion	DTO. CONT. COMUNES	COTIZACIÓN CONTINGENCIAS COMUNES (4,70%)	62.40	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
703	69	deduccion	MEI	COTIZACIÓN MECANISMO EQUIDAD INTERGENERACIONAL (0,13%)	1.73	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
704	69	deduccion	FORMACIÓN PROFESIONAL	COTIZACIÓN FORMACIÓN PROFESIONAL (0,10%)	1.33	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
705	69	deduccion	DESEMPLEO	COTIZACIÓN DESEMPLEO (1,55%)	20.58	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
706	69	aportacion_empresa	TOTAL CONTINGENCIAS COMUNES + PRORRATA PAGAS EXTRAS	BASE INCAPACIDAD TEMPORAL TOTAL	313.35	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
707	69	aportacion_empresa	MEI	MECANISMO EQUIDAD INTERGENERACIONAL	8.89	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
708	69	aportacion_empresa	AT Y EP	AT Y EP	19.91	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
709	69	aportacion_empresa	DESEMPLEO	DESEMPLEO	73.03	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
710	69	aportacion_empresa	FORMACIÓN PROFESIONAL	FORMACIÓN PROFESIONAL	7.97	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
711	69	aportacion_empresa	FONDO GARANTÍA SALARIAL	FONDO DE GARANTÍA SALARIAL	2.66	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
712	70	devengo	SALARIO BASE	*SALARIO BASE	1064.51	t	t	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
713	70	devengo	PAGA EXTRA	*PAGA EXTRA	263.24	t	t	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
714	70	deduccion	DTO. CONT. COMUNES	COTIZACIÓN CONTINGENCIAS COMUNES (4,70%)	62.40	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
715	70	deduccion	MEI	COTIZACIÓN MECANISMO EQUIDAD INTERGENERACIONAL (0,13%)	1.73	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
716	70	deduccion	FORMACIÓN PROFESIONAL	COTIZACIÓN FORMACIÓN PROFESIONAL (0,10%)	1.33	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
717	70	deduccion	DESEMPLEO	COTIZACIÓN DESEMPLEO (1,55%)	20.58	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
782	75	aportacion_empresa	AT Y EP	AT Y EP	25.65	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
718	70	aportacion_empresa	TOTAL CONTINGENCIAS COMUNES + PRORRATA PAGAS EXTRAS	BASE INCAPACIDAD TEMPORAL TOTAL	313.35	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
719	70	aportacion_empresa	MEI	MECANISMO EQUIDAD INTERGENERACIONAL	8.89	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
720	70	aportacion_empresa	AT Y EP	AT Y EP	19.91	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
721	70	aportacion_empresa	DESEMPLEO	DESEMPLEO	73.03	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
722	70	aportacion_empresa	FORMACIÓN PROFESIONAL	FORMACIÓN PROFESIONAL	7.97	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
723	70	aportacion_empresa	FONDO GARANTÍA SALARIAL	FONDO DE GARANTÍA SALARIAL	2.66	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
724	71	devengo	SALARIO BASE	*SALARIO BASE	1033.51	t	t	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
725	71	devengo	PAGA EXTRA	*PAGA EXTRA	255.57	t	t	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
726	71	deduccion	DTO. CONT. COMUNES	COTIZACIÓN CONTINGENCIAS COMUNES (4,70%)	60.59	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
727	71	deduccion	MEI	COTIZACIÓN MECANISMO EQUIDAD INTERGENERACIONAL (0,13%)	1.68	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
728	71	deduccion	FORMACIÓN PROFESIONAL	COTIZACIÓN FORMACIÓN PROFESIONAL (0,10%)	1.29	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
729	71	deduccion	DESEMPLEO	COTIZACIÓN DESEMPLEO (1,55%)	19.98	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
730	71	aportacion_empresa	TOTAL CONTINGENCIAS COMUNES + PRORRATA PAGAS EXTRAS	BASE INCAPACIDAD TEMPORAL TOTAL	304.22	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
731	71	aportacion_empresa	MEI	MECANISMO EQUIDAD INTERGENERACIONAL	8.63	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
732	71	aportacion_empresa	AT Y EP	AT Y EP	19.33	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
733	71	aportacion_empresa	DESEMPLEO	DESEMPLEO	70.90	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
734	71	aportacion_empresa	FORMACIÓN PROFESIONAL	FORMACIÓN PROFESIONAL	7.73	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
735	71	aportacion_empresa	FONDO GARANTÍA SALARIAL	FONDO DE GARANTÍA SALARIAL	2.58	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
736	72	devengo	SALARIO BASE	*SALARIO BASE	1064.51	t	t	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
737	72	devengo	PAGA EXTRA	*PAGA EXTRA	263.24	t	t	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
738	72	deduccion	DTO. CONT. COMUNES	COTIZACIÓN CONTINGENCIAS COMUNES (4,70%)	62.40	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
739	72	deduccion	MEI	COTIZACIÓN MECANISMO EQUIDAD INTERGENERACIONAL (0,13%)	1.73	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
740	72	deduccion	FORMACIÓN PROFESIONAL	COTIZACIÓN FORMACIÓN PROFESIONAL (0,10%)	1.33	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
741	72	deduccion	DESEMPLEO	COTIZACIÓN DESEMPLEO (1,55%)	20.58	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
742	72	aportacion_empresa	TOTAL CONTINGENCIAS COMUNES + PRORRATA PAGAS EXTRAS	CONTINGENCIAS COMUNES	313.35	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
743	72	aportacion_empresa	MEI	MECANISMO EQUIDAD INTERGENERACIONAL	8.89	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
744	72	aportacion_empresa	AT Y EP	AT Y EP	19.91	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
745	72	aportacion_empresa	DESEMPLEO	DESEMPLEO	73.03	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
746	72	aportacion_empresa	FORMACIÓN PROFESIONAL	FORMACIÓN PROFESIONAL	7.97	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
747	72	aportacion_empresa	FONDO GARANTÍA SALARIAL	FONDO DE GARANTÍA SALARIAL	2.66	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
748	73	devengo	SALARIO BASE	*SALARIO BASE	1064.51	t	t	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
749	73	devengo	PAGA EXTRA	*PAGA EXTRA	263.24	t	t	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
750	73	deduccion	DTO. CONT. COMUNES	COTIZACIÓN CONTINGENCIAS COMUNES (4,70%)	62.40	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
751	73	deduccion	MEI	COTIZACIÓN MECANISMO EQUIDAD INTERGENERACIONAL (0,13%)	1.73	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
752	73	deduccion	DTO. BASE ACCIDENTE	COTIZACIÓN FORMACIÓN PROFESIONAL (0,10%)	1.33	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
753	73	deduccion	DTO. SEGURIDAD SOCIAL	COTIZACIÓN DESEMPLEO (1,55%)	20.58	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
754	73	aportacion_empresa	TOTAL CONTINGENCIAS COMUNES + PRORRATA PAGAS EXTRAS	BASE INCAPACIDAD TEMPORAL TOTAL	313.35	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
755	73	aportacion_empresa	MEI	MECANISMO EQUIDAD INTERGENERACIONAL	8.89	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
756	73	aportacion_empresa	AT Y EP	AT Y EP	19.91	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
757	73	aportacion_empresa	DESEMPLEO	DESEMPLEO	73.03	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
758	73	aportacion_empresa	FORMACIÓN PROFESIONAL	FORMACIÓN PROFESIONAL	7.97	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
759	73	aportacion_empresa	FONDO GARANTÍA SALARIAL	FONDO DE GARANTÍA SALARIAL	2.66	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
760	74	devengo	SALARIO BASE	*SALARIO BASE	1064.51	t	t	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
761	74	devengo	PAGA EXTRA	*PAGA EXTRA	263.24	t	t	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
762	74	deduccion	DTO. CONT. COMUNES	COTIZACIÓN CONTINGENCIAS COMUNES (4,70%)	62.40	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
763	74	deduccion	MEI	COTIZACIÓN MECANISMO EQUIDAD INTERGENERACIONAL (0,13%)	1.73	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
764	74	deduccion	FORMACIÓN PROFESIONAL	COTIZACIÓN FORMACIÓN PROFESIONAL (0,10%)	1.33	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
765	74	deduccion	DESEMPLEO	COTIZACIÓN DESEMPLEO (1,55%)	20.58	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
766	74	aportacion_empresa	TOTAL CONTINGENCIAS COMUNES + PRORRATA PAGAS EXTRAS	BASE INCAPACIDAD TEMPORAL TOTAL	313.35	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
767	74	aportacion_empresa	MEI	MECANISMO EQUIDAD INTERGENERACIONAL	8.89	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
768	74	aportacion_empresa	AT Y EP	AT Y EP	19.91	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
769	74	aportacion_empresa	DESEMPLEO	DESEMPLEO	73.03	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
770	74	aportacion_empresa	FORMACIÓN PROFESIONAL	FORMACIÓN PROFESIONAL	7.97	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
771	74	aportacion_empresa	FONDO GARANTÍA SALARIAL	FONDO DE GARANTÍA SALARIAL	2.66	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
772	75	devengo	SALARIO BASE	*SALARIO BASE	1359.38	t	t	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
773	75	devengo	HORAS NOCTURNAS	*HORAS NOCTURNAS	26.26	t	t	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
774	75	devengo	PAGA EXTRA	*PAGA EXTRA	324.58	t	t	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
775	75	deduccion	DTO. CONT. COMUNES	COTIZACIÓN CONTINGENCIAS COMUNES (4,70%)	80.38	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
776	75	deduccion	MEI	COTIZACIÓN MECANISMO EQUIDAD INTERGENERACIONAL (0,13%)	2.22	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
777	75	deduccion	FORMACIÓN PROFESIONAL	COTIZACIÓN FORMACIÓN PROFESIONAL (0,10%)	1.71	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
778	75	deduccion	DESEMPLEO	COTIZACIÓN DESEMPLEO (1,55%)	26.51	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
779	75	deduccion	RETENCION IRPF	TRIBUTACIÓN IRPF (9,21%)	157.51	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
780	75	aportacion_empresa	TOTAL CONTINGENCIAS COMUNES + PRORRATA PAGAS EXTRAS	BASE INCAPACIDAD TEMPORAL TOTAL	403.61	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
781	75	aportacion_empresa	MEI	MECANISMO EQUIDAD INTERGENERACIONAL	11.46	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
783	75	aportacion_empresa	DESEMPLEO	DESEMPLEO	94.06	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
784	75	aportacion_empresa	FORMACIÓN PROFESIONAL	FORMACIÓN PROFESIONAL	10.26	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
785	75	aportacion_empresa	FONDO GARANTÍA SALARIAL	FONDO DE GARANTÍA SALARIAL	3.42	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
786	76	devengo	SALARIO BASE	*SALARIO BASE	1359.38	t	t	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
787	76	devengo	HORAS NOCTURNAS	*HORAS NOCTURNAS	32.32	t	t	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
788	76	devengo	PAGA EXTRA	*PAGA EXTRA	324.58	t	t	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
789	76	deduccion	DTO. CONT. COMUNES	COTIZACIÓN CONTINGENCIAS COMUNES (4,70%)	80.67	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
790	76	deduccion	MEI	COTIZACIÓN MECANISMO EQUIDAD INTERGENERACIONAL (0,13%)	2.23	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
791	76	deduccion	FORMACIÓN PROFESIONAL	COTIZACIÓN FORMACIÓN PROFESIONAL (0,10%)	1.72	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
792	76	deduccion	DESEMPLEO	COTIZACIÓN DESEMPLEO (1,55%)	26.60	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
793	76	deduccion	RETENCION IRPF	TRIBUTACIÓN IRPF (8,20%)	140.73	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
794	76	aportacion_empresa	TOTAL CONTINGENCIAS COMUNES + PRORRATA PAGAS EXTRAS	BASE INCAPACIDAD TEMPORAL TOTAL	405.04	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
795	76	aportacion_empresa	MEI	MECANISMO EQUIDAD INTERGENERACIONAL	11.50	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
796	76	aportacion_empresa	AT Y EP	AT Y EP	25.74	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
797	76	aportacion_empresa	DESEMPLEO	DESEMPLEO	94.40	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
798	76	aportacion_empresa	FORMACIÓN PROFESIONAL	FORMACIÓN PROFESIONAL	10.30	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
799	76	aportacion_empresa	FONDO GARANTÍA SALARIAL	FONDO DE GARANTÍA SALARIAL	3.43	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
800	77	devengo	SALARIO BASE	SALARIO BASE	1359.38	t	t	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
801	77	devengo	HORAS NOCTURNAS	HORAS NOCTURNAS	18.18	t	t	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
802	77	devengo	PAGA EXTRA	PAGA EXTRA	324.58	t	t	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
803	77	deduccion	DTO. CONT. COMUNES	COTIZACIÓN CONTINGENCIAS COMUNES (4,70%)	80.00	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
804	77	deduccion	MEI	COTIZACIÓN MECANISMO EQUIDAD INTERGENERACIONAL (0,13%)	2.21	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
805	77	deduccion	FORMACIÓN PROFESIONAL	COTIZACIÓN FORMACIÓN PROFESIONAL (0,10%)	1.70	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
806	77	deduccion	DESEMPLEO	COTIZACIÓN DESEMPLEO (1,55%)	26.38	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
807	77	deduccion	RETENCION IRPF	TRIBUTACIÓN IRPF (8,20%)	139.58	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
808	77	aportacion_empresa	TOTAL CONTINGENCIAS COMUNES + PRORRATA PAGAS EXTRAS	BASE INCAPACIDAD TEMPORAL TOTAL	401.71	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
809	77	aportacion_empresa	MEI	MECANISMO EQUIDAD INTERGENERACIONAL	11.41	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
810	77	aportacion_empresa	AT Y EP	AT Y EP	25.53	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
811	77	aportacion_empresa	DESEMPLEO	DESEMPLEO	93.62	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
812	77	aportacion_empresa	FORMACIÓN PROFESIONAL	FORMACIÓN PROFESIONAL	10.21	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
813	77	aportacion_empresa	FONDO GARANTÍA SALARIAL	FONDO DE GARANTÍA SALARIAL	3.40	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
814	78	devengo	SALARIO BASE	*SALARIO BASE	1400.16	t	t	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
815	78	devengo	HORAS NOCTURNAS	*HORAS NOCTURNAS	23.23	t	t	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
816	78	devengo	PAGA EXTRA	*PAGA EXTRA	334.33	t	t	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
817	78	deduccion	DTO. CONT. COMUNES	COTIZACIÓN CONTINGENCIAS COMUNES (4,70%)	82.61	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
818	78	deduccion	MEI	COTIZACIÓN MECANISMO EQUIDAD INTERGENERACIONAL (0,13%)	2.29	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
819	78	deduccion	FORMACIÓN PROFESIONAL	COTIZACIÓN FORMACIÓN PROFESIONAL (0,10%)	1.76	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
820	78	deduccion	DESEMPLEO	COTIZACIÓN DESEMPLEO (1,55%)	27.24	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
821	78	deduccion	RETENCION IRPF	TRIBUTACIÓN IRPF (8,20%)	144.13	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
822	78	aportacion_empresa	TOTAL CONTINGENCIAS COMUNES + PRORRATA PAGAS EXTRAS	BASE INCAPACIDAD TEMPORAL TOTAL	414.82	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
823	78	aportacion_empresa	MEI	MECANISMO EQUIDAD INTERGENERACIONAL	11.77	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
824	78	aportacion_empresa	AT Y EP	AT Y EP	26.36	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
825	78	aportacion_empresa	DESEMPLEO	DESEMPLEO	96.67	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
826	78	aportacion_empresa	FORMACIÓN PROFESIONAL	FORMACIÓN PROFESIONAL	10.55	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
827	78	aportacion_empresa	FONDO GARANTÍA SALARIAL	FONDO DE GARANTÍA SALARIAL	3.52	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
828	79	devengo	SALARIO BASE	*Salario Base	1400.16	t	t	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
829	79	devengo	HORAS NOCTURNAS	*Horas nocturnas	32.32	t	t	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
830	79	devengo	PAGA EXTRA	*Paga Extra	334.33	t	t	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
831	79	deduccion	DTO. CONT. COMUNES	Cotización Contingencias Comunes (4,70%)	83.04	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
832	79	deduccion	MEI	Cotización Mecanismo Equidad Intergeneracional (0,13%)	2.30	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
833	79	deduccion	FORMACIÓN PROFESIONAL	Cotización Formación Profesional (0,10%)	1.77	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
834	79	deduccion	DESEMPLEO	Cotización Desempleo (1,55%)	27.39	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
835	79	deduccion	RETENCION IRPF	Tributación IRPF (8,20%)	144.88	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
836	79	aportacion_empresa	TOTAL CONTINGENCIAS COMUNES + PRORRATA PAGAS EXTRAS	Base Incapacidad Temporal Total	416.97	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
837	79	aportacion_empresa	MEI	Mecanismo Equidad Intergeneracional	11.83	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
838	79	aportacion_empresa	AT Y EP	AT y EP	26.50	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
839	79	aportacion_empresa	DESEMPLEO	Desempleo	97.17	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
840	79	aportacion_empresa	FORMACIÓN PROFESIONAL	Formación Profesional	10.60	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
841	79	aportacion_empresa	FONDO GARANTÍA SALARIAL	Fondo de garantía salarial	3.53	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
842	80	devengo	SALARIO BASE	*SALARIO BASE	1400.16	t	t	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
843	80	devengo	HORAS NOCTURNAS	*HORAS NOCTURNAS	32.32	t	t	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
844	80	devengo	PAGA EXTRA	*PAGA EXTRA	334.33	t	t	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
845	80	deduccion	DTO. CONT. COMUNES	COTIZACIÓN CONTINGENCIAS COMUNES (4,70%)	83.04	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
846	80	deduccion	MEI	COTIZACIÓN MECANISMO EQUIDAD INTERGENERACIONAL (0,13%)	2.30	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
847	80	deduccion	FORMACIÓN PROFESIONAL	COTIZACIÓN FORMACIÓN PROFESIONAL (0,10%)	1.77	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
848	80	deduccion	DESEMPLEO	COTIZACIÓN DESEMPLEO (1,55%)	27.39	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
849	80	deduccion	RETENCION IRPF	TRIBUTACIÓN IRPF (8,20%)	144.88	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
850	80	aportacion_empresa	TOTAL CONTINGENCIAS COMUNES + PRORRATA PAGAS EXTRAS	BASE INCAPACIDAD TEMPORAL TOTAL	416.97	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
851	80	aportacion_empresa	MEI	MECANISMO EQUIDAD INTERGENERACIONAL	11.83	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
852	80	aportacion_empresa	AT Y EP	AT Y EP	26.50	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
853	80	aportacion_empresa	DESEMPLEO	DESEMPLEO	97.17	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
854	80	aportacion_empresa	FORMACIÓN PROFESIONAL	FORMACIÓN PROFESIONAL	10.60	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
855	80	aportacion_empresa	FONDO GARANTÍA SALARIAL	FONDO DE GARANTÍA SALARIAL	3.53	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
856	81	devengo	SALARIO BASE	*Salario Base	1400.16	t	t	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
857	81	devengo	HORAS NOCTURNAS	*Horas nocturnas	27.27	t	t	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
858	81	devengo	PAGA EXTRA	*Paga Extra	334.33	t	t	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
859	81	deduccion	DTO. CONT. COMUNES	Cotización Contingencias Comunes (4,70%)	82.80	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
860	81	deduccion	MEI	Cotización Mecanismo Equidad Intergeneracional (0,13%)	2.29	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
861	81	deduccion	FORMACIÓN PROFESIONAL	Cotización Formación Profesional (0,10%)	1.76	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
862	81	deduccion	DESEMPLEO	Cotización Desempleo (1,55%)	27.31	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
863	81	deduccion	RETENCION IRPF	Tributación IRPF (8,20%)	144.46	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
864	81	aportacion_empresa	TOTAL CONTINGENCIAS COMUNES + PRORRATA PAGAS EXTRAS	Base Incapacidad Temporal Total	415.78	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
865	81	aportacion_empresa	MEI	Mecanismo Equidad Intergeneracional	11.80	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
866	81	aportacion_empresa	AT Y EP	AT y EP	26.42	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
867	81	aportacion_empresa	DESEMPLEO	Desempleo	96.90	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
868	81	aportacion_empresa	FORMACIÓN PROFESIONAL	Formación Profesional	10.57	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
869	81	aportacion_empresa	FONDO GARANTÍA SALARIAL	Fondo de garantía salarial	3.52	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
870	82	devengo	SALARIO BASE	*SALARIO BASE	1400.16	t	t	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
871	82	devengo	HORAS NOCTURNAS	*HORAS NOCTURNAS	39.39	t	t	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
872	82	devengo	PAGA EXTRA	*PAGA EXTRA	334.33	t	t	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
873	82	deduccion	DTO. CONT. COMUNES	COTIZACIÓN CONTINGENCIAS COMUNES (4,70%)	83.37	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
874	82	deduccion	MEI	COTIZACIÓN MECANISMO EQUIDAD INTERGENERACIONAL (0,13%)	2.31	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
875	82	deduccion	FORMACIÓN PROFESIONAL	COTIZACIÓN FORMACIÓN PROFESIONAL (0,10%)	1.77	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
876	82	deduccion	DESEMPLEO	COTIZACIÓN DESEMPLEO (1,55%)	27.50	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
877	82	deduccion	RETENCION IRPF	TRIBUTACIÓN IRPF (8,20%)	145.46	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
878	82	aportacion_empresa	TOTAL CONTINGENCIAS COMUNES + PRORRATA PAGAS EXTRAS	BASE INCAPACIDAD TEMPORAL TOTAL	418.64	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
879	82	aportacion_empresa	MEI	MECANISMO EQUIDAD INTERGENERACIONAL	11.88	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
880	82	aportacion_empresa	AT Y EP	AT Y EP	26.61	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
881	82	aportacion_empresa	DESEMPLEO	DESEMPLEO	97.56	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
882	82	aportacion_empresa	FORMACIÓN PROFESIONAL	FORMACIÓN PROFESIONAL	10.64	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
883	82	aportacion_empresa	FONDO GARANTÍA SALARIAL	FONDO DE GARANTÍA SALARIAL	3.55	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
884	83	devengo	SALARIO BASE	*SALARIO BASE	1400.16	t	t	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
885	83	devengo	HORAS NOCTURNAS	*HORAS NOCTURNAS	35.35	t	t	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
886	83	devengo	PAGA EXTRA	*PAGA EXTRA	334.33	t	t	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
887	83	deduccion	DTO. CONT. COMUNES	COTIZACIÓN CONTINGENCIAS COMUNES (4,70%)	83.18	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
888	83	deduccion	MEI	COTIZACIÓN MECANISMO EQUIDAD INTERGENERACIONAL (0,13%)	2.30	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
889	83	deduccion	FORMACIÓN PROFESIONAL	COTIZACIÓN FORMACIÓN PROFESIONAL (0,10%)	1.77	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
890	83	deduccion	DESEMPLEO	COTIZACIÓN DESEMPLEO (1,55%)	27.43	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
891	83	deduccion	RETENCION IRPF	TRIBUTACIÓN IRPF (8,20%)	145.13	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
892	83	aportacion_empresa	TOTAL CONTINGENCIAS COMUNES + PRORRATA PAGAS EXTRAS	BASE INCAPACIDAD TEMPORAL TOTAL	417.68	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
893	83	aportacion_empresa	MEI	MECANISMO EQUIDAD INTERGENERACIONAL	11.86	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
894	83	aportacion_empresa	AT Y EP	AT Y EP	26.55	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
895	83	aportacion_empresa	DESEMPLEO	DESEMPLEO	97.34	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
896	83	aportacion_empresa	FORMACIÓN PROFESIONAL	FORMACIÓN PROFESIONAL	10.62	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
897	83	aportacion_empresa	FONDO GARANTÍA SALARIAL	FONDO DE GARANTÍA SALARIAL	3.54	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
898	84	devengo	SALARIO BASE	*SALARIO BASE	1400.16	t	t	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
899	84	devengo	HORAS NOCTURNAS	*HORAS NOCTURNAS	26.26	t	t	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
900	84	devengo	PAGA EXTRA	*PAGA EXTRA	334.33	t	t	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
901	84	deduccion	DTO. CONT. COMUNES	COTIZACIÓN CONTINGENCIAS COMUNES (4,70%)	82.76	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
902	84	deduccion	MEI	COTIZACIÓN MECANISMO EQUIDAD INTERGENERACIONAL (0,13%)	2.29	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
903	84	deduccion	FORMACIÓN PROFESIONAL	COTIZACIÓN FORMACIÓN PROFESIONAL (0,10%)	1.76	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
904	84	deduccion	DESEMPLEO	COTIZACIÓN DESEMPLEO (1,55%)	27.29	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
905	84	deduccion	RETENCION IRPF	TRIBUTACIÓN IRPF (8,20%)	144.38	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
906	84	aportacion_empresa	TOTAL CONTINGENCIAS COMUNES + PRORRATA PAGAS EXTRAS	BASE INCAPACIDAD TEMPORAL TOTAL	415.54	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
907	84	aportacion_empresa	MEI	MECANISMO EQUIDAD INTERGENERACIONAL	11.80	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
908	84	aportacion_empresa	AT Y EP	AT Y EP	26.42	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
909	84	aportacion_empresa	DESEMPLEO	DESEMPLEO	96.84	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
910	84	aportacion_empresa	FORMACIÓN PROFESIONAL	FORMACIÓN PROFESIONAL	10.56	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
911	84	aportacion_empresa	FONDO GARANTÍA SALARIAL	FONDO DE GARANTÍA SALARIAL	3.52	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
912	85	devengo	SALARIO BASE	*SALARIO BASE	1400.16	t	t	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
913	85	devengo	HORAS NOCTURNAS	*HORAS NOCTURNAS	40.40	t	t	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
914	85	devengo	PAGA EXTRA	*PAGA EXTRA	334.33	t	t	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
915	85	deduccion	DTO. CONT. COMUNES	COTIZACIÓN CONTINGENCIAS COMUNES (4,70%)	83.42	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
916	85	deduccion	MEI	COTIZACIÓN MECANISMO EQUIDAD INTERGENERACIONAL (0,13%)	2.31	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
917	85	deduccion	FORMACIÓN PROFESIONAL	COTIZACIÓN FORMACIÓN PROFESIONAL (0,10%)	1.77	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
918	85	deduccion	DESEMPLEO	COTIZACIÓN DESEMPLEO (1,55%)	27.51	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
919	85	deduccion	RETENCION IRPF	TRIBUTACIÓN IRPF (8,20%)	145.54	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
920	85	aportacion_empresa	TOTAL CONTINGENCIAS COMUNES + PRORRATA PAGAS EXTRAS	BASE INCAPACIDAD TEMPORAL TOTAL	418.87	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
921	85	aportacion_empresa	MEI	MECANISMO EQUIDAD INTERGENERACIONAL	11.89	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
922	85	aportacion_empresa	AT Y EP	AT Y EP	26.62	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
923	85	aportacion_empresa	DESEMPLEO	DESEMPLEO	97.62	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
924	85	aportacion_empresa	FORMACIÓN PROFESIONAL	FORMACIÓN PROFESIONAL	10.65	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
925	85	aportacion_empresa	FONDO GARANTÍA SALARIAL	FONDO DE GARANTÍA SALARIAL	3.55	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
926	86	devengo	SALARIO BASE	*SALARIO BASE	458.68	t	t	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
927	86	devengo	HORAS NOCTURNAS	*HORAS NOCTURNAS	25.25	t	t	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
928	86	devengo	PAGA EXTRA	*PAGA EXTRA	112.39	t	t	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
930	86	deduccion	DTO. CONT. COMUNES	COTIZACIÓN CONTINGENCIAS COMUNES (4,70%)	30.97	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
931	86	deduccion	MEI	COTIZACIÓN MECANISMO EQUIDAD INTERGENERACIONAL (0,13%)	0.86	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
932	86	deduccion	FORMACIÓN PROFESIONAL	COTIZACIÓN FORMACIÓN PROFESIONAL (0,10%)	0.66	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
933	86	deduccion	DESEMPLEO	COTIZACIÓN DESEMPLEO (1,55%)	10.21	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
934	86	aportacion_empresa	TOTAL CONTINGENCIAS COMUNES + PRORRATA PAGAS EXTRAS	CONTINGENCIAS COMUNES	155.52	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
935	86	aportacion_empresa	MEI	MECANISMO EQUIDAD INTERGENERACIONAL	4.41	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
936	86	aportacion_empresa	AT Y EP	AT Y EP	9.88	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
937	86	aportacion_empresa	DESEMPLEO	DESEMPLEO	36.24	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
938	86	aportacion_empresa	FORMACIÓN PROFESIONAL	FORMACIÓN PROFESIONAL	3.95	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
939	86	aportacion_empresa	FONDO GARANTÍA SALARIAL	FONDO DE GARANTÍA SALARIAL	1.32	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
940	87	devengo	HORAS NOCTURNAS	*HORAS NOCTURNAS	27.27	t	t	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
941	87	devengo	ENFERMEDAD 60% EMP.	PREST. ENFERMEDAD CARGO EMPRESA	384.00	t	t	t	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
942	87	devengo	ENFERMEDAD 60% INS.	PREST. ENFERMEDAD	640.00	t	t	t	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
944	87	deduccion	DTO. CONT. COMUNES	COTIZACIÓN CONTINGENCIAS COMUNES (4,70%)	75.20	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
945	87	deduccion	MEI	COTIZACIÓN MECANISMO EQUIDAD INTERGENERACIONAL (0,13%)	2.08	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
946	87	deduccion	FORMACIÓN PROFESIONAL	COTIZACIÓN FORMACIÓN PROFESIONAL (0,10%)	1.60	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
947	87	deduccion	DESEMPLEO	COTIZACIÓN DESEMPLEO (1,55%)	24.80	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
948	87	deduccion	RETENCION IRPF	TRIBUTACIÓN IRPF (6,57%)	97.97	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
949	87	aportacion_empresa	TOTAL CONTINGENCIAS COMUNES + PRORRATA PAGAS EXTRAS	CONTINGENCIAS COMUNES	377.58	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
950	87	aportacion_empresa	MEI	MECANISMO EQUIDAD INTERGENERACIONAL	10.72	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
951	87	aportacion_empresa	AT Y EP	AT Y EP	24.00	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
952	87	aportacion_empresa	DESEMPLEO	DESEMPLEO	87.99	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
953	87	aportacion_empresa	FORMACIÓN PROFESIONAL	FORMACIÓN PROFESIONAL	9.60	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
954	87	aportacion_empresa	FONDO GARANTÍA SALARIAL	FONDO DE GARANTÍA SALARIAL	3.20	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
955	88	devengo	SALARIO BASE	*SALARIO BASE	687.19	t	t	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
956	88	devengo	PAGA EXTRA	*PAGA EXTRA	168.38	t	t	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
957	88	devengo	ENFERMEDAD 60% EMP.	PREST. ENFERMEDAD	560.00	t	t	t	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
958	88	deduccion	DTO. CONT. COMUNES	COTIZACIÓN CONTINGENCIAS COMUNES (4,70%)	75.30	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
959	88	deduccion	MEI	COTIZACIÓN MECANISMO EQUIDAD INTERGENERACIONAL (0,13%)	2.08	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
960	88	deduccion	DTO. SEGURIDAD SOCIAL	COTIZACIÓN FORMACIÓN PROFESIONAL (0,10%)	1.60	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
961	88	deduccion	DTO. BASE ACCIDENTE	COTIZACIÓN DESEMPLEO (1,55%)	24.83	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
962	88	deduccion	RETENCION IRPF	TRIBUTACIÓN IRPF (7,07%)	100.08	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
963	88	aportacion_empresa	TOTAL CONTINGENCIAS COMUNES + PRORRATA PAGAS EXTRAS	CONTINGENCIAS COMUNES	378.12	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
964	88	aportacion_empresa	MEI	MECANISMO EQUIDAD INTERGENERACIONAL	10.74	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
965	88	aportacion_empresa	AT Y EP	AT Y EP	24.03	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
966	88	aportacion_empresa	DESEMPLEO	DESEMPLEO	88.12	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
967	88	aportacion_empresa	FORMACIÓN PROFESIONAL	FORMACIÓN PROFESIONAL	9.61	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
968	88	aportacion_empresa	FONDO GARANTÍA SALARIAL	FONDO DE GARANTÍA SALARIAL	3.20	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
969	89	devengo	SALARIO BASE	SALARIO BASE	1245.53	t	t	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
970	89	devengo	HORAS NOCTURNAS	HORAS NOCTURNAS	16.16	t	t	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
971	89	devengo	PAGA EXTRA	PAGA EXTRA	305.19	t	t	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
972	89	deduccion	DTO. CONT. COMUNES	COTIZACIÓN CONTINGENCIAS COMUNES (4,70%)	76.15	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
973	89	deduccion	MEI	COTIZACIÓN MECANISMO EQUIDAD INTERGENERACIONAL (0,13%)	2.11	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
974	89	deduccion	FORMACIÓN PROFESIONAL	COTIZACIÓN FORMACIÓN PROFESIONAL (0,10%)	1.62	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
975	89	deduccion	DESEMPLEO	COTIZACIÓN DESEMPLEO (1,55%)	25.11	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
976	89	deduccion	RETENCION IRPF	TRIBUTACIÓN IRPF (7,07%)	110.78	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
977	89	aportacion_empresa	TOTAL CONTINGENCIAS COMUNES + PRORRATA PAGAS EXTRAS	CONTINGENCIAS COMUNES	382.39	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
978	89	aportacion_empresa	MEI	MECANISMO EQUIDAD INTERGENERACIONAL	10.85	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
979	89	aportacion_empresa	AT Y EP	AT Y EP	24.30	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
980	89	aportacion_empresa	DESEMPLEO	DESEMPLEO	89.12	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
981	89	aportacion_empresa	FORMACIÓN PROFESIONAL	FORMACIÓN PROFESIONAL	9.72	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
982	89	aportacion_empresa	FONDO GARANTÍA SALARIAL	FONDO DE GARANTÍA SALARIAL	3.24	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
983	90	devengo	SALARIO BASE	*SALARIO BASE	1288.48	t	t	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
984	90	devengo	HORAS NOCTURNAS	*HORAS NOCTURNAS	33.33	t	t	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
985	90	devengo	PAGA EXTRA	*PAGA EXTRA	315.71	t	t	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
986	90	deduccion	DTO. CONT. COMUNES	COTIZACIÓN CONTINGENCIAS COMUNES (4,70%)	76.96	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
987	90	deduccion	MEI	COTIZACIÓN MECANISMO EQUIDAD INTERGENERACIONAL (0,13%)	2.13	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
988	90	deduccion	FORMACIÓN PROFESIONAL	COTIZACIÓN FORMACIÓN PROFESIONAL (0,10%)	1.64	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
989	90	deduccion	DESEMPLEO	COTIZACIÓN DESEMPLEO (1,55%)	25.38	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
990	90	deduccion	RETENCION IRPF	TRIBUTACIÓN IRPF (7,07%)	115.77	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
991	90	aportacion_empresa	TOTAL CONTINGENCIAS COMUNES + PRORRATA PAGAS EXTRAS	BASE INCAPACIDAD TEMPORAL TOTAL	386.45	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
992	90	aportacion_empresa	MEI	MECANISMO EQUIDAD INTERGENERACIONAL	10.97	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
993	90	aportacion_empresa	AT Y EP	AT Y EP	24.56	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
994	90	aportacion_empresa	DESEMPLEO	DESEMPLEO	90.06	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
995	90	aportacion_empresa	FORMACIÓN PROFESIONAL	FORMACIÓN PROFESIONAL	9.83	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
996	90	aportacion_empresa	FONDO GARANTÍA SALARIAL	FONDO DE GARANTÍA SALARIAL	3.28	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
997	91	devengo	SALARIO BASE	*SALARIO BASE	1288.48	t	t	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
998	91	devengo	HORAS NOCTURNAS	*HORAS NOCTURNAS	43.43	t	t	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
999	91	devengo	PAGA EXTRA	*PAGA EXTRA	315.71	t	t	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1000	91	deduccion	DTO. CONT. COMUNES	COTIZACIÓN CONTINGENCIAS COMUNES (4,70%)	77.44	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1001	91	deduccion	MEI	COTIZACIÓN MECANISMO EQUIDAD INTERGENERACIONAL (0,13%)	2.14	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1002	91	deduccion	FORMACIÓN PROFESIONAL	COTIZACIÓN FORMACIÓN PROFESIONAL (0,10%)	1.65	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1003	91	deduccion	DESEMPLEO	COTIZACIÓN DESEMPLEO (1,55%)	25.54	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1004	91	deduccion	RETENCION IRPF	TRIBUTACIÓN IRPF (7,07%)	116.49	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1005	91	aportacion_empresa	TOTAL CONTINGENCIAS COMUNES + PRORRATA PAGAS EXTRAS	CONTINGENCIAS COMUNES	388.84	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1006	91	aportacion_empresa	MEI	MECANISMO EQUIDAD INTERGENERACIONAL	11.04	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1007	91	aportacion_empresa	AT Y EP	AT Y EP	24.71	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1008	91	aportacion_empresa	DESEMPLEO	DESEMPLEO	90.62	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1009	91	aportacion_empresa	FORMACIÓN PROFESIONAL	FORMACIÓN PROFESIONAL	9.89	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1010	91	aportacion_empresa	FONDO GARANTÍA SALARIAL	FONDO DE GARANTÍA SALARIAL	3.30	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1011	92	devengo	SALARIO BASE	*SALARIO BASE	1288.48	t	t	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1012	92	devengo	HORAS NOCTURNAS	*HORAS NOCTURNAS	42.42	t	t	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1013	92	devengo	PAGA EXTRA	*PAGA EXTRA	315.71	t	t	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1014	92	deduccion	DTO. CONT. COMUNES	COTIZACIÓN CONTINGENCIAS COMUNES (4,70%)	77.39	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1015	92	deduccion	MEI	COTIZACIÓN MECANISMO EQUIDAD INTERGENERACIONAL (0,13%)	2.14	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1016	92	deduccion	DTO. SEGURIDAD SOCIAL	COTIZACIÓN FORMACIÓN PROFESIONAL (0,10%)	1.65	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1017	92	deduccion	DTO. SEGURIDAD SOCIAL	COTIZACIÓN DESEMPLEO (1,55%)	25.52	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1018	92	deduccion	RETENCION IRPF	TRIBUTACIÓN IRPF (7,07%)	116.42	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1019	92	aportacion_empresa	TOTAL CONTINGENCIAS COMUNES + PRORRATA PAGAS EXTRAS	BASE INCAPACIDAD TEMPORAL TOTAL	388.60	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1020	92	aportacion_empresa	MEI	MECANISMO EQUIDAD INTERGENERACIONAL	11.03	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1021	92	aportacion_empresa	AT Y EP	AT Y EP	24.70	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1022	92	aportacion_empresa	DESEMPLEO	DESEMPLEO	90.56	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1023	92	aportacion_empresa	FORMACIÓN PROFESIONAL	FORMACIÓN PROFESIONAL	9.88	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1024	92	aportacion_empresa	FONDO GARANTÍA SALARIAL	FONDO DE GARANTÍA SALARIAL	3.29	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1025	93	devengo	SALARIO BASE	*Salario Base	1288.48	t	t	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1026	93	devengo	HORAS NOCTURNAS	*Horas nocturnas	36.36	t	t	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1027	93	devengo	PAGA EXTRA	*Paga Extra	315.71	t	t	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1028	93	deduccion	DTO. CONT. COMUNES	Cotización Contingencias Comunes (4,70%)	77.11	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1029	93	deduccion	MEI	Cotización Mecanismo Equidad Intergeneracional (0,13%)	2.13	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1030	93	deduccion	FORMACIÓN PROFESIONAL	Cotización Formación Profesional (0,10%)	1.64	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1031	93	deduccion	DESEMPLEO	Cotización Desempleo (1,55%)	25.43	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1032	93	deduccion	RETENCION IRPF	Tributación IRPF (7,07%)	115.99	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1033	93	aportacion_empresa	TOTAL CONTINGENCIAS COMUNES + PRORRATA PAGAS EXTRAS	Contingencias Comunes	387.17	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1034	93	aportacion_empresa	MEI	Mecanismo Equidad Intergeneracional	10.99	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1035	93	aportacion_empresa	AT Y EP	AT y EP	24.60	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1036	93	aportacion_empresa	DESEMPLEO	Desempleo	90.23	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1037	93	aportacion_empresa	FORMACIÓN PROFESIONAL	Formación Profesional	9.84	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1038	93	aportacion_empresa	FONDO GARANTÍA SALARIAL	Fondo de garantía salarial	3.28	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1039	94	devengo	SALARIO BASE	*SALARIO BASE	1288.48	t	t	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1040	94	devengo	HORAS NOCTURNAS	*HORAS NOCTURNAS	34.34	t	t	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1041	94	devengo	PAGA EXTRA	*PAGA EXTRA	315.71	t	t	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1042	94	deduccion	DTO. CONT. COMUNES	COTIZACIÓN CONTINGENCIAS COMUNES (4,70%)	77.01	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1043	94	deduccion	MEI	COTIZACIÓN MECANISMO EQUIDAD INTERGENERACIONAL (0,13%)	2.13	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1044	94	deduccion	FORMACIÓN PROFESIONAL	COTIZACIÓN FORMACIÓN PROFESIONAL (0,10%)	1.64	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1045	94	deduccion	DESEMPLEO	COTIZACIÓN DESEMPLEO (1,55%)	25.40	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1046	94	deduccion	RETENCION IRPF	TRIBUTACIÓN IRPF (7,07%)	115.84	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1047	94	aportacion_empresa	TOTAL CONTINGENCIAS COMUNES + PRORRATA PAGAS EXTRAS	CONTINGENCIAS COMUNES	386.69	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1048	94	aportacion_empresa	MEI	MECANISMO EQUIDAD INTERGENERACIONAL	10.98	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1049	94	aportacion_empresa	AT Y EP	AT Y EP	24.58	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1050	94	aportacion_empresa	DESEMPLEO	DESEMPLEO	90.12	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1051	94	aportacion_empresa	FORMACIÓN PROFESIONAL	FORMACIÓN PROFESIONAL	9.83	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1052	94	aportacion_empresa	FONDO GARANTÍA SALARIAL	FONDO DE GARANTÍA SALARIAL	3.28	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1053	95	devengo	SALARIO BASE	*SALARIO BASE	1288.48	t	t	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1054	95	devengo	HORAS NOCTURNAS	*HORAS NOCTURNAS	16.16	t	t	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1055	95	devengo	PAGA EXTRA	*PAGA EXTRA	315.71	t	t	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1056	95	deduccion	DTO. CONT. COMUNES	COTIZACIÓN CONTINGENCIAS COMUNES (4,70%)	76.16	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1057	95	deduccion	MEI	COTIZACIÓN MECANISMO EQUIDAD INTERGENERACIONAL (0,13%)	2.11	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1058	95	deduccion	FORMACIÓN PROFESIONAL	COTIZACIÓN FORMACIÓN PROFESIONAL (0,10%)	1.62	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1059	95	deduccion	DESEMPLEO	COTIZACIÓN DESEMPLEO (1,55%)	25.12	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1060	95	deduccion	RETENCION IRPF	TRIBUTACIÓN IRPF (7,07%)	114.56	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1061	95	aportacion_empresa	TOTAL CONTINGENCIAS COMUNES + PRORRATA PAGAS EXTRAS	CONTINGENCIAS COMUNES	382.40	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1062	95	aportacion_empresa	MEI	MECANISMO EQUIDAD INTERGENERACIONAL	10.85	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1063	95	aportacion_empresa	AT Y EP	AT Y EP	24.30	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1064	95	aportacion_empresa	DESEMPLEO	DESEMPLEO	89.12	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1065	95	aportacion_empresa	FORMACIÓN PROFESIONAL	FORMACIÓN PROFESIONAL	9.72	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1066	95	aportacion_empresa	FONDO GARANTÍA SALARIAL	FONDO DE GARANTÍA SALARIAL	3.24	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1067	96	devengo	SALARIO BASE	*SALARIO BASE	1215.89	t	t	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1068	96	devengo	HORAS NOCTURNAS	*HORAS NOCTURNAS	30.30	t	t	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1069	96	devengo	PAGA EXTRA	*PAGA EXTRA	290.32	t	t	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1070	96	deduccion	DTO. CONT. COMUNES	COTIZACIÓN CONTINGENCIAS COMUNES (4,70%)	72.22	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1071	96	deduccion	MEI	COTIZACIÓN MECANISMO EQUIDAD INTERGENERACIONAL (0,13%)	2.00	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1072	96	deduccion	DTO. SEGURIDAD SOCIAL	COTIZACIÓN FORMACIÓN PROFESIONAL (0,10%)	1.54	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1073	96	deduccion	DTO. SEGURIDAD SOCIAL	COTIZACIÓN DESEMPLEO (1,55%)	23.82	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1074	96	deduccion	RETENCION IRPF	TRIBUTACIÓN IRPF (5,23%)	80.36	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1075	96	aportacion_empresa	TOTAL CONTINGENCIAS COMUNES + PRORRATA PAGAS EXTRAS	CONTINGENCIAS COMUNES	362.62	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1076	96	aportacion_empresa	MEI	MECANISMO EQUIDAD INTERGENERACIONAL	10.29	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1077	96	aportacion_empresa	AT Y EP	AT Y EP	23.05	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1078	96	aportacion_empresa	DESEMPLEO	DESEMPLEO	84.51	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1079	96	aportacion_empresa	FORMACIÓN PROFESIONAL	FORMACIÓN PROFESIONAL	9.22	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1080	96	aportacion_empresa	FONDO GARANTÍA SALARIAL	FONDO DE GARANTÍA SALARIAL	3.07	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1081	97	devengo	SALARIO BASE	*SALARIO BASE	957.51	t	t	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1082	97	devengo	HORAS NOCTURNAS	*HORAS NOCTURNAS	34.34	t	t	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1083	97	devengo	PAGA EXTRA	*PAGA EXTRA	228.62	t	t	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1084	97	deduccion	DTO. CONT. COMUNES	COTIZACIÓN CONTINGENCIAS COMUNES (4,70%)	57.36	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1085	97	deduccion	MEI	COTIZACIÓN MECANISMO EQUIDAD INTERGENERACIONAL (0,13%)	1.59	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1086	97	deduccion	FORMACIÓN PROFESIONAL	COTIZACIÓN FORMACIÓN PROFESIONAL (0,10%)	1.22	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1087	97	deduccion	DESEMPLEO	COTIZACIÓN DESEMPLEO (1,55%)	18.92	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1088	97	aportacion_empresa	TOTAL CONTINGENCIAS COMUNES + PRORRATA PAGAS EXTRAS	CONTINGENCIAS COMUNES	288.03	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1089	97	aportacion_empresa	MEI	MECANISMO EQUIDAD INTERGENERACIONAL	8.17	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1090	97	aportacion_empresa	AT Y EP	AT Y EP	18.30	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1091	97	aportacion_empresa	DESEMPLEO	DESEMPLEO	67.13	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1092	97	aportacion_empresa	FORMACIÓN PROFESIONAL	FORMACIÓN PROFESIONAL	7.32	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1093	97	aportacion_empresa	FONDO GARANTÍA SALARIAL	FONDO DE GARANTÍA SALARIAL	2.44	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1094	98	devengo	SALARIO BASE	*SALARIO BASE	358.18	t	t	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1095	98	devengo	HORAS NOCTURNAS	*HORAS NOCTURNAS	20.20	t	t	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1096	98	devengo	PAGA EXTRA	*PAGA EXTRA	85.53	t	t	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1097	98	deduccion	DTO. CONT. COMUNES	COTIZACIÓN CONTINGENCIAS COMUNES (4,70%)	23.14	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1098	98	deduccion	MEI	COTIZACIÓN MECANISMO EQUIDAD INTERGENERACIONAL (0,13%)	0.64	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1099	98	deduccion	FORMACIÓN PROFESIONAL	COTIZACIÓN FORMACIÓN PROFESIONAL (0,10%)	0.50	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1100	98	deduccion	DESEMPLEO	COTIZACIÓN DESEMPLEO (1,55%)	7.64	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1101	98	aportacion_empresa	TOTAL CONTINGENCIAS COMUNES + PRORRATA PAGAS EXTRAS	BASE INCAPACIDAD TEMPORAL TOTAL	116.24	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1102	98	aportacion_empresa	MEI	MECANISMO EQUIDAD INTERGENERACIONAL	3.30	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1103	98	aportacion_empresa	AT Y EP	AT Y EP	7.39	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1104	98	aportacion_empresa	DESEMPLEO	DESEMPLEO	27.09	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1105	98	aportacion_empresa	FORMACIÓN PROFESIONAL	FORMACIÓN PROFESIONAL	2.96	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1106	98	aportacion_empresa	FONDO GARANTÍA SALARIAL	FONDO DE GARANTÍA SALARIAL	0.98	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1107	99	devengo	SALARIO BASE	SALARIO BASE	653.54	t	t	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1108	99	devengo	NOCTURNIDAD	HORAS NOCTURNAS	30.30	t	t	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1109	99	devengo	PAGA EXTRA	PAGA EXTRA	161.61	t	t	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1110	99	deduccion	DTO. CONT. COMUNES	COTIZACIÓN CONTINGENCIAS COMUNES (4,70%)	39.74	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1111	99	deduccion	MEI	COTIZACIÓN MECANISMO EQUIDAD INTERGENERACIONAL (0,13%)	1.10	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1112	99	deduccion	DTO. SEGURIDAD SOCIAL	COTIZACIÓN FORMACIÓN PROFESIONAL (0,10%)	0.85	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1113	99	deduccion	DTO. SEGURIDAD SOCIAL	COTIZACIÓN DESEMPLEO (1,55%)	13.10	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1114	99	aportacion_empresa	TOTAL CONTINGENCIAS COMUNES + PRORRATA PAGAS EXTRAS	CONTINGENCIAS COMUNES	199.53	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1115	99	aportacion_empresa	MEI	MECANISMO EQUIDAD INTERGENERACIONAL	5.66	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1116	99	aportacion_empresa	AT Y EP	AT Y EP	12.68	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1117	99	aportacion_empresa	DESEMPLEO	DESEMPLEO	46.50	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1118	99	aportacion_empresa	FORMACIÓN PROFESIONAL	FORMACIÓN PROFESIONAL	5.07	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1119	99	aportacion_empresa	FONDO GARANTÍA SALARIAL	FONDO DE GARANTÍA SALARIAL	1.69	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1120	100	devengo	SALARIO BASE	*SALARIO BASE	653.54	t	t	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1121	100	devengo	HORAS NOCTURNAS	*HORAS NOCTURNAS	19.19	t	t	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1122	100	devengo	PAGA EXTRA	*PAGA EXTRA	161.61	t	t	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1123	100	deduccion	DTO. CONT. COMUNES	COTIZACIÓN CONTINGENCIAS COMUNES (4,70%)	39.21	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1124	100	deduccion	MEI	COTIZACIÓN MECANISMO EQUIDAD INTERGENERACIONAL (0,13%)	1.08	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1125	100	deduccion	FORMACIÓN PROFESIONAL	COTIZACIÓN FORMACIÓN PROFESIONAL (0,10%)	0.83	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1126	100	deduccion	DESEMPLEO	COTIZACIÓN DESEMPLEO (1,55%)	12.93	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1127	100	aportacion_empresa	TOTAL CONTINGENCIAS COMUNES + PRORRATA PAGAS EXTRAS	CONTINGENCIAS COMUNES TOTAL	196.90	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1128	100	aportacion_empresa	MEI	MECANISMO EQUIDAD INTERGENERACIONAL	5.59	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1129	100	aportacion_empresa	AT Y EP	AT Y EP	12.51	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1130	100	aportacion_empresa	DESEMPLEO	DESEMPLEO	45.89	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1131	100	aportacion_empresa	FORMACIÓN PROFESIONAL	FORMACIÓN PROFESIONAL	5.01	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1132	100	aportacion_empresa	FONDO GARANTÍA SALARIAL	FONDO DE GARANTÍA SALARIAL	1.67	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1133	101	devengo	SALARIO BASE	*SALARIO BASE	664.18	t	t	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1134	101	devengo	HORAS NOCTURNAS	*HORAS NOCTURNAS	21.21	t	t	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1135	101	devengo	HORAS COMPLEMENTARIAS	*HORAS COMPLEMENTARIAS	4.18	t	t	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1136	101	devengo	PAGA EXTRA	*PAGA EXTRA	164.24	t	t	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1137	101	deduccion	DTO. CONT. COMUNES	COTIZACIÓN CONTINGENCIAS COMUNES (4,70%)	40.45	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1138	101	deduccion	MEI	COTIZACIÓN MECANISMO EQUIDAD INTERGENERACIONAL (0,13%)	1.12	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1139	101	deduccion	FORMACIÓN PROFESIONAL	COTIZACIÓN FORMACIÓN PROFESIONAL (0,10%)	0.85	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1140	101	deduccion	DESEMPLEO	COTIZACIÓN DESEMPLEO (1,55%)	13.34	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1141	101	aportacion_empresa	TOTAL CONTINGENCIAS COMUNES + PRORRATA PAGAS EXTRAS	BASE INCAPACIDAD TEMPORAL TOTAL	203.14	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1142	101	aportacion_empresa	MEI	MECANISMO EQUIDAD INTERGENERACIONAL	5.77	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1143	101	aportacion_empresa	AT Y EP	AT Y EP	12.91	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1144	101	aportacion_empresa	DESEMPLEO	DESEMPLEO	47.34	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1145	101	aportacion_empresa	FORMACIÓN PROFESIONAL	FORMACIÓN PROFESIONAL	5.16	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1146	101	aportacion_empresa	FONDO GARANTÍA SALARIAL	FONDO DE GARANTÍA SALARIAL	1.73	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1147	102	devengo	SALARIO BASE	*SALARIO BASE	706.02	t	t	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1148	102	devengo	HORAS NOCTURNAS	*HORAS NOCTURNAS	20.20	t	t	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1149	102	devengo	PAGA EXTRA	*PAGA EXTRA	174.58	t	t	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1150	102	deduccion	DTO. CONT. COMUNES	COTIZACIÓN CONTINGENCIAS COMUNES (4,70%)	43.47	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1151	102	deduccion	MEI	COTIZACIÓN MECANISMO EQUIDAD INTERGENERACIONAL (0,13%)	1.20	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1152	102	deduccion	FORMACIÓN PROFESIONAL	COTIZACIÓN FORMACIÓN PROFESIONAL (0,10%)	0.92	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1153	102	deduccion	DESEMPLEO	COTIZACIÓN DESEMPLEO (1,55%)	14.34	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1154	102	aportacion_empresa	TOTAL CONTINGENCIAS COMUNES + PRORRATA PAGAS EXTRAS	BASE INCAPACIDAD TEMPORAL TOTAL	218.31	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1155	102	aportacion_empresa	MEI	MECANISMO EQUIDAD INTERGENERACIONAL	6.20	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1156	102	aportacion_empresa	AT Y EP	AT Y EP	13.88	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1157	102	aportacion_empresa	DESEMPLEO	DESEMPLEO	50.88	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1158	102	aportacion_empresa	FORMACIÓN PROFESIONAL	FORMACIÓN PROFESIONAL	5.55	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1159	102	aportacion_empresa	FONDO GARANTÍA SALARIAL	FONDO DE GARANTÍA SALARIAL	1.86	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1160	103	devengo	SALARIO BASE	*SALARIO BASE	673.15	t	t	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1161	103	devengo	HORAS NOCTURNAS	*HORAS NOCTURNAS	28.28	t	t	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1162	103	devengo	PAGA EXTRA	*PAGA EXTRA	166.46	t	t	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1163	103	deduccion	DTO. CONT. COMUNES	COTIZACIÓN CONTINGENCIAS COMUNES (4,70%)	40.79	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1164	103	deduccion	MEI	COTIZACIÓN MECANISMO EQUIDAD INTERGENERACIONAL (0,13%)	1.13	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1165	103	deduccion	FORMACIÓN PROFESIONAL	COTIZACIÓN FORMACIÓN PROFESIONAL (0,10%)	0.87	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1166	103	deduccion	DESEMPLEO	COTIZACIÓN DESEMPLEO (1,55%)	13.45	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1167	103	aportacion_empresa	TOTAL CONTINGENCIAS COMUNES + PRORRATA PAGAS EXTRAS	CONTINGENCIAS COMUNES	204.82	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1168	103	aportacion_empresa	MEI	MECANISMO EQUIDAD INTERGENERACIONAL	5.81	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1169	103	aportacion_empresa	AT Y EP	AT Y EP	13.02	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1170	103	aportacion_empresa	DESEMPLEO	DESEMPLEO	47.73	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1171	103	aportacion_empresa	FORMACIÓN PROFESIONAL	FORMACIÓN PROFESIONAL	5.21	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1172	103	aportacion_empresa	FONDO GARANTÍA SALARIAL	FONDO DE GARANTÍA SALARIAL	1.74	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1173	104	devengo	SALARIO BASE	*Salario Base	713.33	t	t	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1174	104	devengo	HORAS NOCTURNAS	*Horas nocturnas	32.32	t	t	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1175	104	devengo	PAGA EXTRA	*Paga Extra	176.40	t	t	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1176	104	deduccion	DTO. CONT. COMUNES	Cotización Contingencias Comunes (4,70%)	43.98	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1177	104	deduccion	MEI	Cotización Mecanismo Equidad Intergeneracional (0,13%)	1.21	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1178	104	deduccion	FORMACIÓN PROFESIONAL	Cotización Formación Profesional (0,10%)	0.94	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1179	104	deduccion	DESEMPLEO	Cotización Desempleo (1,55%)	14.49	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1180	104	aportacion_empresa	TOTAL CONTINGENCIAS COMUNES + PRORRATA PAGAS EXTRAS	Base Incapacidad Temporal Total	220.82	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1181	104	aportacion_empresa	MEI	Mecanismo Equidad Intergeneracional	6.27	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1182	104	aportacion_empresa	AT Y EP	AT y EP	14.03	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1183	104	aportacion_empresa	DESEMPLEO	Desempleo	51.46	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1184	104	aportacion_empresa	FORMACIÓN PROFESIONAL	Formación Profesional	5.62	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1185	104	aportacion_empresa	FONDO GARANTÍA SALARIAL	Fondo de garantía salarial	1.87	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1186	105	devengo	SALARIO BASE	*SALARIO BASE	767.86	t	t	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1187	105	devengo	HORAS NOCTURNAS	*HORAS NOCTURNAS	36.36	t	t	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1188	105	devengo	HORAS COMPLEMENTARIAS	*HORAS COMPLEMENTARIAS	20.88	t	t	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1189	105	devengo	PAGA EXTRA	*PAGA EXTRA	189.88	t	t	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1190	105	deduccion	DTO. CONT. COMUNES	COTIZACIÓN CONTINGENCIAS COMUNES (4,70%)	50.80	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1191	105	deduccion	MEI	COTIZACIÓN MECANISMO EQUIDAD INTERGENERACIONAL (0,13%)	1.40	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1192	105	deduccion	FORMACIÓN PROFESIONAL	COTIZACIÓN FORMACIÓN PROFESIONAL (0,10%)	1.08	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1193	105	deduccion	DESEMPLEO	COTIZACIÓN DESEMPLEO (1,55%)	16.76	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1194	105	aportacion_empresa	TOTAL CONTINGENCIAS COMUNES + PRORRATA PAGAS EXTRAS	CONTINGENCIAS COMUNES	255.06	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1195	105	aportacion_empresa	MEI	MECANISMO EQUIDAD INTERGENERACIONAL	7.25	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1196	105	aportacion_empresa	AT Y EP	AT Y EP	16.21	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1197	105	aportacion_empresa	DESEMPLEO	DESEMPLEO	59.46	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1198	105	aportacion_empresa	FORMACIÓN PROFESIONAL	FORMACIÓN PROFESIONAL	6.49	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1199	105	aportacion_empresa	FONDO GARANTÍA SALARIAL	FONDO DE GARANTÍA SALARIAL	2.16	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1200	106	devengo	SALARIO BASE	*SALARIO BASE	779.08	t	t	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1201	106	devengo	HORAS NOCTURNAS	*HORAS NOCTURNAS	42.42	t	t	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1202	106	devengo	PAGA EXTRA	*PAGA EXTRA	192.66	t	t	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1203	106	deduccion	DTO. CONT. COMUNES	COTIZACIÓN CONTINGENCIAS COMUNES (4,70%)	48.38	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1204	106	deduccion	MEI	COTIZACIÓN MECANISMO EQUIDAD INTERGENERACIONAL (0,13%)	1.34	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1205	106	deduccion	FORMACIÓN PROFESIONAL	COTIZACIÓN FORMACIÓN PROFESIONAL (0,10%)	1.03	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1206	106	deduccion	DESEMPLEO	COTIZACIÓN DESEMPLEO (1,55%)	15.96	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1207	106	aportacion_empresa	TOTAL CONTINGENCIAS COMUNES + PRORRATA PAGAS EXTRAS	CONTINGENCIAS COMUNES	242.91	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1208	106	aportacion_empresa	MEI	MECANISMO EQUIDAD INTERGENERACIONAL	6.90	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1209	106	aportacion_empresa	AT Y EP	AT Y EP	15.45	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1210	106	aportacion_empresa	DESEMPLEO	DESEMPLEO	56.62	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1211	106	aportacion_empresa	FORMACIÓN PROFESIONAL	FORMACIÓN PROFESIONAL	6.17	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1212	106	aportacion_empresa	FONDO GARANTÍA SALARIAL	FONDO DE GARANTÍA SALARIAL	2.06	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1213	107	devengo	SALARIO BASE	SALARIO BASE	314.14	t	t	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1214	107	devengo	PAGA EXTRA	PAGA EXTRA	77.68	t	t	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1215	107	deduccion	DTO. CONT. COMUNES	COTIZACIÓN CONTINGENCIAS COMUNES (4,70%)	18.42	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1216	107	deduccion	MEI	COTIZACIÓN MECANISMO EQUIDAD INTERGENERACIONAL (0,13%)	0.51	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1217	107	deduccion	FORMACIÓN PROFESIONAL	COTIZACIÓN FORMACIÓN PROFESIONAL (0,10%)	0.39	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1218	107	deduccion	DESEMPLEO	COTIZACIÓN DESEMPLEO (1,55%)	6.07	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1219	107	aportacion_empresa	TOTAL CONTINGENCIAS COMUNES + PRORRATA PAGAS EXTRAS	CONTINGENCIAS COMUNES	92.47	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1220	107	aportacion_empresa	MEI	MECANISMO EQUIDAD INTERGENERACIONAL	2.62	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1221	107	aportacion_empresa	AT Y EP	AT Y EP	5.87	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1222	107	aportacion_empresa	DESEMPLEO	DESEMPLEO	21.55	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1223	107	aportacion_empresa	FORMACIÓN PROFESIONAL	FORMACIÓN PROFESIONAL	2.35	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1224	107	aportacion_empresa	FONDO GARANTÍA SALARIAL	FONDO DE GARANTÍA SALARIAL	0.78	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1225	108	devengo	SALARIO BASE	*SALARIO BASE	314.10	t	t	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1226	108	devengo	PAGA EXTRA	*PAGA EXTRA	77.67	t	t	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1227	108	deduccion	DTO. CONT. COMUNES	COTIZACIÓN CONTINGENCIAS COMUNES (4,70%)	20.98	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1228	108	deduccion	MEI	COTIZACIÓN MECANISMO EQUIDAD INTERGENERACIONAL (0,13%)	0.58	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1229	108	deduccion	FORMACIÓN PROFESIONAL	COTIZACIÓN FORMACIÓN PROFESIONAL (0,10%)	0.45	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1230	108	deduccion	DESEMPLEO	COTIZACIÓN DESEMPLEO (1,55%)	6.92	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1231	108	aportacion_empresa	TOTAL CONTINGENCIAS COMUNES + PRORRATA PAGAS EXTRAS	BASE INCAPACIDAD TEMPORAL TOTAL	105.33	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1232	108	aportacion_empresa	MEI	MECANISMO EQUIDAD INTERGENERACIONAL	2.99	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1233	108	aportacion_empresa	AT Y EP	AT Y EP	6.69	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1234	108	aportacion_empresa	DESEMPLEO	DESEMPLEO	24.55	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1235	108	aportacion_empresa	FORMACIÓN PROFESIONAL	FORMACIÓN PROFESIONAL	2.68	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1236	108	aportacion_empresa	FONDO GARANTÍA SALARIAL	FONDO DE GARANTÍA SALARIAL	0.89	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1237	109	devengo	SALARIO BASE	SALARIO BASE	31.41	t	t	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1238	109	devengo	PAGA EXTRA	PAGA EXTRA	7.77	t	t	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1239	109	devengo	ENFERMEDAD 75% INS.	PREST. ACCIDENTE	182.58	t	t	t	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1240	109	deduccion	DTO. CONT. COMUNES	COTIZACIÓN CONTINGENCIAS COMUNES (4,70%)	14.18	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1241	109	deduccion	MEI	COTIZACIÓN MECANISMO EQUIDAD INTERGENERACIONAL (0,13%)	0.39	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1242	109	deduccion	FORMACIÓN PROFESIONAL	COTIZACIÓN FORMACIÓN PROFESIONAL (0,10%)	0.30	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1243	109	deduccion	DESEMPLEO	COTIZACIÓN DESEMPLEO (1,55%)	4.68	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1244	109	aportacion_empresa	TOTAL CONTINGENCIAS COMUNES + PRORRATA PAGAS EXTRAS	BASE INCAPACIDAD TEMPORAL	71.19	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1245	109	aportacion_empresa	MEI	MECANISMO EQUIDAD INTERGENERACIONAL	2.02	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1246	109	aportacion_empresa	AT Y EP	AT Y EP	4.53	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1247	109	aportacion_empresa	DESEMPLEO	DESEMPLEO	16.59	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1248	109	aportacion_empresa	FORMACIÓN PROFESIONAL	FORMACIÓN PROFESIONAL	1.81	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1249	109	aportacion_empresa	FONDO GARANTÍA SALARIAL	FONDO DE GARANTÍA SALARIAL	0.60	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1250	110	devengo	SALARIO BASE	*SALARIO BASE	769.94	t	t	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1251	110	devengo	HORAS NOCTURNAS	*HORAS NOCTURNAS	26.26	t	t	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1252	110	devengo	PAGA EXTRA	*PAGA EXTRA	190.39	t	t	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1253	110	deduccion	DTO. CONT. COMUNES	COTIZACIÓN CONTINGENCIAS COMUNES (4,70%)	47.86	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1254	110	deduccion	MEI	COTIZACIÓN MECANISMO EQUIDAD INTERGENERACIONAL (0,13%)	1.32	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1255	110	deduccion	FORMACIÓN PROFESIONAL	COTIZACIÓN FORMACIÓN PROFESIONAL (0,10%)	1.01	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1256	110	deduccion	DESEMPLEO	COTIZACIÓN DESEMPLEO (1,55%)	15.78	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1257	110	deduccion	RETENCION IRPF	TRIBUTACIÓN IRPF (2,00%)	19.73	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1258	110	aportacion_empresa	TOTAL CONTINGENCIAS COMUNES + PRORRATA PAGAS EXTRAS	BASE INCAPACIDAD TEMPORAL TOTAL	240.29	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1259	110	aportacion_empresa	MEI	MECANISMO EQUIDAD INTERGENERACIONAL	6.82	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1260	110	aportacion_empresa	AT Y EP	AT Y EP	15.26	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1261	110	aportacion_empresa	DESEMPLEO	DESEMPLEO	56.00	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1262	110	aportacion_empresa	FORMACIÓN PROFESIONAL	FORMACIÓN PROFESIONAL	6.11	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1263	110	aportacion_empresa	FONDO GARANTÍA SALARIAL	FONDO DE GARANTÍA SALARIAL	2.04	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1264	111	devengo	SALARIO BASE	SALARIO BASE	963.54	t	t	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1265	111	devengo	HORAS NOCTURNAS	HORAS NOCTURNAS	25.25	t	t	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1266	111	devengo	PAGA EXTRA	PAGA EXTRA	238.27	t	t	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1267	111	deduccion	DTO. CONT. COMUNES	COTIZACIÓN CONTINGENCIAS COMUNES (4,70%)	57.83	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1268	111	deduccion	MEI	COTIZACIÓN MECANISMO EQUIDAD INTERGENERACIONAL (0,13%)	1.59	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1269	111	deduccion	FORMACIÓN PROFESIONAL	COTIZACIÓN FORMACIÓN PROFESIONAL (0,10%)	1.24	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1270	111	deduccion	DESEMPLEO	COTIZACIÓN DESEMPLEO (1,55%)	19.07	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1271	111	deduccion	RETENCION IRPF	TRIBUTACIÓN IRPF (2,00%)	24.53	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1272	111	aportacion_empresa	TOTAL CONTINGENCIAS COMUNES + PRORRATA PAGAS EXTRAS	CONTINGENCIAS COMUNES	290.37	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1273	111	aportacion_empresa	MEI	MECANISMO EQUIDAD INTERGENERACIONAL	8.25	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1274	111	aportacion_empresa	AT Y EP	AT Y EP	18.46	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1275	111	aportacion_empresa	DESEMPLEO	DESEMPLEO	67.68	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1276	111	aportacion_empresa	FORMACIÓN PROFESIONAL	FORMACIÓN PROFESIONAL	7.38	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1277	111	aportacion_empresa	FONDO GARANTÍA SALARIAL	FONDO DE GARANTÍA SALARIAL	2.46	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1278	112	devengo	SALARIO BASE	*SALARIO BASE	1084.08	t	t	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1279	112	devengo	HORAS NOCTURNAS	*HORAS NOCTURNAS	36.36	t	t	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1280	112	devengo	PAGA EXTRA	*PAGA EXTRA	268.08	t	t	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1281	112	deduccion	DTO. CONT. COMUNES	COTIZACIÓN CONTINGENCIAS COMUNES (4,70%)	70.30	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1282	112	deduccion	MEI	COTIZACIÓN MECANISMO EQUIDAD INTERGENERACIONAL (0,13%)	1.95	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1283	112	deduccion	FORMACIÓN PROFESIONAL	COTIZACIÓN FORMACIÓN PROFESIONAL (0,10%)	1.49	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1284	112	deduccion	DESEMPLEO	COTIZACIÓN DESEMPLEO (1,55%)	23.18	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1285	112	deduccion	RETENCION IRPF	TRIBUTACIÓN IRPF (2,00%)	27.76	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1286	112	aportacion_empresa	TOTAL CONTINGENCIAS COMUNES + PRORRATA PAGAS EXTRAS	BASE INCAPACIDAD TEMPORAL TOTAL	352.98	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1287	112	aportacion_empresa	MEI	MECANISMO EQUIDAD INTERGENERACIONAL	10.01	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1288	112	aportacion_empresa	AT Y EP	AT Y EP	22.43	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1289	112	aportacion_empresa	DESEMPLEO	DESEMPLEO	82.26	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1290	112	aportacion_empresa	FORMACIÓN PROFESIONAL	FORMACIÓN PROFESIONAL	8.97	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1291	112	aportacion_empresa	FONDO GARANTÍA SALARIAL	FONDO DE GARANTÍA SALARIAL	2.99	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1292	113	devengo	SALARIO BASE	*SALARIO BASE	223.93	t	t	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1293	113	devengo	PAGA EXTRA	*PAGA EXTRA	55.37	t	t	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1294	113	deduccion	DTO. CONT. COMUNES	COTIZACIÓN CONTINGENCIAS COMUNES (4,70%)	13.86	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1295	113	deduccion	MEI	COTIZACIÓN MECANISMO EQUIDAD INTERGENERACIONAL (0,13%)	0.38	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1296	113	deduccion	FORMACIÓN PROFESIONAL	COTIZACIÓN FORMACIÓN PROFESIONAL (0,10%)	0.29	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1297	113	deduccion	DESEMPLEO	COTIZACIÓN DESEMPLEO (1,55%)	4.57	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1298	113	aportacion_empresa	TOTAL CONTINGENCIAS COMUNES + PRORRATA PAGAS EXTRAS	BASE INCAPACIDAD TEMPORAL TOTAL	69.59	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1299	113	aportacion_empresa	MEI	MECANISMO EQUIDAD INTERGENERACIONAL	1.98	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1300	113	aportacion_empresa	AT Y EP	AT Y EP	4.42	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1301	113	aportacion_empresa	DESEMPLEO	DESEMPLEO	16.22	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1302	113	aportacion_empresa	FORMACIÓN PROFESIONAL	FORMACIÓN PROFESIONAL	1.77	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1303	113	aportacion_empresa	FONDO GARANTÍA SALARIAL	FONDO DE GARANTÍA SALARIAL	0.59	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1304	114	devengo	SALARIO BASE	SALARIO BASE	418.22	t	t	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1305	114	devengo	HORAS NOCTURNAS	HORAS NOCTURNAS	14.14	t	t	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1306	114	devengo	HORAS COMPLEMENTARIAS	HORAS COMPLEMENTARIAS	151.15	t	t	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1307	114	devengo	PAGA EXTRA	PAGA EXTRA	103.42	t	t	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1308	114	deduccion	DTO. CONT. COMUNES	COTIZACIÓN CONTINGENCIAS COMUNES (4,70%)	32.48	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1309	114	deduccion	MEI	COTIZACIÓN MECANISMO EQUIDAD INTERGENERACIONAL (0,13%)	0.90	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1310	114	deduccion	FORMACIÓN PROFESIONAL	COTIZACIÓN FORMACIÓN PROFESIONAL (0,10%)	0.69	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1311	114	deduccion	DESEMPLEO	COTIZACIÓN DESEMPLEO (1,55%)	10.71	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1312	114	aportacion_empresa	TOTAL CONTINGENCIAS COMUNES + PRORRATA PAGAS EXTRAS	BASE INCAPACIDAD TEMPORAL TOTAL	163.07	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1313	114	aportacion_empresa	MEI	MECANISMO EQUIDAD INTERGENERACIONAL	4.62	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1314	114	aportacion_empresa	AT Y EP	AT Y EP	10.35	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1315	114	aportacion_empresa	DESEMPLEO	DESEMPLEO	38.00	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1316	114	aportacion_empresa	FORMACIÓN PROFESIONAL	FORMACIÓN PROFESIONAL	4.14	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1317	114	aportacion_empresa	FONDO GARANTÍA SALARIAL	FONDO DE GARANTÍA SALARIAL	1.38	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1318	115	devengo	SALARIO BASE	*SALARIO BASE	797.67	t	t	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1319	115	devengo	HORAS NOCTURNAS	*HORAS NOCTURNAS	26.26	t	t	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1320	115	devengo	PAGA EXTRA	*PAGA EXTRA	197.25	t	t	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1321	115	deduccion	DTO. CONT. COMUNES	COTIZACIÓN CONTINGENCIAS COMUNES (4,70%)	49.81	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1322	115	deduccion	MEI	COTIZACIÓN MECANISMO EQUIDAD INTERGENERACIONAL (0,13%)	1.38	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1323	115	deduccion	FORMACIÓN PROFESIONAL	COTIZACIÓN FORMACIÓN PROFESIONAL (0,10%)	1.06	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1324	115	deduccion	DESEMPLEO	COTIZACIÓN DESEMPLEO (1,55%)	16.43	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1325	115	aportacion_empresa	TOTAL CONTINGENCIAS COMUNES + PRORRATA PAGAS EXTRAS	BASE INCAPACIDAD TEMPORAL TOTAL	250.10	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1326	115	aportacion_empresa	MEI	MECANISMO EQUIDAD INTERGENERACIONAL	7.10	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1327	115	aportacion_empresa	AT Y EP	AT Y EP	15.90	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1328	115	aportacion_empresa	DESEMPLEO	DESEMPLEO	58.28	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1329	115	aportacion_empresa	FORMACIÓN PROFESIONAL	FORMACIÓN PROFESIONAL	6.36	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1330	115	aportacion_empresa	FONDO GARANTÍA SALARIAL	FONDO DE GARANTÍA SALARIAL	2.13	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1331	116	devengo	SALARIO BASE	*SALARIO BASE	791.59	t	t	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1332	116	devengo	HORAS NOCTURNAS	*HORAS NOCTURNAS	33.33	t	t	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1333	116	devengo	PAGA EXTRA	*PAGA EXTRA	195.75	t	t	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1334	116	deduccion	DTO. CONT. COMUNES	COTIZACIÓN CONTINGENCIAS COMUNES (4,70%)	48.72	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1335	116	deduccion	MEI	COTIZACIÓN MECANISMO EQUIDAD INTERGENERACIONAL (0,13%)	1.35	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1336	116	deduccion	FORMACIÓN PROFESIONAL	COTIZACIÓN FORMACIÓN PROFESIONAL (0,10%)	1.04	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1337	116	deduccion	DESEMPLEO	COTIZACIÓN DESEMPLEO (1,55%)	16.06	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1338	116	aportacion_empresa	TOTAL CONTINGENCIAS COMUNES + PRORRATA PAGAS EXTRAS	BASE INCAPACIDAD TEMPORAL TOTAL	244.60	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1339	116	aportacion_empresa	MEI	MECANISMO EQUIDAD INTERGENERACIONAL	6.94	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1340	116	aportacion_empresa	AT Y EP	AT Y EP	15.55	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1341	116	aportacion_empresa	DESEMPLEO	DESEMPLEO	57.00	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1342	116	aportacion_empresa	FORMACIÓN PROFESIONAL	FORMACIÓN PROFESIONAL	6.22	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1343	116	aportacion_empresa	FONDO GARANTÍA SALARIAL	FONDO DE GARANTÍA SALARIAL	2.08	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1344	117	devengo	SALARIO BASE	*SALARIO BASE	407.02	t	t	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1345	117	devengo	HORAS NOCTURNAS	*HORAS NOCTURNAS	30.30	t	t	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1346	117	devengo	PAGA EXTRA	*PAGA EXTRA	100.65	t	t	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1347	117	deduccion	DTO. CONT. COMUNES	COTIZACIÓN CONTINGENCIAS COMUNES (4,70%)	25.28	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1348	117	deduccion	MEI	COTIZACIÓN MECANISMO EQUIDAD INTERGENERACIONAL (0,13%)	0.70	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1349	117	deduccion	FORMACIÓN PROFESIONAL	COTIZACIÓN FORMACIÓN PROFESIONAL (0,10%)	0.54	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1350	117	deduccion	DESEMPLEO	COTIZACIÓN DESEMPLEO (1,55%)	8.34	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1351	117	aportacion_empresa	TOTAL CONTINGENCIAS COMUNES + PRORRATA PAGAS EXTRAS	CONTINGENCIAS COMUNES	126.96	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1352	117	aportacion_empresa	MEI	MECANISMO EQUIDAD INTERGENERACIONAL	3.60	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1353	117	aportacion_empresa	AT Y EP	AT Y EP	8.07	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1354	117	aportacion_empresa	DESEMPLEO	DESEMPLEO	29.59	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1355	117	aportacion_empresa	FORMACIÓN PROFESIONAL	FORMACIÓN PROFESIONAL	3.23	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1356	117	aportacion_empresa	FONDO GARANTÍA SALARIAL	FONDO DE GARANTÍA SALARIAL	1.08	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1357	118	devengo	SALARIO BASE	*SALARIO BASE	591.49	t	t	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1358	118	devengo	HORAS NOCTURNAS	*HORAS NOCTURNAS	30.30	t	t	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1359	118	devengo	HORAS COMPLEMENTARIAS	*HORAS COMPLEMENTARIAS	48.02	t	t	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1360	118	devengo	PAGA EXTRA	*PAGA EXTRA	146.28	t	t	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1361	118	deduccion	DTO. CONT. COMUNES	COTIZACIÓN CONTINGENCIAS COMUNES (4,70%)	38.73	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1362	118	deduccion	MEI	COTIZACIÓN MECANISMO EQUIDAD INTERGENERACIONAL (0,13%)	1.08	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1363	118	deduccion	FORMACIÓN PROFESIONAL	COTIZACIÓN FORMACIÓN PROFESIONAL (0,10%)	0.82	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1364	118	deduccion	DESEMPLEO	COTIZACIÓN DESEMPLEO (1,55%)	12.77	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1365	118	aportacion_empresa	TOTAL CONTINGENCIAS COMUNES + PRORRATA PAGAS EXTRAS	BASE INCAPACIDAD TEMPORAL TOTAL	194.48	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1366	118	aportacion_empresa	MEI	MECANISMO EQUIDAD INTERGENERACIONAL	5.51	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1367	118	aportacion_empresa	AT Y EP	AT Y EP	12.35	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1368	118	aportacion_empresa	DESEMPLEO	DESEMPLEO	45.32	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1369	118	aportacion_empresa	FORMACIÓN PROFESIONAL	FORMACIÓN PROFESIONAL	4.94	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1370	118	aportacion_empresa	FONDO GARANTÍA SALARIAL	FONDO DE GARANTÍA SALARIAL	1.65	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1371	119	devengo	SALARIO BASE	*SALARIO BASE	594.10	t	t	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1372	119	devengo	HORAS NOCTURNAS	*HORAS NOCTURNAS	39.39	t	t	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1373	119	devengo	PAGA EXTRA	*PAGA EXTRA	146.91	t	t	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1374	119	deduccion	DTO. CONT. COMUNES	COTIZACIÓN CONTINGENCIAS COMUNES (4,70%)	39.08	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1375	119	deduccion	MEI	COTIZACIÓN MECANISMO EQUIDAD INTERGENERACIONAL (0,13%)	1.08	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1376	119	deduccion	FORMACIÓN PROFESIONAL	COTIZACIÓN FORMACIÓN PROFESIONAL (0,10%)	0.84	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1377	119	deduccion	DESEMPLEO	COTIZACIÓN DESEMPLEO (1,55%)	12.90	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1378	119	aportacion_empresa	TOTAL CONTINGENCIAS COMUNES + PRORRATA PAGAS EXTRAS	BASE INCAPACIDAD TEMPORAL TOTAL	196.23	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1379	119	aportacion_empresa	MEI	MECANISMO EQUIDAD INTERGENERACIONAL	5.57	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1380	119	aportacion_empresa	AT Y EP	AT Y EP	12.47	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1381	119	aportacion_empresa	DESEMPLEO	DESEMPLEO	45.74	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1382	119	aportacion_empresa	FORMACIÓN PROFESIONAL	FORMACIÓN PROFESIONAL	4.99	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1383	119	aportacion_empresa	FONDO GARANTÍA SALARIAL	FONDO DE GARANTÍA SALARIAL	1.66	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1384	120	devengo	SALARIO BASE	*SALARIO BASE	781.16	t	t	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1385	120	devengo	HORAS NOCTURNAS	*HORAS NOCTURNAS	32.32	t	t	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1386	120	devengo	HORAS COMPLEMENTARIAS	*HORAS COMPLEMENTARIAS	83.50	t	t	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1387	120	devengo	PAGA EXTRA	*PAGA EXTRA	193.17	t	t	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1388	120	deduccion	DTO. CONT. COMUNES	COTIZACIÓN CONTINGENCIAS COMUNES (4,70%)	51.92	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1389	120	deduccion	MEI	COTIZACIÓN MECANISMO EQUIDAD INTERGENERACIONAL (0,13%)	1.44	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1390	120	deduccion	FORMACIÓN PROFESIONAL	COTIZACIÓN FORMACIÓN PROFESIONAL (0,10%)	1.10	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1391	120	deduccion	DESEMPLEO	COTIZACIÓN DESEMPLEO (1,55%)	17.12	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1392	120	aportacion_empresa	TOTAL CONTINGENCIAS COMUNES + PRORRATA PAGAS EXTRAS	BASE INCAPACIDAD TEMPORAL TOTAL	260.64	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1393	120	aportacion_empresa	MEI	MECANISMO EQUIDAD INTERGENERACIONAL	7.39	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1394	120	aportacion_empresa	AT Y EP	AT Y EP	16.56	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1395	120	aportacion_empresa	DESEMPLEO	DESEMPLEO	60.75	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1396	120	aportacion_empresa	FORMACIÓN PROFESIONAL	FORMACIÓN PROFESIONAL	6.64	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1397	120	aportacion_empresa	FONDO GARANTÍA SALARIAL	FONDO DE GARANTÍA SALARIAL	2.21	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1398	121	devengo	SALARIO BASE	*SALARIO BASE	582.35	t	t	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1399	121	devengo	HORAS NOCTURNAS	*HORAS NOCTURNAS	27.27	t	t	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1400	121	devengo	HORAS COMPLEMENTARIAS	*HORAS COMPLEMENTARIAS	16.70	t	t	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1401	121	devengo	PAGA EXTRA	*PAGA EXTRA	144.01	t	t	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1402	121	deduccion	DTO. CONT. COMUNES	COTIZACIÓN CONTINGENCIAS COMUNES (4,70%)	36.97	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1403	121	deduccion	MEI	COTIZACIÓN MECANISMO EQUIDAD INTERGENERACIONAL (0,13%)	1.02	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1404	121	deduccion	FORMACIÓN PROFESIONAL	COTIZACIÓN FORMACIÓN PROFESIONAL (0,10%)	0.79	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1405	121	deduccion	DESEMPLEO	COTIZACIÓN DESEMPLEO (1,55%)	12.19	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1406	121	aportacion_empresa	TOTAL CONTINGENCIAS COMUNES + PRORRATA PAGAS EXTRAS	BASE INCAPACIDAD TEMPORAL TOTAL	185.59	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1407	121	aportacion_empresa	MEI	MECANISMO EQUIDAD INTERGENERACIONAL	5.28	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1408	121	aportacion_empresa	AT Y EP	AT Y EP	11.81	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1409	121	aportacion_empresa	DESEMPLEO	DESEMPLEO	43.25	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1410	121	aportacion_empresa	FORMACIÓN PROFESIONAL	FORMACIÓN PROFESIONAL	4.71	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1411	121	aportacion_empresa	FONDO GARANTÍA SALARIAL	FONDO DE GARANTÍA SALARIAL	1.57	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1412	122	devengo	SALARIO BASE	*SALARIO BASE	538.00	t	t	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1413	122	devengo	HORAS NOCTURNAS	*HORAS NOCTURNAS	28.28	t	t	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1414	122	devengo	PAGA EXTRA	*PAGA EXTRA	133.05	t	t	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1415	122	deduccion	DTO. CONT. COMUNES	COTIZACIÓN CONTINGENCIAS COMUNES (4,70%)	35.69	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1416	122	deduccion	MEI	COTIZACIÓN MECANISMO EQUIDAD INTERGENERACIONAL (0,13%)	0.98	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1417	122	deduccion	FORMACIÓN PROFESIONAL	COTIZACIÓN FORMACIÓN PROFESIONAL (0,10%)	0.76	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1418	122	deduccion	DESEMPLEO	COTIZACIÓN DESEMPLEO (1,55%)	11.77	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1419	122	aportacion_empresa	TOTAL CONTINGENCIAS COMUNES + PRORRATA PAGAS EXTRAS	BASE INCAPACIDAD TEMPORAL TOTAL	179.18	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1420	122	aportacion_empresa	MEI	MECANISMO EQUIDAD INTERGENERACIONAL	5.09	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1421	122	aportacion_empresa	AT Y EP	AT Y EP	11.38	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1422	122	aportacion_empresa	DESEMPLEO	DESEMPLEO	41.76	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1423	122	aportacion_empresa	FORMACIÓN PROFESIONAL	FORMACIÓN PROFESIONAL	4.56	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1424	122	aportacion_empresa	FONDO GARANTÍA SALARIAL	FONDO DE GARANTÍA SALARIAL	1.52	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1425	123	devengo	SALARIO BASE	*SALARIO BASE	479.81	t	t	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1426	123	devengo	HORAS NOCTURNAS	*HORAS NOCTURNAS	27.27	t	t	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1427	123	devengo	PAGA EXTRA	*PAGA EXTRA	118.64	t	t	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1428	123	deduccion	DTO. CONT. COMUNES	COTIZACIÓN CONTINGENCIAS COMUNES (4,70%)	29.40	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1429	123	deduccion	MEI	COTIZACIÓN MECANISMO EQUIDAD INTERGENERACIONAL (0,13%)	0.81	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1430	123	deduccion	FORMACIÓN PROFESIONAL	COTIZACIÓN FORMACIÓN PROFESIONAL (0,10%)	0.63	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1431	123	deduccion	DESEMPLEO	COTIZACIÓN DESEMPLEO (1,55%)	9.70	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1432	123	aportacion_empresa	TOTAL CONTINGENCIAS COMUNES + PRORRATA PAGAS EXTRAS	CONTINGENCIAS COMUNES	147.66	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1433	123	aportacion_empresa	MEI	MECANISMO EQUIDAD INTERGENERACIONAL	4.20	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1434	123	aportacion_empresa	AT Y EP	AT Y EP	9.40	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1435	123	aportacion_empresa	DESEMPLEO	DESEMPLEO	34.41	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1436	123	aportacion_empresa	FORMACIÓN PROFESIONAL	FORMACIÓN PROFESIONAL	3.75	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1437	123	aportacion_empresa	FONDO GARANTÍA SALARIAL	FONDO DE GARANTÍA SALARIAL	1.25	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1438	124	devengo	SALARIO BASE	*SALARIO BASE	174.29	t	t	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1439	124	devengo	PAGA EXTRA	*PAGA EXTRA	43.10	t	t	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1440	124	deduccion	DTO. CONT. COMUNES	COTIZACIÓN CONTINGENCIAS COMUNES (4,70%)	11.84	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1441	124	deduccion	MEI	COTIZACIÓN MECANISMO EQUIDAD INTERGENERACIONAL (0,13%)	0.32	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1442	124	deduccion	FORMACIÓN PROFESIONAL	COTIZACIÓN FORMACIÓN PROFESIONAL (0,10%)	0.25	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1443	124	deduccion	DESEMPLEO	COTIZACIÓN DESEMPLEO (1,55%)	3.90	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1444	124	deduccion	RETENCION IRPF	TRIBUTACIÓN IRPF (2,00%)	4.35	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1445	124	aportacion_empresa	TOTAL CONTINGENCIAS COMUNES + PRORRATA PAGAS EXTRAS	BASE INCAPACIDAD TEMPORAL TOTAL	59.45	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1446	124	aportacion_empresa	MEI	MECANISMO EQUIDAD INTERGENERACIONAL	1.69	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1447	124	aportacion_empresa	AT Y EP	AT Y EP	3.77	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1448	124	aportacion_empresa	DESEMPLEO	DESEMPLEO	13.85	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1449	124	aportacion_empresa	FORMACIÓN PROFESIONAL	FORMACIÓN PROFESIONAL	1.51	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1450	124	aportacion_empresa	FONDO GARANTÍA SALARIAL	FONDO DE GARANTÍA SALARIAL	0.51	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1451	125	devengo	SALARIO BASE	*SALARIO BASE	467.55	t	t	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1452	125	devengo	PAGA EXTRA	*PAGA EXTRA	115.62	t	t	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1453	125	deduccion	DTO. CONT. COMUNES	COTIZACIÓN CONTINGENCIAS COMUNES (4,70%)	27.41	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1454	125	deduccion	MEI	COTIZACIÓN MECANISMO EQUIDAD INTERGENERACIONAL (0,13%)	0.76	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1455	125	deduccion	DTO. SEGURIDAD SOCIAL	COTIZACIÓN FORMACIÓN PROFESIONAL (0,10%)	0.58	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1456	125	deduccion	DTO. BASE ACCIDENTE	COTIZACIÓN DESEMPLEO (1,60%)	9.33	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1457	125	aportacion_empresa	TOTAL CONTINGENCIAS COMUNES + PRORRATA PAGAS EXTRAS	BASE INCAPACIDAD TEMPORAL TOTAL	137.63	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1458	125	aportacion_empresa	MEI	MECANISMO EQUIDAD INTERGENERACIONAL	3.91	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1459	125	aportacion_empresa	AT Y EP	AT Y EP	8.75	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1460	125	aportacion_empresa	DESEMPLEO	DESEMPLEO	39.07	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1461	125	aportacion_empresa	FORMACIÓN PROFESIONAL	FORMACIÓN PROFESIONAL	3.50	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1462	125	aportacion_empresa	FONDO GARANTÍA SALARIAL	FONDO DE GARANTÍA SALARIAL	1.17	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1463	126	devengo	SALARIO BASE	*SALARIO BASE	1001.89	t	t	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1464	126	devengo	PAGA EXTRA	*PAGA EXTRA	247.75	t	t	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1465	126	deduccion	DTO. CONT. COMUNES	COTIZACIÓN CONTINGENCIAS COMUNES (4,70%)	59.11	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1466	126	deduccion	MEI	COTIZACIÓN MECANISMO EQUIDAD INTERGENERACIONAL (0,13%)	1.63	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1467	126	deduccion	FORMACIÓN PROFESIONAL	COTIZACIÓN FORMACIÓN PROFESIONAL (0,10%)	1.26	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1468	126	deduccion	DESEMPLEO	COTIZACIÓN DESEMPLEO (1,60%)	3.46	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1469	126	deduccion	DESEMPLEO	COTIZACIÓN DESEMPLEO (1,55%)	16.14	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1470	126	deduccion	RETENCION IRPF	TRIBUTACIÓN IRPF (8,00%)	99.97	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1471	126	aportacion_empresa	TOTAL CONTINGENCIAS COMUNES + PRORRATA PAGAS EXTRAS	BASE INCAPACIDAD TEMPORAL TOTAL	296.81	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1472	126	aportacion_empresa	MEI	MECANISMO EQUIDAD INTERGENERACIONAL	8.43	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1473	126	aportacion_empresa	AT Y EP	AT Y EP	18.86	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1474	126	aportacion_empresa	DESEMPLEO	DESEMPLEO	71.77	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1475	126	aportacion_empresa	FORMACIÓN PROFESIONAL	FORMACIÓN PROFESIONAL	7.55	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1476	126	aportacion_empresa	FONDO GARANTÍA SALARIAL	FONDO DE GARANTÍA SALARIAL	2.51	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1477	127	devengo	SALARIO BASE	*SALARIO BASE	1252.37	t	t	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1478	127	devengo	PAGA EXTRA	*PAGA EXTRA	309.69	t	t	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1479	127	deduccion	DTO. CONT. COMUNES	COTIZACIÓN CONTINGENCIAS COMUNES (4,70%)	73.42	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1480	127	deduccion	MEI	COTIZACIÓN MECANISMO EQUIDAD INTERGENERACIONAL (0,13%)	2.03	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1481	127	deduccion	DTO. SEGURIDAD SOCIAL	COTIZACIÓN FORMACIÓN PROFESIONAL (0,10%)	1.56	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1482	127	deduccion	DTO. BASE ACCIDENTE	COTIZACIÓN DESEMPLEO (1,55%)	24.21	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1483	127	deduccion	RETENCION IRPF	TRIBUTACIÓN IRPF (8,00%)	124.96	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1484	127	aportacion_empresa	TOTAL CONTINGENCIAS COMUNES + PRORRATA PAGAS EXTRAS	BASE INCAPACIDAD TEMPORAL TOTAL	368.65	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1485	127	aportacion_empresa	MEI	MECANISMO EQUIDAD INTERGENERACIONAL	10.47	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1486	127	aportacion_empresa	AT Y EP	AT Y EP	23.43	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1487	127	aportacion_empresa	DESEMPLEO	DESEMPLEO	85.91	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1488	127	aportacion_empresa	FORMACIÓN PROFESIONAL	FORMACIÓN PROFESIONAL	9.37	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1489	127	aportacion_empresa	FONDO GARANTÍA SALARIAL	FONDO DE GARANTÍA SALARIAL	3.12	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1490	128	devengo	SALARIO BASE	SALARIO BASE	1252.37	t	t	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1491	128	devengo	PAGA EXTRA	PAGA EXTRA	309.69	t	t	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1492	128	deduccion	DTO. CONT. COMUNES	COTIZACIÓN CONTINGENCIAS COMUNES (4,70%)	73.42	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1493	128	deduccion	MEI	COTIZACIÓN MECANISMO EQUIDAD INTERGENERACIONAL (0,13%)	2.03	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1494	128	deduccion	DTO. SEGURIDAD SOCIAL	COTIZACIÓN FORMACIÓN PROFESIONAL (0,10%)	1.56	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1495	128	deduccion	DTO. SEGURIDAD SOCIAL	COTIZACIÓN DESEMPLEO (1,55%)	24.21	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1496	128	deduccion	RETENCION IRPF	TRIBUTACIÓN IRPF (8,00%)	124.96	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1497	128	aportacion_empresa	TOTAL CONTINGENCIAS COMUNES + PRORRATA PAGAS EXTRAS	CONTINGENCIAS COMUNES	368.65	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1498	128	aportacion_empresa	MEI	MECANISMO EQUIDAD INTERGENERACIONAL	10.47	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1499	128	aportacion_empresa	AT Y EP	AT Y EP	23.43	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1500	128	aportacion_empresa	DESEMPLEO	DESEMPLEO	85.91	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1501	128	aportacion_empresa	FORMACIÓN PROFESIONAL	FORMACIÓN PROFESIONAL	9.37	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1502	128	aportacion_empresa	FONDO GARANTÍA SALARIAL	FONDO DE GARANTÍA SALARIAL	3.12	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1503	129	devengo	SALARIO BASE	*SALARIO BASE	1252.37	t	t	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1504	129	devengo	PAGA EXTRA	*PAGA EXTRA	309.69	t	t	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1505	129	deduccion	DTO. CONT. COMUNES	COTIZACIÓN CONTINGENCIAS COMUNES (4,70%)	73.42	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1506	129	deduccion	MEI	COTIZACIÓN MECANISMO EQUIDAD INTERGENERACIONAL (0,13%)	2.03	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1507	129	deduccion	DTO. SEGURIDAD SOCIAL	COTIZACIÓN FORMACIÓN PROFESIONAL (0,10%)	1.56	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1508	129	deduccion	DTO. SEGURIDAD SOCIAL	COTIZACIÓN DESEMPLEO (1,55%)	24.21	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1509	129	deduccion	RETENCION IRPF	TRIBUTACIÓN IRPF (8,00%)	124.96	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1510	129	aportacion_empresa	TOTAL CONTINGENCIAS COMUNES + PRORRATA PAGAS EXTRAS	BASE INCAPACIDAD TEMPORAL TOTAL	368.65	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1511	129	aportacion_empresa	MEI	MECANISMO EQUIDAD INTERGENERACIONAL	10.47	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1512	129	aportacion_empresa	AT Y EP	AT Y EP	23.43	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1513	129	aportacion_empresa	DESEMPLEO	DESEMPLEO	85.91	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1514	129	aportacion_empresa	FORMACIÓN PROFESIONAL	FORMACIÓN PROFESIONAL	9.37	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1515	129	aportacion_empresa	FONDO GARANTÍA SALARIAL	FONDO DE GARANTÍA SALARIAL	3.12	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1516	130	devengo	SALARIO BASE	*SALARIO BASE	1252.37	t	t	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1517	130	devengo	PAGA EXTRA	*PAGA EXTRA	309.69	t	t	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1518	130	deduccion	DTO. CONT. COMUNES	COTIZACIÓN CONTINGENCIAS COMUNES (4,70%)	73.42	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1519	130	deduccion	MEI	COTIZACIÓN MECANISMO EQUIDAD INTERGENERACIONAL (0,13%)	2.03	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1520	130	deduccion	FORMACIÓN PROFESIONAL	COTIZACIÓN FORMACIÓN PROFESIONAL (0,10%)	1.56	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1521	130	deduccion	DESEMPLEO	COTIZACIÓN DESEMPLEO (1,55%)	24.21	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1522	130	deduccion	RETENCION IRPF	TRIBUTACIÓN IRPF (8,00%)	124.96	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1523	130	aportacion_empresa	TOTAL CONTINGENCIAS COMUNES + PRORRATA PAGAS EXTRAS	BASE INCAPACIDAD TEMPORAL TOTAL	368.65	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1524	130	aportacion_empresa	MEI	MECANISMO EQUIDAD INTERGENERACIONAL	10.47	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1525	130	aportacion_empresa	AT Y EP	AT Y EP	23.43	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1526	130	aportacion_empresa	DESEMPLEO	DESEMPLEO	85.91	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1527	130	aportacion_empresa	FORMACIÓN PROFESIONAL	FORMACIÓN PROFESIONAL	9.37	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1528	130	aportacion_empresa	FONDO GARANTÍA SALARIAL	FONDO DE GARANTÍA SALARIAL	3.12	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1529	131	devengo	SALARIO BASE	SALARIO BASE	485.03	t	t	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1530	131	devengo	NOCTURNIDAD	HORAS NOCTURNAS	25.25	t	t	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1531	131	devengo	PAGA EXTRA	PAGA EXTRA	119.93	t	t	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1532	131	deduccion	DTO. CONT. COMUNES	COTIZACIÓN CONTINGENCIAS COMUNES (4,70%)	30.42	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1533	131	deduccion	MEI	COTIZACIÓN MECANISMO EQUIDAD INTERGENERACIONAL (0,13%)	0.84	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1534	131	deduccion	DTO. SEGURIDAD SOCIAL	COTIZACIÓN FORMACIÓN PROFESIONAL (0,10%)	0.64	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1535	131	deduccion	DTO. SEGURIDAD SOCIAL	COTIZACIÓN DESEMPLEO (1,55%)	10.03	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1536	131	deduccion	RETENCION IRPF	TRIBUTACIÓN IRPF (2,00%)	12.61	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1537	131	aportacion_empresa	TOTAL CONTINGENCIAS COMUNES + PRORRATA PAGAS EXTRAS	BASE INCAPACIDAD TEMPORAL TOTAL	152.73	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1538	131	aportacion_empresa	MEI	MECANISMO EQUIDAD INTERGENERACIONAL	4.34	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1539	131	aportacion_empresa	AT Y EP	AT Y EP	9.70	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1540	131	aportacion_empresa	DESEMPLEO	DESEMPLEO	35.60	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1541	131	aportacion_empresa	FORMACIÓN PROFESIONAL	FORMACIÓN PROFESIONAL	3.88	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1542	131	aportacion_empresa	FONDO GARANTÍA SALARIAL	FONDO DE GARANTÍA SALARIAL	1.29	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1543	132	devengo	SALARIO BASE	*SALARIO BASE	880.83	t	t	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1544	132	devengo	HORAS NOCTURNAS	*HORAS NOCTURNAS	34.34	t	t	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1545	132	devengo	HORAS COMPLEMENTARIAS	*HORAS COMPLEMENTARIAS	41.75	t	t	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1546	132	devengo	PAGA EXTRA	*PAGA EXTRA	217.82	t	t	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1547	132	deduccion	DTO. CONT. COMUNES	COTIZACIÓN CONTINGENCIAS COMUNES (4,70%)	60.19	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1548	132	deduccion	MEI	COTIZACIÓN MECANISMO EQUIDAD INTERGENERACIONAL (0,13%)	1.67	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1549	132	deduccion	FORMACIÓN PROFESIONAL	COTIZACIÓN FORMACIÓN PROFESIONAL (0,10%)	1.27	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1550	132	deduccion	DESEMPLEO	COTIZACIÓN DESEMPLEO (1,55%)	19.84	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1551	132	deduccion	RETENCION IRPF	TRIBUTACIÓN IRPF (2,00%)	23.49	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1552	132	aportacion_empresa	TOTAL CONTINGENCIAS COMUNES + PRORRATA PAGAS EXTRAS	BASE INCAPACIDAD TEMPORAL TOTAL	302.22	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1553	132	aportacion_empresa	MEI	MECANISMO EQUIDAD INTERGENERACIONAL	8.57	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1554	132	aportacion_empresa	AT Y EP	AT Y EP	19.21	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1555	132	aportacion_empresa	DESEMPLEO	DESEMPLEO	70.43	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1556	132	aportacion_empresa	FORMACIÓN PROFESIONAL	FORMACIÓN PROFESIONAL	7.68	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1557	132	aportacion_empresa	FONDO GARANTÍA SALARIAL	FONDO DE GARANTÍA SALARIAL	2.56	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1558	133	devengo	SALARIO BASE	*SALARIO BASE	870.93	t	t	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1559	133	devengo	HORAS NOCTURNAS	*HORAS NOCTURNAS	33.33	t	t	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1560	133	devengo	PAGA EXTRA	*PAGA EXTRA	215.37	t	t	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1561	133	deduccion	DTO. CONT. COMUNES	COTIZACIÓN CONTINGENCIAS COMUNES (4,70%)	52.63	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1562	133	deduccion	MEI	COTIZACIÓN MECANISMO EQUIDAD INTERGENERACIONAL (0,13%)	1.46	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1563	133	deduccion	FORMACIÓN PROFESIONAL	COTIZACIÓN FORMACIÓN PROFESIONAL (0,10%)	1.11	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1564	133	deduccion	DESEMPLEO	COTIZACIÓN DESEMPLEO (1,55%)	17.36	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1565	133	deduccion	RETENCION IRPF	TRIBUTACIÓN IRPF (2,00%)	22.40	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1566	133	aportacion_empresa	TOTAL CONTINGENCIAS COMUNES + PRORRATA PAGAS EXTRAS	BASE INCAPACIDAD TEMPORAL TOTAL	264.23	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1567	133	aportacion_empresa	MEI	MECANISMO EQUIDAD INTERGENERACIONAL	7.49	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1568	133	aportacion_empresa	AT Y EP	AT Y EP	16.79	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1569	133	aportacion_empresa	DESEMPLEO	DESEMPLEO	61.58	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1570	133	aportacion_empresa	FORMACIÓN PROFESIONAL	FORMACIÓN PROFESIONAL	6.72	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1571	133	aportacion_empresa	FONDO GARANTÍA SALARIAL	FONDO DE GARANTÍA SALARIAL	2.24	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1572	134	deduccion	PREAVISO	DESCUENTO PREAVISO	285.08	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1573	140	devengo	VACACIONES NO DISFRUTADAS	PARTE PROPORCIONAL VACACIONES	135.00	t	t	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1574	140	deduccion	COTIZACIÓN CONTINGENCIAS COMUNES	COTIZACIÓN CONTINGENCIAS COMUNES (4,70%)	6.35	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1575	140	deduccion	COTIZACIÓN MEI	COTIZACIÓN MECANISMO EQUIDAD INTERGENERACIONAL (0,13%)	0.18	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1576	140	deduccion	COTIZACIÓN FORMACIÓN PROFESIONAL	COTIZACIÓN FORMACIÓN PROFESIONAL (0,10%)	0.14	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1577	140	deduccion	COTIZACIÓN DESEMPLEO	COTIZACIÓN DESEMPLEO (1,55%)	2.09	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
1578	140	deduccion	RETENCION IRPF	TRIBUTACIÓN IRPF (2,00%)	2.70	f	f	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
929	86	devengo	COMPLEMENTO I.T.	COMPLEMENTO I.T.	94.01	t	t	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 13:40:34.731962+00
943	87	devengo	COMPLEMENTO I.T.	COMPLEMENTO I.T.	439.91	t	t	f	f	f	f	2025-12-31 12:13:30.253855+00	2025-12-31 13:40:34.731962+00
\.


--
-- Data for Name: payrolls; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.payrolls (id, employee_id, type, periodo, devengo_total, deduccion_total, aportacion_empresa_total, liquido_a_percibir, prorrata_pagas_extra, base_cc, base_at_ep, base_irpf, tipo_irpf, warnings, is_merged, merged_from_files, created_at, updated_at) FROM stdin;
1	6	payslip	{"desde": "2025-01-01", "hasta": "2025-01-31", "dias": 30}	1131.32	77.29	382.56	1054.03	0.00	1192.89	1192.89	1131.32	0.00	["Standardized the format of the worker's name.", "Standardized the format of the Social Security Affiliation Number.", "The value 'aportacion_empresa_total' was not found and has been calculated by summing its components."]	f	\N	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
2	6	payslip	{"desde": "2025-02-01", "hasta": "2025-02-28", "dias": 30}	1075.23	72.08	356.72	1003.15	0.00	1112.36	1112.36	1075.23	0.00	["Standardized the format of the worker's name.", "Standardized the format of the Social Security Affiliation Number.", "The value 'aportacion_empresa_total' was not found and has been calculated by summing its components."]	f	\N	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
3	6	payslip	{"desde": "2025-03-01", "hasta": "2025-03-31", "dias": 30}	1137.91	75.88	375.51	1062.03	0.00	1170.87	1170.87	1137.91	0.00	["Standardized the format of the worker's name.", "Standardized the format of the Social Security Affiliation Number.", "The value 'aportacion_empresa_total' was not found and has been calculated by summing its components."]	f	\N	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
4	6	payslip	{"desde": "2025-04-01", "hasta": "2025-04-30", "dias": 30}	1125.43	72.93	360.92	1052.50	0.00	1125.43	1125.43	1125.43	0.00	["Standardized the format of the worker's name.", "Standardized the format of the Social Security Affiliation Number.", "The value 'aportacion_empresa_total' was not found and has been calculated by summing its components."]	f	\N	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
5	6	payslip	{"desde": "2025-05-01", "hasta": "2025-05-31", "dias": 30}	1155.53	74.88	370.57	1080.65	0.00	1155.53	1155.53	1155.53	0.00	["Standardized the format of the worker's name.", "Standardized the format of the Social Security Affiliation Number.", "The value 'aportacion_empresa_total' was not found and has been calculated by summing its components."]	f	\N	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
6	6	payslip	{"desde": "2025-06-01", "hasta": "2025-06-30", "dias": 30}	1128.46	188.42	361.91	940.04	0.00	1128.46	1128.46	1128.46	0.00	["Standardized the format of the worker's name.", "Standardized the format of the Social Security Affiliation Number.", "The value 'aportacion_empresa_total' was not found and has been calculated by summing its components.", "The concept '*ABSENTISMO' was moved to deductions as it represents a discount from gross pay."]	f	\N	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
7	6	payslip	{"desde": "2025-07-01", "hasta": "2025-07-31", "dias": 30}	1125.43	175.41	360.92	950.02	0.00	1125.43	1125.43	1125.43	0.00	["Standardized the format of the worker's name.", "Standardized the format of the Social Security Affiliation Number.", "The value 'aportacion_empresa_total' was not found and has been calculated by summing its components."]	f	\N	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
8	12	payslip	{"desde": "2025-02-21", "hasta": "2025-02-28", "dias": 10}	303.31	19.65	97.28	283.66	0.00	303.31	303.31	303.31	0.00	["Standardized the format of the worker's name.", "Standardized the format of the Social Security Affiliation Number.", "The value 'aportacion_empresa_total' was not found and has been calculated by summing its components."]	f	\N	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
9	12	payslip	{"desde": "2025-03-01", "hasta": "2025-03-31", "dias": 30}	920.03	59.62	295.05	860.41	0.00	920.03	920.03	920.03	0.00	["Standardized the format of the worker's name.", "Standardized the format of the Social Security Affiliation Number.", "The value 'aportacion_empresa_total' was not found and has been calculated by summing its components."]	f	\N	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
10	12	payslip	{"desde": "2025-04-01", "hasta": "2025-04-30", "dias": 30}	1145.76	75.03	371.33	1070.73	0.00	1157.83	1157.83	1145.76	0.00	["Standardized the format of the worker's name.", "Standardized the format of the Social Security Affiliation Number.", "The value 'aportacion_empresa_total' was not found and has been calculated by summing its components."]	f	\N	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
11	12	payslip	{"desde": "2025-05-01", "hasta": "2025-05-31", "dias": 30}	857.97	65.27	323.02	792.70	0.00	1007.24	1007.24	857.97	0.00	["Standardized the format of the worker's name.", "Standardized the format of the Social Security Affiliation Number.", "The value 'aportacion_empresa_total' was not found and has been calculated by summing its components."]	f	\N	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
12	12	payslip	{"desde": "2025-06-01", "hasta": "2025-06-30", "dias": 30}	695.17	63.08	312.20	632.09	0.00	973.50	973.50	695.17	0.00	["Standardized the format of the worker's name.", "Standardized the format of the Social Security Affiliation Number.", "The value 'aportacion_empresa_total' was not found and has been calculated by summing its components."]	f	\N	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
13	12	payslip	{"desde": "2025-07-01", "hasta": "2025-07-10", "dias": 10}	305.52	20.44	101.12	285.08	0.00	315.33	315.33	305.52	0.00	["Standardized the format of the worker's name.", "Standardized the format of the Social Security Affiliation Number.", "The value 'aportacion_empresa_total' was not found and has been calculated by summing its components."]	f	\N	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
14	19	payslip	{"desde": "2025-01-01", "hasta": "2025-01-31", "dias": 30}	750.00	262.50	0.00	487.50	0.00	0.00	0.00	750.00	35.00	["Standardized the format of the worker's name.", "Standardized the format of the Social Security Affiliation Number.", "The value 'aportacion_empresa_total' was not found and has been set to 0.0 as no employer contribution details were provided in the breakdown."]	f	\N	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
15	19	payslip	{"desde": "2025-02-01", "hasta": "2025-02-28", "dias": 30}	750.00	262.50	0.00	487.50	0.00	0.00	0.00	750.00	35.00	["Standardized the format of the worker's name.", "Standardized the format of the Social Security Affiliation Number.", "The value 'aportacion_empresa_total' was not found and has been set to 0.0 as no employer contribution items were listed in the breakdown."]	f	\N	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
16	19	payslip	{"desde": "2025-03-01", "hasta": "2025-03-31", "dias": 30}	750.00	262.50	0.00	487.50	0.00	0.00	0.00	750.00	35.00	["Standardized the format of the worker's name.", "Standardized the format of the Social Security Affiliation Number.", "No employer contribution items were found in the document."]	f	\N	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
17	19	payslip	{"desde": "2025-04-01", "hasta": "2025-04-30", "dias": 30}	750.00	262.50	0.00	487.50	0.00	0.00	0.00	750.00	35.00	["Standardized the format of the worker's name.", "Standardized the format of the Social Security Affiliation Number.", "The value 'aportacion_empresa_total' was not found and has been calculated by summing its components.", "Social Security contribution bases and employer contributions are missing or not specified in the document."]	f	\N	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
18	19	payslip	{"desde": "2025-09-01", "hasta": "2025-09-30", "dias": 30}	750.00	262.50	0.00	487.50	0.00	0.00	0.00	750.00	35.00	["Standardized the format of the worker's name.", "Standardized the format of the Social Security Affiliation Number.", "The value 'aportacion_empresa_total' was not found and has been set to 0.0 as no employer contribution items were listed in the breakdown."]	f	\N	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
19	19	payslip	{"desde": "2025-10-01", "hasta": "2025-10-31", "dias": 30}	750.00	262.50	0.00	487.50	0.00	0.00	0.00	750.00	35.00	["Standardized the format of the worker's name.", "Standardized the format of the Social Security Affiliation Number.", "The value 'aportacion_empresa_total' was not found and has been set to 0.0 as no employer contribution items were listed in the breakdown."]	f	\N	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
20	19	payslip	{"desde": "2025-11-01", "hasta": "2025-11-30", "dias": 30}	750.00	262.50	0.00	487.50	0.00	0.00	0.00	750.00	35.00	["Standardized the format of the worker's name.", "Standardized the format of the Social Security Affiliation Number.", "The value 'aportacion_empresa_total' was not found and has been set to 0.0 as no contribution details were provided in the breakdown."]	f	\N	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
21	16	payslip	{"desde": "2025-01-01", "hasta": "2025-01-31", "dias": 30}	2015.00	221.65	0.00	1793.35	0.00	0.00	0.00	2015.00	11.00	["Standardized the format of the worker's name.", "Standardized the format of the Social Security Affiliation Number.", "The value 'aportacion_empresa_total' was not found and has been set to 0.0 as no employer contribution details were provided in the document."]	f	\N	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
22	16	payslip	{"desde": "2025-02-01", "hasta": "2025-02-28", "dias": 30}	2015.00	221.65	0.00	1793.35	0.00	0.00	0.00	2015.00	11.00	["Standardized the format of the worker's name.", "Standardized the format of the Social Security Affiliation Number.", "The value 'aportacion_empresa_total' was not found and has been set to 0.0 as no employer contribution details were provided in the document."]	f	\N	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
23	16	payslip	{"desde": "2025-03-01", "hasta": "2025-03-31", "dias": 30}	1381.33	40.20	0.00	1341.13	0.00	0.00	0.00	1381.33	2.91	["Standardized the format of the worker's name.", "Standardized the format of the Social Security Affiliation Number.", "The value 'aportacion_empresa_total' was set to 0.0 as no employer contribution details were found in the provided document section."]	f	\N	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
24	16	payslip	{"desde": "2025-04-01", "hasta": "2025-04-30", "dias": 30}	1715.34	49.92	0.00	1665.42	0.00	0.00	0.00	1715.34	2.91	["Standardized the format of the worker's name.", "Standardized the format of the Social Security Affiliation Number.", "The value 'aportacion_empresa_total' was not found and has been set to 0.0 as no contribution details were provided in the document."]	f	\N	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
25	16	payslip	{"desde": "2025-05-01", "hasta": "2025-05-31", "dias": 30}	1715.34	49.92	0.00	1665.42	0.00	0.00	0.00	1715.34	2.91	["Standardized the format of the worker's name.", "Standardized the format of the Social Security Affiliation Number.", "The value 'aportacion_empresa_total' was not found and has been set to 0.0 as no employer contribution items were listed in the breakdown."]	f	\N	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
26	16	payslip	{"desde": "2025-06-01", "hasta": "2025-06-30", "dias": 30}	1715.34	49.92	0.00	1665.42	0.00	0.00	0.00	1715.34	2.91	["Standardized the format of the worker's name.", "Standardized the format of the Social Security Affiliation Number.", "The value 'aportacion_empresa_total' was not found and has been set to 0.0 as no employer contribution items were listed in the breakdown section."]	f	\N	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
27	16	payslip	{"desde": "2025-07-01", "hasta": "2025-07-31", "dias": 30}	1715.34	49.92	0.00	1665.42	0.00	0.00	0.00	1715.34	2.91	["Standardized the format of the worker's name.", "Standardized the format of the Social Security Affiliation Number.", "The value 'aportacion_empresa_total' was not found and has been set to 0.0 as no employer contribution items were listed in the breakdown."]	f	\N	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
28	16	payslip	{"desde": "2025-08-01", "hasta": "2025-08-31", "dias": 30}	1715.34	49.92	0.00	1665.42	0.00	0.00	0.00	1715.34	2.91	["Standardized the format of the worker's name.", "Standardized the format of the Social Security Affiliation Number.", "The value 'aportacion_empresa_total' was not found and has been set to 0.0 as no employer contribution items were listed in the breakdown."]	f	\N	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
29	16	payslip	{"desde": "2025-09-01", "hasta": "2025-09-30", "dias": 30}	1715.34	257.30	0.00	1458.04	0.00	0.00	0.00	1715.34	15.00	["Standardized the format of the worker's name.", "Standardized the format of the Social Security Affiliation Number.", "The value 'aportacion_empresa_total' was not found and has been set to 0.0 as no employer contribution items were listed in the document."]	f	\N	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
30	16	payslip	{"desde": "2025-10-01", "hasta": "2025-10-31", "dias": 30}	1715.34	257.30	0.00	1458.04	0.00	0.00	0.00	1715.34	15.00	["Standardized the format of the worker's name.", "Standardized the format of the Social Security Affiliation Number.", "The value 'aportacion_empresa_total' was set to 0.0 as the employer contribution section is empty in the document.", "Social Security contribution bases (CC, AT/EP) were not explicitly found in the totals section and set to null."]	f	\N	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
31	16	payslip	{"desde": "2025-11-01", "hasta": "2025-11-30", "dias": 30}	1715.34	257.30	0.00	1458.04	0.00	0.00	0.00	1715.34	15.00	["Standardized the format of the worker's name.", "Standardized the format of the Social Security Affiliation Number.", "The value 'aportacion_empresa_total' was not found and has been set to 0.0 as no employer contribution items were listed in the breakdown."]	f	\N	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
32	11	payslip	{"desde": "2025-04-01", "hasta": "2025-04-30", "dias": 30}	846.23	55.66	275.46	790.57	0.00	859.00	859.00	846.23	0.00	["Standardized the format of the worker's name.", "Standardized the format of the Social Security Affiliation Number.", "The value 'aportacion_empresa_total' was not found and has been calculated by summing its components."]	f	\N	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
33	11	payslip	{"desde": "2025-01-01", "hasta": "2025-01-31", "dias": 30}	900.99	61.38	303.80	839.61	0.00	947.27	947.27	900.99	0.00	["Standardized the format of the worker's name.", "Standardized the format of the Social Security Affiliation Number.", "The value 'aportacion_empresa_total' was not found and has been calculated by summing its components."]	f	\N	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
34	11	payslip	{"desde": "2025-02-01", "hasta": "2025-02-28", "dias": 30}	847.52	54.92	271.80	792.60	0.00	847.52	847.52	847.52	0.00	["Standardized the format of the worker's name.", "Standardized the format of the Social Security Affiliation Number.", "The value 'aportacion_empresa_total' was not found and has been calculated by summing its components."]	f	\N	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
35	11	payslip	{"desde": "2025-03-01", "hasta": "2025-03-31", "dias": 30}	842.50	56.19	278.03	786.31	0.00	866.94	866.94	842.50	0.00	["Standardized the format of the worker's name.", "Standardized the format of the Social Security Affiliation Number.", "The value 'aportacion_empresa_total' was not found and has been calculated by summing its components."]	f	\N	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
36	11	payslip	{"desde": "2025-05-01", "hasta": "2025-05-31", "dias": 30}	860.90	58.35	288.82	802.55	0.00	900.56	900.56	860.90	0.00	["Standardized the format of the worker's name.", "Standardized the format of the Social Security Affiliation Number.", "The value 'aportacion_empresa_total' was not found and has been calculated by summing its components."]	f	\N	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
37	11	payslip	{"desde": "2025-06-01", "hasta": "2025-06-30", "dias": 30}	931.78	61.33	303.50	870.45	0.00	946.36	946.36	931.78	0.00	["Standardized the format of the worker's name.", "Standardized the format of the Social Security Affiliation Number.", "The value 'aportacion_empresa_total' was not found and has been calculated by summing its components."]	f	\N	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
38	11	payslip	{"desde": "2025-07-01", "hasta": "2025-07-31", "dias": 30}	984.49	69.44	343.60	915.05	0.00	1071.43	1071.43	984.49	0.00	["Standardized the format of the worker's name.", "Standardized the format of the Social Security Affiliation Number.", "The value 'aportacion_empresa_total' was not found and has been calculated by summing its components."]	f	\N	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
39	11	payslip	{"desde": "2025-08-01", "hasta": "2025-08-31", "dias": 30}	1480.86	97.33	481.69	1383.53	0.00	1502.03	1502.03	1480.86	0.00	["Standardized the format of the worker's name.", "Standardized the format of the Social Security Affiliation Number.", "The value 'aportacion_empresa_total' was not found and has been calculated by summing its components."]	f	\N	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
40	11	payslip	{"desde": "2025-09-01", "hasta": "2025-09-30", "dias": 30}	971.06	64.09	317.07	906.97	0.00	988.80	988.80	971.06	0.00	["Standardized the format of the worker's name.", "Standardized the format of the Social Security Affiliation Number.", "The value 'aportacion_empresa_total' was not found and has been calculated by summing its components."]	f	\N	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
41	11	payslip	{"desde": "2025-10-01", "hasta": "2025-10-31", "dias": 30}	804.07	56.49	279.68	747.58	0.00	872.05	872.05	804.07	0.00	["Standardized the format of the worker's name.", "Standardized the format of the Social Security Affiliation Number.", "The value 'aportacion_empresa_total' was not found and has been calculated by summing its components."]	f	\N	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
42	11	payslip	{"desde": "2025-11-01", "hasta": "2025-11-30", "dias": 30}	837.45	54.27	268.59	783.18	0.00	837.45	837.45	837.45	0.00	["Standardized the format of the worker's name.", "Standardized the format of the Social Security Affiliation Number.", "The value 'aportacion_empresa_total' was not found and has been calculated by summing its components."]	f	\N	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
43	14	payslip	{"desde": "2025-04-01", "hasta": "2025-04-30", "dias": 30}	822.04	53.27	263.62	768.77	0.00	822.04	822.04	822.04	0.00	["Standardized the format of the worker's name.", "Standardized the format of the Social Security Affiliation Number.", "The value 'aportacion_empresa_total' was not found and has been calculated by summing its components."]	f	\N	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
44	14	payslip	{"desde": "2025-05-01", "hasta": "2025-05-31", "dias": 30}	794.29	51.46	254.73	742.83	0.00	794.29	794.29	794.29	0.00	["Standardized the format of the worker's name.", "Standardized the format of the Social Security Affiliation Number.", "The value 'aportacion_empresa_total' was not found and has been calculated by summing its components."]	f	\N	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
45	14	payslip	{"desde": "2025-06-01", "hasta": "2025-06-11", "dias": 11}	284.57	18.43	91.27	266.14	0.00	284.57	284.57	284.57	0.00	["Standardized the format of the worker's name.", "Standardized the format of the Social Security Affiliation Number.", "The value 'aportacion_empresa_total' was not found and has been calculated by summing its components."]	f	\N	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
46	2	payslip	{"desde": "2025-06-20", "hasta": "2025-06-26", "dias": 7}	145.80	12.44	48.51	133.36	0.00	145.80	145.80	145.80	2.00	["Standardized the format of the worker's name.", "Standardized the format of the Social Security Affiliation Number.", "The value 'aportacion_empresa_total' was not found and has been calculated by summing its components."]	f	\N	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
47	2	payslip	{"desde": "2025-07-07", "hasta": "2025-07-31", "dias": 24}	523.03	48.15	186.64	474.88	0.00	581.95	581.95	523.03	2.00	["Standardized the format of the worker's name.", "Standardized the format of the Social Security Affiliation Number.", "The value 'aportacion_empresa_total' was not found and has been calculated by summing its components.", "The start date of the period was adjusted to the seniority date (2025-07-07) as the document indicates '7 Julio 2025'."]	f	\N	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
48	2	payslip	{"desde": "2025-08-01", "hasta": "2025-08-31", "dias": 30}	696.55	59.68	226.46	636.87	0.00	706.15	706.15	696.55	2.00	["Standardized the format of the worker's name.", "Standardized the format of the Social Security Affiliation Number.", "The value 'aportacion_empresa_total' was not found and has been calculated by summing its components."]	f	\N	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
49	2	payslip	{"desde": "2025-09-01", "hasta": "2025-09-07", "dias": 7}	113.90	9.66	36.52	104.24	0.00	113.90	113.90	113.90	2.00	["Standardized the format of the worker's name.", "Standardized the format of the Social Security Affiliation Number.", "The value 'aportacion_empresa_total' was not found and has been calculated by summing its components."]	f	\N	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
50	2	payslip	{"desde": "2025-11-08", "hasta": "2025-11-30", "dias": 23}	341.62	30.37	116.51	311.25	0.00	363.33	363.33	341.62	2.00	["Standardized the format of the worker's name.", "Standardized the format of the Social Security Affiliation Number.", "The value 'aportacion_empresa_total' was not found and has been calculated by summing its components."]	f	\N	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
51	20	payslip	{"desde": "2025-01-08", "hasta": "2025-01-10", "dias": 3}	22.77	1.54	7.67	21.23	0.00	23.91	23.91	22.77	0.00	["Standardized the format of the worker's name.", "Standardized the format of the Social Security Affiliation Number.", "The value 'aportacion_empresa_total' was not found and has been calculated by summing its components."]	f	\N	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
52	3	payslip	{"desde": "2025-06-17", "hasta": "2025-06-30", "dias": 14}	265.56	23.09	88.01	242.47	0.00	274.39	274.39	265.56	2.00	["Standardized the format of the worker's name.", "Standardized the format of the Social Security Affiliation Number.", "The value 'aportacion_empresa_total' was not found and has been calculated by summing its components."]	f	\N	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
53	3	payslip	{"desde": "2025-07-01", "hasta": "2025-07-31", "dias": 30}	627.28	57.40	221.99	569.88	0.00	692.10	692.10	627.28	2.00	["Standardized the format of the worker's name.", "Standardized the format of the Social Security Affiliation Number.", "The value 'aportacion_empresa_total' was not found and has been calculated by summing its components."]	f	\N	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
54	3	payslip	{"desde": "2025-08-01", "hasta": "2025-08-20", "dias": 20}	315.67	27.42	104.40	288.25	0.00	325.51	325.51	315.67	2.00	["Standardized the format of the worker's name.", "Standardized the format of the Social Security Affiliation Number.", "The value 'aportacion_empresa_total' was not found and has been calculated by summing its components."]	f	\N	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
55	22	payslip	{"desde": "2025-09-15", "hasta": "2025-09-30", "dias": 16}	382.89	33.62	128.47	349.27	0.00	400.63	400.63	382.89	2.00	["Standardized the format of the worker's name.", "Standardized the format of the Social Security Affiliation Number.", "The value 'aportacion_empresa_total' was not found and has been calculated by summing its components."]	f	\N	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
56	22	payslip	{"desde": "2025-10-01", "hasta": "2025-10-31", "dias": 30}	882.31	80.47	310.91	801.84	0.00	969.47	969.47	882.31	2.00	["Standardized the format of the worker's name.", "Standardized the format of the Social Security Affiliation Number.", "The value 'aportacion_empresa_total' was not found and has been calculated by summing its components."]	f	\N	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
57	22	payslip	{"desde": "2025-11-01", "hasta": "2025-11-04", "dias": 4}	118.45	12.62	50.69	105.83	0.00	158.08	158.08	118.45	2.00	["Standardized the format of the worker's name.", "Standardized the format of the Social Security Affiliation Number.", "The value 'aportacion_empresa_total' was not found and has been calculated by summing its components."]	f	\N	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
58	6	hybrid	{"desde": "2025-08-01", "hasta": "2025-08-07", "dias": 7}	698.65	45.28	224.06	653.37	0.00	698.65	698.65	698.65	0.00	["Standardized the format of the worker's name.", "Standardized the format of the Social Security Affiliation Number.", "The value 'aportacion_empresa_total' was not found and has been calculated by summing its components.", "The payslip contains a concept related to settlement (*Vacaciones)."]	f	\N	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
59	3	hybrid	{"desde": "2025-08-01", "hasta": "2025-08-20", "dias": 20}	45.74	5.98	25.11	39.76	0.00	78.27	78.27	45.74	2.00	["Standardized the format of the worker's name.", "Standardized the format of the Social Security Affiliation Number.", "The value 'aportacion_empresa_total' was not found and has been calculated by summing its components.", "The start date of the period was assumed to be the first of the month as only the end date was explicitly provided for this settlement."]	f	\N	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
60	25	hybrid	{"desde": "2025-02-01", "hasta": "2025-02-22", "dias": 22}	89.16	6.57	32.49	82.59	0.00	101.29	101.29	89.16	0.00	["Standardized the format of the worker's name.", "Standardized the format of the Social Security Affiliation Number.", "The value 'aportacion_empresa_total' was not found and has been calculated by summing its components.", "The start date of the period was assumed to be the first of the month as only the end date was explicitly provided for this settlement."]	f	\N	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
61	23	hybrid	{"desde": "2025-01-01", "hasta": "2025-01-31", "dias": 31}	267.50	33.99	99.00	233.51	0.00	308.70	308.70	267.50	5.23	["Standardized the format of the worker's name.", "Standardized the format of the Social Security Affiliation Number.", "The value 'aportacion_empresa_total' was not found and has been calculated by summing its components.", "The start date of the period was assumed to be the first of the month as only the end date was explicitly provided in the period field."]	f	\N	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
62	25	payslip	{"desde": "2025-01-01", "hasta": "2025-01-31", "dias": 30}	316.44	20.50	101.48	295.94	0.00	316.44	316.44	316.44	0.00	["Standardized the format of the worker's name.", "Standardized the format of the Social Security Affiliation Number.", "The value 'aportacion_empresa_total' was not found and has been calculated by summing its components."]	f	\N	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
63	25	payslip	{"desde": "2025-02-01", "hasta": "2025-02-22", "dias": 22}	262.70	17.02	84.26	245.68	0.00	262.70	262.70	262.70	0.00	["Standardized the format of the worker's name.", "Standardized the format of the Social Security Affiliation Number.", "The value 'aportacion_empresa_total' was not found and has been calculated by summing its components."]	f	\N	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
64	5	payslip	{"desde": "2025-01-01", "hasta": "2025-01-31", "dias": 30}	1289.08	83.54	413.39	1205.54	0.00	1289.08	1289.08	1289.08	0.00	["Standardized the format of the worker's name.", "Standardized the format of the Social Security Affiliation Number.", "The value 'aportacion_empresa_total' was not found and has been calculated by summing its components."]	f	\N	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
65	5	payslip	{"desde": "2025-03-01", "hasta": "2025-03-31", "dias": 30}	1289.08	83.54	413.39	1205.54	0.00	1289.08	1289.08	1289.08	0.00	["Standardized the format of the worker's name.", "Standardized the format of the Social Security Affiliation Number.", "The value 'aportacion_empresa_total' was not found and has been calculated by summing its components."]	f	\N	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
66	5	payslip	{"desde": "2025-04-01", "hasta": "2025-04-30", "dias": 30}	1327.75	86.04	425.81	1241.71	0.00	1327.75	1327.75	1327.75	0.00	["Standardized the format of the worker's name.", "Standardized the format of the Social Security Affiliation Number.", "The value 'aportacion_empresa_total' was not found and has been calculated by summing its components."]	f	\N	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
67	5	payslip	{"desde": "2025-05-01", "hasta": "2025-05-31", "dias": 30}	1327.75	86.04	425.81	1241.71	0.00	1327.75	1327.75	1327.75	0.00	["Standardized the format of the worker's name.", "Standardized the format of the Social Security Affiliation Number.", "The value 'aportacion_empresa_total' was not found and has been calculated by summing its components."]	f	\N	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
68	5	payslip	{"desde": "2025-06-01", "hasta": "2025-06-30", "dias": 30}	1327.75	86.04	425.81	1241.71	0.00	1327.75	1327.75	1327.75	0.00	["Standardized the format of the worker's name.", "Standardized the format of the Social Security Affiliation Number.", "The value 'aportacion_empresa_total' was not found and has been calculated by summing its components."]	f	\N	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
69	5	payslip	{"desde": "2025-08-01", "hasta": "2025-08-31", "dias": 30}	1327.75	86.04	425.81	1241.71	0.00	1327.75	1327.75	1327.75	0.00	["Standardized the format of the worker's name.", "Standardized the format of the Social Security Affiliation Number.", "The value 'aportacion_empresa_total' was not found and has been calculated by summing its components."]	f	\N	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
70	5	payslip	{"desde": "2025-11-01", "hasta": "2025-11-30", "dias": 30}	1327.75	86.04	425.81	1241.71	0.00	1327.75	1327.75	1327.75	0.00	["Standardized the format of the worker's name.", "Standardized the format of the Social Security Affiliation Number.", "The value 'aportacion_empresa_total' was not found and has been calculated by summing its components."]	f	\N	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
71	5	payslip	{"desde": "2025-02-01", "hasta": "2025-02-28", "dias": 30}	1289.08	83.54	413.39	1205.54	0.00	1289.08	1289.08	1289.08	0.00	["Standardized the format of the worker's name.", "Standardized the format of the Social Security Affiliation Number.", "The value 'aportacion_empresa_total' was not found and has been calculated by summing its components."]	f	\N	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
72	5	payslip	{"desde": "2025-07-01", "hasta": "2025-07-31", "dias": 30}	1327.75	86.04	425.81	1241.71	0.00	1327.75	1327.75	1327.75	0.00	["Standardized the format of the worker's name.", "Standardized the format of the Social Security Affiliation Number.", "The value 'aportacion_empresa_total' was not found and has been calculated by summing its components."]	f	\N	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
73	5	payslip	{"desde": "2025-09-01", "hasta": "2025-09-30", "dias": 30}	1327.75	86.04	425.81	1241.71	0.00	1327.75	1327.75	1327.75	0.00	["Standardized the format of the worker's name.", "Standardized the format of the Social Security Affiliation Number.", "The value 'aportacion_empresa_total' was not found and has been calculated by summing its components."]	f	\N	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
74	5	payslip	{"desde": "2025-10-01", "hasta": "2025-10-31", "dias": 30}	1327.75	86.04	425.81	1241.71	0.00	1327.75	1327.75	1327.75	0.00	["Standardized the format of the worker's name.", "Standardized the format of the Social Security Affiliation Number.", "The value 'aportacion_empresa_total' was not found and has been calculated by summing its components."]	f	\N	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
75	13	payslip	{"desde": "2025-01-01", "hasta": "2025-01-31", "dias": 30}	1710.22	268.33	548.46	1441.89	0.00	1710.22	1710.22	1710.22	9.21	["Standardized the format of the worker's name.", "Standardized the format of the Social Security Affiliation Number.", "The value 'aportacion_empresa_total' was not found and has been calculated by summing its components."]	f	\N	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
76	13	payslip	{"desde": "2025-02-01", "hasta": "2025-02-28", "dias": 30}	1716.28	251.95	550.41	1464.33	0.00	1716.28	1716.28	1716.28	8.20	["Standardized the format of the worker's name.", "Standardized the format of the Social Security Affiliation Number.", "The value 'aportacion_empresa_total' was not found and has been calculated by summing its components."]	f	\N	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
77	13	payslip	{"desde": "2025-03-01", "hasta": "2025-03-31", "dias": 30}	1702.14	249.87	545.88	1452.27	0.00	1702.14	1702.14	1702.14	8.20	["Standardized the format of the worker's name.", "Standardized the format of the Social Security Affiliation Number.", "The value 'aportacion_empresa_total' was not found and has been calculated by summing its components."]	f	\N	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
78	13	payslip	{"desde": "2025-04-01", "hasta": "2025-04-30", "dias": 30}	1757.72	258.03	563.69	1499.69	0.00	1757.72	1757.72	1757.72	8.20	["Standardized the format of the worker's name.", "Standardized the format of the Social Security Affiliation Number.", "The value 'aportacion_empresa_total' was not found and has been calculated by summing its components."]	f	\N	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
79	13	payslip	{"desde": "2025-05-01", "hasta": "2025-05-31", "dias": 30}	1766.81	259.38	566.60	1507.43	0.00	1766.81	1766.81	1766.81	8.20	["Standardized the format of the worker's name.", "Standardized the format of the Social Security Affiliation Number.", "The value 'aportacion_empresa_total' was not found and has been calculated by summing its components."]	f	\N	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
80	13	payslip	{"desde": "2025-06-01", "hasta": "2025-06-30", "dias": 30}	1766.81	259.38	566.60	1507.43	0.00	1766.81	1766.81	1766.81	8.20	["Standardized the format of the worker's name.", "Standardized the format of the Social Security Affiliation Number.", "The value 'aportacion_empresa_total' was not found and has been calculated by summing its components."]	f	\N	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
81	13	payslip	{"desde": "2025-07-01", "hasta": "2025-07-31", "dias": 30}	1761.76	258.62	564.99	1503.14	0.00	1761.76	1761.76	1761.76	8.20	["Standardized the format of the worker's name.", "Standardized the format of the Social Security Affiliation Number.", "The value 'aportacion_empresa_total' was not found and has been calculated by summing its components."]	f	\N	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
82	13	payslip	{"desde": "2025-08-01", "hasta": "2025-08-31", "dias": 30}	1773.88	260.41	568.88	1513.47	0.00	1773.88	1773.88	1773.88	8.20	["Standardized the format of the worker's name.", "Standardized the format of the Social Security Affiliation Number.", "The value 'aportacion_empresa_total' was not found and has been calculated by summing its components."]	f	\N	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
83	13	payslip	{"desde": "2025-09-01", "hasta": "2025-09-30", "dias": 30}	1769.84	259.81	567.59	1510.03	0.00	1769.84	1769.84	1769.84	8.20	["Standardized the format of the worker's name.", "Standardized the format of the Social Security Affiliation Number.", "The value 'aportacion_empresa_total' was not found and has been calculated by summing its components."]	f	\N	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
84	13	payslip	{"desde": "2025-10-01", "hasta": "2025-10-31", "dias": 30}	1760.75	258.48	564.68	1502.27	0.00	1760.75	1760.75	1760.75	8.20	["Standardized the format of the worker's name.", "Standardized the format of the Social Security Affiliation Number.", "The value 'aportacion_empresa_total' was not found and has been calculated by summing its components."]	f	\N	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
85	13	payslip	{"desde": "2025-11-01", "hasta": "2025-11-30", "dias": 30}	1774.89	260.55	569.20	1514.34	0.00	1774.89	1774.89	1774.89	8.20	["Standardized the format of the worker's name.", "Standardized the format of the Social Security Affiliation Number.", "The value 'aportacion_empresa_total' was not found and has been calculated by summing its components."]	f	\N	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
86	18	payslip	{"desde": "2025-02-17", "hasta": "2025-02-28", "dias": 14}	690.33	42.70	211.32	647.63	0.00	658.99	658.99	690.33	0.00	["Standardized the format of the worker's name.", "Standardized the format of the Social Security Affiliation Number.", "The value 'aportacion_empresa_total' was not found and has been calculated by summing its components."]	f	\N	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
87	18	payslip	{"desde": "2025-03-01", "hasta": "2025-03-31", "dias": 30}	1491.18	201.65	513.09	1289.53	0.00	1599.90	1599.90	1491.18	6.57	["Standardized the format of the worker's name.", "Standardized the format of the Social Security Affiliation Number.", "The value 'aportacion_empresa_total' was not found and has been calculated by summing its components."]	f	\N	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
88	18	payslip	{"desde": "2025-04-01", "hasta": "2025-04-30", "dias": 30}	1415.57	203.89	513.82	1211.68	0.00	1602.19	1602.19	1415.57	7.07	["Standardized the format of the worker's name.", "Standardized the format of the Social Security Affiliation Number.", "The value 'aportacion_empresa_total' was not found and has been calculated by summing its components."]	f	\N	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
89	18	payslip	{"desde": "2025-05-01", "hasta": "2025-05-31", "dias": 30}	1566.88	215.77	519.62	1351.11	0.00	1620.29	1620.29	1566.88	7.07	["Standardized the format of the worker's name.", "Standardized the format of the Social Security Affiliation Number.", "The value 'aportacion_empresa_total' was not found and has been calculated by summing its components."]	f	\N	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
90	18	payslip	{"desde": "2025-06-01", "hasta": "2025-06-30", "dias": 30}	1637.52	221.88	525.15	1415.64	0.00	1637.52	1637.52	1637.52	7.07	["Standardized the format of the worker's name.", "Standardized the format of the Social Security Affiliation Number.", "The value 'aportacion_empresa_total' was not found and has been calculated by summing its components."]	f	\N	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
91	18	payslip	{"desde": "2025-07-01", "hasta": "2025-07-31", "dias": 30}	1647.62	223.26	528.40	1424.36	0.00	1647.62	1647.62	1647.62	7.07	["Standardized the format of the worker's name.", "Standardized the format of the Social Security Affiliation Number.", "The value 'aportacion_empresa_total' was not found and has been calculated by summing its components."]	f	\N	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
92	18	payslip	{"desde": "2025-08-01", "hasta": "2025-08-31", "dias": 30}	1646.61	223.12	528.06	1423.49	0.00	1646.61	1646.61	1646.61	7.07	["Standardized the format of the worker's name.", "Standardized the format of the Social Security Affiliation Number.", "The value 'aportacion_empresa_total' was not found and has been calculated by summing its components."]	f	\N	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
93	18	payslip	{"desde": "2025-09-01", "hasta": "2025-09-30", "dias": 30}	1640.55	222.30	526.11	1418.25	0.00	1640.55	1640.55	1640.55	7.07	["Standardized the format of the worker's name.", "Standardized the format of the Social Security Affiliation Number.", "The value 'aportacion_empresa_total' was not found and has been calculated by summing its components."]	f	\N	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
94	18	payslip	{"desde": "2025-10-01", "hasta": "2025-10-31", "dias": 30}	1638.53	222.02	525.48	1416.51	0.00	1638.53	1638.53	1638.53	7.07	["Standardized the format of the worker's name.", "Standardized the format of the Social Security Affiliation Number.", "The value 'aportacion_empresa_total' was not found and has been calculated by summing its components."]	f	\N	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
95	18	payslip	{"desde": "2025-11-01", "hasta": "2025-11-30", "dias": 30}	1620.35	219.57	519.63	1400.78	0.00	1620.35	1620.35	1620.35	7.07	["Standardized the format of the worker's name.", "Standardized the format of the Social Security Affiliation Number.", "The value 'aportacion_empresa_total' was not found and has been calculated by summing its components."]	f	\N	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
96	23	payslip	{"desde": "2025-01-01", "hasta": "2025-01-31", "dias": 30}	1536.51	179.94	492.76	1356.57	0.00	1536.51	1536.51	1536.51	5.23	["Standardized the format of the worker's name.", "Standardized the format of the Social Security Affiliation Number.", "The value 'aportacion_empresa_total' was not found and has been calculated by summing its components."]	f	\N	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
97	10	payslip	{"desde": "2025-01-01", "hasta": "2025-01-31", "dias": 30}	1220.47	79.09	391.39	1141.38	0.00	1220.47	1220.47	1220.47	0.00	["Standardized the format of the worker's name.", "Standardized the format of the Social Security Affiliation Number.", "The value 'aportacion_empresa_total' was not found and has been calculated by summing its components."]	f	\N	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
98	10	payslip	{"desde": "2025-02-01", "hasta": "2025-02-11", "dias": 11}	463.91	31.92	157.96	431.99	0.00	492.52	492.52	463.91	0.00	["Standardized the format of the worker's name.", "Standardized the format of the Social Security Affiliation Number.", "The value 'aportacion_empresa_total' was not found and has been calculated by summing its components."]	f	\N	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
99	15	payslip	{"desde": "2025-01-01", "hasta": "2025-01-31", "dias": 30}	845.45	54.79	271.13	790.66	0.00	845.45	845.45	845.45	0.00	["Standardized the format of the worker's name.", "Standardized the format of the Social Security Affiliation Number.", "The value 'aportacion_empresa_total' was not found and has been calculated by summing its components."]	f	\N	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
100	15	payslip	{"desde": "2025-02-01", "hasta": "2025-02-28", "dias": 30}	834.34	54.05	267.57	780.29	0.00	834.34	834.34	834.34	0.00	["Standardized the format of the worker's name.", "Standardized the format of the Social Security Affiliation Number.", "The value 'aportacion_empresa_total' was not found and has been calculated by summing its components."]	f	\N	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
101	15	payslip	{"desde": "2025-03-01", "hasta": "2025-03-31", "dias": 30}	853.81	55.76	276.05	798.05	0.00	860.75	860.75	853.81	0.00	["Standardized the format of the worker's name.", "Standardized the format of the Social Security Affiliation Number.", "The value 'aportacion_empresa_total' was not found and has been calculated by summing its components."]	f	\N	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
102	15	payslip	{"desde": "2025-04-01", "hasta": "2025-04-30", "dias": 30}	900.80	59.93	296.68	840.87	0.00	925.01	925.01	900.80	0.00	["Standardized the format of the worker's name.", "Standardized the format of the Social Security Affiliation Number.", "The value 'aportacion_empresa_total' was not found and has been calculated by summing its components."]	f	\N	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
103	15	payslip	{"desde": "2025-05-01", "hasta": "2025-05-31", "dias": 30}	867.89	56.24	278.33	811.65	0.00	867.89	867.89	867.89	0.00	["Standardized the format of the worker's name.", "Standardized the format of the Social Security Affiliation Number.", "The value 'aportacion_empresa_total' was not found and has been calculated by summing its components."]	f	\N	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
104	15	payslip	{"desde": "2025-06-01", "hasta": "2025-06-30", "dias": 30}	922.05	60.62	300.07	861.43	0.00	935.66	935.66	922.05	0.00	["Standardized the format of the worker's name.", "Standardized the format of the Social Security Affiliation Number.", "The value 'aportacion_empresa_total' was not found and has been calculated by summing its components."]	f	\N	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
105	15	payslip	{"desde": "2025-07-01", "hasta": "2025-07-31", "dias": 30}	1014.98	70.04	346.63	944.94	0.00	1080.79	1080.79	1014.98	0.00	["Standardized the format of the worker's name.", "Standardized the format of the Social Security Affiliation Number.", "The value 'aportacion_empresa_total' was not found and has been calculated by summing its components."]	f	\N	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
106	15	payslip	{"desde": "2025-08-01", "hasta": "2025-08-31", "dias": 30}	1014.16	66.71	330.11	947.45	0.00	1029.28	1029.28	1014.16	0.00	["Standardized the format of the worker's name.", "Standardized the format of the Social Security Affiliation Number.", "The value 'aportacion_empresa_total' was not found and has been calculated by summing its components."]	f	\N	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
107	15	payslip	{"desde": "2025-09-01", "hasta": "2025-09-14", "dias": 14}	391.82	25.39	125.64	366.43	0.00	391.82	391.82	391.82	0.00	["Standardized the format of the worker's name.", "Standardized the format of the Social Security Affiliation Number.", "The value 'aportacion_empresa_total' was not found and has been calculated by summing its components."]	f	\N	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
108	21	payslip	{"desde": "2025-01-21", "hasta": "2025-01-31", "dias": 10}	391.77	28.93	143.13	362.84	0.00	446.32	446.32	391.77	0.00	["Standardized the format of the worker's name.", "Standardized the format of the Social Security Affiliation Number.", "The value 'aportacion_empresa_total' was not found and has been calculated by summing its components."]	f	\N	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
109	21	payslip	{"desde": "2025-02-01", "hasta": "2025-02-07", "dias": 7}	221.76	19.55	96.74	202.21	0.00	301.66	301.66	221.76	0.00	["Standardized the format of the worker's name.", "Standardized the format of the Social Security Affiliation Number.", "The value 'aportacion_empresa_total' was not found and has been calculated by summing its components."]	f	\N	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
110	8	payslip	{"desde": "2025-09-08", "hasta": "2025-09-30", "dias": 23}	986.59	85.70	326.52	900.89	0.00	1018.18	1018.18	986.59	2.00	["Standardized the format of the worker's name.", "Standardized the format of the Social Security Affiliation Number.", "The value 'aportacion_empresa_total' was not found and has been calculated by summing its components."]	f	\N	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
111	8	payslip	{"desde": "2025-11-01", "hasta": "2025-11-30", "dias": 30}	1227.06	104.26	394.60	1122.80	0.00	1230.42	1230.42	1227.06	2.00	["Standardized the format of the worker's name.", "Standardized the format of the Social Security Affiliation Number.", "The value 'aportacion_empresa_total' was not found and has been calculated by summing its components."]	f	\N	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
112	8	payslip	{"desde": "2025-10-01", "hasta": "2025-10-31", "dias": 30}	1388.52	124.68	479.64	1263.84	0.00	1495.67	1495.67	1388.52	2.00	["Standardized the format of the worker's name.", "Standardized the format of the Social Security Affiliation Number.", "The value 'aportacion_empresa_total' was not found and has been calculated by summing its components."]	f	\N	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
113	17	payslip	{"desde": "2025-01-14", "hasta": "2025-01-31", "dias": 17}	279.30	19.10	94.57	260.20	0.00	294.89	294.89	279.30	0.00	["Standardized the format of the worker's name.", "Standardized the format of the Social Security Affiliation Number.", "The value 'aportacion_empresa_total' was not found and has been calculated by summing its components."]	f	\N	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
114	17	payslip	{"desde": "2025-02-01", "hasta": "2025-02-28", "dias": 30}	686.93	44.78	221.56	642.15	0.00	690.94	690.94	686.93	0.00	["Standardized the format of the worker's name.", "Standardized the format of the Social Security Affiliation Number.", "The value 'aportacion_empresa_total' was not found and has been calculated by summing its components."]	f	\N	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
115	17	payslip	{"desde": "2025-03-01", "hasta": "2025-03-31", "dias": 30}	1021.18	68.68	339.87	952.50	0.00	1059.73	1059.73	1021.18	0.00	["Standardized the format of the worker's name.", "Standardized the format of the Social Security Affiliation Number.", "The value 'aportacion_empresa_total' was not found and has been calculated by summing its components."]	f	\N	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
116	17	payslip	{"desde": "2025-04-01", "hasta": "2025-04-30", "dias": 30}	1020.67	67.17	332.39	953.50	0.00	1036.47	1036.47	1020.67	0.00	["Standardized the format of the worker's name.", "Standardized the format of the Social Security Affiliation Number.", "The value 'aportacion_empresa_total' was not found and has been calculated by summing its components."]	f	\N	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
117	17	payslip	{"desde": "2025-05-01", "hasta": "2025-05-31", "dias": 30}	537.97	34.86	172.53	503.11	0.00	537.97	537.97	537.97	0.00	["Standardized the format of the worker's name.", "Standardized the format of the Social Security Affiliation Number.", "The value 'aportacion_empresa_total' was not found and has been calculated by summing its components."]	f	\N	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
118	17	payslip	{"desde": "2025-06-01", "hasta": "2025-06-30", "dias": 30}	816.09	53.40	264.25	762.69	0.00	824.12	824.12	816.09	0.00	["Standardized the format of the worker's name.", "Standardized the format of the Social Security Affiliation Number.", "The value 'aportacion_empresa_total' was not found and has been calculated by summing its components."]	f	\N	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
119	17	payslip	{"desde": "2025-07-01", "hasta": "2025-07-31", "dias": 30}	780.40	53.90	266.66	726.50	0.00	831.47	831.47	780.40	0.00	["Standardized the format of the worker's name.", "Standardized the format of the Social Security Affiliation Number.", "The value 'aportacion_empresa_total' was not found and has been calculated by summing its components."]	f	\N	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
120	17	payslip	{"desde": "2025-08-01", "hasta": "2025-08-31", "dias": 30}	1090.15	71.58	354.19	1018.57	0.00	1104.42	1104.42	1090.15	0.00	["Standardized the format of the worker's name.", "Standardized the format of the Social Security Affiliation Number.", "The value 'aportacion_empresa_total' was not found and has been calculated by summing its components."]	f	\N	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
121	17	payslip	{"desde": "2025-09-01", "hasta": "2025-09-30", "dias": 30}	770.33	50.97	252.21	719.36	0.00	786.41	786.41	770.33	0.00	["Standardized the format of the worker's name.", "Standardized the format of the Social Security Affiliation Number.", "The value 'aportacion_empresa_total' was not found and has been calculated by summing its components."]	f	\N	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
122	17	payslip	{"desde": "2025-10-01", "hasta": "2025-10-31", "dias": 30}	699.33	49.20	243.49	650.13	0.00	759.27	759.27	699.33	0.00	["Standardized the format of the worker's name.", "Standardized the format of the Social Security Affiliation Number.", "The value 'aportacion_empresa_total' was not found and has been calculated by summing its components."]	f	\N	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
123	17	payslip	{"desde": "2025-11-01", "hasta": "2025-11-30", "dias": 30}	625.72	40.54	200.67	585.18	0.00	625.72	625.72	625.72	0.00	["Standardized the format of the worker's name.", "Standardized the format of the Social Security Affiliation Number.", "The value 'aportacion_empresa_total' was not found and has been calculated by summing its components."]	f	\N	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
124	7	payslip	{"desde": "2025-09-03", "hasta": "2025-09-10", "dias": 8}	217.39	20.66	80.78	196.73	0.00	251.90	251.90	217.39	2.00	["Standardized the format of the worker's name.", "Standardized the format of the Social Security Affiliation Number.", "The value 'aportacion_empresa_total' was not found and has been calculated by summing its components."]	f	\N	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
125	1	payslip	{"desde": "2025-06-03", "hasta": "2025-06-30", "dias": 28}	583.17	38.08	194.03	545.09	0.00	583.17	583.17	583.17	0.00	["Standardized the format of the worker's name.", "Standardized the format of the Social Security Affiliation Number.", "The value 'aportacion_empresa_total' was not found and has been calculated by summing its components."]	f	\N	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
126	1	payslip	{"desde": "2025-07-01", "hasta": "2025-07-31", "dias": 30}	1249.64	181.57	405.93	1068.07	0.00	1257.69	1257.69	1249.64	8.00	["Standardized the format of the worker's name.", "Standardized the format of the Social Security Affiliation Number.", "The value 'aportacion_empresa_total' was not found and has been calculated by summing its components.", "Calculated the percentage for Desempleo (employer) as 5.71% based on the provided base and amount."]	f	\N	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
127	1	payslip	{"desde": "2025-08-01", "hasta": "2025-08-31", "dias": 30}	1562.06	226.18	500.95	1335.88	0.00	1562.06	1562.06	1562.06	8.00	["Standardized the format of the worker's name.", "Standardized the format of the Social Security Affiliation Number.", "The value 'aportacion_empresa_total' was not found and has been calculated by summing its components."]	f	\N	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
128	1	payslip	{"desde": "2025-09-01", "hasta": "2025-09-30", "dias": 30}	1562.06	226.18	500.95	1335.88	0.00	1562.06	1562.06	1562.06	8.00	["Standardized the format of the worker's name.", "Standardized the format of the Social Security Affiliation Number.", "The value 'aportacion_empresa_total' was not found and has been calculated by summing its components."]	f	\N	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
129	1	payslip	{"desde": "2025-10-01", "hasta": "2025-10-31", "dias": 30}	1562.06	226.18	500.95	1335.88	0.00	1562.06	1562.06	1562.06	8.00	["Standardized the format of the worker's name.", "Standardized the format of the Social Security Affiliation Number.", "The value 'aportacion_empresa_total' was not found and has been calculated by summing its components."]	f	\N	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
130	1	payslip	{"desde": "2025-11-01", "hasta": "2025-11-30", "dias": 30}	1562.06	226.18	500.95	1335.88	0.00	1562.06	1562.06	1562.06	8.00	["Standardized the format of the worker's name.", "Standardized the format of the Social Security Affiliation Number.", "The value 'aportacion_empresa_total' was not found and has been calculated by summing its components."]	f	\N	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
131	9	payslip	{"desde": "2025-09-12", "hasta": "2025-09-30", "dias": 19}	630.21	54.54	207.54	575.67	0.00	647.17	647.17	630.21	2.00	["Standardized the format of the worker's name.", "Standardized the format of the Social Security Affiliation Number.", "The value 'aportacion_empresa_total' was not found and has been calculated by summing its components."]	f	\N	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
132	9	payslip	{"desde": "2025-10-01", "hasta": "2025-10-31", "dias": 30}	1174.74	106.46	410.67	1068.28	0.00	1280.58	1280.58	1174.74	2.00	["Standardized the format of the worker's name.", "Standardized the format of the Social Security Affiliation Number.", "The value 'aportacion_empresa_total' was not found and has been calculated by summing its components."]	f	\N	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
133	9	payslip	{"desde": "2025-11-01", "hasta": "2025-11-30", "dias": 30}	1119.63	94.96	359.05	1024.67	0.00	1119.63	1119.63	1119.63	2.00	["Standardized the format of the worker's name.", "Standardized the format of the Social Security Affiliation Number.", "The value 'aportacion_empresa_total' was not found and has been calculated by summing its components."]	f	\N	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
134	12	settlement	{"desde": "2025-07-01", "hasta": "2025-07-10", "dias": 10}	0.00	285.08	0.00	-285.08	0.00	0.00	0.00	0.00	0.00	["Standardized the format of the worker's name to UPPERCASE and removed commas.", "The document contains only a deduction (Descuento Preaviso), resulting in a negative net amount.", "Termination date (fecha_cese) inferred from the settlement period date.", "Social Security number formatted by removing non-numeric characters."]	f	\N	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
135	14	settlement	{"desde": "2025-06-01", "hasta": "2025-06-11", "dias": 11}	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	["Standardized the format of the worker's name to uppercase and removed commas.", "The document appears to be a template or a zero-value settlement as no specific line items or amounts were found in the devengos/deducciones sections.", "Date format was converted to YYYY-MM-DD.", "Social Security number was cleaned of non-numeric characters."]	f	\N	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
136	2	settlement	{"desde": "2025-09-01", "hasta": "2025-09-07", "dias": 7}	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	["Standardized the format of the worker's name to uppercase and removed commas.", "No financial line items or amounts were found in the provided settlement document.", "Dates were converted to YYYY-MM-DD format.", "The company CIF was extracted from the footer of the document."]	f	\N	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
137	2	settlement	{"desde": "2025-06-01", "hasta": "2025-06-26", "dias": 26}	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	["Standardized the format of the worker's name to UPPERCASE and removed commas.", "The document appears to be a settlement template or zero-value settlement as no specific line items or amounts were found in the devengos/deducciones columns.", "Termination date (fecha_cese) inferred from the settlement period/date.", "Social Security number formatted by removing non-digit characters."]	f	\N	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
138	2	settlement	{"desde": "2025-09-01", "hasta": "2025-09-08", "dias": 8}	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	["Standardized the format of the worker's name to UPPERCASE and removed commas.", "The document appears to be a settlement template or zero-value settlement as no specific line items or amounts were found in the devengos/deducciones columns.", "Date format was converted to YYYY-MM-DD.", "Social Security number was cleaned of non-numeric characters."]	f	\N	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
139	20	settlement	{"desde": "2025-01-01", "hasta": "2025-01-10", "dias": 10}	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	["Standardized the format of the worker's name to UPPERCASE and removed commas.", "Social Security number formatted by removing non-numeric characters.", "No specific line items or amounts were found in the provided document text; totals default to 0.0.", "Termination date (fecha_cese) inferred from the settlement period date."]	f	\N	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
140	22	settlement	{"desde": "2025-11-01", "hasta": "2025-11-04", "dias": 4}	135.00	11.46	0.00	123.54	0.00	135.00	135.00	135.00	2.00	["Standardized the format of the worker's name to UPPERCASE and removed commas.", "Extracted settlement date from the 'Finiquito - 4 Noviembre 2025' and signature section.", "Social Security number formatted by removing non-digit characters.", "Mapped 'TRIBUTACIÓN IRPF' to standardized 'RETENCION IRPF'."]	f	\N	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
141	10	settlement	{"desde": "2025-02-01", "hasta": "2025-02-11", "dias": 11}	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	["Standardized the format of the worker's name to uppercase and removed commas.", "Social Security number was cleaned of non-numeric characters.", "No specific earnings or deduction items were found in the document table.", "Termination date inferred from the settlement period date.", "The net amount (liquido_a_percibir) is 0.0 as no values were present in the document's amount fields."]	f	\N	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
142	15	settlement	{"desde": "2025-09-01", "hasta": "2025-09-14", "dias": 14}	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	["Standardized the format of the worker's name to uppercase and removed commas.", "No specific earnings (devengos) or deductions (deducciones) were found in the provided document text.", "The termination date (fecha_cese) was inferred from the settlement period date.", "The Social Security number was cleaned of formatting characters."]	f	\N	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
143	21	settlement	{"desde": "2025-02-01", "hasta": "2025-02-07", "dias": 7}	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	["Standardized the format of the worker's name to UPPERCASE and removed commas.", "The document appears to be a template or an empty settlement as no specific line items (earnings/deductions) or amounts were found in the provided text/image.", "Date format was converted to YYYY-MM-DD.", "Termination date (fecha_cese) inferred from the period/settlement date as it was not explicitly labeled."]	f	\N	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
144	7	settlement	{"desde": "2025-09-01", "hasta": "2025-09-10", "dias": 10}	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	0.00	["Standardized the format of the worker's name.", "No specific earnings or deductions were found in the provided document; totals are set to 0.0.", "Termination date (fecha_cese) was inferred from the settlement period date.", "Social Security number was cleaned to a 12-digit format."]	f	\N	2025-12-31 12:13:30.253855+00	2025-12-31 12:13:30.253855+00
\.


--
-- Name: checklist_items_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.checklist_items_id_seq', 1, false);


--
-- Name: client_locations_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.client_locations_id_seq', 1, true);


--
-- Name: documents_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.documents_id_seq', 1, false);


--
-- Name: employee_periods_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.employee_periods_id_seq', 27, true);


--
-- Name: employees_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.employees_id_seq', 25, true);


--
-- Name: payroll_lines_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.payroll_lines_id_seq', 1578, true);


--
-- Name: payrolls_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.payrolls_id_seq', 144, true);


--
-- Name: checklist_items checklist_items_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.checklist_items
    ADD CONSTRAINT checklist_items_pkey PRIMARY KEY (id);


--
-- Name: client_locations client_locations_ccc_ss_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.client_locations
    ADD CONSTRAINT client_locations_ccc_ss_key UNIQUE (ccc_ss);


--
-- Name: client_locations client_locations_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.client_locations
    ADD CONSTRAINT client_locations_pkey PRIMARY KEY (id);


--
-- Name: clients clients_cif_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.clients
    ADD CONSTRAINT clients_cif_key UNIQUE (cif);


--
-- Name: clients clients_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.clients
    ADD CONSTRAINT clients_pkey PRIMARY KEY (id);


--
-- Name: documents documents_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.documents
    ADD CONSTRAINT documents_pkey PRIMARY KEY (id);


--
-- Name: employee_periods employee_periods_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.employee_periods
    ADD CONSTRAINT employee_periods_pkey PRIMARY KEY (id);


--
-- Name: employees employees_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.employees
    ADD CONSTRAINT employees_pkey PRIMARY KEY (id);


--
-- Name: nomina_concepts nomina_concepts_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.nomina_concepts
    ADD CONSTRAINT nomina_concepts_pkey PRIMARY KEY (concept_code);


--
-- Name: payroll_lines payroll_lines_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.payroll_lines
    ADD CONSTRAINT payroll_lines_pkey PRIMARY KEY (id);


--
-- Name: payrolls payrolls_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.payrolls
    ADD CONSTRAINT payrolls_pkey PRIMARY KEY (id);


--
-- Name: idx_checklist_items_client_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_checklist_items_client_id ON public.checklist_items USING btree (client_id);


--
-- Name: idx_checklist_items_due_date; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_checklist_items_due_date ON public.checklist_items USING btree (due_date);


--
-- Name: idx_checklist_items_status; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_checklist_items_status ON public.checklist_items USING btree (status);


--
-- Name: idx_client_locations_ccc_ss; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_client_locations_ccc_ss ON public.client_locations USING btree (ccc_ss);


--
-- Name: idx_client_locations_company_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_client_locations_company_id ON public.client_locations USING btree (company_id);


--
-- Name: idx_documents_client_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_documents_client_id ON public.documents USING btree (client_id);


--
-- Name: idx_documents_employee_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_documents_employee_id ON public.documents USING btree (employee_id);


--
-- Name: idx_documents_status; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_documents_status ON public.documents USING btree (status);


--
-- Name: idx_employee_periods_dates; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_employee_periods_dates ON public.employee_periods USING btree (period_begin_date, period_end_date);


--
-- Name: idx_employee_periods_employee_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_employee_periods_employee_id ON public.employee_periods USING btree (employee_id);


--
-- Name: idx_employee_periods_location_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_employee_periods_location_id ON public.employee_periods USING btree (location_id);


--
-- Name: idx_employee_periods_type; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_employee_periods_type ON public.employee_periods USING btree (period_type);


--
-- Name: idx_employees_identity_card; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_employees_identity_card ON public.employees USING btree (identity_card_number);


--
-- Name: idx_payroll_lines_category; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_payroll_lines_category ON public.payroll_lines USING btree (category);


--
-- Name: idx_payroll_lines_concept; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_payroll_lines_concept ON public.payroll_lines USING btree (concept);


--
-- Name: idx_payroll_lines_payroll_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_payroll_lines_payroll_id ON public.payroll_lines USING btree (payroll_id);


--
-- Name: idx_payrolls_created_at; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_payrolls_created_at ON public.payrolls USING btree (created_at);


--
-- Name: idx_payrolls_employee_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_payrolls_employee_id ON public.payrolls USING btree (employee_id);


--
-- Name: checklist_items checklist_items_client_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.checklist_items
    ADD CONSTRAINT checklist_items_client_id_fkey FOREIGN KEY (client_id) REFERENCES public.clients(id) ON DELETE CASCADE;


--
-- Name: checklist_items checklist_items_document_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.checklist_items
    ADD CONSTRAINT checklist_items_document_id_fkey FOREIGN KEY (document_id) REFERENCES public.documents(id) ON DELETE SET NULL;


--
-- Name: checklist_items checklist_items_employee_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.checklist_items
    ADD CONSTRAINT checklist_items_employee_id_fkey FOREIGN KEY (employee_id) REFERENCES public.employees(id) ON DELETE CASCADE;


--
-- Name: checklist_items checklist_items_payroll_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.checklist_items
    ADD CONSTRAINT checklist_items_payroll_id_fkey FOREIGN KEY (payroll_id) REFERENCES public.payrolls(id) ON DELETE SET NULL;


--
-- Name: client_locations client_locations_company_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.client_locations
    ADD CONSTRAINT client_locations_company_id_fkey FOREIGN KEY (company_id) REFERENCES public.clients(id) ON DELETE CASCADE;


--
-- Name: documents documents_client_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.documents
    ADD CONSTRAINT documents_client_id_fkey FOREIGN KEY (client_id) REFERENCES public.clients(id) ON DELETE CASCADE;


--
-- Name: documents documents_employee_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.documents
    ADD CONSTRAINT documents_employee_id_fkey FOREIGN KEY (employee_id) REFERENCES public.employees(id) ON DELETE CASCADE;


--
-- Name: documents documents_payroll_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.documents
    ADD CONSTRAINT documents_payroll_id_fkey FOREIGN KEY (payroll_id) REFERENCES public.payrolls(id) ON DELETE CASCADE;


--
-- Name: employee_periods employee_periods_employee_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.employee_periods
    ADD CONSTRAINT employee_periods_employee_id_fkey FOREIGN KEY (employee_id) REFERENCES public.employees(id) ON DELETE CASCADE;


--
-- Name: employee_periods employee_periods_location_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.employee_periods
    ADD CONSTRAINT employee_periods_location_id_fkey FOREIGN KEY (location_id) REFERENCES public.client_locations(id) ON DELETE CASCADE;


--
-- Name: payroll_lines payroll_lines_payroll_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.payroll_lines
    ADD CONSTRAINT payroll_lines_payroll_id_fkey FOREIGN KEY (payroll_id) REFERENCES public.payrolls(id) ON DELETE CASCADE;


--
-- Name: payrolls payrolls_employee_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.payrolls
    ADD CONSTRAINT payrolls_employee_id_fkey FOREIGN KEY (employee_id) REFERENCES public.employees(id) ON DELETE CASCADE;


--
-- PostgreSQL database dump complete
--

\unrestrict qafPVpfZ0ZYawMcyUUFVybWG8l8JoSv9pW6vHBn7Zcwyn3ZXuquQXqmyln0LtvR

