# Face Project

얼굴·홍채 동시 인식 기반 사용자 인증과, 워치 연동 심박수 기록을 하나로 묶은 멀티모달 생체 인증 시스템. 별도 연구 트랙으로 저조도 환경 rPPG 심박수 추정(EfficientPhys + BiGRU) 실험도 포함한다 (`BUAA_lowlight_rPPG/`).

웹·Android·iOS 세 클라이언트가 **FastAPI 백엔드 하나**를 공유한다.

```
 Web (브라우저)   Android (Kotlin)   iOS (SwiftUI)
        └──────────────┼──────────────┘
                       ▼  HTTPS (ngrok 고정 도메인)
              FastAPI 백엔드 (backend/api.py)
        ┌──────────────┼───────────────────┐
        ▼              ▼                   ▼
  얼굴 인식        홍채 인식          심박수 저장
 (ArcFace)   (ResNet18 파인튜닝)   (워치 → 폰 앱 → 서버)
        └──────── SQLite (users.db) + database.pkl
```

- **인증 판정**: 얼굴 인식이 최종 판정, 홍채는 같은 사진에서 함께 계산되는 보조 신호
- **심박수**: 카메라 rPPG 대신 워치(갤럭시 워치 → Health Connect, 애플 워치 → HealthKit)에서 읽은 값을 서버에 저장. 얼굴 인증에 성공하면 자동으로 함께 기록된다

---

## 프로젝트 구조

```
face_project/
├── backend/                 # FastAPI 서버 (api.py, face_auth.py, iris_auth.py,
│                            #   heart_rate_store.py, user_profile_store.py)
├── web/                     # 순수 HTML/CSS/JS 웹앱 + 관리자 페이지(admin.*)
├── android/                 # Kotlin + Jetpack Compose 앱
├── ios/                     # Swift + SwiftUI 앱 (XcodeGen: project.yml)
├── src/                     # 연구용 전처리·학습 스크립트
│   ├── detect_face.py / align_face.py / crop_face.py
│   ├── extract_embedding.py / build_database.py / recognize_face.py
│   ├── analyze_iris_dataset.py / iris_preprocess.py / preprocess.py
│   ├── iris_embedding.py
│   └── train_iris_model.py  # 홍채 ResNet18 파인튜닝
├── BUAA_lowlight_rPPG/      # rPPG 연구 트랙 (별도 README 참고)
├── models/                  # w600k_r50.onnx, iris_resnet18_finetuned.pt (Git LFS)
├── datasets/                # 데이터셋 (GitHub 제외)
├── output/                  # 결과 저장 폴더 (GitHub 제외)
├── render.yaml              # Render 배포 시도 기록 (아래 참고, 실사용 안 함)
├── requirements.txt         # 전체 (연구용 포함)
└── requirements-web.txt     # 서버 실행에 필요한 최소 패키지
```

---

## 개발 환경

- Python 3.11, macOS / Windows
- OpenCV, InsightFace, ONNX Runtime, MediaPipe, PyTorch
- Android Studio (Koala 이상), Xcode 16 이상 + XcodeGen

## 설치

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

모델 가중치(`models/*.onnx`, `models/*.pt`)는 Git LFS로 관리한다. 새로 클론했다면:

```bash
brew install git-lfs && git lfs install && git lfs pull
```

## 데이터셋

GitHub에는 데이터셋이 포함되어 있지 않다.

- CASIA Iris Interval
- CASIA WebFace

```
datasets/
├── CASIA-Iris-Interval/
└── CASIA-WebFace_crop/
```

## 연구용 전처리 실행 순서

```bash
python src/analyze_iris_dataset.py   # 1. 데이터셋 확인
python src/iris_preprocess.py        # 2. 홍채 전처리 → output/iris_preprocessed
python src/build_database.py         # 3. 얼굴 데이터베이스 생성
python src/recognize_face.py         # 4. 얼굴 인식 실행
```

GitHub에 올리지 않는 항목: `datasets/`, `output/`, `.venv/`, `users.db`(등록 사용자 개인정보).

---

## Backend API 서버 (FastAPI)

```bash
source .venv/bin/activate
uvicorn backend.api:app --host 0.0.0.0 --port 8000 --reload
```

