# src/area_detection.py

import re
from typing import List, Dict


# ---------------------------------------------------------
# Known building areas
# ---------------------------------------------------------

KNOWN_AREAS = [
    "hall",
    "living room",
    "bedroom",
    "master bedroom",
    "kitchen",
    "bathroom",
    "common bathroom",
    "toilet",
    "wc",
    "balcony",
    "parking",
    "parking area",
    "external wall",
    "ceiling",
    "wall",
    "floor",
    "terrace",
    "roof"
]


# ---------------------------------------------------------
# Detect area from a sentence
# ---------------------------------------------------------

def detect_area(sentence: str) -> str:
    """
    Detect building area mentioned in sentence.
    """

    s = sentence.lower()

    for area in KNOWN_AREAS:

        if area in s:
            return area.title()

    return "General Area"


# ---------------------------------------------------------
# Convert observation sentences → structured observations
# ---------------------------------------------------------

def build_area_observations(sentences: List[str]) -> List[Dict]:
    """
    Convert raw sentences into structured area observations.
    """

    observations = []

    for s in sentences:

        area = detect_area(s)

        observations.append({
            "area": area,
            "observation": s,
            "source": "inspection",
            "related_image_ids": []
        })

    return observations


# ---------------------------------------------------------
# Merge duplicate observations
# ---------------------------------------------------------

def deduplicate_observations(observations: List[Dict]) -> List[Dict]:
    """
    Remove duplicate observations.
    """

    seen = set()
    cleaned = []

    for obs in observations:

        key = (obs["area"], obs["observation"])

        if key in seen:
            continue

        seen.add(key)
        cleaned.append(obs)

    return cleaned