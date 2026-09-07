import os
import pickle

import cv2
import numpy as np
import onnxruntime as ort
import mediapipe as mp


# ============================================================
# CONFIG
# ============================================================

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

MODEL_PATH = os.path.join(
    BASE_DIR,
    "models",
    "w600k_r50.onnx"
)

DATABASE_PATH = os.path.join(
    BASE_DIR,
    "output",
    "database",
    "database.pkl"
)

FACE_THRESHOLD = 0.45


# ============================================================
# LOAD DATABASE
# ============================================================

with open(DATABASE_PATH, "rb") as f:
    DATABASE = pickle.load(f)


# ============================================================
# LOAD ARC FACE MODEL
# ============================================================

SESSION = ort.InferenceSession(
    MODEL_PATH,
    providers=["CPUExecutionProvider"]
)

INPUT_NAME = SESSION.get_inputs()[0].name


# ============================================================
# MEDIAPIPE FACE MESH
# ============================================================

FACE_MESH = mp.solutions.face_mesh.FaceMesh(
    static_image_mode=True,
    max_num_faces=1,
    refine_landmarks=True
)


# ============================================================
# FACE CROP
# ============================================================

def crop_face(image):
    """
    Detect face landmarks and create the same
    112x112 face crop used by the existing pipeline.
    """

    if image is None:
        return None

    rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

    result = FACE_MESH.process(rgb)

    if not result.multi_face_landmarks:
        return None

    landmarks = result.multi_face_landmarks[0].landmark

    h, w = image.shape[:2]

    # Existing pipeline:
    # left eye landmark 33
    # right eye landmark 263

    left_eye = np.array([
        landmarks[33].x * w,
        landmarks[33].y * h
    ])

    right_eye = np.array([
        landmarks[263].x * w,
        landmarks[263].y * h
    ])

    center = (left_eye + right_eye) / 2

    cx = int(center[0])
    cy = int(center[1])

    x1 = cx - 80
    x2 = cx + 80

    y1 = cy - 90
    y2 = cy + 110

    # Boundary protection
    x1 = max(0, x1)
    y1 = max(0, y1)
    x2 = min(w, x2)
    y2 = min(h, y2)

    crop = image[y1:y2, x1:x2]

    if crop.size == 0:
        return None

    crop = cv2.resize(crop, (112, 112))

    return crop


# ============================================================
# ARC FACE EMBEDDING
# ============================================================

def extract_embedding(face_image):
    """
    Extract 512-D ArcFace embedding.
    """

    if face_image is None:
        return None

    image = cv2.cvtColor(face_image, cv2.COLOR_BGR2RGB)

    image = image.astype(np.float32)

    image = (image - 127.5) / 127.5

    image = np.transpose(image, (2, 0, 1))

    image = np.expand_dims(image, axis=0)

    embedding = SESSION.run(
        None,
        {INPUT_NAME: image}
    )[0][0]

    # L2 normalization
    norm = np.linalg.norm(embedding)

    if norm == 0:
        return None

    embedding = embedding / norm

    return embedding.astype(np.float32)


# ============================================================
# COSINE SIMILARITY
# ============================================================

def cosine_similarity(a, b):
    """
    Cosine similarity between two embeddings.
    """

    a = np.asarray(a, dtype=np.float32)
    b = np.asarray(b, dtype=np.float32)

    denom = np.linalg.norm(a) * np.linalg.norm(b)

    if denom == 0:
        return 0.0

    return float(np.dot(a, b) / denom)


# ============================================================
# FACE AUTHENTICATION
# ============================================================

def authenticate_face(image, threshold=FACE_THRESHOLD):
    """
    Main backend function.

    Parameters
    ----------
    image : numpy.ndarray
        BGR image from camera/upload.

    threshold : float
        Authentication threshold.

    Returns
    -------
    dict
        {
            "authenticated": bool,
            "name": str or None,
            "score": float
        }
    """

    face_crop = crop_face(image)

    if face_crop is None:
        return {
            "authenticated": False,
            "name": None,
            "score": 0.0,
            "reason": "face_not_detected"
        }

    embedding = extract_embedding(face_crop)

    if embedding is None:
        return {
            "authenticated": False,
            "name": None,
            "score": 0.0,
            "reason": "embedding_failed"
        }

    best_name = None
    best_score = -1.0

    for name, db_embedding in DATABASE.items():

        score = cosine_similarity(
            embedding,
            db_embedding
        )

        if score > best_score:
            best_score = score
            best_name = name

    authenticated = best_score >= threshold

    if not authenticated:
        best_name = None

    return {
        "authenticated": authenticated,
        "name": best_name,
        "score": round(float(best_score), 4)
    }


# ============================================================
# TEST
# ============================================================

if __name__ == "__main__":

    print("=" * 60)
    print("FACE AUTH BACKEND TEST")
    print("=" * 60)

    print(f"Database entries : {len(DATABASE)}")
    print(f"Model            : {MODEL_PATH}")
    print(f"Threshold        : {FACE_THRESHOLD}")

    print("=" * 60)
    print("Module loaded successfully.")
