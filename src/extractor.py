# src/extractor.py

import os
import fitz          # this is pymupdf — the import name is fitz
from PIL import Image
import io
from src.utils import clean_text, make_sure_folder_exists


def extract_from_pdf(pdf_path, image_output_folder, doc_label):
    """
    Opens a PDF and pulls out:
      - All the text, page by page
      - All embedded images, saved as files

    Returns a dict like:
    {
        "label": "inspection",
        "full_text": "...",
        "pages": [
            {"page_num": 1, "text": "..."},
            ...
        ],
        "images": [
            {"image_id": "inspection_p1_img0", "file_path": "outputs/..."},
            ...
        ]
    }
    """
    make_sure_folder_exists(image_output_folder)

    _result = {
        "label": doc_label,
        "full_text": "",
        "pages": [],
        "images": []
    }

    _all_text_parts = []

    # open the PDF
    _doc = fitz.open(pdf_path)

    for _page_index in range(len(_doc)):
        _page = _doc[_page_index]
        _page_num = _page_index + 1

        # --- extract text from this page ---
        _raw_text = _page.get_text("text")
        _page_text = clean_text(_raw_text)
        _all_text_parts.append(f"[Page {_page_num}]\n{_page_text}")

        _result["pages"].append({
            "page_num": _page_num,
            "text": _page_text
        })

        # --- extract images from this page ---
        _image_list = _page.get_images(full=True)

        for _img_index, _img_ref in enumerate(_image_list):
            _xref = _img_ref[0]   # xref is the image reference id in pymupdf

            try:
                _base_image = _doc.extract_image(_xref)
                _image_bytes = _base_image["image"]
                _image_ext = _base_image["ext"]   # usually png or jpeg

                # build a meaningful filename
                _image_id = f"{doc_label}_p{_page_num}_img{_img_index}"
                _image_filename = f"{_image_id}.{_image_ext}"
                _image_save_path = os.path.join(image_output_folder, _image_filename)

                # save the image to disk
                _img_obj = Image.open(io.BytesIO(_image_bytes))

                # skip tiny images — they're usually decorative borders or icons
                _width, _height = _img_obj.size
                if _width < 50 or _height < 50:
                    continue

                _img_obj.save(_image_save_path)

                _result["images"].append({
                    "image_id": _image_id,
                    "file_path": _image_save_path,
                    "page_num": _page_num,
                    "width": _width,
                    "height": _height
                })

            except Exception as _err:
                # some embedded objects aren't real images — just skip them
                print(f"  [skip] could not extract image {_xref} on page {_page_num}: {_err}")
                continue

    _doc.close()

    _result["full_text"] = "\n\n".join(_all_text_parts)

    _total_images = len(_result["images"])
    _total_pages = len(_result["pages"])
    print(f"[extractor] {doc_label}: {_total_pages} pages, {_total_images} images extracted")

    return _result