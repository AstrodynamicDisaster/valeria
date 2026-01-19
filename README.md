# ValerIA - Spanish Payroll Processing System

ValerIA is a simplified payroll onboarding automation system designed for Spanish payroll service companies. It focuses on AI-powered document processing, missing document detection, and Spanish tax reporting (Models 111/190).

## 🚀 Quick Start

### 1. Setup Database

```bash
# Install dependencies
pip install -r requirements.txt

# Setup database (requires PostgreSQL running)
python setup_database.py
```

### 2. Generate Test Data

```bash
# Generate synthetic Spanish payroll data
python generate_test_data.py --employees 4 --year 2025

# Convert HTML payslips to PDF for AI processing
python convert_payslips_to_pdf.py --create-vision-sample
```

### 3. Test the System

The system will create:
- `./test_data/vida_laboral_*.csv` - Spanish Social Security employment data
- `./test_data/payslips/` - PDF payslips for AI vision model processing
- `./documents/` - Local file storage for processed documents

## 📁 Project Structure

### Core Files
- **`setup_database.py`** - Main database setup with essential models only
- **`generate_test_data.py`** - Synthetic Spanish payroll data generator
- **`convert_payslips_to_pdf.py`** - HTML to PDF conversion for AI processing

### Future Extensions
- **`database_extensions_future.py`** - Advanced features for future implementation
- **`test_vision_processing.py`** - Sample AI vision model integration

## 🗄️ Database Schema (Simplified)

### Core Models

1. **`clients`** - Client companies
   - Basic company info + Spanish CCC codes
   - Contact emails for notifications

2. **`employees`** - Employee records
   - Spanish identity fields (documento, NIF, NSS)
   - Compatible with vida laboral CSV imports

3. **`payrolls`** - Core payroll data
   - Focus on IRPF data for Models 111/190
   - AI extraction results and validation

4. **`documents`** - Simple local file storage
   - Relative file paths (no S3/cloud complexity)
   - AI processing status and confidence scores

5. **`checklist_items`** - Missing document tracking
   - Automated reminder system
   - Core feature for workflow management

### Key Features

- **Local File Storage**: No AWS/cloud dependencies
- **Spanish Tax Focus**: Models 111/190 reporting ready
- **AI Processing**: Document extraction workflow
- **Missing Document Detection**: Core business feature
- **Vida Laboral Integration**: Spanish Social Security CSV import

## 📋 Synthetic Data Generation

### Vida Laboral CSV
Generates realistic Spanish employment data:
- Valid Spanish DNI/NIE numbers with check digits
- Realistic employment scenarios (ALTA, BAJA, VAC.RETRIB.NO)
- Proper Spanish date formats and naming conventions

### Spanish Payslips
Creates authentic Spanish payroll documents:
- Realistic salary ranges and tax calculations
- Spanish payroll concepts and Social Security contributions
- Intentional gaps for missing document detection testing
- HTML format convertible to PDF for AI vision models

## 🔧 Usage Examples

### Import Vida Laboral Data

```python
from setup_database import parse_vida_laboral_csv_simple

# Parse vida laboral CSV
with open('test_data/vida_laboral_*.csv', 'r') as f:
    csv_content = f.read()

parsed_data = parse_vida_laboral_csv_simple(csv_content, client_id=1)
print(f"Found {len(parsed_data['employees'])} employees")
```

### Process Documents

```python
from setup_database import save_document_file

# Save payslip file with local storage
with open('payslip.pdf', 'rb') as f:
    file_content = f.read()

file_path = save_document_file(
    file_content=file_content,
    filename='nomina_2025_03.pdf',
    client_id=1,
    employee_id=123
)
print(f"Document saved: {file_path}")
```

### Check Missing Documents

```sql
-- View for detecting missing payslips
SELECT * FROM payroll_completeness
WHERE complete_year = false
AND period_year = 2025;
```

### Modelo 190 concept mapping (YAML buckets)

```bash
# Export a YAML template with all concepts in clave A + empty L.* buckets
python scripts/export_190_concepts.py --bucket-template --out 190_buckets.yml

# Edit 190_buckets.yml, moving concepts into the right buckets and ss_tax_concepts

# Build the JSON mapping consumed by 190.py
python scripts/export_190_concepts.py --mapping-from 190_buckets.yml --mapping-out 190_mapping.json
```

## 🧪 Testing & Development

### Generate Test Dataset
```bash
python generate_test_data.py --employees 5 --year 2025 --output-dir ./my_test_data
```

### Convert to PDFs
```bash
python convert_payslips_to_pdf.py --test-data-dir ./my_test_data
```

### Vision Model Testing
```bash
python test_vision_processing.py  # Sample integration template
```

## 📈 Future Enhancements

The `database_extensions_future.py` file contains advanced features that can be added later:

- **ContributionCenter Model** - Multiple CCC codes per client
- **EmploymentStatus Tracking** - Detailed vida laboral history
- **Enhanced Employment Periods** - Spanish Social Security alignment
- **Cloud Storage Integration** - S3/Azure support
- **Advanced Reporting** - Model 111/190 tables and aggregations
- **Complex Import Utilities** - Full vida laboral processing

## 🇪🇸 Spanish Compliance

- **Tax Reporting**: Models 111 (quarterly) and 190 (annual) ready
- **Social Security**: CCC codes and NSS number support
- **Employment Law**: ALTA/BAJA status tracking
- **Document Standards**: Spanish payslip formats and concepts
- **Date Formats**: Spanish date parsing and formatting

## 🛠️ Requirements

- **Python 3.8+**
- **PostgreSQL** (running locally or via Docker)
- **WeasyPrint** (for PDF generation)

```bash
# Database environment (matches docker-compose.yml)
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=valeria
POSTGRES_USER=valeria
POSTGRES_PASSWORD=***********
```

## 📞 Integration Points

This simplified system is designed to integrate with:

1. **n8n Workflows** - Document processing automation
2. **AI Vision Models** - OpenAI GPT-4V, Claude, etc.
3. **Spanish Tax Systems** - Model 111/190 export formats
4. **Email Systems** - Missing document reminders
5. **Document Storage** - Local filesystem (expandable to cloud)

## 🎯 Core Focus

- ✅ **Simple Setup** - No complex dependencies
- ✅ **Spanish Payroll** - Native support for Spanish employment law
- ✅ **AI Ready** - Vision model integration points
- ✅ **Local Storage** - No cloud vendor lock-in
- ✅ **Testing Data** - Realistic synthetic datasets
- ✅ **Extensible** - Clear upgrade path for advanced features

## 📝 License

This project is part of the ValerIA payroll automation system.
