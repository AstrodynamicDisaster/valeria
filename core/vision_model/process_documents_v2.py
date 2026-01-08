import json
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional
from time import sleep

from core.vision_model.document_parser.unified_parser import create_unified_parser
from core.vision_model.common import (
    get_gemini_pricing,
    calculate_cost,
    find_pdf_files,
    generate_output_filename,
)
# Ensure we import get_pdf_bytes_and_text safely
from core.vision_model.common.utils import get_pdf_bytes_and_text

def _process_and_save_chunk(
    pdf_path: Path,
    parser: Any,
    output_dir: Path,
    start_page: int,
    end_page: int,
    total_pages: int,
    is_chunked: bool = False
) -> Dict[str, Any]:
    """
    Helper function to process a specific range of pages and save the result.
    """
    # Define page range string for logging/filename
    if start_page == end_page:
        page_range_str = f"{start_page + 1}"
    else:
        page_range_str = f"{start_page + 1}-{end_page + 1}"
        
    print(f"📄 Processing pages {page_range_str} as a unified set...")
    
    result = {"page_range": page_range_str}
    
    try:
        # Get PDF content
        pdf_bytes, text_pdf = get_pdf_bytes_and_text(str(pdf_path), from_page=start_page, to_page=end_page)
        
        print("  🔍 Classifying and parsing unified document...")
        start_time = time.time()
        parsed_response, usage_info = parser.parse_with_usage(pdf_bytes, text_pdf)
        processing_time = time.time() - start_time
        
        doc_count = len(parsed_response.logical_documents)
        print(f"     ✅ Found {doc_count} logical document(s)")
        
        doc_types_found = set()
        first_doc_data = None
        
        for i, d in enumerate(parsed_response.logical_documents, 1):
            doc_types_found.add(d.type)
            print(f"        {i}. {d.type.upper()}")
            if i == 1:
                first_doc_data = d.data

        print(f"     ⏱️  Time: {processing_time:.2f}s")

        # Calculate cost
        pricing = get_gemini_pricing(parser.model)
        input_tokens = usage_info.get('input_tokens', 0)
        output_tokens = usage_info.get('output_tokens', 0)
        total_tokens = usage_info.get('total_tokens', 0)
        
        cost = calculate_cost(
            input_tokens, 
            output_tokens, 
            pricing.get("input", 0.0), 
            pricing.get("output", 0.0)
        )
        
        if total_tokens > 0:
            print(f"     🔢 Tokens: Input: {input_tokens:,} | Output: {output_tokens:,} | Total: {total_tokens:,}")
            input_price_per_1k = pricing.get("input", 0.0)
            output_price_per_1k = pricing.get("output", 0.0)
            input_price_per_1m = input_price_per_1k * 1000
            output_price_per_1m = output_price_per_1k * 1000
            print(f"     💰 Cost: ${input_price_per_1m:.2f}*Input + ${output_price_per_1m:.2f}*Output = ${cost:.4f}")
        else:
            print("     ⚠️  Warning: Token usage not captured - check API response structure")

        # Determine filename metadata
        if first_doc_data:
            dni = first_doc_data.trabajador.dni if first_doc_data.trabajador else None
            employee_name = first_doc_data.trabajador.nombre if first_doc_data.trabajador else None
            company = first_doc_data.empresa.razon_social if first_doc_data.empresa else None
            
            if "payslip" in doc_types_found and "settlement" in doc_types_found:
                doc_type_str = "PAYSLIP_SETTLEMENT"
            elif "settlement" in doc_types_found:
                doc_type_str = "SETTLEMENT"
            else:
                doc_type_str = "PAYSLIP"
            
            # Determine date
            date_for_filename = None
            for doc in parsed_response.logical_documents:
                if doc.type == "settlement":
                    if hasattr(doc.data, "fecha_liquidacion") and doc.data.fecha_liquidacion:
                        date_for_filename = doc.data.fecha_liquidacion
                        break
                    if hasattr(doc.data, "fecha_cese") and doc.data.fecha_cese:
                        date_for_filename = doc.data.fecha_cese
                        break
            
            if not date_for_filename:
                for doc in parsed_response.logical_documents:
                    if doc.type == "payslip":
                        if hasattr(doc.data, "periodo") and doc.data.periodo and doc.data.periodo.hasta:
                            date_for_filename = doc.data.periodo.hasta
                            break
                        if hasattr(doc.data, "fecha_documento") and doc.data.fecha_documento:
                            date_for_filename = doc.data.fecha_documento
                            break
            
            # Use page number in filename only if processing chunk by chunk
            page_num_for_filename = start_page if is_chunked else None
            
            base_filename = generate_output_filename(
                document_type=doc_type_str,
                dni=dni,
                employee_name=employee_name,
                company=company,
                page_num=page_num_for_filename,
                date=date_for_filename,
            )
            
            # Safety check: if chunked but filename doesn't contain page info, append it
            if is_chunked and f"_P{start_page+1}" not in base_filename:
                 base_filename += f"_P{start_page+1}"

            output_filename = f"V2_{pdf_path.stem}_{base_filename}"
        else:
            # Fallback filename
            suffix = f"_P{start_page+1}" if is_chunked else ""
            output_filename = f"V2_{pdf_path.stem}{suffix}.json"
            
        output_path = output_dir / output_filename
        
        # Handle duplicate filenames
        counter = 1
        original_output_path = output_path
        while output_path.exists():
            stem = original_output_path.stem
            if stem.lower().endswith(".json"):
                stem = stem[:-5]
            output_path = output_dir / f"{stem}_{counter}.json"
            counter += 1

        output_data = {
            "source_pdf": pdf_path.name,
            "total_pages": total_pages,
            "processed_pages": page_range_str,
            "processing_version": "V2",
            "processing_time_seconds": processing_time,
            "parsing_usage": usage_info,
            "parsing_cost_usd": cost,
            "timestamp": datetime.now().isoformat(),
            "logical_documents": [
                {
                    "type": doc.type,
                    "data": doc.data.model_dump()
                } for doc in parsed_response.logical_documents
            ],
            "global_warnings": parsed_response.warnings
        }
        
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)
            
        print(f"     💾 Saved to: {output_path.name}")
        result["logical_documents"] = output_data["logical_documents"]
        
    except Exception as e:
        print(f"  ❌ Unified parsing failed: {e}")
        import traceback
        traceback.print_exc()
        result["error"] = str(e)
        
    return result

