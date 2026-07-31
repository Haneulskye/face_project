from pathlib import Path
from PIL import Image

DATASET = Path("datasets/CASIA-Iris-Interval")

person_count = 0
image_count = 0
left_count = 0
right_count = 0

sizes = {}

for person in sorted(DATASET.iterdir()):

    if not person.is_dir():
        continue

    person_count += 1

    for eye in ["L", "R"]:

        eye_dir = person / eye

        if not eye_dir.exists():
            continue

        for img_path in eye_dir.glob("*.jpg"):

            image_count += 1

            if eye == "L":
                left_count += 1
            else:
                right_count += 1

            with Image.open(img_path) as img:
                sizes[img.size] = sizes.get(img.size, 0) + 1

print("=" * 50)
print(f"Subjects : {person_count}")
print(f"Images   : {image_count}")
print(f"Left Eye : {left_count}")
print(f"Right Eye: {right_count}")

print("\nImage Sizes")

for size, cnt in sizes.items():
    print(size, cnt)