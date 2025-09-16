import json
import pandas as pd
from openai import OpenAI
import base64
from PIL import Image
import io
import pathlib
import os

def extract_payroll_info(file_path, openai_api_key):
    """
    Extract employee names and ID numbers from payroll files (image, PDF, Excel)
    using OpenAI's vision model.
    
    Args:
        file_path (str): Path to the file (image, PDF, or Excel)
        openai_api_key (str): OpenAI API key
    
    Returns:
        list: List of dictionaries containing employee names and IDs
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

def _call_openai_vision(client, base64_image):
    """Call OpenAI vision model to extract employee information"""
    try:
        prompt = """
        Analyze this payroll document and identify which type it is:

        TYPE 1: PAYROLL SUMMARY - A table/grid format where columns or rows contain multiple employee names with payroll concepts and amounts.
        TYPE 2: INDIVIDUAL PAYROLL - A single employee's payroll information for a specific period.

        For TYPE 1 (PAYROLL SUMMARY):
        - Extract all employee names from column headers, rows, or any labeled sections
        - If employee IDs are present, include them
        - Look for sections labeled "Employee", "Name", "Worker", etc.
        - Ignore monetary values, dates, and payroll concept labels
        
        For TYPE 2 (INDIVIDUAL PAYROLL):
        - Extract the name of the single employee featured in this document
        - Look for employee ID, identification number, SSN, or similar identifiers
        - The employee name might be in headers, title sections, or recipient fields
        
        Return results in this JSON format: 
        [{"name": "Employee Full Name", "id": "ID123"}, ...]
        
        If no ID is found for an employee, omit the "id" field.
        Exclude headers, labels, company names, and non-employee text.
        If you're uncertain whether text represents an employee name, include it and note your uncertainty in the name field.
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
        print(f"Raw response: {content}")
        
        # Try to parse JSON from the response
        try:
            # First, check if response is wrapped in markdown code blocks
            if "```" in content:
                # Extract content between code blocks
                content_parts = content.split("```")
                # The JSON is typically in the second part (after first ```)
                if len(content_parts) >= 2:
                    # Remove potential "json\n" or "JSON\n" header that might be included
                    json_content = content_parts[1]
                    if json_content.lower().startswith("json"):
                        json_content = json_content[4:].lstrip()
                    # Now parse the actual JSON content
                    employees = json.loads(json_content)
                    return employees
            
            # Fallback to the original method if no markdown code blocks
            start_idx = content.find('[')
            end_idx = content.rfind(']') + 1
            
            if start_idx != -1 and end_idx != 0:
                json_str = content[start_idx:end_idx]
                employees = json.loads(json_str)
                return employees
            else:
                print("No valid JSON found in response")
                return []
                
        except json.JSONDecodeError as e:
            print(f"Failed to parse JSON from response: {content}")
            print(f"JSON error: {e}")
            return []
            
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