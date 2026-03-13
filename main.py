# main.py

import argparse
import os
import sys
from dotenv import load_dotenv

# load .env before anything else
load_dotenv()

from src.extractor import extract_from_pdf
from src.analyzer import analyze_documents
from src.report_builder import build_html_report
from src.utils import save_json, make_sure_folder_exists


def parse_args():
    """
    Sets up command-line arguments so we can run this like:
    python main.py --inspection inputs/report.pdf --thermal inputs/thermal.pdf
    """
    _parser = argparse.ArgumentParser(
        description="DDR Report Generator — converts inspection + thermal PDFs into a structured diagnostic report"
    )

    _parser.add_argument(
        "--inspection",
        type=str,
        required=True,
        help="Path to the inspection report PDF"
    )

    _parser.add_argument(
        "--thermal",
        type=str,
        required=True,
        help="Path to the thermal report PDF"
    )

    _parser.add_argument(
        "--output",
        type=str,
        default="outputs/ddr_report.html",
        help="Where to save the final DDR report (default: outputs/ddr_report.html)"
    )

    return _parser.parse_args()


def check_files_exist(inspection_path, thermal_path):
    """
    Simple sanity check before we do anything expensive.
    Better to fail fast with a clear message than crash midway.
    """
    _missing = []

    if not os.path.exists(inspection_path):
        _missing.append(f"  - Inspection PDF not found: {inspection_path}")

    if not os.path.exists(thermal_path):
        _missing.append(f"  - Thermal PDF not found: {thermal_path}")

    if _missing:
        print("\n[error] Missing input files:")
        for _m in _missing:
            print(_m)
        print("\nPlease place your PDFs in the inputs/ folder and try again.")
        sys.exit(1)


def main():
    print("\n=== DDR Report Generator ===\n")

    _args = parse_args()

    # make sure the input files exist
    check_files_exist(_args.inspection, _args.thermal)

    _image_folder = "outputs/extracted_images"
    make_sure_folder_exists(_image_folder)

    # ── Step 1: Extract from inspection PDF ──────────────────────
    print("[step 1/4] Extracting from inspection report ...")
    _inspection_data = extract_from_pdf(
        pdf_path=_args.inspection,
        image_output_folder=_image_folder,
        doc_label="inspection"
    )

    # ── Step 2: Extract from thermal PDF ─────────────────────────
    print("\n[step 2/4] Extracting from thermal report ...")
    _thermal_data = extract_from_pdf(
        pdf_path=_args.thermal,
        image_output_folder=_image_folder,
        doc_label="thermal"
    )

    # save intermediate extraction data for debugging
    save_json(_inspection_data, "outputs/debug_inspection_extraction.json")
    save_json(_thermal_data, "outputs/debug_thermal_extraction.json")
    print("\n[debug] extraction JSON saved to outputs/")

    # ── Step 3: Send to LLM, get structured DDR ──────────────────
    print("\n[step 3/4] Analyzing with GPT-4o ...")
    _ddr_data = analyze_documents(_inspection_data, _thermal_data)

    # save raw DDR JSON too
    save_json(_ddr_data, "outputs/debug_ddr_raw.json")
    print("[debug] raw DDR JSON saved to outputs/debug_ddr_raw.json")

    # ── Step 4: Build the HTML report ────────────────────────────
    print("\n[step 4/4] Building HTML report ...")
    _report_path = build_html_report(
        ddr_data=_ddr_data,
        inspection_data=_inspection_data,
        thermal_data=_thermal_data,
        output_path=_args.output
    )

    print(f"\n✓ Done! Open your report here:\n  {os.path.abspath(_report_path)}\n")


if __name__ == "__main__":
    main()