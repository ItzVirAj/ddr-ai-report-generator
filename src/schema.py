# src/schema.py

DDR_SCHEMA = {
    "property_issue_summary": str,
    "area_wise_observations": list,
    "probable_root_cause": list,
    "severity_assessment": dict,
    "recommended_actions": list,
    "additional_notes": str,
    "missing_or_unclear_information": str
}


def validate_ddr(data):
    """
    Ensure the DDR JSON always contains required fields
    and normalize the structure so downstream code never breaks.
    """

    clean = {}

    # -----------------------------------------------------
    # Property Summary
    # -----------------------------------------------------

    clean["property_issue_summary"] = data.get(
        "property_issue_summary",
        "Not Available"
    )

    # -----------------------------------------------------
    # Area Observations
    # -----------------------------------------------------

    observations = data.get("area_wise_observations", [])

    normalized_obs = []

    for obs in observations:

        if not isinstance(obs, dict):
            continue

        normalized_obs.append({
            "area": obs.get("area", "General Area"),
            "observation": obs.get("observation", "Observation not available"),
            "source": obs.get("source", "inspection"),
            "related_image_ids": obs.get("related_image_ids", [])
        })

    clean["area_wise_observations"] = normalized_obs

    # -----------------------------------------------------
    # Root Causes
    # -----------------------------------------------------

    root_causes = data.get("probable_root_cause", [])

    if not isinstance(root_causes, list):
        root_causes = [str(root_causes)]

    clean["probable_root_cause"] = root_causes

    # -----------------------------------------------------
    # Severity Assessment
    # -----------------------------------------------------

    severity = data.get("severity_assessment", {})

    if not isinstance(severity, dict):
        severity = {}

    clean["severity_assessment"] = {
        "level": severity.get("level", "Medium"),
        "reasoning": severity.get(
            "reasoning",
            "Multiple moisture indicators observed across inspected areas."
        )
    }

    # -----------------------------------------------------
    # Recommended Actions
    # -----------------------------------------------------

    actions = data.get("recommended_actions", [])

    if not isinstance(actions, list):
        actions = [str(actions)]

    clean["recommended_actions"] = actions

    # -----------------------------------------------------
    # Additional Notes
    # -----------------------------------------------------

    clean["additional_notes"] = data.get(
        "additional_notes",
        "Not Available"
    )

    # -----------------------------------------------------
    # Missing Information
    # -----------------------------------------------------

    clean["missing_or_unclear_information"] = data.get(
        "missing_or_unclear_information",
        "None reported."
    )

    return clean