def process_document_v2(
    pdf_path: Path,
    parser: Any,
    output_dir: Path,
    doc_index: int,
    total_docs: int,
    delay_seconds: float = 1.0,
) -> Dict[str, Any]:
    """
    Process a PDF document using the Unified Parser (V2).
    """
    print(f"\n{'='*80}")
    print(f"Processing document {doc_index}/{total_docs} (V2): {pdf_path.name}")
    print(f"{'='*80}")
    
    import pymupdf
    try:
        doc = pymupdf.open(str(pdf_path))
        total_pages = doc.page_count
        doc.close()
    except Exception as e:
        print(f"❌ Error opening PDF: {e}")
        return {"error": str(e), "pdf": pdf_path.name}

    results = {
        "pdf": pdf_path.name,
        "total_pages": total_pages,
        "chunks": []
    }

    # STRATEGY:
    # 1. If PDF <= 5 pages: Process as a single unified document (context preserved)
    # 2. If PDF > 5 pages: Process page by page (chunk size = 1)
    
    if total_pages <= 5:
        print(f"📚 Document is short ({total_pages} pages). Processing as a single unit.")
        result = _process_and_save_chunk(
            pdf_path, parser, output_dir, 
            start_page=0, end_page=total_pages-1, 
            total_pages=total_pages, is_chunked=False
        )
        results["chunks"].append(result)
        sleep(delay_seconds)
    else:
        print(f"📚 Document is long ({total_pages} pages). Processing page by page.")
        for page_num in range(total_pages):
            result = _process_and_save_chunk(
                pdf_path, parser, output_dir, 
                start_page=page_num, end_page=page_num, 
                total_pages=total_pages, is_chunked=True
            )
            results["chunks"].append(result)
            sleep(delay_seconds) # Respect rate limits between pages

    return results

def main_v2(config: Optional[Dict[str, Any]] = None):
    DEFAULT_CONFIG = {
        "input_path": "docs_to_process/",
        "output_dir": "processed_documents_v2",
        "provider": "gemini",
        "model": "gemini-3-flash-preview",
        "delay": 2.0,
    }
    
    if config:
        DEFAULT_CONFIG.update(config)
    config = DEFAULT_CONFIG

    input_path = Path(config["input_path"])
    output_dir = Path(__file__).parent.parent.parent / config["output_dir"]
    output_dir.mkdir(exist_ok=True)
    
    pdf_files = find_pdf_files(input_path)
    if not pdf_files:
        print("❌ No PDF files found")
        return

    # Skip already processed (V2)
    processed_pdfs = set()
    for json_file in output_dir.rglob("V2_*.json"):
        try:
            with open(json_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                if "source_pdf" in data:
                    processed_pdfs.add(data["source_pdf"])
        except Exception:
            print(f"Error loading JSON file: {json_file}")
            continue
            
    # For chunked processing, check if ALL chunks are done might be tricky.
    # For now, simple check: if ANY V2 JSON exists for this source PDF, we assume it's started/done.
    
    pdf_files_to_process = []
    for f in pdf_files:
        if f.name not in processed_pdfs:
            pdf_files_to_process.append(f)
            
    print(f"📚 Found {len(pdf_files_to_process)} new PDF file(s) to process with V2")

    parser = create_unified_parser(
        provider=config["provider"],
        model=config["model"]
    )

    for i, pdf_path in enumerate(pdf_files_to_process, 1):
        process_document_v2(
            pdf_path, 
            parser, 
            output_dir, 
            i, 
            len(pdf_files_to_process), 
            delay_seconds=config["delay"]
        )

if __name__ == "__main__":

    custom_config = {
        "input_path": "docs_to_process_fliits",      # Carpeta de entrada
        "output_dir": "processed_documents_fliits", # Carpeta de salida
        "provider": "gemini",
        "model": "gemini-3-flash-preview",
        "delay": 1.5
    }
    import os
    if not os.path.exists(custom_config["input_path"]):
        print(f"⚠️ Atención: La carpeta '{custom_config['input_path']}' no existe. Créala y pon los PDFs ahí.")
    else:
        main_v2(custom_config)
