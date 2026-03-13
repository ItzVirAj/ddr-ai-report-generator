# src/image_mapper.py

from typing import List, Dict


# ---------------------------------------------------------
# Area keywords for text-based matching
# ---------------------------------------------------------

AREA_KEYWORDS = {
    "bathroom":     ["bathroom", "bath", "toilet", "wc", "washroom"],
    "bedroom":      ["bedroom", "bed room", "master bedroom", "sleeping"],
    "kitchen":      ["kitchen", "cooking", "sink"],
    "hall":         ["hall", "living room", "drawing room", "lounge"],
    "balcony":      ["balcony", "terrace", "gallery"],
    "ceiling":      ["ceiling", "roof", "overhead"],
    "wall":         ["wall", "skirting", "plaster"],
    "floor":        ["floor", "flooring", "slab"],
    "plumbing":     ["pipe", "plumbing", "drain", "water line"],
}


# ---------------------------------------------------------
# Build page → image lookup
# ---------------------------------------------------------

def build_page_image_index(images: List[Dict]) -> Dict[int, List[str]]:
    """
    Convert image list into quick lookup:
    page_num → [image_id, image_id, ...]
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
# Build keyword → image lookup from image file names + page text
# ---------------------------------------------------------

def build_keyword_image_index(
    images: List[Dict],
    pages: List[Dict]
) -> Dict[str, List[str]]:
    """
    Map area keywords → image IDs.

    Strategy:
    - For each image, look at the text on the same page
    - If the page text mentions an area keyword, link that image to the area
    """

    # page_num → page_text lookup
    page_text_lookup = {}
    for page in pages:
        page_num = page.get("page_num")
        text = page.get("text", "").lower()
        if page_num:
            page_text_lookup[page_num] = text

    # area_category → [image_ids]
    keyword_index = {}

    for img in images:
        page_num = img.get("page_num")
        img_id = img.get("image_id")

        if not img_id:
            continue

        page_text = page_text_lookup.get(page_num, "")

        for area_category, keywords in AREA_KEYWORDS.items():
            for kw in keywords:
                if kw in page_text:
                    if area_category not in keyword_index:
                        keyword_index[area_category] = []
                    if img_id not in keyword_index[area_category]:
                        keyword_index[area_category].append(img_id)

    return keyword_index


# ---------------------------------------------------------
# Match observation area to keyword category
# ---------------------------------------------------------

def match_area_to_category(area_text: str) -> str:
    """
    Find which area category best matches the observation area label.

    Returns the matched category string or None.
    """

    area_lower = area_text.lower()

    for category, keywords in AREA_KEYWORDS.items():
        for kw in keywords:
            if kw in area_lower:
                return category

    return None


# ---------------------------------------------------------
# Map observation text to images via keyword matching
# ---------------------------------------------------------

def match_observation_to_images(
    obs_text: str,
    area_text: str,
    keyword_index: Dict[str, List[str]],
    page_index: Dict[int, List[str]],
    obs_page: int = None,
    max_images: int = 3
) -> List[str]:
    """
    Find relevant image IDs for an observation.

    Priority:
    1. Page-based match (if page_num is available)
    2. Area keyword match from keyword_index
    3. Observation text keyword match
    4. Fallback: first available image
    """

    matched = []

    # Priority 1 — page-based match
    if obs_page and obs_page in page_index:
        matched.extend(page_index[obs_page])

    if len(matched) >= max_images:
        return matched[:max_images]

    # Priority 2 — area label match
    category = match_area_to_category(area_text)

    if category and category in keyword_index:
        for img_id in keyword_index[category]:
            if img_id not in matched:
                matched.append(img_id)

    if len(matched) >= max_images:
        return matched[:max_images]

    # Priority 3 — observation text keyword scan
    obs_lower = obs_text.lower()

    for category, keywords in AREA_KEYWORDS.items():
        for kw in keywords:
            if kw in obs_lower:
                if category in keyword_index:
                    for img_id in keyword_index[category]:
                        if img_id not in matched:
                            matched.append(img_id)

    return matched[:max_images]


# ---------------------------------------------------------
# Main entry point
# ---------------------------------------------------------

def map_images_to_observations(
    observations: List[Dict],
    inspection_images: List[Dict],
    thermal_images: List[Dict],
    inspection_pages: List[Dict] = None,
    thermal_pages: List[Dict] = None,
    max_images_per_obs: int = 3
) -> List[Dict]:
    """
    Attach image IDs to each observation.

    Uses multi-strategy matching:
    - Page proximity
    - Area keyword matching
    - Observation text keyword matching
    - Fallback to first available
    """

    inspection_pages = inspection_pages or []
    thermal_pages = thermal_pages or []

    # build indexes
    inspection_page_index = build_page_image_index(inspection_images)
    thermal_page_index = build_page_image_index(thermal_images)

    inspection_keyword_index = build_keyword_image_index(
        inspection_images, inspection_pages
    )
    thermal_keyword_index = build_keyword_image_index(
        thermal_images, thermal_pages
    )

    # merge keyword indexes
    combined_keyword_index = {}

    for k, v in inspection_keyword_index.items():
        combined_keyword_index[k] = v[:]

    for k, v in thermal_keyword_index.items():
        if k in combined_keyword_index:
            for img_id in v:
                if img_id not in combined_keyword_index[k]:
                    combined_keyword_index[k].append(img_id)
        else:
            combined_keyword_index[k] = v[:]

    # merge page indexes
    combined_page_index = {}

    for page, imgs in inspection_page_index.items():
        combined_page_index[page] = imgs[:]

    for page, imgs in thermal_page_index.items():
        if page in combined_page_index:
            combined_page_index[page].extend(imgs)
        else:
            combined_page_index[page] = imgs[:]

    # fallback images
    fallback_images = []

    if inspection_images:
        fallback_images.append(inspection_images[0]["image_id"])

    if thermal_images:
        fallback_images.append(thermal_images[0]["image_id"])

    # process each observation
    for obs in observations:

        if not isinstance(obs, dict):
            continue

        # skip if AI already provided image IDs
        existing = obs.get("related_image_ids", [])
        if existing and len(existing) > 0:
            continue

        area_text = obs.get("area", "")
        obs_text = obs.get("observation", "")
        obs_page = obs.get("page_num")

        matched_images = match_observation_to_images(
            obs_text=obs_text,
            area_text=area_text,
            keyword_index=combined_keyword_index,
            page_index=combined_page_index,
            obs_page=obs_page,
            max_images=max_images_per_obs
        )

        # fallback if still empty
        if not matched_images:
            matched_images = fallback_images[:max_images_per_obs]

        obs["related_image_ids"] = matched_images

    return observations