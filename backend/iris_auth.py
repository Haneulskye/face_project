from pathlib import Path
import sqlite3

import cv2
import numpy as np

from src.iris_embedding import extract_iris_embedding


# ============================================================
# CONFIG
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DB_PATH = PROJECT_ROOT / "users.db"

IRIS_THRESHOLD = 0.75


# ============================================================
# DATABASE
# ============================================================

def get_db_connection():
    return sqlite3.connect(DB_PATH)


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


def load_iris_database():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT name, embedding FROM iris_users"
    )

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
    threshold=IRIS_THRESHOLD
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

    database = load_iris_database()

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
