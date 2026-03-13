# src/report_builder.py

import os
from datetime import datetime
from jinja2 import Environment, FileSystemLoader
from src.utils import make_sure_folder_exists


def _build_image_map(inspection_data, thermal_data):
    """
    The template needs to look up image file paths by image_id.
    We build a simple dict: { image_id: absolute_file_path }
    so the template can do image_map[img_id] to get the src.

    We use absolute paths so the HTML can find images regardless
    of where it's opened from.
    """
    _image_map = {}

    _all_images = inspection_data["images"] + thermal_data["images"]

    for _img_info in _all_images:
        _img_id = _img_info["image_id"]
        _raw_path = _img_info["file_path"]

        # convert to absolute path so img src works in the HTML file
        _abs_path = os.path.abspath(_raw_path)
        _image_map[_img_id] = _abs_path

    return _image_map


def build_html_report(ddr_data, inspection_data, thermal_data, output_path, templates_dir="templates"):
    """
    Takes the DDR JSON data and renders it into a proper HTML report
    using our Jinja2 template.

    Args:
        ddr_data        — the dict returned by analyzer.py
        inspection_data — extraction result from the inspection PDF
        thermal_data    — extraction result from the thermal PDF
        output_path     — where to save the final HTML file
        templates_dir   — folder where ddr_template.html lives
    """
    make_sure_folder_exists(os.path.dirname(output_path))

    # build the image lookup dict
    _image_map = _build_image_map(inspection_data, thermal_data)

    # set up Jinja2 to load from our templates folder
    _env = Environment(
        loader=FileSystemLoader(templates_dir),
        autoescape=True
    )

    _template = _env.get_template("ddr_template.html")

    # format a nice date string
    _generated_date = datetime.now().strftime("%B %d, %Y at %I:%M %p")

    # render the template
    _rendered_html = _template.render(
        ddr=ddr_data,
        image_map=_image_map,
        generated_date=_generated_date
    )

    # write to file
    with open(output_path, "w", encoding="utf-8") as _out_file:
        _out_file.write(_rendered_html)

    print(f"[report_builder] HTML report saved to: {output_path}")
    return output_path