기동 후 `http://localhost:8000/docs`에서 Swagger UI로 테스트할 수 있다.

| Method | Endpoint | 설명 |
|---|---|---|
| GET | `/health` | 서버 상태 확인 |
| POST | `/auth/face` | 얼굴 이미지(`image`, multipart)로 인증. `{authenticated, name, score, profile, reason, iris}` 반환. `iris: {matched, score, reason}`는 보조 신호일 뿐 최종 판정은 얼굴 결과만으로 결정된다 |
| POST | `/users/register` | 신규 등록. `name/age/nickname/gender/height_cm/weight_kg(선택)/consent` + `image`. 같은 사진에서 홍채도 best-effort로 함께 등록 |
| GET | `/users/{name}` | 프로필 조회 |
| DELETE | `/users/{name}` | 사용자 삭제 (얼굴·홍채·심박수·프로필 전부) |
| GET | `/users/{name}/heart-rate/latest`, `/history` | 저장된 최신/전체 심박수 기록 조회 |
| POST | `/users/{name}/heart-rate/measure` | `bpm`(옵션) + `source`(옵션: `galaxy_watch`/`apple_watch`)를 저장 후 반환. `bpm`이 없으면 `{"available": false}` |
| GET | `/admin/users` | (관리자) 전체 사용자 목록 + 홍채 등록 여부 + 최신 심박수 |
| DELETE | `/admin/users/{name}` | (관리자) 사용자 삭제 |

- **등록 제한**: 만 14세 미만은 `age_restricted`(400), 얼굴 사진이 너무 흐리면 `low_quality_face`(422)로 거부된다. 흐린 템플릿이 등록되면 사람이 늘수록 오인식 위험이 커지므로 인증이 아니라 **등록 시점**에서만 막는다 (Laplacian variance 기반).
- **저장**: 얼굴 embedding은 `output/database/database.pkl`, 프로필은 `users.db`의 `app_users`, 홍채 embedding은 `iris_users`에 저장된다. 홍채 매칭은 `app_users`에 있는 이름으로만 필터링해 CASIA 249명과 섞이지 않게 했다.
- **관리자 API 인증**: `X-Admin-Token` 헤더가 `ADMIN_TOKEN` 환경변수와 일치해야 한다. 기본값(`changeme-admin`)은 로컬 데모용이므로 **실제로 서버를 띄울 때는 반드시 환경변수로 바꿀 것** (토큰 값은 저장소에 커밋하지 않는다).

### 얼굴 인식

ArcFace(`w600k_r50.onnx`, 512차원) embedding + 코사인 유사도, `FACE_THRESHOLD = 0.68`.

처음 0.65로 두었는데, 실사용자 테스트에서 서로 다른 두 사람의 유사도가 0.6467까지 나와 임계값에 거의 닿는 경우가 발견되어 0.68로 올렸다. 다만 너무 올리면 본인도 못 알아보는 경우가 늘어난다(0.72에서 실제로 발생). 등록 사진을 밝은 곳에서 정면으로 찍는 것이 임계값 조정보다 근본적인 개선이다.

### 홍채 인식

`backend/iris_auth.py`가 얼굴 사진에서 MediaPipe FaceMesh로 눈 주변을 크롭해 홍채 embedding을 계산한다. 모델은 CASIA-Iris-Interval(249명, 395개 subject_eye 클래스)로 파인튜닝한 ResNet18이다 (`src/train_iris_model.py`, `models/iris_resnet18_finetuned.pt`).

- 파인튜닝 전(ImageNet 특징만 사용): 서로 다른 사람인데 유사도 0.69~0.87 — 사실상 아무나 매칭되는 수준
- 파인튜닝 + augmentation 후(`IRIS_THRESHOLD = 0.64`): 검증 샘플 기준 본인 평균 0.93(최소 0.65) vs 타인 평균 0.45(최대 0.63)로 겹침 없이 분리

학습 데이터가 적외선 카메라(CASIA)라 폰 카메라(가시광선)와는 도메인 차이가 있다. 실기기 데이터로 재검증되기 전까지는 보조 신호로만 취급하며, `iris.matched`는 홍채 best-match가 얼굴 결과와 **같은 사람일 때만** true다. **모델을 교체하면 기존 홍채 embedding은 호환되지 않으므로** 삭제 후 재등록해야 한다.

