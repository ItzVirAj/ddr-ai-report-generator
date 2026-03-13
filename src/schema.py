# src/schema.py

from typing import Any, Dict, List


def _safe_str(value: Any, default: str = "Not Available") -> str:
    if not value:
        return default
    return str(value).strip() or default


def _safe_list(value: Any) -> list:
    if isinstance(value, list):
        return value
    return []


def validate_observation(obs: Any) -> Dict:
    """
    Validate and normalize a single area observation.
    """

    if not isinstance(obs, dict):
        return {
            "area": "General Area",
            "observation": "Not Available",
            "source": "inspection",
            "thermal_confirmation": "Not confirmed by thermal scan",
            "related_image_ids": []
        }

    source = obs.get("source", "inspection")

    if source not in ("inspection", "thermal", "both"):
        source = "inspection"

    return {
        "area": _safe_str(obs.get("area"), "General Area"),
        "observation": _safe_str(obs.get("observation"), "Not Available"),
        "source": source,
        "thermal_confirmation": _safe_str(
            obs.get("thermal_confirmation"),
            "Not confirmed by thermal scan"
        ),
        "related_image_ids": _safe_list(obs.get("related_image_ids"))
    }


def validate_severity(severity: Any) -> Dict:
    """
    Validate severity assessment block.
    """

    if not isinstance(severity, dict):
        return {
            "level": "Medium",
            "reasoning": "Not Available"
        }

    level = severity.get("level", "Medium")

    valid_levels = ("Low", "Medium", "High", "Critical")

    if level not in valid_levels:
        level = "Medium"

    return {
        "level": level,
        "reasoning": _safe_str(severity.get("reasoning"), "Not Available")
    }


def validate_ddr(ddr: Any) -> Dict:
    """
    Validate and normalize the full DDR JSON structure.
    """

    if not isinstance(ddr, dict):
        ddr = {}

    observations_raw = _safe_list(ddr.get("area_wise_observations"))
    observations = [validate_observation(o) for o in observations_raw]

    return {
        "property_issue_summary": _safe_str(
            ddr.get("property_issue_summary")
        ),
        "area_wise_observations": observations,
        "probable_root_cause": _safe_list(ddr.get("probable_root_cause")),
        "severity_assessment": validate_severity(
            ddr.get("severity_assessment")
        ),
        "recommended_actions": _safe_list(ddr.get("recommended_actions")),
        "additional_notes": _safe_str(ddr.get("additional_notes")),
        "missing_or_unclear_information": _safe_str(
            ddr.get("missing_or_unclear_information"), "None reported."
        )
    }