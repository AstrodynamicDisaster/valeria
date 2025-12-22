import json
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional
from time import sleep

from core.vision_model.auto_parser import AutoParser, UnsupportedDocumentTypeError
from core.vision_model.payslips.payslip_models import PayslipData
from core.vision_model.common import (
    get_openai_pricing,
    get_gemini_pricing,
    calculate_cost,
    find_pdf_files,
    get_page_as_pdf,
    generate_output_filename,
)


# Default configuration
DEFAULT_CONFIG = {
    "input_path": None,  # Required - set this
    "output_dir": "processed_documents",
    "provider": "gemini",  # LLM provider for parsing
    "model": "gemini-3-flash-preview",  # Model name for parsing
    "classification_provider": "gemini",  # LLM provider for classification
    "classification_model": "gemini-3-flash-preview",  # Model name for classification
    "delay": 1.0,  # Delay between API calls in seconds
}


def process_document(
    pdf_path: Path,
    parser: AutoParser,
    output_dir: Path,
    delay_seconds: float = 1.0,
) -> Dict[str, Any]:
    """
    Process a PDF document with all its pages.
    
    Args:
        pdf_path: Path to PDF file
        parser: AutoParser instance
        output_dir: Directory to save results
        delay_seconds: Delay between API calls
    
    Returns:
        Dictionary with processing results
    """
    print(f"\n{'='*80}")
    print(f"Processing: {pdf_path.name}")
    print(f"{'='*80}")
    
    doc = None
    try:
        import pymupdf
        doc = pymupdf.open(str(pdf_path))
        total_pages = len(doc)
        doc.close()
    except Exception as e:
        print(f"❌ Error opening PDF: {e}")
        return {"error": str(e), "pdf": pdf_path.name}
    
    results = {
        "pdf": pdf_path.name,
        "total_pages": total_pages,
        "pages": []
    }
    
    for page_num in range(total_pages):
        print(f"\n📄 Processing page {page_num + 1}/{total_pages}...")
        
        try:
            # Get page as PDF bytes and text
            pdf_bytes, text_pdf = get_page_as_pdf(str(pdf_path), page_num)
            
            # Parse with AutoParser (with usage tracking for parsing only)
            print("  🔍 Classifying and parsing document...")
            start_time = time.time()
            
            try:
                parsed_data, classification_info, usage_info = parser.parse_with_usage(pdf_bytes, text_pdf)
                processing_time = time.time() - start_time
                
                document_type = classification_info["document_type"]
                confidence = classification_info.get("confidence", "unknown")
                reasoning = classification_info.get("reasoning", "")
                classification_time = usage_info.get("classification_time_seconds", 0.0)
                parsing_time = processing_time - classification_time
                
                print(f"     ✅ Document type: {document_type.upper()} (confidence: {confidence})")
                print(f"     ⏱️  Time: Total {processing_time:.2f}s (Classification: {classification_time:.2f}s | Parsing: {parsing_time:.2f}s)")
                if reasoning:
                    print(f"     💭 Reasoning: {reasoning}")
                
                # Display token usage and pricing (parsing only, not classification)
                input_tokens = usage_info.get('input_tokens', 0)
                output_tokens = usage_info.get('output_tokens', 0)
                total_tokens = usage_info.get('total_tokens', 0)
                
                if total_tokens > 0:
                    print(f"     🔢 Tokens: Input: {input_tokens:,} | Output: {output_tokens:,} | Total: {total_tokens:,}")
                    
                    # Calculate and display cost
                    if parser.parsing_provider == "openai":
                        pricing = get_openai_pricing(parser.parsing_model)
                    else:
                        pricing = get_gemini_pricing(parser.parsing_model)
                    
                    input_price_per_1k = pricing.get("input", 0.0)
                    output_price_per_1k = pricing.get("output", 0.0)
                    cost = calculate_cost(input_tokens, output_tokens, input_price_per_1k, output_price_per_1k)
                    
                    # Show per-1M-token prices in formula (convert from per-1K)
                    input_price_per_1m = input_price_per_1k * 1000
                    output_price_per_1m = output_price_per_1k * 1000
                    print(f"     💰 Cost: ${input_price_per_1m:.2f}*Input + ${output_price_per_1m:.2f}*Output = ${cost:.4f}")
                else:
                    print("     ⚠️  Warning: Token usage not captured - check API response structure")
                    cost = 0.0
                
                # Extract metadata for filename
                date_for_filename = None
                if isinstance(parsed_data, PayslipData):
                    dni = parsed_data.trabajador.dni if parsed_data.trabajador else None
                    employee_name = parsed_data.trabajador.nombre if parsed_data.trabajador else None
                    company = parsed_data.empresa.razon_social if parsed_data.empresa else None
                    # Use classification to distinguish payslip from payslip+settlement
                    if document_type == "payslip+settlement":
                        doc_type = "PAYSLIP_FINIQUITO"
                    else:
                        doc_type = "PAYSLIP"
                    # Use "hasta" date for payslips
                    if parsed_data.periodo and parsed_data.periodo.hasta:
                        date_for_filename = parsed_data.periodo.hasta
                else:  # SettlementData
                    dni = parsed_data.trabajador.dni if parsed_data.trabajador else None
                    employee_name = parsed_data.trabajador.nombre if parsed_data.trabajador else None
                    company = parsed_data.empresa.razon_social if parsed_data.empresa else None
                    doc_type = "SETTLEMENT"
                    # Use "fecha_liquidacion" for settlements
                    if parsed_data.fecha_liquidacion:
                        date_for_filename = parsed_data.fecha_liquidacion
                
                # Generate filename
                filename = generate_output_filename(
                    document_type=doc_type,
                    dni=dni,
                    employee_name=employee_name,
                    company=company,
                    page_num=page_num if total_pages > 1 else None,
                    date=date_for_filename,
                )
                
                output_path = output_dir / filename
                
                # Handle duplicate filenames
                counter = 1
                original_output_path = output_path
                while output_path.exists():
                    stem = original_output_path.stem
                    output_path = output_dir / f"{stem}_{counter}.json"
                    counter += 1
                
                # Prepare output data
                output_data = {
                    "source_pdf": pdf_path.name,
                    "page": page_num + 1,
                    "total_pages": total_pages,
                    "document_type": document_type,
                    "classification": classification_info,
                    "processing_time_seconds": processing_time,
                    "parsing_usage": usage_info,  # Only parsing usage, not classification
                    "parsing_cost_usd": cost if total_tokens > 0 else 0.0,
                    "timestamp": datetime.now().isoformat(),
                    "data": parsed_data.model_dump(),
                }
                
                # Save to JSON
                with open(output_path, "w", encoding="utf-8") as f:
                    json.dump(output_data, f, indent=2, ensure_ascii=False)
                
                print(f"     💾 Saved to: {output_path.name}")
                
                page_result = {
                    "page": page_num + 1,
                    "success": True,
                    "document_type": document_type,
                    "classification": classification_info,
                    "processing_time_seconds": processing_time,
                    "classification_time_seconds": classification_time,
                    "parsing_time_seconds": parsing_time,
                    "parsing_usage": usage_info,
                    "parsing_cost_usd": cost if total_tokens > 0 else 0.0,
                    "output_filename": output_path.name,
                }
                
                results["pages"].append(page_result)
                sleep(delay_seconds)  # Rate limiting
                
            except UnsupportedDocumentTypeError as e:
                # Document classified as "other" - skip processing
                classification_time = e.classification_time
                print(f"     ⏭️  Skipping document: {str(e)}")
                print(f"     ⏱️  Classification time: {classification_time:.2f}s")
                
                page_result = {
                    "page": page_num + 1,
                    "success": False,
                    "skipped": True,
                    "reason": "Document classified as 'other'",
                    "classification_time_seconds": classification_time,
                }
                results["pages"].append(page_result)
                sleep(delay_seconds)  # Rate limiting
                
            except Exception as e:
                print(f"  ❌ Parsing failed: {e}")
                import traceback
                traceback.print_exc()
                page_result = {
                    "page": page_num + 1,
                    "success": False,
                    "error": str(e),
                }
                results["pages"].append(page_result)
            
        except Exception as e:
            print(f"  ❌ Error processing page {page_num + 1}: {e}")
            import traceback
            traceback.print_exc()
            results["pages"].append({
                "page": page_num + 1,
                "success": False,
                "error": str(e)
            })
    
    return results


