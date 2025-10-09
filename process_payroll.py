import json
import pandas as pd
from openai import OpenAI
import base64
import pathlib
import os
import re

def extract_payroll_info(file_path, openai_api_key):
    """
    Extract complete payroll information from Spanish payslip files (image, PDF, Excel)
    using OpenAI's vision model.

    Args:
        file_path (str): Path to the file (image, PDF, or Excel)
        openai_api_key (str): OpenAI API key

    Returns:
        list: List of dictionaries containing complete payroll data including:
              - Employee information (name, ID)
              - Pay period dates
              - Monetary amounts (gross, net, taxes, deductions)
              - Individual concept lines with codes and amounts
    """
    try:
        client = OpenAI(api_key=openai_api_key)
        file_extension = pathlib.Path(file_path).suffix.lower()
        
        if file_extension in ['.xlsx', '.xls', '.csv']:
            return _process_excel_file(file_path)
        
        elif file_extension == '.pdf':
            return _process_pdf_with_vision(file_path, client)
        
        elif file_extension in ['.jpg', '.jpeg', '.png', '.bmp', '.tiff']:
            return _process_image_with_vision(file_path, client)
        
        else:
            raise ValueError(f"Unsupported file type: {file_extension}")
            
    except Exception as e:
        print(f"Error processing file: {e}")
        return []

def _process_excel_file(file_path):
    """Process Excel/CSV files directly without vision model"""
    try:
        if file_path.endswith('.csv'):
            df = pd.read_csv(file_path)
        else:
            df = pd.read_excel(file_path)
        
        employees = []
        
        # Look for common column names for employee data
        name_columns = [col for col in df.columns if any(keyword in col.lower() 
                    for keyword in ['name', 'employee', 'emp'])]
        id_columns = [col for col in df.columns if any(keyword in col.lower() 
                    for keyword in ['id', 'number', 'emp_id', 'employee_id'])]
        
        name_col = name_columns[0] if name_columns else df.columns[0]
        id_col = id_columns[0] if id_columns else None
        
        for _, row in df.iterrows():
            employee = {"name": str(row[name_col]) if pd.notna(row[name_col]) else ""}
            if id_col and pd.notna(row[id_col]):
                employee["id"] = str(row[id_col])
            employees.append(employee)
        
        return employees
        
    except Exception as e:
        print(f"Error processing Excel file: {e}")
        return []

def _process_pdf_with_vision(pdf_path, client, debug=False):
    """Convert PDF pages to images and process with vision model"""
    try:
        import pymupdf
        
        # Create a debug directory to save images
        if debug:
            debug_dir = os.path.join(os.path.dirname(pdf_path), "debug_images")
            os.makedirs(debug_dir, exist_ok=True)
        
        doc = pymupdf.open(pdf_path)
        all_employees = []
        
        for page_num in range(len(doc)):
            page = doc[page_num]
            # Convert PDF page to image
            mat = pymupdf.Matrix(2, 2)  # Zoom factor
            pix = page.get_pixmap(matrix=mat)
            img_data = pix.tobytes("png")

            if debug:
                # Save the image for debugging
                debug_image_path = os.path.join(debug_dir, f"page_{page_num}.png")
                with open(debug_image_path, "wb") as img_file:
                    img_file.write(img_data)
                print(f"Saved debug image: {debug_image_path}")
            
            # Encode image for OpenAI
            base64_image = base64.b64encode(img_data).decode('utf-8')
            
            employees = _call_openai_vision(client, base64_image)
            all_employees.extend(employees)
        
        doc.close()
        return all_employees
        
    except Exception as e:
        print(f"Error processing PDF: {e}")
        return []

def _process_image_with_vision(image_path, client):
    """Process image files with OpenAI vision model"""
    try:
        with open(image_path, "rb") as image_file:
            base64_image = base64.b64encode(image_file.read()).decode('utf-8')
        
        return _call_openai_vision(client, base64_image)
        
    except Exception as e:
        print(f"Error processing image: {e}")
        return []

def _clean_json_response(content: str) -> str:
    """Clean and preprocess OpenAI response for JSON parsing"""
    # Remove markdown code blocks
    if "```" in content:
        content_parts = content.split("```")
        if len(content_parts) >= 2:
            json_content = content_parts[1]
            # Remove language identifier like "json\n"
            if json_content.lower().startswith(("json", "JSON")):
                json_content = json_content[4:].lstrip()
            content = json_content

    # Remove leading/trailing whitespace and newlines
    content = content.strip()

    # Find JSON boundaries more reliably
    start_idx = content.find('[')
    end_idx = content.rfind(']') + 1

    if start_idx != -1 and end_idx > start_idx:
        content = content[start_idx:end_idx]

    return content

def _repair_json(json_str: str) -> str:
    """Repair common JSON formatting issues"""
    # Replace single quotes with double quotes for property names and values
    # This regex handles property names like 'name': and values like 'value'
    json_str = re.sub(r"'([^']*)':", r'"\1":', json_str)  # Property names
    json_str = re.sub(r":\s*'([^']*)'", r': "\1"', json_str)  # String values

    # Fix unquoted property names (word followed by colon)
    json_str = re.sub(r'(\w+)(\s*):', r'"\1"\2:', json_str)

    # Remove trailing commas before } or ]
    json_str = re.sub(r',(\s*[}\]])', r'\1', json_str)

    # Fix common boolean/null values
    json_str = re.sub(r'\btrue\b', 'true', json_str, flags=re.IGNORECASE)
    json_str = re.sub(r'\bfalse\b', 'false', json_str, flags=re.IGNORECASE)
    json_str = re.sub(r'\bnull\b', 'null', json_str, flags=re.IGNORECASE)

    return json_str

