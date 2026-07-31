from pathlib import Path
import cv2
import csv

# ==========================
# Path
# ==========================

INPUT_DIR = Path("datasets/CASIA-Iris-Interval")

OUTPUT_DIR = Path("output/iris_preprocessed")
LOG_DIR = Path("output/iris_logs")

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
LOG_DIR.mkdir(parents=True, exist_ok=True)

LOG_FILE = LOG_DIR / "preprocess_log.csv"

TARGET_SIZE = (224, 224)

# ==========================
# CLAHE
# ==========================

clahe = cv2.createCLAHE(
    clipLimit=2.0,
    tileGridSize=(8, 8)
)

# ==========================
# CSV
# ==========================

with open(LOG_FILE, "w", newline="") as f:

    writer = csv.writer(f)

    writer.writerow([
        "subject",
        "eye",
        "filename",
        "status"
    ])

    total = 0
    success = 0

    # ==========================
    # Subject Loop
    # ==========================

    for subject in sorted(INPUT_DIR.iterdir()):

        if not subject.is_dir():
            continue

        for eye in ["L", "R"]:

            eye_dir = subject / eye

            if not eye_dir.exists():
                continue

            save_eye_dir = OUTPUT_DIR / subject.name / eye
            save_eye_dir.mkdir(parents=True, exist_ok=True)

            for img_path in sorted(eye_dir.glob("*.jpg")):

                total += 1

                img = cv2.imread(str(img_path), cv2.IMREAD_GRAYSCALE)

                if img is None:

                    writer.writerow([
                        subject.name,
                        eye,
                        img_path.name,
                        "FAIL"
                    ])

                    continue

                # Resize
                img = cv2.resize(
                    img,
                    TARGET_SIZE,
                    interpolation=cv2.INTER_AREA
                )

                # CLAHE
                img = clahe.apply(img)

                # Normalize
                img = cv2.normalize(
                    img,
                    None,
                    0,
                    255,
                    cv2.NORM_MINMAX
                )

                save_path = save_eye_dir / img_path.name

                cv2.imwrite(str(save_path), img)

                success += 1

                writer.writerow([
                    subject.name,
                    eye,
                    img_path.name,
                    "PASS"
                ])

print("=" * 50)
print(f"TOTAL   : {total}")
print(f"SUCCESS : {success}")
print(f"FAIL    : {total-success}")
print("=" * 50)
print("Saved to :", OUTPUT_DIR)
print("Log      :", LOG_FILE)