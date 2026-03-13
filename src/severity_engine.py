# src/severity_engine.py

from typing import List, Dict


# ------------------------------------------------------------------
# keyword weights used for severity scoring
# ------------------------------------------------------------------

KEYWORD_WEIGHTS = {
    "dampness": 1,
    "moisture": 1,
    "efflorescence": 1,
    "leakage": 2,
    "seepage": 2,
    "plumbing": 2,
    "crack": 3,
    "structural": 3,
    "water ingress": 2,
    "thermal anomaly": 1,
}


# ------------------------------------------------------------------
# severity thresholds
# ------------------------------------------------------------------

SEVERITY_THRESHOLDS = {
    "low": 0,
    "medium": 3,
    "high": 6,
    "critical": 9,
}


# ------------------------------------------------------------------
# compute severity score from observations
# ------------------------------------------------------------------

def compute_severity_score(observations: List[Dict]) -> int:
    """
    Compute numeric severity score based on observation keywords.
    """

    score = 0

    for obs in observations:

        if not isinstance(obs, dict):
            continue

        text = obs.get("observation", "").lower()

        for keyword, weight in KEYWORD_WEIGHTS.items():

            if keyword in text:
                score += weight

    return score


# ------------------------------------------------------------------
# convert numeric score to severity level
# ------------------------------------------------------------------

def map_score_to_severity(score: int) -> str:
    """
    Convert score into severity category.
    """

    if score >= SEVERITY_THRESHOLDS["critical"]:
        return "Critical"

    if score >= SEVERITY_THRESHOLDS["high"]:
        return "High"

    if score >= SEVERITY_THRESHOLDS["medium"]:
        return "Medium"

    return "Low"


# ------------------------------------------------------------------
# main severity evaluation
# ------------------------------------------------------------------

def evaluate_severity(area_wise_observations: List[Dict]) -> Dict:
    """
    Determine severity level and reasoning from observations.
    """

    score = compute_severity_score(area_wise_observations)

    level = map_score_to_severity(score)

    reasoning = (
        f"Severity score computed as {score} based on detected moisture, "
        f"leakage, and structural indicators in inspection observations."
    )

    return {
        "level": level,
        "reasoning": reasoning
    }