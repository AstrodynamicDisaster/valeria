#!/usr/bin/env python3
"""
Test script for progress bar functionality
"""

import time
from tqdm import tqdm

def simulate_nomina_processing():
    """Simulate the nomina processing with progress bar"""

    # Simulate a list of PDF files
    pdf_files = [
        "FRANCISCO_LEON_RUIZ_12400924Z_2025_01.pdf",
        "FRANCISCO_LEON_RUIZ_12400924Z_2025_02.pdf",
        "RAFAEL_RUIZ_MUÑOZ_40670920C_2025_01.pdf",
        "RAFAEL_RUIZ_MUÑOZ_40670920C_2025_02.pdf",
        "ANDREA_SANCHEZ_SANCHEZ_88469776T_2025_01.pdf"
    ]

    total_files = len(pdf_files)
    start_time = time.time()
    processed_count = 0
    failed_count = 0

    print(f"🔄 Processing {total_files} nomina PDF files...")

    # Create progress bar just like in the agent
    with tqdm(total=total_files, desc="Processing nominas", unit="file") as pbar:
        for i, pdf_file in enumerate(pdf_files):
            # Update progress bar with current file
            pbar.set_description(f"Processing {pdf_file[:20]}...")

            # Simulate processing time
            time.sleep(0.5)  # Simulate actual processing

            # Simulate success/failure
            if i == 2:  # Simulate one failure
                failed_count += 1
            else:
                processed_count += 1

            # Calculate time estimation
            elapsed_time = time.time() - start_time
            files_done = i + 1

            if files_done > 0:
                avg_time_per_file = elapsed_time / files_done
                remaining_files = total_files - files_done
                estimated_remaining = avg_time_per_file * remaining_files

                # Update progress bar with ETA
                pbar.set_postfix({
                    'processed': processed_count,
                    'failed': failed_count,
                    'ETA': f"{estimated_remaining:.1f}s"
                })

            pbar.update(1)

    # Final summary
    total_time = time.time() - start_time
    avg_time_per_file = total_time / total_files

    print(f"\n✅ Processing completed!")
    print(f"   📊 Processed: {processed_count}/{total_files} payslips")
    print(f"   ⏱️  Total time: {total_time:.1f}s (avg: {avg_time_per_file:.1f}s per file)")
    if failed_count > 0:
        print(f"   ⚠️  Failed: {failed_count} files")

if __name__ == "__main__":
    print("🧪 Testing Progress Bar for Nomina Processing")
    print("=" * 50)
    simulate_nomina_processing()
    print("\n🎉 Progress bar test completed!")