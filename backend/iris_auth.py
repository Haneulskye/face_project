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

IRIS_THRESHOLD = 0.68

# NOTE (2026-09-17 갱신):
# extract_iris_embedding()은 이제 CASIA-Iris-Interval(249명, 395개
# subject_eye 클래스)로 파인튜닝된 ResNet18을 쓴다 (src/train_iris_model.py,
# 가중치는 models/iris_resnet18_finetuned.pt). 파인튜닝 전에는 ImageNet
# 사전학습 특징만 썼는데, 실제 등록된 사용자들로 측정해보니 서로 다른
# 사람인데도 코사인 유사도가 0.75~0.87까지 나와 threshold(0.75)로 걸러지지
# 않는 상태였다 — 사실상 아무나 매칭되는 수준. 파인튜닝 후 CASIA 검증
# 세트 기준 genuine 평균 0.92(최소 0.61) vs impostor 평균 0.47(최대 0.66)로
# 분리가 뚜렷해졌고, threshold도 그에 맞춰 0.68로 낮췄다.
#
# 다만 학습 데이터가 적외선 카메라로 찍은 CASIA 이미지라, 폰 카메라(가시광선)
# 사진과는 도메인 차이가 있다 — 실제 라이브 등록자 데이터로 재검증 전까지는
# 여전히 보조 신호로만 취급한다 (얼굴 인식이 최종 인증을 판정, iris는 화면에
# 함께 보여주기만 함. backend/api.py 참고).
#
# 기존에 등록된 사용자(모델 교체 전)의 홍채 embedding은 새 모델과 호환되지
# 않는다 — 다시 매칭되게 하려면 DELETE 후 재등록해야 한다.


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


def has_iris(name):
    conn = get_db_connection()
    row = conn.execute("SELECT 1 FROM iris_users WHERE name = ?", (name,)).fetchone()
    conn.close()
    return row is not None


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
