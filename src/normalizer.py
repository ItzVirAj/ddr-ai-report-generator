# src/normalizer.py

import re


def normalize_document_text(text: str) -> str:
    """
    Clean raw PDF text before sending it to the LLM.

    Removes:
    - repeated duplicate lines
    - extra whitespace
    - page label markers

    Keeps:
    - all observation content
    - area names
    - inspection findings
    - thermal readings
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

        # remove internal page markers added by extractor
        if line.lower().startswith("[page"):
            continue

        # remove confidential watermarks
        if "confidential" in line.lower():
            continue

        # collapse excessive whitespace
        line = re.sub(r"\s+", " ", line)

        # avoid duplicate lines
        if line in seen:
            continue

        seen.add(line)
        cleaned.append(line)

    return "\n".join(cleaned)


# ---------------------------------------------------------
# Extract observation sentences
# ---------------------------------------------------------

def extract_observation_sentences(text: str):
    """
    Extract observation-like sentences from document text.

    Covers both inspection keywords and thermal keywords.
    """

    # inspection keywords
    inspection_patterns = [
        r"dampness.*",
        r"leakage.*",
        r"crack.*",
        r"seepage.*",
        r"moisture.*",
        r"efflorescence.*",
        r"plumbing.*",
        r"hollow.*",
        r"tile.*",
        r"ceiling.*",
        r"skirting.*",
        r"parking.*",
        r"outlet.*",
        r"blackish.*",
        r"observed.*",
    ]

    # thermal keywords
    thermal_patterns = [
        r"hotspot.*",
        r"coldspot.*",
        r"thermal.*",
        r"temperature.*",
        r"emissivity.*",
        r"\d+\.\d+\s*°[Cc].*",   # matches temperature readings like 23.4 °C
    ]

    all_patterns = inspection_patterns + thermal_patterns

    observations = []

    for line in text.split("\n"):

        line = line.strip()

        if not line:
            continue

        for pattern in all_patterns:
            if re.search(pattern, line, re.IGNORECASE):
                observations.append(line)
                break

    # limit to avoid overloading prompt
    return observations[:40]


# ---------------------------------------------------------
# Build normalized context for LLM
# ---------------------------------------------------------

def build_llm_context(inspection_text: str, thermal_text: str) -> dict:
    """
    Returns cleaned and structured context for the analyzer.
    """

    inspection_clean = normalize_document_text(inspection_text)
    thermal_clean = normalize_document_text(thermal_text)

    inspection_obs = extract_observation_sentences(inspection_clean)
    thermal_obs = extract_observation_sentences(thermal_clean)

    return {
        "inspection_clean": inspection_clean,
        "thermal_clean": thermal_clean,
        "inspection_observations": inspection_obs,
        "thermal_observations": thermal_obs
    }