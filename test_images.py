# test_images.py — run this to check

import json
import os

with open("outputs/debug_inspection_extraction.json", "r") as f:
    data = json.load(f)

images = data.get("images", [])

print(f"Total images extracted: {len(images)}")
print()

for img in images:
    path = img.get("file_path", "")
    exists = os.path.exists(path)
    print(f"{'✓' if exists else '✗'} {img['image_id']} → {path}")