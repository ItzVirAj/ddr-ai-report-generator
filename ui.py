# ui.py

import streamlit as st
import os
import tempfile
from pathlib import Path

from src.extractor import extract_from_pdf
from src.analyzer import DDRAnalyzer                        # FIXED name
from src.image_mapper import map_images_to_observations     # ADDED
from src.report_builder import build_html_report
from src.utils import save_json, make_sure_folder_exists


# ---------------------------------------------------------
# PAGE CONFIG
# ---------------------------------------------------------

st.set_page_config(
    page_title="DDR Report Generator",
    page_icon="📋",
    layout="wide"
)

st.title("📋 Detailed Diagnostic Report Generator")

st.write(
    "Upload an **Inspection Report** and a **Thermal Report** "
    "to automatically generate a Detailed Diagnostic Report (DDR)."
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
        "📄 Upload Inspection Report (PDF)",
        type=["pdf"]
    )

with col2:
    thermal_file = st.file_uploader(
        "🌡 Upload Thermal Report (PDF)",
        type=["pdf"]
    )


# ---------------------------------------------------------
# RUN BUTTON
# ---------------------------------------------------------

run_button = st.button(
    "🚀 Generate DDR Report",
    type="primary",
    use_container_width=True
)


# ---------------------------------------------------------
# PIPELINE EXECUTION
# ---------------------------------------------------------

if run_button:

    if inspection_file is None or thermal_file is None:
        st.error("Please upload both the inspection and thermal reports.")
        st.stop()

    try:

        # -------------------------------------------------
        # SAVE UPLOADED FILES TO TEMP
        # -------------------------------------------------

        with st.spinner("Preparing uploaded files..."):

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

        with st.spinner("Step 1/4 — Extracting inspection report..."):

            inspection_data = extract_from_pdf(
                pdf_path=inspection_path,
                image_output_folder=IMAGE_DIR,
                doc_label="inspection"
            )

        st.success(
            f"Inspection report extracted — "
            f"{len(inspection_data.get('pages', []))} pages, "
            f"{len(inspection_data.get('images', []))} images"
        )

        # -------------------------------------------------
        # STEP 2 — EXTRACT THERMAL
        # -------------------------------------------------

        with st.spinner("Step 2/4 — Extracting thermal report..."):

            thermal_data = extract_from_pdf(
                pdf_path=thermal_path,
                image_output_folder=IMAGE_DIR,
                doc_label="thermal"
            )

        st.success(
            f"Thermal report extracted — "
            f"{len(thermal_data.get('pages', []))} pages, "
            f"{len(thermal_data.get('images', []))} images"
        )

        # save debug JSON
        save_json(inspection_data, "outputs/debug_inspection_extraction.json")
        save_json(thermal_data, "outputs/debug_thermal_extraction.json")

        # -------------------------------------------------
        # STEP 3 — GEMINI ANALYSIS
        # -------------------------------------------------

        with st.spinner("Step 3/4 — Analyzing reports with Gemini AI..."):

            analyzer = DDRAnalyzer()                        # FIXED name

            result = analyzer.analyze_documents(
                inspection_data.get("full_text", ""),
                thermal_data.get("full_text", "")
            )

        if not result.get("success"):
            st.error("Gemini analysis failed.")
            st.code(result.get("error", "Unknown error"))
            st.stop()

        ddr_data = result.get("ddr", {})

        obs_count = len(ddr_data.get("area_wise_observations", []))

        st.success(
            f"Analysis complete — "
            f"{obs_count} area observations generated"
        )

        save_json(ddr_data, "outputs/debug_ddr_raw.json")

        # -------------------------------------------------
        # STEP 3.5 — IMAGE MAPPING                        # ADDED
        # -------------------------------------------------

        with st.spinner("Mapping images to observations..."):

            ddr_data["area_wise_observations"] = map_images_to_observations(
                observations=ddr_data.get("area_wise_observations", []),
                inspection_images=inspection_data.get("images", []),
                thermal_images=thermal_data.get("images", []),
                inspection_pages=inspection_data.get("pages", []),
                thermal_pages=thermal_data.get("pages", [])
            )

        # -------------------------------------------------
        # STEP 4 — BUILD HTML REPORT
        # -------------------------------------------------

        with st.spinner("Step 4/4 — Building DDR report..."):

            report_path = build_html_report(
                ddr_data=ddr_data,
                inspection_data=inspection_data,
                thermal_data=thermal_data,
                output_path="outputs/ddr_report.html"
            )

        st.success("✅ DDR Report Generated Successfully!")

        st.divider()

        # -------------------------------------------------
        # DDR SUMMARY STATS
        # -------------------------------------------------

        severity = ddr_data.get(
            "severity_assessment", {}
        ).get("level", "Unknown")

        root_causes = len(ddr_data.get("probable_root_cause", []))
        actions = len(ddr_data.get("recommended_actions", []))

        m1, m2, m3, m4 = st.columns(4)

        m1.metric("Areas Observed", obs_count)
        m2.metric("Severity Level", severity)
        m3.metric("Root Causes", root_causes)
        m4.metric("Recommended Actions", actions)

        st.divider()

        # -------------------------------------------------
        # REPORT PREVIEW
        # -------------------------------------------------

        st.subheader("📄 Report Preview")

        st.info(
            "Images may not display in the preview below due to "
            "browser security restrictions. Download the report "
            "and open it locally to see all images."
        )

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
                label="⬇ Download DDR Report (HTML)",
                data=f,
                file_name="ddr_report.html",
                mime="text/html",
                use_container_width=True
            )

    except Exception as e:

        st.error("An unexpected error occurred.")
        st.code(str(e))