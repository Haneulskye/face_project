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
| POST | `/auth/face` | 얼굴 이미지(`image`, multipart)로 인증. `{authenticated, name, score, profile, reason, iris}` 반환. `iris: {matched, score, reason}`는 같은 사진에서 함께 계산되는 보조 신호일 뿐, 최종 `authenticated` 판정은 얼굴 결과만으로 결정된다 (아래 홍채 인식 참고) |
| POST | `/users/register` | 신규 사용자 등록. `name/age/nickname/gender/height_cm/weight_kg(선택)/consent` + `image`. 같은 사진에서 홍채도 best-effort로 함께 등록됨 |
| GET | `/users/{name}` | 등록된 사용자 프로필 조회 |
| GET | `/users/{name}/heart-rate/latest`, `/history` | 워치에서 동기화되어 저장된 최신/전체 심박수 기록 조회 |
| POST | `/users/{name}/heart-rate/measure` | `bpm`(옵션) + `source`(옵션, 예: `galaxy_watch`/`apple_watch`)를 보내면 저장 후 반환. `bpm`을 안 보내면 기존처럼 `{"available": false}` (워치 미연동 기기용 안전한 폴백) |

등록 시 **만 14세 미만은 `age_restricted`(400)로 거부**된다 (클라이언트에서도 동일하게 막지만 서버에서 한 번 더 검증). 등록된 얼굴 embedding은 `output/database/database.pkl`에 추가되고, 프로필(나이/닉네임/성별/키/몸무게)은 `users.db`의 `app_users` 테이블에 저장된다. 홍채 embedding은 기존 `iris_users` 테이블에 함께 저장되지만, 매칭 시에는 `app_users`에 등록된 이름으로만 필터링해서 CASIA 데이터셋의 249명과 섞이지 않도록 했다.

### 홍채 인식 (프로토타입 / 데모 단계)

`backend/iris_auth.py`가 얼굴 사진에서 MediaPipe FaceMesh로 눈 주변을 크롭해 홍채 embedding을 함께 계산한다. 다만 `src/iris_embedding.py`의 모델은 **홍채 전용으로 학습된 모델이 아니라 ImageNet 사전학습 ResNet18에서 분류 헤드만 제거한 범용 특징 추출기**다 — 즉 실제 홍채 무늬 기반 생체인증이 아니라 눈 주변 이미지의 대략적인 유사도 비교에 가깝다. 폰 카메라(가시광선)로는 적외선 홍채 카메라 수준의 무늬 디테일을 애초에 촬영할 수 없다는 하드웨어 한계도 있다. 그래서 얼굴 인식이 최종 인증을 판정하고, 홍채 결과는 화면에 함께 보여주기만 하는 보조 신호로 설계했다. **정확도 개선은 2026년 10월 말 예정** — 이때는 홍채 전용으로 파인튜닝한 모델로 교체하는 것이 핵심이며, 임계값 조정만으로는 근본적인 해결이 안 된다.

### 워치 심박수 연동

카메라 rPPG 대신 페어링된 워치(갤럭시 워치는 Android의 Health Connect, 애플 워치는 iOS의 HealthKit)에서 읽은 값을 `POST /users/{name}/heart-rate/measure`로 백엔드에 올리는 방식으로 구현했다. 브라우저는 워치에 직접 접근할 수 없으므로, 웹 클라이언트는 폰 앱이 이미 올려둔 값을 조회만 한다. `backend/heart_rate_store.py`가 기록을 저장한다.

## 안드로이드 앱

`android/` 폴더에 Kotlin + Jetpack Compose 프로젝트가 있다. Android Studio(Koala 이상 권장)에서 `android/` 폴더를 열면 Gradle 동기화가 진행된다 (Gradle Wrapper가 없다면 IDE가 생성해준다).

화면 흐름은 `이공계 학술제 ui ppt.pptx` 와이어프레임을 그대로 따른다.

```
메인화면 → 얼굴 인식 중(카메라 촬영)
   ├─ 미등록 얼굴 → 회원가입(이름/나이/성별/키·몸무게/특이사항/개인정보 동의) → 저장 완료
   └─ 등록된 얼굴 → 얼굴 인식 완료(프로필 + 오늘의 심박수 + 전체기록)
```

