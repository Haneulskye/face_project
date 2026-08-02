import numpy as np
from iris_embedding import extract_iris_embedding
from iris_database import register_iris
from iris_verify import verify_iris, authenticate_multimodal

# --- 예시 테스트용 모의 데이터 ---
# (실제 환경에서는 카메라나 파일에서 이미지 읽어옴)
fake_face_img = np.zeros((112, 112, 3), dtype=np.uint8) 
fake_iris_img = np.zeros((224, 224, 3), dtype=np.uint8)

# 1. DB에 테스트 사용자 등록 (1회성)
test_iris_emb = extract_iris_embedding(fake_iris_img)
register_iris("user_01", test_iris_emb)

# 2. 임베딩 추출
# face_emb = extract_embedding(fake_face_img) # 기존 얼굴 추출
iris_emb = extract_iris_embedding(fake_iris_img)

# 3. 개별 인증 수행 (예시 점수 설정)
# face_result = recognize_face(face_emb)
face_result = {"name": "user_01", "score": 0.82}  # 얼굴 인식 결과 예시
iris_result = verify_iris(iris_emb, threshold=0.6)  # 홍채 인식 결과

# 4. 멀티모달 최종 인증 실행
final_auth = authenticate_multimodal(
    face_result=face_result,
    iris_result=iris_result,
    face_weight=0.4,  # 얼굴 가중치 40%
    iris_weight=0.6,  # 홍채 가중치 60% (보안성 강조)
    final_threshold=0.70
)

print("=== 최종 인증 결과 ===")
print(final_auth)