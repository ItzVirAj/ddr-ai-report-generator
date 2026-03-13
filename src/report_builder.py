# src/report_builder.py

import os
import base64
from datetime import datetime
from jinja2 import Environment, FileSystemLoader
from src.utils import make_sure_folder_exists


def _build_image_map(inspection_data, thermal_data):

    _image_map = {}
    _all_images = []

    if inspection_data and "images" in inspection_data:
        _all_images.extend(inspection_data["images"])

    if thermal_data and "images" in thermal_data:
        _all_images.extend(thermal_data["images"])

    for _img_info in _all_images:

        _img_id = _img_info.get("image_id")
        _raw_path = _img_info.get("file_path")

        if not _img_id or not _raw_path:
            continue

        try:
            _abs_path = os.path.abspath(_raw_path)
            _image_map[_img_id] = _abs_path
        except Exception:
            continue

    return _image_map


def _embed_images_as_base64(image_map: dict) -> dict:
    """
    Convert image paths to base64 data URIs.
    Ensures images render correctly in PDF on all platforms.
    """

    embedded = {}

    for img_id, img_path in image_map.items():

        try:
            if not os.path.exists(img_path):
                continue

            with open(img_path, "rb") as img_file:
                img_bytes = img_file.read()

            ext = os.path.splitext(img_path)[1].lower()

            mime_map = {
                ".jpg":  "image/jpeg",
                ".jpeg": "image/jpeg",
                ".png":  "image/png",
                ".gif":  "image/gif",
                ".webp": "image/webp",
            }

            mime_type = mime_map.get(ext, "image/png")

            b64 = base64.b64encode(img_bytes).decode("utf-8")

            embedded[img_id] = f"data:{mime_type};base64,{b64}"

        except Exception:
            continue

    return embedded


def _normalize_ddr(ddr_data):

    if not isinstance(ddr_data, dict):
        return {}

    if "ddr" in ddr_data:
        ddr_data = ddr_data["ddr"]

    ddr_data.setdefault("property_issue_summary", "Not Available")
    ddr_data.setdefault("area_wise_observations", [])
    ddr_data.setdefault("probable_root_cause", [])
    ddr_data.setdefault("severity_assessment", {
        "level": "Medium",
        "reasoning": "Not Available"
    })
    ddr_data.setdefault("recommended_actions", [])
    ddr_data.setdefault("additional_notes", "Not Available")
    ddr_data.setdefault("missing_or_unclear_information", "None reported.")

    return ddr_data


def _render_html(
    ddr_data,
    inspection_data,
    thermal_data,
    templates_dir="templates",
    for_pdf=False
):

    ddr_data = _normalize_ddr(ddr_data)

    _image_map = _build_image_map(inspection_data, thermal_data)

    # embed as base64 for PDF
    if for_pdf:
        _image_map = _embed_images_as_base64(_image_map)

    _env = Environment(
        loader=FileSystemLoader(templates_dir),
        autoescape=True
    )

    try:
        _template = _env.get_template("ddr_template.html")
    except Exception as e:
        raise RuntimeError(f"Template load failed: {e}")

    _generated_date = datetime.now().strftime("%B %d, %Y at %I:%M %p")

    return _template.render(
        ddr=ddr_data,
        image_map=_image_map,
        generated_date=_generated_date
    )


def build_html_report(
    ddr_data,
    inspection_data,
    thermal_data,
    output_path,
    templates_dir="templates"
):

    output_dir = os.path.dirname(output_path)

    if output_dir:
        make_sure_folder_exists(output_dir)

    rendered_html = _render_html(
        ddr_data=ddr_data,
        inspection_data=inspection_data,
        thermal_data=thermal_data,
        templates_dir=templates_dir,
        for_pdf=False
    )

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(rendered_html)

    print(f"[report_builder] HTML report saved to: {output_path}")

    return output_path


def build_pdf_report(
    ddr_data,
    inspection_data,
    thermal_data,
    output_path,
    templates_dir="templates"
):

    try:
        from xhtml2pdf import pisa
    except ImportError:
        raise RuntimeError(
            "xhtml2pdf not installed. Run: pip install xhtml2pdf"
        )

    output_dir = os.path.dirname(output_path)

    if output_dir:
        make_sure_folder_exists(output_dir)

    rendered_html = _render_html(
        ddr_data=ddr_data,
        inspection_data=inspection_data,
        thermal_data=thermal_data,
        templates_dir=templates_dir,
        for_pdf=True
    )

    with open(output_path, "wb") as pdf_file:

        pisa_status = pisa.CreatePDF(
            src=rendered_html,
            dest=pdf_file,
            encoding="utf-8"
        )

    if pisa_status.err:
        raise RuntimeError(
            f"PDF generation failed with {pisa_status.err} errors"
        )

    print(f"[report_builder] PDF report saved to: {output_path}")

    return output_path