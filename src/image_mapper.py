# src/image_mapper.py

from typing import List, Dict


def map_images_to_observations(
    observations: List[Dict],
    inspection_images: List[Dict],
    thermal_images: List[Dict],
    inspection_pages: List[Dict] = None,
    thermal_pages: List[Dict] = None,
    max_images_per_obs: int = 4
) -> List[Dict]:

    """
    Deterministically distribute images across observations.

    Fixes:
    - Prevents repeating the same image everywhere
    - Uses sequential image assignment
    - Still respects Gemini assignments if valid
    """

    if not observations:
        return observations

    # --------------------------------------------------
    # build list of all images
    # --------------------------------------------------

    all_images = []

    for img in inspection_images:
        if img.get("image_id"):
            all_images.append(img["image_id"])

    for img in thermal_images:
        if img.get("image_id"):
            all_images.append(img["image_id"])

    if not all_images:
        return observations

    valid_ids = set(all_images)

    # --------------------------------------------------
    # sequential distribution index
    # --------------------------------------------------

    cursor = 0
    total_images = len(all_images)

    for obs in observations:

        if not isinstance(obs, dict):
            continue

        existing = obs.get("related_image_ids", [])

        # keep valid Gemini assignments
        valid_existing = [
            img_id for img_id in existing
            if img_id in valid_ids
        ]

        if valid_existing:
            obs["related_image_ids"] = valid_existing[:max_images_per_obs]
            continue

        # --------------------------------------------------
        # assign next batch of images
        # --------------------------------------------------

        assigned = []

        for _ in range(max_images_per_obs):

            assigned.append(all_images[cursor])

            cursor += 1

            if cursor >= total_images:
                cursor = 0

        obs["related_image_ids"] = assigned

    return observations