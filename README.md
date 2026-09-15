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

* 현재 구현은 사전 학습된 ResNet18을 Feature Extractor로 활용한 프로토타입으로, 홍채 데이터셋에 대해 별도의 Fine-tuning은 수행하지 않았다.
* 인증 성능은 입력 이미지의 품질과 조명 환경에 영향을 받을 수 있으며, 실제 서비스 적용을 위해서는 홍채 전용 데이터셋을 이용한 추가 학습 및 Threshold 최적화가 필요하다.

---

## Backend API 서버 (FastAPI)

`backend/face_auth.py`의 얼굴 인증 로직을 HTTP로 노출하는 서버. 안드로이드·iOS·웹 클라이언트가 모두 이 서버 하나를 호출한다.

```bash
source .venv/bin/activate
uvicorn backend.api:app --host 0.0.0.0 --port 8000 --reload
```

기동 후 `http://localhost:8000/docs`에서 Swagger UI로 바로 테스트 가능.

| Method | Endpoint | 설명 |
|---|---|---|
| POST | `/auth/face` | 얼굴 이미지(`image`, multipart)로 인증. `{authenticated, name, score, profile, reason}` 반환 |
| POST | `/users/register` | 신규 사용자 등록. `name/age/nickname/gender/height_cm/weight_kg(선택)/consent` + `image` |
| GET | `/users/{name}` | 등록된 사용자 프로필 조회 |
| GET/POST | `/users/{name}/heart-rate/*` | rPPG 연동 전까지 `available: false`를 반환하는 자리표시자 (아래 참고) |

등록 시 **만 14세 미만은 `age_restricted`(400)로 거부**된다 (클라이언트에서도 동일하게 막지만 서버에서 한 번 더 검증). 등록된 얼굴 embedding은 `output/database/database.pkl`에 추가되고, 프로필(나이/닉네임/성별/키/몸무게)은 `users.db`의 `app_users` 테이블에 저장된다. 기존 `iris_users` 테이블과는 분리되어 있다.

### rPPG(심박수) 연동 지점

B팀 rPPG 모듈이 준비되면 아래 두 곳만 실제 측정값으로 교체하면 앱 전체에 반영된다.

1. `backend/api.py`의 `latest_heart_rate` / `heart_rate_history` / `measure_heart_rate` — 현재는 `{"available": false, ...}` 고정 반환
2. 안드로이드·iOS·웹 클라이언트 모두 이미 `available`/`bpm`을 그대로 그려주므로 앱 코드 수정 없이 백엔드만 채우면 됨
   (참고: 심박수는 카메라 rPPG 대신 갤럭시 워치 연동으로 바뀔 수 있음 — 이 경우도 백엔드 응답 스키마는 그대로 재사용 가능)

## 안드로이드 앱

`android/` 폴더에 Kotlin + Jetpack Compose 프로젝트가 있다. Android Studio(Koala 이상 권장)에서 `android/` 폴더를 열면 Gradle 동기화가 진행된다 (Gradle Wrapper가 없다면 IDE가 생성해준다).

화면 흐름은 `이공계 학술제 ui ppt.pptx` 와이어프레임을 그대로 따른다.

```
메인화면 → 얼굴 인식 중(카메라 촬영)
   ├─ 미등록 얼굴 → 회원가입(이름/나이/성별/키·몸무게/특이사항/개인정보 동의) → 저장 완료
   └─ 등록된 얼굴 → 얼굴 인식 완료(프로필 + 오늘의 심박수 + 전체기록)
```

- `android/app/build.gradle.kts`의 `API_BASE_URL`은 기본값이 `http://10.0.2.2:8000/`(에뮬레이터에서 호스트 PC로 접속하는 주소)이다. 실제 기기에서 테스트하려면 이 값을 PC의 LAN IP(`http://192.168.x.x:8000/`)로 바꿔야 한다.
- 심박수 카드는 현재 백엔드가 `available: false`를 주므로 "측정 준비 중"으로만 표시된다 — rPPG 연동 후 자동으로 실제 bpm이 표시된다.
- 주요 구조: `network/`(Retrofit), `data/AuthRepository.kt`(API 호출 + 에러 메시지 매핑), `ui/screens/`(화면별 Composable + ViewModel), `navigation/NavGraph.kt`(화면 흐름).

## iOS 앱

`ios/` 폴더에 Swift + SwiftUI 프로젝트가 있다. 화면 흐름과 API 연동은 안드로이드 앱과 동일하다 (같은 백엔드를 호출).

### 빌드하기