def _robust_json_parse(content: str) -> list:
    """Robust JSON parsing with multiple fallback strategies"""
    # Step 1: Clean the response
    cleaned_content = _clean_json_response(content)

    # Step 2: Try standard JSON parsing
    try:
        return json.loads(cleaned_content)
    except json.JSONDecodeError:
        pass

    # Step 3: Try with repairs
    try:
        repaired_content = _repair_json(cleaned_content)
        return json.loads(repaired_content)
    except json.JSONDecodeError:
        pass

    # Step 4: Try more aggressive cleaning
    try:
        # Remove comments and extra text
        lines = cleaned_content.split('\n')
        json_lines = []
        in_json = False

        for line in lines:
            line = line.strip()
            if line.startswith('[') or in_json:
                in_json = True
                json_lines.append(line)
                if line.endswith(']'):
                    break

        if json_lines:
            fallback_content = '\n'.join(json_lines)
            repaired_fallback = _repair_json(fallback_content)
            return json.loads(repaired_fallback)
    except json.JSONDecodeError:
        pass

    # Step 5: Last resort - try to extract individual objects
    try:
        # Look for individual object patterns
        object_pattern = r'\{[^{}]*\}'
        objects = re.findall(object_pattern, cleaned_content)

        parsed_objects = []
        for obj_str in objects:
            try:
                repaired_obj = _repair_json(obj_str)
                parsed_obj = json.loads(repaired_obj)
                parsed_objects.append(parsed_obj)
            except json.JSONDecodeError:
                continue

        if parsed_objects:
            return parsed_objects
    except Exception:
        pass

    # If all else fails, return empty list with helpful error message
    print(f"⚠️  JSON parsing failed after all repair attempts")
    print(f"📝 First 200 chars: {content[:200]}...")
    print(f"💡 Consider improving the OpenAI prompt or adding more repair patterns")
    return []

def _call_openai_vision(client, base64_image):
    """Call OpenAI vision model to extract complete payroll information"""
    try:
        prompt = """
        Analyze this Spanish payroll document (nómina) and extract ALL payroll information.

        EXTRACT THE FOLLOWING DATA:

        1. EMPLOYEE INFORMATION:
        - Full name
        - Document ID (DNI/NIE)
        - Employee number/code if present

        2. PAY PERIOD:
        - Period start date (fecha inicio)
        - Period end date (fecha fin)
        - Pay date (fecha pago)
        - Month and year

        3. MONETARY AMOUNTS:
        - Total gross (bruto total)
        - Total net (neto a percibir)
        - IRPF withholding base (base IRPF)
        - IRPF withholding amount (retención IRPF)
        - Social Security employee contribution (cuota SS trabajador)

        4. PAYROLL CONCEPT LINES:
        For each concept line, extract:
        - Concept code (if visible)
        - Concept description (e.g., "Salario base", "Plus convenio", "IRPF", etc.)
        - Amount (positive for earnings, negative for deductions)
        - Whether it's earnings (devengos) or deductions (deducciones)

        Return results in this JSON format:
        [
          {
            "name": "Employee Full Name",
            "id": "12345678A",
            "period_start": "2025-01-01",
            "period_end": "2025-01-31",
            "pay_date": "2025-01-31",
            "period_month": 1,
            "period_year": 2025,
            "bruto_total": 1500.00,
            "neto_total": 1200.00,
            "irpf_base": 1500.00,
            "irpf_retencion": 225.00,
            "ss_trabajador": 75.00,
            "concept_lines": [
              {
                "concept_code": "001",
                "concept_desc": "Salario base",
                "amount": 1200.00,
                "is_devengo": true,
                "is_deduccion": false
              },
              {
                "concept_code": "700",
                "concept_desc": "IRPF",
                "amount": -225.00,
                "is_devengo": false,
                "is_deduccion": true
              }
            ]
          }
        ]

        IMPORTANT NOTES:
        - Extract ALL visible amounts and concepts
        - Use negative amounts for deductions (IRPF, Social Security, etc.)
        - Include concept codes if visible (typically 3-digit numbers)
        - If dates are not clear, use reasonable defaults for the month/year visible
        - If multiple employees are on one document, create separate objects for each
        - RETURN ONLY VALID JSON - no explanations, comments, or markdown formatting
        - Use double quotes for all strings and property names
        - Ensure all JSON objects are properly closed with braces and brackets
        """
        
        response = client.chat.completions.create(
            model="gpt-4o",  # Use latest vision model
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": prompt
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/png;base64,{base64_image}"
                            }
                        }
                    ]
                }
            ],
            max_tokens=1500
        )
        
        content = response.choices[0].message.content

        # Use robust JSON parsing with multiple fallback strategies
        return _robust_json_parse(content)
            
    except Exception as e:
        print(f"Error calling OpenAI vision API: {e}")
        return []

# Example usage function
def process_payroll_file(file_path, openai_api_key):
    """
    Main function to process payroll files and display results
    """
    print(f"Processing payroll file: {file_path}")
    
    employees = extract_payroll_info(file_path, openai_api_key)
    
    if employees:
        print(f"\nFound {len(employees)} employees:")
        for i, emp in enumerate(employees, 1):
            name = emp.get('name', 'Unknown')
            emp_id = emp.get('id', 'No ID')
            print(f"{i}. Name: {name}, ID: {emp_id}")
    else:
        print("No employee information found.")
    
    return employees

if __name__ == "__main__":
    # Load key with the OPENAI_API_KEY environment variable
    key = os.getenv("OPENAI_API_KEY")
    employees = process_payroll_file("T_Dec.pdf", key)