# src/utils.py

import os
import json
from pathlib import Path


def make_sure_folder_exists(folder_path):
    """
    Just makes sure a folder is there before we try to write into it.
    Nothing fancy — avoids FileNotFoundError surprises later.
    """
    Path(folder_path).mkdir(parents=True, exist_ok=True)


def save_json(data, file_path):
    """
    Saves a dict as a pretty-printed JSON file.
    Useful for debugging — we can see exactly what got extracted
    before sending it to the LLM.
    """
    with open(file_path, "w", encoding="utf-8") as _f:
        json.dump(data, _f, indent=2, ensure_ascii=False)


def load_json(file_path):
    """
    Loads a JSON file back into a Python dict.
    """
    with open(file_path, "r", encoding="utf-8") as _f:
        return json.load(_f)


def clean_text(raw_text):
    """
    PDFs often have weird whitespace, line breaks in odd places,
    and repeated blank lines. This cleans that up a bit before
    we send it to the LLM.
    """
    _lines = raw_text.split("\n")
    _cleaned = []

    for _line in _lines:
        _stripped = _line.strip()
        if _stripped:
            _cleaned.append(_stripped)

    # rejoin with single newlines
    return "\n".join(_cleaned)


def get_file_stem(file_path):
    """
    Returns just the filename without extension.
    e.g. 'inputs/inspection_report.pdf' → 'inspection_report'
    """
    return Path(file_path).stem