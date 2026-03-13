# src/image_mapper.py

from typing import List, Dict


# ---------------------------------------------------------
# Build page → image lookup
# ---------------------------------------------------------

def build_page_image_index(images: List[Dict]) -> Dict[int, List[str]]:
    """
    Convert image list into quick lookup:

    page_num → [image_id, image_id]
    """

    index = {}

    for img in images:

        page = img.get("page_num")
        img_id = img.get("image_id")

        if not page or not img_id:
            continue

        if page not in index:
            index[page] = []

        index[page].append(img_id)

    return index


# ---------------------------------------------------------
# Map observations → images
# ---------------------------------------------------------

def map_images_to_observations(
    observations: List[Dict],
    inspection_images: List[Dict],
    thermal_images: List[Dict],
    max_images_per_obs: int = 3
) -> List[Dict]:
    """
    Attach image IDs to observations based on page proximity.

    Strategy:
    - build page → image index
    - attach nearby images to observation
    """

    inspection_index = build_page_image_index(inspection_images)
    thermal_index = build_page_image_index(thermal_images)

    for obs in observations:

        if not isinstance(obs, dict):
            continue

        related_images = []

        page = obs.get("page_num")

        if page:

            # inspection images
            if page in inspection_index:
                related_images.extend(inspection_index[page])

            # thermal images
            if page in thermal_index:
                related_images.extend(thermal_index[page])

        # fallback: use first few images if page missing
        if not related_images:

            related_images.extend(
                [img["image_id"] for img in inspection_images[:1]]
            )

            related_images.extend(
                [img["image_id"] for img in thermal_images[:1]]
            )

        obs["related_image_ids"] = related_images[:max_images_per_obs]

    return observations