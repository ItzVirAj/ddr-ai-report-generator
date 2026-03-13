# src/utils.py

import os
import json
from pathlib import Path


def make_sure_folder_exists(folder_path: str) -> None:
    """
    Ensure a folder exists before writing files into it.
    """

    if not folder_path:
        return

    Path(folder_path).mkdir(parents=True, exist_ok=True)


def save_json(data, file_path: str) -> None:
    """
    Save a dict as pretty JSON for debugging or storage.
    Automatically creates parent folder if needed.
    """

    parent = os.path.dirname(file_path)

    if parent:
        make_sure_folder_exists(parent)

    with open(file_path, "w", encoding="utf-8") as _f:
        json.dump(data, _f, indent=2, ensure_ascii=False)


def load_json(file_path: str) -> dict:
    """
    Load a JSON file safely.
    """

    if not os.path.exists(file_path):
        raise FileNotFoundError(f"JSON file not found: {file_path}")

    with open(file_path, "r", encoding="utf-8") as _f:
        return json.load(_f)


def clean_text(raw_text: str) -> str:
    """
    Clean messy PDF text.

    Fixes:
    - random whitespace
    - tab characters
    - empty lines
    """

    if not raw_text:
        return ""

    _lines = raw_text.split("\n")
    _cleaned = []

    for _line in _lines:

        _stripped = _line.strip()

        if not _stripped:
            continue

        _stripped = _stripped.replace("\t", " ")
        _cleaned.append(_stripped)

    return "\n".join(_cleaned)


def get_file_stem(file_path: str) -> str:
    """
    Returns filename without extension.

    Example:
    inputs/inspection_report.pdf → inspection_report
    """

    return Path(file_path).stem