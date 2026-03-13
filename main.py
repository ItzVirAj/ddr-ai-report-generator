import argparse
import os
import sys
from dotenv import load_dotenv

# load .env before anything else
load_dotenv()

from src.extractor import extract_from_pdf
from src.analyzer import DDRAnalyzer
from src.report_builder import build_html_report
from src.utils import save_json, make_sure_folder_exists
from src.image_mapper import map_images_to_observations

def parse_args():
    """
    CLI arguments so we can run:

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
        help="Where to save the final DDR report"
    )

    return _parser.parse_args()


def check_files_exist(inspection_path, thermal_path):
    """
    Fail early if inputs are missing.
    """

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

    # ensure outputs directory exists
    make_sure_folder_exists("outputs")

    _image_folder = "outputs/extracted_images"
    make_sure_folder_exists(_image_folder)

    # initialize analyzer
    analyzer = DDRAnalyzer()

    # ---------------------------------------------------
    # STEP 1 — INSPECTION EXTRACTION
    # ---------------------------------------------------

    print("[step 1/4] Extracting inspection report ...")

    _inspection_data = extract_from_pdf(
        pdf_path=_args.inspection,
        image_output_folder=_image_folder,
        doc_label="inspection"
    )

    # ---------------------------------------------------
    # STEP 2 — THERMAL EXTRACTION
    # ---------------------------------------------------

    print("\n[step 2/4] Extracting thermal report ...")

    _thermal_data = extract_from_pdf(
        pdf_path=_args.thermal,
        image_output_folder=_image_folder,
        doc_label="thermal"
    )

    # save extraction debug
    save_json(_inspection_data, "outputs/debug_inspection_extraction.json")
    save_json(_thermal_data, "outputs/debug_thermal_extraction.json")

    print("\n[debug] Extraction JSON saved to outputs/")

    # ---------------------------------------------------
    # STEP 3 — GEMINI ANALYSIS
    # ---------------------------------------------------

    print("\n[step 3/4] Analyzing reports with Gemini...")

    result = analyzer.analyze_documents(
        _inspection_data.get("full_text", ""),
        _thermal_data.get("full_text", "")
    )

    if not result.get("success"):

        print("\n[error] Analyzer failed:\n")

        print(result.get("error", "Unknown error"))

        sys.exit(1)

    _ddr_data = result.get("ddr", {})

    save_json(_ddr_data, "outputs/debug_ddr_raw.json")

    print("[debug] Raw DDR JSON saved to outputs/debug_ddr_raw.json")

    # ---------------------------------------------------
    # STEP 4 — HTML REPORT
    # ---------------------------------------------------

    print("\n[step 4/4] Building HTML report ...")

    # FIXED: pass pages so keyword matching works
    _ddr_data["area_wise_observations"] = map_images_to_observations(
        observations=_ddr_data.get("area_wise_observations", []),
        inspection_images=_inspection_data.get("images", []),
        thermal_images=_thermal_data.get("images", []),
        inspection_pages=_inspection_data.get("pages", []),   # NEW
        thermal_pages=_thermal_data.get("pages", [])          # NEW
    )

    _report_path = build_html_report(
        ddr_data=_ddr_data,
        inspection_data=_inspection_data,
        thermal_data=_thermal_data,
        output_path=_args.output
    )

    print("\n✓ DDR Report Generated Successfully!\n")
    print("Open the report here:\n")
    print(os.path.abspath(_report_path))
    print()


if __name__ == "__main__":
    main()