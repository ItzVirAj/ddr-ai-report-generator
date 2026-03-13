# src/report_builder.py

import os
from datetime import datetime
from jinja2 import Environment, FileSystemLoader
from src.utils import make_sure_folder_exists


def _build_image_map(inspection_data, thermal_data):
    """
    Build dict of {image_id: absolute_file_path}
    so the HTML template can load images correctly.
    """

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


def _normalize_ddr(ddr_data):
    """
    Normalize DDR structure so the template never breaks.
    """

    if not isinstance(ddr_data, dict):
        return {}

    # analyzer may return {"success":True,"ddr":{...}}
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


def build_html_report(
        ddr_data,
        inspection_data,
        thermal_data,
        output_path,
        templates_dir="templates"
):
    """
    Render the DDR HTML report using Jinja2 template.
    """

    # ensure output directory exists
    output_dir = os.path.dirname(output_path)

    if output_dir:
        make_sure_folder_exists(output_dir)

    # normalize DDR structure
    ddr_data = _normalize_ddr(ddr_data)

    # build image lookup table
    _image_map = _build_image_map(inspection_data, thermal_data)

    # setup Jinja2 environment
    _env = Environment(
        loader=FileSystemLoader(templates_dir),
        autoescape=True
    )

    try:
        _template = _env.get_template("ddr_template.html")
    except Exception as e:
        raise RuntimeError(f"Template load failed: {e}")

    # generate timestamp
    _generated_date = datetime.now().strftime("%B %d, %Y at %I:%M %p")

    # render HTML
    _rendered_html = _template.render(
        ddr=ddr_data,
        image_map=_image_map,
        generated_date=_generated_date
    )

    # write file
    with open(output_path, "w", encoding="utf-8") as _out_file:
        _out_file.write(_rendered_html)

    print(f"[report_builder] HTML report saved to: {output_path}")

    return output_path