# Face Project

얼굴 인식(Face Recognition)과 홍채(Iris Recognition) 전처리를 위한 프로젝트

## 프로젝트 구조

```
face_project/
│
├── src/                     # 소스 코드
│   ├── detect_face.py
│   ├── align_face.py
│   ├── crop_face.py
│   ├── extract_embedding.py
│   ├── build_database.py
│   ├── recognize_face.py
│   ├── analyze_iris_dataset.py
│   ├── iris_preprocess.py
│   └── preprocess.py
│
├── datasets/                # 데이터셋 (GitHub 제외)
├── output/                  # 결과 저장 폴더 (GitHub 제외)
├── models/                  # 모델 파일
│   └── w600k_r50.onnx
│
├── requirements.txt
├── main.py
└── README.md
```

---

## 개발 환경

- Python 3.11
- macOS / Windows
- OpenCV
- InsightFace
- ONNX Runtime

---

## 설치

가상환경 생성

```bash
python -m venv .venv
```

활성화

### macOS / Linux

```bash
source .venv/bin/activate
```

### Windows

```bash
.venv\Scripts\activate
```

패키지 설치

```bash
pip install -r requirements.txt
```

---

## 데이터셋

GitHub에는 데이터셋이 포함되어 있지 않음.

필요한 데이터셋

- CASIA Iris Interval
- CASIA WebFace

다운로드 후 아래와 같이 배치.

```
datasets/
├── CASIA-Iris-Interval/
└── CASIA-WebFace_crop/
```

---

## 모델

필요한 모델

```
models/
└── w600k_r50.onnx
```

모델을 다운로드한 후 `models` 폴더에 넣어주세요.

---

## 실행 순서

### 1. 데이터셋 확인

```bash
python src/analyze_iris_dataset.py
```

---

### 2. 홍채 전처리

```bash
python src/iris_preprocess.py
```

전처리 결과

```
output/iris_preprocessed
```

---

### 3. 얼굴 데이터베이스 생성

```bash
python src/build_database.py
```

---

### 4. 얼굴 인식 실행

```bash
python src/recognize_face.py
```

---

## GitHub에 포함되지 않는 항목

다음 항목은 용량 문제로 GitHub에 업로드하지 않음.

- datasets/
- output/
- .venv/
- 모델 가중치(.onnx)

---

## 기본 안내

프로젝트를 처음 실행하는 경우

1. 저장소 Clone
2. Python 가상환경 생성
3. `pip install -r requirements.txt`
4. 데이터셋 다운로드
5. 모델 다운로드
6. 위 실행 순서대로 실행

#iris recognition module
Iris Image
      │
      ▼
Preprocessing
      │
      ▼
ResNet18 Feature Extractor
      │
      ▼
512-D Embedding Vector
      │
      ▼
SQLite Database
      │
      ▼
Cosine Similarity Matching
      │
      ▼
Authentication Result

{
    "is_authenticated": True,
    "name": "user_01",
    "final_score": 0.928,
    "details": {
        "face_score": 0.82,
        "iris_score": 1.00
    }
}

# 현재 구현은 사전 학습된 ResNet18을 Feature Extractor로 활용한 프로토타입으로, 홍채 데이터셋에 대해 별도의 Fine-tuning은 수행하지 않았다.
# 인증 성능은 입력 이미지의 품질과 조명 환경에 영향을 받을 수 있으며, 실제 서비스 적용을 위해서는 홍채 전용 데이터셋을 이용한 추가 학습 및 Threshold 최적화가 필요하다.
