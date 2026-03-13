# ui.py

import streamlit as st
import os
import tempfile
from pathlib import Path

from src.extractor import extract_from_pdf
from src.analyzer import CodeAnalyzer
from src.report_builder import build_html_report
from src.utils import save_json, make_sure_folder_exists


# ---------------------------------------------------------
# PAGE CONFIG
# ---------------------------------------------------------

st.set_page_config(
    page_title="DDR Report Generator",
    page_icon="📊",
    layout="wide"
)

st.title("📊 Detailed Diagnostic Report Generator")
st.write(
    "Upload an **Inspection Report** and a **Thermal Report** to automatically generate a "
    "Detailed Diagnostic Report (DDR)."
)

st.divider()


# ---------------------------------------------------------
# SETUP OUTPUT FOLDERS
# ---------------------------------------------------------

OUTPUT_DIR = "outputs"
IMAGE_DIR = "outputs/extracted_images"

make_sure_folder_exists(OUTPUT_DIR)
make_sure_folder_exists(IMAGE_DIR)


# ---------------------------------------------------------
# FILE UPLOAD SECTION
# ---------------------------------------------------------

col1, col2 = st.columns(2)

with col1:
    inspection_file = st.file_uploader(
        "Upload Inspection Report (PDF)",
        type=["pdf"]
    )

with col2:
    thermal_file = st.file_uploader(
        "Upload Thermal Report (PDF)",
        type=["pdf"]
    )


# ---------------------------------------------------------
# RUN BUTTON
# ---------------------------------------------------------

run_button = st.button("🚀 Generate DDR Report", type="primary")


# ---------------------------------------------------------
# PIPELINE EXECUTION
# ---------------------------------------------------------

if run_button:

    if inspection_file is None or thermal_file is None:
        st.error("Please upload both inspection and thermal reports.")
        st.stop()

    try:

        with st.spinner("Preparing files..."):

            # Save uploaded PDFs to temp files
            temp_dir = tempfile.mkdtemp()

            inspection_path = os.path.join(temp_dir, inspection_file.name)
            thermal_path = os.path.join(temp_dir, thermal_file.name)

            with open(inspection_path, "wb") as f:
                f.write(inspection_file.read())

            with open(thermal_path, "wb") as f:
                f.write(thermal_file.read())

        # -------------------------------------------------
        # STEP 1 — EXTRACT INSPECTION
        # -------------------------------------------------

        st.info("Step 1/4 — Extracting inspection report")

        inspection_data = extract_from_pdf(
            pdf_path=inspection_path,
            image_output_folder=IMAGE_DIR,
            doc_label="inspection"
        )

        # -------------------------------------------------
        # STEP 2 — EXTRACT THERMAL
        # -------------------------------------------------

        st.info("Step 2/4 — Extracting thermal report")

        thermal_data = extract_from_pdf(
            pdf_path=thermal_path,
            image_output_folder=IMAGE_DIR,
            doc_label="thermal"
        )

        # Save debug JSON
        save_json(inspection_data, "outputs/debug_inspection_extraction.json")
        save_json(thermal_data, "outputs/debug_thermal_extraction.json")

        # -------------------------------------------------
        # STEP 3 — GEMINI ANALYSIS
        # -------------------------------------------------

        st.info("Step 3/4 — Analyzing reports with Gemini")

        analyzer = CodeAnalyzer()

        result = analyzer.analyze_documents(
            inspection_data.get("full_text", ""),
            thermal_data.get("full_text", "")
        )

        if not result.get("success"):
            st.error("Analyzer failed")
            st.code(result.get("error", "Unknown error"))
            st.stop()

        ddr_data = result.get("ddr", {})

        save_json(ddr_data, "outputs/debug_ddr_raw.json")

        # -------------------------------------------------
        # STEP 4 — BUILD HTML REPORT
        # -------------------------------------------------

        st.info("Step 4/4 — Building DDR report")

        report_path = build_html_report(
            ddr_data=ddr_data,
            inspection_data=inspection_data,
            thermal_data=thermal_data,
            output_path="outputs/ddr_report.html"
        )

        # -------------------------------------------------
        # SUCCESS
        # -------------------------------------------------

        st.success("DDR report generated successfully!")

        # -------------------------------------------------
        # REPORT PREVIEW
        # -------------------------------------------------

        st.subheader("📄 Report Preview")

        with open(report_path, "r", encoding="utf-8") as f:
            html_content = f.read()

        st.components.v1.html(
            html_content,
            height=900,
            scrolling=True
        )

        # -------------------------------------------------
        # DOWNLOAD BUTTON
        # -------------------------------------------------

        with open(report_path, "rb") as f:
            st.download_button(
                label="⬇ Download DDR Report",
                data=f,
                file_name="ddr_report.html",
                mime="text/html"
            )

    except Exception as e:

        st.error("Unexpected error occurred")
        st.code(str(e))