- `android/app/build.gradle.kts`의 `API_BASE_URL`은 debug 빌드에서 `http://10.0.2.2:8000/`(에뮬레이터→호스트 PC), release 빌드에서는 현재 임시 ngrok 터널 주소로 되어 있다 — 캠퍼스 네트워크가 폰↔맥 LAN 직접 연결을 막아서 쓴 임시방편이라 **터널을 재시작하면 이 값도 다시 바꿔야 한다.**
- 얼굴 인식 화면에 FaceID 스타일 타원 가이드(`FaceScanScreen.kt`의 `FaceAlignmentGuideOverlay`)가 항상 표시되고, 인증 성공 시 얼굴+홍채 일치 여부를 잠깐 함께 보여준다.
- 심박수는 프로필 화면에서 "심박수 측정"을 누르면 Health Connect(`health/HealthConnectManager.kt`)에서 갤럭시 워치가 동기화한 최신 값을 읽어 백엔드로 올린다. Health Connect가 없거나(에뮬레이터 등) 동기화된 값이 없으면 기존처럼 "측정 준비 중"으로 표시된다.
- 주요 구조: `network/`(Retrofit), `data/AuthRepository.kt`(API 호출 + 에러 메시지 매핑), `health/`(Health Connect), `ui/screens/`(화면별 Composable + ViewModel), `navigation/NavGraph.kt`(화면 흐름).

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

- `FaceAuth/Networking/APIClient.swift`의 `APIConfig.baseURL`이 백엔드 주소다. 안드로이드 release 빌드와 동일한 임시 ngrok 터널 주소를 쓰고 있다 — 터널을 재시작하면 이 값도 다시 바꿔야 한다.
- 카메라 프리뷰(`Camera/CameraController.swift`)는 시뮬레이터에 실제 카메라 장치가 없으면 "이 기기에서는 카메라를 사용할 수 없습니다"로 안전하게 대체 표시된다 (크래시하지 않음). 실기기에서는 정상적으로 전면 카메라가 뜬다.
- 얼굴 인식 화면에 FaceID 스타일 타원 가이드가 표시되고, 인증 성공 시 얼굴+홍채 일치 여부를 잠깐 함께 보여준다 (`Views/FaceScanView.swift`).
- 심박수는 프로필 화면에서 "심박수 측정"을 누르면 HealthKit(`Health/HealthKitManager.swift`)에서 애플 워치가 기록한 최신 값을 읽어 백엔드로 올린다. `com.apple.developer.healthkit` 엔타이틀먼트가 필요하며 `project.yml`에 선언되어 있어 `xcodegen generate` 시 자동 생성된다. **애플 워치 실기기 페어링이 없는 환경(시뮬레이터 등)에서는 검증되지 않았다** — HealthKit은 시뮬레이터에서 실제 워치 데이터를 받을 수 없다.
- 주요 구조: `Networking/`(URLSession 기반 APIClient + DTO), `Camera/`(AVFoundation), `Health/`(HealthKit), `Views/`(화면별 SwiftUI View + ViewModel), `App/ContentView.swift`(NavigationStack 기반 화면 흐름).

## 웹 앱 (학술제 제출용 — 가장 안정적인 데모 경로)

`web/` 폴더에 순수 HTML/CSS/JS로 만든 정적 웹앱이 있다. 빌드 도구나 npm 설치가 전혀 필요 없고, **백엔드 서버(`backend/api.py`)가 이 폴더를 직접 서빙**하므로 서버 하나만 켜면 끝난다.

```bash
source .venv/bin/activate
uvicorn backend.api:app --host 0.0.0.0 --port 8000 --reload
```

브라우저에서 `http://localhost:8000/` 접속 (같은 Wi-Fi의 다른 기기는 `http://<이 PC의 LAN IP>:8000/`).

