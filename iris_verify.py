import sqlite3
import numpy as np

# 4. 코사인 유사도 계산
def cosine_similarity(a, b):
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

def verify_iris(input_embedding, threshold=0.75):
    """
    입력 홍채 임베딩과 DB 전체를 비교하여 가장 유사한 사용자 탐색
    """
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    cursor.execute("SELECT name, embedding FROM iris_users")
    rows = cursor.fetchall()
    conn.close()

    best_match = None
    max_sim = -1.0

    for name, blob in rows:
        db_embedding = np.frombuffer(blob, dtype=np.float32)
        sim = cosine_similarity(input_embedding, db_embedding)
        
        if sim > max_sim:
            max_sim = sim
            best_match = name

    if max_sim >= threshold:
        return {"name": best_match, "score": float(max_sim), "is_authenticated": True}
    return {"name": None, "score": float(max_sim), "is_authenticated": False}


# 5. 얼굴 + 홍채 결합 (Score Fusion) 로직
def authenticate_multimodal(face_result, iris_result, face_weight=0.5, iris_weight=0.5, final_threshold=0.70):
    """
    face_result: {"name": str, "score": float}
    iris_result: {"name": str, "score": float}
    """
    # 1. 동일 인물인지 검증
    if face_result.get("name") != iris_result.get("name") or not face_result.get("name"):
        return {
            "is_authenticated": False,
            "reason": "얼굴과 홍채 인식 대상 불일치",
            "final_score": 0.0
        }

    # 2. Score Fusion (가중 평균)
    face_score = face_result.get("score", 0.0)
    iris_score = iris_result.get("score", 0.0)
    
    final_score = (face_score * face_weight) + (iris_score * iris_weight)
    
    is_success = final_score >= final_threshold

    return {
        "is_authenticated": is_success,
        "name": face_result["name"],
        "final_score": round(final_score, 4),
        "details": {
            "face_score": round(face_score, 4),
            "iris_score": round(iris_score, 4)
        }
    }