### 워치 심박수 연동

브라우저는 워치에 접근할 수 없어, 폰 앱이 워치 값을 읽어 `POST /users/{name}/heart-rate/measure`로 올리고 웹은 조회만 한다.

- **자동 기록**: 얼굴 인증에 성공하는 순간 Android/iOS 앱이 백그라운드로 워치 최신 심박수를 읽어 함께 기록한다 (실패해도 인증 결과에는 영향 없음)
- **수동 기록**: 프로필 화면의 "심박수 측정" 버튼
- 같은 측정이 중복으로 2번 기록되는 경우가 있다 (그래프를 뽑을 때는 연속 중복을 합쳐서 사용)

---

## 안드로이드 앱

`android/`를 Android Studio로 열면 Gradle 동기화가 진행된다.

```
메인화면 → 얼굴 인식 중(카메라 촬영)
   ├─ 미등록 얼굴 → 회원가입 → 저장 완료
   └─ 등록된 얼굴 → 프로필 + 오늘의 심박수 + 전체기록
```

- **빌드 종류에 따라 서버 주소가 다르다** (`app/build.gradle.kts`의 `API_BASE_URL`): debug는 `http://10.0.2.2:8000/`(에뮬레이터 전용), release는 ngrok 고정 도메인. **실기기에는 반드시 release 빌드를 설치**해야 한다 (debug를 실기기에 깔면 서버에 연결되지 않고 HTTP 404가 난다).
  ```bash
  cd android && ./gradlew assembleRelease   # app/build/outputs/apk/release/app-release.apk
  ```
  카카오톡은 `.apk` 직접 전송을 막으므로 zip으로 압축해서 보낸다. 기존에 debug를 깔았다면 서명이 달라 **삭제 후 재설치**해야 한다.
- **Health Connect 권한**: `AndroidManifest.xml`에 `READ_HEART_RATE` 권한과 `<queries><package android:name="com.google.android.apps.healthdata"/></queries>`가 모두 필요하다 (`queries`가 없으면 Android 11+에서 권한 팝업이 아예 뜨지 않고 조용히 거부 처리된다). 프로필 화면에서 "심박수 측정"을 한 번 눌러 권한을 허용해야 하고, 갤럭시 워치는 Samsung Health ↔ Health Connect 연동이 켜져 있어야 값이 들어온다.
- 얼굴 인식 화면의 자동 심박수 기록은 Health Connect 권한이 이미 허용된 경우에만 동작한다 (이 화면에서 새로 권한을 요청하지 않음).
- 주요 구조: `network/`(Retrofit), `data/AuthRepository.kt`, `health/`(Health Connect), `ui/screens/`(Composable + ViewModel), `navigation/NavGraph.kt`.

## iOS 앱

`ios/`에 Swift + SwiftUI 프로젝트가 있다. 화면 흐름·API는 안드로이드와 동일하다.

```bash
cd ios
xcodegen generate          # project.yml → FaceAuth.xcodeproj (저장소에는 커밋하지 않음)
open FaceAuth.xcodeproj
```

- **실기기에 설치할 때 (기기마다 한 번씩)**: 케이블로 연결해 "이 컴퓨터를 신뢰" → Signing & Capabilities에서 Team(Apple ID) 선택 → 아이폰 설정의 **개인정보 보호 및 보안 → 개발자 모드 켜기**(재시작 필요) → Run → 설정 → 일반 → **VPN 및 기기 관리**에서 개발자 앱 신뢰. 케이블 연결 없이는 첫 설치가 불가능하다.
- `Networking/APIClient.swift`의 `APIConfig.baseURL`이 서버 주소다. 모든 요청에 `ngrok-skip-browser-warning` 헤더를 붙인다 — 없으면 무료 ngrok이 캠퍼스 와이파이 등 브라우저처럼 보이는 요청에 JSON 대신 안내 HTML을 돌려줘 "서버 응답을 해석하지 못했습니다"가 뜬다.
- **카메라 프리뷰**(`Camera/CameraPreviewView.swift`, `Views/FaceScanView.swift`): `CameraPreviewView`는 항상 마운트해두고(준비 전엔 opacity 0) 얼굴 가이드 오버레이만 나중에 나타나게 했다. 둘이 같은 화면 갱신에서 처음 마운트되면 SwiftUI AttributeGraph "cyclic graph" 크래시가 난다.
- 심박수는 HealthKit(`Health/HealthKitManager.swift`)에서 읽는다. `com.apple.developer.healthkit` 엔타이틀먼트는 `project.yml`에 선언되어 있다. 시뮬레이터는 실제 워치 데이터를 받을 수 없고 카메라도 없어 **카메라·워치 연동은 실기기에서만 검증 가능**하다.