- 안드로이드/iOS 에뮬레이터·시뮬레이터와 달리 **실제 브라우저의 `getUserMedia`는 카메라 접근이 안정적**이라, 학술제 현장 데모에는 이 웹 버전이 가장 사고 위험이 적다.
- 화면 흐름·필드·검증 로직(닉네임, 몸무게 선택, 만 14세 미만 차단)은 안드로이드/iOS와 동일하다. 얼굴 인식 화면엔 동일한 FaceID 스타일 타원 가이드가 있고, 인증 성공 시 얼굴+홍채 일치 여부를 잠깐 보여준다.
- 브라우저는 워치(Health Connect/HealthKit)에 직접 접근할 수 없으므로, 심박수 카드는 폰 앱이 이미 백엔드에 올려둔 값을 조회만 한다 — 웹만 단독으로 켜둔 경우엔 "측정 준비 중"으로 남는다.
- 주요 구조: `web/index.html`(마크업 + 화면 섹션), `web/app.js`(카메라 캡처·API 호출·화면 전환 전부 포함, 프레임워크 없음), `web/style.css`. 정적 파일에 `?v=2` 같은 캐시 버스팅 쿼리가 붙어있다 — 브라우저가 이전 `style.css`/`app.js`를 강하게 캐싱해서 배포 후 변경 사항이 반영되지 않는 문제가 있었다. 다음에 이 파일들을 수정하면 버전 번호를 올려야 한다.

### 학술제 제출용 배포 (Render.com 무료 티어)

로컬 PC를 계속 켜둘 필요 없이, 인터넷에 항상 떠 있는 링크가 필요할 때 사용한다.

**한 번만 준비할 것**

1. 얼굴인식 모델(`models/w600k_r50.onnx`, 166MB)은 GitHub 100MB 제한을 넘어 **Git LFS**로 관리한다. 이미 이 저장소에 설정되어 있음 (`.gitattributes` 참고) — 새로 클론했다면 `brew install git-lfs && git lfs install` 후 `git lfs pull` 한 번만 하면 된다.
2. CASIA 연구용 얼굴 DB(`output/database/database.pkl`, 208MB, 98,000여 명)는 **배포에 포함하지 않는다** — 용량 문제뿐 아니라 연구용 데이터셋을 공개 서버에 올리는 것 자체가 바람직하지 않다. `backend/face_auth.py`가 이 파일이 없으면 자동으로 빈 데이터베이스로 시작하도록 이미 처리되어 있다 (`output/`는 `.gitignore`에 계속 남아있다).
3. 배포 서버는 `requirements.txt`(연구용 전처리 도구까지 포함) 대신 **`requirements-web.txt`**(FastAPI 실행에 필요한 것만)를 쓴다. 홍채 인식이 `/auth/face`·`/users/register`에 함께 연결되면서 `torch`/`torchvision`도 이제 여기 포함된다 — 이전보다 빌드 용량·시간이 늘었다 (아래 "첫 빌드는 5~10분" 참고).

**배포 절차**

1. [render.com](https://render.com)에서 GitHub 계정으로 가입 (신용카드 불필요)
2. **New +** → **Blueprint** → 이 저장소(`Haneulskye/face_project`) 선택 → 저장소 루트의 `render.yaml`을 자동으로 인식해서 서비스가 구성됨
3. **Apply**를 누르면 빌드가 시작된다 (`git lfs pull`로 모델 다운로드 + `pip install -r requirements-web.txt`) — 첫 빌드는 5~10분 정도 걸릴 수 있다
4. 완료되면 `https://face-project-web.onrender.com` 같은 형태의 고정 주소가 생긴다 (HTTPS 자동 적용 — 브라우저 카메라 권한에 필수)

**무료 티어 주의사항**

- 일정 시간 요청이 없으면 서버가 잠들고, 다음 요청 시 30초 정도 깨어나는 시간이 걸린다 (학술제 발표 직전에 링크를 한 번 열어서 깨워두는 걸 권장).
- **디스크가 영구 저장이 아니다** — 서버가 재시작되면 그 사이 등록된 팀원 얼굴 데이터가 초기화될 수 있다. 발표 직전에 팀원들이 다시 한번 등록하는 것을 권장한다. 영구 저장이 필요하면 Render의 유료 플랜(Persistent Disk, 월 $7~)으로 전환하면 된다.
- 카메라 권한을 브라우저가 거부하면 "카메라 권한이 필요합니다" 안내와 함께 안전하게 처리된다 (크래시 없음).