def main(config: Optional[Dict[str, Any]] = None):
    """
    Main processing function.
    
    Args:
        config: Configuration dictionary. If None, uses DEFAULT_CONFIG.
                Required keys: input_path
                Optional keys: output_dir, provider, model, classification_provider,
                              classification_model, delay
    """
    # Merge with default config
    if config is None:
        config = DEFAULT_CONFIG.copy()
    else:
        merged_config = DEFAULT_CONFIG.copy()
        merged_config.update(config)
        config = merged_config
    
    # Validate required config
    if not config.get("input_path"):
        print("❌ 'input_path' is required in config")
        return
    
    # Get paths
    input_path = Path(config["input_path"])
    if not input_path.exists():
        print(f"❌ Path does not exist: {input_path}")
        return
    
    # Determine output directory (in workspace root)
    workspace_root = Path(__file__).parent.parent.parent
    output_dir = workspace_root / config["output_dir"]
    output_dir.mkdir(exist_ok=True)
    
    # Find PDF files
    if input_path.is_file() and input_path.suffix.lower() == ".pdf":
        pdf_files = [input_path]
    elif input_path.is_dir():
        pdf_files = find_pdf_files(input_path)
    else:
        print(f"❌ Invalid input path: {input_path}")
        return
    
    if not pdf_files:
        print(f"❌ No PDF files found in {input_path}")
        return
    
    print(f"📚 Found {len(pdf_files)} PDF file(s) to process")
    for pdf in pdf_files:
        print(f"   - {pdf.name}")
    
    # Initialize parser
    print("\n🔧 Initializing parser...")
    try:
        auto_parser = AutoParser(
            classification_provider=config["classification_provider"],
            classification_model=config["classification_model"],
            parsing_provider=config["provider"],
            parsing_model=config["model"],
        )
        print("  ✅ Parser initialized")
        print(f"     Classification: {config['classification_provider']}/{config['classification_model']}")
        print(f"     Parsing: {config['provider']}/{config['model']}")
    except Exception as e:
        print(f"  ❌ Failed to initialize parser: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # Process each PDF
    all_results = []
    for pdf_path in pdf_files:
        result = process_document(
            pdf_path,
            auto_parser,
            output_dir,
            delay_seconds=config["delay"]
        )
        all_results.append(result)
    
    # Summary
    print(f"\n{'='*80}")
    print("SUMMARY")
    print(f"{'='*80}")
    
    total_pdfs = len(all_results)
    total_pages = sum(r.get("total_pages", 0) for r in all_results)
    
    # Successful pages: successfully parsed
    successful_pages = sum(
        sum(1 for p in r.get("pages", []) if p.get("success"))
        for r in all_results
    )
    
    # Skipped pages: classified as "other" and intentionally not processed
    skipped_pages = sum(
        sum(1 for p in r.get("pages", []) if p.get("skipped"))
        for r in all_results
    )
    
    # Failed pages: actual errors during processing (not skipped)
    failed_pages = sum(
        sum(1 for p in r.get("pages", []) if not p.get("success") and not p.get("skipped") and p.get("error"))
        for r in all_results
    )
    
    payslip_count = sum(
        sum(1 for p in r.get("pages", []) if p.get("document_type") == "payslip")
        for r in all_results
    )
    payslip_settlement_count = sum(
        sum(1 for p in r.get("pages", []) if p.get("document_type") == "payslip+settlement")
        for r in all_results
    )
    settlement_count = sum(
        sum(1 for p in r.get("pages", []) if p.get("document_type") == "settlement")
        for r in all_results
    )
    other_count = skipped_pages  # "other" documents are the skipped ones
    
    total_processing_time = sum(
        sum(p.get("processing_time_seconds", 0) for p in r.get("pages", []))
        for r in all_results
    )
    
    # Calculate total classification time
    total_classification_time = sum(
        sum(p.get("classification_time_seconds", 0) for p in r.get("pages", []))
        for r in all_results
    )
    
    # Calculate total parsing time
    total_parsing_time = sum(
        sum(p.get("parsing_time_seconds", 0) for p in r.get("pages", []))
        for r in all_results
    )
    
    # Calculate total cost (parsing only)
    total_cost = sum(
        sum(p.get("parsing_cost_usd", 0.0) for p in r.get("pages", []))
        for r in all_results
    )
    
    # Calculate total tokens (parsing only)
    total_input_tokens = sum(
        sum(p.get("parsing_usage", {}).get("input_tokens", 0) for p in r.get("pages", []))
        for r in all_results
    )
    total_output_tokens = sum(
        sum(p.get("parsing_usage", {}).get("output_tokens", 0) for p in r.get("pages", []))
        for r in all_results
    )
    total_tokens = total_input_tokens + total_output_tokens
    
    print(f"📊 Total PDFs processed: {total_pdfs}")
    print(f"📄 Total pages processed: {total_pages}")
    print(f"✅ Successful pages: {successful_pages}")
    print(f"⏭️  Skipped pages (other docs): {skipped_pages}")
    print(f"❌ Failed pages (errors): {failed_pages}")
    print("\n📋 Document Types:")
    print(f"   - Payslips: {payslip_count}")
    print(f"   - Payslips + Settlement: {payslip_settlement_count}")
    print(f"   - Settlements: {settlement_count}")
    print(f"   - Other (skipped): {other_count}")
    print(f"\n⏱️  Total time: {total_processing_time:.2f}s ({total_processing_time/60:.2f} min)")
    print(f"   - Classification: {total_classification_time:.2f}s ({total_classification_time/60:.2f} min)")
    print(f"   - Parsing: {total_parsing_time:.2f}s ({total_parsing_time/60:.2f} min)")
    print(f"🔢 Total parsing tokens: {total_tokens:,} (Input: {total_input_tokens:,}, Output: {total_output_tokens:,})")
    print(f"💰 Total parsing cost: ${total_cost:.4f}")
    print(f"\n📁 Results saved to: {output_dir}")
    
    # Save processing summary
    summary_data = {
        "timestamp": datetime.now().isoformat(),
        "input_path": str(input_path),
        "output_dir": str(output_dir),
        "parser_config": {
            "classification_provider": config["classification_provider"],
            "classification_model": config["classification_model"],
            "parsing_provider": config["provider"],
            "parsing_model": config["model"],
        },
        "summary": {
            "total_pdfs": total_pdfs,
            "total_pages": total_pages,
            "successful_pages": successful_pages,
            "skipped_pages": skipped_pages,
            "failed_pages": failed_pages,
            "document_types": {
                "payslip": payslip_count,
                "payslip_settlement": payslip_settlement_count,
                "settlement": settlement_count,
                "other_skipped": other_count,
            },
            "total_processing_time_seconds": total_processing_time,
            "total_classification_time_seconds": total_classification_time,
            "total_parsing_time_seconds": total_parsing_time,
            "total_parsing_tokens": total_tokens,
            "total_parsing_input_tokens": total_input_tokens,
            "total_parsing_output_tokens": total_output_tokens,
            "total_parsing_cost_usd": total_cost,
        },
        "results": all_results
    }
    
    summary_path = output_dir / f"processing_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(summary_data, f, indent=2, ensure_ascii=False)
    print(f"📊 Processing summary saved to: {summary_path.name}")


if __name__ == "__main__":
    # Example usage with dict config
    config = {
        "input_path": "nominas_tepuy_nov.pdf", # "core/vision_model/tests/sample_docs",  # Change this to your path
        "output_dir": "processed_documents",
        "provider": "gemini",
        "model": "gemini-3-flash-preview",
        "classification_provider": "gemini",
        "classification_model": "gemini-3-flash-preview",
        "delay": 2,
    }
    
    main(config)