## 웹 앱

`web/`의 순수 HTML/CSS/JS 정적 웹앱이며, **백엔드가 이 폴더를 직접 서빙**하므로 서버 하나만 켜면 된다 (`http://localhost:8000/`).

- 실제 브라우저의 `getUserMedia`는 카메라 접근이 안정적이라 현장 시연에 사고 위험이 가장 적다.
- 심박수 카드는 폰 앱이 올려둔 값을 조회만 한다. 웹만 켜면 "측정 준비 중"으로 남는다.
- 구조: `index.html`, `app.js`(카메라·API·화면 전환), `style.css`. 브라우저가 정적 파일을 강하게 캐싱하므로 `style.css?v=4`, `app.js?v=5` 같은 캐시 버스팅 쿼리가 붙어 있다 — **이 파일들을 수정하면 버전 번호를 올릴 것.**
- **관리자 페이지** `/admin.html`: 등록 사용자 목록, 홍채 등록 여부, 최신 심박수 확인 및 삭제. `ADMIN_TOKEN` 입력이 필요하다.

---

## 서버 운영 (현재 방식: 로컬 맥 + ngrok 고정 도메인)

정식 호스팅 없이, 서버를 돌리는 맥에서 ngrok의 무료 **고정(dev) 도메인**으로 외부에 연결한다. 도메인은 재시작해도 바뀌지 않는다.

```bash
ADMIN_TOKEN=<직접 정한 값> uvicorn backend.api:app --host 0.0.0.0 --port 8000
ngrok http 8000 --url https://<예약한-고정-도메인>.ngrok-free.dev
```

앱(Android release / iOS)의 서버 주소는 이 도메인을 가리킨다. 도메인을 바꾸면 `android/app/build.gradle.kts`와 `ios/FaceAuth/Networking/APIClient.swift`를 함께 수정하고 앱을 다시 빌드해야 한다.

맥이 재부팅·재로그인해도 자동으로 다시 뜨도록 `~/Library/LaunchAgents/`에 `RunAtLoad` + `KeepAlive` launchd 작업(백엔드, ngrok 각각)을 등록해 사용했다. 맥이 잠들지 않도록 전원 연결 시 `sudo pmset -c sleep 0`을 설정한다. 단, 맥이 꺼져 있거나 인터넷이 없으면 서버도 내려간다.

### Render.com 배포 시도 (미채택)

`render.yaml`(Blueprint)로 무료 티어 배포를 시도했으나, onnxruntime + mediapipe + torch + opencv를 함께 올리면 **무료 티어 512MB RAM 초과(OOM)**로 기동하지 못했다 (CPU 전용 torch로 바꿔도 동일). 유료 플랜(Standard, 월 $25)이 아니면 어려워 채택하지 않았고, 설정 파일은 기록용으로만 남겨두었다.

---

## 한계 및 향후 과제

- 얼굴·홍채 검증 표본이 작다. 등록자가 늘면 경계 사례가 늘 수 있어 추가 검증과 임계값 재조정이 필요하다 (등록 사진은 밝은 곳에서 정면으로).
- 홍채 모델은 적외선(CASIA)으로 학습되어 폰 카메라와 도메인 차이가 있다 → 보조 신호로만 사용.
- 임베딩은 민감한 생체정보다 — 저장 방식·보관 기간·동의 절차를 정리해야 한다.
- 현재 서버는 로컬 맥 + 임시 터널 구성이라 장시간 안정 운영에는 한계가 있다. 발표는 시연 영상 병행을 전제로 한다.
- rPPG 모델(BiGRU)은 전체 시퀀스가 필요한 offline 구조라 실시간 추론에는 그대로 쓰기 어렵다.