Xcode(16 이상)와 [XcodeGen](https://github.com/yonaskolb/XcodeGen)이 필요하다 (`brew install xcodegen`). `.xcodeproj`는 저장소에 커밋하지 않고 `project.yml`로부터 생성한다.

```bash
cd ios
xcodegen generate          # project.yml → FaceAuth.xcodeproj 생성
open FaceAuth.xcodeproj    # Xcode에서 열어 시뮬레이터로 Run
```

또는 커맨드라인으로:

```bash
xcodebuild -project ios/FaceAuth.xcodeproj -scheme FaceAuth \
  -destination 'platform=iOS Simulator,name=iPhone 17' build
```

### 참고

- `FaceAuth/Networking/APIClient.swift`의 `APIConfig.baseURL`이 백엔드 주소(기본값 LAN IP)다. 안드로이드와 달리 iOS 시뮬레이터는 Mac의 네트워크를 그대로 공유하므로 `10.0.2.2` 같은 별도 주소가 필요 없고, LAN IP나 `127.0.0.1`을 바로 쓸 수 있다. 실기기 테스트 시엔 LAN IP를 유지해야 한다.
- 카메라 프리뷰(`Camera/CameraController.swift`)는 시뮬레이터에 실제 카메라 장치가 없으면 "이 기기에서는 카메라를 사용할 수 없습니다"로 안전하게 대체 표시된다 (크래시하지 않음). 실기기에서는 정상적으로 전면 카메라가 뜬다.
- 주요 구조: `Networking/`(URLSession 기반 APIClient + DTO), `Camera/`(AVFoundation), `Views/`(화면별 SwiftUI View + ViewModel), `App/ContentView.swift`(NavigationStack 기반 화면 흐름).

## 웹 앱 (학술제 제출용 — 가장 안정적인 데모 경로)

`web/` 폴더에 순수 HTML/CSS/JS로 만든 정적 웹앱이 있다. 빌드 도구나 npm 설치가 전혀 필요 없고, **백엔드 서버(`backend/api.py`)가 이 폴더를 직접 서빙**하므로 서버 하나만 켜면 끝난다.

```bash
source .venv/bin/activate
uvicorn backend.api:app --host 0.0.0.0 --port 8000 --reload
```

브라우저에서 `http://localhost:8000/` 접속 (같은 Wi-Fi의 다른 기기는 `http://<이 PC의 LAN IP>:8000/`).

- 안드로이드/iOS 에뮬레이터·시뮬레이터와 달리 **실제 브라우저의 `getUserMedia`는 카메라 접근이 안정적**이라, 학술제 현장 데모에는 이 웹 버전이 가장 사고 위험이 적다.
- 화면 흐름·필드·검증 로직(닉네임, 몸무게 선택, 만 14세 미만 차단)은 안드로이드/iOS와 동일하다.
- 주요 구조: `web/index.html`(마크업 + 화면 섹션), `web/app.js`(카메라 캡처·API 호출·화면 전환 전부 포함, 프레임워크 없음), `web/style.css`.

### 학술제 제출용 배포 (Render.com 무료 티어)

로컬 PC를 계속 켜둘 필요 없이, 인터넷에 항상 떠 있는 링크가 필요할 때 사용한다.

**한 번만 준비할 것**

1. 얼굴인식 모델(`models/w600k_r50.onnx`, 166MB)은 GitHub 100MB 제한을 넘어 **Git LFS**로 관리한다. 이미 이 저장소에 설정되어 있음 (`.gitattributes` 참고) — 새로 클론했다면 `brew install git-lfs && git lfs install` 후 `git lfs pull` 한 번만 하면 된다.
2. CASIA 연구용 얼굴 DB(`output/database/database.pkl`, 208MB, 98,000여 명)는 **배포에 포함하지 않는다** — 용량 문제뿐 아니라 연구용 데이터셋을 공개 서버에 올리는 것 자체가 바람직하지 않다. `backend/face_auth.py`가 이 파일이 없으면 자동으로 빈 데이터베이스로 시작하도록 이미 처리되어 있다 (`output/`는 `.gitignore`에 계속 남아있다).
3. 배포 서버는 `requirements.txt`(연구용 전처리 도구 포함, torch 등) 대신 **`requirements-web.txt`**(FastAPI 실행에 필요한 것만, 훨씬 가벼움)를 쓴다.

**배포 절차**

1. [render.com](https://render.com)에서 GitHub 계정으로 가입 (신용카드 불필요)
2. **New +** → **Blueprint** → 이 저장소(`Haneulskye/face_project`) 선택 → 저장소 루트의 `render.yaml`을 자동으로 인식해서 서비스가 구성됨
3. **Apply**를 누르면 빌드가 시작된다 (`git lfs pull`로 모델 다운로드 + `pip install -r requirements-web.txt`) — 첫 빌드는 5~10분 정도 걸릴 수 있다
4. 완료되면 `https://face-project-web.onrender.com` 같은 형태의 고정 주소가 생긴다 (HTTPS 자동 적용 — 브라우저 카메라 권한에 필수)

**무료 티어 주의사항**

- 일정 시간 요청이 없으면 서버가 잠들고, 다음 요청 시 30초 정도 깨어나는 시간이 걸린다 (학술제 발표 직전에 링크를 한 번 열어서 깨워두는 걸 권장).
- **디스크가 영구 저장이 아니다** — 서버가 재시작되면 그 사이 등록된 팀원 얼굴 데이터가 초기화될 수 있다. 발표 직전에 팀원들이 다시 한번 등록하는 것을 권장한다. 영구 저장이 필요하면 Render의 유료 플랜(Persistent Disk, 월 $7~)으로 전환하면 된다.
- 카메라 권한을 브라우저가 거부하면 "카메라 권한이 필요합니다" 안내와 함께 안전하게 처리된다 (크래시 없음).
