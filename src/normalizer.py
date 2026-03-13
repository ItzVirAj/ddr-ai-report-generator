# src/normalizer.py

import re


def normalize_document_text(text: str) -> str:
    """
    Clean raw PDF text before sending it to the LLM.

    Removes:
    - headers / footers
    - repeated metadata
    - duplicate lines
    - extra whitespace
    """

    if not text:
        return ""

    lines = text.split("\n")

    cleaned = []
    seen = set()

    for line in lines:

        line = line.strip()

        if not line:
            continue

        # remove page labels
        if line.lower().startswith("[page"):
            continue

        # remove repetitive metadata
        if "confidential" in line.lower():
            continue

        if "inspection date" in line.lower():
            continue

        if "client name" in line.lower():
            continue

        # collapse excessive whitespace
        line = re.sub(r"\s+", " ", line)

        # avoid duplicates
        if line in seen:
            continue

        seen.add(line)
        cleaned.append(line)

    return "\n".join(cleaned)


# ---------------------------------------------------------
# OPTIONAL: extract observation sentences
# ---------------------------------------------------------

def extract_observation_sentences(text: str):
    """
    Try to extract observation-like sentences from document text.
    Useful for guiding the LLM.
    """

    patterns = [
        r"dampness.*",
        r"leakage.*",
        r"crack.*",
        r"seepage.*",
        r"moisture.*",
        r"efflorescence.*",
        r"plumbing.*"
    ]

    observations = []

    for line in text.split("\n"):

        for pattern in patterns:

            if re.search(pattern, line, re.IGNORECASE):
                observations.append(line)
                break

    return observations


# ---------------------------------------------------------
# Build normalized context for LLM
# ---------------------------------------------------------

def build_llm_context(inspection_text: str, thermal_text: str):
    """
    Returns cleaned context for the analyzer.
    """

    inspection_clean = normalize_document_text(inspection_text)
    thermal_clean = normalize_document_text(thermal_text)

    inspection_obs = extract_observation_sentences(inspection_clean)
    thermal_obs = extract_observation_sentences(thermal_clean)

    context = {
        "inspection_clean": inspection_clean,
        "thermal_clean": thermal_clean,
        "inspection_observations": inspection_obs,
        "thermal_observations": thermal_obs
    }

    return context