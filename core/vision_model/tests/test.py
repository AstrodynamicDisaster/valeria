import json
import time
from pathlib import Path
from datetime import datetime
from time import sleep
from typing import Dict, Any

from core.vision_model.payslips.payslip_parsers import (
    create_gemini_parser,
    create_openai_parser,
)
from core.vision_model.payslips.payslip_models import PayslipData
from core.vision_model.common import (
    compare_json,
    get_openai_pricing,
    get_gemini_pricing,
    calculate_cost,
    get_page_as_pdf,
    find_pdf_files,
)


def process_pdf_comparison(
    pdf_path: Path,
    gemini_parser,
    openai_parser,
    output_dir: Path,
    delay_seconds: float = 1.0
) -> Dict[str, Any]:
    """
    Process a PDF with both parsers and compare results.
    
    Args:
        pdf_path: Path to PDF file
        gemini_parser: Gemini parser instance
        openai_parser: OpenAI parser instance
        output_dir: Directory to save comparison logs
        delay_seconds: Delay between API calls
    
    Returns:
        Dictionary with comparison results
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
            
            # Parse with Gemini (with timing and usage tracking)
            print("  🔵 Parsing with Gemini...")
            gemini_result = None
            gemini_usage = None
            gemini_time = None
            gemini_validation_error = None
            gemini_aportacion_corrected = False
            try:
                start_time = time.time()
                gemini_result, gemini_usage = gemini_parser.parse_with_usage(pdf_bytes, text_pdf)
                gemini_time = time.time() - start_time
                input_tokens = gemini_usage.get('input_tokens', 0)
                output_tokens = gemini_usage.get('output_tokens', 0)
                total_tokens = gemini_usage.get('total_tokens', 0)
                
                # Display timing
                print(f"     ⏱️  Time: {gemini_time:.2f}s")
                
                # Display tokens
                if total_tokens > 0:
                    print(f"     🔢 Tokens: Input: {input_tokens:,} | Output: {output_tokens:,} | Total: {total_tokens:,}")
                    
                    # Calculate and display cost
                    gemini_pricing = get_gemini_pricing(gemini_parser.model)
                    input_price_per_1k = gemini_pricing["input"]
                    output_price_per_1k = gemini_pricing["output"]
                    cost = calculate_cost(input_tokens, output_tokens, input_price_per_1k, output_price_per_1k)
                    # Show per-1M-token prices in formula (convert from per-1K)
                    input_price_per_1m = input_price_per_1k * 1000
                    output_price_per_1m = output_price_per_1k * 1000
                    print(f"     💰 Cost: ${input_price_per_1m:.2f}*Input + ${output_price_per_1m:.2f}*Output = ${cost:.4f}")
                else:
                    print("     ⚠️  Warning: Token usage not captured - check API response structure")
                
                # Validate with Pydantic model
                gemini_validation_error = None
                gemini_aportacion_corrected = False
                try:
                    gemini_model = PayslipData(**gemini_result)
                    gemini_aportacion_corrected = gemini_model.verify_and_correct_aportacion_empresa_total()
                    if gemini_aportacion_corrected:
                        print("     ✅ Validation passed (aportacion_empresa_total corrected)")
                    else:
                        print("     ✅ Validation passed")
                except Exception as e:
                    gemini_validation_error = str(e)
                    print(f"     ❌ Validation failed: {gemini_validation_error}")
                
                sleep(delay_seconds)  # Rate limiting
            except Exception as e:
                print(f"  ❌ Gemini parsing failed: {e}")
                gemini_result = None
                gemini_usage = None
                gemini_time = None
                gemini_validation_error = None
                gemini_aportacion_corrected = False
            
            # Parse with OpenAI (with timing and usage tracking)
            print("  🟢 Parsing with OpenAI...")
            openai_result = None
            openai_usage = None
            openai_time = None
            openai_validation_error = None
            openai_aportacion_corrected = False
            try:
                start_time = time.time()
                openai_result, openai_usage = openai_parser.parse_with_usage(pdf_bytes, text_pdf)
                openai_time = time.time() - start_time
                input_tokens = openai_usage.get('input_tokens', 0)
                output_tokens = openai_usage.get('output_tokens', 0)
                total_tokens = openai_usage.get('total_tokens', 0)
                
                # Display timing
                print(f"     ⏱️  Time: {openai_time:.2f}s")
                
                # Display tokens
                if total_tokens > 0:
                    print(f"     🔢 Tokens: Input: {input_tokens:,} | Output: {output_tokens:,} | Total: {total_tokens:,}")
                    
                    # Calculate and display cost
                    openai_pricing = get_openai_pricing(openai_parser.model)
                    input_price_per_1k = openai_pricing["input"]
                    output_price_per_1k = openai_pricing["output"]
                    cost = calculate_cost(input_tokens, output_tokens, input_price_per_1k, output_price_per_1k)
                    # Show per-1M-token prices in formula (convert from per-1K)
                    input_price_per_1m = input_price_per_1k * 1000
                    output_price_per_1m = output_price_per_1k * 1000
                    print(f"     💰 Cost: ${input_price_per_1m:.2f}*Input + ${output_price_per_1m:.2f}*Output = ${cost:.4f}")
                else:
                    print("     ⚠️  Warning: Token usage not captured - check API response structure")
                
                # Validate with Pydantic model
                openai_validation_error = None
                openai_aportacion_corrected = False
                try:
                    openai_model = PayslipData(**openai_result)
                    openai_aportacion_corrected = openai_model.verify_and_correct_aportacion_empresa_total()
                    if openai_aportacion_corrected:
                        print("     ✅ Validation passed (aportacion_empresa_total corrected)")
                    else:
                        print("     ✅ Validation passed")
                except Exception as e:
                    openai_validation_error = str(e)
                    print(f"     ❌ Validation failed: {openai_validation_error}")
                
                sleep(delay_seconds)  # Rate limiting
            except Exception as e:
                print(f"  ❌ OpenAI parsing failed: {e}")
                openai_result = None
                openai_usage = None
                openai_time = None
                openai_validation_error = None
                openai_aportacion_corrected = False
            
            # Compare results
            if gemini_result and openai_result:
                diffs = compare_json(
                    gemini_result,
                    openai_result,
                    ignore_array_order=True,
                    object_list_key="concepto"
                )
                
                # Calculate costs
                gemini_pricing = get_gemini_pricing(gemini_parser.model)
                openai_pricing = get_openai_pricing(openai_parser.model)
                
                gemini_cost = calculate_cost(
                    gemini_usage.get("input_tokens", 0),
                    gemini_usage.get("output_tokens", 0),
                    gemini_pricing["input"],
                    gemini_pricing["output"]
                ) if gemini_usage else 0.0
                
                openai_cost = calculate_cost(
                    openai_usage.get("input_tokens", 0),
                    openai_usage.get("output_tokens", 0),
                    openai_pricing["input"],
                    openai_pricing["output"]
                ) if openai_usage else 0.0
                
                page_result = {
                    "page": page_num + 1,
                    "gemini_success": True,
                    "openai_success": True,
                    "differences_count": len(diffs),
                    "differences": diffs,
                    "gemini": {
                        "processing_time_seconds": gemini_time,
                        "usage": gemini_usage,
                        "cost_usd": gemini_cost,
                        "validation_error": gemini_validation_error,
                        "aportacion_corrected": gemini_aportacion_corrected,
                    },
                    "openai": {
                        "processing_time_seconds": openai_time,
                        "usage": openai_usage,
                        "cost_usd": openai_cost,
                        "validation_error": openai_validation_error,
                        "aportacion_corrected": openai_aportacion_corrected,
                    }
                }
                
                # Save comparison log
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                log_filename = f"{pdf_path.stem}_page{page_num + 1}_{timestamp}.txt"
                log_path = output_dir / log_filename
                
                with open(log_path, "w", encoding="utf-8") as f:
                    f.write(f"PDF: {pdf_path.name}\n")
                    f.write(f"Page: {page_num + 1}/{total_pages}\n")
                    f.write(f"Timestamp: {datetime.now().isoformat()}\n")
                    f.write(f"{'='*80}\n\n")
                    f.write(f"Differences found: {len(diffs)}\n\n")
                    
                    if diffs:
                        f.write("DIFFERENCES:\n")
                        f.write("-" * 80 + "\n")
                        for diff in diffs:
                            f.write(f"{diff}\n")
                    else:
                        f.write("✅ No differences found - results match!\n")
                    
                    f.write("\n" + "=" * 80 + "\n\n")
                    f.write("GEMINI RESULT:\n")
                    f.write("-" * 80 + "\n")
                    f.write(json.dumps(gemini_result, indent=2, ensure_ascii=False))
                    f.write("\n\n" + "=" * 80 + "\n\n")
                    f.write("OPENAI RESULT:\n")
                    f.write("-" * 80 + "\n")
                    f.write(json.dumps(openai_result, indent=2, ensure_ascii=False))
                
                print(f"  📝 Comparison saved to: {log_filename}")
                if diffs:
                    print(f"  ⚠️  Found {len(diffs)} differences")
                    for diff in diffs[:5]:  # Show first 5 differences
                        print(f"     - {diff}")
                    if len(diffs) > 5:
                        print(f"     ... and {len(diffs) - 5} more")
                else:
                    print("  ✅ No differences - results match!")
                    
            elif gemini_result:
                gemini_pricing = get_gemini_pricing(gemini_parser.model)
                gemini_cost = calculate_cost(
                    gemini_usage.get("input_tokens", 0) if gemini_usage else 0,
                    gemini_usage.get("output_tokens", 0) if gemini_usage else 0,
                    gemini_pricing["input"],
                    gemini_pricing["output"]
                ) if gemini_usage else 0.0
                
                page_result = {
                    "page": page_num + 1,
                    "gemini_success": True,
                    "openai_success": False,
                    "error": "OpenAI parsing failed",
                    "gemini": {
                        "processing_time_seconds": gemini_time,
                        "usage": gemini_usage,
                        "cost_usd": gemini_cost,
                    },
                    "openai": None
                }
            elif openai_result:
                openai_pricing = get_openai_pricing(openai_parser.model)
                openai_cost = calculate_cost(
                    openai_usage.get("input_tokens", 0) if openai_usage else 0,
                    openai_usage.get("output_tokens", 0) if openai_usage else 0,
                    openai_pricing["input"],
                    openai_pricing["output"]
                ) if openai_usage else 0.0
                
                page_result = {
                    "page": page_num + 1,
                    "gemini_success": False,
                    "openai_success": True,
                    "error": "Gemini parsing failed",
                    "gemini": None,
                    "openai": {
                        "processing_time_seconds": openai_time,
                        "usage": openai_usage,
                        "cost_usd": openai_cost,
                    }
                }
            else:
                page_result = {
                    "page": page_num + 1,
                    "gemini_success": False,
                    "openai_success": False,
                    "error": "Both parsers failed",
                    "gemini": None,
                    "openai": None
                }
            
            results["pages"].append(page_result)
            
        except Exception as e:
            print(f"  ❌ Error processing page {page_num + 1}: {e}")
            results["pages"].append({
                "page": page_num + 1,
                "error": str(e)
            })
    
    return results


def main():
    """Main test function."""
    # Get paths
    test_dir = Path(__file__).parent
    sample_docs_dir = test_dir / "sample_docs"
    output_dir = test_dir / "test_executions"
    
    # Create output directory if it doesn't exist
    output_dir.mkdir(exist_ok=True)
    
    # Find all PDFs
    pdf_files = find_pdf_files(sample_docs_dir)
    
    if not pdf_files:
        print(f"❌ No PDF files found in {sample_docs_dir}")
        return
    
    print(f"📚 Found {len(pdf_files)} PDF file(s) to process")
    for pdf in pdf_files:
        print(f"   - {pdf.name}")
    
    # Initialize parsers
    print("\n🔧 Initializing parsers...")
    try:
        gemini_parser = create_gemini_parser()
        print("  ✅ Gemini parser initialized")
    except Exception as e:
        print(f"  ❌ Failed to initialize Gemini parser: {e}")
        gemini_parser = None
    
    try:
        openai_parser = create_openai_parser()
        print("  ✅ OpenAI parser initialized")
    except Exception as e:
        print(f"  ❌ Failed to initialize OpenAI parser: {e}")
        openai_parser = None
    
    if not gemini_parser or not openai_parser:
        print("\n❌ Cannot run tests - one or both parsers failed to initialize")
        return
    
    # Process each PDF
    all_results = []
    for pdf_path in pdf_files:
        result = process_pdf_comparison(
            pdf_path,
            gemini_parser,
            openai_parser,
            output_dir,
            delay_seconds=1.0
        )
        all_results.append(result)
    
    # Summary
    print(f"\n{'='*80}")
    print("SUMMARY")
    print(f"{'='*80}")
    
    total_pages = sum(r.get("total_pages", 0) for r in all_results)
    total_differences = sum(
        sum(p.get("differences_count", 0) for p in r.get("pages", []))
        for r in all_results
    )
    
    # Calculate aggregated metrics
    gemini_times = []
    openai_times = []
    gemini_costs = []
    openai_costs = []
    gemini_input_tokens = []
    gemini_output_tokens = []
    openai_input_tokens = []
    openai_output_tokens = []
    gemini_validation_errors = []
    openai_validation_errors = []
    gemini_aportacion_corrected_count = 0
    openai_aportacion_corrected_count = 0
    
    for result in all_results:
        for page in result.get("pages", []):
            if page.get("gemini") and page["gemini"].get("processing_time_seconds"):
                gemini_times.append(page["gemini"]["processing_time_seconds"])
                gemini_costs.append(page["gemini"].get("cost_usd", 0.0))
                usage = page["gemini"].get("usage", {})
                gemini_input_tokens.append(usage.get("input_tokens", 0))
                gemini_output_tokens.append(usage.get("output_tokens", 0))
                if page["gemini"].get("validation_error"):
                    gemini_validation_errors.append(page["gemini"]["validation_error"])
                if page["gemini"].get("aportacion_corrected"):
                    gemini_aportacion_corrected_count += 1
            
            if page.get("openai") and page["openai"].get("processing_time_seconds"):
                openai_times.append(page["openai"]["processing_time_seconds"])
                openai_costs.append(page["openai"].get("cost_usd", 0.0))
                usage = page["openai"].get("usage", {})
                openai_input_tokens.append(usage.get("input_tokens", 0))
                openai_output_tokens.append(usage.get("output_tokens", 0))
                if page["openai"].get("validation_error"):
                    openai_validation_errors.append(page["openai"]["validation_error"])
                if page["openai"].get("aportacion_corrected"):
                    openai_aportacion_corrected_count += 1
    
    # Calculate averages
    avg_gemini_time = sum(gemini_times) / len(gemini_times) if gemini_times else 0
    avg_openai_time = sum(openai_times) / len(openai_times) if openai_times else 0
    avg_gemini_cost = sum(gemini_costs) / len(gemini_costs) if gemini_costs else 0
    avg_openai_cost = sum(openai_costs) / len(openai_costs) if openai_costs else 0
    
    total_gemini_time = sum(gemini_times)
    total_openai_time = sum(openai_times)
    total_gemini_cost = sum(gemini_costs)
    total_openai_cost = sum(openai_costs)
    
    # Extrapolate to 10,000 documents
    EXTRAPOLATION_TARGET = 10000
    extrapolated_gemini_time = avg_gemini_time * EXTRAPOLATION_TARGET
    extrapolated_openai_time = avg_openai_time * EXTRAPOLATION_TARGET
    extrapolated_gemini_cost = avg_gemini_cost * EXTRAPOLATION_TARGET
    extrapolated_openai_cost = avg_openai_cost * EXTRAPOLATION_TARGET
    
    print(f"Total PDFs processed: {len(all_results)}")
    print(f"Total pages processed: {total_pages}")
    print(f"Total differences found: {total_differences}")
    
    print("\n" + "=" * 80)
    print("PERFORMANCE METRICS")
    print("=" * 80)
    
    print(f"\n🔵 GEMINI ({gemini_parser.model}):")
    print(f"   Successful pages: {len(gemini_times)}")
    if gemini_times:
        print(f"   Total time: {total_gemini_time:.2f}s ({total_gemini_time/60:.2f} minutes)")
        print(f"   Average time per page: {avg_gemini_time:.2f}s")
        print(f"   Total cost: ${total_gemini_cost:.4f}")
        print(f"   Average cost per page: ${avg_gemini_cost:.4f}")
        print(f"   Total input tokens: {sum(gemini_input_tokens):,}")
        print(f"   Total output tokens: {sum(gemini_output_tokens):,}")
        print(f"   Average input tokens: {sum(gemini_input_tokens)/len(gemini_times):.0f}")
        print(f"   Average output tokens: {sum(gemini_output_tokens)/len(gemini_times):.0f}")
        print(f"   Validation errors: {len(gemini_validation_errors)}/{len(gemini_times)} ({len(gemini_validation_errors)/len(gemini_times)*100:.1f}%)")
        print(f"   Aportacion corrected: {gemini_aportacion_corrected_count}/{len(gemini_times)} ({gemini_aportacion_corrected_count/len(gemini_times)*100:.1f}%)")
    
    print(f"\n🟢 OPENAI ({openai_parser.model}):")
    print(f"   Successful pages: {len(openai_times)}")
    if openai_times:
        print(f"   Total time: {total_openai_time:.2f}s ({total_openai_time/60:.2f} minutes)")
        print(f"   Average time per page: {avg_openai_time:.2f}s")
        print(f"   Total cost: ${total_openai_cost:.4f}")
        print(f"   Average cost per page: ${avg_openai_cost:.4f}")
        print(f"   Total input tokens: {sum(openai_input_tokens):,}")
        print(f"   Total output tokens: {sum(openai_output_tokens):,}")
        print(f"   Average input tokens: {sum(openai_input_tokens)/len(openai_times):.0f}")
        print(f"   Average output tokens: {sum(openai_output_tokens)/len(openai_times):.0f}")
        print(f"   Validation errors: {len(openai_validation_errors)}/{len(openai_times)} ({len(openai_validation_errors)/len(openai_times)*100:.1f}%)")
        print(f"   Aportacion corrected: {openai_aportacion_corrected_count}/{len(openai_times)} ({openai_aportacion_corrected_count/len(openai_times)*100:.1f}%)")
    
    print("\n" + "=" * 80)
    print(f"EXTRAPOLATION TO {EXTRAPOLATION_TARGET:,} DOCUMENTS")
    print("=" * 80)
    
    if gemini_times:
        print("\n🔵 GEMINI:")
        print(f"   Estimated total time: {extrapolated_gemini_time:.2f}s ({extrapolated_gemini_time/3600:.2f} hours)")
        print(f"   Estimated total cost: ${extrapolated_gemini_cost:.2f}")
    
    if openai_times:
        print("\n🟢 OPENAI:")
        print(f"   Estimated total time: {extrapolated_openai_time:.2f}s ({extrapolated_openai_time/3600:.2f} hours)")
        print(f"   Estimated total cost: ${extrapolated_openai_cost:.2f}")
    
    if gemini_times and openai_times:
        time_diff = extrapolated_openai_time - extrapolated_gemini_time
        cost_diff = extrapolated_openai_cost - extrapolated_gemini_cost
        print("\n📊 COMPARISON:")
        print(f"   Time difference: {abs(time_diff):.2f}s ({'OpenAI' if time_diff < 0 else 'Gemini'} is faster)")
        print(f"   Cost difference: ${abs(cost_diff):.2f} ({'OpenAI' if cost_diff < 0 else 'Gemini'} is cheaper)")
    
    print(f"\n📁 Comparison logs saved to: {output_dir}")
    
    # Save summary JSON with metrics
    summary_data = {
        "timestamp": datetime.now().isoformat(),
        "total_pdfs": len(all_results),
        "total_pages": total_pages,
        "total_differences": total_differences,
        "metrics": {
            "gemini": {
                "model": gemini_parser.model,
                "successful_pages": len(gemini_times),
                "total_time_seconds": total_gemini_time,
                "average_time_seconds": avg_gemini_time,
                "total_cost_usd": total_gemini_cost,
                "average_cost_usd": avg_gemini_cost,
                "total_input_tokens": sum(gemini_input_tokens),
                "total_output_tokens": sum(gemini_output_tokens),
                "average_input_tokens": sum(gemini_input_tokens)/len(gemini_times) if gemini_times else 0,
                "average_output_tokens": sum(gemini_output_tokens)/len(gemini_times) if gemini_times else 0,
                "validation_errors_count": len(gemini_validation_errors),
                "validation_errors_percentage": len(gemini_validation_errors)/len(gemini_times)*100 if gemini_times else 0,
                "aportacion_corrected_count": gemini_aportacion_corrected_count,
                "aportacion_corrected_percentage": gemini_aportacion_corrected_count/len(gemini_times)*100 if gemini_times else 0,
            },
            "openai": {
                "model": openai_parser.model,
                "successful_pages": len(openai_times),
                "total_time_seconds": total_openai_time,
                "average_time_seconds": avg_openai_time,
                "total_cost_usd": total_openai_cost,
                "average_cost_usd": avg_openai_cost,
                "total_input_tokens": sum(openai_input_tokens),
                "total_output_tokens": sum(openai_output_tokens),
                "average_input_tokens": sum(openai_input_tokens)/len(openai_times) if openai_times else 0,
                "average_output_tokens": sum(openai_output_tokens)/len(openai_times) if openai_times else 0,
                "validation_errors_count": len(openai_validation_errors),
                "validation_errors_percentage": len(openai_validation_errors)/len(openai_times)*100 if openai_times else 0,
                "aportacion_corrected_count": openai_aportacion_corrected_count,
                "aportacion_corrected_percentage": openai_aportacion_corrected_count/len(openai_times)*100 if openai_times else 0,
            },
            "extrapolation": {
                "target_documents": EXTRAPOLATION_TARGET,
                "gemini": {
                    "estimated_time_seconds": extrapolated_gemini_time,
                    "estimated_time_hours": extrapolated_gemini_time / 3600,
                    "estimated_cost_usd": extrapolated_gemini_cost,
                },
                "openai": {
                    "estimated_time_seconds": extrapolated_openai_time,
                    "estimated_time_hours": extrapolated_openai_time / 3600,
                    "estimated_cost_usd": extrapolated_openai_cost,
                }
            }
        },
        "results": all_results
    }
    
    summary_path = output_dir / f"summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(summary_data, f, indent=2, ensure_ascii=False)
    print(f"📊 Summary saved to: {summary_path.name}")


if __name__ == "__main__":
    main()

