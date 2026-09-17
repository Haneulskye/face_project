from pathlib import Path
import sqlite3

import cv2
import mediapipe as mp
import numpy as np

from src.iris_embedding import extract_iris_embedding


# ============================================================
# CONFIG
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DB_PATH = PROJECT_ROOT / "users.db"

IRIS_THRESHOLD = 0.75

# NOTE (프로토타입 / 데모 단계):
# extract_iris_embedding()은 홍채 전용으로 학습된 모델이 아니라 ImageNet
# 사전학습 ResNet18에서 분류 헤드만 제거한 범용 특징 추출기다. 즉 지금의
# 홍채 "인식"은 실제 홍채 무늬 기반 생체인증이 아니라 눈 주변 이미지의
# 대략적인 유사도 비교에 가깝다. 학술제 데모(흐름 시연)용으로는 충분하지만
# 정확도가 필요하면 홍채 전용 데이터로 파인튜닝한 모델로 교체해야 한다.
# (10월 말 정확도 개선 작업 시 이 파일과 src/iris_embedding.py를 함께 본다.)


# ============================================================
# DATABASE
# ============================================================

def get_db_connection():
    return sqlite3.connect(DB_PATH)


def _init_iris_table():
    conn = get_db_connection()
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS iris_users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            embedding BLOB
        )
        """
    )
    conn.commit()
    conn.close()


_init_iris_table()


# ============================================================
# EYE CROP (for live camera photos — CASIA-trained preprocessing
# assumes an already-cropped eye image, so a live full-face/selfie
# photo needs this step first)
# ============================================================

_IRIS_FACE_MESH = mp.solutions.face_mesh.FaceMesh(
    static_image_mode=True,
    max_num_faces=1,
    refine_landmarks=True,
)

# MediaPipe FaceMesh eye-contour landmark ids (subject's left eye).
_EYE_LANDMARK_IDS = [33, 7, 163, 144, 145, 153, 154, 155, 133, 173, 157, 158, 159, 160, 161, 246]

_CLAHE = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))


def crop_iris(image):
    """
    Locate one eye in a live camera photo and return a preprocessed
    grayscale crop matching the CASIA-Iris-Interval preprocessing
    (resize 224x224 + CLAHE + normalize) that the embedding model expects.
    """

    if image is None:
        return None

    rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    result = _IRIS_FACE_MESH.process(rgb)

    if not result.multi_face_landmarks:
        return None

    landmarks = result.multi_face_landmarks[0].landmark
    h, w = image.shape[:2]

    xs = [landmarks[i].x * w for i in _EYE_LANDMARK_IDS]
    ys = [landmarks[i].y * h for i in _EYE_LANDMARK_IDS]

    cx = int((min(xs) + max(xs)) / 2)
    cy = int((min(ys) + max(ys)) / 2)

    eye_width = max(xs) - min(xs)
    half = max(int(eye_width * 1.4), 30)

    x1, x2 = max(0, cx - half), min(w, cx + half)
    y1, y2 = max(0, cy - half), min(h, cy + half)

    crop = image[y1:y2, x1:x2]

    if crop.size == 0:
        return None

    gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)
    gray = cv2.resize(gray, (224, 224), interpolation=cv2.INTER_AREA)
    gray = _CLAHE.apply(gray)
    gray = cv2.normalize(gray, None, 0, 255, cv2.NORM_MINMAX)

    return gray


# ============================================================
# UTILS
# ============================================================

def cosine_similarity(a, b):
    a = np.asarray(a, dtype=np.float32)
    b = np.asarray(b, dtype=np.float32)

    a_norm = np.linalg.norm(a)
    b_norm = np.linalg.norm(b)

    if a_norm == 0 or b_norm == 0:
        return 0.0

    return float(np.dot(a, b) / (a_norm * b_norm))


def load_iris_database(only_app_users=True):
    """
    By default only returns entries for names present in `app_users`
    (real registered demo users) — the same gallery-pollution problem
    diagnosed for face auth applies here: matching against the 249
    unrelated CASIA-Iris-Interval subjects inflates false accepts.
    """

    conn = get_db_connection()
    cursor = conn.cursor()

    if only_app_users:
        cursor.execute(
            """
            SELECT iris_users.name, iris_users.embedding
            FROM iris_users
            INNER JOIN app_users ON app_users.name = iris_users.name
            """
        )
    else:
        cursor.execute("SELECT name, embedding FROM iris_users")

    rows = cursor.fetchall()
    conn.close()

    database = []

    for name, blob in rows:
        embedding = np.frombuffer(
            blob,
            dtype=np.float32
        )

        database.append(
            {
                "name": name,
                "embedding": embedding
            }
        )

    return database


# ============================================================
# IRIS AUTHENTICATION
# ============================================================

def authenticate_iris(
    iris_image,
    threshold=IRIS_THRESHOLD,
    only_app_users=True
):
    """
    Authenticate a user from an iris image.

    Parameters
    ----------
    iris_image : numpy.ndarray
        Iris image. Grayscale or BGR image is accepted.

    threshold : float
        Cosine similarity threshold.

    Returns
    -------
    dict
        {
            "authenticated": bool,
            "name": str or None,
            "score": float
        }
    """

    if iris_image is None:
        return {
            "authenticated": False,
            "name": None,
            "score": 0.0,
            "reason": "iris image is None"
        }

    # --------------------------------------------------------
    # Convert image to RGB
    # --------------------------------------------------------

    if len(iris_image.shape) == 2:
        iris_rgb = cv2.cvtColor(
            iris_image,
            cv2.COLOR_GRAY2RGB
        )
    else:
        iris_rgb = cv2.cvtColor(
            iris_image,
            cv2.COLOR_BGR2RGB
        )

    # --------------------------------------------------------
    # Extract embedding
    # --------------------------------------------------------

    try:
        embedding = extract_iris_embedding(iris_rgb)
    except Exception as e:
        return {
            "authenticated": False,
            "name": None,
            "score": 0.0,
            "reason": f"embedding extraction failed: {e}"
        }

    # --------------------------------------------------------
    # Load database
    # --------------------------------------------------------

    database = load_iris_database(only_app_users=only_app_users)

    if not database:
        return {
            "authenticated": False,
            "name": None,
            "score": 0.0,
            "reason": "iris database is empty"
        }

    # --------------------------------------------------------
    # Matching
    # --------------------------------------------------------

    best_name = None
    best_score = -1.0

    for item in database:
        score = cosine_similarity(
            embedding,
            item["embedding"]
        )

        if score > best_score:
            best_score = score
            best_name = item["name"]

    authenticated = best_score >= threshold

    return {
        "authenticated": authenticated,
        "name": best_name if authenticated else None,
        "score": round(best_score, 4)
    }


# ============================================================
# LIVE REGISTRATION / AUTH FROM A FULL CAMERA PHOTO
#
# The functions above operate on an already-cropped eye image (the
# CASIA-Iris-Interval convention). Live clients only take one selfie-style
# photo per registration/auth attempt, so these wrappers do the eye crop
# first and share that one photo with the face pipeline.
# ============================================================

def register_iris(name, image):
    """
    Crop the eye region out of a live registration photo, embed it, and
    store it under `name` in `iris_users` (replacing any prior entry for
    that name). Best-effort: returns None (without raising) if no eye
    could be located, since iris registration is a secondary modality —
    registration should not fail just because this step didn't work.
    """

    iris_crop = crop_iris(image)

    if iris_crop is None:
        return None

    try:
        iris_rgb = cv2.cvtColor(iris_crop, cv2.COLOR_GRAY2RGB)
        embedding = np.asarray(extract_iris_embedding(iris_rgb), dtype=np.float32)
    except Exception:
        return None

    conn = get_db_connection()
    conn.execute("DELETE FROM iris_users WHERE name = ?", (name,))
    conn.execute(
        "INSERT INTO iris_users (name, embedding) VALUES (?, ?)",
        (name, embedding.tobytes()),
    )
    conn.commit()
    conn.close()

    return embedding


def delete_iris(name):
    """Remove `name`'s iris entry, if present. Returns whether one existed."""

    conn = get_db_connection()
    cursor = conn.execute("DELETE FROM iris_users WHERE name = ?", (name,))
    conn.commit()
    deleted = cursor.rowcount > 0
    conn.close()

    return deleted


def authenticate_iris_from_photo(image, threshold=IRIS_THRESHOLD):
    """Crop the eye out of a live photo, then run authenticate_iris on it."""

    iris_crop = crop_iris(image)

    if iris_crop is None:
        return {
            "authenticated": False,
            "name": None,
            "score": 0.0,
            "reason": "eye_not_detected",
        }

    return authenticate_iris(iris_crop, threshold=threshold)
