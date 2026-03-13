# main.py

import argparse
import os
import sys
from dotenv import load_dotenv

load_dotenv()

from src.extractor import extract_from_pdf
from src.analyzer import DDRAnalyzer
from src.report_builder import build_html_report, build_pdf_report
from src.utils import save_json, make_sure_folder_exists
from src.image_mapper import map_images_to_observations


def parse_args():

    _parser = argparse.ArgumentParser(
        description="DDR Report Generator"
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
        help="Where to save the final DDR report"
    )

    _parser.add_argument(
        "--pdf",
        action="store_true",
        help="Also generate a PDF version of the report"
    )

    return _parser.parse_args()


def check_files_exist(inspection_path, thermal_path):

    _missing = []

    if not os.path.exists(inspection_path):
        _missing.append(f"Inspection PDF not found: {inspection_path}")

    if not os.path.exists(thermal_path):
        _missing.append(f"Thermal PDF not found: {thermal_path}")

    if _missing:
        print("\n[error] Missing input files:\n")
        for _m in _missing:
            print(" -", _m)
        print("\nPlease place your PDFs inside the inputs/ folder.\n")
        sys.exit(1)


def main():

    print("\n=== DDR Report Generator ===\n")

    _args = parse_args()

    check_files_exist(_args.inspection, _args.thermal)

    make_sure_folder_exists("outputs")

    _image_folder = "outputs/extracted_images"
    make_sure_folder_exists(_image_folder)

    analyzer = DDRAnalyzer()

    # ---------------------------------------------------
    # STEP 1 — INSPECTION EXTRACTION
    # ---------------------------------------------------

    print("[step 1/5] Extracting inspection report ...")

    _inspection_data = extract_from_pdf(
        pdf_path=_args.inspection,
        image_output_folder=_image_folder,
        doc_label="inspection"
    )

    # ---------------------------------------------------
    # STEP 2 — THERMAL EXTRACTION
    # ---------------------------------------------------

    print("\n[step 2/5] Extracting thermal report ...")

    _thermal_data = extract_from_pdf(
        pdf_path=_args.thermal,
        image_output_folder=_image_folder,
        doc_label="thermal"
    )

    save_json(_inspection_data, "outputs/debug_inspection_extraction.json")
    save_json(_thermal_data, "outputs/debug_thermal_extraction.json")

    print("\n[debug] Extraction JSON saved to outputs/")

    # ---------------------------------------------------
    # STEP 3 — GEMINI ANALYSIS
    # ---------------------------------------------------

    print("\n[step 3/5] Analyzing reports with Gemini...")

    result = analyzer.analyze_documents(
        inspection_text=_inspection_data.get("full_text", ""),
        thermal_text=_thermal_data.get("full_text", ""),
        inspection_images=_inspection_data.get("images", []),
        thermal_images=_thermal_data.get("images", [])
    )

    if not result.get("success"):
        print("\n[error] Analyzer failed:\n")
        print(result.get("error", "Unknown error"))
        sys.exit(1)

    _ddr_data = result.get("ddr", {})

    save_json(_ddr_data, "outputs/debug_ddr_raw.json")

    print("[debug] Raw DDR JSON saved to outputs/debug_ddr_raw.json")

    # ---------------------------------------------------
    # STEP 4 — IMAGE MAPPING
    # ---------------------------------------------------

    print("\n[step 4/5] Mapping images to observations ...")

    _ddr_data["area_wise_observations"] = map_images_to_observations(
        observations=_ddr_data.get("area_wise_observations", []),
        inspection_images=_inspection_data.get("images", []),
        thermal_images=_thermal_data.get("images", []),
        inspection_pages=_inspection_data.get("pages", []),
        thermal_pages=_thermal_data.get("pages", [])
    )

    # ---------------------------------------------------
    # STEP 5 — BUILD REPORTS
    # ---------------------------------------------------

    print("\n[step 5/5] Building reports ...")

    _report_path = build_html_report(
        ddr_data=_ddr_data,
        inspection_data=_inspection_data,
        thermal_data=_thermal_data,
        output_path=_args.output
    )

    print("\n✓ HTML Report Generated:")
    print(os.path.abspath(_report_path))

    if _args.pdf:

        _pdf_path = _args.output.replace(".html", ".pdf")

        try:
            _pdf_report_path = build_pdf_report(
                ddr_data=_ddr_data,
                inspection_data=_inspection_data,
                thermal_data=_thermal_data,
                output_path=_pdf_path
            )
            print("\n✓ PDF Report Generated:")
            print(os.path.abspath(_pdf_report_path))

        except Exception as e:
            print(f"\n[warning] PDF generation failed: {e}")
            print("Run: pip install xhtml2pdf")

    print()


if __name__ == "__main__":
    main()