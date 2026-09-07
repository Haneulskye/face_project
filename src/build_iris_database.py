from pathlib import Path
import sqlite3
import numpy as np

from iris_embedding import extract_iris_embedding
from iris_database import get_connection, init_iris_db


# ============================================================
# CONFIG
# ============================================================

INPUT_DIR = Path("output/iris_preprocessed")


# ============================================================
# EMBEDDING
# ============================================================

def build_subject_embedding(subject_dir):
    """
    한 subject의 모든 전처리 홍채 이미지에서
    embedding을 추출하고 평균 embedding을 생성한다.
    """

    embeddings = []

    image_paths = sorted(subject_dir.glob("*/*.jpg"))

    for image_path in image_paths:

        try:
            import cv2

            image = cv2.imread(
                str(image_path),
                cv2.IMREAD_GRAYSCALE
            )

            if image is None:
                continue

            # ResNet18 입력을 위해 grayscale -> RGB
            image = cv2.cvtColor(
                image,
                cv2.COLOR_GRAY2RGB
            )

            embedding = extract_iris_embedding(image)

            embedding = np.asarray(
                embedding,
                dtype=np.float32
            )

            embeddings.append(embedding)

        except Exception as e:
            print(
                f"[WARNING] Failed: {image_path}"
            )
            print(e)

    if not embeddings:
        return None

    # 여러 이미지의 평균
    mean_embedding = np.mean(
        np.stack(embeddings),
        axis=0
    )

    # L2 normalization
    norm = np.linalg.norm(mean_embedding)

    if norm == 0:
        return None

    mean_embedding = mean_embedding / norm

    return mean_embedding.astype(np.float32)


# ============================================================
# DATABASE
# ============================================================

def get_registered_subjects():
    conn = get_connection()

    cursor = conn.cursor()

    cursor.execute(
        "SELECT name FROM iris_users"
    )

    subjects = {
        row[0]
        for row in cursor.fetchall()
    }

    conn.close()

    return subjects


def register_subject(name, embedding):
    conn = get_connection()

    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO iris_users
        (name, embedding)
        VALUES (?, ?)
        """,
        (
            name,
            embedding.tobytes()
        )
    )

    conn.commit()
    conn.close()


# ============================================================
# MAIN
# ============================================================

def main():

    print("=" * 60)
    print("IRIS DATABASE BUILD")
    print("=" * 60)

    init_iris_db()

    existing = get_registered_subjects()

    subject_dirs = sorted(
        [
            p for p in INPUT_DIR.iterdir()
            if p.is_dir()
        ],
        key=lambda p: p.name
    )

    print(f"Subjects found    : {len(subject_dirs)}")
    print(f"Already registered: {len(existing)}")
    print()

    success = 0
    skipped = 0
    failed = 0

    for i, subject_dir in enumerate(subject_dirs, 1):

        subject = subject_dir.name

        print(
            f"[{i}/{len(subject_dirs)}] "
            f"Subject {subject}"
        )

        # 이미 등록되어 있으면 건너뜀
        if subject in existing:
            print("  -> SKIP (already registered)")
            skipped += 1
            continue

        embedding = build_subject_embedding(
            subject_dir
        )

        if embedding is None:
            print("  -> FAIL")
            failed += 1
            continue

        register_subject(
            subject,
            embedding
        )

        print(
            f"  -> REGISTERED "
            f"(embedding: {embedding.shape})"
        )

        success += 1

    print()
    print("=" * 60)
    print("IRIS DATABASE BUILD COMPLETE")
    print("=" * 60)
    print(f"Success : {success}")
    print(f"Skipped : {skipped}")
    print(f"Failed  : {failed}")
    print("=" * 60)


if __name__ == "__main__":
    main()
